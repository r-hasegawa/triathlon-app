# app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import os

from .database import engine, Base
from .routers import auth, user_data, competition, feedback
from .routers.admin import router as admin_router  # 管理者ルーターを正しくインポート

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# データベーステーブル作成
Base.metadata.create_all(bind=engine)

# FastAPIアプリケーション
app = FastAPI(
    title="Triathlon Sensor Data Feedback System",
    description="トライアスロンセンサーデータフィードバックシステム API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # フロントエンド開発サーバー
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite開発サーバー
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 静的ファイル配信（アップロード済みファイル用）
uploads_dir = "uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# ルーター登録（正しい順序で）
app.include_router(auth.router, prefix="/auth", tags=["認証"])
app.include_router(admin_router, tags=["管理者"])  # 管理者ルーター（/adminプレフィックス含む）
app.include_router(user_data.router, tags=["ユーザーデータ"])  # /meプレフィックス含む
app.include_router(competition.router, prefix="/competitions", tags=["大会"])
app.include_router(feedback.router, tags=["フィードバック"])  # フィードバック機能

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

# ルートエンドポイント
@app.get("/")
async def root():
    """
    APIルート情報
    """
    return {
        "message": "Triathlon Sensor Data Feedback System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "available_endpoints": {
            "auth": "/auth/*",
            "admin": "/admin/*", 
            "user_data": "/me/*",
            "competitions": "/competitions/*",
            "feedback": "/me/competitions, /me/feedback-data/*"
        }
    }

# エラーハンドラー修正
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