"""
app/models/__init__.py

全モデルのインポート統合
"""

# 既存モデル
from .user import User, AdminUser
from .sensor_data import (
    SensorData, 
    SensorMapping, 
    UploadHistory,
    CapsuleTemperatureData,
    HeartRateData
)

# 🆕 新規モデル
from .competition import (
    Competition,
    RaceRecord, 
    WBGTData
)

# エクスポート用
__all__ = [
    # ユーザー関連
    "User",
    "AdminUser",
    
    # センサデータ関連
    "SensorData",
    "SensorMapping", 
    "UploadHistory",
    "CapsuleTemperatureData",
    "HeartRateData",
    
    # 🆕 大会関連
    "Competition",
    "RaceRecord",
    "WBGTData",
]