from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.user import User, AdminUser
from app.schemas.auth import LoginResponse, Token
from app.schemas.user import UserCreate, UserResponse, AdminCreate, AdminResponse
from app.utils.security import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.utils.dependencies import get_current_user, get_current_admin


# 認証情報変更用スキーマ
class AdminCredentialsChange(BaseModel):
    new_username: str = Field(..., min_length=3, max_length=100)
    new_password: str = Field(..., min_length=8, max_length=100)

class UserCredentialsChange(BaseModel):
    new_username: str = Field(..., min_length=3, max_length=100)
    new_password: str = Field(..., min_length=6, max_length=100)

router = APIRouter()

@router.post("/admin/change-credentials")
async def change_admin_credentials(
    credentials: AdminCredentialsChange,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """管理者のユーザー名とパスワードを変更"""
    
    # 新しいユーザー名が既に存在するかチェック（自分自身を除く）
    existing_admin = db.query(AdminUser).filter(
        AdminUser.username == credentials.new_username,
        AdminUser.id != current_admin.id
    ).first()
    
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # ユーザー名とパスワードを更新
    current_admin.username = credentials.new_username
    current_admin.hashed_password = get_password_hash(credentials.new_password)
    
    db.commit()
    db.refresh(current_admin)
    
    return {
        "message": "Admin credentials updated successfully",
        "username": current_admin.username,
        "admin_id": current_admin.admin_id
    }

@router.post("/user/change-credentials")
async def change_user_credentials(
    credentials: UserCredentialsChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ユーザーのユーザー名とパスワードを変更"""
    
    # 新しいユーザー名が既に存在するかチェック（自分自身を除く）
    existing_user = db.query(User).filter(
        User.username == credentials.new_username,
        User.id != current_user.id
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # ユーザー名とパスワードを更新
    current_user.username = credentials.new_username
    current_user.hashed_password = get_password_hash(credentials.new_password)
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "User credentials updated successfully",
        "username": current_user.username,
        "user_id": current_user.user_id
    }

@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """ユーザー・管理者ログイン"""
    username = form_data.username
    password = form_data.password
    
    # まずユーザーとして検索
    user = db.query(User).filter_by(username=username).first()
    if user and user.is_active and verify_password(password, user.hashed_password):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.user_id, "is_admin": False},
            expires_delta=access_token_expires
        )
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user_info={
                "user_id": user.user_id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email,
                "is_admin": False
            },
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    # 管理者として検索
    admin = db.query(AdminUser).filter_by(username=username).first()
    if admin and admin.is_active and verify_password(password, admin.hashed_password):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": admin.admin_id, "is_admin": True},
            expires_delta=access_token_expires
        )
        
        admin.last_login = datetime.utcnow()
        db.commit()
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer", 
            user_info={
                "admin_id": admin.admin_id,
                "username": admin.username,
                "full_name": admin.full_name,
                "role": admin.role,
                "is_admin": True
            },
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.post("/register/user", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """ユーザー登録（開発・テスト用）"""
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

@router.post("/register/admin", response_model=AdminResponse)
async def register_admin(
    admin_data: AdminCreate,
    db: Session = Depends(get_db)
):
    """管理者登録（開発・テスト用）"""
    existing_admin = db.query(AdminUser).filter(
        (AdminUser.admin_id == admin_data.admin_id) | 
        (AdminUser.username == admin_data.username)
    ).first()
    
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin ID or username already exists"
        )
    
    admin = AdminUser(
        admin_id=admin_data.admin_id,
        username=admin_data.username,
        full_name=admin_data.full_name,
        role=admin_data.role,
        hashed_password=get_password_hash(admin_data.password)
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    return admin

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """現在のユーザー情報取得"""
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "is_admin": False
    }

@router.post("/logout")
async def logout():
    """ログアウト"""
    return {"message": "Successfully logged out"}