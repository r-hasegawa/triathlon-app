"""
setup_database.py (新システム版)
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.database import engine, Base, SessionLocal
from app.models.user import User, AdminUser
from app.models.competition import Competition, RaceRecord  
from app.models.flexible_sensor_data import (
    RawSensorData, FlexibleSensorMapping,
    SkinTemperatureData, CoreTemperatureData, 
    HeartRateData, WBGTData
)
from app.utils.security import get_password_hash

def create_tables():
    """全テーブル作成"""
    print("🗄️  Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")

# 他の関数も新システムに対応...

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
    """🆕 サンプル大会データ作成"""
    db = SessionLocal()
    
    try:
        # サンプル大会データ
        competitions = [
            {
                "name": "第1回東京湾トライアスロン2025",
                "date": date(2025, 6, 15),
                "location": "東京都江東区お台場海浜公園",
                "description": "初夏の東京湾で開催される研究用トライアスロン大会"
            },
            {
                "name": "真夏の湘南オープンウォータートライアスロン",
                "date": date(2025, 8, 10),
                "location": "神奈川県藤沢市湘南海岸",
                "description": "高温環境下での生理学的応答を調査する真夏の大会"
            },
            {
                "name": "秋季長距離トライアスロン研究大会",
                "date": date(2025, 10, 5),
                "location": "静岡県熱海市",
                "description": "涼しい季節での長距離耐久性能テスト大会"
            }
        ]
        
        created_competitions = []
        for comp_data in competitions:
            existing = db.query(Competition).filter_by(name=comp_data["name"]).first()
            if not existing:
                competition = Competition(**comp_data)
                db.add(competition)
                created_competitions.append(competition)
                print(f"✅ Competition created: {comp_data['name']} (ID: {competition.competition_id})")
        
        db.commit()
        
        # 作成された大会のIDを返す
        return [comp.competition_id for comp in created_competitions]
        
    except Exception as e:
        print(f"❌ Error creating competitions: {e}")
        db.rollback()
        return []
    finally:
        db.close()

def create_race_records(competition_ids):
    """🆕 大会記録サンプルデータ作成"""
    db = SessionLocal()
    
    try:
        # 各大会について、数名分の記録を作成
        for comp_id in competition_ids:
            competition = db.query(Competition).filter_by(competition_id=comp_id).first()
            if not competition:
                continue
                
            # 大会開始時刻を設定 (大会日の朝8時)
            race_start_base = datetime.combine(competition.date, datetime.min.time()) + timedelta(hours=8)
            
            # テストユーザーの一部に記録を作成
            users = db.query(User).limit(3).all()
            
            for i, user in enumerate(users):
                # 各選手のスタート時刻をずらす (5分間隔)
                user_start = race_start_base + timedelta(minutes=i * 5)
                
                # 各種目の所要時間をランダム生成 (分)
                swim_duration = random.randint(25, 45)  # 25-45分
                bike_duration = random.randint(90, 150)  # 1.5-2.5時間
                run_duration = random.randint(45, 80)   # 45-80分
                
                # 各種目の開始・終了時刻計算
                swim_start = user_start
                swim_finish = swim_start + timedelta(minutes=swim_duration)
                
                bike_start = swim_finish + timedelta(minutes=random.randint(2, 8))  # トランジション
                bike_finish = bike_start + timedelta(minutes=bike_duration)
                
                run_start = bike_finish + timedelta(minutes=random.randint(2, 6))   # トランジション
                run_finish = run_start + timedelta(minutes=run_duration)
                
                # レース記録作成
                race_record = RaceRecord(
                    competition_id=comp_id,
                    user_id=user.user_id,
                    race_number=f"{i+1:03d}",  # ゼッケン番号
                    swim_start_time=swim_start,
                    swim_finish_time=swim_finish,
                    bike_start_time=bike_start,
                    bike_finish_time=bike_finish,
                    run_start_time=run_start,
                    run_finish_time=run_finish
                )
                
                # 総合記録を計算
                race_record.calculate_total_times()
                
                db.add(race_record)
                print(f"✅ Race record created: {user.full_name} in {competition.name}")
        
        db.commit()
        
    except Exception as e:
        print(f"❌ Error creating race records: {e}")
        db.rollback()
    finally:
        db.close()

def create_sensor_mappings_with_competitions(competition_ids):
    """🆕 大会対応センサマッピング作成"""
    db = SessionLocal()
    
    try:
        users = db.query(User).limit(3).all()
        
        for comp_id in competition_ids:
            # 各大会でセンサーを使い回し
            sensor_mappings = [
                ("SENSOR_001", users[0].user_id, users[0].full_name),
                ("SENSOR_002", users[1].user_id, users[1].full_name),
                ("SENSOR_003", users[2].user_id, users[2].full_name),
            ]
            
            for sensor_id, user_id, subject_name in sensor_mappings:
                # 同じ大会内での重複チェック
                existing = db.query(SensorMapping).filter_by(
                    sensor_id=sensor_id, 
                    competition_id=comp_id
                ).first()
                
                if not existing:
                    mapping = SensorMapping(
                        sensor_id=sensor_id,
                        user_id=user_id,
                        competition_id=comp_id,
                        subject_name=subject_name,
                        device_type="halshare_temperature"
                    )
                    db.add(mapping)
                    print(f"✅ Sensor mapping created: {sensor_id} -> {subject_name} (Competition: {comp_id})")
        
        db.commit()
        
    except Exception as e:
        print(f"❌ Error creating sensor mappings: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_sensor_data_with_competitions(competition_ids):
    """🆕 大会対応センサデータ作成"""
    db = SessionLocal()
    
    try:
        for comp_id in competition_ids:
            # 大会の記録データを取得して、その時間範囲でセンサデータを生成
            race_records = db.query(RaceRecord).filter_by(competition_id=comp_id).all()
            
            for record in race_records:
                if not (record.total_start_time and record.total_finish_time):
                    continue
                
                # センサデータ生成期間（レース開始1時間前から終了1時間後まで）
                data_start = record.total_start_time - timedelta(hours=1)
                data_end = record.total_finish_time + timedelta(hours=1)
                
                # 5分間隔でデータポイント生成
                current_time = data_start
                sensor_id = f"SENSOR_{record.user_id[-3:]}"  # user001 -> SENSOR_001
                
                base_temp = 36.0 + random.uniform(-0.5, 0.5)  # 基準体温
                
                while current_time <= data_end:
                    # 時間帯による体温変動をシミュレート
                    time_factor = 0
                    
                    # レース中は体温上昇
                    if record.total_start_time <= current_time <= record.total_finish_time:
                        progress = (current_time - record.total_start_time).total_seconds() / \
                                 (record.total_finish_time - record.total_start_time).total_seconds()
                        time_factor = progress * 2.0  # 最大2度上昇
                    
                    # ランダムノイズ
                    noise = random.uniform(-0.2, 0.2)
                    temperature = base_temp + time_factor + noise
                    
                    sensor_data = SensorData(
                        sensor_id=sensor_id,
                        user_id=record.user_id,
                        competition_id=comp_id,
                        timestamp=current_time,
                        temperature=round(temperature, 1),
                        data_source="sample_data"
                    )
                    
                    db.add(sensor_data)
                    current_time += timedelta(minutes=5)
                
                print(f"✅ Sensor data created for {record.user_id} in competition {comp_id}")
        
        db.commit()
        
    except Exception as e:
        print(f"❌ Error creating sensor data: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_wbgt_data(competition_ids):
    """🆕 WBGT環境データ作成"""
    db = SessionLocal()
    
    try:
        for comp_id in competition_ids:
            competition = db.query(Competition).filter_by(competition_id=comp_id).first()
            if not competition:
                continue
            
            # 大会当日の8時間分のWBGTデータ (6:00-14:00)
            start_time = datetime.combine(competition.date, datetime.min.time()) + timedelta(hours=6)
            end_time = start_time + timedelta(hours=8)
            
            current_time = start_time
            base_wbgt = random.uniform(20, 28)  # 季節に応じたベースWBGT値
            
            while current_time <= end_time:
                # 時間による変動シミュレート（朝は低く、昼に向けて上昇）
                hour = current_time.hour
                if hour < 10:
                    time_factor = -2.0  # 朝は低め
                elif hour < 12:
                    time_factor = 0.0   # 午前中
                else:
                    time_factor = 2.0   # 昼以降は高め
                
                # ランダムノイズ
                noise = random.uniform(-1.0, 1.0)
                wbgt_value = base_wbgt + time_factor + noise
                
                # 気象データもシミュレート
                temperature = wbgt_value + random.uniform(5, 15)  # 気温はWBGTより高め
                humidity = random.uniform(40, 80)  # 湿度40-80%
                wind_speed = random.uniform(0.5, 3.0)  # 風速0.5-3.0m/s
                
                wbgt_data = WBGTData(
                    competition_id=comp_id,
                    timestamp=current_time,
                    wbgt_value=round(wbgt_value, 1),
                    temperature=round(temperature, 1),
                    humidity=round(humidity, 1),
                    wind_speed=round(wind_speed, 1),
                    location="スタート地点"
                )
                
                db.add(wbgt_data)
                current_time += timedelta(minutes=30)  # 30分間隔
            
            print(f"✅ WBGT data created for competition {comp_id}")
        
        db.commit()
        
    except Exception as e:
        print(f"❌ Error creating WBGT data: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_multi_sensor_data(competition_ids):
    """🆕 マルチセンサーデータ作成（カプセル体温・心拍）"""
    db = SessionLocal()
    
    try:
        for comp_id in competition_ids:
            race_records = db.query(RaceRecord).filter_by(competition_id=comp_id).all()
            
            for record in race_records:
                if not (record.total_start_time and record.total_finish_time):
                    continue
                
                # データ生成期間
                data_start = record.total_start_time - timedelta(minutes=30)
                data_end = record.total_finish_time + timedelta(minutes=30)
                
                current_time = data_start
                
                # カプセル体温データ生成
                monitor_id = f"MONITOR_{record.user_id[-3:]}"
                capsule_id = f"CAPSULE_{record.user_id[-3:]}_01"
                base_core_temp = 37.0 + random.uniform(-0.3, 0.3)
                
                # 心拍データ生成
                device_id = f"GARMIN_{record.user_id[-3:]}"
                base_hr = random.randint(60, 80)  # 安静時心拍
                
                while current_time <= data_end:
                    # === カプセル体温データ ===
                    # レース中の体温上昇
                    core_temp_factor = 0
                    if record.total_start_time <= current_time <= record.total_finish_time:
                        progress = (current_time - record.total_start_time).total_seconds() / \
                                 (record.total_finish_time - record.total_start_time).total_seconds()
                        core_temp_factor = progress * 1.5  # 最大1.5度上昇
                    
                    core_temperature = base_core_temp + core_temp_factor + random.uniform(-0.1, 0.1)
                    
                    capsule_data = CapsuleTemperatureData(
                        monitor_id=monitor_id,
                        capsule_id=capsule_id,
                        user_id=record.user_id,
                        competition_id=comp_id,
                        timestamp=current_time,
                        core_temperature=round(core_temperature, 1),
                        battery_level=random.uniform(70, 100),
                        signal_strength=random.uniform(80, 100)
                    )
                    db.add(capsule_data)
                    
                    # === 心拍データ ===
                    # 運動強度による心拍変動
                    hr_factor = 0
                    if record.total_start_time <= current_time <= record.total_finish_time:
                        # 競技種目による心拍変動
                        if record.swim_start_time and record.swim_finish_time and \
                           record.swim_start_time <= current_time <= record.swim_finish_time:
                            hr_factor = random.randint(40, 60)  # Swim: 高強度
                        elif record.bike_start_time and record.bike_finish_time and \
                             record.bike_start_time <= current_time <= record.bike_finish_time:
                            hr_factor = random.randint(50, 80)  # Bike: 中-高強度
                        elif record.run_start_time and record.run_finish_time and \
                             record.run_start_time <= current_time <= record.run_finish_time:
                            hr_factor = random.randint(60, 90)  # Run: 高強度
                    
                    heart_rate = min(220 - 30, base_hr + hr_factor + random.randint(-5, 5))  # 年齢30歳想定の最大心拍制限
                    
                    # 心拍ゾーン計算 (簡易版)
                    hr_zone = 1
                    if heart_rate > base_hr + 20:
                        hr_zone = 2
                    if heart_rate > base_hr + 40:
                        hr_zone = 3
                    if heart_rate > base_hr + 60:
                        hr_zone = 4
                    if heart_rate > base_hr + 80:
                        hr_zone = 5
                    
                    hr_data = HeartRateData(
                        device_id=device_id,
                        user_id=record.user_id,
                        competition_id=comp_id,
                        timestamp=current_time,
                        heart_rate=heart_rate,
                        heart_rate_zone=hr_zone,
                        rrinterval=random.uniform(400, 1000),  # RR間隔 (ms)
                        activity_type="triathlon"
                    )
                    db.add(hr_data)
                    
                    current_time += timedelta(minutes=1)  # 1分間隔
                
                print(f"✅ Multi-sensor data created for {record.user_id} in competition {comp_id}")
        
        db.commit()
        
    except Exception as e:
        print(f"❌ Error creating multi-sensor data: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """メイン実行関数"""
    print("🚀 Initializing Triathlon Sensor Database with Competition Management...")
    print("=" * 70)
    
    # ステップ1: テーブル作成
    create_tables()
    print()
    
    # ステップ2: 初期ユーザー作成
    print("👥 Creating initial users...")
    create_initial_users()
    print()
    
    # ステップ3: 🆕 大会データ作成
    print("🏆 Creating sample competitions...")
    competition_ids = create_sample_competitions()
    print()
    
    if competition_ids:
        # ステップ4: 🆕 大会記録作成
        print("🏃 Creating race records...")
        create_race_records(competition_ids)
        print()
        
        # ステップ5: 🆕 大会対応センサマッピング作成
        print("🔗 Creating sensor mappings for competitions...")
        create_sensor_mappings_with_competitions(competition_ids)
        print()
        
        # ステップ6: 🆕 大会対応センサデータ作成
        print("📊 Creating sensor data for competitions...")
        create_sample_sensor_data_with_competitions(competition_ids)
        print()
        
        # ステップ7: 🆕 WBGT環境データ作成
        print("🌡️  Creating WBGT environmental data...")
        create_sample_wbgt_data(competition_ids)
        print()
        
        # ステップ8: 🆕 マルチセンサーデータ作成
        print("💓 Creating multi-sensor data (capsule temp + heart rate)...")
        create_sample_multi_sensor_data(competition_ids)
        print()
    
    print("=" * 70)
    print("🎉 Database initialization completed with competition management!")
    print()
    print("📋 Summary:")
    print(f"   • Competitions created: {len(competition_ids)}")
    print("   • Users: 5 test users + 1 admin")
    print("   • Sample data: Temperature, Heart Rate, Capsule Temperature, WBGT")
    print("   • Race records: Swim/Bike/Run times for each competition")
    print()
    print("🔑 Login Information:")
    print("   Admin:     username=admin,     password=admin123")
    print("   Test User: username=testuser1, password=password123")
    print()
    print("🌐 Access URLs:")
    print("   Backend API: http://localhost:8000")
    print("   API Docs:    http://localhost:8000/docs")
    print("   Frontend:    http://localhost:3000")

if __name__ == "__main__":
    main()