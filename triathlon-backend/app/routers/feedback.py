# app/routers/feedback.py - 完全新規作成版

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel

from ..database import get_db
from ..utils.dependencies import get_current_user, get_current_admin
from ..models.user import User, AdminUser
from ..models.competition import Competition, RaceRecord
from ..models.flexible_sensor_data import (
    FlexibleSensorMapping, SkinTemperatureData, 
    CoreTemperatureData, HeartRateData, WBGTData, SensorType
)

router = APIRouter()
logger = logging.getLogger(__name__)

# ===== スキーマ定義 =====

class CompetitionRace(BaseModel):
    id: str
    name: str
    date: str
    description: Optional[str] = None

class SensorDataPoint(BaseModel):
    timestamp: str
    skin_temperature: Optional[float] = None
    core_temperature: Optional[float] = None
    wbgt_temperature: Optional[float] = None
    heart_rate: Optional[int] = None
    sensor_id: Optional[str] = None
    data_type: Optional[str] = None

class RaceRecordSchema(BaseModel):
    competition_id: str
    user_id: str
    swim_start: Optional[str] = None
    swim_finish: Optional[str] = None
    bike_start: Optional[str] = None
    bike_finish: Optional[str] = None
    run_start: Optional[str] = None
    run_finish: Optional[str] = None

class FeedbackDataResponse(BaseModel):
    sensor_data: List[SensorDataPoint]
    race_record: Optional[RaceRecordSchema] = None
    competition: CompetitionRace
    statistics: Optional[Dict[str, Any]] = None

# ===== 一般ユーザー用エンドポイント =====

@router.get("/me/competitions", response_model=List[CompetitionRace])
async def get_user_competitions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """現在のユーザーが参加している大会一覧を取得"""
    try:
        logger.info(f"Getting competitions for user: {current_user.user_id}")
        
        # ユーザーがマッピングを持っている大会を取得
        competitions = db.query(Competition).join(
            FlexibleSensorMapping,
            Competition.competition_id == FlexibleSensorMapping.competition_id
        ).filter(
            FlexibleSensorMapping.user_id == current_user.user_id
        ).distinct().order_by(Competition.date.desc()).all()
        
        logger.info(f"Found {len(competitions)} competitions for user {current_user.user_id}")
        
        result = [
            CompetitionRace(
                id=comp.competition_id,
                name=comp.name,
                date=comp.date.isoformat(),
            )
            for comp in competitions
        ]
        
        logger.info(f"Returning competitions: {[c.id for c in result]}")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching user competitions: {e}")
        raise HTTPException(status_code=500, detail="大会一覧の取得に失敗しました")


@router.get("/me/feedback-data/{competition_id}", response_model=FeedbackDataResponse)
async def get_user_feedback_data(
    competition_id: str,
    offset_minutes: int = Query(10, ge=0, le=60),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """指定された大会のフィードバックデータを取得"""
    try:
        logger.info(f"Getting feedback data for user: {current_user.user_id}, competition: {competition_id}")
        
        # 大会の存在確認
        competition = db.query(Competition).filter(
            Competition.competition_id == competition_id
        ).first()
        
        if not competition:
            logger.error(f"Competition not found: {competition_id}")
            raise HTTPException(status_code=404, detail="指定された大会が見つかりません")
        
        # センサーデータを取得
        sensor_data = get_sensor_data(db, current_user.user_id, competition_id)
        logger.info(f"Retrieved {len(sensor_data)} sensor data points")
        
        # 大会記録を取得
        race_record = get_race_record(db, current_user.user_id, competition_id)
        logger.info(f"Race record found: {race_record is not None}")
        
        return FeedbackDataResponse(
            sensor_data=sensor_data,
            race_record=race_record,
            competition=CompetitionRace(
                id=competition.competition_id,
                name=competition.name,
                date=competition.date.isoformat(),
                description=competition.description
            ),
            statistics={
                "total_records": len(sensor_data),
                "data_types": list(set([data.data_type for data in sensor_data if data.data_type]))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching feedback data: {e}")
        raise HTTPException(status_code=500, detail="フィードバックデータの取得に失敗しました")


@router.get("/me/sensor-data", response_model=List[SensorDataPoint])
async def get_user_sensor_data(
    competition_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ユーザーのセンサーデータを取得"""
    try:
        logger.info(f"Getting sensor data for user: {current_user.user_id}, competition: {competition_id}")
        return get_sensor_data(db, current_user.user_id, competition_id)
    except Exception as e:
        logger.error(f"Error fetching sensor data: {e}")
        raise HTTPException(status_code=500, detail="センサーデータの取得に失敗しました")


# ===== 管理者用エンドポイント =====

@router.get("/admin/users/{user_id}/competitions", response_model=List[CompetitionRace])
async def get_admin_user_competitions(
    user_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """管理者用：指定ユーザーの参加大会一覧を取得"""
    try:
        logger.info(f"Admin getting competitions for user: {user_id}")
        
        competitions = db.query(Competition).join(
            FlexibleSensorMapping,
            Competition.competition_id == FlexibleSensorMapping.competition_id
        ).filter(
            FlexibleSensorMapping.user_id == user_id
        ).distinct().order_by(Competition.date.desc()).all()
        
        return [
            CompetitionRace(
                id=comp.competition_id,
                name=comp.name,
                date=comp.date.isoformat(),
            )
            for comp in competitions
        ]
    except Exception as e:
        logger.error(f"Error fetching admin user competitions: {e}")
        raise HTTPException(status_code=500, detail="大会一覧の取得に失敗しました")


@router.get("/admin/users/{user_id}/feedback-data/{competition_id}", response_model=FeedbackDataResponse)
async def get_admin_user_feedback_data(
    user_id: str,
    competition_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """管理者用：指定ユーザーの大会フィードバックデータを取得"""
    try:
        logger.info(f"Admin getting feedback data for user: {user_id}, competition: {competition_id}")
        
        # ユーザーと大会の存在確認
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="指定されたユーザーが見つかりません")
            
        competition = db.query(Competition).filter(
            Competition.competition_id == competition_id
        ).first()
        if not competition:
            raise HTTPException(status_code=404, detail="指定された大会が見つかりません")
        
        # データ取得
        sensor_data = get_sensor_data(db, user_id, competition_id)
        race_record = get_race_record(db, user_id, competition_id)
        
        return FeedbackDataResponse(
            sensor_data=sensor_data,
            race_record=race_record,
            competition=CompetitionRace(
                id=competition.competition_id,
                name=competition.name,
                date=competition.date.isoformat(),
            ),
            statistics={
                "total_records": len(sensor_data),
                "data_types": list(set([data.data_type for data in sensor_data if data.data_type]))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching admin feedback data: {e}")
        raise HTTPException(status_code=500, detail="フィードバックデータの取得に失敗しました")


# ===== 内部関数 =====

def get_sensor_data(db: Session, user_id: str, competition_id: Optional[str] = None) -> List[SensorDataPoint]:
    """センサーデータを取得して統合形式に変換"""
    try:
        logger.info(f"Getting sensor data for user: {user_id}, competition: {competition_id}")
        
        # ユーザーのマッピングを取得
        mappings_query = db.query(FlexibleSensorMapping).filter(
            FlexibleSensorMapping.user_id == user_id
        )
        if competition_id:
            mappings_query = mappings_query.filter(
                FlexibleSensorMapping.competition_id == competition_id
            )
        
        mappings = mappings_query.all()
        logger.info(f"Found {len(mappings)} mappings for user {user_id}")
        
        if not mappings:
            logger.warning(f"No mappings found for user {user_id}, competition {competition_id}")
            return []
        
        # データをタイムスタンプごとにグループ化
        grouped_data = {}
        
        # 体表温度データ処理
        skin_mappings = [m for m in mappings if m.sensor_type == SensorType.SKIN_TEMPERATURE]
        logger.info(f"Processing {len(skin_mappings)} skin temperature mappings")
        
        for mapping in skin_mappings:
            try:
                logger.info(f"Processing skin temp sensor: {mapping.sensor_id}")
                
                query = db.query(SkinTemperatureData).filter(
                    SkinTemperatureData.halshare_id == mapping.sensor_id
                )
                if competition_id:
                    query = query.filter(SkinTemperatureData.competition_id == competition_id)
                
                skin_data = query.order_by(SkinTemperatureData.datetime).all()
                logger.info(f"Found {len(skin_data)} skin temperature records for sensor {mapping.sensor_id}")
                
                for data in skin_data:
                    timestamp_key = data.datetime.isoformat()
                    if timestamp_key not in grouped_data:
                        grouped_data[timestamp_key] = SensorDataPoint(
                            timestamp=timestamp_key,
                            sensor_id=mapping.sensor_id
                        )
                    grouped_data[timestamp_key].skin_temperature = data.temperature
                    grouped_data[timestamp_key].data_type = "skin_temperature"
                    
            except Exception as e:
                logger.error(f"Error processing skin temp mapping {mapping.sensor_id}: {e}")
        
        # カプセル体温データ処理
        core_mappings = [m for m in mappings if m.sensor_type == SensorType.CORE_TEMPERATURE]
        logger.info(f"Processing {len(core_mappings)} core temperature mappings")
        
        for mapping in core_mappings:
            try:
                logger.info(f"Processing core temp sensor: {mapping.sensor_id}")
                
                query = db.query(CoreTemperatureData).filter(
                    CoreTemperatureData.capsule_id == mapping.sensor_id
                )
                if competition_id:
                    query = query.filter(CoreTemperatureData.competition_id == competition_id)
                
                core_data = query.order_by(CoreTemperatureData.datetime).all()
                logger.info(f"Found {len(core_data)} core temperature records for sensor {mapping.sensor_id}")
                
                for data in core_data:
                    timestamp_key = data.datetime.isoformat()
                    if timestamp_key not in grouped_data:
                        grouped_data[timestamp_key] = SensorDataPoint(
                            timestamp=timestamp_key,
                            sensor_id=mapping.sensor_id
                        )
                    grouped_data[timestamp_key].core_temperature = data.temperature
                    grouped_data[timestamp_key].data_type = "core_temperature"
                    
            except Exception as e:
                logger.error(f"Error processing core temp mapping {mapping.sensor_id}: {e}")
        
        # 心拍データ処理
        hr_mappings = [m for m in mappings if m.sensor_type == SensorType.HEART_RATE]
        logger.info(f"Processing {len(hr_mappings)} heart rate mappings")
        
        for mapping in hr_mappings:
            try:
                logger.info(f"Processing heart rate sensor: {mapping.sensor_id}")
                
                query = db.query(HeartRateData).filter(
                    HeartRateData.sensor_id == mapping.sensor_id
                )
                if competition_id:
                    query = query.filter(HeartRateData.competition_id == competition_id)
                
                hr_data = query.order_by(HeartRateData.time).all()
                logger.info(f"Found {len(hr_data)} heart rate records for sensor {mapping.sensor_id}")
                
                for data in hr_data:
                    timestamp_key = data.time.isoformat()
                    if timestamp_key not in grouped_data:
                        grouped_data[timestamp_key] = SensorDataPoint(
                            timestamp=timestamp_key,
                            sensor_id=mapping.sensor_id
                        )
                    grouped_data[timestamp_key].heart_rate = data.heart_rate
                    grouped_data[timestamp_key].data_type = "heart_rate"
                    
            except Exception as e:
                logger.error(f"Error processing heart rate mapping {mapping.sensor_id}: {e}")
        
        # WBGT データ（大会全体で共有）
        if competition_id:
            try:
                # ⚠️ 修正: WBGTData.datetime を WBGTData.timestamp に変更
                wbgt_data = db.query(WBGTData).filter(
                    WBGTData.competition_id == competition_id
                ).order_by(WBGTData.timestamp).all()  # ← datetime → timestamp
                
                logger.info(f"Found {len(wbgt_data)} WBGT records for competition {competition_id}")
                
                for data in wbgt_data:
                    # ⚠️ 修正: data.datetime を data.timestamp に変更
                    timestamp_key = data.timestamp.isoformat()  # ← datetime → timestamp
                    if timestamp_key not in grouped_data:
                        grouped_data[timestamp_key] = SensorDataPoint(
                            timestamp=timestamp_key,
                            sensor_id="wbgt_sensor"
                        )
                    # ⚠️ 修正: data.temperature を data.wbgt_value に変更
                    grouped_data[timestamp_key].wbgt_temperature = data.wbgt_value  # ← temperature → wbgt_value
                    if not grouped_data[timestamp_key].data_type:
                        grouped_data[timestamp_key].data_type = "wbgt"
                        
            except Exception as e:
                logger.error(f"Error processing WBGT data: {e}")
        
        # ソートして返す
        result = sorted(grouped_data.values(), key=lambda x: x.timestamp)
        logger.info(f"Returning {len(result)} sensor data points")
        
        # デバッグ: 最初の数件をログ出力
        for i, point in enumerate(result[:3]):
            logger.info(f"Sample data {i}: {point.timestamp}, skin: {point.skin_temperature}, core: {point.core_temperature}, hr: {point.heart_rate}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting sensor data: {e}")
        return []


def get_race_record(db: Session, user_id: str, competition_id: str) -> Optional[RaceRecordSchema]:
    """大会記録を取得"""
    try:
        logger.info(f"Getting race record for user: {user_id}, competition: {competition_id}")
        
        # ユーザーのマッピングからゼッケン番号を取得
        mapping = db.query(FlexibleSensorMapping).filter(
            FlexibleSensorMapping.user_id == user_id,
            FlexibleSensorMapping.competition_id == competition_id,
            FlexibleSensorMapping.sensor_type == SensorType.RACE_RECORD
        ).first()
        
        if not mapping:
            logger.warning(f"No race record mapping found for user {user_id} in competition {competition_id}")
            return None
        
        race_number = mapping.sensor_id  # RACE_RECORDタイプの場合、sensor_idがゼッケン番号
        logger.info(f"Found race number: {race_number}")
        
        # 大会記録を取得
        race_record = db.query(RaceRecord).filter(
            RaceRecord.competition_id == competition_id,
            RaceRecord.race_number == race_number
        ).first()
        
        if not race_record:
            logger.warning(f"No race record found for race number {race_number}")
            return None
        
        logger.info(f"Found race record for race number {race_number}")
        
        return RaceRecordSchema(
            competition_id=race_record.competition_id,
            user_id=user_id,
            swim_start=race_record.swim_start_time.isoformat() if race_record.swim_start_time else None,
            swim_finish=race_record.swim_finish_time.isoformat() if race_record.swim_finish_time else None,
            bike_start=race_record.bike_start_time.isoformat() if race_record.bike_start_time else None,
            bike_finish=race_record.bike_finish_time.isoformat() if race_record.bike_finish_time else None,
            run_start=race_record.run_start_time.isoformat() if race_record.run_start_time else None,
            run_finish=race_record.run_finish_time.isoformat() if race_record.run_finish_time else None,
        )
        
    except Exception as e:
        logger.error(f"Error getting race record: {e}")
        return None