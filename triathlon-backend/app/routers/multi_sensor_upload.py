from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from app.utils.dependencies import get_current_admin, get_db
from app.models.user import AdminUser
from app.services.flexible_csv_service import FlexibleCSVService
from app.schemas.sensor_data import (
    UploadResponse, MappingResponse, DataSummaryResponse, 
    MappingStatusResponse, SensorType, SensorDataStatus
)

router = APIRouter(prefix="/multi-sensor", tags=["マルチセンサーデータ管理"])

# === データアップロード ===

@router.post("/upload/skin-temperature", response_model=UploadResponse)
async def upload_skin_temperature(
    data_file: UploadFile = File(...),
    competition_id: Optional[str] = Form(None),
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
    competition_id: Optional[str] = Form(None),
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
    competition_id: Optional[str] = Form(None),
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
    competition_id: Optional[str] = Form(None),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """WBGT環境データアップロード（上書き対応）"""
    csv_service = FlexibleCSVService()
    return await csv_service.process_wbgt_data(
        wbgt_file=data_file,
        competition_id=competition_id,
        db=db,
        overwrite=True
    )

@router.post("/upload/mapping", response_model=MappingResponse)
async def upload_mapping(
    mapping_file: UploadFile = File(...),
    competition_id: Optional[str] = Form(None),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """マッピングデータアップロード（上書き対応）"""
    csv_service = FlexibleCSVService()
    return await csv_service.process_mapping_data(
        mapping_file=mapping_file,
        competition_id=competition_id,
        db=db,
        overwrite=True
    )

# === 複数ファイル同時アップロード ===

@router.post("/upload/multiple-sensors", response_model=List[UploadResponse])
async def upload_multiple_sensors(
    sensor_type: SensorType = Form(...),
    data_files: List[UploadFile] = File(...),
    competition_id: Optional[str] = Form(None),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """同種別センサーデータ複数同時アップロード"""
    if sensor_type in [SensorType.WBGT]:
        raise HTTPException(status_code=400, detail="WBGTは単一ファイルのみ対応")
    
    csv_service = FlexibleCSVService()
    results = []
    
    for data_file in data_files:
        try:
            result = await csv_service.process_sensor_data_only(
                sensor_file=data_file,
                sensor_type=sensor_type,
                competition_id=competition_id,
                db=db
            )
            results.append(result)
        except Exception as e:
            results.append(UploadResponse(
                success=False,
                message=f"ファイル{data_file.filename}の処理に失敗: {str(e)}",
                total_records=0,
                processed_records=0
            ))
    
    return results

# === データ状況確認 ===

@router.get("/status", response_model=DataSummaryResponse)
async def get_data_status(
    competition_id: Optional[str] = Query(None),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """データ状況サマリー"""
    csv_service = FlexibleCSVService()
    return csv_service.get_data_summary(db, competition_id)

@router.get("/mapping-status", response_model=MappingStatusResponse)
async def get_mapping_status(
    competition_id: Optional[str] = Query(None),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """マッピング状況確認"""
    csv_service = FlexibleCSVService()
    return csv_service.get_mapping_status(db, competition_id)

@router.get("/unmapped-sensors")
async def get_unmapped_sensors(
    sensor_type: Optional[SensorType] = Query(None),
    competition_id: Optional[str] = Query(None),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """未マッピングセンサー一覧"""
    csv_service = FlexibleCSVService()
    return csv_service.get_unmapped_sensors(db, sensor_type, competition_id)