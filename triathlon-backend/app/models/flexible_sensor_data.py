"""
app/models/flexible_sensor_data.py

マッピング不要でもデータを保持できる柔軟なセンサーデータモデル
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index, Boolean, func, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum

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
    WBGT = "wbgt"                            # WBGT環境データ
    OTHER = "other"                          # その他

# === 🆕 生センサーデータテーブル（マッピング不要） ===

class RawSensorData(Base):
    """生センサーデータ - マッピングなしでも保存"""
    __tablename__ = "raw_sensor_data"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(100), nullable=False, index=True)
    sensor_type = Column(Enum(SensorType), nullable=False, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=True, index=True)
    
    # データ内容
    timestamp = Column(DateTime, nullable=False, index=True)
    data_values = Column(Text, nullable=False)  # JSON形式でセンサー値を保存
    raw_data = Column(Text, nullable=True)      # 元のCSV行データ
    
    # マッピング状態
    mapping_status = Column(Enum(SensorDataStatus), default=SensorDataStatus.UNMAPPED, index=True)
    mapped_user_id = Column(String(50), ForeignKey("users.user_id"), nullable=True, index=True)
    
    # メタデータ
    upload_batch_id = Column(String(100), nullable=True, index=True)  # アップロードバッチ識別
    data_source = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    mapped_at = Column(DateTime, nullable=True)

    # リレーション（循環インポートを避けるため文字列で参照）
    competition = relationship("Competition")
    mapped_user = relationship("User", foreign_keys=[mapped_user_id])
    
    # 専用テーブルへのリレーション
    skin_temperature = relationship("SkinTemperatureData", back_populates="raw_data", uselist=False)
    core_temperature = relationship("CoreTemperatureData", back_populates="raw_data", uselist=False)
    heart_rate = relationship("HeartRateData", back_populates="raw_data", uselist=False)
    wbgt = relationship("WBGTData", back_populates="raw_data", uselist=False)
    
    # インデックス
    __table_args__ = (
        Index('idx_sensor_type_status', 'sensor_type', 'mapping_status'),
        Index('idx_competition_sensor_timestamp', 'competition_id', 'sensor_id', 'timestamp'),
        Index('idx_unmapped_data', 'sensor_type', 'mapping_status', 'competition_id'),
    )
    
    def get_data_as_dict(self):
        """データ値をPython辞書として取得"""
        import json
        return json.loads(self.data_values) if self.data_values else {}
    
    def set_data_from_dict(self, data_dict):
        """Python辞書からデータ値を設定"""
        import json
        self.data_values = json.dumps(data_dict)

# === 🆕 センサー種別ごとの専用テーブル ===

class SkinTemperatureData(Base):
    """体表温データ（halshare）"""
    __tablename__ = "skin_temperature_data"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_data_id = Column(Integer, ForeignKey("raw_sensor_data.id"), nullable=False, unique=True)
    sensor_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=True, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # 体表温固有データ
    skin_temperature = Column(Float, nullable=False)
    sensor_location = Column(String(50), nullable=True)  # センサー装着位置
    ambient_temperature = Column(Float, nullable=True)   # 周囲温度
    
    created_at = Column(DateTime, server_default=func.now())
    
    # リレーション
    raw_data = relationship("RawSensorData")
    user = relationship("User")
    competition = relationship("Competition")

class CoreTemperatureData(Base):
    """カプセル体温データ（e-Celcius）"""
    __tablename__ = "core_temperature_data"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_data_id = Column(Integer, ForeignKey("raw_sensor_data.id"), nullable=False, unique=True)
    monitor_id = Column(String(100), nullable=False, index=True)  # モニターID
    capsule_id = Column(String(100), nullable=False, index=True)  # カプセルID
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=True, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # カプセル体温固有データ
    core_temperature = Column(Float, nullable=False)
    battery_level = Column(Float, nullable=True)
    signal_strength = Column(Float, nullable=True)
    capsule_status = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # リレーション
    raw_data = relationship("RawSensorData")
    user = relationship("User")
    competition = relationship("Competition")

class HeartRateData(Base):
    """心拍データ（Garmin）"""
    __tablename__ = "heart_rate_data"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_data_id = Column(Integer, ForeignKey("raw_sensor_data.id"), nullable=False, unique=True)
    device_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=True, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # 心拍固有データ
    heart_rate = Column(Integer, nullable=False)
    heart_rate_zone = Column(Integer, nullable=True)
    rrinterval = Column(Float, nullable=True)
    activity_type = Column(String(50), nullable=True)
    calories = Column(Float, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # リレーション
    raw_data = relationship("RawSensorData")
    user = relationship("User")
    competition = relationship("Competition")

class WBGTData(Base):
    """WBGT環境データ"""
    __tablename__ = "wbgt_data"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_data_id = Column(Integer, ForeignKey("raw_sensor_data.id"), nullable=False, unique=True)
    station_id = Column(String(100), nullable=False, index=True)  # 測定局ID
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # WBGT固有データ
    wbgt_value = Column(Float, nullable=False)
    air_temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)
    solar_radiation = Column(Float, nullable=True)
    location = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # リレーション
    raw_data = relationship("RawSensorData")
    competition = relationship("Competition")

# === 🆕 柔軟なセンサーマッピング ===

class FlexibleSensorMapping(Base):
    """柔軟なセンサーマッピング"""
    __tablename__ = "flexible_sensor_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(100), nullable=False, index=True)
    sensor_type = Column(Enum(SensorType), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=True, index=True)
    
    # マッピング詳細
    subject_name = Column(String(255), nullable=True)
    device_type = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    # 適用期間
    effective_from = Column(DateTime, nullable=True)  # 適用開始日時
    effective_to = Column(DateTime, nullable=True)    # 適用終了日時
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # リレーション
    user = relationship("User")
    competition = relationship("Competition")
    
    # ユニーク制約：同一大会・同一センサー種別内でセンサーIDは一意
    __table_args__ = (
        Index('idx_sensor_mapping_unique', 'sensor_id', 'sensor_type', 'competition_id', unique=True),
        Index('idx_user_sensor_type', 'user_id', 'sensor_type', 'competition_id'),
    )

# === 🆕 データ統合ビュー（既存互換性のため） ===

class SensorDataView(Base):
    """既存システムとの互換性のための統合ビュー"""
    __tablename__ = "sensor_data_view"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(100), nullable=False, index=True)
    sensor_type = Column(Enum(SensorType), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=True, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # 共通データ項目
    primary_value = Column(Float, nullable=True)  # メイン値（温度 or 心拍数）
    secondary_value = Column(Float, nullable=True)  # サブ値
    raw_data_id = Column(Integer, ForeignKey("raw_sensor_data.id"), nullable=False)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # リレーション
    raw_data = relationship("RawSensorData")
    user = relationship("User")
    competition = relationship("Competition")