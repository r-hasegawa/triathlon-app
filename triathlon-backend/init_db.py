"""
データベース初期化スクリプト（修正版）
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.database import engine, Base
from app.utils.security import get_password_hash
from sqlalchemy.orm import sessionmaker

# 🔄 必要なモデルのみ個別にインポート（重複を避ける）
from app.models.user import User, AdminUser
from app.models.competition import Competition, RaceRecord
from app.models.flexible_sensor_data import (
    FlexibleSensorMapping,
    SkinTemperatureData, CoreTemperatureData, 
    HeartRateData, WBGTData
)

def drop_all_tables():
    """既存テーブルを全削除"""
    print("🗑️  Dropping all existing tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped!")

def create_tables():
    """全テーブル作成（新設計）"""
    print("🏗️  Creating new database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ New tables created successfully!")
    
    # 作成されたテーブル一覧を表示
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"📋 Created tables: {', '.join(tables)}")

def create_admin_user():
    """初期管理者アカウント作成"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        existing_admin = db.query(AdminUser).filter_by(admin_id="admin").first()
        if existing_admin:
            print("⚠️  Admin user already exists!")
            return
        
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
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_data():
    """サンプルデータ作成"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # サンプル大会作成
        sample_comp = Competition(
            name="2025年トライアスロン大会",
            location="お台場",
            description="マルチセンサーテスト大会"
        )
        db.add(sample_comp)
        db.flush()  # IDを取得するため
        
        # サンプルユーザー作成（正しいフィールド名を使用）
        sample_user = User(
            user_id="test_user_001",
            username="test_taro",
            full_name="テスト太郎",  # ✅ 正しいフィールド名
            email="test@example.com",
            hashed_password=get_password_hash("password123")
        )
        db.add(sample_user)
        
        # 追加サンプルユーザー
        sample_user2 = User(
            user_id="test_user_002",
            username="test_hanako",
            full_name="テスト花子",
            email="hanako@example.com", 
            hashed_password=get_password_hash("password123")
        )
        db.add(sample_user2)
        
        db.commit()
        print("✅ Sample data created!")
        print(f"   Competition ID: {sample_comp.competition_id}")
        print(f"   User 1 ID: {sample_user.user_id}")
        print(f"   User 2 ID: {sample_user2.user_id}")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

def create_sample_sensor_data():
    """サンプルセンサーデータ作成"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        from datetime import datetime, timedelta
        import json
        
        # 大会とユーザーを取得
        competition = db.query(Competition).first()
        users = db.query(User).all()
        
        if not competition or not users:
            print("⚠️  No competition or users found. Skipping sensor data creation.")
            return
        
        # 各ユーザーに対してサンプルセンサーデータを作成
        base_time = datetime.now() - timedelta(hours=2)
        
        for i, user in enumerate(users):
            sensor_id = f"SENSOR_{user.user_id[-3:]}"  # test_user_001 -> SENSOR_001
            
            # 30分間のデータを5分間隔で作成
            for j in range(6):
                timestamp = base_time + timedelta(minutes=j * 5)
                temperature = 36.0 + (j * 0.1) + (i * 0.2)  # 体温シミュレーション
                
                # RawSensorDataとして保存
                raw_data = RawSensorData(
                    sensor_id=sensor_id,
                    sensor_type="skin_temperature",
                    competition_id=competition.competition_id,
                    timestamp=timestamp,
                    data_values=json.dumps({
                        "temperature": temperature,
                        "location": "forehead",
                        "ambient_temp": 25.0
                    }),
                    raw_data=f"{sensor_id},{timestamp},{temperature},forehead,25.0",
                    mapping_status="unmapped",  # 最初は未マッピング
                    upload_batch_id=f"batch_{i+1}",
                    data_source="sample_data"
                )
                db.add(raw_data)
        
        db.commit()
        print("✅ Sample sensor data created!")
        print(f"   Created data for {len(users)} users with 6 data points each")
        
    except Exception as e:
        print(f"❌ Error creating sample sensor data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Recreating Triathlon Database from scratch...")
    
    # Step 1: 既存DB削除
    drop_all_tables()
    
    # Step 2: 新テーブル作成
    create_tables()
    
    # Step 3: 初期管理者作成
    create_admin_user()
    
    # Step 4: サンプルデータ作成
    create_sample_data()
    
    # Step 5: サンプルセンサーデータ作成
    create_sample_sensor_data()
    
    print("🎉 Database recreation completed!")
    print("\n📝 Next steps:")
    print("1. Start backend: uvicorn app.main:app --reload")
    print("2. Test MultiSensorUpload page")
    print("3. Upload test CSV files")
    print("\n🔗 Login credentials:")
    print("   Admin: admin / admin123")
    print("   User 1: test_taro / password123")
    print("   User 2: test_hanako / password123")