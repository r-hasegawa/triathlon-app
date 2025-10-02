# app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import os

from .database import engine, Base
from .routers import auth, user_data, feedback
from .routers.admin import router as admin_router

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

# 🆕 CORS設定（環境変数対応）
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

# ルーター登録
app.include_router(auth.router, prefix="/auth", tags=["認証"])
app.include_router(admin_router, tags=["管理者"])
app.include_router(user_data.router, tags=["ユーザーデータ"])
app.include_router(feedback.router, tags=["フィードバック"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "triathlon-feedback-system",
        "version": "1.0.0"
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