from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from datetime import datetime
import os
from pathlib import Path
import uvicorn

# ルーター import 🆕 competition 追加
from app.routers import auth, admin, data, competition, multi_sensor_upload

# アップロードディレクトリ作成
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads/csv"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# FastAPI アプリケーション初期化
app = FastAPI(
    title="Triathlon Sensor Data Feedback System",
    description="トライアスロン研究センサデータフィードバックシステム API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS設定
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 静的ファイル設定（将来のフロントエンド用）
if Path("static").exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

# ルーター登録 🆕 競技管理ルーター追加
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(data.router, prefix="/data", tags=["Data"])
app.include_router(competition.router, prefix="/api", tags=["Competition"])
app.include_router(multi_sensor_upload.router, prefix="/api", tags=["MultiSensor"])

# ルートエンドポイント
@app.get("/")
async def root():
    """API ルート"""
    return {
        "message": "Triathlon Sensor Data Feedback System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    try:
        # データベース接続テスト
        from app.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "database": "connected",
            "upload_dir": str(UPLOAD_DIR),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

# 例外ハンドラー
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )

@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)