"""
app/routers/multi_sensor_upload.py

マルチセンサー対応のアップロードAPI
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from enum import Enum

from app.database import get_db
from app.models.user import AdminUser
from app.models.flexible_sensor_data import SensorType, SensorDataStatus
from app.services.flexible_csv_service import FlexibleCSVService
from app.utils.dependencies import get_current_admin
from pydantic import BaseModel

router = APIRouter(prefix="/multi-sensor", tags=["multi-sensor"])

# === レスポンススキーマ ===

class UploadResponse(BaseModel):
    status: str
    batch_id: str
    sensor_type: str
    processed_records: int
    errors: List[str]
    message: str

class MappingResponse(BaseModel):
    status: str
    mapped_records: int
    specialized_records: int
    mapping_errors: List[str]
    specialized_errors: List[str]
    message: str

class DataSummaryResponse(BaseModel):
    total_unmapped_records: int
    by_sensor_type: Dict
    competition_id: Optional[str]

class MappingStatusResponse(BaseModel):
    total_records: int
    mapping_status: Dict[str, int]
    mapping_completion_rate: float

# === センサーデータアップロード（種別ごと） ===

@router.post("/upload/skin-temperature", response_model=UploadResponse)
async def upload_skin_temperature_data(
    data_file: UploadFile = File(..., description="体表温データCSVファイル"),
    competition_id: Optional[str] = Form(None, description="大会ID"),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """体表温データアップロード（マッピング不要）"""
    
    csv_service = FlexibleCSVService()
    
    return await csv_service.process_sensor_data_only(
        sensor_file=data_file,
        sensor_type=SensorType.SKIN_TEMPERATURE,
        competition_id=competition_id,
        db=db
    )

@router.post("/upload/core-temperature", response_model=UploadResponse)
async def upload_core_temperature_data(
    data_file: UploadFile = File(..., description="カプセル体温データCSVファイル"),
    competition_id: Optional[str] = Form(None, description="大会ID"),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """カプセル体温データアップロード（マッピング不要）"""
    
    csv_service = FlexibleCSVService()
    
    return await csv_service.process_sensor_data_only(
        sensor_file=data_file,
        sensor_type=SensorType.CORE_TEMPERATURE,
        competition_id=competition_id,
        db=db
    )

@router.post("/upload/heart-rate", response_model=UploadResponse)
async def upload_heart_rate_data(
    data_file: UploadFile = File(..., description="心拍データCSVファイル"),
    competition_id: Optional[str] = Form(None, description="大会ID"),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """心拍データアップロード（マッピング不要）"""
    
    csv_service = FlexibleCSVService()
    
    return await csv_service.process_sensor_data_only(
        sensor_file=data_file,
        sensor_type=SensorType.HEART_RATE,
        competition_id=competition_id,
        db=db
    )

@router.post("/upload/wbgt", response_model=UploadResponse)
async def upload_wbgt_data(
    data_file: UploadFile = File(..., description="WBGT環境データCSVファイル"),
    competition_id: Optional[str] = Form(None, description="大会ID"),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """WBGT環境データアップロード（マッピング不要）"""
    
    csv_service = FlexibleCSVService()
    
    return await csv_service.process_sensor_data_only(
        sensor_file=data_file,
        sensor_type=SensorType.WBGT,
        competition_id=competition_id,
        db=db
    )

# === マッピング適用 ===

@router.post("/mapping/skin-temperature", response_model=MappingResponse)
async def apply_skin_temperature_mapping(
    mapping_file: UploadFile = File(..., description="体表温センサーマッピングCSVファイル"),
    competition_id: Optional[str] = Form(None, description="大会ID"),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """体表温センサーマッピング適用"""
    
    csv_service = FlexibleCSVService()
    
    return await csv_service.apply_mapping_to_unmapped_data(
        mapping_file=mapping_file,
        sensor_type=SensorType.SKIN_TEMPERATURE,
        competition_id=competition_id,
        db=db
    )

@router.post("/mapping/core-temperature", response_model=MappingResponse)
async def apply_core_temperature_mapping(
    mapping_file: UploadFile = File(..., description="カプセル体温センサーマッピングCSVファイル"),
    competition_id: Optional[str] = Form(None, description="大会ID"),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """カプセル体温センサーマッピング適用"""
    
    csv_service = FlexibleCSVService()
    
    return await csv_service.apply_mapping_to_unmapped_data(
        mapping_file=mapping_file,
        sensor_type=SensorType.CORE_TEMPERATURE,
        competition_id=competition_id,
        db=db
    )

@router.post("/mapping/heart-rate", response_model=MappingResponse)
async def apply_heart_rate_mapping(
    mapping_file: UploadFile = File(..., description="心拍センサーマッピングCSVファイル"),
    competition_id: Optional[str] = Form(None, description="大会ID"),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """心拍センサーマッピング適用"""
    
    csv_service = FlexibleCSVService()
    
    return await csv_service.apply_mapping_to_unmapped_data(
        mapping_file=mapping_file,
        sensor_type=SensorType.HEART_RATE,
        competition_id=competition_id,
        db=db
    )

# === データ管理・監視 ===

@router.get("/unmapped-summary", response_model=DataSummaryResponse)
async def get_unmapped_data_summary(
    competition_id: Optional[str] = Query(None, description="大会ID"),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """未マッピングデータのサマリー取得"""
    
    csv_service = FlexibleCSVService()
    return csv_service.get_unmapped_data_summary(db, competition_id)

@router.get("/mapping-status", response_model=MappingStatusResponse)
async def get_mapping_status(
    competition_id: Optional[str] = Query(None, description="大会ID"),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """マッピング状況の取得"""
    
    csv_service = FlexibleCSVService()
    return csv_service.get_mapping_status(db, competition_id)

@router.get("/unmapped-sensors/{sensor_type}")
async def get_unmapped_sensors(
    sensor_type: SensorType,
    competition_id: Optional[str] = Query(None, description="大会ID"),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """特定センサータイプの未マッピングセンサーID一覧"""
    
    from app.models.flexible_sensor_data import RawSensorData
    
    query = db.query(RawSensorData).filter_by(
        sensor_type=sensor_type,
        mapping_status=SensorDataStatus.UNMAPPED
    )
    
    if competition_id:
        query = query.filter_by(competition_id=competition_id)
    
    unmapped_data = query.all()
    sensor_ids = list(set([data.sensor_id for data in unmapped_data]))
    
    # センサーごとのレコード数
    sensor_details = {}
    for sensor_id in sensor_ids:
        count = len([data for data in unmapped_data if data.sensor_id == sensor_id])
        latest_timestamp = max([data.timestamp for data in unmapped_data if data.sensor_id == sensor_id])
        
        sensor_details[sensor_id] = {
            "record_count": count,
            "latest_timestamp": latest_timestamp.isoformat(),
            "sensor_type": sensor_type.value
        }
    
    return {
        "sensor_type": sensor_type.value,
        "unmapped_sensor_count": len(sensor_ids),
        "sensor_details": sensor_details,
        "competition_id": competition_id
    }

# === 一括マッピング管理 ===

@router.post("/bulk-remap/{sensor_type}")
async def bulk_remap_sensors(
    sensor_type: SensorType,
    sensor_mappings: Dict[str, str],  # {sensor_id: user_id}
    competition_id: Optional[str] = None,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """センサーの一括再マッピング"""
    
    csv_service = FlexibleCSVService()
    
    return await csv_service.bulk_remap_sensors(
        sensor_id_mappings=sensor_mappings,
        sensor_type=sensor_type,
        competition_id=competition_id,
        db=db
    )

@router.delete("/unmapped-data/{sensor_type}")
async def delete_unmapped_data(
    sensor_type: SensorType,
    competition_id: Optional[str] = Query(None, description="大会ID"),
    confirm: bool = Query(False, description="削除確認"),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """未マッピングデータの削除"""
    
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Please set confirm=true to delete unmapped data"
        )
    
    from app.models.flexible_sensor_data import RawSensorData
    
    query = db.query(RawSensorData).filter_by(
        sensor_type=sensor_type,
        mapping_status=SensorDataStatus.UNMAPPED
    )
    
    if competition_id:
        query = query.filter_by(competition_id=competition_id)
    
    deleted_count = query.count()
    query.delete()
    db.commit()
    
    return {
        "status": "success",
        "deleted_records": deleted_count,
        "sensor_type": sensor_type.value,
        "competition_id": competition_id
    }

# === 統合データ取得（既存API互換性） ===

@router.get("/integrated-data/{user_id}")
async def get_integrated_user_data(
    user_id: str,
    competition_id: Optional[str] = Query(None, description="大会ID"),
    sensor_types: Optional[List[SensorType]] = Query(None, description="取得するセンサータイプ"),
    start_time: Optional[str] = Query(None, description="開始時刻"),
    end_time: Optional[str] = Query(None, description="終了時刻"),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """ユーザーの統合センサーデータ取得（既存API互換性）"""
    
    from app.models.flexible_sensor_data import RawSensorData
    from datetime import datetime
    
    query = db.query(RawSensorData).filter_by(
        mapped_user_id=user_id,
        mapping_status=SensorDataStatus.MAPPED
    )
    
    if competition_id:
        query = query.filter_by(competition_id=competition_id)
    
    if sensor_types:
        query = query.filter(RawSensorData.sensor_type.in_(sensor_types))
    
    if start_time:
        start_dt = datetime.fromisoformat(start_time)
        query = query.filter(RawSensorData.timestamp >= start_dt)
    
    if end_time:
        end_dt = datetime.fromisoformat(end_time)
        query = query.filter(RawSensorData.timestamp <= end_dt)
    
    data = query.order_by(RawSensorData.timestamp).all()
    
    # データ変換
    integrated_data = []
    for record in data:
        data_values = record.get_data_as_dict()
        
        integrated_record = {
            "id": record.id,
            "sensor_id": record.sensor_id,
            "sensor_type": record.sensor_type.value,
            "user_id": record.mapped_user_id,
            "timestamp": record.timestamp.isoformat(),
            "competition_id": record.competition_id,
            "data_values": data_values,
            "created_at": record.created_at.isoformat()
        }
        
        integrated_data.append(integrated_record)
    
    return {
        "user_id": user_id,
        "total_records": len(integrated_data),
        "data": integrated_data,
        "competition_id": competition_id
    }