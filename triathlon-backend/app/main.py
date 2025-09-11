"""
app/main.py (最終修正版)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base

# 🔧 存在するルーターのみインポート
from app.routers import auth, admin, competition, multi_sensor_upload, user_data

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Triathlon Real Data Format Management API",
    description="実データ形式対応トライアスロンデータ管理システム",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# エンドポイント規則:
# auth/ → 認証
# admin/ → 管理者専用
# me/ → 一般ユーザー本人のデータ  
# public/ → 公共の環境データ

app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(admin.router, tags=["admin"])  # admin.pyで既にprefix="/admin"設定済み
app.include_router(user_data.router, tags=["user-data"])  # /me/* endpoints
app.include_router(competition.router, tags=["competitions"])  # /public/* endpoints
app.include_router(multi_sensor_upload.router, prefix="/admin", tags=["multi-sensor"])

@app.get("/")
async def root():
    return {
        "message": "Triathlon Real Data Format Management API v3.0",
        "status": "running",
        "new_features": [
            "halshare CSV format support (halshareWearerName, halshareId, datetime, temperature)",
            "e-Celcius CSV format support (capsule_id, monitor_id, datetime, temperature, status)", 
            "Garmin TCX format support (sensor_id, time, heart_rate)",
            "Batch upload management with file-based deletion",
            "Upload history tracking and error reporting"
        ],
        "endpoints": {
            "auth": "/auth/*",
            "admin": "/admin/*", 
            "user_data": "/me/*",
            "public": "/public/*"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "version": "3.0.0",
        "database": "real_data_format_ready",
        "supported_formats": ["halshare", "e-Celcius", "TCX"]
    }