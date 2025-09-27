# app/routers/user_data.py - /me/data-summary エンドポイント追加版

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.competition import Competition, RaceRecord
from app.models.flexible_sensor_data import (
    FlexibleSensorMapping, SkinTemperatureData, 
    CoreTemperatureData, HeartRateData, SensorType
)
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/me", tags=["ユーザーデータ"])


def get_user_sensor_data_count_for_me(db: Session, user_id: str, sensor_type: str) -> int:
    """一般ユーザー向けのセンサーデータ数取得関数"""
    try:
        if sensor_type == "skin_temperature":
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
        print(f"❌ get_user_sensor_data_count_for_me error for {sensor_type}: {e}")
        return 0


@router.get("/data-summary")
async def get_my_data_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """一般ユーザーの自分のデータサマリー取得"""
    try:
        # センサーデータ統計を取得
        sensor_data = {
            "skin_temperature": get_user_sensor_data_count_for_me(db, current_user.user_id, "skin_temperature"),
            "core_temperature": get_user_sensor_data_count_for_me(db, current_user.user_id, "core_temperature"),
            "heart_rate": get_user_sensor_data_count_for_me(db, current_user.user_id, "heart_rate")
        }
        
        # マッピング情報
        mappings = db.query(FlexibleSensorMapping).filter_by(user_id=current_user.user_id).all()
        
        # 大会参加情報
        race_records = db.query(RaceRecord).filter_by(user_id=current_user.user_id).all()
        
        # 参加大会の詳細情報を取得
        competitions_data = []
        for record in race_records:
            competition = db.query(Competition).filter_by(
                competition_id=record.competition_id
            ).first()
            
            if competition:
                competitions_data.append({
                    "competition_id": competition.competition_id,
                    "name": competition.name,
                    "date": competition.date.isoformat() if competition.date else None,
                    "bib_number": getattr(record, 'race_number', None) or getattr(record, 'bib_number', None)
                })
        
        return {
            "user_info": {
                "user_id": current_user.user_id,
                "full_name": current_user.full_name,
                "email": current_user.email
            },
            "sensor_data_summary": sensor_data,
            "total_sensor_records": sum(sensor_data.values()),
            "mappings_count": len(mappings),
            "competitions_participated": len(race_records),
            "competitions": competitions_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"データサマリー取得エラー: {str(e)}"
        )


@router.get("/sensor-data")
async def get_my_sensor_data(
    competition_id: Optional[str] = None,
    sensor_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """一般ユーザーの自分のセンサーデータ詳細取得（今後の拡張用）"""
    try:
        # マッピング情報を取得
        query = db.query(FlexibleSensorMapping).filter_by(user_id=current_user.user_id)
        
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        
        if sensor_type:
            try:
                sensor_type_enum = SensorType(sensor_type)
                query = query.filter_by(sensor_type=sensor_type_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"無効なセンサータイプ: {sensor_type}"
                )
        
        mappings = query.all()
        
        sensor_data_summary = []
        for mapping in mappings:
            mapping_info = {
                "mapping_id": mapping.id,
                "sensor_id": mapping.sensor_id,
                "sensor_type": mapping.sensor_type.value,
                "competition_id": mapping.competition_id,
                "subject_name": mapping.subject_name,
                "device_type": mapping.device_type,
                "created_at": mapping.created_at.isoformat() if mapping.created_at else None
            }
            
            # 各センサータイプのデータ数を取得
            if mapping.sensor_type == SensorType.SKIN_TEMPERATURE:
                data_count = db.query(func.count(SkinTemperatureData.id))\
                    .filter(SkinTemperatureData.halshare_id == mapping.sensor_id)\
                    .scalar() or 0
            elif mapping.sensor_type == SensorType.CORE_TEMPERATURE:
                data_count = db.query(func.count(CoreTemperatureData.id))\
                    .filter(CoreTemperatureData.capsule_id == mapping.sensor_id)\
                    .scalar() or 0
            elif mapping.sensor_type == SensorType.HEART_RATE:
                data_count = db.query(func.count(HeartRateData.id))\
                    .filter(HeartRateData.sensor_id == mapping.sensor_id)\
                    .scalar() or 0
            else:
                data_count = 0
            
            mapping_info["data_count"] = data_count
            sensor_data_summary.append(mapping_info)
        
        return {
            "user_id": current_user.user_id,
            "sensor_mappings": sensor_data_summary,
            "total_mappings": len(mappings),
            "filters": {
                "competition_id": competition_id,
                "sensor_type": sensor_type
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"センサーデータ取得エラー: {str(e)}"
        )


@router.get("/competitions")
async def get_my_competitions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """一般ユーザーの参加大会一覧取得"""
    try:
        # 大会参加記録を取得
        race_records = db.query(RaceRecord).filter_by(user_id=current_user.user_id).all()
        
        competitions_data = []
        for record in race_records:
            competition = db.query(Competition).filter_by(
                competition_id=record.competition_id
            ).first()
            
            if competition:
                # センサーマッピング数を取得
                mapping_count = db.query(FlexibleSensorMapping).filter_by(
                    user_id=current_user.user_id,
                    competition_id=competition.competition_id
                ).count()
                
                competitions_data.append({
                    "competition_id": competition.competition_id,
                    "name": competition.name,
                    "date": competition.date.isoformat() if competition.date else None,
                    "location": competition.location,
                    "description": competition.description,
                    "bib_number": getattr(record, 'race_number', None) or getattr(record, 'bib_number', None),
                    "mapping_count": mapping_count,
                    "created_at": competition.created_at.isoformat() if competition.created_at else None
                })
        
        return {
            "user_id": current_user.user_id,
            "competitions": competitions_data,
            "total_competitions": len(competitions_data)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"参加大会一覧取得エラー: {str(e)}"
        )