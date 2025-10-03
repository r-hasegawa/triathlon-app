from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    # 🔧 timezone=True を削除（SQLite/PostgreSQL両対応）
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # 🔧 循環参照を避けるためリレーションを削除
    # relationshipは flexible_sensor_data.py で定義
    
    def __repr__(self):
        return f"<User(user_id='{self.user_id}', username='{self.username}')>"

class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(String(50), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="admin")  # admin, super_admin
    is_active = Column(Boolean, default=True)
    # 🔧 timezone=True を削除（SQLite/PostgreSQL両対応）
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<AdminUser(admin_id='{self.admin_id}', role='{self.role}')>"