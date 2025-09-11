"""
app/models/sensor_data.py (更新版)

大会管理機能対応のためのセンサデータモデル
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index, Boolean, func
from sqlalchemy.orm import relationship
from app.database import Base

class SensorData(Base):
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=True, index=True)  # 🆕 大会ID追加
    timestamp = Column(DateTime, nullable=False, index=True)
    temperature = Column(Float, nullable=False)  # 体表温度
    raw_data = Column(Text, nullable=True)  # 生データのJSONまたはCSV行
    data_source = Column(String(100), nullable=True)  # データソース識別
    created_at = Column(DateTime, server_default=func.now())
    
    # リレーション 🆕
    competition = relationship("Competition", back_populates="sensor_data")
    user = relationship("User")
    
    # インデックス設定（大会ID追加）
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_sensor_timestamp', 'sensor_id', 'timestamp'),
        Index('idx_competition_user_timestamp', 'competition_id', 'user_id', 'timestamp'),  # 🆕
    )
    
    def __repr__(self):
        return f"<SensorData(sensor_id='{self.sensor_id}', timestamp='{self.timestamp}', temp={self.temperature})>"

class SensorMapping(Base):
    __tablename__ = "sensor_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(100), nullable=False, index=True)  # 🔄 ユニーク制約削除（大会ごとに使い回し可能）
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=True, index=True)  # 🆕 大会ID追加
    subject_name = Column(String(255), nullable=True)  # 被験者名（オプション）
    device_type = Column(String(100), default="temperature_sensor")
    calibration_offset = Column(Float, default=0.0)  # キャリブレーション補正値
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # リレーション 🆕
    competition = relationship("Competition", back_populates="sensor_mappings")
    user = relationship("User")
    
    # 🆕 ユニーク制約: 同一大会内でセンサーIDは一意
    __table_args__ = (
        Index('idx_sensor_competition_unique', 'sensor_id', 'competition_id', unique=True),
    )
    
    def __repr__(self):
        return f"<SensorMapping(sensor_id='{self.sensor_id}', user_id='{self.user_id}', competition='{self.competition_id}')>"

class UploadHistory(Base):
    __tablename__ = "upload_history"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(String(100), unique=True, nullable=False, index=True)
    admin_id = Column(String(50), ForeignKey("admin_users.admin_id"), nullable=False)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=True, index=True)  # 🆕 大会ID追加
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    records_count = Column(Integer, default=0)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime, nullable=True)
    
    # リレーション 🆕
    competition = relationship("Competition")
    admin = relationship("AdminUser")
    
    def __repr__(self):
        return f"<UploadHistory(filename='{self.filename}', status='{self.status}', competition='{self.competition_id}')>"

# 🆕 新しいセンサデータ種別

class CapsuleTemperatureData(Base):
    """カプセル体温データ (e-Celcius)"""
    __tablename__ = "capsule_temperature_data"
    
    id = Column(Integer, primary_key=True, index=True)
    monitor_id = Column(String(100), nullable=False, index=True)  # モニターID
    capsule_id = Column(String(100), nullable=False, index=True)  # カプセルID (1-3)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    core_temperature = Column(Float, nullable=False)  # カプセル体温
    battery_level = Column(Float, nullable=True)  # バッテリーレベル
    signal_strength = Column(Float, nullable=True)  # 信号強度
    raw_data = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # リレーション
    competition = relationship("Competition")
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_capsule_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_monitor_capsule_timestamp', 'monitor_id', 'capsule_id', 'timestamp'),
    )

class HeartRateData(Base):
    """心拍データ (Garmin)"""
    __tablename__ = "heart_rate_data"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), nullable=False, index=True)  # GarminデバイスID
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    heart_rate = Column(Integer, nullable=False)  # 心拍数 (bpm)
    heart_rate_zone = Column(Integer, nullable=True)  # 心拍ゾーン (1-5)
    rrinterval = Column(Float, nullable=True)  # RR間隔 (ms)
    activity_type = Column(String(50), nullable=True)  # アクティビティタイプ
    raw_data = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # リレーション
    competition = relationship("Competition")
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_hr_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_device_timestamp', 'device_id', 'timestamp'),
    )