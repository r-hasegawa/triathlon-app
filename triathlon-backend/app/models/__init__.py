"""
app/models/__init__.py (新システムのみ版)
"""

# Core models
from .user import User, AdminUser
from .competition import Competition, RaceRecord

# 🆕 新しいマルチセンサーシステムのみ
from .flexible_sensor_data import (
    # Enums
    SensorType,
    SensorDataStatus,
    
    # Core tables
    RawSensorData,
    FlexibleSensorMapping,
    
    # Specialized tables
    SkinTemperatureData,
    CoreTemperatureData, 
    HeartRateData,
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
    
    # New multi-sensor system
    "SensorType",
    "SensorDataStatus", 
    "RawSensorData",
    "FlexibleSensorMapping",
    "SkinTemperatureData",
    "CoreTemperatureData",
    "HeartRateData", 
    "WBGTData",
    "SensorDataView"
]