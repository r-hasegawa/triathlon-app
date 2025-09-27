"""
app/routers/admin/data_upload/race_records.py
大会記録データアップロード機能（/upload/race-recordsエンドポイント）
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.user import AdminUser
from app.models.competition import Competition, RaceRecord
from app.utils.dependencies import get_current_admin
from app.services.flexible_csv_service import FlexibleCSVService


router = APIRouter()


@router.post("/upload/race-records")
async def upload_race_records(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
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
    
    csv_service = FlexibleCSVService()
    
    try:
        file_info = []
        
        for file in files:
            content = await file.read()
            await file.seek(0)
        
        result = await csv_service.process_race_record_data(
            race_files=files,
            competition_id=competition_id,
            db=db
        )
        
        result.update({
            "competition_id": competition_id,
            "competition_name": competition.name,
            "uploaded_files": file_info,
            "upload_time": datetime.now().isoformat(),
            "uploaded_by": current_admin.admin_id
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"大会記録アップロード失敗: {str(e)}")


@router.get("/race-records/status")
async def get_race_records_status(
    competition_id: str = Query(None),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会記録アップロード状況取得"""
    
    try:
        from app.models.competition import RaceRecord
        query = db.query(RaceRecord)
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        
        records = query.all()
        
        total_records = len(records)
        mapped_records = len([r for r in records if r.user_id is not None])
        unmapped_records = total_records - mapped_records
        
        by_competition = {}
        for record in records:
            comp_id = record.competition_id
            if comp_id not in by_competition:
                competition = db.query(Competition).filter_by(competition_id=comp_id).first()
                by_competition[comp_id] = {
                    "competition_name": competition.name if competition else "Unknown",
                    "total_records": 0,
                    "mapped_records": 0,
                    "unmapped_records": 0
                }
            
            by_competition[comp_id]["total_records"] += 1
            if record.user_id:
                by_competition[comp_id]["mapped_records"] += 1
            else:
                by_competition[comp_id]["unmapped_records"] += 1
        
        return {
            "success": True,
            "total_records": total_records,
            "mapped_records": mapped_records,
            "unmapped_records": unmapped_records,
            "mapping_coverage": round((mapped_records / total_records * 100), 2) if total_records > 0 else 0,
            "competitions": by_competition,
            "competition_count": len(by_competition)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"大会記録状況取得エラー: {str(e)}")