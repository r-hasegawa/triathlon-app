"""
app/models/competition.py

大会管理用のSQLAlchemyモデル定義
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Boolean, Float, func, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime

class Competition(Base):
    """大会テーブル"""
    __tablename__ = "competitions"
    
    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(String(50), unique=True, nullable=False, index=True)  # 自動生成ID
    name = Column(String(200), nullable=False)  # 大会名
    date = Column(Date, nullable=True)  # 開催日
    location = Column(String(200), nullable=True)  # 開催地
    description = Column(Text, nullable=True)  # 大会説明
    is_active = Column(Boolean, default=True)  # アクティブフラグ
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # リレーション定義（後で追加される他テーブルとの関係）
    sensor_data = relationship("SensorData", back_populates="competition", cascade="all, delete-orphan")
    sensor_mappings = relationship("SensorMapping", back_populates="competition", cascade="all, delete-orphan")
    race_records = relationship("RaceRecord", back_populates="competition", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        # competition_idが指定されていない場合は自動生成
        if 'competition_id' not in kwargs:
            kwargs['competition_id'] = self.generate_competition_id()
        super().__init__(**kwargs)
    
    @staticmethod
    def generate_competition_id():
        """大会IDを自動生成 (例: COMP_20250911_ABC123)"""
        date_str = datetime.now().strftime("%Y%m%d")
        unique_str = str(uuid.uuid4())[:6].upper()
        return f"COMP_{date_str}_{unique_str}"
    
    def __repr__(self):
        return f"<Competition(id='{self.competition_id}', name='{self.name}', date='{self.date}')>"

class RaceRecord(Base):
    """大会記録テーブル (Swim/Bike/Runのタイム記録)"""
    __tablename__ = "race_records"
    
    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    race_number = Column(String(20), nullable=True)  # ゼッケン番号
    
    # Swim記録
    swim_start_time = Column(DateTime, nullable=True)
    swim_finish_time = Column(DateTime, nullable=True)
    
    # Bike記録
    bike_start_time = Column(DateTime, nullable=True)
    bike_finish_time = Column(DateTime, nullable=True)
    
    # Run記録
    run_start_time = Column(DateTime, nullable=True)
    run_finish_time = Column(DateTime, nullable=True)
    
    # 総合記録
    total_start_time = Column(DateTime, nullable=True)  # 最初の競技開始時刻
    total_finish_time = Column(DateTime, nullable=True)  # 最後の競技終了時刻
    
    # メタデータ
    notes = Column(Text, nullable=True)  # 備考
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # リレーション
    competition = relationship("Competition", back_populates="race_records")
    user = relationship("User")
    
    def calculate_total_times(self):
        """総合記録の自動計算"""
        times = []
        if self.swim_start_time:
            times.append(self.swim_start_time)
        if self.bike_start_time:
            times.append(self.bike_start_time)
        if self.run_start_time:
            times.append(self.run_start_time)
        
        if times:
            self.total_start_time = min(times)
        
        times = []
        if self.swim_finish_time:
            times.append(self.swim_finish_time)
        if self.bike_finish_time:
            times.append(self.bike_finish_time)
        if self.run_finish_time:
            times.append(self.run_finish_time)
        
        if times:
            self.total_finish_time = max(times)
    
    def __repr__(self):
        return f"<RaceRecord(competition='{self.competition_id}', user='{self.user_id}', number='{self.race_number}')>"

class WBGTData(Base):
    """WBGT値（環境測定データ）テーブル"""
    __tablename__ = "wbgt_data"
    
    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    wbgt_value = Column(Float, nullable=False)  # WBGT値
    temperature = Column(Float, nullable=True)  # 気温
    humidity = Column(Float, nullable=True)  # 湿度
    wind_speed = Column(Float, nullable=True)  # 風速
    solar_radiation = Column(Float, nullable=True)  # 日射量
    location = Column(String(100), nullable=True)  # 測定地点
    created_at = Column(DateTime, server_default=func.now())
    
    # リレーション
    competition = relationship("Competition")
    
    def __repr__(self):
        return f"<WBGTData(competition='{self.competition_id}', timestamp='{self.timestamp}', wbgt={self.wbgt_value})>"