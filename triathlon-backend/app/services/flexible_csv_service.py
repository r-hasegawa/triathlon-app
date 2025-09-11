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
        competition_id: Optional[str],
        db: Session
    ) -> UploadResponse:
        """センサーデータのみ処理"""
        try:
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
                message=f"{sensor_type.value}データを{processed}件処理しました",
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
        """WBGT環境データ処理（1大会1つ、上書き対応）"""
        try:
            # 上書き処理：既存データを削除
            if overwrite and competition_id:
                deleted_count = db.query(WBGTData).filter_by(competition_id=competition_id).delete()
                db.commit()
                print(f"既存WBGTデータ{deleted_count}件を削除しました")
            
            content = await wbgt_file.read()
            df = pd.read_csv(io.BytesIO(content))
            
            processed = 0
            
            for _, row in df.iterrows():
                wbgt_data = WBGTData(
                    timestamp=pd.to_datetime(row.get('timestamp')),
                    wbgt_value=float(row.get('wbgt_value', 0)),
                    air_temperature=float(row.get('temperature', 0)) if pd.notna(row.get('temperature')) else None,
                    humidity=float(row.get('humidity', 0)) if pd.notna(row.get('humidity')) else None,
                    location=str(row.get('location', '')),
                    competition_id=competition_id,
                    station_id=str(row.get('station_id', 'WBGT_STATION'))
                )
                db.add(wbgt_data)
                processed += 1
            
            db.commit()
            
            return UploadResponse(
                success=True,
                message=f"WBGTデータを{processed}件処理しました（上書き: {overwrite}）",
                total_records=len(df),
                processed_records=processed
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"WBGT処理エラー: {str(e)}")

    async def process_mapping_data(
        self,
        mapping_file: UploadFile,
        competition_id: Optional[str],
        db: Session,
        overwrite: bool = True
    ) -> MappingResponse:
        """マッピングデータ処理"""
        try:
            if overwrite and competition_id:
                db.query(FlexibleSensorMapping).filter_by(competition_id=competition_id).delete()
            
            content = await mapping_file.read()
            df = pd.read_csv(io.BytesIO(content))
            
            processed = 0
            
            for _, row in df.iterrows():
                user_id = str(row.get('user_id', '')).strip()
                if not user_id:
                    continue
                
                # 各センサーID列を処理
                for col in df.columns:
                    if col != 'user_id' and pd.notna(row.get(col)):
                        sensor_id = str(row[col]).strip()
                        if sensor_id:
                            mapping_data = FlexibleSensorMapping(
                                user_id=user_id,
                                sensor_id=sensor_id,
                                sensor_type=SensorType.SKIN_TEMPERATURE,  # デフォルト
                                competition_id=competition_id,
                                subject_name=str(row.get('subject_name', ''))
                            )
                            db.add(mapping_data)
                
                processed += 1
            
            db.commit()
            
            return MappingResponse(
                success=True,
                message=f"マッピングデータを{processed}件処理しました",
                mapped_sensors=processed
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"マッピング処理エラー: {str(e)}")

    def get_data_summary(
        self,
        db: Session,
        competition_id: Optional[str] = None
    ) -> DataSummaryResponse:
        """データ状況サマリー"""
        
        query = db.query(RawSensorData)
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        
        total_records = query.count()
        mapped_records = query.filter_by(mapping_status=SensorDataStatus.MAPPED).count()
        unmapped_records = query.filter_by(mapping_status=SensorDataStatus.UNMAPPED).count()
        
        sensor_counts = {}
        for sensor_type in SensorType:
            count = query.filter_by(sensor_type=sensor_type).count()
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
        competition_id: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """未マッピングセンサー一覧"""
        
        query = db.query(RawSensorData).filter_by(mapping_status=SensorDataStatus.UNMAPPED)
        
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        
        if sensor_type:
            query = query.filter_by(sensor_type=sensor_type)
        
        results = query.distinct(RawSensorData.sensor_id, RawSensorData.sensor_type).all()
        
        unmapped_sensors = {}
        for record in results:
            type_key = record.sensor_type.value
            if type_key not in unmapped_sensors:
                unmapped_sensors[type_key] = []
            if record.sensor_id not in unmapped_sensors[type_key]:
                unmapped_sensors[type_key].append(record.sensor_id)
        
        return unmapped_sensors