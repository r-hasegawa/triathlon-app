"""
app/routers/competition.py

大会管理APIエンドポイント - 完全新規作成版
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel

from app.database import get_db
from app.models import Competition, RaceRecord, WBGTData
from app.utils.dependencies import get_current_admin, get_current_user

router = APIRouter(prefix="/competitions", tags=["competitions"])

# === Pydantic スキーマ定義 ===

class CompetitionCreate(BaseModel):
    name: str
    date: Optional[date] = None
    location: Optional[str] = None
    description: Optional[str] = None

class CompetitionUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class CompetitionResponse(BaseModel):
    id: int
    competition_id: str
    name: str
    date: Optional[date]
    location: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    participant_count: Optional[int] = 0
    sensor_data_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class RaceRecordCreate(BaseModel):
    user_id: str
    race_number: Optional[str] = None
    swim_start_time: Optional[datetime] = None
    swim_finish_time: Optional[datetime] = None
    bike_start_time: Optional[datetime] = None
    bike_finish_time: Optional[datetime] = None
    run_start_time: Optional[datetime] = None
    run_finish_time: Optional[datetime] = None
    notes: Optional[str] = None

class RaceRecordResponse(BaseModel):
    id: int
    competition_id: str
    user_id: str
    race_number: Optional[str]
    swim_start_time: Optional[datetime]
    swim_finish_time: Optional[datetime]
    bike_start_time: Optional[datetime]
    bike_finish_time: Optional[datetime]
    run_start_time: Optional[datetime]
    run_finish_time: Optional[datetime]
    total_start_time: Optional[datetime]
    total_finish_time: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# === 管理者用エンドポイント ===

@router.post("/", response_model=CompetitionResponse)
async def create_competition(
    competition: CompetitionCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """新規大会作成"""
    try:
        # 同名大会の重複チェック
        existing = db.query(Competition).filter_by(name=competition.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Competition with name '{competition.name}' already exists"
            )
        
        # 新規大会作成
        db_competition = Competition(**competition.dict())
        db.add(db_competition)
        db.commit()
        db.refresh(db_competition)
        
        return CompetitionResponse.from_orm(db_competition)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create competition: {str(e)}"
        )

@router.get("/", response_model=List[CompetitionResponse])
async def list_competitions(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """大会一覧取得（管理者用）"""
    query = db.query(Competition)
    
    if not include_inactive:
        query = query.filter(Competition.is_active == True)
    
    competitions = query.order_by(Competition.date.desc()).all()
    
    # 統計情報を追加
    result = []
    for comp in competitions:
        comp_data = CompetitionResponse.from_orm(comp)
        
        # 参加者数
        participant_count = db.query(RaceRecord).filter_by(competition_id=comp.competition_id).count()
        comp_data.participant_count = participant_count
        
        # センサデータ数
        from app.models import SensorData
        sensor_data_count = db.query(SensorData).filter_by(competition_id=comp.competition_id).count()
        comp_data.sensor_data_count = sensor_data_count
        
        result.append(comp_data)
    
    return result

@router.put("/{competition_id}", response_model=CompetitionResponse)
async def update_competition(
    competition_id: str,
    competition_update: CompetitionUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """大会情報更新"""
    db_competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not db_competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found"
        )
    
    # 更新データを適用
    update_data = competition_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_competition, field, value)
    
    try:
        db.commit()
        db.refresh(db_competition)
        return CompetitionResponse.from_orm(db_competition)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update competition: {str(e)}"
        )

@router.delete("/{competition_id}")
async def delete_competition(
    competition_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """大会削除（関連データすべて削除）"""
    db_competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not db_competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found"
        )
    
    try:
        # カスケード削除で関連データもすべて削除される
        db.delete(db_competition)
        db.commit()
        
        return {"message": f"Competition '{db_competition.name}' and all related data deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete competition: {str(e)}"
        )

# === 大会記録管理 ===

@router.post("/{competition_id}/race-records", response_model=RaceRecordResponse)
async def create_race_record(
    competition_id: str,
    race_record: RaceRecordCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """大会記録作成"""
    # 大会存在チェック
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found"
        )
    
    # ユーザー存在チェック
    from app.models import User
    user = db.query(User).filter_by(user_id=race_record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        db_record = RaceRecord(
            competition_id=competition_id,
            **race_record.dict()
        )
        
        # 総合記録を自動計算
        db_record.calculate_total_times()
        
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        
        return RaceRecordResponse.from_orm(db_record)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create race record: {str(e)}"
        )

@router.get("/{competition_id}/race-records", response_model=List[RaceRecordResponse])
async def get_race_records(
    competition_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """大会記録一覧取得"""
    records = db.query(RaceRecord).filter_by(competition_id=competition_id).all()
    return [RaceRecordResponse.from_orm(record) for record in records]

# === 被験者用エンドポイント ===

@router.get("/my-competitions", response_model=List[CompetitionResponse])
async def get_my_competitions(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """自分が参加した大会一覧"""
    # 自分のレース記録がある大会を取得
    competitions = db.query(Competition).join(RaceRecord).filter(
        RaceRecord.user_id == current_user.user_id,
        Competition.is_active == True
    ).distinct().order_by(Competition.date.desc()).all()
    
    return [CompetitionResponse.from_orm(comp) for comp in competitions]

@router.get("/{competition_id}")
async def get_competition_detail(
    competition_id: str,
    db: Session = Depends(get_db)
):
    """大会詳細情報取得（認証不要）"""
    competition = db.query(Competition).filter_by(
        competition_id=competition_id,
        is_active=True
    ).first()
    
    if not competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found"
        )
    
    return CompetitionResponse.from_orm(competition)

# === 公開エンドポイント ===

@router.get("/public/list", response_model=List[CompetitionResponse])
async def get_public_competitions(
    db: Session = Depends(get_db)
):
    """公開大会一覧（認証不要）"""
    competitions = db.query(Competition).filter(
        Competition.is_active == True
    ).order_by(Competition.date.desc()).all()
    
    result = []
    for comp in competitions:
        comp_data = CompetitionResponse.from_orm(comp)
        result.append(comp_data)
    
    return result