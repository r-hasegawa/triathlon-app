from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.sensor_data import SensorData

class SensorRepositoryInterface(ABC):
    """センサーデータリポジトリインターフェース"""
    
    @abstractmethod
    def get_sensor_data_by_user(self, user_id: str, limit: int = 100) -> List[SensorData]:
        pass
    
    @abstractmethod
    def get_sensor_data_stats(self, user_id: str, sensor_id: Optional[str] = None):
        pass
    
    @abstractmethod
    def create_sensor_data_batch(self, sensor_data_list: List[SensorData]) -> int:
        pass

class SQLiteSensorRepository(SensorRepositoryInterface):
    """SQLite用センサーデータリポジトリ実装"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_sensor_data_by_user(self, user_id: str, limit: int = 100) -> List[SensorData]:
        return self.db.query(SensorData)\
                     .filter_by(user_id=user_id)\
                     .order_by(SensorData.timestamp.desc())\
                     .limit(limit)\
                     .all()
    
    def get_sensor_data_stats(self, user_id: str, sensor_id: Optional[str] = None):
        from sqlalchemy import func
        
        query = self.db.query(SensorData).filter_by(user_id=user_id)
        
        if sensor_id:
            query = query.filter_by(sensor_id=sensor_id)
        
        stats = query.with_entities(
            func.count(SensorData.id).label('total_records'),
            func.min(SensorData.temperature).label('min_temperature'),
            func.max(SensorData.temperature).label('max_temperature'),
            func.avg(SensorData.temperature).label('avg_temperature'),
            func.min(SensorData.timestamp).label('start_time'),
            func.max(SensorData.timestamp).label('end_time')
        ).first()
        
        return stats
    
    def create_sensor_data_batch(self, sensor_data_list: List[SensorData]) -> int:
        self.db.bulk_save_objects(sensor_data_list)
        self.db.commit()
        return len(sensor_data_list)