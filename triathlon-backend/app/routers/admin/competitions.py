"""
app/routers/admin/competitions.py
大会管理機能（JSONボディ対応版）
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models.user import AdminUser
from app.models.competition import Competition, RaceRecord
from app.models.flexible_sensor_data import (
    SkinTemperatureData, CoreTemperatureData, HeartRateData, 
    WBGTData, FlexibleSensorMapping
)
from app.utils.dependencies import get_current_admin

router = APIRouter()


# 🆕 Pydanticスキーマを追加
class CompetitionCreate(BaseModel):
    name: str
    date: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None


@router.post("/competitions")
async def create_competition(
    competition_data: CompetitionCreate = Body(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """新規大会作成（仕様書1.2対応・JSONボディ版）"""
    
    # 大会名重複チェック
    existing_competition = db.query(Competition).filter_by(name=competition_data.name).first()
    if existing_competition:
        raise HTTPException(
            status_code=400,
            detail=f"大会名 '{competition_data.name}' は既に存在します"
        )
    
    try:
        # 大会IDを自動生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        competition_id = f"comp_{timestamp}"
        
        # 日付の変換
        competition_date = None
        if competition_data.date:
            try:
                competition_date = datetime.strptime(competition_data.date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="日付は YYYY-MM-DD 形式で入力してください"
                )
        
        # 大会作成
        competition = Competition(
            competition_id=competition_id,
            name=competition_data.name,
            date=competition_date,
            location=competition_data.location
        )
        
        db.add(competition)
        db.commit()
        db.refresh(competition)
        
        return {
            "message": f"大会 '{competition_data.name}' を作成しました",
            "competition": {
                "competition_id": competition.competition_id,
                "name": competition.name,
                "date": competition.date.isoformat() if competition.date else None,
                "location": competition.location
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"大会作成エラー: {str(e)}"
        )


@router.get("/competitions")
async def list_competitions(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会一覧取得（仕様書4.3対応）"""
    
    query = db.query(Competition)
    
    # 並び替え：日付の新しい順
    competitions = query.order_by(
        desc(Competition.date),
    ).all()
    
    return {
        "competitions": [
            {
                "competition_id": comp.competition_id,
                "name": comp.name,
                "date": comp.date.isoformat() if comp.date else None,
                "location": comp.location
            }
            for comp in competitions
        ]
    }


@router.delete("/competitions/{competition_id}")
async def delete_competition(
    competition_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会削除（仕様書4.3対応 - 関連データ全削除）"""
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(
            status_code=404,
            detail="大会が見つかりません"
        )
    
    competition_name = competition.name
    
    try:
        # 削除統計（削除前にカウント）
        race_records_count = db.query(RaceRecord).filter_by(competition_id=competition_id).count()
        wbgt_count = db.query(WBGTData).filter_by(competition_id=competition_id).count()
        mapping_count = db.query(FlexibleSensorMapping).filter_by(competition_id=competition_id).count()
        
        # センサーデータのカウント
        skin_temp_count = db.query(SkinTemperatureData).filter_by(competition_id=competition_id).count()
        core_temp_count = db.query(CoreTemperatureData).filter_by(competition_id=competition_id).count()
        heart_rate_count = db.query(HeartRateData).filter_by(competition_id=competition_id).count()
        
        # バッチ情報のカウント
        from app.models.flexible_sensor_data import UploadBatch
        batch_count = db.query(UploadBatch).filter_by(competition_id=competition_id).count()
        
        # 1. 大会記録を削除
        db.query(RaceRecord).filter_by(competition_id=competition_id).delete()
        
        # 2. WBGT データを削除
        db.query(WBGTData).filter_by(competition_id=competition_id).delete()
        
        # 3. センサーマッピングを削除
        db.query(FlexibleSensorMapping).filter_by(competition_id=competition_id).delete()
        
        # 4. センサーデータを削除
        db.query(SkinTemperatureData).filter_by(competition_id=competition_id).delete()
        db.query(CoreTemperatureData).filter_by(competition_id=competition_id).delete()
        db.query(HeartRateData).filter_by(competition_id=competition_id).delete()
        
        # 5. アップロードバッチ情報を削除
        db.query(UploadBatch).filter_by(competition_id=competition_id).delete()
        
        # 6. 大会本体を削除
        db.delete(competition)
        
        db.commit()
        
        return {
            "message": f"大会 '{competition_name}' とその関連データを削除しました",
            "deleted_data": {
                "race_records": race_records_count,
                "wbgt_records": wbgt_count,
                "mappings": mapping_count,
                "skin_temperature": skin_temp_count,
                "core_temperature": core_temp_count,
                "heart_rate": heart_rate_count,
                "upload_batches": batch_count
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"大会削除エラー: {str(e)}"
        )