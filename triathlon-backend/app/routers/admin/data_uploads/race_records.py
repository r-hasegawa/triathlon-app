# app/routers/admin/data_uploads/race_records.py (完全修正版)

"""
app/routers/admin/data_upload/race_records.py
大会記録データアップロード機能（/upload/race-recordsエンドポイント）
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
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


@router.post("/upload/race-records")
async def upload_race_records(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    overwrite: bool = Form(True),  # 🆕 追加
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会記録データアップロード（FlexibleCSVService使用）"""
    
    for file in files:
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail=f"CSVファイルのみアップロード可能です: {file.filename}")
    
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="最低1つのCSVファイルが必要です")
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
    
    # 🆕 batch_idを先に生成
    batch_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_race_records_{len(files)}files"
    
    # 🆕 overwriteが有効な場合、既存の大会記録とバッチを削除
    if overwrite:
        from app.models.competition import RaceRecord
        
        # 既存のrace_recordsに紐づくbatch_idを取得
        existing_records = db.query(RaceRecord).filter_by(competition_id=competition_id).all()
        existing_batch_ids = set()
        for record in existing_records:
            if record.upload_batch_id:
                existing_batch_ids.add(record.upload_batch_id)
        
        # 既存レコードを削除
        deleted_count = db.query(RaceRecord).filter_by(competition_id=competition_id).delete()
        print(f"既存大会記録削除: {deleted_count}件")
        
        # 対応するUploadBatchレコードも削除
        if existing_batch_ids:
            deleted_batch_count = db.query(UploadBatch).filter(
                UploadBatch.batch_id.in_(existing_batch_ids),
                UploadBatch.sensor_type == SensorType.RACE_RECORD
            ).delete(synchronize_session=False)
            print(f"既存大会記録バッチ削除: {deleted_batch_count}件")
        
        db.commit()
    
    csv_service = FlexibleCSVService()
    
    try:
        # 🆕 batch_idを渡す
        result = await csv_service.process_race_record_data(
            race_files=files,
            competition_id=competition_id,
            db=db,
            batch_id=batch_id  # 🆕 追加
        )
        
        # UploadBatchレコード作成
        batch = UploadBatch(
            batch_id=batch_id,
            sensor_type=SensorType.RACE_RECORD,
            competition_id=competition_id,
            file_name=f"{len(files)}_files",
            total_records=result.get("total_csv_records", 0),
            success_records=result.get("saved_count", 0),
            failed_records=result.get("failed_count", 0),
            status=UploadStatus.SUCCESS if result.get("success") else UploadStatus.PARTIAL
        )
        db.add(batch)
        db.commit()
        
        result.update({
            "batch_id": batch_id,
            "competition_id": competition_id,
            "competition_name": competition.name,
            "upload_time": datetime.now().isoformat(),
            "uploaded_by": current_admin.admin_id
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"大会記録アップロード失敗: {str(e)}")