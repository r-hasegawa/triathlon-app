from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from app.utils.dependencies import get_current_admin, get_db
from app.models.user import AdminUser
from app.services.flexible_csv_service import FlexibleCSVService

# 🔧 正しいインポート先に修正
from app.models.flexible_sensor_data import SensorType, SensorDataStatus
from app.schemas.sensor_data import (
    UploadResponse, MappingResponse, DataSummaryResponse, 
    MappingStatusResponse
)

# 管理者専用エンドポイント - prefix="/admin" はmain.pyで設定
router = APIRouter(prefix="/multi-sensor", tags=["マルチセンサーデータ管理"])

# === データアップロード ===

@router.post("/upload/skin-temperature", response_model=UploadResponse)
async def upload_skin_temperature(
    data_file: UploadFile = File(...),
    competition_id: str = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """体表温データアップロード"""
    csv_service = FlexibleCSVService()
    return await csv_service.process_sensor_data_only(
        sensor_file=data_file,
        sensor_type=SensorType.SKIN_TEMPERATURE,
        competition_id=competition_id,
        db=db
    )

@router.post("/upload/core-temperature", response_model=UploadResponse)
async def upload_core_temperature(
    data_file: UploadFile = File(...),
    competition_id: str = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """カプセル体温データアップロード"""
    csv_service = FlexibleCSVService()
    return await csv_service.process_sensor_data_only(
        sensor_file=data_file,
        sensor_type=SensorType.CORE_TEMPERATURE,
        competition_id=competition_id,
        db=db
    )

@router.post("/upload/heart-rate", response_model=UploadResponse)
async def upload_heart_rate(
    data_file: UploadFile = File(...),
    competition_id: str = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """心拍データアップロード"""
    csv_service = FlexibleCSVService()
    return await csv_service.process_sensor_data_only(
        sensor_file=data_file,
        sensor_type=SensorType.HEART_RATE,
        competition_id=competition_id,
        db=db
    )

@router.post("/upload/wbgt", response_model=UploadResponse)
async def upload_wbgt(
    data_file: UploadFile = File(...),
    competition_id: str = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """WBGT環境データアップロード"""
    csv_service = FlexibleCSVService()
    return await csv_service.process_sensor_data_only(
        sensor_file=data_file,
        sensor_type=SensorType.WBGT,
        competition_id=competition_id,
        db=db
    )

# === マッピング管理 ===

@router.post("/mapping", response_model=MappingResponse)
async def create_mapping(
    mapping_file: UploadFile = File(...),
    competition_id: str = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """マッピングファイルアップロード"""
    csv_service = FlexibleCSVService()
    return await csv_service.process_mapping_data(
        mapping_file=mapping_file,
        competition_id=competition_id,
        db=db
    )

@router.get("/mapping/status", response_model=MappingStatusResponse)
async def get_mapping_status(
    competition_id: Optional[str] = Query(None),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """マッピング状況確認"""
    csv_service = FlexibleCSVService()
    return csv_service.get_mapping_status(db, competition_id)

# === データ確認・管理 ===

@router.get("/data/summary", response_model=DataSummaryResponse)
async def get_data_summary(
    competition_id: Optional[str] = Query(None),
    sensor_type: Optional[SensorType] = Query(None),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """データサマリー取得"""
    csv_service = FlexibleCSVService()
    return csv_service.get_data_summary(db, competition_id, sensor_type)

@router.get("/data/unmapped")
async def get_unmapped_data(
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """未マッピングデータ一覧"""
    csv_service = FlexibleCSVService()
    return csv_service.get_unmapped_data_summary(db)