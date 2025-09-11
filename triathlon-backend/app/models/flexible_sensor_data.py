"""
app/models/flexible_sensor_data.py

実際のデータ形式に対応した修正版
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index, Boolean, func, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum
import json

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

class UploadStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"

# === 生センサーデータテーブル（マッピング不要） ===

class RawSensorData(Base):
    """生センサーデータ - マッピングなしでも保存"""
    __tablename__ = "raw_sensor_data"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(100), nullable=False, index=True)
    sensor_type = Column(Enum(SensorType), nullable=False, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False, index=True)
        
    # データ内容
    timestamp = Column(DateTime, nullable=False, index=True)
    data_values = Column(Text, nullable=False)  # JSON形式でセンサー値を保存
    raw_data = Column(Text, nullable=True)      # 元のCSV行データ
    
    # マッピング状態
    mapping_status = Column(Enum(SensorDataStatus), default=SensorDataStatus.UNMAPPED, index=True)
    mapped_user_id = Column(String(50), ForeignKey("users.user_id"), nullable=True, index=True)
    mapped_at = Column(DateTime, nullable=True)
    
    # メタデータ
    upload_batch_id = Column(String(100), nullable=True, index=True)
    data_source = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # リレーション
    competition = relationship("Competition")
    mapped_user = relationship("User", foreign_keys=[mapped_user_id])
    
    # インデックス
    __table_args__ = (
        Index('idx_sensor_type_status', 'sensor_type', 'mapping_status'),
        Index('idx_competition_sensor_timestamp', 'competition_id', 'sensor_id', 'timestamp'),
        Index('idx_unmapped_data', 'sensor_type', 'mapping_status', 'competition_id'),
    )
    
    def get_data_as_dict(self):
        """データ値をPython辞書として取得"""
        return json.loads(self.data_values) if self.data_values else {}
    
    def set_data_from_dict(self, data_dict):
        """Python辞書からデータ値を設定"""
        self.data_values = json.dumps(data_dict)

# === 🆕 実際のデータ形式に対応した専用テーブル ===

class SkinTemperatureData(Base):
    """体表温データ（halshare）- 実データ形式対応"""
    __tablename__ = "skin_temperature_data"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # センサー識別（実データに対応）
    halshare_wearer_name = Column(String(100), nullable=False)  # 今後のメイン識別子候補
    halshare_id = Column(String(100), nullable=False, index=True)  # 現在のメイン識別子
    
    # 測定データ
    datetime = Column(DateTime, nullable=False, index=True)
    temperature = Column(Float, nullable=False)
    
    # アップロード管理
    upload_batch_id = Column(String(200), nullable=False, index=True)  # {日時}_{ファイル名}
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False, index=True)
    uploaded_at = Column(DateTime, server_default=func.now())
    
    # マッピング（後から設定）
    mapped_user_id = Column(String(50), ForeignKey("users.user_id"), nullable=True, index=True)
    mapped_at = Column(DateTime, nullable=True)
    
    # リレーション
    user = relationship("User", foreign_keys=[mapped_user_id])
    competition = relationship("Competition")

class CoreTemperatureData(Base):
    """カプセル体温データ（e-Celcius）- 実データ形式対応"""
    __tablename__ = "core_temperature_data"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # センサー識別（実データに対応）
    capsule_id = Column(String(100), nullable=False, index=True)  # Pill n-1, n-2, n-3の識別子
    monitor_id = Column(String(100), nullable=False)  # モニター識別子（ファイル名由来）
    
    # 測定データ
    datetime = Column(DateTime, nullable=False, index=True)  # Date + Hour 結合
    temperature = Column(Float, nullable=True)  # Missing dataの場合null
    status = Column(String(50), nullable=True)  # "Synchronized", "Missing data" etc.
    
    # アップロード管理
    upload_batch_id = Column(String(200), nullable=False, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False, index=True)
    uploaded_at = Column(DateTime, server_default=func.now())
    
    # マッピング（後から設定）
    mapped_user_id = Column(String(50), ForeignKey("users.user_id"), nullable=True, index=True)
    mapped_at = Column(DateTime, nullable=True)
    
    # リレーション
    user = relationship("User", foreign_keys=[mapped_user_id])
    competition = relationship("Competition")

class HeartRateData(Base):
    """心拍データ（Garmin TCX）- 実データ形式対応"""
    __tablename__ = "heart_rate_data"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # センサー識別（入力時に手動指定）
    sensor_id = Column(String(100), nullable=False, index=True)  # 入力時に指定
    
    # 測定データ
    time = Column(DateTime, nullable=False, index=True)  # TCXのTime要素
    heart_rate = Column(Integer, nullable=True)  # HeartRateBpmのValue
    
    # アップロード管理
    upload_batch_id = Column(String(200), nullable=False, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False, index=True)
    uploaded_at = Column(DateTime, server_default=func.now())
    
    # マッピング（後から設定）
    mapped_user_id = Column(String(50), ForeignKey("users.user_id"), nullable=True, index=True)
    mapped_at = Column(DateTime, nullable=True)
    
    # リレーション
    user = relationship("User", foreign_keys=[mapped_user_id])
    competition = relationship("Competition")

# === 🆕 アップロードバッチ管理 ===
class UploadBatch(Base):
    """アップロードバッチ管理"""
    __tablename__ = "upload_batches"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(200), unique=True, nullable=False, index=True)  # {日時}_{ファイル名}
    
    # バッチ情報
    sensor_type = Column(Enum(SensorType), nullable=False)
    file_name = Column(String(200), nullable=False)
    file_size = Column(Integer, nullable=True)
    
    # 処理結果
    total_records = Column(Integer, nullable=False, default=0)
    success_records = Column(Integer, nullable=False, default=0)
    failed_records = Column(Integer, nullable=False, default=0)
    status = Column(Enum(UploadStatus), nullable=False, default=UploadStatus.SUCCESS)
    
    # メタデータ
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False, index=True)
    uploaded_by = Column(String(50), nullable=False)  # 管理者ID
    uploaded_at = Column(DateTime, server_default=func.now())
    
    # エラー情報
    error_message = Column(Text, nullable=True)
    processing_notes = Column(Text, nullable=True)
    
    # リレーション
    competition = relationship("Competition")

# === 🆕 センサーマッピング（マッピングデータ用） ===
class SensorMapping(Base):
    """センサーマッピング"""
    __tablename__ = "sensor_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # マッピング対象
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False, index=True)
    
    # センサーID
    skin_temp_sensor_id = Column(String(100), nullable=True)     # 体表温センサID
    core_temp_sensor_id = Column(String(100), nullable=True)     # カプセル体温センサID  
    heart_rate_sensor_id = Column(String(100), nullable=True)    # 心拍センサID
    race_record_id = Column(String(100), nullable=True)          # 大会記録ID（ゼッケン番号）
    
    # メタデータ
    uploaded_at = Column(DateTime, server_default=func.now())
    upload_batch_id = Column(String(200), nullable=False, index=True)
    
    # リレーション
    user = relationship("User", foreign_keys=[user_id])
    competition = relationship("Competition")
    
    # ユニーク制約
    __table_args__ = (
        Index('idx_user_competition_mapping', 'user_id', 'competition_id', unique=True),
    )

# === WBGT環境データ（既存のまま） ===

class WBGTData(Base):
    """WBGT環境データ"""
    __tablename__ = "wbgt_data"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_data_id = Column(Integer, ForeignKey("raw_sensor_data.id"), nullable=True)
    station_id = Column(String(100), nullable=False, index=True)
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

# === 柔軟なセンサーマッピング（既存のまま） ===

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
    effective_from = Column(DateTime, nullable=True)
    effective_to = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # リレーション
    user = relationship("User", foreign_keys=[user_id])
    competition = relationship("Competition")
    
    # ユニーク制約
    __table_args__ = (
        Index('idx_sensor_mapping_unique', 'sensor_id', 'sensor_type', 'competition_id', unique=True),
        Index('idx_user_sensor_type', 'user_id', 'sensor_type', 'competition_id'),
    )

# === データ統合ビュー（既存互換性のため） ===

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
    primary_value = Column(Float, nullable=True)    # メイン値（温度 or 心拍数）
    secondary_value = Column(Float, nullable=True)  # サブ値
    raw_data_id = Column(Integer, ForeignKey("raw_sensor_data.id"), nullable=False)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # リレーション
    raw_data = relationship("RawSensorData")
    user = relationship("User", foreign_keys=[user_id])
    competition = relationship("Competition")