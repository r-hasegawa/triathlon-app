"""
app/main.py (新システムのみ版)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base

# 🆕 新しいルーターのみインポート
from app.routers import auth, admin, competition, multi_sensor_upload

# データベーステーブル作成
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Triathlon Sensor Data Management API",
    description="マルチセンサー対応トライアスロンデータ管理システム",
    version="2.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🆕 新しいルーターのみ追加
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(competition.router, prefix="/competitions", tags=["competitions"])
app.include_router(multi_sensor_upload.router, prefix="/api", tags=["multi-sensor"])

@app.get("/")
async def root():
    return {
        "message": "Triathlon Multi-Sensor Data Management API v2.0",
        "status": "running",
        "features": [
            "Multi-sensor data upload (skin temp, core temp, heart rate, WBGT)",
            "Flexible mapping system",
            "Competition management",
            "User management"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}