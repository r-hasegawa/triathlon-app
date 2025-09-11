"""
app/models/competition.py (修正版)

WBGTDataの定義を削除（flexible_sensor_data.pyで定義されるため）
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
    competition_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    date = Column(Date, nullable=True)
    location = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __init__(self, **kwargs):
        if 'competition_id' not in kwargs:
            kwargs['competition_id'] = self.generate_competition_id()
        super().__init__(**kwargs)
    
    @staticmethod
    def generate_competition_id():
        date_str = datetime.now().strftime("%Y%m%d")
        random_part = str(uuid.uuid4())[:8].upper()
        return f"COMP_{date_str}_{random_part}"

class RaceRecord(Base):
    """大会記録テーブル"""
    __tablename__ = "race_records"
    
    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    race_number = Column(String(50), nullable=True)
    
    # レース時間記録
    swim_start_time = Column(DateTime, nullable=True)
    swim_finish_time = Column(DateTime, nullable=True)
    bike_start_time = Column(DateTime, nullable=True)
    bike_finish_time = Column(DateTime, nullable=True)
    run_start_time = Column(DateTime, nullable=True)
    run_finish_time = Column(DateTime, nullable=True)
    
    # 計算フィールド（プロパティとして後で追加）
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # リレーション（循環インポートを避けるため後で定義）
    # competition = relationship("Competition", back_populates="race_records")
    # user = relationship("User", back_populates="race_records")
    
    @property
    def total_start_time(self):
        """最初の競技スタート時刻"""
        times = [self.swim_start_time, self.bike_start_time, self.run_start_time]
        valid_times = [t for t in times if t is not None]
        return min(valid_times) if valid_times else None
    
    @property
    def total_finish_time(self):
        """最後の競技フィニッシュ時刻"""
        times = [self.swim_finish_time, self.bike_finish_time, self.run_finish_time]
        valid_times = [t for t in times if t is not None]
        return max(valid_times) if valid_times else None

# 🚫 WBGTDataクラスは削除（flexible_sensor_data.pyで定義）
# class WBGTData(Base): ...