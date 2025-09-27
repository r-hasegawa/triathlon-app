"""
app/routers/admin/__init__.py
管理者機能の統合ルーター（data_uploads分割対応版）
"""

from fastapi import APIRouter

# 各機能ルーターのインポート
from .stats import router as stats_router
from .users import router as users_router
from .competitions import router as competitions_router
from .data_uploads import router as uploads_router  # 分割されたdata_uploadsフォルダから
from .mappings import router as mappings_router
from .batches import router as batches_router
from .race_records import router as race_records_router  # 新しく追加

# メインの管理者ルーター
router = APIRouter(prefix="/admin", tags=["admin"])

# 各機能ルーターを統合
router.include_router(stats_router)
router.include_router(users_router)
router.include_router(competitions_router)
router.include_router(uploads_router)  # /admin/upload/*
router.include_router(mappings_router)
router.include_router(batches_router)
router.include_router(race_records_router)  # /admin/race-records/*

# 管理者機能概要エンドポイント
@router.get("/")
async def admin_overview():
    """管理者機能の概要"""
    return {
        "admin_functions": {
            "user_management": "/admin/users/*",
            "competition_management": "/admin/competitions/*", 
            "data_uploads": "/admin/upload/*",
            "race_records": "/admin/race-records/*",
            "sensor_mappings": "/admin/mappings/*",
            "batch_management": "/admin/batches/*",
            "system_stats": "/admin/stats/*"
        },
        "data_upload_endpoints": {
            "skin_temperature": "/admin/upload/skin-temperature",
            "core_temperature": "/admin/upload/core-temperature",
            "heart_rate": "/admin/upload/heart-rate",
            "wbgt": "/admin/upload/wbgt",
            "race_records": "/admin/upload/race-records",
            "mapping": "/admin/upload/mapping"
        },
        "format_info": {
            "skin_temperature": "/admin/upload/skin-temperature/format",
            "core_temperature": "/admin/upload/core-temperature/format",
            "heart_rate": "/admin/upload/heart-rate/format",
            "wbgt": "/admin/upload/wbgt/format",
            "race_records": "/admin/upload/race-records/format",
            "mapping": "/admin/upload/mapping/format"
        }
    }