"""
setup_database.py (完全版 - 大会記録機能対応)
"""

import sys
import os
import csv
from pathlib import Path
from datetime import date, datetime, timedelta
import random

sys.path.append(str(Path(__file__).parent))

from app.database import engine, Base, SessionLocal
from app.models.user import User, AdminUser
from app.models.competition import Competition, RaceRecord  
from app.models.flexible_sensor_data import (
    SkinTemperatureData, CoreTemperatureData, 
    HeartRateData, WBGTData, UploadBatch,
    FlexibleSensorMapping, SensorType, UploadStatus
)
from app.utils.security import get_password_hash

def create_tables():
    """全テーブル作成（修正版のモデル含む）"""
    print("🗄️  Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")
    print("📊 Sensor data tables included:")
    print("   - race_records (大会記録 - LAP・区間データ対応)")
    print("   - skin_temperature_data (halshare対応)")
    print("   - core_temperature_data (e-Celcius対応)")
    print("   - heart_rate_data (TCX対応)")
    print("   - wbgt_data (環境データ)")
    print("   - mappings (マッピング)")
    print("   - upload_batches (バッチ管理)")

def create_initial_users():
    """初期ユーザー・管理者作成"""
    db = SessionLocal()
    
    try:
        # 管理者作成
        if not db.query(AdminUser).filter_by(admin_id="admin").first():
            admin_user = AdminUser(
                admin_id="admin",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                full_name="システム管理者",
                role="super_admin"
            )
            db.add(admin_user)
            print("✅ Admin user created (username: admin, password: admin123)")
        
        # テストユーザー作成
        test_users = [
            ("user001", "testuser1", "田中太郎", "user001@example.com"),
            ("user002", "testuser2", "佐藤花子", "user002@example.com"),
            ("user003", "testuser3", "山田次郎", "user003@example.com"),
            ("user004", "testuser4", "鈴木美香", "user004@example.com"),
            ("user005", "testuser5", "高橋健太", "user005@example.com"),
        ]
        
        for user_id, username, full_name, email in test_users:
            if not db.query(User).filter_by(user_id=user_id).first():
                user = User(
                    user_id=user_id,
                    username=username,
                    hashed_password=get_password_hash("password123"),
                    full_name=full_name,
                    email=email
                )
                db.add(user)
                print(f"✅ Test user created: {username} (password: password123)")
        
        db.commit()
        
    except Exception as e:
        print(f"❌ Error creating users: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_competitions():
    """サンプル大会データ作成"""
    db = SessionLocal()
    
    try:
        # サンプル大会データ
        competitions = [
            {
                "competition_id": "comp_2025_001",
                "name": "第1回東京湾トライアスロン2025",
                "date": date(2025, 7, 27),
                "location": "東京都江東区お台場海浜公園",
            },
            {
                "competition_id": "comp_2025_002", 
                "name": "真夏の湘南オープンウォータートライアスロン",
                "date": date(2025, 8, 10),
                "location": "神奈川県藤沢市湘南海岸",
            },
            {
                "competition_id": "comp_2025_003",
                "name": "秋季アイアンマン研究大会",
                "date": date(2025, 10, 5),
                "location": "千葉県館山市",
            }
        ]
        
        competition_ids = []
        
        for comp_data in competitions:
            if not db.query(Competition).filter_by(competition_id=comp_data["competition_id"]).first():
                competition = Competition(**comp_data)
                db.add(competition)
                competition_ids.append(comp_data["competition_id"])
                print(f"✅ Competition created: {comp_data['name']}")
        
        db.commit()
        return competition_ids
        
    except Exception as e:
        print(f"❌ Error creating competitions: {e}")
        db.rollback()
        return []
    finally:
        db.close()

def main():
    """メイン実行関数（完全版）"""
    print("🚀 Initializing Triathlon Database with Complete Race Record Support...")
    print("=" * 80)
    
    # ステップ1: テーブル作成（修正版モデル）
    create_tables()
    print()
    
    # ステップ2: 初期ユーザー作成
    print("👥 Creating initial users...")
    create_initial_users()
    print()
    
    # ステップ3: 大会データ作成
    print("🏆 Creating sample competitions...")
    competition_ids = create_sample_competitions()
    print()
    
    print("=" * 80)
    print("🎉 Database initialization completed with complete race record support!")
    print("🆕 Race record CSV upload functionality is now ready for testing!")
    print()
    print("📝 Next steps:")
    print("1. uvicorn app.main:app --reload")
    print("2. Go to http://localhost:8000/docs")
    print("3. Test /admin/upload/race-records endpoint")
    print("4. Use sample CSV files from sample_race_records/ directory")

if __name__ == "__main__":
    main()