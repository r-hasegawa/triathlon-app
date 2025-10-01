"""
app/services/flexible_csv_service.py

実データ対応版（WBGT実装含む）
"""

import pandas as pd
import io
from io import BytesIO
import chardet
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.competition import Competition, RaceRecord
from app.models.user import AdminUser
from app.models.flexible_sensor_data import (
    FlexibleSensorMapping,
    SkinTemperatureData, CoreTemperatureData, 
    HeartRateData, WBGTData, SensorDataStatus, SensorType,
    UploadBatch, SensorType, UploadStatus
)
from app.schemas.sensor_data import (
    UploadResponse, MappingResponse,
    DataSummaryResponse, MappingStatusResponse
)

class FlexibleCSVService:

    def _parse_time_with_competition_date(self, time_value: str, competition_date: datetime) -> Optional[datetime]:
        """
        時刻データと競技日付を結合してdatetimeを生成（修正版）
        
        Args:
            time_value: 時刻文字列（例："17:43:38", "9:15:30", "8:00:00"）
            competition_date: 競技の開催日（Competition.dateから取得）
        
        Returns:
            datetime: 結合された日時データ、失敗時はNone
        """
        if not time_value or pd.isna(time_value):
            return None
            
        try:
            # 時刻文字列を正規化
            time_str = str(time_value).strip()
            
            # 空文字チェック
            if not time_str or time_str.lower() in ['nan', 'null', '']:
                return None
            
            # 時刻フォーマットのパターンマッチング
            import re
            
            # HH:MM:SS形式（例："17:43:38", "8:00:00"）
            time_pattern = re.match(r'(\d{1,2}):(\d{2}):(\d{2})', time_str)
            if time_pattern:
                hour, minute, second = map(int, time_pattern.groups())
                
                # datetimeオブジェクトを直接作成（より安全）
                from datetime import datetime
                combined_datetime = datetime(
                    year=competition_date.year,
                    month=competition_date.month,
                    day=competition_date.day,
                    hour=hour,
                    minute=minute,
                    second=second
                )
                
                return combined_datetime
            
            # pandas で時刻解析を試行
            try:
                parsed_time = pd.to_datetime(time_str, format='%H:%M:%S')
                
                # datetimeオブジェクトを直接作成
                combined_datetime = datetime(
                    year=competition_date.year,
                    month=competition_date.month,
                    day=competition_date.day,
                    hour=parsed_time.hour,
                    minute=parsed_time.minute,
                    second=parsed_time.second
                )
                
                return combined_datetime
            except:
                pass
            
            # 最後の手段：pandas汎用パーサー
            try:
                parsed = pd.to_datetime(time_str)
                
                combined_datetime = datetime(
                    year=competition_date.year,
                    month=competition_date.month,
                    day=competition_date.day,
                    hour=parsed.hour,
                    minute=parsed.minute,
                    second=parsed.second
                )
                
                return combined_datetime
            except:
                pass
            
            print(f"時刻解析失敗: '{time_str}'")
            return None
            
        except Exception as e:
            print(f"時刻解析エラー: {time_value} -> {e}")
            return None


    def process_race_record_csv(
        self,
        csv_string: str,
        competition_id: str,
        batch_id: str,
        filename: str
    ) -> dict:
        """大会記録データ処理（upload_batch_id対応版）"""
        try:
            # 競技情報取得
            from app.models.competition import Competition
            competition = self.db.query(Competition).filter_by(competition_id=competition_id).first()
            if not competition:
                return {
                    "filename": filename,
                    "status": "error", 
                    "message": f"大会ID '{competition_id}' が見つかりません"
                }
            
            # 競技日付取得
            competition_date = competition.date
            if not competition_date:
                return {
                    "filename": filename,
                    "status": "error",
                    "message": "競技日付が設定されていません"
                }
            
            print(f"競技日付: {competition_date}")
            
            # CSV読み込み
            df = pd.read_csv(io.StringIO(csv_string))
            df.columns = df.columns.str.strip()
            
            # ゼッケン番号列の確認
            race_number_col = None
            for col in ['No.', 'NO.', 'no.', 'No', 'race_number', 'bib_number', 'ゼッケン']:
                if col in df.columns:
                    race_number_col = col
                    break
            
            if not race_number_col:
                return {
                    "filename": filename,
                    "status": "error",
                    "message": f"ゼッケン番号列が見つかりません。列: {list(df.columns)}"
                }
            
            # 時刻列のマッピング定義（柔軟なマッチング）
            time_field_mapping = {
                'swim_start_time': ['SWIM-START', 'START', 'SWIM_START', 'Swim Start', 'swim_start'],
                'swim_finish_time': ['SWIM-FINISH', 'SF', 'SWIM_FINISH', 'Swim Finish', 'swim_finish'],
                'bike_start_time': ['BIKE-START', 'BS', 'BIKE_START', 'Bike Start', 'bike_start'], 
                'bike_finish_time': ['BIKE-FINISH', 'BF', 'BIKE_FINISH', 'Bike Finish', 'bike_finish'],
                'run_start_time': ['RUN-START', 'RS', 'RUN_START', 'Run Start', 'run_start'],
                'run_finish_time': ['RUN-FINISH', 'RF', 'RUN_FINISH', 'Run Finish', 'run_finish']
            }
            
            # LAP列の検出
            lap_columns = [col for col in df.columns if any(prefix in col.upper() for prefix in ['BL', 'RL', 'LAP'])]
            print(f"検出されたLAP列: {lap_columns}")
            
            processed = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    race_number = str(row.get(race_number_col, '')).strip()
                    
                    if not race_number or race_number.lower() in ['nan', '', 'none']:
                        continue
                    
                    # 基本データ構築
                    race_record_data = {
                        'competition_id': competition_id,
                        'race_number': race_number,
                        'upload_batch_id': batch_id  # 🆕 upload_batch_id追加
                    }
                    
                    # 各競技の時刻データを処理
                    for field_name, possible_columns in time_field_mapping.items():
                        time_value = None
                        
                        # 列名マッチング
                        for col in possible_columns:
                            if col in df.columns:
                                time_value = row.get(col)
                                if time_value and pd.notna(time_value):
                                    break
                        
                        # 時刻データがある場合、競技日付と結合
                        if time_value and pd.notna(time_value):
                            combined_datetime = self._parse_time_with_competition_date(
                                time_value, competition_date
                            )
                            if combined_datetime:
                                race_record_data[field_name] = combined_datetime
                                print(f"  {field_name}: {time_value} -> {combined_datetime}")
                    
                    # LAP時刻データの処理
                    lap_data = {}
                    for lap_col in lap_columns:
                        lap_time_value = row.get(lap_col)
                        if lap_time_value and pd.notna(lap_time_value):
                            combined_lap_time = self._parse_time_with_competition_date(
                                lap_time_value, competition_date
                            )
                            if combined_lap_time:
                                lap_data[lap_col] = combined_lap_time.isoformat()
                    
                    # RaceRecord作成
                    from app.models.competition import RaceRecord
                    race_record = RaceRecord(**race_record_data)
                    
                    # LAP データ設定
                    if lap_data:
                        import json
                        race_record.lap_data = json.dumps(lap_data)
                    
                    self.db.add(race_record)
                    processed += 1
                    
                    print(f"保存成功: ゼッケン{race_number} - 時刻データ: {len([k for k, v in race_record_data.items() if 'time' in k and v])}件")
                    
                except Exception as e:
                    error_msg = f"行{index+1}: {str(e)}"
                    errors.append(error_msg)
                    print(f"処理エラー: {error_msg}")
                    continue
            
            # コミット実行
            self.db.commit()
            
            return {
                "filename": filename,
                "status": "success" if processed > 0 else "warning",
                "message": f"処理完了: {processed}件保存, {len(errors)}件エラー",
                "processed_records": processed,
                "error_records": len(errors),
                "errors": errors[:10],
                "competition_date_used": competition_date.isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "filename": filename,
                "status": "error",
                "message": f"CSV処理失敗: {str(e)}"
            }

    def process_wbgt_csv(
        self,
        csv_string: str,
        competition_id: str,
        batch_id: str,
        filename: str
    ) -> dict:
        """WBGT環境データ処理"""
        try:
            # CSV読み込み
            df = pd.read_csv(io.StringIO(csv_string))
            
            # 列名の正規化
            df.columns = df.columns.str.strip()
            
            processed = 0
            errors = []
            
            # 列マッピング
            column_mapping = self._normalize_wbgt_columns(df.columns)
            
            if not column_mapping:
                return {
                    "filename": filename,
                    "status": "error",
                    "message": f"WBGT必須列が見つかりません。現在の列: {list(df.columns)}"
                }
            
            # UploadBatch作成
            upload_batch = UploadBatch(
                batch_id=batch_id,
                sensor_type=SensorType.WBGT,
                file_name=filename,
                competition_id=competition_id,
                total_records=len(df),
                status=UploadStatus.PROCESSING,
                uploaded_at=datetime.now()
            )
            self.db.add(upload_batch)
            
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
                    
                    # WBGTDataオブジェクト作成
                    wbgt_data = WBGTData(
                        timestamp=datetime_value,
                        wbgt_value=wbgt_value,
                        air_temperature=air_temp,
                        humidity=humidity,
                        globe_temperature=globe_temp,
                        competition_id=competition_id,
                        upload_batch_id=batch_id,
                        uploaded_at=datetime.now()
                    )
                    
                    self.db.add(wbgt_data)
                    processed += 1
                    
                except Exception as e:
                    errors.append(f"行{index+1}: {str(e)}")
                    continue
            
            # バッチ状態更新
            upload_batch.success_records = processed
            upload_batch.failed_records = len(errors)
            upload_batch.status = UploadStatus.SUCCESS if processed > 0 else UploadStatus.FAILED
            
            self.db.commit()
            
            return {
                "filename": filename,
                "status": "success" if processed > 0 else "failed",
                "total": len(df),
                "success": processed,
                "failed": len(errors),
                "batch_id": batch_id
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "filename": filename,
                "status": "error",
                "message": f"処理エラー: {str(e)}"
            }

    # ヘルパーメソッド
    def _normalize_wbgt_columns(self, columns):
        """WBGT列名の正規化"""
        mapping = {}
        for col in columns:
            col_lower = col.lower().strip()
            if '日付' in col or 'date' in col_lower:
                mapping['date'] = col
            elif '時刻' in col or 'time' in col_lower:
                mapping['time'] = col
            elif 'wbgt' in col_lower:
                mapping['wbgt'] = col
            elif '気温' in col or 'air' in col_lower:
                mapping['air_temperature'] = col
            elif '湿度' in col or 'humidity' in col_lower:
                mapping['humidity'] = col
            elif '黒球' in col or 'globe' in col_lower:
                mapping['globe_temperature'] = col
        
        return mapping if 'date' in mapping and 'time' in mapping and 'wbgt' in mapping else None

    def _combine_date_time(self, row, column_mapping):
        """日付と時刻を結合"""
        try:
            date_value = row.get(column_mapping.get('date'))
            time_value = row.get(column_mapping.get('time'))
            
            if pd.isna(date_value) or pd.isna(time_value):
                return None
            
            # 日付と時刻を文字列として結合
            datetime_str = f"{date_value} {time_value}"
            return pd.to_datetime(datetime_str)
        except:
            return None

    def _safe_float(self, value):
        """安全な数値変換"""
        try:
            if pd.isna(value):
                return None
            return float(value)
        except:
            return None

    def _detect_encoding(self, content: bytes) -> str:
        """ファイルのエンコーディングを自動検出"""
        result = chardet.detect(content)
        encoding = result.get('encoding', 'utf-8')
        confidence = result.get('confidence', 0)
        
        print(f"文字コード検出: {encoding} (信頼度: {confidence:.2f})")
        
        # エンコーディングの正規化
        if encoding and encoding.lower() in ['shift_jis', 'shift-jis', 'cp932']:
            return 'shift_jis'
        elif encoding and encoding.lower() in ['utf-8-sig', 'utf-8']:
            return 'utf-8'
        elif encoding and encoding.lower() in ['cp1252', 'iso-8859-1']:
            return 'cp1252'
        else:
            # デフォルトはUTF-8
            return 'utf-8'

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
                total_records=len(df),
                success_records=processed,
                failed_records=len(errors),
                status=UploadStatus.SUCCESS if not errors else UploadStatus.PARTIAL
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
        mapping_file, 
        competition_id: str, 
        db: Session,
        batch_id: str,  # 🆕 必須パラメータに変更
        overwrite: bool = True
    ) -> dict:
        """マッピングデータ処理（不要列削除、upload_batch_id追加）"""
        
        try:
            # 大会存在チェック  
            from app.models.competition import Competition
            competition = db.query(Competition).filter_by(competition_id=competition_id).first()
            if not competition:
                raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
            
            # 既存マッピング削除（overwriteが有効な場合）
            if overwrite:
                # 1. 既存マッピングを取得して、batch_idを収集
                existing_mappings = db.query(FlexibleSensorMapping).filter_by(
                    competition_id=competition_id
                ).all()
                
                existing_batch_ids = set()  # 重複を避けるためsetを使用
                for mapping in existing_mappings:
                    if mapping.upload_batch_id:
                        existing_batch_ids.add(mapping.upload_batch_id)
                
                # 2. マッピングデータを削除
                existing_count = db.query(FlexibleSensorMapping).filter_by(
                    competition_id=competition_id
                ).delete()
                
                # 3. 対応するUploadBatchレコードも削除
                if existing_batch_ids:
                    deleted_batch_count = db.query(UploadBatch).filter(
                        UploadBatch.batch_id.in_(existing_batch_ids),
                        UploadBatch.sensor_type == SensorType.OTHER
                    ).delete(synchronize_session=False)
                
                db.commit()
            
            # CSVファイル読み込み
            content = await mapping_file.read()
            encoding = self._detect_encoding(content)
            
            try:
                df = pd.read_csv(BytesIO(content), encoding=encoding)
                print(f"CSV読み込み成功: {encoding}")
            except UnicodeDecodeError as e:
                print(f"エンコーディングエラー({encoding}): {e}")
                for fallback_encoding in ['utf-8', 'shift_jis', 'cp932']:
                    try:
                        df = pd.read_csv(BytesIO(content), encoding=fallback_encoding)
                        print(f"{fallback_encoding}で再試行成功")
                        break
                    except Exception:
                        continue
                else:
                    raise HTTPException(status_code=400, detail="CSVファイル読み込み失敗")
            
            if df.empty:
                raise HTTPException(status_code=400, detail="CSVファイルが空です")
            
            # 列名の空白除去と正規化
            df.columns = df.columns.str.strip()
            
            print(f"📊 CSV情報:")
            print(f"   - ファイル名: {mapping_file.filename}")
            print(f"   - 行数: {len(df)}")
            print(f"   - 列名: {list(df.columns)}")
            
            # 必須列チェック
            if 'user_id' not in df.columns:
                raise HTTPException(status_code=400, detail="user_id列が必要です")
            
            # 認識するセンサー列（不要列除外）
            recognized_sensor_columns = {
                'skin_temp_sensor_id': SensorType.SKIN_TEMPERATURE,
                'core_temp_sensor_id': SensorType.CORE_TEMPERATURE,
                'heart_rate_sensor_id': SensorType.HEART_RATE,
                'skin_temperature_sensor_id': SensorType.SKIN_TEMPERATURE,
                'core_temperature_sensor_id': SensorType.CORE_TEMPERATURE
            }
            
            processed = 0
            skipped = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    user_id = str(row['user_id']).strip()
                    
                    if not user_id or pd.isna(user_id) or user_id.lower() in ['nan', '']:
                        skipped += 1
                        continue
                    
                    # 各センサータイプについて処理
                    for csv_column, sensor_type in recognized_sensor_columns.items():
                        if csv_column not in df.columns:
                            continue
                        
                        sensor_id = row.get(csv_column)
                        
                        if pd.isna(sensor_id) or not str(sensor_id).strip():
                            continue
                        
                        sensor_id = str(sensor_id).strip()
                        
                        # 🆕 upload_batch_id を含めてマッピング作成
                        mapping = FlexibleSensorMapping(
                            sensor_id=sensor_id,
                            sensor_type=sensor_type,
                            user_id=user_id,
                            competition_id=competition_id,
                            upload_batch_id=batch_id  # 🆕 追加
                        )
                        
                        db.add(mapping)
                        processed += 1
                        
                except Exception as e:
                    errors.append(f"行 {idx+2}: {str(e)}")
                    skipped += 1
                    continue
            
            db.commit()
            
            return {
                "success": True,
                "message": f"マッピング処理完了: {processed}件登録",
                "total_records": len(df),
                "processed_records": processed,
                "skipped_records": skipped,
                "errors": errors[:20]  # 最大20件のエラーのみ返す
            }
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"マッピング処理エラー: {str(e)}")


    # 🆕 大会記録マッピング適用処理（改善版）
    async def apply_race_number_mapping(
        self,
        competition_id: str,
        db: Session
    ) -> dict:
        """大会記録マッピング適用（改善版）"""
        
        try:
            from app.models.competition import RaceRecord
            from app.models.flexible_sensor_data import FlexibleSensorMapping
            
            # 🆕 RACE_RECORDタイプのマッピングを取得
            race_mappings = db.query(FlexibleSensorMapping).filter_by(
                competition_id=competition_id,
                sensor_type=SensorType.RACE_RECORD
            ).all()
            
            print(f"🏃 大会記録マッピング数: {len(race_mappings)}")
            
            applied_count = 0
            errors = []
            
            for mapping in race_mappings:
                race_number = mapping.sensor_id  # 🔄 sensor_idから取得
                user_id = mapping.user_id
                
                print(f"🔍 処理中: race_number={race_number}, user_id={user_id}")
                
                # 対応する大会記録を検索・更新
                race_records = db.query(RaceRecord).filter_by(
                    competition_id=competition_id,
                    race_number=race_number,
                    user_id=None  # 未マッピングのもののみ
                ).all()
                
                for record in race_records:
                    record.user_id = user_id
                    applied_count += 1
                    print(f"✅ 大会記録マッピング適用: race_number={race_number} → user_id={user_id}")
            
            db.commit()
            
            return {
                "success": True,
                "applied_race_records": applied_count,
                "total_mappings": len(race_mappings),
                "message": f"大会記録マッピング適用完了: {applied_count}件",
                "errors": errors
            }
            
        except Exception as e:
            db.rollback()
            error_message = f"大会記録マッピング適用エラー: {str(e)}"
            print(f"❌ {error_message}")
            return {
                "success": False,
                "applied_race_records": 0,
                "errors": [error_message]
            }

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
                total_records=len(df),
                success_records=processed,
                failed_records=len(errors),
                status=UploadStatus.SUCCESS if len(errors) == 0 else UploadStatus.PARTIAL
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

    # app/services/flexible_csv_service.py - 簡素版（上書き機能削除）

    async def process_race_record_data(
        self,
        race_files: List[UploadFile],
        competition_id: str,
        db: Session,
        batch_id: str  # 🆕 batch_idパラメータを追加
    ) -> dict:
        """大会記録データ処理（複数CSVファイル対応、batch_id追加版）"""
        
        try:
            # 大会存在チェック
            from app.models.competition import Competition
            from app.models.user import AdminUser
            
            competition = db.query(Competition).filter_by(competition_id=competition_id).first()
            if not competition:
                raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
            
            competition_date = competition.date
            print(f"使用する競技日付: {competition_date}")
            
            # 処理統計
            total_files_processed = 0
            total_csv_records = 0
            saved_count = 0
            failed_count = 0
            all_errors = []
            
            # 一時的にself.dbを設定（互換性のため）
            self.db = db
            
            for file_idx, file in enumerate(race_files):
                try:
                    print(f"ファイル処理 {file_idx + 1}/{len(race_files)}: {file.filename}")
                    
                    # ファイル読み込み
                    content = await file.read()
                    if not content:
                        all_errors.append(f"{file.filename}: 空ファイル")
                        continue
                    
                    # エンコーディング自動検出と読み込み
                    csv_string = None
                    for encoding in ['utf-8', 'shift_jis', 'cp932', 'iso-8859-1']:
                        try:
                            csv_string = content.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if csv_string is None:
                        all_errors.append(f"{file.filename}: 文字コード認識失敗")
                        continue
                    
                    # CSVファイル単位で処理（batch_idを渡す）
                    result = self.process_race_record_csv(
                        csv_string=csv_string,
                        competition_id=competition_id,
                        batch_id=batch_id,  # 🆕 batch_idを渡す
                        filename=file.filename
                    )
                    
                    # 統計更新
                    total_files_processed += 1
                    if result["status"] in ["success", "warning"]:
                        saved_count += result.get("processed_records", 0)
                        failed_count += result.get("error_records", 0)
                        if result.get("errors"):
                            all_errors.extend([f"{file.filename}: {err}" for err in result["errors"]])
                    else:
                        all_errors.append(f"{file.filename}: {result['message']}")
                    
                    print(f"  結果: {result['status']} - {result['message']}")
                    
                except Exception as e:
                    all_errors.append(f"{file.filename}: 予期しないエラー - {str(e)}")
                    print(f"ファイル処理エラー: {e}")
            
            # 最終結果
            success = saved_count > 0
            
            return {
                "success": success,
                "message": f"大会記録アップロード完了: {saved_count}件保存, {failed_count}件エラー",
                "total_files": len(race_files),
                "processed_files": total_files_processed,
                "saved_count": saved_count,
                "failed_count": failed_count,
                "total_csv_records": saved_count + failed_count,
                "errors": all_errors[:20]  # 最大20件のエラー
            }
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"大会記録処理エラー: {str(e)}")

    def _is_likely_time_data(self, time_str: str) -> bool:
        """文字列が時刻データの可能性が高いかチェック"""
        if not time_str or len(time_str.strip()) == 0:
            return False
        
        time_str = time_str.strip()
        
        # 明らかに時刻ではないパターンを除外
        non_time_patterns = [
            '選手_', '部門', '男性', '女性', '県', '完走', 'DNS', 'DNF', 'DQ',
            'LONG', 'SHORT', 'スプリント', 'オリンピック'
        ]
        
        for pattern in non_time_patterns:
            if pattern in time_str:
                return False
        
        # 数字のみで構成され、かつ1-4桁の場合は時刻の可能性が低い
        # （ただし、秒数や分数の場合もあるので完全除外はしない）
        if time_str.isdigit():
            num = int(time_str)
            # ゼッケン番号や年齢の可能性が高い範囲
            if 1 <= num <= 9999:
                # さらに詳細チェック：時刻として妥当かどうか
                if num <= 23:  # 時間として妥当
                    return True
                elif num <= 59:  # 分・秒として妥当
                    return True
                else:
                    return False
        
        # 時刻らしいパターン
        time_patterns = [
            ':',  # HH:MM:SS形式
            '-',  # 日付形式
            '/',  # 日付形式
            '.'   # 小数点（秒の小数部）
        ]
        
        return any(pattern in time_str for pattern in time_patterns)

    def _parse_race_time(self, time_value) -> Optional[datetime]:
        """レース時刻の柔軟な解析（エラーログ出力抑制版）"""
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
                "%H:%M:%S.%f",
                "%M:%S",  # 分:秒
                "%S.%f"   # 秒.ミリ秒
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue
            
            # pandas to_datetimeで最後の試行
            return pd.to_datetime(time_str, errors='coerce')
            
        except Exception as e:
            # エラーログを出力しない（デバッグ時のみ）
            # print(f"時刻解析エラー: {time_str} - {e}")
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


    def process_heart_rate_tcx(
        self,
        tcx_string: str,
        competition_id: str,
        batch_id: str,
        filename: str,
        sensor_id: str = "GARMIN_DEFAULT"
    ) -> Dict[str, Any]:
        """
        Garmin TCXファイルの心拍データ処理（日本時間変換対応）
        
        仕様変更：
        - TCXの時刻データは通常UTCであることが多い
        - 日本の標準時差は+9時間（UTC+9）
        - DBに格納する際は日本時間（JST）に変換する
        """
        try:
            # XML解析
            root = ET.fromstring(tcx_string)
            
            # TCXの名前空間
            namespaces = {
                'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'
            }
            
            processed_count = 0
            failed_count = 0
            errors = []
            trackpoints_data = []
            
            # 全てのTrackpointを検索
            trackpoints = root.findall('.//tcx:Trackpoint', namespaces)
            
            print(f"📊 TCX解析開始: {filename}")
            print(f"   - センサーID: {sensor_id}")
            print(f"   - Trackpoint数: {len(trackpoints)}")
            
            for idx, trackpoint in enumerate(trackpoints):
                try:
                    # 時刻取得
                    time_elem = trackpoint.find('tcx:Time', namespaces)
                    if time_elem is None:
                        failed_count += 1
                        continue
                    
                    time_str = time_elem.text
                    
                    # 🔧 日本時間変換処理
                    # TCXの時刻はISO8601形式（例: 2023-07-15T08:30:00Z）
                    parsed_time = self._parse_tcx_time_to_jst(time_str)
                    
                    if parsed_time is None:
                        errors.append(f"Trackpoint {idx+1}: 時刻解析失敗 ({time_str})")
                        failed_count += 1
                        continue
                    
                    # 心拍数取得
                    hr_elem = trackpoint.find('.//tcx:HeartRateBpm/tcx:Value', namespaces)
                    heart_rate = None
                    if hr_elem is not None:
                        try:
                            heart_rate = int(hr_elem.text)
                        except (ValueError, TypeError):
                            pass
                    
                    # データ保存用辞書作成
                    trackpoint_data = {
                        'sensor_id': sensor_id,
                        'time': parsed_time,  # 日本時間に変換済み
                        'heart_rate': heart_rate,
                        'upload_batch_id': batch_id,
                        'competition_id': competition_id
                    }
                    
                    trackpoints_data.append(trackpoint_data)
                    processed_count += 1
                    
                except Exception as e:
                    errors.append(f"Trackpoint {idx+1}: {str(e)}")
                    failed_count += 1
                    continue
            
            # データベース保存
            if trackpoints_data:
                self._save_heart_rate_data(trackpoints_data)
            
            # バッチ記録作成
            self._create_heart_rate_batch(
                batch_id=batch_id,
                filename=filename,
                sensor_id=sensor_id,
                competition_id=competition_id,
                total_records=len(trackpoints),
                success_records=processed_count,
                failed_records=failed_count
            )
            
            print(f"✅ TCX処理完了: {processed_count}件成功, {failed_count}件失敗")
            
            return {
                "filename": filename,
                "status": "success" if processed_count > 0 else "failed",
                "batch_id": batch_id,
                "total": len(trackpoints),
                "success": processed_count,
                "failed": failed_count,
                "trackpoints_total": len(trackpoints),
                "sensor_ids": [sensor_id],
                "error": errors[0] if errors and processed_count == 0 else None,
                "message": f"心拍データ {processed_count}件を日本時間で保存しました"
            }
            
        except ET.ParseError as e:
            return {
                "filename": filename,
                "status": "failed",
                "error": f"XMLパースエラー: {str(e)}",
                "total": 0,
                "success": 0,
                "failed": 0
            }
        except Exception as e:
            return {
                "filename": filename,
                "status": "failed",
                "error": f"TCX処理エラー: {str(e)}",
                "total": 0,
                "success": 0,
                "failed": 0
            }
    
    def _parse_tcx_time_to_jst(self, time_str: str) -> Optional[datetime]:
        """
        TCXの時刻文字列を日本時間（JST）に変換
        
        Args:
            time_str: TCXの時刻文字列（例: "2023-07-15T08:30:00Z"）
        
        Returns:
            datetime: 日本時間（JST）のdatetimeオブジェクト
        """
        try:
            # ISO8601形式の解析
            if time_str.endswith('Z'):
                # UTC時刻の場合（例: "2023-07-15T08:30:00Z"）
                utc_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                
                # UTC → JST変換（+9時間）
                jst_time = utc_time.astimezone(timezone(timedelta(hours=9)))
                
                # タイムゾーン情報を除去してnaive datetimeとして返す
                return jst_time.replace(tzinfo=None)
                
            elif '+' in time_str or '-' in time_str[-6:]:
                # タイムゾーン付きの場合（例: "2023-07-15T08:30:00+00:00"）
                aware_time = datetime.fromisoformat(time_str)
                
                # JST に変換
                jst_time = aware_time.astimezone(timezone(timedelta(hours=9)))
                
                # タイムゾーン情報を除去
                return jst_time.replace(tzinfo=None)
                
            else:
                # タイムゾーン情報がない場合
                naive_time = datetime.fromisoformat(time_str)
                
                # ⚠️ この場合、元データがUTCかJSTか判断が困難
                # 仕様書に基づき、+9時間してJSTとして扱う
                jst_time = naive_time + timedelta(hours=9)
                
                print(f"⚠️ タイムゾーン不明の時刻を+9時間してJST扱い: {time_str} → {jst_time}")
                
                return jst_time
                
        except Exception as e:
            print(f"❌ 時刻解析エラー: {time_str} - {str(e)}")
            return None
    
    def _save_heart_rate_data(self, trackpoints_data: List[Dict[str, Any]]):
        """心拍データをデータベースに保存"""
        from app.models.flexible_sensor_data import HeartRateData
        
        for data in trackpoints_data:
            heart_rate_record = HeartRateData(
                sensor_id=data['sensor_id'],
                time=data['time'],  # 日本時間（JST）
                heart_rate=data['heart_rate'],
                upload_batch_id=data['upload_batch_id'],
                competition_id=data['competition_id']
            )
            self.db.add(heart_rate_record)
        
        self.db.commit()
    
    def _create_heart_rate_batch(
        self, 
        batch_id: str, 
        filename: str, 
        sensor_id: str,
        competition_id: str,
        total_records: int,
        success_records: int,
        failed_records: int
    ):
        """心拍データバッチ記録を作成"""
        from app.models.flexible_sensor_data import UploadBatch, SensorType, UploadStatus
        
        status = UploadStatus.SUCCESS if failed_records == 0 else (
            UploadStatus.PARTIAL if success_records > 0 else UploadStatus.FAILED
        )
        
        batch = UploadBatch(
            batch_id=batch_id,
            sensor_type=SensorType.HEART_RATE,
            competition_id=competition_id,
            file_name=filename,
            total_records=total_records,
            success_records=success_records,
            failed_records=failed_records,
            status=status,
            uploaded_by="admin",
            notes=f"センサーID: {sensor_id}, 日本時間変換適用"
        )
        
        self.db.add(batch)
        self.db.commit()