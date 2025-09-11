"""
app/services/flexible_csv_service.py

マッピング不要でもデータを保持する柔軟なCSV処理サービス
"""

import pandas as pd
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile

from app.models.flexible_sensor_data import (
    RawSensorData, SensorType, SensorDataStatus,
    SkinTemperatureData, CoreTemperatureData, HeartRateData, WBGTData,
    FlexibleSensorMapping
)
from app.models.user import User

class FlexibleCSVService:
    """柔軟なCSV処理サービス"""
    
    def __init__(self, upload_dir: str = "./uploads/csv"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    # === データアップロード（マッピング不要） ===
    
    async def process_sensor_data_only(
        self, 
        sensor_file: UploadFile, 
        sensor_type: SensorType,
        competition_id: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """センサーデータのみアップロード（マッピング不要）"""
        
        batch_id = str(uuid.uuid4())
        
        try:
            # ファイル保存
            file_path, filename = await self.save_uploaded_file(sensor_file)
            
            # CSV構造検証
            df = self.validate_sensor_csv(file_path, sensor_type)
            
            # 生データとして保存
            processed_count, errors = await self.save_raw_sensor_data(
                df, sensor_type, batch_id, competition_id, db
            )
            
            return {
                "status": "success",
                "batch_id": batch_id,
                "sensor_type": sensor_type.value,
                "processed_records": processed_count,
                "errors": errors,
                "message": f"{processed_count} records saved. Mapping can be applied later."
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    async def save_raw_sensor_data(
        self, 
        df: pd.DataFrame, 
        sensor_type: SensorType, 
        batch_id: str,
        competition_id: Optional[str],
        db: Session
    ) -> Tuple[int, List[str]]:
        """生センサーデータを保存"""
        
        processed_count = 0
        errors = []
        raw_data_batch = []
        
        for index, row in df.iterrows():
            try:
                # センサータイプごとのデータ抽出
                data_values = self.extract_sensor_values(row, sensor_type)
                
                # 生データとして保存
                raw_data = RawSensorData(
                    sensor_id=str(row['sensor_id']).strip(),
                    sensor_type=sensor_type,
                    competition_id=competition_id,
                    timestamp=row['timestamp'],
                    data_values=json.dumps(data_values),
                    raw_data=row.to_json(),
                    mapping_status=SensorDataStatus.UNMAPPED,
                    upload_batch_id=batch_id,
                    data_source="csv_upload"
                )
                
                raw_data_batch.append(raw_data)
                processed_count += 1
                
                # バッチ保存
                if len(raw_data_batch) >= 1000:
                    db.bulk_save_objects(raw_data_batch)
                    db.commit()
                    raw_data_batch = []
                
            except Exception as e:
                errors.append(f"Row {index}: {str(e)}")
                continue
        
        # 残りデータ保存
        if raw_data_batch:
            db.bulk_save_objects(raw_data_batch)
            db.commit()
        
        return processed_count, errors
    
    def extract_sensor_values(self, row: pd.Series, sensor_type: SensorType) -> Dict[str, Any]:
        """センサータイプごとのデータ値を抽出"""
        
        if sensor_type == SensorType.SKIN_TEMPERATURE:
            return {
                "skin_temperature": float(row.get('temperature', row.get('skin_temperature', 0))),
                "sensor_location": str(row.get('location', '')),
                "ambient_temperature": float(row.get('ambient_temp', 0)) if 'ambient_temp' in row else None
            }
        
        elif sensor_type == SensorType.CORE_TEMPERATURE:
            return {
                "core_temperature": float(row.get('temperature', row.get('core_temperature', 0))),
                "monitor_id": str(row.get('monitor_id', '')),
                "capsule_id": str(row.get('capsule_id', '')),
                "battery_level": float(row.get('battery', 0)) if 'battery' in row else None,
                "signal_strength": float(row.get('signal', 0)) if 'signal' in row else None
            }
        
        elif sensor_type == SensorType.HEART_RATE:
            return {
                "heart_rate": int(row.get('heart_rate', row.get('bpm', 0))),
                "heart_rate_zone": int(row.get('hr_zone', 0)) if 'hr_zone' in row else None,
                "rrinterval": float(row.get('rr_interval', 0)) if 'rr_interval' in row else None,
                "activity_type": str(row.get('activity', '')),
                "calories": float(row.get('calories', 0)) if 'calories' in row else None
            }
        
        elif sensor_type == SensorType.WBGT:
            return {
                "wbgt_value": float(row.get('wbgt', row.get('wbgt_value', 0))),
                "air_temperature": float(row.get('air_temp', 0)) if 'air_temp' in row else None,
                "humidity": float(row.get('humidity', 0)) if 'humidity' in row else None,
                "wind_speed": float(row.get('wind_speed', 0)) if 'wind_speed' in row else None,
                "solar_radiation": float(row.get('solar', 0)) if 'solar' in row else None,
                "location": str(row.get('location', ''))
            }
        
        else:
            # その他のセンサータイプ
            return {"value": str(row.get('value', ''))}
    
    # === マッピング適用 ===
    
    async def apply_mapping_to_unmapped_data(
        self,
        mapping_file: UploadFile,
        sensor_type: SensorType,
        competition_id: Optional[str],
        db: Session
    ) -> Dict[str, Any]:
        """未マッピングデータにマッピングを適用"""
        
        try:
            # マッピングファイル処理
            file_path, filename = await self.save_uploaded_file(mapping_file)
            mapping_df = self.validate_mapping_csv(file_path)
            
            # マッピング適用
            mapped_count, mapping_errors = await self.apply_mappings(
                mapping_df, sensor_type, competition_id, db
            )
            
            # 専用テーブルにデータ作成
            specialized_count, specialized_errors = await self.create_specialized_data(
                sensor_type, competition_id, db
            )
            
            return {
                "status": "success",
                "mapped_records": mapped_count,
                "specialized_records": specialized_count,
                "mapping_errors": mapping_errors,
                "specialized_errors": specialized_errors,
                "message": f"Applied mapping to {mapped_count} records"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Mapping failed: {str(e)}")
    
    async def apply_mappings(
        self,
        mapping_df: pd.DataFrame,
        sensor_type: SensorType,
        competition_id: Optional[str],
        db: Session
    ) -> Tuple[int, List[str]]:
        """マッピングを適用"""
        
        mapped_count = 0
        errors = []
        
        for index, row in mapping_df.iterrows():
            try:
                sensor_id = str(row['sensor_id']).strip()
                user_id = str(row['user_id']).strip()
                
                # ユーザー存在確認
                user = db.query(User).filter_by(user_id=user_id).first()
                if not user:
                    errors.append(f"Row {index}: user_id '{user_id}' not found")
                    continue
                
                # マッピング作成・更新
                existing_mapping = db.query(FlexibleSensorMapping).filter_by(
                    sensor_id=sensor_id,
                    sensor_type=sensor_type,
                    competition_id=competition_id
                ).first()
                
                if existing_mapping:
                    existing_mapping.user_id = user_id
                    existing_mapping.updated_at = datetime.utcnow()
                else:
                    new_mapping = FlexibleSensorMapping(
                        sensor_id=sensor_id,
                        sensor_type=sensor_type,
                        user_id=user_id,
                        competition_id=competition_id,
                        subject_name=row.get('subject_name', ''),
                        is_active=True
                    )
                    db.add(new_mapping)
                
                # 未マッピング生データを更新
                unmapped_data = db.query(RawSensorData).filter_by(
                    sensor_id=sensor_id,
                    sensor_type=sensor_type,
                    mapping_status=SensorDataStatus.UNMAPPED,
                    competition_id=competition_id
                ).all()
                
                for data in unmapped_data:
                    data.mapping_status = SensorDataStatus.MAPPED
                    data.mapped_user_id = user_id
                    data.mapped_at = datetime.utcnow()
                    mapped_count += 1
                
                db.commit()
                
            except Exception as e:
                errors.append(f"Row {index}: {str(e)}")
                db.rollback()
                continue
        
        return mapped_count, errors
    
    async def create_specialized_data(
        self,
        sensor_type: SensorType,
        competition_id: Optional[str],
        db: Session
    ) -> Tuple[int, List[str]]:
        """マッピング済みデータから専用テーブルデータを作成"""
        
        created_count = 0
        errors = []
        
        # マッピング済みの生データを取得
        mapped_raw_data = db.query(RawSensorData).filter_by(
            sensor_type=sensor_type,
            mapping_status=SensorDataStatus.MAPPED,
            competition_id=competition_id
        ).all()
        
        for raw_data in mapped_raw_data:
            try:
                # 既存チェック
                if self.specialized_data_exists(raw_data.id, sensor_type, db):
                    continue
                
                # センサータイプごとの専用データ作成
                specialized_data = self.create_specialized_record(raw_data, sensor_type)
                if specialized_data:
                    db.add(specialized_data)
                    created_count += 1
                
            except Exception as e:
                errors.append(f"Raw data ID {raw_data.id}: {str(e)}")
                continue
        
        if created_count > 0:
            db.commit()
        
        return created_count, errors
    
    def create_specialized_record(self, raw_data: RawSensorData, sensor_type: SensorType):
        """専用テーブルレコード作成"""
        
        data_values = json.loads(raw_data.data_values)
        
        if sensor_type == SensorType.SKIN_TEMPERATURE:
            return SkinTemperatureData(
                raw_data_id=raw_data.id,
                sensor_id=raw_data.sensor_id,
                user_id=raw_data.mapped_user_id,
                competition_id=raw_data.competition_id,
                timestamp=raw_data.timestamp,
                skin_temperature=data_values.get('skin_temperature', 0),
                sensor_location=data_values.get('sensor_location'),
                ambient_temperature=data_values.get('ambient_temperature')
            )
        
        elif sensor_type == SensorType.CORE_TEMPERATURE:
            return CoreTemperatureData(
                raw_data_id=raw_data.id,
                monitor_id=data_values.get('monitor_id', ''),
                capsule_id=data_values.get('capsule_id', ''),
                user_id=raw_data.mapped_user_id,
                competition_id=raw_data.competition_id,
                timestamp=raw_data.timestamp,
                core_temperature=data_values.get('core_temperature', 0),
                battery_level=data_values.get('battery_level'),
                signal_strength=data_values.get('signal_strength')
            )
        
        elif sensor_type == SensorType.HEART_RATE:
            return HeartRateData(
                raw_data_id=raw_data.id,
                device_id=raw_data.sensor_id,
                user_id=raw_data.mapped_user_id,
                competition_id=raw_data.competition_id,
                timestamp=raw_data.timestamp,
                heart_rate=data_values.get('heart_rate', 0),
                heart_rate_zone=data_values.get('heart_rate_zone'),
                rrinterval=data_values.get('rrinterval'),
                activity_type=data_values.get('activity_type'),
                calories=data_values.get('calories')
            )
        
        elif sensor_type == SensorType.WBGT:
            return WBGTData(
                raw_data_id=raw_data.id,
                station_id=raw_data.sensor_id,
                competition_id=raw_data.competition_id,
                timestamp=raw_data.timestamp,
                wbgt_value=data_values.get('wbgt_value', 0),
                air_temperature=data_values.get('air_temperature'),
                humidity=data_values.get('humidity'),
                wind_speed=data_values.get('wind_speed'),
                solar_radiation=data_values.get('solar_radiation'),
                location=data_values.get('location')
            )
        
        return None
    
    def specialized_data_exists(self, raw_data_id: int, sensor_type: SensorType, db: Session) -> bool:
        """専用テーブルにデータが既に存在するかチェック"""
        
        if sensor_type == SensorType.SKIN_TEMPERATURE:
            return db.query(SkinTemperatureData).filter_by(raw_data_id=raw_data_id).first() is not None
        elif sensor_type == SensorType.CORE_TEMPERATURE:
            return db.query(CoreTemperatureData).filter_by(raw_data_id=raw_data_id).first() is not None
        elif sensor_type == SensorType.HEART_RATE:
            return db.query(HeartRateData).filter_by(raw_data_id=raw_data_id).first() is not None
        elif sensor_type == SensorType.WBGT:
            return db.query(WBGTData).filter_by(raw_data_id=raw_data_id).first() is not None
        
        return False
    
    # === CSV検証 ===
    
    def validate_sensor_csv(self, file_path: str, sensor_type: SensorType) -> pd.DataFrame:
        """センサータイプごとのCSV検証"""
        
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        
        # 共通必須項目
        required_columns = ['sensor_id', 'timestamp']
        
        # センサータイプごとの必須項目
        if sensor_type == SensorType.SKIN_TEMPERATURE:
            required_columns.extend(['temperature'])
        elif sensor_type == SensorType.CORE_TEMPERATURE:
            required_columns.extend(['temperature', 'monitor_id', 'capsule_id'])
        elif sensor_type == SensorType.HEART_RATE:
            required_columns.extend(['heart_rate'])
        elif sensor_type == SensorType.WBGT:
            required_columns.extend(['wbgt'])
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns for {sensor_type.value}: {missing_columns}"
            )
        
        return df
    
    def validate_mapping_csv(self, file_path: str) -> pd.DataFrame:
        """マッピングCSV検証"""
        
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        
        required_columns = ['sensor_id', 'user_id']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns in mapping file: {missing_columns}"
            )
        
        return df
    
    async def save_uploaded_file(self, file: UploadFile) -> Tuple[str, str]:
        """アップロードファイルの保存"""
        try:
            file_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{file_id}_{file.filename}"
            file_path = self.upload_dir / safe_filename
            
            await file.seek(0)
            content = await file.read()
            
            import aiofiles
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            return str(file_path), safe_filename
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # === データ管理機能 ===
    
    def get_unmapped_data_summary(self, db: Session, competition_id: Optional[str] = None) -> Dict[str, Any]:
        """未マッピングデータのサマリー取得"""
        
        query = db.query(RawSensorData).filter_by(mapping_status=SensorDataStatus.UNMAPPED)
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        
        unmapped_data = query.all()
        
        # センサータイプ別の集計
        summary = {}
        for sensor_type in SensorType:
            type_data = [d for d in unmapped_data if d.sensor_type == sensor_type]
            sensor_ids = list(set([d.sensor_id for d in type_data]))
            
            summary[sensor_type.value] = {
                "total_records": len(type_data),
                "unique_sensors": len(sensor_ids),
                "sensor_ids": sensor_ids,
                "latest_upload": max([d.created_at for d in type_data]) if type_data else None
            }
        
        return {
            "total_unmapped_records": len(unmapped_data),
            "by_sensor_type": summary,
            "competition_id": competition_id
        }
    
    def get_mapping_status(self, db: Session, competition_id: Optional[str] = None) -> Dict[str, Any]:
        """マッピング状況の取得"""
        
        query = db.query(RawSensorData)
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        
        all_data = query.all()
        
        status_summary = {}
        for status in SensorDataStatus:
            count = len([d for d in all_data if d.mapping_status == status])
            status_summary[status.value] = count
        
        return {
            "total_records": len(all_data),
            "mapping_status": status_summary,
            "mapping_completion_rate": round(
                (status_summary.get('mapped', 0) / len(all_data) * 100) if all_data else 0, 2
            )
        }
    
    async def bulk_remap_sensors(
        self,
        sensor_id_mappings: Dict[str, str],  # {sensor_id: user_id}
        sensor_type: SensorType,
        competition_id: Optional[str],
        db: Session
    ) -> Dict[str, Any]:
        """センサーの一括再マッピング"""
        
        updated_count = 0
        errors = []
        
        for sensor_id, user_id in sensor_id_mappings.items():
            try:
                # ユーザー存在確認
                user = db.query(User).filter_by(user_id=user_id).first()
                if not user:
                    errors.append(f"User '{user_id}' not found for sensor '{sensor_id}'")
                    continue
                
                # 生データ更新
                raw_data_records = db.query(RawSensorData).filter_by(
                    sensor_id=sensor_id,
                    sensor_type=sensor_type,
                    competition_id=competition_id
                ).all()
                
                for raw_data in raw_data_records:
                    old_user_id = raw_data.mapped_user_id
                    raw_data.mapped_user_id = user_id
                    raw_data.mapping_status = SensorDataStatus.MAPPED
                    raw_data.mapped_at = datetime.utcnow()
                    updated_count += 1
                
                # マッピングテーブル更新
                mapping = db.query(FlexibleSensorMapping).filter_by(
                    sensor_id=sensor_id,
                    sensor_type=sensor_type,
                    competition_id=competition_id
                ).first()
                
                if mapping:
                    mapping.user_id = user_id
                    mapping.updated_at = datetime.utcnow()
                else:
                    new_mapping = FlexibleSensorMapping(
                        sensor_id=sensor_id,
                        sensor_type=sensor_type,
                        user_id=user_id,
                        competition_id=competition_id,
                        is_active=True
                    )
                    db.add(new_mapping)
                
            except Exception as e:
                errors.append(f"Sensor '{sensor_id}': {str(e)}")
                continue
        
        if updated_count > 0:
            db.commit()
            
            # 専用テーブルデータを再作成
            await self.create_specialized_data(sensor_type, competition_id, db)
        
        return {
            "updated_records": updated_count,
            "errors": errors,
            "message": f"Bulk remapping completed for {len(sensor_id_mappings)} sensors"
        }