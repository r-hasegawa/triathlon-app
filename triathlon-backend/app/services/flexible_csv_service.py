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
        competition_id: str,
        db: Session,
        overwrite: bool = True
    ) -> UploadResponse:
        """WBGT環境データ処理（計測時刻をtimestampに保存）"""
        try:
            # バッチID生成
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_id = f"{timestamp_str}_{wbgt_file.filename}"
            
            # 上書き処理：既存データ削除
            if overwrite:
                deleted_count = db.query(WBGTData).filter_by(competition_id=competition_id).delete()
                db.commit()
                print(f"既存WBGTデータ{deleted_count}件を削除しました")
            
            # CSV読み込み
            content = await wbgt_file.read()
            decoded_content = content.decode('shift_jis')
            df = pd.read_csv(io.StringIO(decoded_content))
            
            # 列マッピング
            column_mapping = {
                'date': '日付',
                'time': '時刻',
                'wbgt': 'WBGT値',
                'air_temperature': '気温',
                'humidity': '相対湿度',
                'globe_temperature': '黒球温度'
            }
            
            processed = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    # 計測時刻を timestamp に
                    date_str = str(row[column_mapping['date']]).strip()
                    time_str = str(row[column_mapping['time']]).strip()
                    dt = datetime.strptime(f"{date_str} {time_str}", '%Y/%m/%d %H:%M:%S')
                    
                    wbgt_value = float(row[column_mapping['wbgt']])
                    air_temp = float(row[column_mapping['air_temperature']])
                    humidity = float(row[column_mapping['humidity']])
                    globe_temp = float(row[column_mapping['globe_temperature']])
                    
                    wbgt_data = WBGTData(
                        timestamp=dt,
                        wbgt_value=wbgt_value,
                        air_temperature=air_temp,
                        humidity=humidity,
                        globe_temperature=globe_temp,
                        competition_id=competition_id,
                        upload_batch_id=batch_id
                    )
                    db.add(wbgt_data)
                    processed += 1
                except Exception as e:
                    errors.append(f"行{idx+1}: {e}")
                    continue
            
            # UploadBatch登録
            from app.models.flexible_sensor_data import UploadBatch, UploadStatus, SensorType
            batch = UploadBatch(
                batch_id=batch_id,
                sensor_type=SensorType.WBGT,
                competition_id=competition_id,
                file_name=wbgt_file.filename,
                file_size=len(content),
                total_records=len(df),
                success_records=processed,
                failed_records=len(errors),
                status=UploadStatus.SUCCESS if not errors else UploadStatus.PARTIAL,
                uploaded_by="admin",
                notes=f"エラー{len(errors)}件" if errors else None
            )
            db.add(batch)
            db.commit()
            
            return UploadResponse(
                success=True,
                message=f"WBGTデータ {processed}件処理しました",
                total_records=len(df),
                processed_records=processed,
                errors=errors[:20]  # 最大20件
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
        competition_id: str,
        db: Session,
        overwrite: bool = True
    ) -> Dict[str, Any]:
        """マッピングデータ処理（柔軟な列構成対応）"""
        df = None  # 変数を最初に初期化
        
        try:
            # 大会存在チェック
            from app.models.competition import Competition
            competition = db.query(Competition).filter_by(competition_id=competition_id).first()
            if not competition:
                raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
            
            # 上書き処理：既存マッピングデータを削除
            if overwrite and competition_id:
                deleted_count = db.query(FlexibleSensorMapping).filter_by(competition_id=competition_id).delete()
                db.commit()
                print(f"既存マッピングデータ{deleted_count}件を削除しました")
            
            # CSVファイル読み込み
            try:
                # ファイルポインタを先頭に戻す
                await mapping_file.seek(0)
                content = await mapping_file.read()
            except Exception:
                # seek失敗時は既存contentを使用
                content = await mapping_file.read()
            
            if not content:
                raise HTTPException(status_code=400, detail="CSVファイルが空です")
            
            # エンコーディング自動検出
            decoded_content = None
            detected_encoding = None
            
            for encoding in ['utf-8', 'shift_jis', 'cp932', 'iso-8859-1']:
                try:
                    decoded_content = content.decode(encoding)
                    detected_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if decoded_content is None:
                raise HTTPException(status_code=400, detail="CSVファイルの文字コードを認識できませんでした")
            
            print(f"マッピングデータ使用エンコーディング: {detected_encoding}")
            
            # CSVをDataFrameに読み込み
            try:
                df = pd.read_csv(io.StringIO(decoded_content))
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"CSV読み込みエラー: {str(e)}")
            
            if df is None or df.empty:
                raise HTTPException(status_code=400, detail="CSVファイルにデータがありません")
            
            print(f"マッピングデータ読み込み完了 - 行数: {len(df)}, 列数: {len(df.columns)}")
            print(f"列名: {list(df.columns)}")
            
            # 列名の空白除去
            df.columns = df.columns.str.strip()
            
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
            
            # 認識するセンサー列（柔軟対応）
            recognized_sensor_columns = {
                'skin_temp_sensor_id': SensorType.SKIN_TEMPERATURE,
                'core_temp_sensor_id': SensorType.CORE_TEMPERATURE,
                'heart_rate_sensor_id': SensorType.HEART_RATE,
                'skin_temperature_sensor_id': SensorType.SKIN_TEMPERATURE,  # 別名対応
                'core_temperature_sensor_id': SensorType.CORE_TEMPERATURE,  # 別名対応
                'heart_rate_id': SensorType.HEART_RATE,  # 別名対応
            }
            
            # デバッグ情報
            print(f"認識可能な列: {list(recognized_sensor_columns.keys())}")
            available_sensor_columns = [col for col in df.columns if col in recognized_sensor_columns]
            print(f"CSVに存在する認識可能な列: {available_sensor_columns}")
            
            if not available_sensor_columns:
                raise HTTPException(
                    status_code=400, 
                    detail=f"認識可能なセンサー列がありません。利用可能な列: {list(df.columns)}"
                )
            
            processed = 0
            skipped = 0
            errors = []
            
            for index, row in df.iterrows():
                user_id = str(row.get('user_id', '')).strip()
                
                print(f"処理中 行{index+1}: user_id='{user_id}'")
                
                if not user_id or user_id == 'nan':
                    skipped += 1
                    errors.append(f"行{index+1}: user_idが空")
                    continue
                
                # ユーザー存在チェック
                from app.models.user import User
                user = db.query(User).filter_by(user_id=user_id).first()
                if not user:
                    skipped += 1
                    errors.append(f"行{index+1}: 未登録ユーザー '{user_id}'")
                    print(f"ユーザー '{user_id}' が見つかりません")
                    continue
                
                print(f"ユーザー '{user_id}' 存在確認")
                
                # 各センサーのマッピング処理
                user_mappings_created = 0
                for col_name, sensor_type in recognized_sensor_columns.items():
                    if col_name in df.columns:
                        sensor_id = str(row.get(col_name, '')).strip()
                        print(f"列 '{col_name}': sensor_id='{sensor_id}'")
                        
                        if sensor_id and sensor_id != 'nan' and sensor_id != '':
                            try:
                                # マッピングデータ作成
                                mapping = FlexibleSensorMapping(
                                    user_id=user_id,
                                    competition_id=competition_id,
                                    sensor_id=sensor_id,
                                    sensor_type=sensor_type,
                                    subject_name=str(row.get('subject_name', '')).strip() or None,
                                    device_type=col_name,
                                    is_active=True,
                                    created_at=datetime.now()
                                )
                                db.add(mapping)
                                user_mappings_created += 1
                                print(f"マッピング作成: {user_id} -> {sensor_id} ({sensor_type.value})")
                                
                            except Exception as e:
                                errors.append(f"行{index+1}, 列{col_name}: マッピング作成エラー - {str(e)}")
                                print(f"マッピング作成エラー: {str(e)}")
                    else:
                        print(f"列 '{col_name}' はCSVに存在しません")
                
                print(f"ユーザー '{user_id}' で作成されたマッピング数: {user_mappings_created}")
                
                if user_mappings_created > 0:
                    processed += 1
                else:
                    skipped += 1
                    errors.append(f"行{index+1}: ユーザー '{user_id}' に有効なセンサーマッピングなし")
            
            db.commit()
            
            # 結果メッセージ作成
            message = f"マッピングデータを{processed}件のユーザーに対して処理しました"
            if skipped > 0:
                message += f"（スキップ: {skipped}件）"
            
            return {
                "success": True,
                "message": message,
                "total_records": len(df),
                "processed_records": processed,
                "skipped_records": skipped,
                "errors": errors[:10] if errors else []  # 最初の10件のみ
            }
            
        except HTTPException:
            # HTTPExceptionは再発生させる
            raise
        except Exception as e:
            db.rollback()
            error_message = f"マッピング処理エラー: {str(e)}"
            print(error_message)
            
            # dfが定義されていない場合のフォールバック
            total_records = len(df) if df is not None else 0
            
            raise HTTPException(status_code=500, detail=error_message)

    async def process_wbgt_data(
        self,
        wbgt_file: UploadFile,
        competition_id: str,
        db: Session,
        overwrite: bool = True
    ) -> UploadResponse:
        """WBGT環境データ処理（実データ対応版＋バッチ管理）"""
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
                        upload_batch_id=batch_id,  # バッチID設定
                        uploaded_at=datetime.now()
                    )
                    
                    db.add(wbgt_data)
                    processed += 1
                    
                except Exception as e:
                    errors.append(f"行{index+1}: {str(e)}")
                    continue
            
            # UploadBatch記録作成
            from app.models.flexible_sensor_data import UploadBatch, UploadStatus, SensorType
            
            upload_batch = UploadBatch(
                batch_id=batch_id,
                sensor_type=SensorType.WBGT,
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
            
            return UploadResponse(
                success=True,
                message=message,
                total_records=len(df),
                processed_records=processed,
                success_records=processed,  # フロントエンド互換性のため
                failed_records=len(errors),
                errors=errors[:10] if errors else None  # 最初の10件のみ
            )
            
        except Exception as e:
            db.rollback()
            print(f"WBGT処理エラー: {str(e)}")
            raise HTTPException(status_code=500, detail=f"WBGT処理エラー: {str(e)}")

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

    def _detect_race_phases(self, record_data: dict) -> dict:
        """SWIM/BIKE/RUN区間自動判定（フィードバックグラフ背景色用）"""
        phases = {
            'swim_phase': None,
            'bike_phase': None, 
            'run_phase': None,
            'total_phase': None,
            'transition_phases': []  # トランジション期間
        }
        
        try:
            # 全体の開始・終了時刻
            start_times = [record_data['swim_start'], record_data['bike_start'], record_data['run_start']]
            finish_times = [record_data['swim_finish'], record_data['bike_finish'], record_data['run_finish']]
            
            start_times = [t for t in start_times if t is not None]
            finish_times = [t for t in finish_times if t is not None]
            
            if start_times and finish_times:
                total_start = min(start_times)
                total_finish = max(finish_times)
                phases['total_phase'] = {
                    'start': total_start,
                    'finish': total_finish,
                    'duration_seconds': (total_finish - total_start).total_seconds()
                }
            
            # 各競技フェーズ（フィードバックグラフの背景色用）
            if record_data['swim_start'] and record_data['swim_finish']:
                swim_duration = (record_data['swim_finish'] - record_data['swim_start']).total_seconds()
                phases['swim_phase'] = {
                    'start': record_data['swim_start'],
                    'finish': record_data['swim_finish'],
                    'duration_seconds': swim_duration,
                    'phase_type': 'swim'
                }
            
            if record_data['bike_start'] and record_data['bike_finish']:
                bike_duration = (record_data['bike_finish'] - record_data['bike_start']).total_seconds()
                phases['bike_phase'] = {
                    'start': record_data['bike_start'],
                    'finish': record_data['bike_finish'],
                    'duration_seconds': bike_duration,
                    'phase_type': 'bike'
                }
            
            if record_data['run_start'] and record_data['run_finish']:
                run_duration = (record_data['run_finish'] - record_data['run_start']).total_seconds()
                phases['run_phase'] = {
                    'start': record_data['run_start'],
                    'finish': record_data['run_finish'],
                    'duration_seconds': run_duration,
                    'phase_type': 'run'
                }
            
            # 🆕 トランジション期間の検出（競技間の移行時間）
            transitions = []
            
            # SWIM → BIKE トランジション
            if (record_data['swim_finish'] and record_data['bike_start'] and 
                record_data['bike_start'] > record_data['swim_finish']):
                t1_duration = (record_data['bike_start'] - record_data['swim_finish']).total_seconds()
                transitions.append({
                    'name': 'T1_transition',
                    'start': record_data['swim_finish'],
                    'finish': record_data['bike_start'],
                    'duration_seconds': t1_duration,
                    'phase_type': 'transition'
                })
            
            # BIKE → RUN トランジション
            if (record_data['bike_finish'] and record_data['run_start'] and 
                record_data['run_start'] > record_data['bike_finish']):
                t2_duration = (record_data['run_start'] - record_data['bike_finish']).total_seconds()
                transitions.append({
                    'name': 'T2_transition',
                    'start': record_data['bike_finish'],
                    'finish': record_data['run_start'],
                    'duration_seconds': t2_duration,
                    'phase_type': 'transition'
                })
            
            phases['transition_phases'] = transitions
            
            # 🆕 LAP時刻の解析（BL1, BL2...から区間推定）
            if record_data['laps']:
                lap_analysis = self._analyze_lap_times(record_data['laps'], phases)
                phases['lap_analysis'] = lap_analysis
            
            # 🆕 フィードバックグラフ用の時間軸データ生成
            phases['graph_segments'] = self._generate_graph_segments(phases)
            
        except Exception as e:
            print(f"区間判定エラー: {e}")
            # エラー時もbasestructureは返す
            phases['error'] = str(e)
        
        return phases

    def _analyze_lap_times(self, laps: dict, phases: dict) -> dict:
        """LAP時刻の解析（BL1, BL2...からの詳細区間推定）"""
        lap_analysis = {
            'total_laps': len(laps),
            'lap_times': [],
            'estimated_segments': []
        }
        
        try:
            # LAP時刻をソート
            sorted_laps = sorted(laps.items(), key=lambda x: x[1] if x[1] else datetime.min)
            
            for i, (lap_name, lap_time) in enumerate(sorted_laps):
                if lap_time is None:
                    continue
                    
                lap_info = {
                    'lap_name': lap_name,
                    'lap_time': lap_time,
                    'lap_number': i + 1
                }
                
                # 前のLAPとの時間差計算
                if i > 0:
                    prev_time = sorted_laps[i-1][1]
                    if prev_time:
                        interval_seconds = (lap_time - prev_time).total_seconds()
                        lap_info['interval_from_previous'] = interval_seconds
                
                # 競技開始からの経過時間
                if phases.get('total_phase') and phases['total_phase'].get('start'):
                    total_start = phases['total_phase']['start']
                    elapsed_seconds = (lap_time - total_start).total_seconds()
                    lap_info['elapsed_from_start'] = elapsed_seconds
                
                lap_analysis['lap_times'].append(lap_info)
            
            # 🆕 LAP時刻から競技区間の推定
            lap_analysis['estimated_segments'] = self._estimate_segments_from_laps(
                sorted_laps, phases
            )
            
        except Exception as e:
            lap_analysis['error'] = str(e)
            print(f"LAP解析エラー: {e}")
        
        return lap_analysis

    def _estimate_segments_from_laps(self, sorted_laps, phases: dict) -> list:
        """LAP時刻から競技区間を推定（実データBL/RL対応）"""
        segments = []
        
        try:
            if not sorted_laps or len(sorted_laps) < 1:
                return segments
            
            # 🆕 実データ対応：BL(バイクLAP)とRL(ランLAP)の区別
            bike_laps = [(name, time) for name, time in sorted_laps if name.upper().startswith('BL')]
            run_laps = [(name, time) for name, time in sorted_laps if name.upper().startswith('RL')]
            
            # バイクLAP区間
            if bike_laps:
                bike_laps.sort(key=lambda x: x[1])  # 時刻でソート
                segments.append({
                    'segment_type': 'bike_lap_segment',
                    'start_lap': bike_laps[0][0],
                    'end_lap': bike_laps[-1][0],
                    'start_time': bike_laps[0][1],
                    'end_time': bike_laps[-1][1],
                    'lap_count': len(bike_laps),
                    'confidence': 'high'  # BL列なので確実にバイク区間
                })
            
            # ランLAP区間
            if run_laps:
                run_laps.sort(key=lambda x: x[1])  # 時刻でソート
                segments.append({
                    'segment_type': 'run_lap_segment',
                    'start_lap': run_laps[0][0],
                    'end_lap': run_laps[-1][0],
                    'start_time': run_laps[0][1],
                    'end_time': run_laps[-1][1],
                    'lap_count': len(run_laps),
                    'confidence': 'high'  # RL列なので確実にラン区間
                })
            
            # 🆕 実データに基づく区間推定ロジック
            # START → SF：スイム区間
            # SF → BS：第1トランジション
            # BS → BL1〜BLn：バイク区間
            # BLn → RS：第2トランジション（バイク終了判定が必要な場合）
            # RS → RL1〜RLn → RF：ラン区間
            
            # より詳細な解析（実測値と組み合わせ）
            all_times = [(name, time) for name, time in sorted_laps if time]
            all_times.sort(key=lambda x: x[1])
            
            if all_times:
                segments.append({
                    'segment_type': 'total_lap_coverage',
                    'start_lap': all_times[0][0],
                    'end_lap': all_times[-1][0],
                    'start_time': all_times[0][1],
                    'end_time': all_times[-1][1],
                    'total_laps': len(all_times),
                    'bike_laps': len(bike_laps),
                    'run_laps': len(run_laps)
                })
            
        except Exception as e:
            print(f"実データ区間推定エラー: {e}")
        
        return segments

    def _generate_graph_segments(self, phases: dict) -> list:
        """フィードバックグラフ用の時間軸セグメント生成"""
        segments = []
        
        try:
            # 確定区間（実際のSTART/FINISH時刻から）
            for phase_name in ['swim_phase', 'bike_phase', 'run_phase']:
                phase = phases.get(phase_name)
                if phase and phase.get('start') and phase.get('finish'):
                    segments.append({
                        'segment_type': phase['phase_type'],
                        'start_time': phase['start'],
                        'end_time': phase['finish'],
                        'duration_seconds': phase['duration_seconds'],
                        'confidence': 'high',  # 実測値なので高信頼度
                        'background_color': self._get_phase_color(phase['phase_type'])
                    })
            
            # トランジション区間
            for transition in phases.get('transition_phases', []):
                segments.append({
                    'segment_type': 'transition',
                    'start_time': transition['start'],
                    'end_time': transition['finish'],
                    'duration_seconds': transition['duration_seconds'],
                    'confidence': 'high',
                    'background_color': '#f0f0f0'  # グレー
                })
            
            # LAP推定区間（実測値がない場合の補完）
            lap_analysis = phases.get('lap_analysis', {})
            if lap_analysis.get('estimated_segments') and not segments:
                # 実測値がない場合のみLAP推定を使用
                for est_segment in lap_analysis['estimated_segments']:
                    segments.append({
                        'segment_type': est_segment['segment_type'],
                        'start_time': est_segment['start_time'],
                        'end_time': est_segment['end_time'],
                        'confidence': 'medium',  # 推定値なので中信頼度
                        'background_color': self._get_phase_color(
                            est_segment['segment_type'].replace('estimated_', '')
                        )
                    })
            
            # 時間順にソート
            segments.sort(key=lambda x: x['start_time'])
            
        except Exception as e:
            print(f"グラフセグメント生成エラー: {e}")
        
        return segments

    def _get_phase_color(self, phase_type: str) -> str:
        """競技フェーズの背景色を取得"""
        colors = {
            'swim': '#e3f2fd',    # 水色（SWIM）
            'bike': '#fff3e0',    # オレンジ（BIKE）
            'run': '#e8f5e8',     # 緑（RUN）
            'transition': '#f5f5f5'  # グレー（トランジション）
        }
        return colors.get(phase_type, '#ffffff')  # デフォルトは白# app/services/flexible_csv_service.py に追加するメソッド

    async def process_race_record_data(
        self,
        race_files: List[UploadFile],
        competition_id: str,
        db: Session,
        overwrite: bool = True
    ) -> Dict[str, Any]:
        """
        大会記録データ処理（複数CSV統合対応）
        
        仕様書2.5準拠:
        - 複数CSVファイル対応
        - ゼッケン番号（"No."列）による統合
        - 可変LAP構成（BL1, BL2...）対応
        - SWIM/BIKE/RUN区間自動判定
        """
        try:
            # 大会存在チェック
            from app.models.competition import Competition, RaceRecord
            competition = db.query(Competition).filter_by(competition_id=competition_id).first()
            if not competition:
                raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
            
            # 上書き処理：既存大会記録を削除
            if overwrite and competition_id:
                deleted_count = db.query(RaceRecord).filter_by(competition_id=competition_id).delete()
                db.commit()
                print(f"既存大会記録{deleted_count}件を削除しました")
            
            # バッチID生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_id = f"{timestamp}_race_records_{len(race_files)}files"
            
            # 全CSVファイルを読み込み・統合
            all_records = {}  # ゼッケン番号をキーとした統合データ
            lap_columns = set()  # 検出されたLAP列名
            total_files_processed = 0
            total_csv_records = 0
            errors = []
            
            for file_idx, file in enumerate(race_files):
                try:
                    print(f"Processing file {file_idx + 1}/{len(race_files)}: {file.filename}")
                    
                    # ファイル読み込み
                    content = await file.read()
                    if not content:
                        errors.append(f"{file.filename}: 空ファイル")
                        continue
                    
                    # エンコーディング自動検出
                    detected_encoding = None
                    for encoding in ['utf-8', 'shift_jis', 'cp932', 'iso-8859-1']:
                        try:
                            decoded_content = content.decode(encoding)
                            detected_encoding = encoding
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if detected_encoding is None:
                        errors.append(f"{file.filename}: 文字コード認識失敗")
                        continue
                    
                    print(f"  使用エンコーディング: {detected_encoding}")
                    
                    # CSVをDataFrameに読み込み
                    df = pd.read_csv(io.StringIO(decoded_content))
                    
                    if df.empty:
                        errors.append(f"{file.filename}: データが空")
                        continue
                    
                    total_csv_records += len(df)
                    
                    # 必須列チェック：ゼッケン番号（"No."列）
                    bib_number_col = None
                    for col in df.columns:
                        if col.strip().lower() in ['no.', 'no', 'bib', 'bib_number', 'ゼッケン', 'ゼッケン番号']:
                            bib_number_col = col
                            break
                    
                    if bib_number_col is None:
                        errors.append(f"{file.filename}: ゼッケン番号列（'No.'）が見つかりません")
                        continue
                    
                    # LAP列の検出（BL1, BL2, BL3...等 + RL1, RL2...等）
                    file_lap_columns = []
                    for col in df.columns:
                        col_upper = col.strip().upper()
                        # バイクLAP（BL1, BL2...）とランLAP（RL1, RL2...）両方を検出
                        if ((col_upper.startswith('BL') or col_upper.startswith('RL')) and 
                            len(col_upper) >= 3 and col_upper[2:].isdigit()):
                            file_lap_columns.append(col)
                            lap_columns.add(col)
                    
                    print(f"  検出されたLAP列: {file_lap_columns}")
                    
                    # 各行を処理してゼッケン番号で統合
                    for _, row in df.iterrows():
                        bib_number = str(row[bib_number_col]).strip()
                        
                        if not bib_number or bib_number == 'nan':
                            continue
                        
                        # 統合データ構造の初期化
                        if bib_number not in all_records:
                            all_records[bib_number] = {
                                'bib_number': bib_number,
                                'swim_start': None,
                                'swim_finish': None,
                                'bike_start': None,
                                'bike_finish': None,
                                'run_start': None,
                                'run_finish': None,
                                'laps': {},
                                'source_files': []
                            }
                        
                        record = all_records[bib_number]
                        record['source_files'].append(file.filename)
                        
                        # 🆕 実データ対応：短縮形式の列名マッピング
                        for col in df.columns:
                            col_clean = col.strip()
                            col_upper = col_clean.upper()
                            value = row[col]
                            
                            if pd.isna(value):
                                continue
                            
                            # 時刻データの解析
                            time_value = self._parse_race_time(value)
                            if time_value is None:
                                continue
                            
                            # 🆕 実データの短縮形式に対応
                            if col_upper == 'START':
                                record['swim_start'] = time_value
                            elif col_upper == 'SF':  # Swim Finish
                                record['swim_finish'] = time_value
                            elif col_upper == 'BS':  # Bike Start
                                record['bike_start'] = time_value
                            elif col_upper == 'RS':  # Run Start
                                record['run_start'] = time_value
                            elif col_upper == 'RF':  # Run Finish
                                record['run_finish'] = time_value
                            
                            # レガシー列名も念のため対応
                            elif 'swim' in col_upper and 'start' in col_upper:
                                record['swim_start'] = time_value
                            elif 'swim' in col_upper and ('finish' in col_upper or 'end' in col_upper):
                                record['swim_finish'] = time_value
                            elif 'bike' in col_upper and 'start' in col_upper:
                                record['bike_start'] = time_value
                            elif 'bike' in col_upper and ('finish' in col_upper or 'end' in col_upper):
                                record['bike_finish'] = time_value
                            elif 'run' in col_upper and 'start' in col_upper:
                                record['run_start'] = time_value
                            elif 'run' in col_upper and ('finish' in col_upper or 'end' in col_upper):
                                record['run_finish'] = time_value
                        
                        # LAP データ抽出
                        for lap_col in file_lap_columns:
                            lap_value = row[lap_col]
                            if not pd.isna(lap_value):
                                lap_time = self._parse_race_time(lap_value)
                                if lap_time:
                                    record['laps'][lap_col] = lap_time
                    
                    total_files_processed += 1
                    print(f"  ✅ {file.filename}: {len(df)}件の記録を処理")
                    
                except Exception as e:
                    error_msg = f"{file.filename}: 処理エラー - {str(e)}"
                    errors.append(error_msg)
                    print(f"  ❌ {error_msg}")
                    continue
            
            if not all_records:
                raise HTTPException(status_code=400, detail="処理可能な大会記録が見つかりませんでした")
            
            # データベースに保存
            saved_count = 0
            failed_count = 0
            
            for bib_number, record_data in all_records.items():
                try:
                    # SWIM/BIKE/RUN区間の自動判定
                    phases = self._detect_race_phases(record_data)
                    
                    # RaceRecordエンティティ作成
                    race_record = RaceRecord(
                        competition_id=competition_id,
                        user_id=None,  # マッピング後に設定
                        race_number=bib_number,
                        swim_start_time=record_data['swim_start'],
                        swim_finish_time=record_data['swim_finish'],
                        bike_start_time=record_data['bike_start'],
                        bike_finish_time=record_data['bike_finish'],
                        run_start_time=record_data['run_start'],
                        run_finish_time=record_data['run_finish'],
                        notes=f"LAP数: {len(record_data['laps'])}, ソースファイル: {', '.join(record_data['source_files'])}"
                    )
                    
                    # 🆕 LAP データと区間情報を設定
                    if record_data['laps']:
                        race_record.set_lap_data(record_data['laps'])
                    
                    if phases:
                        race_record.set_calculated_phases(phases)
                    
                    db.add(race_record)
                    saved_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    error_msg = f"ゼッケン{bib_number}: 保存エラー - {str(e)}"
                    errors.append(error_msg)
                    print(f"❌ {error_msg}")
            
            # バッチ記録作成
            from app.models.flexible_sensor_data import UploadBatch, SensorType, UploadStatus
            
            total_file_size = sum([len(await f.read()) for f in race_files])
            
            batch = UploadBatch(
                batch_id=batch_id,
                sensor_type=SensorType.OTHER,  # 大会記録用
                competition_id=competition_id,
                file_name=f"race_records_{len(race_files)}files.csv",
                file_size=total_file_size,
                total_records=total_csv_records,
                success_records=saved_count,
                failed_records=failed_count,
                status=UploadStatus.SUCCESS if failed_count == 0 else UploadStatus.PARTIAL,
                uploaded_by=db.query(AdminUser).first().admin_id,  # 要修正
                notes=f"統合LAP列: {', '.join(sorted(lap_columns))}" if lap_columns else None
            )
            db.add(batch)
            
            db.commit()
            
            # 結果メッセージ作成
            message = f"大会記録を{saved_count}件統合処理しました"
            if failed_count > 0:
                message += f"（失敗: {failed_count}件）"
            
            return {
                "success": saved_count > 0,
                "message": message,
                "total_files": len(race_files),
                "processed_files": total_files_processed,
                "total_csv_records": total_csv_records,
                "saved_records": saved_count,
                "failed_records": failed_count,
                "detected_lap_columns": sorted(lap_columns),
                "batch_id": batch_id,
                "errors": errors[:10] if errors else []  # 最初の10件のみ
            }
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            error_message = f"大会記録処理エラー: {str(e)}"
            print(error_message)
            raise HTTPException(status_code=500, detail=error_message)

    def _parse_race_time(self, time_value) -> Optional[datetime]:
        """レース時刻の柔軟な解析"""
        if pd.isna(time_value):
            return None
        
        time_str = str(time_value).strip()
        if not time_str or time_str.lower() in ['nan', '', 'null']:
            return None
        
        try:
            # 複数の時刻フォーマットに対応
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y/%m/%d %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
                "%H:%M:%S",
                "%H:%M",
                "%Y-%m-%d",
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue
            
            # pandas to_datetimeでフォールバック
            return pd.to_datetime(time_str)
            
        except Exception as e:
            print(f"時刻解析エラー: {time_str} - {e}")
            return None

    def _detect_race_phases(self, record_data: dict) -> dict:
        """SWIM/BIKE/RUN区間自動判定"""
        phases = {
            'swim_phase': None,
            'bike_phase': None, 
            'run_phase': None,
            'total_phase': None
        }
        
        try:
            # 全体の開始・終了時刻
            start_times = [record_data['swim_start'], record_data['bike_start'], record_data['run_start']]
            finish_times = [record_data['swim_finish'], record_data['bike_finish'], record_data['run_finish']]
            
            start_times = [t for t in start_times if t is not None]
            finish_times = [t for t in finish_times if t is not None]
            
            if start_times and finish_times:
                total_start = min(start_times)
                total_finish = max(finish_times)
                phases['total_phase'] = {'start': total_start, 'finish': total_finish}
            
            # 各競技フェーズ
            if record_data['swim_start'] and record_data['swim_finish']:
                phases['swim_phase'] = {
                    'start': record_data['swim_start'],
                    'finish': record_data['swim_finish']
                }
            
            if record_data['bike_start'] and record_data['bike_finish']:
                phases['bike_phase'] = {
                    'start': record_data['bike_start'],
                    'finish': record_data['bike_finish']
                }
            
            if record_data['run_start'] and record_data['run_finish']:
                phases['run_phase'] = {
                    'start': record_data['run_start'],
                    'finish': record_data['run_finish']
                }
            
        except Exception as e:
            print(f"区間判定エラー: {e}")
        
        return phases