"""
高度なエクスポート機能のためのサービスクラス
"""

import pandas as pd
import json
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from io import StringIO, BytesIO
import pytz
from app.models.sensor_data import SensorData

class ExportService:
    """データエクスポートサービス"""
    
    @staticmethod
    def prepare_data_for_export(
        data: List[SensorData], 
        timezone: str = "Asia/Tokyo",
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """エクスポート用データの準備"""
        target_tz = pytz.timezone(timezone)
        
        prepared_data = []
        for item in data:
            # タイムゾーン変換
            utc_time = item.timestamp.replace(tzinfo=pytz.UTC)
            local_time = utc_time.astimezone(target_tz)
            
            record = {
                'timestamp': item.timestamp.isoformat(),
                'local_timestamp': local_time.isoformat(),
                'sensor_id': item.sensor_id,
                'temperature': item.temperature,
                'local_time_formatted': local_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            }
            
            if include_metadata:
                record.update({
                    'id': item.id,
                    'user_id': item.user_id,
                    'created_at': item.created_at.isoformat() if item.created_at else None,
                    'data_source': item.data_source,
                    'raw_data': item.raw_data
                })
            
            prepared_data.append(record)
        
        return prepared_data
    
    @staticmethod
    def calculate_statistics(data: List[SensorData]) -> Dict[str, Any]:
        """データ統計の計算"""
        if not data:
            return {
                'count': 0,
                'min_temperature': None,
                'max_temperature': None,
                'avg_temperature': None,
                'start_time': None,
                'end_time': None
            }
        
        temperatures = [item.temperature for item in data]
        timestamps = [item.timestamp for item in data]
        
        return {
            'count': len(data),
            'min_temperature': min(temperatures),
            'max_temperature': max(temperatures),
            'avg_temperature': sum(temperatures) / len(temperatures),
            'start_time': min(timestamps).isoformat(),
            'end_time': max(timestamps).isoformat(),
            'temperature_std': pd.Series(temperatures).std()
        }
    
    @staticmethod
    def generate_metadata(
        user_info: Dict[str, Any],
        filters: Dict[str, Any],
        statistics: Dict[str, Any],
        export_format: str,
        timezone: str
    ) -> Dict[str, Any]:
        """メタデータ生成"""
        target_tz = pytz.timezone(timezone)
        export_time = datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(target_tz)
        
        return {
            'export_info': {
                'exported_at': export_time.isoformat(),
                'exported_by': user_info.get('username'),
                'user_id': user_info.get('user_id'),
                'format': export_format,
                'timezone': timezone,
                'version': '2.0'
            },
            'filters_applied': filters,
            'statistics': statistics,
            'system_info': {
                'application': 'Triathlon Sensor Data System',
                'export_engine': 'Enhanced Export Service v2.0'
            }
        }