"""
app/main.py (エンドポイント規則統一版)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base

from app.routers import auth, admin, user_data, competition, multi_sensor_upload

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Triathlon Sensor Data Management API",
    description="マルチセンサー対応トライアスロンデータ管理システム",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# エンドポイント規則:
# auth/ → 認証
# admin/ → 管理者専用
# me/ → 一般ユーザー本人のデータ  
# public/ → 公共の環境データ

# エンドポイント規則に従ったルーター設定:
# auth/ → 認証 (auth.pyにprefixなし)
# admin/ → 管理者専用 (admin.pyで/adminが設定済み)
# me/ → 一般ユーザー本人のデータ  
# public/ → 公共の環境データ (competition.pyで設定)

app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(admin.router, tags=["admin"])  # admin.pyで既にprefix="/admin"設定済み - 重複削除！
app.include_router(user_data.router)
app.include_router(competition.router, tags=["competitions"])
app.include_router(multi_sensor_upload.router, prefix="/admin", tags=["multi-sensor"])

@app.get("/")
async def root():
    return {
        "message": "Triathlon Multi-Sensor Data Management API v2.0",
        "status": "running",
        "endpoints": {
            "auth": "/auth/*",
            "admin": "/admin/*", 
            "user_data": "/me/*",
            "public": "/public/*"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}