"""
app/main.py (admin フォルダ分割対応版)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base

# ルーターインポート（admin は新しいフォルダ構造から）
from app.routers import auth, user_data, competition
from app.routers.admin import router as admin_router  # 新しいadminフォルダから

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Triathlon Real Data Format Management API",
    description="実データ形式対応トライアスロンデータ管理システム（admin機能分割版）",
    version="3.1.0"
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
# admin/ → 管理者専用（機能別に分割）
# me/ → 一般ユーザー本人のデータ  
# public/ → 公共の環境データ

app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(admin_router, tags=["admin"])  # 統合されたadminルーター
app.include_router(user_data.router, tags=["user-data"])  # /me/* endpoints
app.include_router(competition.router, tags=["competitions"])  # /public/* endpoints

@app.get("/")
async def root():
    return {
        "message": "Triathlon Real Data Format Management API v3.1",
        "status": "running",
        "updates": [
            "Admin functionality modularized into separate files",
            "Improved code organization and maintainability",
            "Preserved all existing API endpoints"
        ],
        "admin_modules": [
            "stats - システム統計・ダッシュボード",
            "users - ユーザー管理（作成・削除・パスワードリセット）",
            "competitions - 大会管理",
            "data_uploads - データアップロード機能",
            "mappings - センサーマッピング管理"
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
        "version": "3.1.0",
        "database": "real_data_format_ready",
        "supported_formats": ["halshare", "e-Celcius", "TCX"],
        "admin_modules": "modularized"
    }