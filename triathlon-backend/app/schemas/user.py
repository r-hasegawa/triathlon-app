from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

# ユーザー基本スキーマ
class UserBase(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=50)
    username: str = Field(..., min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# 管理者スキーマ
class AdminBase(BaseModel):
    admin_id: str = Field(..., min_length=3, max_length=50)
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None
    role: str = "admin"

class AdminCreate(AdminBase):
    password: str = Field(..., min_length=8, max_length=100)

class AdminResponse(AdminBase):
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True