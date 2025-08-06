from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# データベースディレクトリ作成
DB_DIR = Path("data")
DB_DIR.mkdir(exist_ok=True)

# SQLite データベース設定
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/triathlon.db")

# SQLAlchemy エンジン作成
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=True  # 開発時はSQLログを表示
)

# セッションファクトリ
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ベースクラス
Base = declarative_base()

# データベースセッション依存性注入
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()