"""
app/routers/admin/data_upload/mapping.py
マッピングデータアップロード機能
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.user import AdminUser
from app.models.competition import Competition
from app.models.flexible_sensor_data import (
    UploadBatch, 
    SensorType,
    UploadStatus
)
from app.utils.dependencies import get_current_admin
from app.services.flexible_csv_service import FlexibleCSVService


router = APIRouter()


@router.post("/upload/mapping")
async def upload_mapping_data(
    mapping_file: UploadFile = File(...),
    competition_id: str = Form(...),
    overwrite: bool = Form(True),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """マッピングデータアップロード（FlexibleCSVService使用）"""
    
    if not mapping_file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSVファイルのみアップロード可能です")
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
    
    csv_service = FlexibleCSVService()
    
    try:
        content = await mapping_file.read()
        await mapping_file.seek(0)
        
        result = await csv_service.process_mapping_data(
            mapping_file=mapping_file,
            competition_id=competition_id,
            db=db,
            overwrite=overwrite
        )
        
        batch_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{mapping_file.filename}"
        
        batch = UploadBatch(
            batch_id=batch_id,
            sensor_type=SensorType.OTHER,
            competition_id=competition_id,
            file_name=mapping_file.filename,
            total_records=result["total_records"],
            success_records=result["processed_records"],
            failed_records=result["skipped_records"],
            status=UploadStatus.SUCCESS if result["success"] else UploadStatus.PARTIAL
        )
        db.add(batch)
        db.commit()
        
        return {
            "success": result["success"],
            "message": result["message"],
            "total_records": result["total_records"],
            "processed_records": result["processed_records"],
            "skipped_records": result["skipped_records"],
            "errors": result.get("errors", []),
            "batch_id": batch_id
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"マッピングアップロード失敗: {str(e)}")