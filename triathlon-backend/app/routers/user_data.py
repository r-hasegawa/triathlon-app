# app/routers/user_data.py - 種別カウント対応版

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, distinct
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel

from ..database import get_db
from ..utils.dependencies import get_current_user
from ..models.user import User
from ..models.competition import Competition, RaceRecord
from ..models.flexible_sensor_data import (
    FlexibleSensorMapping, SkinTemperatureData, 
    CoreTemperatureData, HeartRateData, WBGTData, SensorType
)

router = APIRouter(prefix="/me", tags=["ユーザーデータ"])
logger = logging.getLogger(__name__)

# ===== スキーマ定義（種別カウント追加版） =====

class UserDataSummary(BaseModel):
    total_sensor_records: int
    competitions_participated: int
    skin_temperature_count: int = 0
    core_temperature_count: int = 0
    heart_rate_count: int = 0
    mappings_count: int = 0

# ===== メインエンドポイント =====

@router.get("/data-summary", response_model=UserDataSummary)
async def get_user_data_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ユーザーのデータサマリーを取得（種別カウント対応版）
    """
    try:
        logger.info(f"Getting data summary for user: {current_user.user_id}")
        
        # ユーザーのセンサーマッピングを取得
        mappings = db.query(FlexibleSensorMapping).filter(
            FlexibleSensorMapping.user_id == current_user.user_id
        ).all()
        
        logger.info(f"Found {len(mappings)} mappings for user {current_user.user_id}")
        
        # マッピングがない場合
        if not mappings:
            logger.warning(f"No mappings found for user {current_user.user_id}")
            return UserDataSummary(
                total_sensor_records=0,
                competitions_participated=0,
                skin_temperature_count=0,
                core_temperature_count=0,
                heart_rate_count=0,
                mappings_count=0
            )
        
        # データ統計を収集
        total_records = 0
        skin_temp_count = 0
        core_temp_count = 0
        heart_rate_count = 0
        
        # 参加大会数
        competitions_participated = len(set(m.competition_id for m in mappings))
        logger.info(f"User participated in {competitions_participated} competitions")
        
        # 体表温度データ
        skin_mappings = [m for m in mappings if m.sensor_type == SensorType.SKIN_TEMPERATURE]
        logger.info(f"Processing {len(skin_mappings)} skin temperature mappings")
        
        for mapping in skin_mappings:
            try:
                skin_data = db.query(SkinTemperatureData).filter(
                    SkinTemperatureData.halshare_id == mapping.sensor_id
                ).all()
                
                count = len(skin_data)
                skin_temp_count += count
                total_records += count
                
                logger.info(f"Skin temp sensor {mapping.sensor_id}: {count} records")
                
            except Exception as e:
                logger.error(f"Error processing skin temp mapping {mapping.sensor_id}: {e}")
        
        # カプセル体温データ
        core_mappings = [m for m in mappings if m.sensor_type == SensorType.CORE_TEMPERATURE]
        logger.info(f"Processing {len(core_mappings)} core temperature mappings")
        
        for mapping in core_mappings:
            try:
                core_data = db.query(CoreTemperatureData).filter(
                    CoreTemperatureData.capsule_id == mapping.sensor_id
                ).all()
                
                count = len(core_data)
                core_temp_count += count
                total_records += count
                
                logger.info(f"Core temp sensor {mapping.sensor_id}: {count} records")
                
            except Exception as e:
                logger.error(f"Error processing core temp mapping {mapping.sensor_id}: {e}")
        
        # 心拍データ
        hr_mappings = [m for m in mappings if m.sensor_type == SensorType.HEART_RATE]
        logger.info(f"Processing {len(hr_mappings)} heart rate mappings")
        
        for mapping in hr_mappings:
            try:
                hr_data = db.query(HeartRateData).filter(
                    HeartRateData.sensor_id == mapping.sensor_id
                ).all()
                
                count = len(hr_data)
                heart_rate_count += count
                total_records += count
                
                logger.info(f"Heart rate sensor {mapping.sensor_id}: {count} records")
                
            except Exception as e:
                logger.error(f"Error processing heart rate mapping {mapping.sensor_id}: {e}")
        
        logger.info(f"Final counts - Total: {total_records}, Skin: {skin_temp_count}, Core: {core_temp_count}, HR: {heart_rate_count}")
        
        result = UserDataSummary(
            total_sensor_records=total_records,
            competitions_participated=competitions_participated,
            skin_temperature_count=skin_temp_count,
            core_temperature_count=core_temp_count,
            heart_rate_count=heart_rate_count,
            mappings_count=len(mappings)
        )
        
        logger.info(f"Returning summary: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching user data summary: {e}")
        logger.error(f"Error details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"データサマリーの取得に失敗しました: {str(e)}")

# ===== 他のエンドポイントは既存のまま =====

@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ユーザーのセンサー統計を取得
    """
    try:
        mappings = db.query(FlexibleSensorMapping).filter(
            FlexibleSensorMapping.user_id == current_user.user_id
        ).all()
        
        if not mappings:
            return {
                "total_records": 0,
                "avg_temperature": None,
                "max_temperature": None,
                "min_temperature": None,
                "latest_record_date": None,
                "earliest_record_date": None
            }
        
        total_records = 0
        temperature_values = []
        all_timestamps = []
        
        # 体表温度データ統計
        skin_mappings = [m for m in mappings if m.sensor_type == SensorType.SKIN_TEMPERATURE]
        for mapping in skin_mappings:
            skin_data = db.query(SkinTemperatureData.temperature, SkinTemperatureData.datetime).filter(
                SkinTemperatureData.halshare_id == mapping.sensor_id,
                SkinTemperatureData.temperature.isnot(None)
            ).all()
            
            total_records += len(skin_data)
            temperature_values.extend([d.temperature for d in skin_data])
            all_timestamps.extend([d.datetime for d in skin_data])
        
        # カプセル体温データ統計
        core_mappings = [m for m in mappings if m.sensor_type == SensorType.CORE_TEMPERATURE]
        for mapping in core_mappings:
            core_data = db.query(CoreTemperatureData.temperature, CoreTemperatureData.datetime).filter(
                CoreTemperatureData.capsule_id == mapping.sensor_id,
                CoreTemperatureData.temperature.isnot(None)
            ).all()
            
            total_records += len(core_data)
            temperature_values.extend([d.temperature for d in core_data])
            all_timestamps.extend([d.datetime for d in core_data])
        
        # 統計計算
        avg_temp = sum(temperature_values) / len(temperature_values) if temperature_values else None
        max_temp = max(temperature_values) if temperature_values else None
        min_temp = min(temperature_values) if temperature_values else None
        latest_date = max(all_timestamps).isoformat() if all_timestamps else None
        earliest_date = min(all_timestamps).isoformat() if all_timestamps else None
        
        return {
            "total_records": total_records,
            "avg_temperature": avg_temp,
            "max_temperature": max_temp,
            "min_temperature": min_temp,
            "latest_record_date": latest_date,
            "earliest_record_date": earliest_date
        }
        
    except Exception as e:
        logger.error(f"Error fetching user stats: {e}")
        raise HTTPException(status_code=500, detail="統計データの取得に失敗しました")

@router.get("/sensor-mappings")
async def get_user_sensor_mappings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ユーザーのセンサーマッピング一覧を取得
    """
    try:
        mappings = db.query(FlexibleSensorMapping).filter(
            FlexibleSensorMapping.user_id == current_user.user_id
        ).all()
        
        result = []
        for mapping in mappings:
            # 各マッピングのレコード数を取得
            record_count = 0
            if mapping.sensor_type == SensorType.SKIN_TEMPERATURE:
                record_count = db.query(func.count(SkinTemperatureData.id)).filter(
                    SkinTemperatureData.halshare_id == mapping.sensor_id
                ).scalar() or 0
            elif mapping.sensor_type == SensorType.CORE_TEMPERATURE:
                record_count = db.query(func.count(CoreTemperatureData.id)).filter(
                    CoreTemperatureData.capsule_id == mapping.sensor_id
                ).scalar() or 0
            elif mapping.sensor_type == SensorType.HEART_RATE:
                record_count = db.query(func.count(HeartRateData.id)).filter(
                    HeartRateData.sensor_id == mapping.sensor_id
                ).scalar() or 0
            
            result.append({
                "sensor_id": mapping.sensor_id,
                "sensor_type": mapping.sensor_type.value,
                "competition_id": mapping.competition_id,
                "record_count": record_count,
                "subject_name": mapping.subject_name,
                "notes": mapping.notes
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching sensor mappings: {e}")
        raise HTTPException(status_code=500, detail="センサーマッピングの取得に失敗しました")