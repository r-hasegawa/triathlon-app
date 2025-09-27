"""
app/routers/admin/race_records.py
大会記録関連機能（/upload/以外のエンドポイント）
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import AdminUser
from app.models.competition import Competition, RaceRecord
from app.utils.dependencies import get_current_admin


router = APIRouter()


@router.get("/race-records")
async def get_race_records(
    competition_id: str = Query(None),
    user_id: str = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会記録一覧取得"""
    
    try:
        query = db.query(RaceRecord)
        
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        total_count = query.count()
        records = query.offset(offset).limit(limit).all()
        
        records_data = []
        for record in records:
            competition = db.query(Competition).filter_by(competition_id=record.competition_id).first()
            records_data.append({
                "record_id": record.record_id,
                "competition_id": record.competition_id,
                "competition_name": competition.name if competition else "Unknown",
                "user_id": record.user_id,
                "participant_name": record.participant_name,
                "bib_number": record.bib_number,
                "race_time": record.race_time,
                "finish_position": record.finish_position,
                "category": record.category,
                "age_group": record.age_group,
                "gender": record.gender,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None
            })
        
        return {
            "success": True,
            "total_count": total_count,
            "records": records_data,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(records) < total_count
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"大会記録取得エラー: {str(e)}")


@router.get("/race-records/{record_id}")
async def get_race_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """個別大会記録取得"""
    
    try:
        record = db.query(RaceRecord).filter_by(record_id=record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="大会記録が見つかりません")
        
        competition = db.query(Competition).filter_by(competition_id=record.competition_id).first()
        
        return {
            "success": True,
            "record": {
                "record_id": record.record_id,
                "competition_id": record.competition_id,
                "competition_name": competition.name if competition else "Unknown",
                "user_id": record.user_id,
                "participant_name": record.participant_name,
                "bib_number": record.bib_number,
                "race_time": record.race_time,
                "finish_position": record.finish_position,
                "category": record.category,
                "age_group": record.age_group,
                "gender": record.gender,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"大会記録取得エラー: {str(e)}")


@router.put("/race-records/{record_id}/mapping")
async def update_race_record_mapping(
    record_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会記録のユーザーマッピング更新"""
    
    try:
        record = db.query(RaceRecord).filter_by(record_id=record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="大会記録が見つかりません")
        
        # ユーザーIDの検証（必要に応じて）
        # user = db.query(User).filter_by(user_id=user_id).first()
        # if not user:
        #     raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
        record.user_id = user_id
        db.commit()
        
        return {
            "success": True,
            "message": f"記録ID {record_id} をユーザーID {user_id} にマッピングしました",
            "record_id": record_id,
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"マッピング更新エラー: {str(e)}")


@router.delete("/race-records/{record_id}")
async def delete_race_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会記録削除"""
    
    try:
        record = db.query(RaceRecord).filter_by(record_id=record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="大会記録が見つかりません")
        
        db.delete(record)
        db.commit()
        
        return {
            "success": True,
            "message": f"記録ID {record_id} を削除しました",
            "record_id": record_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"記録削除エラー: {str(e)}")