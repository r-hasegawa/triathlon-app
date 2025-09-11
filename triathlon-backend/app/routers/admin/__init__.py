"""
app/routers/admin/__init__.py
"""

from fastapi import APIRouter
from . import upload

# 管理者専用ルーターを統合
router = APIRouter(prefix="/admin")

# 存在するサブルーターのみ含める
router.include_router(upload.router)