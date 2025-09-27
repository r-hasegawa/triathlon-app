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
router = APIRouter(prefix="/admin", tags=["管理者"])

# 各機能ルーターを統合
router.include_router(stats_router)
router.include_router(users_router)
router.include_router(competitions_router)
router.include_router(uploads_router)  # /admin/upload/*
router.include_router(mappings_router)
router.include_router(batches_router)
router.include_router(race_records_router)  # /admin/race-records/*
