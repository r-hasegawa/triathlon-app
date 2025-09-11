from .user import UserBase, UserCreate, UserUpdate, UserResponse, AdminBase, AdminCreate, AdminResponse
from .sensor_data import (
    # 既存スキーマ
    SensorDataBase, SensorDataCreate, SensorDataResponse,
    SensorMappingBase, SensorMappingCreate, SensorMappingResponse,
    SensorDataStats, SensorDataPaginated,
    
    # 🆕 実データ対応スキーマ
    UploadBatchResponse, SkinTemperatureResponse, 
    CoreTemperatureResponse, HeartRateResponse,
    UploadResult, BatchDeleteResponse,
    
    # 🔧 flexible_csv_service.py互換スキーマ
    UploadResponse, MappingResponse, DataSummaryResponse, MappingStatusResponse,
    
    # 詳細スキーマ
    BatchListResponse, UploadError, DetailedUploadResult
)
from .auth import Token, TokenData, LoginRequest, LoginResponse

__all__ = [
    # Core user/auth schemas
    "UserBase", "UserCreate", "UserUpdate", "UserResponse",
    "AdminBase", "AdminCreate", "AdminResponse",
    "Token", "TokenData", "LoginRequest", "LoginResponse",
    
    # Legacy sensor schemas (互換性維持)
    "SensorDataBase", "SensorDataCreate", "SensorDataResponse",
    "SensorMappingBase", "SensorMappingCreate", "SensorMappingResponse",
    "SensorDataStats", "SensorDataPaginated",
    
    # 🆕 Real data format schemas
    "UploadBatchResponse", "SkinTemperatureResponse", 
    "CoreTemperatureResponse", "HeartRateResponse",
    "UploadResult", "BatchDeleteResponse", "BatchListResponse",
    
    # 🔧 Service compatibility schemas
    "UploadResponse", "MappingResponse", "DataSummaryResponse", "MappingStatusResponse",
    
    # Error handling
    "UploadError", "DetailedUploadResult"
]