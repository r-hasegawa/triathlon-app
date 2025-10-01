"""
app/models/competition.py (大会記録機能対応版)

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
    # description = Column(Text, nullable=True)
    # created_at = Column(DateTime, server_default=func.now())
    
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
    """大会記録テーブル（不要列削除、upload_batch_id追加）"""
    __tablename__ = "race_records"
    
    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False, index=True)
    
    # 🆕 ゼッケン番号（複数CSV統合のキー）
    race_number = Column(String(50), nullable=True, index=True)
    
    # レース時間記録
    swim_start_time = Column(DateTime, nullable=True)
    swim_finish_time = Column(DateTime, nullable=True)
    bike_start_time = Column(DateTime, nullable=True)
    bike_finish_time = Column(DateTime, nullable=True)
    run_start_time = Column(DateTime, nullable=True)
    run_finish_time = Column(DateTime, nullable=True)
    
    # 🆕 可変LAP対応（JSON形式で保存）
    lap_data = Column(Text, nullable=True)  # {"BL1": "2025-06-15 09:30:00", "BL2": "2025-06-15 10:15:00", ...}
    
    # 🆕 アップロードバッチID（削除管理用）
    upload_batch_id = Column(String(200), nullable=True, index=True)
    
    # リレーション（一方向のみ）
    competition = relationship("Competition")
    
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
    
    @property
    def parsed_lap_data(self):
        """LAP データの JSON 解析"""
        if not self.lap_data:
            return {}
        try:
            import json
            return json.loads(self.lap_data)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_lap_data(self, lap_dict: dict):
        """LAP データを JSON 形式で保存"""
        if lap_dict:
            import json
            # datetimeオブジェクトを文字列に変換
            serializable_dict = {}
            for key, value in lap_dict.items():
                if hasattr(value, 'isoformat'):
                    serializable_dict[key] = value.isoformat()
                else:
                    serializable_dict[key] = str(value) if value is not None else None
            self.lap_data = json.dumps(serializable_dict)
        else:
            self.lap_data = None
    
    def get_swim_duration_seconds(self):
        """SWIM区間の秒数"""
        if self.swim_start_time and self.swim_finish_time:
            return (self.swim_finish_time - self.swim_start_time).total_seconds()
        return None
    
    def get_bike_duration_seconds(self):
        """BIKE区間の秒数"""
        if self.bike_start_time and self.bike_finish_time:
            return (self.bike_finish_time - self.bike_start_time).total_seconds()
        return None
    
    def get_run_duration_seconds(self):
        """RUN区間の秒数"""
        if self.run_start_time and self.run_finish_time:
            return (self.run_finish_time - self.run_start_time).total_seconds()
        return None
    
    def get_total_duration_seconds(self):
        """総競技時間の秒数"""
        if self.total_start_time and self.total_finish_time:
            return (self.total_finish_time - self.total_start_time).total_seconds()
        return None
    
    def __repr__(self):
        return f"<RaceRecord(race_number='{self.race_number}', competition='{self.competition_id}')>"