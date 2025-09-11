"""
app/routers/admin.py (完全新システム版)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, date

from app.database import get_db
from app.models.user import User, AdminUser
from app.models.competition import Competition
from app.models.flexible_sensor_data import RawSensorData, FlexibleSensorMapping
from app.schemas.user import UserCreate, UserUpdate, UserResponse, AdminResponse
from app.utils.dependencies import get_current_admin
from app.utils.security import get_password_hash

router = APIRouter(prefix="/admin", tags=["admin"])

# === 管理者情報取得 ===
@router.get("/me", response_model=AdminResponse)
async def get_admin_info(current_admin: AdminUser = Depends(get_current_admin)):
    return current_admin

# === ユーザー管理 ===
@router.get("/users")
async def get_users_with_stats(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """ユーザー一覧取得"""
    
    query = db.query(User)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.user_id.like(search_term)) |
            (User.username.like(search_term)) |
            (User.full_name.like(search_term))
        )
    
    users = query.offset(skip).limit(limit).all()
    
    # 新システムでの統計情報取得
    users_with_stats = []
    for user in users:
        # 新システムでのセンサー数取得
        sensor_count = db.query(func.count(FlexibleSensorMapping.id))\
                        .filter_by(user_id=user.user_id, is_active=True)\
                        .scalar() or 0
        
        # 最新データ日時取得
        last_data = db.query(func.max(RawSensorData.timestamp))\
                      .filter_by(mapped_user_id=user.user_id)\
                      .scalar()
        
        user_data = {
            "id": user.id,
            "user_id": user.user_id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "sensor_count": sensor_count,
            "last_data_at": last_data.isoformat() if last_data else None
        }
        users_with_stats.append(user_data)
    
    return users_with_stats

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """ユーザー作成"""
    existing_user = db.query(User).filter(
        (User.user_id == user_data.user_id) | 
        (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID or username already exists"
        )
    
    user = User(
        user_id=user_data.user_id,
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """ユーザー更新"""
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_data = user_data.dict(exclude_unset=True)
    
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """ユーザー削除"""
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": f"User {user_id} deleted successfully"}

# === 大会管理 ===
@router.get("/competitions")
async def get_competitions(
    active_only: bool = Query(False),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """大会一覧取得"""
    query = db.query(Competition)
    
    if active_only:
        query = query.filter(Competition.is_active == True)
    
    competitions = query.order_by(desc(Competition.created_at)).all()
    
    return [
        {
            "id": comp.id,
            "competition_id": comp.competition_id,
            "name": comp.name,
            "date": comp.date.isoformat() if comp.date else None,
            "location": comp.location,
            "description": comp.description,
            "is_active": comp.is_active,
            "created_at": comp.created_at.isoformat(),
            "participant_count": 0,  # 🔄 後で実装
            "sensor_data_count": db.query(func.count(RawSensorData.id))\
                                  .filter_by(competition_id=comp.competition_id)\
                                  .scalar() or 0
        }
        for comp in competitions
    ]

# === システム統計 ===
@router.get("/stats")
async def get_system_stats(
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """システム統計情報取得（新システム版）"""
    
    try:
        stats = {
            "total_users": db.query(func.count(User.id)).scalar(),
            "active_users": db.query(func.count(User.id)).filter(User.is_active == True).scalar(),
            "total_competitions": db.query(func.count(Competition.id)).scalar(),
            "active_competitions": db.query(func.count(Competition.id)).filter(Competition.is_active == True).scalar(),
            "total_sensor_records": db.query(func.count(RawSensorData.id)).scalar(),
            "mapped_sensor_records": db.query(func.count(RawSensorData.id))\
                                      .filter(RawSensorData.mapping_status == "mapped")\
                                      .scalar(),
            "unmapped_sensor_records": db.query(func.count(RawSensorData.id))\
                                        .filter(RawSensorData.mapping_status == "unmapped")\
                                        .scalar()
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )

# === 🆕 新システム専用エンドポイント ===
@router.get("/unmapped-data-summary")
async def get_unmapped_data_summary_admin(
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """未マッピングデータサマリー（管理者用）"""
    
    from app.services.flexible_csv_service import FlexibleCSVService
    csv_service = FlexibleCSVService()
    
    return csv_service.get_unmapped_data_summary(db)