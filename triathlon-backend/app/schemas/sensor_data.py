from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime

class SensorType(str, Enum):
    SKIN_TEMPERATURE = "skin_temperature"
    CORE_TEMPERATURE = "core_temperature"
    HEART_RATE = "heart_rate"
    WBGT = "wbgt"
    OTHER = "other"

class SensorDataStatus(str, Enum):
    UNMAPPED = "unmapped"
    MAPPED = "mapped"
    INVALID_MAPPING = "invalid"
    ARCHIVED = "archived"

# 既存のスキーマ（互換性維持）
class SensorDataBase(BaseModel):
    sensor_id: str = Field(..., max_length=100)
    timestamp: datetime
    temperature: float = Field(..., ge=-50.0, le=100.0)
    raw_data: Optional[str] = None

class SensorDataCreate(SensorDataBase):
    user_id: str

class SensorDataResponse(SensorDataBase):
    id: int
    user_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class SensorMappingBase(BaseModel):
    sensor_id: str = Field(..., max_length=100)
    user_id: str = Field(..., max_length=50)
    subject_name: Optional[str] = None
    device_type: str = "temperature_sensor"
    calibration_offset: float = 0.0

class SensorMappingCreate(SensorMappingBase):
    pass

class SensorMappingResponse(SensorMappingBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class SensorDataStats(BaseModel):
    total_records: int
    min_temperature: float
    max_temperature: float
    avg_temperature: float
    start_time: datetime
    end_time: datetime

class SensorDataPaginated(BaseModel):
    data: List[SensorDataResponse]
    total: int
    page: int
    limit: int
    has_next: bool

# 新しいマルチセンサー用スキーマ
class UploadResponse(BaseModel):
    success: bool
    message: str
    total_records: int
    processed_records: int
    error_details: Optional[str] = None

class MappingResponse(BaseModel):
    success: bool
    message: str
    mapped_sensors: int
    error_details: Optional[str] = None

class DataSummaryResponse(BaseModel):
    total_sensor_records: int
    mapped_records: int
    unmapped_records: int
    sensor_type_counts: Dict[str, int]
    wbgt_records: int
    mapping_records: int
    competition_id: Optional[str]

class MappingStatusResponse(BaseModel):
    status_counts: Dict[str, int]
    unmapped_by_sensor_type: Dict[str, int]
    competition_id: Optional[str]