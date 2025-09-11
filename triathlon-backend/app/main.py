"""
app/main.py (修正版)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base

# ルーターインポート
from app.routers import auth, user_data, competition
from app.routers.admin import router as admin_router

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
app.include_router(admin_router, tags=["admin"])  # /admin/* endpoints
app.include_router(user_data.router, tags=["user-data"])  # /me/* endpoints
app.include_router(competition.router, tags=["competitions"])  # /public/* endpoints

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