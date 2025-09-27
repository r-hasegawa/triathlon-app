"""
app/routers/admin/stats.py
システム統計・ダッシュボード機能
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, AdminUser
from app.models.competition import Competition, RaceRecord
from app.models.flexible_sensor_data import (
    SkinTemperatureData, CoreTemperatureData, HeartRateData, 
    WBGTData, FlexibleSensorMapping
)
from app.utils.dependencies import get_current_admin

router = APIRouter()


@router.get("/stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """管理者向けシステム統計情報（シンプル化版）"""
    try:
        # ユーザー統計
        total_users = db.query(User).count()
        total_admins = db.query(AdminUser).count()
        
        # 大会統計
        total_competitions = db.query(Competition).count()
        
        # センサーデータ統計（シンプル）
        total_skin_temp = db.query(SkinTemperatureData).count()
        total_core_temp = db.query(CoreTemperatureData).count()
        total_heart_rate = db.query(HeartRateData).count()
        total_wbgt = db.query(WBGTData).count()
        total_race_records = db.query(RaceRecord).count()
        
        # マッピング統計（物理削除ベース）
        total_mappings = db.query(FlexibleSensorMapping).count()
        
        return {
            "users": {
                "general_users": total_users,
                "admin_users": total_admins,
                "total": total_users + total_admins
            },
            "competitions": {
                "total": total_competitions
            },
            "sensor_data": {
                "skin_temperature": total_skin_temp,
                "core_temperature": total_core_temp,
                "heart_rate": total_heart_rate,
                "wbgt": total_wbgt,
                "total": total_skin_temp + total_core_temp + total_heart_rate + total_wbgt
            },
            "race_records": {
                "total": total_race_records
            },
            "mappings": {
                "total": total_mappings
            }
        }
        
    except Exception as e:
        # エラーハンドリング：部分的な統計でも返す
        return {
            "error": f"統計取得中にエラーが発生しました: {str(e)}",
            "users": {"total": 0},
            "competitions": {"total": 0},
            "sensor_data": {"total": 0},
            "race_records": {"total": 0},
            "mappings": {"total": 0}
        }