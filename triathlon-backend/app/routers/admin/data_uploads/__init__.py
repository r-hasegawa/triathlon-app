"""
app/routers/admin/data_upload/__init__.py
データアップロード機能のメインルーター
"""

from fastapi import APIRouter
from .skin_temperature import router as skin_temperature_router
from .core_temperature import router as core_temperature_router
from .heart_rate import router as heart_rate_router
from .wbgt import router as wbgt_router
from .mapping import router as mapping_router
from .race_records import router as race_records_upload_router

# データアップロード関連のサブルーター
router = APIRouter()

# 各センサーデータのルーターを統合
router.include_router(skin_temperature_router, tags=["skin-temperature"])
router.include_router(core_temperature_router, tags=["core-temperature"])
router.include_router(heart_rate_router, tags=["heart-rate"])
router.include_router(wbgt_router, tags=["wbgt"])
router.include_router(mapping_router, tags=["mapping"])
router.include_router(race_records_upload_router, tags=["race-records-upload"])