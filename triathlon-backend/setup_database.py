#!/usr/bin/env python3
"""
データベース初期化とサンプルデータ作成スクリプト
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import random

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent))

from app.database import engine, Base, SessionLocal
from app.models.user import User, AdminUser
from app.models.sensor_data import SensorData, SensorMapping, UploadHistory
from app.utils.security import get_password_hash

def create_tables():
    """全テーブル作成"""
    print("🗄️  Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")

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

def create_sensor_mappings():
    """センサマッピング作成"""
    db = SessionLocal()
    
    try:
        mappings = [
            ("SENSOR_001", "user001", "田中太郎"),
            ("SENSOR_002", "user001", "田中太郎"),
            ("SENSOR_003", "user002", "佐藤花子"),
            ("SENSOR_004", "user003", "山田次郎"),
        ]
        
        for sensor_id, user_id, subject_name in mappings:
            if not db.query(SensorMapping).filter_by(sensor_id=sensor_id).first():
                mapping = SensorMapping(
                    sensor_id=sensor_id,
                    user_id=user_id,
                    subject_name=subject_name,
                    device_type="temperature_sensor"
                )
                db.add(mapping)
                print(f"✅ Sensor mapping created: {sensor_id} -> {user_id}")
        
        db.commit()
        
    except Exception as e:
        print(f"❌ Error creating sensor mappings: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_sensor_data():
    """サンプルセンサデータ作成"""
    db = SessionLocal()
    
    try:
        # 過去24時間のデータを生成
        end_time = datetime.now(datetime.UTC)
        start_time = end_time - timedelta(hours=24)
        
        sensors = ["SENSOR_001", "SENSOR_002", "SENSOR_003", "SENSOR_004"]
        user_mapping = {
            "SENSOR_001": "user001",
            "SENSOR_002": "user001", 
            "SENSOR_003": "user002",
            "SENSOR_004": "user003"
        }
        
        sample_data = []
        
        for sensor_id in sensors:
            current_time = start_time
            base_temp = random.uniform(36.0, 37.5)  # 基準体温
            
            while current_time <= end_time:
                # 時間による温度変化をシミュレート
                hour = current_time.hour
                if 6 <= hour <= 18:  # 日中は体温やや高め
                    temp_variation = random.uniform(-0.3, 0.5)
                else:  # 夜間は体温やや低め
                    temp_variation = random.uniform(-0.5, 0.2)
                
                # ランダムノイズ追加
                noise = random.uniform(-0.1, 0.1)
                temperature = base_temp + temp_variation + noise
                
                sensor_data = SensorData(
                    sensor_id=sensor_id,
                    user_id=user_mapping[sensor_id],
                    timestamp=current_time,
                    temperature=round(temperature, 2),
                    data_source="sample_data"
                )
                
                sample_data.append(sensor_data)
                current_time += timedelta(minutes=5)  # 5分間隔
        
        # バッチ挿入
        db.bulk_save_objects(sample_data)
        db.commit()
        
        print(f"✅ Sample sensor data created: {len(sample_data)} records")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_csv_files():
    """サンプルCSVファイル作成"""
    upload_dir = Path("uploads/csv")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # センサマッピングCSV
    mapping_data = [
        {"sensor_id": "SENSOR_005", "user_id": "user001", "subject_name": "田中太郎"},
        {"sensor_id": "SENSOR_006", "user_id": "user002", "subject_name": "佐藤花子"},
        {"sensor_id": "SENSOR_007", "user_id": "user003", "subject_name": "山田次郎"},
    ]
    
    mapping_df = pd.DataFrame(mapping_data)
    mapping_path = upload_dir / "sample_sensor_mapping.csv"
    mapping_df.to_csv(mapping_path, index=False, encoding='utf-8')
    print(f"✅ Sample mapping CSV created: {mapping_path}")
    
    # センサデータCSV
    sensor_data = []
    end_time = datetime.now(datetime.UTC)
    start_time = end_time - timedelta(hours=2)  # 直近2時間分
    
    for sensor_id in ["SENSOR_005", "SENSOR_006", "SENSOR_007"]:
        current_time = start_time
        base_temp = random.uniform(36.0, 37.5)
        
        while current_time <= end_time:
            temperature = base_temp + random.uniform(-0.3, 0.3)
            sensor_data.append({
                "sensor_id": sensor_id,
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "temperature": round(temperature, 2)
            })
            current_time += timedelta(minutes=1)  # 1分間隔
    
    data_df = pd.DataFrame(sensor_data)
    data_path = upload_dir / "sample_sensor_data.csv"
    data_df.to_csv(data_path, index=False, encoding='utf-8')
    print(f"✅ Sample data CSV created: {data_path} ({len(sensor_data)} records)")

def main():
    """メイン実行"""
    print("🚀 Initializing Triathlon Sensor Database...")
    
    create_tables()
    create_initial_users()
    create_sensor_mappings()
    create_sample_sensor_data()
    create_sample_csv_files()
    
    print("\n🎉 Database initialization completed!")
    print("\n📋 Created accounts:")
    print("   Admin: username=admin, password=admin123")
    print("   User1: username=testuser1, password=password123")
    print("   User2: username=testuser2, password=password123")
    print("   User3: username=testuser3, password=password123")
    print("\n🚀 Start server with: uvicorn app.main:app --reload")
    print("📚 API Docs: http://localhost:8000/docs")

if __name__ == "__main__":
    main()