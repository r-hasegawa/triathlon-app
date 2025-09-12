"""
app/services/flexible_csv_service.py

実データ対応版（WBGT実装含む）
"""

import pandas as pd
import io
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.flexible_sensor_data import (
    RawSensorData, FlexibleSensorMapping,
    SkinTemperatureData, CoreTemperatureData, 
    HeartRateData, WBGTData, SensorDataStatus, SensorType
)
from app.schemas.sensor_data import (
    UploadResponse, MappingResponse,
    DataSummaryResponse, MappingStatusResponse
)

class FlexibleCSVService:
    
    async def process_sensor_data_only(
        self,
        sensor_file: UploadFile,
        sensor_type: SensorType,
        competition_id: str,
        db: Session
    ) -> UploadResponse:
        """センサーデータのみ処理"""
        try:
            # 大会存在チェック追加
            from app.models import Competition
            competition = db.query(Competition).filter_by(competition_id=competition_id).first()
            if not competition:
                raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
            
            content = await sensor_file.read()
            df = pd.read_csv(io.BytesIO(content))
            
            processed = 0
            
            for _, row in df.iterrows():
                raw_data = RawSensorData(
                    sensor_type=sensor_type,
                    sensor_id=str(row.get('sensor_id', '')),
                    timestamp=pd.to_datetime(row.get('timestamp')),
                    data_values=str(row.get('value', 0)),
                    competition_id=competition_id,
                    mapping_status=SensorDataStatus.UNMAPPED,
                    raw_data=row.to_json()
                )
                db.add(raw_data)
                processed += 1
            
            db.commit()
            
            return UploadResponse(
                success=True,
                message=f"{sensor_type.value}データを{processed}件処理しました（大会: {competition.name}）",
                total_records=len(df),
                processed_records=processed
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"データ処理エラー: {str(e)}")

    async def process_wbgt_data(
        self,
        wbgt_file: UploadFile,
        competition_id: Optional[str],
        db: Session,
        overwrite: bool = True
    ) -> UploadResponse:
        """WBGT環境データ処理（実データ対応版 + バッチ管理）
        
        仕様：
        - 入力：日付、時刻、WBGT値、気温、相対湿度、黒球温度（6列）
        - 処理：日付と時刻を組み合わせて一つのdatetimeに変換
        - 保存：datetime、WBGT値、気温、相対湿度、黒球温度の5つの値
        - バッチ管理：他のセンサーデータと同様のバッチ管理
        """
        try:
            # バッチID生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_id = f"{timestamp}_{wbgt_file.filename}"
            
            # 上書き処理：既存データを削除
            if overwrite and competition_id:
                deleted_count = db.query(WBGTData).filter_by(competition_id=competition_id).delete()
                db.commit()
                print(f"既存WBGTデータ{deleted_count}件を削除しました")
            
            # CSVファイル読み込み（エンコーディング対応）
            content = await wbgt_file.read()
            
            # Shift_JISで直接読み込み（WBGTデータは日本の機器なのでShift_JIS）
            try:
                decoded_content = content.decode('shift_jis')
                detected_encoding = 'shift_jis'
            except UnicodeDecodeError:
                # フォールバック
                for encoding in ['utf-8', 'cp932', 'iso-8859-1']:
                    try:
                        decoded_content = content.decode(encoding)
                        detected_encoding = encoding
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise HTTPException(status_code=400, detail="CSVファイルの文字コードを認識できませんでした")
            
            print(f"使用エンコーディング: {detected_encoding}")
            
            # CSVをDataFrameに読み込み
            df = pd.read_csv(io.StringIO(decoded_content))
            
            print(f"読み込み完了 - 行数: {len(df)}, 列数: {len(df.columns)}")
            print(f"列名: {list(df.columns)}")
            
            # 列名の正規化（文字化け対応）
            column_mapping = self._normalize_wbgt_columns(df.columns)
            
            if not column_mapping:
                raise HTTPException(
                    status_code=400, 
                    detail=f"WBGT必須列が見つかりません。現在の列: {list(df.columns)}"
                )
            
            print(f"列マッピング: {column_mapping}")
            
            # データ処理
            processed = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # 日付と時刻の結合
                    datetime_value = self._combine_date_time(row, column_mapping)
                    
                    if datetime_value is None:
                        errors.append(f"行{index+1}: 日付・時刻の結合に失敗")
                        continue
                    
                    # WBGT関連データの取得
                    wbgt_value = self._safe_float(row.get(column_mapping.get('wbgt')))
                    air_temp = self._safe_float(row.get(column_mapping.get('air_temperature')))
                    humidity = self._safe_float(row.get(column_mapping.get('humidity')))
                    globe_temp = self._safe_float(row.get(column_mapping.get('globe_temperature')))
                    
                    # 必須項目チェック
                    if wbgt_value is None:
                        errors.append(f"行{index+1}: WBGT値が無効")
                        continue
                    
                    # WBGTDataオブジェクト作成（バッチ管理対応）
                    wbgt_data = WBGTData(
                        timestamp=datetime_value,
                        wbgt_value=wbgt_value,
                        air_temperature=air_temp,
                        humidity=humidity,
                        globe_temperature=globe_temp,
                        competition_id=competition_id,
                        station_id="WBGT_STATION_001",  # デフォルト値
                        upload_batch_id=batch_id,  # 🆕 バッチID設定
                        uploaded_at=datetime.now()
                    )
                    
                    db.add(wbgt_data)
                    processed += 1
                    
                except Exception as e:
                    errors.append(f"行{index+1}: {str(e)}")
                    continue
            
            # 🆕 UploadBatch記録作成
            from app.models.flexible_sensor_data import UploadBatch, UploadStatus, SensorType
            
            upload_batch = UploadBatch(
                batch_id=batch_id,
                sensor_type=SensorType.WBGT,  # WBGT用のSensorType
                competition_id=competition_id,
                file_name=wbgt_file.filename,
                file_size=len(content),
                total_records=len(df),
                success_records=processed,
                failed_records=len(errors),
                status=UploadStatus.SUCCESS if len(errors) == 0 else UploadStatus.PARTIAL,
                uploaded_by="admin",  # TODO: 実際のユーザーIDに変更
                notes=f"エラー: {len(errors)}件" if errors else None
            )
            db.add(upload_batch)
            
            db.commit()
            
            # 結果メッセージ作成
            message = f"WBGTデータを{processed}件処理しました（バッチID: {batch_id}）"
            if errors:
                message += f"（エラー{len(errors)}件）"
                print("エラー詳細:", errors[:10])  # 最初の10件のみログ出力
            
            return UploadResponse(
                success=True,
                message=message,
                total_records=len(df),
                processed_records=processed,
                errors=errors[:20] if errors else []  # 最大20件のエラーを返却
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"WBGT処理エラー: {str(e)}")

    def _normalize_wbgt_columns(self, columns: List[str]) -> Dict[str, str]:
        """WBGT列名を正規化してマッピングを作成（実データ対応）"""
        columns = [str(col).strip() for col in columns]
        mapping = {}
        
        # 実データの正確な列名でマッピング
        column_map = {
            '日付': 'date',
            '時刻': 'time', 
            'WBGT値': 'wbgt',
            '気温': 'air_temperature',
            '相対湿度': 'humidity',
            '黒球温度': 'globe_temperature'
        }
        
        # 正確な列名マッチング
        for col in columns:
            if col in column_map:
                mapping[column_map[col]] = col
        
        # 最低限WBGT値が必要
        if 'wbgt' not in mapping:
            return {}
        
        return mapping

    def _combine_date_time(self, row: pd.Series, column_mapping: Dict[str, str]) -> Optional[datetime]:
        """日付と時刻を結合してdatetimeオブジェクトを作成（実データ対応）"""
        try:
            date_col = column_mapping.get('date')  # '日付'
            time_col = column_mapping.get('time')  # '時刻'
            
            if not date_col or not time_col:
                return None
                
            date_str = str(row.get(date_col, '')).strip()  # '2025/07/15'
            time_str = str(row.get(time_col, '')).strip()  # '17:43:38'
            
            if not date_str or not time_str or date_str == 'nan' or time_str == 'nan':
                return None
            
            # 実データフォーマット: '2025/07/15 17:43:38'
            datetime_str = f"{date_str} {time_str}"
            
            try:
                # 実データの正確なフォーマット
                return datetime.strptime(datetime_str, '%Y/%m/%d %H:%M:%S')
            except ValueError:
                # フォールバック
                try:
                    return pd.to_datetime(datetime_str)
                except:
                    return None
            
        except Exception as e:
            print(f"日付・時刻結合エラー: {e}")
            return None

    def _safe_float(self, value) -> Optional[float]:
        """安全にfloat変換"""
        if value is None or pd.isna(value):
            return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    async def process_mapping_data(
        self,
        mapping_file: UploadFile,
        competition_id: str,  # 必須
        db: Session,
        overwrite: bool = True
    ) -> MappingResponse:
        """柔軟なマッピングデータ処理"""
        try:
            # 大会存在チェック
            from app.models import Competition
            competition = db.query(Competition).filter_by(competition_id=competition_id).first()
            if not competition:
                raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
            
            if overwrite and competition_id:
                db.query(FlexibleSensorMapping).filter_by(competition_id=competition_id).delete()
            
            content = await mapping_file.read()
            df = pd.read_csv(io.BytesIO(content))
            
            # 必須列チェック
            if 'user_id' not in df.columns:
                raise HTTPException(status_code=400, detail="user_id列が必要です")
            
            # user_id重複チェック
            duplicate_users = df[df['user_id'].duplicated()]['user_id'].tolist()
            if duplicate_users:
                raise HTTPException(
                    status_code=400, 
                    detail=f"user_idに重複があります: {duplicate_users}"
                )
            
            # 認識するセンサー列のみ（固定列名）- 個人データのみ
            recognized_sensor_columns = {
                'skin_temp_sensor_id': SensorType.SKIN_TEMPERATURE,
                'core_temp_sensor_id': SensorType.CORE_TEMPERATURE,
                'heart_rate_sensor_id': SensorType.HEART_RATE
                # WBGTは環境データなのでマッピング不要
            }
            
            # 認識する列リスト（user_id + センサー列のみ）
            recognized_columns = {'user_id'}.union(set(recognized_sensor_columns.keys()))
            
            processed = 0
            skipped = 0
            errors = []
            
            for _, row in df.iterrows():
                user_id = str(row.get('user_id', '')).strip()
                
                if not user_id:
                    skipped += 1
                    continue
                
                # ユーザー存在チェック
                from app.models import User
                user = db.query(User).filter_by(user_id=user_id).first()
                if not user:
                    skipped += 1
                    errors.append(f"未登録ユーザー: {user_id}")
                    continue
                
                # センサーマッピング処理
                for col_name, sensor_type in recognized_sensor_columns.items():
                    sensor_id = str(row.get(col_name, '')).strip()
                    
                    if sensor_id and sensor_id != 'nan':
                        # マッピングデータ作成
                        mapping = FlexibleSensorMapping(
                            user_id=user_id,
                            competition_id=competition_id,
                            sensor_id=sensor_id,
                            sensor_type=sensor_type,
                            subject_name=str(row.get('subject_name', '')).strip() or None,
                            device_type=col_name,
                            is_active=True
                        )
                        db.add(mapping)
                
                processed += 1
            
            db.commit()
            
            return MappingResponse(
                success=True,
                message=f"マッピングデータを{processed}件処理しました（スキップ: {skipped}件）",
                total_records=len(df),
                processed_records=processed,
                skipped_records=skipped,
                errors=errors
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"マッピング処理エラー: {str(e)}")

    def get_data_summary(
        self,
        db: Session,
        competition_id: Optional[str] = None
    ) -> DataSummaryResponse:
        """データサマリー取得"""
        
        # センサーデータ統計
        query = db.query(RawSensorData)
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        
        total_records = query.count()
        mapped_records = query.filter(RawSensorData.mapping_status == SensorDataStatus.MAPPED).count()
        unmapped_records = query.filter(RawSensorData.mapping_status == SensorDataStatus.UNMAPPED).count()
        
        # センサータイプ別統計
        sensor_counts = {}
        for sensor_type in SensorType:
            count = query.filter(RawSensorData.sensor_type == sensor_type).count()
            sensor_counts[sensor_type.value] = count
        
        wbgt_count = db.query(WBGTData)
        if competition_id:
            wbgt_count = wbgt_count.filter_by(competition_id=competition_id)
        wbgt_count = wbgt_count.count()
        
        mapping_count = db.query(FlexibleSensorMapping)
        if competition_id:
            mapping_count = mapping_count.filter_by(competition_id=competition_id)
        mapping_count = mapping_count.count()
        
        return DataSummaryResponse(
            total_sensor_records=total_records,
            mapped_records=mapped_records,
            unmapped_records=unmapped_records,
            sensor_type_counts=sensor_counts,
            wbgt_records=wbgt_count,
            mapping_records=mapping_count,
            competition_id=competition_id
        )

    def get_mapping_status(
        self,
        db: Session,
        competition_id: Optional[str] = None
    ) -> MappingStatusResponse:
        """マッピング状況確認"""
        
        query = db.query(RawSensorData)
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        
        status_counts = {}
        for status in SensorDataStatus:
            count = query.filter_by(mapping_status=status).count()
            status_counts[status.value] = count
        
        unmapped_by_type = {}
        for sensor_type in SensorType:
            count = query.filter(
                RawSensorData.sensor_type == sensor_type,
                RawSensorData.mapping_status == SensorDataStatus.UNMAPPED
            ).count()
            unmapped_by_type[sensor_type.value] = count
        
        return MappingStatusResponse(
            status_counts=status_counts,
            unmapped_by_sensor_type=unmapped_by_type,
            competition_id=competition_id
        )

    def get_unmapped_sensors(
        self,
        db: Session,
        sensor_type: Optional[SensorType] = None,
        competition_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """未マップセンサー一覧取得"""
        
        query = db.query(RawSensorData).filter_by(mapping_status=SensorDataStatus.UNMAPPED)
        
        if sensor_type:
            query = query.filter_by(sensor_type=sensor_type)
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        
        # センサーIDでグループ化
        unmapped_sensors = query.with_entities(
            RawSensorData.sensor_id,
            RawSensorData.sensor_type,
            RawSensorData.competition_id
        ).distinct().limit(limit).all()
        
        return [
            {
                'sensor_id': sensor.sensor_id,
                'sensor_type': sensor.sensor_type.value,
                'competition_id': sensor.competition_id
            }
            for sensor in unmapped_sensors
        ]