"""
setup_database.py (テーブル重複回避版)
"""

import sys
from pathlib import Path
from datetime import date, datetime, timedelta
import random

sys.path.append(str(Path(__file__).parent))

from app.database import engine, Base, SessionLocal
from app.models.user import User, AdminUser
from app.models.competition import Competition, RaceRecord  
from app.models.flexible_sensor_data import (
    # 既存のモデルのみ使用（新しいテーブルも含まれている）
    RawSensorData, FlexibleSensorMapping,
    SkinTemperatureData, CoreTemperatureData, 
    HeartRateData, WBGTData, UploadBatch
)
from app.utils.security import get_password_hash

def create_tables():
    """全テーブル作成（修正版のモデル含む）"""
    print("🗄️  Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")
    print("📊 Sensor data tables included:")
    print("   - skin_temperature_data (halshare対応)")
    print("   - core_temperature_data (e-Celcius対応)")
    print("   - heart_rate_data (TCX対応)")
    print("   - upload_batches (バッチ管理)")
    print("   - sensor_mappings (マッピング)")

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
                "date": date(2025, 6, 15),
                "location": "東京都江東区お台場海浜公園",
                "description": "初夏の東京湾で開催される研究用トライアスロン大会"
            },
            {
                "competition_id": "comp_2025_002", 
                "name": "真夏の湘南オープンウォータートライアスロン",
                "date": date(2025, 8, 10),
                "location": "神奈川県藤沢市湘南海岸",
                "description": "高温環境下での生理学的応答を調査する真夏の大会"
            },
            {
                "competition_id": "comp_2025_003",
                "name": "秋季アイアンマン研究大会",
                "date": date(2025, 10, 5),
                "location": "千葉県館山市",
                "description": "長距離耐久競技における生体反応の詳細解析"
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

def create_race_records(competition_ids):
    """大会記録作成"""
    db = SessionLocal()
    
    try:
        for comp_id in competition_ids:
            # 各大会に5人の参加者
            for i in range(1, 6):
                user_id = f"user00{i}"
                
                # レース時間を生成（現実的な時間）
                start_time = datetime(2025, 6, 15, 8, 0, 0)  # 8:00スタート
                swim_duration = timedelta(minutes=random.randint(25, 40))
                bike_duration = timedelta(minutes=random.randint(60, 90))
                run_duration = timedelta(minutes=random.randint(35, 55))
                
                swim_start = start_time
                swim_finish = swim_start + swim_duration
                bike_start = swim_finish + timedelta(minutes=random.randint(2, 5))  # トランジション
                bike_finish = bike_start + bike_duration
                run_start = bike_finish + timedelta(minutes=random.randint(2, 5))  # トランジション
                run_finish = run_start + run_duration
                
                race_record = RaceRecord(
                    user_id=user_id,
                    competition_id=comp_id,
                    bib_number=str(100 + i),
                    swim_start_time=swim_start,
                    swim_finish_time=swim_finish,
                    bike_start_time=bike_start,
                    bike_finish_time=bike_finish,
                    run_start_time=run_start,
                    run_finish_time=run_finish,
                    total_start_time=swim_start,
                    total_finish_time=run_finish
                )
                db.add(race_record)
                
        db.commit()
        print("✅ Race records created for all competitions")
        
    except Exception as e:
        print(f"❌ Error creating race records: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_real_format_data(competition_ids):
    """🆕 実際のデータ形式でサンプルデータ作成"""
    db = SessionLocal()
    
    try:
        for comp_id in competition_ids:
            # 各大会用にサンプルデータ作成
            for i in range(1, 4):  # 3人分のデータ
                batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # 1. 体表温データ（halshare形式）
                skin_batch_id = f"{batch_timestamp}_2025_大阪大学_test{i}_halshare.csv"
                for j in range(10):  # 10データポイント
                    skin_data = SkinTemperatureData(
                        halshare_wearer_name=f"test{i}",
                        halshare_id=f"11000002{i}B17",
                        datetime=datetime.now() + timedelta(minutes=j),
                        temperature=33.0 + random.uniform(-1, 2),
                        upload_batch_id=skin_batch_id,
                        competition_id=comp_id
                    )
                    db.add(skin_data)
                
                # 2. カプセル温データ（e-Celcius形式）
                core_batch_id = f"{batch_timestamp}_monitor{i}.csv"
                for j in range(10):
                    core_data = CoreTemperatureData(
                        capsule_id=f"23.10.8E.8{i}",
                        monitor_id=f"monitor{i}",
                        datetime=datetime.now() + timedelta(minutes=j),
                        temperature=37.0 + random.uniform(-0.5, 1.5) if j % 4 != 0 else None,  # Missing dataをシミュレート
                        status="Synchronized" if j % 4 != 0 else "Missing data",
                        upload_batch_id=core_batch_id,
                        competition_id=comp_id
                    )
                    db.add(core_data)
                
                # 3. 心拍データ（TCX形式）
                hr_batch_id = f"{batch_timestamp}_東京トライアスロン_{i}.tcx"
                for j in range(10):
                    hr_data = HeartRateData(
                        sensor_id=f"GARMIN_00{i}",
                        time=datetime.now() + timedelta(minutes=j),
                        heart_rate=70 + random.randint(0, 50),
                        upload_batch_id=hr_batch_id,
                        competition_id=comp_id
                    )
                    db.add(hr_data)
                
                # 4. アップロードバッチ記録
                for batch_id, sensor_type, file_name in [
                    (skin_batch_id, "skin_temperature", f"halshare_test{i}.csv"),
                    (core_batch_id, "core_temperature", f"monitor{i}.csv"), 
                    (hr_batch_id, "heart_rate", f"garmin_test{i}.tcx")
                ]:
                    batch = UploadBatch(
                        batch_id=batch_id,
                        sensor_type=sensor_type,
                        file_name=file_name,
                        total_records=10,
                        success_records=10 if sensor_type != "core_temperature" else 7,  # core_temperatureは一部Missing
                        failed_records=0 if sensor_type != "core_temperature" else 3,
                        status="success" if sensor_type != "core_temperature" else "partial",
                        competition_id=comp_id,
                        uploaded_by="admin"
                    )
                    db.add(batch)
                
                # 5. サンプルマッピング
                mapping = SensorMapping(
                    user_id=f"user00{i}",
                    competition_id=comp_id,
                    skin_temp_sensor_id=f"11000002{i}B17",
                    core_temp_sensor_id=f"23.10.8E.8{i}",
                    heart_rate_sensor_id=f"GARMIN_00{i}",
                    race_record_id=str(100 + i),
                    upload_batch_id=f"{batch_timestamp}_mapping.csv"
                )
                db.add(mapping)
        
        db.commit()
        print("✅ Sample data created with real format compatibility")
        print("   - halshareWearerName, halshareId, datetime, temperature")
        print("   - capsule_id, monitor_id, datetime, temperature, status")
        print("   - sensor_id, time, heart_rate")
        
    except Exception as e:
        print(f"❌ Error creating sample real format data: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """メイン実行関数"""
    print("🚀 Initializing Triathlon Database with Real Data Format Support...")
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
    
    if competition_ids:
        # ステップ4: 大会記録作成
        print("🏃 Creating race records...")
        create_race_records(competition_ids)
        print()
        
        # ステップ5: 🆕 実データ形式でサンプルデータ作成
        print("📊 Creating sample data with real formats...")
        create_sample_real_format_data(competition_ids)
        print()
    
    print("=" * 80)
    print("🎉 Database initialization completed with real data format support!")
    print()
    print("📋 Summary:")
    print(f"   • Competitions created: {len(competition_ids)}")
    print("   • Users: 5 test users + 1 admin")
    print("   • Real Format Models: halshare, e-Celcius, TCX support")
    print("   • Batch Management: Upload history and deletion ready")
    print("   • Sample data: Ready for testing with actual file formats")
    print()
    print("🔑 Login Information:")
    print("   Admin:     username=admin,     password=admin123")
    print("   Test User: username=testuser1, password=password123")
    print()
    print("🌐 Access URLs:")
    print("   Backend API: http://localhost:8000")
    print("   API Docs:    http://localhost:8000/docs")
    print("   Frontend:    http://localhost:3000")
    print()
    print("🆕 New Features Ready:")
    print("   • Real data format support:")
    print("     - halshare: halshareWearerName, halshareId, datetime, temperature")
    print("     - e-Celcius: capsule_id, monitor_id, datetime, temperature, status")  
    print("     - TCX: sensor_id, time, heart_rate")
    print("   • Batch upload management with file-based deletion")
    print("   • Upload history tracking")
    print("   • Error handling and reporting")
    print()
    print("🚀 Next Steps:")
    print("   1. Add upload endpoints: app/routers/admin/upload.py")
    print("   2. Add frontend upload page: SensorDataUpload.tsx")
    print("   3. Test with actual data files")

if __name__ == "__main__":
    main()