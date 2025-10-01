"""
app/schemas/sensor_data.py (実データ対応版)
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models.flexible_sensor_data import SensorType, UploadStatus

# === 🆕 実データ対応スキーマ ===

class UploadBatchResponse(BaseModel):
    batch_id: str
    sensor_type: str  # SensorType のenum値
    file_name: str
    total_records: int
    success_records: int
    failed_records: int
    status: str  # UploadStatus のenum値
    uploaded_at: datetime
    uploaded_by: str
    competition_id: str
    
    class Config:
        from_attributes = True

class SkinTemperatureResponse(BaseModel):
    id: int
    halshare_wearer_name: str
    halshare_id: str
    datetime: datetime
    temperature: float
    upload_batch_id: str
    competition_id: str
    mapped_user_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class CoreTemperatureResponse(BaseModel):
    id: int
    capsule_id: str
    monitor_id: str
    datetime: datetime
    temperature: Optional[float]
    status: Optional[str]
    upload_batch_id: str
    competition_id: str
    mapped_user_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class HeartRateResponse(BaseModel):
    id: int
    sensor_id: str
    time: datetime
    heart_rate: Optional[int]
    upload_batch_id: str
    competition_id: str
    mapped_user_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class SensorMappingResponse(BaseModel):
    """マッピングレスポンス（不要フィールド削除、upload_batch_id追加）"""
    id: int
    user_id: str
    competition_id: str
    sensor_id: str
    sensor_type: str
    upload_batch_id: Optional[str] = None  # 🆕 追加
    created_at: datetime
    
    class Config:
        from_attributes = True

# === アップロード関連スキーマ ===

class UploadResult(BaseModel):
    file: str
    batch_id: Optional[str] = None
    total: Optional[int] = None
    success: Optional[int] = None
    failed: Optional[int] = None
    status: str
    error: Optional[str] = None
    sensor_ids: Optional[List[str]] = None
    trackpoints_total: Optional[int] = None  # TCX用
    sensors_found: Optional[int] = None      # カプセル温用

class BatchDeleteResponse(BaseModel):
    message: str
    sensor_type: str
    file_name: str
    deleted_records: int

class BatchListResponse(BaseModel):
    batches: List[UploadBatchResponse]
    total: int

# === 統計・サマリー用スキーマ ===

class DataSummaryResponse(BaseModel):
    total_batches: int
    total_records: int
    records_by_type: dict  # {"skin_temperature": 100, "core_temperature": 50, ...}
    recent_uploads: List[UploadBatchResponse]
    competitions_with_data: List[str]

class MappingStatusResponse(BaseModel):
    """マッピング状態サマリー"""
    total_users: int
    mapped_users: int
    unmapped_sensors: int
    mapping_coverage: float

# === エラーレポート用スキーマ ===

class UploadError(BaseModel):
    line_number: int
    error_message: str
    raw_data: str

class DetailedUploadResult(UploadResult):
    errors: List[UploadError] = []
    warnings: List[str] = []
    processing_time_seconds: float

# === 🔧 flexible_csv_service.py用のスキーマ（互換性） ===

class UploadResponse(BaseModel):
    success: bool
    message: str
    total_records: int
    processed_records: int

class MappingResponse(BaseModel):
    """マッピングアップロード結果"""
    success: bool
    message: str
    total_records: int
    processed_records: int
    skipped_records: int = 0
    errors: list = []
    batch_id: Optional[str] = None  # 🆕 追加

class DataSummaryResponse(BaseModel):
    total_records: int
    mapped_records: int
    unmapped_records: int
    sensor_counts: dict
    competition_id: Optional[str] = None

class MappingStatusResponse(BaseModel):
    total_users: int
    mapped_users: int
    unmapped_sensors: int
    mapping_coverage: float