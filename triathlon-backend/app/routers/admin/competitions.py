"""
app/routers/admin/competitions.py
大会管理機能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.user import AdminUser
from app.models.competition import Competition, RaceRecord
from app.models.flexible_sensor_data import (
    SkinTemperatureData, CoreTemperatureData, HeartRateData, 
    WBGTData, FlexibleSensorMapping
)
from app.utils.dependencies import get_current_admin

router = APIRouter()


@router.post("/competitions")
async def create_competition(
    name: str,
    date: str = None,
    location: str = None,
    description: str = None,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """新規大会作成（仕様書1.2対応）"""
    
    # 大会名重複チェック
    existing_competition = db.query(Competition).filter_by(name=name).first()
    if existing_competition:
        raise HTTPException(
            status_code=400,
            detail=f"大会名 '{name}' は既に存在します"
        )
    
    try:
        # 大会IDを自動生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        competition_id = f"comp_{timestamp}"
        
        # 日付の変換
        competition_date = None
        if date:
            try:
                competition_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="日付は YYYY-MM-DD 形式で入力してください"
                )
        
        # 大会作成
        competition = Competition(
            competition_id=competition_id,
            name=name,
            date=competition_date,
            location=location,
            description=description
        )
        
        db.add(competition)
        db.commit()
        db.refresh(competition)
        
        return {
            "message": f"大会 '{name}' を作成しました",
            "competition": {
                "competition_id": competition.competition_id,
                "name": competition.name,
                "date": competition.date.isoformat() if competition.date else None,
                "location": competition.location,
                "description": competition.description,
                "created_at": competition.created_at.isoformat() if competition.created_at else None
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
    include_stats: bool = True,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会一覧取得（管理者用）"""
    try:
        competitions = db.query(Competition).order_by(desc(Competition.date)).all()
        
        competition_list = []
        for comp in competitions:
            comp_data = {
                "competition_id": comp.competition_id,
                "name": comp.name,
                "date": comp.date.isoformat() if comp.date else None,
                "location": comp.location,
                "description": comp.description,
                "created_at": comp.created_at.isoformat() if comp.created_at else None
            }
            
            if include_stats:
                # 参加者数
                participant_count = db.query(RaceRecord).filter_by(
                    competition_id=comp.competition_id
                ).count()
                
                # 関連データ数
                wbgt_count = db.query(WBGTData).filter_by(
                    competition_id=comp.competition_id
                ).count()
                
                # マッピング数
                mapping_count = db.query(FlexibleSensorMapping).filter_by(
                    competition_id=comp.competition_id
                ).count()
                
                comp_data["stats"] = {
                    "participants": participant_count,
                    "wbgt_records": wbgt_count,
                    "mappings": mapping_count
                }
            
            competition_list.append(comp_data)
        
        return {
            "competitions": competition_list,
            "total": len(competition_list)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"大会一覧取得エラー: {str(e)}"
        )


@router.get("/competitions/{competition_id}")
async def get_competition_detail(
    competition_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会詳細取得"""
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(
            status_code=404,
            detail="大会が見つかりません"
        )
    
    try:
        # 参加者一覧
        race_records = db.query(RaceRecord).filter_by(
            competition_id=competition_id
        ).all()
        
        participants = []
        for record in race_records:
            from app.models.user import User
            user = db.query(User).filter_by(user_id=record.user_id).first()
            if user:
                participants.append({
                    "user_id": user.user_id,
                    "full_name": user.full_name,
                    "bib_number": record.bib_number,
                    "swim_start": record.swim_start.isoformat() if record.swim_start else None,
                    "swim_finish": record.swim_finish.isoformat() if record.swim_finish else None,
                    "bike_start": record.bike_start.isoformat() if record.bike_start else None,
                    "bike_finish": record.bike_finish.isoformat() if record.bike_finish else None,
                    "run_start": record.run_start.isoformat() if record.run_start else None,
                    "run_finish": record.run_finish.isoformat() if record.run_finish else None
                })
        
        # WBGT データ統計
        wbgt_count = db.query(WBGTData).filter_by(competition_id=competition_id).count()
        
        # マッピング情報
        mappings = db.query(FlexibleSensorMapping).filter_by(
            competition_id=competition_id
        ).all()
        
        return {
            "competition": {
                "competition_id": competition.competition_id,
                "name": competition.name,
                "date": competition.date.isoformat() if competition.date else None,
                "location": competition.location,
                "description": competition.description,
                "created_at": competition.created_at.isoformat() if competition.created_at else None
            },
            "participants": participants,
            "data_summary": {
                "participant_count": len(participants),
                "wbgt_records": wbgt_count,
                "mapping_count": len(mappings)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"大会詳細取得エラー: {str(e)}"
        )


@router.put("/competitions/{competition_id}")
async def update_competition(
    competition_id: str,
    name: str = None,
    date: str = None,
    location: str = None,
    description: str = None,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会情報更新"""
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(
            status_code=404,
            detail="大会が見つかりません"
        )
    
    try:
        # 更新可能なフィールドの処理
        if name is not None:
            # 名前重複チェック（自分以外）
            existing = db.query(Competition).filter(
                Competition.name == name,
                Competition.competition_id != competition_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"大会名 '{name}' は既に存在します"
                )
            competition.name = name
        
        if date is not None:
            try:
                competition.date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="日付は YYYY-MM-DD 形式で入力してください"
                )
        
        if location is not None:
            competition.location = location
        
        if description is not None:
            competition.description = description
        
        # updated_atが存在する場合は更新
        if hasattr(competition, 'updated_at'):
            competition.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(competition)
        
        return {
            "message": f"大会 '{competition.name}' を更新しました",
            "competition": {
                "competition_id": competition.competition_id,
                "name": competition.name,
                "date": competition.date.isoformat() if competition.date else None,
                "location": competition.location,
                "description": competition.description
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"大会更新エラー: {str(e)}"
        )


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
        
        # 1. 大会記録を削除
        db.query(RaceRecord).filter_by(competition_id=competition_id).delete()
        
        # 2. WBGT データを削除
        db.query(WBGTData).filter_by(competition_id=competition_id).delete()
        
        # 3. センサーマッピングを削除
        db.query(FlexibleSensorMapping).filter_by(competition_id=competition_id).delete()
        
        # 4. 大会本体を削除
        db.delete(competition)
        
        db.commit()
        
        return {
            "message": f"大会 '{competition_name}' (ID: {competition_id}) とその関連データを削除しました",
            "deleted_data": {
                "race_records": race_records_count,
                "wbgt_records": wbgt_count,
                "mappings": mapping_count
            },
            "note": "センサーデータは保持されます（正規化設計）"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"大会削除エラー: {str(e)}"
        )