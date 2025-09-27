"""
app/routers/admin/__init__.py
管理者機能の統合ルーター
"""

from fastapi import APIRouter

# 各機能ルーターのインポート
from .stats import router as stats_router
from .users import router as users_router
from .competitions import router as competitions_router
from .data_uploads import router as uploads_router
from .mappings import router as mappings_router

# メインの管理者ルーター
router = APIRouter(prefix="/admin", tags=["admin"])

# 各機能ルーターを統合
router.include_router(stats_router)
router.include_router(users_router)
router.include_router(competitions_router)
router.include_router(uploads_router)
router.include_router(mappings_router)