"""
app/models/flexible_sensor_data.py

実際のデータ形式に対応した修正版（WBGT実データ対応）
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index, Boolean, func, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum
import json
from typing import Dict, Optional

class SensorDataStatus(str, enum.Enum):
    """センサーデータの状態"""
    UNMAPPED = "unmapped"        # マッピング未設定
    MAPPED = "mapped"            # マッピング済み
    INVALID_MAPPING = "invalid"  # マッピング無効（ユーザー不存在等）
    ARCHIVED = "archived"        # アーカイブ済み

class SensorType(str, enum.Enum):
    """センサーの種類"""
    SKIN_TEMPERATURE = "skin_temperature"     # 体表温（halshare）
    CORE_TEMPERATURE = "core_temperature"     # カプセル体温（e-Celcius）
    HEART_RATE = "heart_rate"                 # 心拍（Garmin）
    RACE_RECORD = "race_record"               # 🆕 大会記録
    WBGT = "wbgt"                            # WBGT環境データ
    OTHER = "other"                          # その他

class UploadStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    PROCESSING = "processing"

# === 実際のデータ形式に対応した専用テーブル ===

class SkinTemperatureData(Base):
    """体表温データ（完全正規化版）"""
    __tablename__ = "skin_temperature_data"
    
    id = Column(Integer, primary_key=True, index=True)
    halshare_id = Column(String(100), nullable=False, index=True)
    datetime = Column(DateTime, nullable=False, index=True)
    temperature = Column(Float, nullable=False)
    
    # アップロード管理
    upload_batch_id = Column(String(200), nullable=False, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False)
    uploaded_at = Column(DateTime, server_default=func.now())
    
    # リレーション
    competition = relationship("Competition")

class CoreTemperatureData(Base):
    """カプセル体温データ（完全正規化版）"""
    __tablename__ = "core_temperature_data"
    
    id = Column(Integer, primary_key=True, index=True)
    capsule_id = Column(String(100), nullable=False, index=True)
    monitor_id = Column(String(100), nullable=False)
    datetime = Column(DateTime, nullable=False, index=True)
    temperature = Column(Float, nullable=True)
    status = Column(String(50), nullable=True)
    
    # アップロード管理
    upload_batch_id = Column(String(200), nullable=False, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False)
    uploaded_at = Column(DateTime, server_default=func.now())
    
    # リレーション
    competition = relationship("Competition")

class HeartRateData(Base):
    """心拍データ（完全正規化版）"""
    __tablename__ = "heart_rate_data"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(100), nullable=False, index=True)
    time = Column(DateTime, nullable=False, index=True)
    heart_rate = Column(Integer, nullable=True)
    
    # アップロード管理
    upload_batch_id = Column(String(200), nullable=False, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False)
    uploaded_at = Column(DateTime, server_default=func.now())
    
    # リレーション
    competition = relationship("Competition")

# === WBGT環境データ（実データ対応版） ===

class WBGTData(Base):
    """WBGT環境データ"""
    __tablename__ = "wbgt_data"
    
    id = Column(Integer, primary_key=True, index=True)
    
    timestamp = Column(DateTime, nullable=False, index=True)
    # WBGT固有データ
    wbgt_value = Column(Float, nullable=False)
    air_temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    globe_temperature = Column(Float, nullable=True)
    
    # アップロード管理
    upload_batch_id = Column(String(200), nullable=False, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False, index=True)
    uploaded_at = Column(DateTime, server_default=func.now())

    # リレーション
    competition = relationship("Competition")


# === アップロードバッチ管理 ===
class UploadBatch(Base):
    """アップロードバッチ管理"""
    __tablename__ = "upload_batches"
    
    id = Column(Integer, primary_key=True, index=True)

    batch_id = Column(String(200), unique=True, nullable=False, index=True)  # {日時}_{ファイル名}
    sensor_type = Column(Enum(SensorType), nullable=False, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False, index=True)
    
    # ファイル情報
    file_name = Column(String(255), nullable=False)
    
    # 処理結果
    total_records = Column(Integer, nullable=False)
    success_records = Column(Integer, nullable=False, default=0)
    failed_records = Column(Integer, nullable=False, default=0)
    status = Column(Enum(UploadStatus), nullable=False)
    
    # メタデータ
    uploaded_at = Column(DateTime, server_default=func.now())
    
    # リレーション
    competition = relationship("Competition")

# === センサーマッピング ===

class FlexibleSensorMapping(Base):
    """センサーマッピング（シンプル版）"""
    __tablename__ = "flexible_sensor_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(100), nullable=False, index=True)
    sensor_type = Column(Enum(SensorType), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False, index=True)
    
    # オプション情報
    subject_name = Column(String(255), nullable=True)
    device_type = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # リレーション
    user = relationship("User", foreign_keys=[user_id])
    competition = relationship("Competition")
    
    # ユニーク制約
    __table_args__ = (
        Index('idx_sensor_mapping_unique', 'sensor_id', 'sensor_type', 'competition_id', unique=True),
    )