from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index, Boolean, func
from sqlalchemy.orm import relationship
from app.database import Base

class SensorData(Base):
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    temperature = Column(Float, nullable=False)  # 体表温度
    raw_data = Column(Text, nullable=True)  # 生データのJSONまたはCSV行
    data_source = Column(String(100), nullable=True)  # データソース識別
    created_at = Column(DateTime, server_default=func.now())
    
    # インデックス設定（複合インデックス）
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_sensor_timestamp', 'sensor_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<SensorData(sensor_id='{self.sensor_id}', timestamp='{self.timestamp}', temp={self.temperature})>"

class SensorMapping(Base):
    __tablename__ = "sensor_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    subject_name = Column(String(255), nullable=True)  # 被験者名（オプション）
    device_type = Column(String(100), default="temperature_sensor")
    calibration_offset = Column(Float, default=0.0)  # キャリブレーション補正値
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f"<SensorMapping(sensor_id='{self.sensor_id}', user_id='{self.user_id}')>"

class UploadHistory(Base):
    __tablename__ = "upload_history"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(String(100), unique=True, nullable=False, index=True)
    admin_id = Column(String(50), ForeignKey("admin_users.admin_id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    records_count = Column(Integer, default=0)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<UploadHistory(filename='{self.filename}', status='{self.status}')>"