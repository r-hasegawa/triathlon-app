"""
app/models/__init__.py (実データ対応版)
"""

# Core models
from .user import User, AdminUser
from .competition import Competition, RaceRecord

# 🆕 実データ対応マルチセンサーシステム
from .flexible_sensor_data import (
    # Enums
    SensorType,
    SensorDataStatus,
    UploadStatus,
    
    # Core tables
    RawSensorData,
    FlexibleSensorMapping,
    
    # 🆕 実データ対応テーブル
    SkinTemperatureData,
    CoreTemperatureData, 
    HeartRateData,
    UploadBatch,
    
    # Environment data
    WBGTData,
    
    # View
    SensorDataView
)

__all__ = [
    # Core
    "User",
    "AdminUser", 
    "Competition",
    "RaceRecord",
    
    # Multi-sensor system
    "SensorType",
    "SensorDataStatus",
    "UploadStatus", 
    "RawSensorData",
    "FlexibleSensorMapping",
    
    # 🆕 Real data format tables
    "SkinTemperatureData",
    "CoreTemperatureData",
    "HeartRateData",
    "UploadBatch",
    
    # Environment & View
    "WBGTData",
    "SensorDataView"
]