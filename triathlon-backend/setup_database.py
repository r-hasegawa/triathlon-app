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
    print("   - flexible_sensor_mappings (マッピング)")
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
    """大会記録作成（修正版）"""
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
                
                # 🔧 修正：プロパティへの代入を削除
                race_record = RaceRecord(
                    user_id=user_id,
                    competition_id=comp_id,
                    race_number=str(100 + i),  # bib_number → race_number
                    swim_start_time=swim_start,
                    swim_finish_time=swim_finish,
                    bike_start_time=bike_start,
                    bike_finish_time=bike_finish,
                    run_start_time=run_start,
                    run_finish_time=run_finish
                    # total_start_time, total_finish_time を削除（プロパティで自動計算）
                )
                
                # 🆕 サンプルLAPデータ設定
                sample_laps = {
                    "BL1": bike_start + timedelta(minutes=20),
                    "BL2": bike_start + timedelta(minutes=40),
                    "RL1": run_start + timedelta(minutes=15)
                }
                race_record.set_lap_data(sample_laps)
                
                # 🆕 サンプル区間データ設定
                sample_phases = {
                    "swim_phase": {
                        "start": swim_start,
                        "finish": swim_finish,
                        "duration_seconds": swim_duration.total_seconds()
                    },
                    "bike_phase": {
                        "start": bike_start,
                        "finish": bike_finish,
                        "duration_seconds": bike_duration.total_seconds()
                    },
                    "run_phase": {
                        "start": run_start,
                        "finish": run_finish,
                        "duration_seconds": run_duration.total_seconds()
                    }
                }
                race_record.set_calculated_phases(sample_phases)
                
                db.add(race_record)
                
        db.commit()
        print("✅ Race records created for all competitions")
        
    except Exception as e:
        print(f"❌ Error creating race records: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

def create_sample_real_format_data(competition_ids):
    """🆕 実際のデータ形式でサンプルデータ作成（修正版）"""
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
                    (skin_batch_id, SensorType.SKIN_TEMPERATURE, f"halshare_test{i}.csv"),
                    (core_batch_id, SensorType.CORE_TEMPERATURE, f"monitor{i}.csv"), 
                    (hr_batch_id, SensorType.HEART_RATE, f"garmin_test{i}.tcx")
                ]:
                    batch = UploadBatch(
                        batch_id=batch_id,
                        sensor_type=sensor_type,
                        file_name=file_name,
                        total_records=10,
                        success_records=10 if sensor_type != SensorType.CORE_TEMPERATURE else 7,  # core_temperatureは一部Missing
                        failed_records=0 if sensor_type != SensorType.CORE_TEMPERATURE else 3,
                        status=UploadStatus.SUCCESS if sensor_type != SensorType.CORE_TEMPERATURE else UploadStatus.PARTIAL,
                        competition_id=comp_id,
                        uploaded_by="admin"
                    )
                    db.add(batch)
                
                # 5. 🔧 修正：FlexibleSensorMappingの正しい構造で作成
                # 各センサータイプ別に個別のマッピング作成
                mappings = [
                    {
                        "sensor_id": f"11000002{i}B17",
                        "sensor_type": SensorType.SKIN_TEMPERATURE
                    },
                    {
                        "sensor_id": f"23.10.8E.8{i}",
                        "sensor_type": SensorType.CORE_TEMPERATURE
                    },
                    {
                        "sensor_id": f"GARMIN_00{i}",
                        "sensor_type": SensorType.HEART_RATE
                    }
                ]
                
                for mapping_data in mappings:
                    mapping = FlexibleSensorMapping(
                        user_id=f"user00{i}",
                        competition_id=comp_id,
                        sensor_id=mapping_data["sensor_id"],
                        sensor_type=mapping_data["sensor_type"],
                        is_active=True,
                        subject_name=f"テスト被験者{i}",
                        device_type="research"
                    )
                    db.add(mapping)
        
        db.commit()
        print("✅ Sample data created with real format compatibility")
        print("   - halshareWearerName, halshareId, datetime, temperature")
        print("   - capsule_id, monitor_id, datetime, temperature, status")
        print("   - sensor_id, time, heart_rate")
        print("   - FlexibleSensorMapping (各センサータイプ別)")
        
    except Exception as e:
        print(f"❌ Error creating sample real format data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

def create_sample_race_record_csvs(competition_ids):
    """🆕 大会記録CSVファイルのサンプル生成（実データ形式対応）"""
    print("📊 Creating sample race record CSV files...")
    
    # サンプルディレクトリ作成
    sample_dir = "sample_race_records"
    os.makedirs(sample_dir, exist_ok=True)
    
    try:
        for comp_idx, comp_id in enumerate(competition_ids):
            print(f"  Creating race records for competition: {comp_id}")
            
            # 大会ごとに複数のCSVファイルを生成（実データ形式対応）
            categories = [
                {
                    "name": "sprint", 
                    "participants": 10, 
                    "bike_laps": ["BL1"],  # スプリント：BL1のみ
                    "run_laps": ["RL1"]    # スプリント：RL1のみ
                },
                {
                    "name": "standard", 
                    "participants": 8, 
                    "bike_laps": ["BL1", "BL2"],  # スタンダード：BL1, BL2
                    "run_laps": ["RL1", "RL2"]    # スタンダード：RL1, RL2
                },
                {
                    "name": "long", 
                    "participants": 5, 
                    "bike_laps": ["BL1", "BL2", "BL3"],  # ロング：BL1〜BL3
                    "run_laps": ["RL1", "RL2", "RL3"]    # ロング：RL1〜RL3
                }
            ]
            
            base_time = datetime(2025, 6, 15, 8, 0, 0) + timedelta(days=comp_idx * 30)
            bib_counter = 100 + comp_idx * 50
            
            for category in categories:
                filename = f"{sample_dir}/race_records_{comp_id}_{category['name']}.csv"
                
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    # 🆕 実データ対応ヘッダー作成
                    headers = [
                        'No.',      # ゼッケン番号（統合キー）
                        '氏名',     # 実データと同じ日本語列名
                        '部門',
                        'カテゴリー',
                        '年齢',
                        '性別',
                        '登録地',
                        'START',    # 🆕 実データ形式（SWIM_STARTではなく）
                        'SF',       # 🆕 Swim Finish
                        'BS',       # 🆕 Bike Start
                    ]
                    
                    # 🆕 バイクLAP列追加（BL1, BL2...）
                    headers.extend(category['bike_laps'])
                    
                    # 🆕 ラン関連列追加
                    headers.append('RS')  # Run Start
                    headers.extend(category['run_laps'])  # RL1, RL2...
                    headers.append('RF')  # Run Finish
                    
                    # 🆕 実データにある追加列
                    headers.extend(['総合記録', 'ステータス', '備考'])
                    
                    writer = csv.writer(csvfile)
                    writer.writerow(headers)
                    
                    # 参加者データ生成
                    for i in range(category['participants']):
                        bib_number = str(bib_counter)
                        bib_counter += 1
                        
                        # 現実的なレース時間生成
                        swim_start = base_time + timedelta(minutes=random.randint(0, 10))
                        swim_duration = timedelta(minutes=random.randint(20, 45))
                        swim_finish = swim_start + swim_duration
                        
                        # トランジション1（2-5分）
                        t1_duration = timedelta(minutes=random.randint(2, 5))
                        bike_start = swim_finish + t1_duration
                        bike_duration = timedelta(minutes=random.randint(50, 120))
                        
                        # バイクLAP時刻生成
                        bike_lap_times = []
                        current_bike_time = bike_start
                        bike_lap_interval = bike_duration / len(category['bike_laps'])
                        
                        for lap_idx in range(len(category['bike_laps'])):
                            current_bike_time += bike_lap_interval + timedelta(minutes=random.randint(-5, 5))
                            bike_lap_times.append(current_bike_time.strftime('%Y-%m-%d %H:%M:%S'))
                        
                        bike_finish = current_bike_time  # 最後のバイクLAP時刻
                        
                        # トランジション2（2-5分）
                        t2_duration = timedelta(minutes=random.randint(2, 5))
                        run_start = bike_finish + t2_duration
                        run_duration = timedelta(minutes=random.randint(30, 70))
                        
                        # ランLAP時刻生成
                        run_lap_times = []
                        current_run_time = run_start
                        run_lap_interval = run_duration / len(category['run_laps'])
                        
                        for lap_idx in range(len(category['run_laps'])):
                            current_run_time += run_lap_interval + timedelta(minutes=random.randint(-3, 3))
                            run_lap_times.append(current_run_time.strftime('%Y-%m-%d %H:%M:%S'))
                        
                        run_finish = current_run_time  # 最後のランLAP時刻
                        
                        # 総合記録計算
                        total_time = run_finish - swim_start
                        total_record = str(total_time).split('.')[0]  # 秒以下切り捨て
                        
                        # 行データ作成（実データ形式）
                        row = [
                            bib_number,
                            f"選手_{bib_number}",
                            f"部門{random.choice(['A', 'B', 'C'])}",
                            category['name'].upper(),
                            random.randint(20, 60),
                            random.choice(['男性', '女性']),
                            random.choice(['東京都', '神奈川県', '千葉県', '埼玉県']),
                            swim_start.strftime('%Y-%m-%d %H:%M:%S'),    # START
                            swim_finish.strftime('%Y-%m-%d %H:%M:%S'),   # SF
                            bike_start.strftime('%Y-%m-%d %H:%M:%S'),    # BS
                        ]
                        
                        # バイクLAP時刻追加
                        row.extend(bike_lap_times)
                        
                        # ラン関連時刻追加
                        row.append(run_start.strftime('%Y-%m-%d %H:%M:%S'))  # RS
                        row.extend(run_lap_times)  # RL1, RL2...
                        row.append(run_finish.strftime('%Y-%m-%d %H:%M:%S'))  # RF
                        
                        # 追加情報
                        row.extend([
                            total_record,  # 総合記録
                            '完走',        # ステータス
                            ''             # 備考
                        ])
                        
                        writer.writerow(row)
                
                print(f"    ✅ Created: {filename} ({category['participants']} records, "
                      f"Bike LAPs: {len(category['bike_laps'])}, Run LAPs: {len(category['run_laps'])})")
        
        print(f"📊 Sample race record CSV files created in '{sample_dir}' directory")
        print("🔍 Files can be used to test the race record upload functionality")
        
        # 使用方法の説明
        print("\n" + "="*60)
        print("📋 How to test race record upload:")
        print("1. Start the backend server")
        print("2. Login as admin")
        print("3. Go to sensor upload page")
        print("4. Select a competition")
        print(f"5. Upload multiple CSV files from '{sample_dir}' directory")
        print("6. Check the integration results")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error creating sample race record CSV files: {e}")
        import traceback
        traceback.print_exc()

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
    
    if competition_ids:
        # ステップ4: 大会記録作成
        print("🏃 Creating race records...")
        create_race_records(competition_ids)
        print()
        
        # ステップ5: 実データ形式でサンプルデータ作成
        print("📊 Creating sample data with real formats...")
        create_sample_real_format_data(competition_ids)
        print()
        
        # ステップ6: 🆕 大会記録CSVファイル生成
        print("📋 Creating sample race record CSV files...")
        create_sample_race_record_csvs(competition_ids)
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