from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class SensorDataBase(BaseModel):
    sensor_id: str = Field(..., max_length=100)
    timestamp: datetime
    temperature: float = Field(..., ge=-50.0, le=100.0)  # 温度範囲制限
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

# データ統計用スキーマ
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