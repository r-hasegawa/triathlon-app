"""
scripts/recreate_database.py
データベースを再作成するスクリプト（開発用）

⚠️ 警告: このスクリプトは全てのデータを削除します！
本番環境では絶対に実行しないでください！
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine, Base, get_database_info, print_database_info
from app.utils.security import get_password_hash
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# 全モデルをインポート
from app.models.user import User, AdminUser
from app.models.competition import Competition, RaceRecord
from app.models.flexible_sensor_data import (
    FlexibleSensorMapping,
    SkinTemperatureData, 
    CoreTemperatureData,
    HeartRateData, 
    WBGTData,
    UploadBatch
)
from app.models.competition_feedback import CompetitionFeedback

def confirm_action():
    """実行前の確認"""
    print("\n" + "="*60)
    print("⚠️  警告: データベースを再作成します")
    print("="*60)
    
    db_info = get_database_info()
    print(f"\n対象データベース: {db_info['database_type']}")
    print(f"URL: {db_info['database_url']}")
    
    print("\n⚠️  全てのテーブルとデータが削除されます！")
    response = input("\n続行しますか? (yes/no): ")
    
    return response.lower() == "yes"


def drop_all_tables():
    """全テーブルを削除"""
    print("\n🗑️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped")


def create_all_tables():
    """全テーブルを作成"""
    print("\n🏗️  Creating all tables...")
    Base.metadata.create_all(bind=engine)
    
    # 作成されたテーブル一覧を表示
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print("✅ Tables created:")
    for table in tables:
        print(f"   - {table}")


def create_initial_data():
    """初期データを作成"""
    print("\n📝 Creating initial data...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 管理者アカウント作成
        admin = AdminUser(
            admin_id="admin",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            role="super_admin",
            created_at=datetime.utcnow()
        )
        db.add(admin)
        print("✅ Admin user created (admin / admin123)")
        
        # テストユーザー作成
        test_user = User(
            user_id="testuser1",
            username="testuser1",
            email="testuser1@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Test User 1",
            created_at=datetime.utcnow()
        )
        db.add(test_user)
        print("✅ Test user created (testuser1 / password123)")
        
        # テスト大会作成
        test_competition = Competition(
            competition_id="COMP_TEST_001",
            name="テスト大会2025",
            date=datetime(2025, 7, 27).date(),
            location="テスト会場"
        )
        db.add(test_competition)
        print("✅ Test competition created")
        
        db.commit()
        print("\n✅ Initial data created successfully")
        
    except Exception as e:
        print(f"\n❌ Error creating initial data: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """メイン処理"""
    print("\n" + "="*60)
    print("📊 Database Migration Tool")
    print("="*60)
    
    # データベース情報を表示
    print_database_info()
    
    # 実行確認
    if not confirm_action():
        print("\n❌ 操作をキャンセルしました")
        return
    
    try:
        # テーブル削除
        drop_all_tables()
        
        # テーブル作成
        create_all_tables()
        
        # 初期データ作成
        create_initial_data()
        
        print("\n" + "="*60)
        print("🎉 Database recreation completed successfully!")
        print("="*60)
        print("\nログイン情報:")
        print("  管理者: admin / admin123")
        print("  ユーザー: testuser1 / password123")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()