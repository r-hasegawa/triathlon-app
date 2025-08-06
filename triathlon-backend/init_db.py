"""
データベース初期化スクリプト
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent))

from app.database import engine, Base
from app.models import User, AdminUser, SensorData, SensorMapping, UploadHistory
from app.utils.security import get_password_hash
from sqlalchemy.orm import sessionmaker

def create_tables():
    """全テーブル作成"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")

def create_admin_user():
    """初期管理者アカウント作成"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 既存管理者チェック
        existing_admin = db.query(AdminUser).filter_by(admin_id="admin").first()
        if existing_admin:
            print("⚠️  Admin user already exists!")
            return
        
        # 初期管理者作成
        admin_user = AdminUser(
            admin_id="admin",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            role="super_admin"
        )
        
        db.add(admin_user)
        db.commit()
        print("✅ Initial admin user created!")
        print("   Username: admin")
        print("   Password: admin123")
        print("   ⚠️  Please change password after first login!")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Initializing Triathlon Sensor Database...")
    create_tables()
    create_admin_user()
    print("🎉 Database initialization completed!")