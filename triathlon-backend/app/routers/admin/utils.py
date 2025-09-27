"""
app/routers/admin/utils.py
管理者機能で使用する共通ユーティリティ関数
"""

import secrets
import string
import chardet
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.flexible_sensor_data import (
    FlexibleSensorMapping, SkinTemperatureData, 
    CoreTemperatureData, HeartRateData
)


def generate_batch_id(filename: str) -> str:
    """バッチIDを生成"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{filename}"


def detect_encoding(content: bytes) -> str:
    """ファイルのエンコーディングを自動検出"""
    result = chardet.detect(content)
    encoding = result['encoding']
    
    if encoding in ['cp1252', 'ISO-8859-1']:
        return 'cp1252'
    elif encoding in ['shift_jis', 'shift-jis']:
        return 'shift_jis'
    elif encoding is None or encoding == 'ascii':
        return 'utf-8'
    
    return encoding


def generate_user_id() -> str:
    """ユニークなユーザーIDを生成"""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_suffix = ''.join(secrets.choice(string.digits) for _ in range(4))
    return f"user_{timestamp}_{random_suffix}"


def generate_password() -> str:
    """安全なパスワードを生成（8文字、英数字混合）"""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(8))


"""
app/routers/admin/utils.py
管理者機能で使用する共通ユーティリティ関数（スキーマ修正版）
"""

import secrets
import string
import chardet
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.flexible_sensor_data import (
    FlexibleSensorMapping, SkinTemperatureData, 
    CoreTemperatureData, HeartRateData, SensorType
)


def generate_batch_id(filename: str) -> str:
    """バッチIDを生成"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{filename}"


def detect_encoding(content: bytes) -> str:
    """ファイルのエンコーディングを自動検出"""
    result = chardet.detect(content)
    encoding = result['encoding']
    
    if encoding in ['cp1252', 'ISO-8859-1']:
        return 'cp1252'
    elif encoding in ['shift_jis', 'shift-jis']:
        return 'shift_jis'
    elif encoding is None or encoding == 'ascii':
        return 'utf-8'
    
    return encoding


def generate_user_id() -> str:
    """ユニークなユーザーIDを生成"""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_suffix = ''.join(secrets.choice(string.digits) for _ in range(4))
    return f"user_{timestamp}_{random_suffix}"


def generate_password() -> str:
    """安全なパスワードを生成（8文字、英数字混合）"""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(8))


def get_user_sensor_data_count(db: Session, user_id: str, sensor_type: str) -> int:
    """ユーザーのセンサーデータ数を取得（実際のスキーマに基づく修正版）"""
    try:
        if sensor_type == "skin_temperature":
            # 体表温データ: halshare_id経由でマッピング
            mappings = db.query(FlexibleSensorMapping).filter(
                FlexibleSensorMapping.user_id == user_id,
                FlexibleSensorMapping.sensor_type == SensorType.SKIN_TEMPERATURE
            ).all()
            
            total_count = 0
            for mapping in mappings:
                count = db.query(func.count(SkinTemperatureData.id))\
                    .filter(SkinTemperatureData.halshare_id == mapping.sensor_id)\
                    .scalar() or 0
                total_count += count
            
            return total_count
                
        elif sensor_type == "core_temperature":
            # カプセル体温データ: capsule_id経由でマッピング
            mappings = db.query(FlexibleSensorMapping).filter(
                FlexibleSensorMapping.user_id == user_id,
                FlexibleSensorMapping.sensor_type == SensorType.CORE_TEMPERATURE
            ).all()
            
            total_count = 0
            for mapping in mappings:
                count = db.query(func.count(CoreTemperatureData.id))\
                    .filter(CoreTemperatureData.capsule_id == mapping.sensor_id)\
                    .scalar() or 0
                total_count += count
            
            return total_count
                
        elif sensor_type == "heart_rate":
            # 心拍データ: sensor_id経由でマッピング
            mappings = db.query(FlexibleSensorMapping).filter(
                FlexibleSensorMapping.user_id == user_id,
                FlexibleSensorMapping.sensor_type == SensorType.HEART_RATE
            ).all()
            
            total_count = 0
            for mapping in mappings:
                count = db.query(func.count(HeartRateData.id))\
                    .filter(HeartRateData.sensor_id == mapping.sensor_id)\
                    .scalar() or 0
                total_count += count
            
            return total_count
                
        return 0
        
    except Exception as e:
        print(f"❌ get_user_sensor_data_count error for {sensor_type}: {e}")
        return 0