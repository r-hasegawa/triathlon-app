# app/main.py

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import os

from .database import engine, Base, SessionLocal
from .routers import auth, user_data, feedback
from .routers.admin import router as admin_router

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション
app = FastAPI(
    title="Triathlon Sensor Data Feedback System",
    description="トライアスロンセンサーデータフィードバックシステム API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS設定（環境変数対応）
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# 本番環境のフロントエンドURLを追加
if FRONTEND_URL not in allowed_origins:
    allowed_origins.append(FRONTEND_URL)
    logger.info(f"Added FRONTEND_URL to CORS: {FRONTEND_URL}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 静的ファイル配信
uploads_dir = "uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


# ===== 🆕 起動時の自動初期化 =====
@app.on_event("startup")
async def startup_event():
    """
    アプリ起動時の初期化処理
    - データベーステーブル作成（存在しない場合のみ）
    - 管理者アカウント作成（存在しない場合のみ）
    """
    
    logger.info("=" * 60)
    logger.info("Starting Triathlon Backend...")
    logger.info("=" * 60)
    
    # 1. テーブル作成（存在しない場合のみ）
    try:
        logger.info("Checking database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables ready")
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        raise
    
    # 2. 管理者アカウントの確認・作成
    db = SessionLocal()
    try:
        from .models.user import AdminUser
        from .utils.security import get_password_hash
        
        # 管理者が存在するかチェック
        existing_admin = db.query(AdminUser).filter_by(admin_id="admin").first()
        
        if not existing_admin:
            logger.info("Creating initial admin user...")
            admin_user = AdminUser(
                admin_id="admin",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                full_name="システム管理者",
                role="super_admin"
            )
            db.add(admin_user)
            db.commit()
            logger.info("✅ Admin user created (username: admin, password: admin123)")
        else:
            logger.info("✅ Admin user already exists")
            
    except Exception as e:
        logger.error(f"❌ Error during admin user initialization: {e}")
        db.rollback()
        # 管理者作成エラーは警告にとどめ、アプリは起動させる
        logger.warning("⚠️  Admin user creation failed, but app will continue")
    finally:
        db.close()
    
    logger.info("=" * 60)
    logger.info("🚀 Triathlon Backend started successfully!")
    logger.info(f"📊 Database: {os.getenv('DATABASE_URL', 'sqlite')[:50]}...")
    logger.info(f"🌐 CORS origins: {allowed_origins}")
    logger.info("=" * 60)


# ルーター登録
app.include_router(auth.router, prefix="/auth", tags=["認証"])
app.include_router(admin_router, tags=["管理者"])
app.include_router(user_data.router, tags=["ユーザーデータ"])
app.include_router(feedback.router, tags=["フィードバック"])


# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    """
    システムの状態確認
    """
    return {
        "status": "healthy",
        "service": "triathlon-feedback-system",
        "version": "1.0.0"
    }


# エラーハンドラー
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    HTTPエラーハンドラー
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """
    404エラーハンドラー
    """
    return JSONResponse(
        status_code=404,
        content={"detail": "リソースが見つかりません"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """
    500エラーハンドラー
    """
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "内部サーバーエラーが発生しました"}
    )


# グローバル例外ハンドラー
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全般的な例外ハンドラー
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "予期しないエラーが発生しました"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )