import pandas as pd
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
import aiofiles
import os
import tempfile

from app.models.sensor_data import SensorData, SensorMapping, UploadHistory
from app.models.user import User

class CSVProcessingService:
    """CSV処理サービス"""
    
    def __init__(self, upload_dir: str = "./uploads/csv"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_uploaded_file(self, file: UploadFile) -> Tuple[str, str]:
        """アップロードファイルの保存"""
        try:
            # ユニークファイル名生成
            file_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{file_id}_{file.filename}"
            file_path = self.upload_dir / safe_filename
            
            # ファイル内容を読み込み（既に読み込み済みの場合はシーク）
            await file.seek(0)
            content = await file.read()
            
            # ファイル保存
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            return str(file_path), safe_filename
        except Exception as e:
            print(f"File save error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    def validate_csv_structure(self, file_path: str, csv_type: str) -> pd.DataFrame:
        """CSV構造検証"""
        try:
            # CSVファイル読み込み（エンコーディングを自動判定）
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(file_path, encoding='shift_jis')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='cp932')
            
            # 空ファイルチェック
            if df.empty:
                raise HTTPException(status_code=400, detail="CSV file is empty")
            
            # ヘッダーの空白文字を削除
            df.columns = df.columns.str.strip()
            
            if csv_type == "sensor_data":
                # センサデータCSVの必須カラム
                required_columns = ['sensor_id', 'timestamp', 'temperature']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing required columns: {missing_columns}. Found columns: {list(df.columns)}"
                    )
                
                # データ型検証
                try:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce')
                    df['sensor_id'] = df['sensor_id'].astype(str).str.strip()
                except Exception as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Data type conversion error: {str(e)}"
                    )
                
                # 無効なデータ行を削除
                invalid_rows = df[df['temperature'].isna() | df['sensor_id'].isna()]
                if not invalid_rows.empty:
                    print(f"Warning: Removed {len(invalid_rows)} invalid rows from sensor data")
                    df = df.dropna(subset=['temperature', 'sensor_id'])
                
            elif csv_type == "sensor_mapping":
                # センサマッピングCSVの必須カラム
                required_columns = ['sensor_id', 'user_id']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing required columns: {missing_columns}. Found columns: {list(df.columns)}"
                    )
                
                # データ型を文字列に統一
                df['sensor_id'] = df['sensor_id'].astype(str).str.strip()
                df['user_id'] = df['user_id'].astype(str).str.strip()
                if 'subject_name' in df.columns:
                    df['subject_name'] = df['subject_name'].astype(str).str.strip()
                
                # 重複チェック
                duplicates = df[df.duplicated(['sensor_id'])]
                if not duplicates.empty:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Duplicate sensor_id found: {duplicates['sensor_id'].tolist()}"
                    )
            
            print(f"CSV validation successful: {len(df)} rows, columns: {list(df.columns)}")
            return df
            
        except HTTPException:
            raise
        except pd.errors.EmptyDataError:
            raise HTTPException(status_code=400, detail="CSV file is empty or invalid")
        except pd.errors.ParserError as e:
            raise HTTPException(status_code=400, detail=f"CSV parsing error: {str(e)}")
        except Exception as e:
            print(f"CSV validation error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"CSV validation error: {str(e)}")
    
    def process_sensor_data_csv(
        self, 
        sensor_df: pd.DataFrame, 
        mapping_df: pd.DataFrame,
        db: Session
    ) -> Tuple[int, List[str]]:
        """センサデータCSV処理"""
        processed_count = 0
        errors = []
        
        try:
            # センサマッピング辞書作成
            sensor_mapping = dict(zip(mapping_df['sensor_id'], mapping_df['user_id']))
            print(f"Sensor mapping created: {sensor_mapping}")
            
            # バッチ処理用リスト
            sensor_data_batch = []
            
            for index, row in sensor_df.iterrows():
                try:
                    sensor_id = str(row['sensor_id']).strip()
                    
                    # センサIDマッピング確認
                    if sensor_id not in sensor_mapping:
                        errors.append(f"Row {index}: sensor_id '{sensor_id}' not found in mapping")
                        continue
                    
                    user_id = sensor_mapping[sensor_id]
                    
                    # ユーザー存在確認
                    user = db.query(User).filter_by(user_id=user_id).first()
                    if not user:
                        errors.append(f"Row {index}: user_id '{user_id}' not found")
                        continue
                    
                    # センサデータ作成
                    sensor_data = SensorData(
                        sensor_id=sensor_id,
                        user_id=user_id,
                        timestamp=row['timestamp'],
                        temperature=float(row['temperature']),
                        raw_data=row.to_json(),  # 元データをJSONで保存
                        data_source="csv_upload"
                    )
                    
                    sensor_data_batch.append(sensor_data)
                    processed_count += 1
                    
                    # バッチサイズ1000でコミット
                    if len(sensor_data_batch) >= 1000:
                        db.bulk_save_objects(sensor_data_batch)
                        db.commit()
                        sensor_data_batch = []
                        print(f"Batch saved: {processed_count} records processed")
                    
                except Exception as e:
                    errors.append(f"Row {index}: {str(e)}")
                    continue
            
            # 残りのデータをコミット
            if sensor_data_batch:
                db.bulk_save_objects(sensor_data_batch)
                db.commit()
                print(f"Final batch saved: {len(sensor_data_batch)} records")
            
            print(f"Sensor data processing completed: {processed_count} records, {len(errors)} errors")
            return processed_count, errors
            
        except Exception as e:
            print(f"Sensor data processing error: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Sensor data processing failed: {str(e)}")
    
    def process_sensor_mapping_csv(self, mapping_df: pd.DataFrame, db: Session) -> Tuple[int, List[str]]:
        """センサマッピングCSV処理"""
        processed_count = 0
        errors = []
        
        try:
            for index, row in mapping_df.iterrows():
                try:
                    sensor_id = str(row['sensor_id']).strip()
                    user_id = str(row['user_id']).strip()
                    subject_name = str(row.get('subject_name', '')).strip() if 'subject_name' in row and pd.notna(row.get('subject_name')) else None
                    
                    # ユーザー存在確認
                    user = db.query(User).filter_by(user_id=user_id).first()
                    if not user:
                        errors.append(f"Row {index}: user_id '{user_id}' not found")
                        continue
                    
                    # 既存マッピング確認・更新
                    existing_mapping = db.query(SensorMapping).filter_by(sensor_id=sensor_id).first()
                    
                    if existing_mapping:
                        existing_mapping.user_id = user_id
                        existing_mapping.subject_name = subject_name
                        existing_mapping.updated_at = datetime.utcnow()
                        print(f"Updated existing mapping: {sensor_id} -> {user_id}")
                    else:
                        # 新規マッピング作成
                        mapping = SensorMapping(
                            sensor_id=sensor_id,
                            user_id=user_id,
                            subject_name=subject_name
                        )
                        db.add(mapping)
                        print(f"Created new mapping: {sensor_id} -> {user_id}")
                    
                    processed_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index}: {str(e)}")
                    continue
            
            db.commit()
            print(f"Sensor mapping processing completed: {processed_count} records, {len(errors)} errors")
            return processed_count, errors
            
        except Exception as e:
            print(f"Sensor mapping processing error: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Sensor mapping processing failed: {str(e)}")
    
    def create_upload_history(
        self,
        admin_id: str,
        filename: str,
        file_path: str,
        file_size: int,
        db: Session
    ) -> UploadHistory:
        """アップロード履歴作成"""
        try:
            upload_history = UploadHistory(
                upload_id=str(uuid.uuid4()),
                admin_id=admin_id,
                filename=filename,
                file_path=file_path,
                file_size=file_size,
                status="pending"
            )
            
            db.add(upload_history)
            db.commit()
            db.refresh(upload_history)
            
            print(f"Upload history created: {upload_history.upload_id}")
            return upload_history
            
        except Exception as e:
            print(f"Upload history creation error: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create upload history: {str(e)}")