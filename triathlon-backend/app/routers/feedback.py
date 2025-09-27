# app/routers/feedback.py

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

# ===== スキーマ定義（直接定義） =====

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

class LapRecord(BaseModel):
    lap_number: int
    lap_time: str
    split_time: Optional[str] = None
    segment_type: Optional[str] = None

class RaceRecordSchema(BaseModel):
    competition_id: str
    user_id: str
    swim_start: Optional[str] = None
    swim_finish: Optional[str] = None
    bike_start: Optional[str] = None
    bike_finish: Optional[str] = None
    run_start: Optional[str] = None
    run_finish: Optional[str] = None
    lap_records: Optional[List[LapRecord]] = None

class FeedbackStatistics(BaseModel):
    total_records: int
    date_range: Dict[str, str]
    data_types: List[str]

class FeedbackDataResponse(BaseModel):
    sensor_data: List[SensorDataPoint]
    race_record: Optional[RaceRecordSchema] = None
    competition: CompetitionRace
    statistics: Optional[FeedbackStatistics] = None

# ===== 一般ユーザー用エンドポイント =====

@router.get("/me/competitions", response_model=List[CompetitionRace])
async def get_user_competitions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    現在のユーザーが参加している大会一覧を取得
    """
    try:
        # ユーザーがセンサーマッピングを持っている大会を取得
        competitions = db.query(Competition).join(
            FlexibleSensorMapping,
            Competition.competition_id == FlexibleSensorMapping.competition_id
        ).filter(
            FlexibleSensorMapping.user_id == current_user.user_id
        ).distinct().order_by(Competition.created_at.desc()).all()
        
        return [
            CompetitionRace(
                id=comp.competition_id,
                name=comp.name,
                date=comp.created_at.isoformat(),
                description=comp.description
            )
            for comp in competitions
        ]
    except Exception as e:
        logger.error(f"Error fetching user competitions: {e}")
        raise HTTPException(status_code=500, detail="大会一覧の取得に失敗しました")


@router.get("/me/feedback-data/{competition_id}", response_model=FeedbackDataResponse)
async def get_user_feedback_data(
    competition_id: str,
    offset_minutes: int = Query(10, ge=0, le=60, description="前後のオフセット時間（分）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    指定された大会のフィードバックデータを取得
    """
    try:
        # 大会の存在確認
        competition = db.query(Competition).filter(
            Competition.competition_id == competition_id
        ).first()
        
        if not competition:
            raise HTTPException(status_code=404, detail="指定された大会が見つかりません")
        
        # センサーデータを取得
        sensor_data = await _get_sensor_data(
            db, current_user.user_id, competition_id
        )
        
        # 大会記録を取得
        race_record = await _get_race_record(
            db, current_user.user_id, competition_id
        )
        
        # 時間範囲を計算
        time_range = _calculate_time_range(race_record, offset_minutes)
        
        # 時間範囲でフィルタリング
        if time_range and sensor_data:
            filtered_data = [
                data for data in sensor_data
                if time_range['start'] <= datetime.fromisoformat(data.timestamp.replace('Z', '+00:00')) <= time_range['end']
            ]
        else:
            filtered_data = sensor_data
        
        return FeedbackDataResponse(
            sensor_data=filtered_data,
            race_record=race_record,
            competition=CompetitionRace(
                id=competition.competition_id,
                name=competition.name,
                date=competition.created_at.isoformat(),
                description=competition.description
            ),
            statistics={
                "total_records": len(filtered_data),
                "date_range": {
                    "start": time_range['start'].isoformat() if time_range else "",
                    "end": time_range['end'].isoformat() if time_range else ""
                },
                "data_types": list(set([data.data_type for data in filtered_data if data.data_type]))
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
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    data_types: Optional[List[str]] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ユーザーのセンサーデータを取得
    """
    try:
        # ユーザーのマッピングを取得
        mappings_query = db.query(FlexibleSensorMapping).filter(
            FlexibleSensorMapping.user_id == current_user.user_id
        )
        
        if competition_id:
            mappings_query = mappings_query.filter(FlexibleSensorMapping.competition_id == competition_id)
        
        if data_types:
            sensor_types = [SensorType(dt) for dt in data_types if dt in [e.value for e in SensorType]]
            mappings_query = mappings_query.filter(FlexibleSensorMapping.sensor_type.in_(sensor_types))
        
        mappings = mappings_query.all()
        
        # 日時フィルター設定
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # データをタイムスタンプごとにグループ化
        grouped_data = {}
        
        for mapping in mappings:
            if mapping.sensor_type == SensorType.SKIN_TEMPERATURE:
                query = db.query(SkinTemperatureData).filter(
                    SkinTemperatureData.halshare_id == mapping.sensor_id
                )
                if competition_id:
                    query = query.filter(SkinTemperatureData.competition_id == competition_id)
                if start_dt:
                    query = query.filter(SkinTemperatureData.datetime >= start_dt)
                if end_dt:
                    query = query.filter(SkinTemperatureData.datetime <= end_dt)
                
                skin_data = query.order_by(SkinTemperatureData.datetime).all()
                
                for data in skin_data:
                    timestamp_key = data.datetime.isoformat()
                    if timestamp_key not in grouped_data:
                        grouped_data[timestamp_key] = SensorDataPoint(timestamp=timestamp_key)
                    grouped_data[timestamp_key].skin_temperature = data.temperature
                    grouped_data[timestamp_key].sensor_id = data.halshare_id
                    grouped_data[timestamp_key].data_type = "skin_temperature"
            
            elif mapping.sensor_type == SensorType.CORE_TEMPERATURE:
                query = db.query(CoreTemperatureData).filter(
                    CoreTemperatureData.capsule_id == mapping.sensor_id
                )
                if competition_id:
                    query = query.filter(CoreTemperatureData.competition_id == competition_id)
                if start_dt:
                    query = query.filter(CoreTemperatureData.datetime >= start_dt)
                if end_dt:
                    query = query.filter(CoreTemperatureData.datetime <= end_dt)
                
                core_data = query.order_by(CoreTemperatureData.datetime).all()
                
                for data in core_data:
                    timestamp_key = data.datetime.isoformat()
                    if timestamp_key not in grouped_data:
                        grouped_data[timestamp_key] = SensorDataPoint(timestamp=timestamp_key)
                    grouped_data[timestamp_key].core_temperature = data.temperature
                    grouped_data[timestamp_key].sensor_id = data.capsule_id
                    grouped_data[timestamp_key].data_type = "core_temperature"
            
            elif mapping.sensor_type == SensorType.HEART_RATE:
                query = db.query(HeartRateData).filter(
                    HeartRateData.sensor_id == mapping.sensor_id
                )
                if competition_id:
                    query = query.filter(HeartRateData.competition_id == competition_id)
                if start_dt:
                    query = query.filter(HeartRateData.time >= start_dt)
                if end_dt:
                    query = query.filter(HeartRateData.time <= end_dt)
                
                hr_data = query.order_by(HeartRateData.time).all()
                
                for data in hr_data:
                    timestamp_key = data.time.isoformat()
                    if timestamp_key not in grouped_data:
                        grouped_data[timestamp_key] = SensorDataPoint(timestamp=timestamp_key)
                    grouped_data[timestamp_key].heart_rate = data.heart_rate
                    grouped_data[timestamp_key].sensor_id = data.sensor_id
                    grouped_data[timestamp_key].data_type = "heart_rate"
        
        # WBGTデータを追加（競技環境データ）
        if competition_id:
            wbgt_query = db.query(WBGTData).filter(
                WBGTData.competition_id == competition_id
            )
            if start_dt:
                wbgt_query = wbgt_query.filter(WBGTData.datetime >= start_dt)
            if end_dt:
                wbgt_query = wbgt_query.filter(WBGTData.datetime <= end_dt)
            
            wbgt_data = wbgt_query.order_by(WBGTData.datetime).all()
            
            for data in wbgt_data:
                timestamp_key = data.datetime.isoformat()
                if timestamp_key not in grouped_data:
                    grouped_data[timestamp_key] = SensorDataPoint(timestamp=timestamp_key)
                grouped_data[timestamp_key].wbgt_temperature = data.wbgt_value
                grouped_data[timestamp_key].sensor_id = "WBGT_ENV"
                grouped_data[timestamp_key].data_type = "wbgt"
        
        return list(grouped_data.values())
        
    except Exception as e:
        logger.error(f"Error fetching sensor data: {e}")
        raise HTTPException(status_code=500, detail="センサーデータの取得に失敗しました")


@router.get("/me/race-records/{competition_id}", response_model=Optional[RaceRecordSchema])
async def get_user_race_record(
    competition_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ユーザーの指定大会の競技記録を取得
    """
    try:
        race_record = await _get_race_record(db, current_user.user_id, competition_id)
        return race_record
    except Exception as e:
        logger.error(f"Error fetching race record: {e}")
        raise HTTPException(status_code=500, detail="競技記録の取得に失敗しました")


# ===== 管理者用エンドポイント =====

@router.get("/admin/users/{user_id}/competitions", response_model=List[CompetitionRace])
async def get_admin_user_competitions(
    user_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    管理者用：指定ユーザーの参加大会一覧を取得
    """
    try:
        # ユーザーの存在確認
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="指定されたユーザーが見つかりません")
        
        # ユーザーがセンサーマッピングを持っている大会を取得
        competitions = db.query(Competition).join(
            FlexibleSensorMapping,
            Competition.competition_id == FlexibleSensorMapping.competition_id
        ).filter(
            FlexibleSensorMapping.user_id == user_id
        ).distinct().order_by(Competition.created_at.desc()).all()
        
        return [
            CompetitionRace(
                id=comp.competition_id,
                name=comp.name,
                date=comp.created_at.isoformat(),
                description=comp.description
            )
            for comp in competitions
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching admin user competitions: {e}")
        raise HTTPException(status_code=500, detail="ユーザー大会一覧の取得に失敗しました")


@router.get("/admin/users/{user_id}/feedback-data/{competition_id}", response_model=FeedbackDataResponse)
async def get_admin_user_feedback_data(
    user_id: str,
    competition_id: str,
    offset_minutes: int = Query(10, ge=0, le=60),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    管理者用：指定ユーザーの指定大会のフィードバックデータを取得
    """
    try:
        # ユーザーと大会の存在確認
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="指定されたユーザーが見つかりません")
        
        competition = db.query(Competition).filter(
            Competition.competition_id == competition_id
        ).first()
        if not competition:
            raise HTTPException(status_code=404, detail="指定された大会が見つかりません")
        
        # センサーデータを取得
        sensor_data = await _get_sensor_data(db, user_id, competition_id)
        
        # 大会記録を取得
        race_record = await _get_race_record(db, user_id, competition_id)
        
        # 時間範囲を計算
        time_range = _calculate_time_range(race_record, offset_minutes)
        
        # 時間範囲でフィルタリング
        if time_range and sensor_data:
            filtered_data = [
                data for data in sensor_data
                if time_range['start'] <= datetime.fromisoformat(data.timestamp.replace('Z', '+00:00')) <= time_range['end']
            ]
        else:
            filtered_data = sensor_data
        
        return FeedbackDataResponse(
            sensor_data=filtered_data,
            race_record=race_record,
            competition=CompetitionRace(
                id=competition.competition_id,
                name=competition.name,
                date=competition.created_at.isoformat(),
                description=competition.description
            ),
            statistics={
                "total_records": len(filtered_data),
                "date_range": {
                    "start": time_range['start'].isoformat() if time_range else "",
                    "end": time_range['end'].isoformat() if time_range else ""
                },
                "data_types": list(set([data.data_type for data in filtered_data if data.data_type]))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching admin feedback data: {e}")
        raise HTTPException(status_code=500, detail="フィードバックデータの取得に失敗しました")


# ===== 内部関数 =====

async def _get_sensor_data(db: Session, user_id: str, competition_id: str) -> List[SensorDataPoint]:
    """センサーデータを取得して統合形式に変換"""
    try:
        # ユーザーのセンサーマッピングを取得
        mappings = db.query(FlexibleSensorMapping).filter(
            FlexibleSensorMapping.user_id == user_id,
            FlexibleSensorMapping.competition_id == competition_id
        ).all()
        
        if not mappings:
            return []
        
        # データをタイムスタンプごとにグループ化
        grouped_data = {}
        
        # 体表温度データを取得
        skin_mappings = [m for m in mappings if m.sensor_type == SensorType.SKIN_TEMPERATURE]
        for mapping in skin_mappings:
            skin_data = db.query(SkinTemperatureData).filter(
                SkinTemperatureData.halshare_id == mapping.sensor_id,
                SkinTemperatureData.competition_id == competition_id
            ).order_by(SkinTemperatureData.datetime).all()
            
            for data in skin_data:
                timestamp_key = data.datetime.isoformat()
                if timestamp_key not in grouped_data:
                    grouped_data[timestamp_key] = SensorDataPoint(timestamp=timestamp_key)
                grouped_data[timestamp_key].skin_temperature = data.temperature
        
        # カプセル体温データを取得
        core_mappings = [m for m in mappings if m.sensor_type == SensorType.CORE_TEMPERATURE]
        for mapping in core_mappings:
            core_data = db.query(CoreTemperatureData).filter(
                CoreTemperatureData.capsule_id == mapping.sensor_id,
                CoreTemperatureData.competition_id == competition_id
            ).order_by(CoreTemperatureData.datetime).all()
            
            for data in core_data:
                timestamp_key = data.datetime.isoformat()
                if timestamp_key not in grouped_data:
                    grouped_data[timestamp_key] = SensorDataPoint(timestamp=timestamp_key)
                grouped_data[timestamp_key].core_temperature = data.temperature
        
        # 心拍データを取得
        hr_mappings = [m for m in mappings if m.sensor_type == SensorType.HEART_RATE]
        for mapping in hr_mappings:
            hr_data = db.query(HeartRateData).filter(
                HeartRateData.sensor_id == mapping.sensor_id,
                HeartRateData.competition_id == competition_id
            ).order_by(HeartRateData.time).all()
            
            for data in hr_data:
                timestamp_key = data.time.isoformat()
                if timestamp_key not in grouped_data:
                    grouped_data[timestamp_key] = SensorDataPoint(timestamp=timestamp_key)
                grouped_data[timestamp_key].heart_rate = data.heart_rate
        
        # WBGTデータを取得（共通環境データ）
        wbgt_data = db.query(WBGTData).filter(
            WBGTData.competition_id == competition_id
        ).order_by(WBGTData.datetime).all()
        
        for data in wbgt_data:
            timestamp_key = data.datetime.isoformat()
            if timestamp_key not in grouped_data:
                grouped_data[timestamp_key] = SensorDataPoint(timestamp=timestamp_key)
            grouped_data[timestamp_key].wbgt_temperature = data.wbgt_value
        
        return list(grouped_data.values())
        
    except Exception as e:
        logger.error(f"Error processing sensor data: {e}")
        return []


async def _get_race_record(db: Session, user_id: str, competition_id: str) -> Optional[RaceRecordSchema]:
    """大会記録データを取得"""
    try:
        # 大会記録データを取得
        race_record = db.query(RaceRecord).filter(
            RaceRecord.user_id == user_id,
            RaceRecord.competition_id == competition_id
        ).first()
        
        if not race_record:
            # 大会記録がない場合、センサーデータから推定
            return await _estimate_race_record_from_sensors(db, user_id, competition_id)
        
        return RaceRecordSchema(
            competition_id=competition_id,
            user_id=user_id,
            swim_start=race_record.swim_start.isoformat() if race_record.swim_start else None,
            swim_finish=race_record.swim_finish.isoformat() if race_record.swim_finish else None,
            bike_start=race_record.bike_start.isoformat() if race_record.bike_start else None,
            bike_finish=race_record.bike_finish.isoformat() if race_record.bike_finish else None,
            run_start=race_record.run_start.isoformat() if race_record.run_start else None,
            run_finish=race_record.run_finish.isoformat() if race_record.run_finish else None,
        )
        
    except Exception as e:
        logger.error(f"Error fetching race record: {e}")
        return None


async def _estimate_race_record_from_sensors(db: Session, user_id: str, competition_id: str) -> Optional[RaceRecordSchema]:
    """センサーデータから競技区間を推定"""
    try:
        # ユーザーのマッピングを取得
        mappings = db.query(FlexibleSensorMapping).filter(
            FlexibleSensorMapping.user_id == user_id,
            FlexibleSensorMapping.competition_id == competition_id
        ).all()
        
        if not mappings:
            return None
        
        # 最初と最後のデータ時刻を取得して推定
        earliest_time = None
        latest_time = None
        
        # 体表温度データから時間範囲を取得
        for mapping in mappings:
            if mapping.sensor_type == SensorType.SKIN_TEMPERATURE:
                first_data = db.query(SkinTemperatureData).filter(
                    SkinTemperatureData.halshare_id == mapping.sensor_id,
                    SkinTemperatureData.competition_id == competition_id
                ).order_by(SkinTemperatureData.datetime).first()
                
                last_data = db.query(SkinTemperatureData).filter(
                    SkinTemperatureData.halshare_id == mapping.sensor_id,
                    SkinTemperatureData.competition_id == competition_id
                ).order_by(SkinTemperatureData.datetime.desc()).first()
                
                if first_data and (not earliest_time or first_data.datetime < earliest_time):
                    earliest_time = first_data.datetime
                if last_data and (not latest_time or last_data.datetime > latest_time):
                    latest_time = last_data.datetime
        
        if earliest_time and latest_time:
            # 推定で競技区間を分割（仮実装）
            total_duration = latest_time - earliest_time
            swim_duration = total_duration * 0.2  # 20%をswimと仮定
            bike_duration = total_duration * 0.6  # 60%をbikeと仮定
            
            swim_end = earliest_time + swim_duration
            bike_end = swim_end + bike_duration
            
            return RaceRecordSchema(
                competition_id=competition_id,
                user_id=user_id,
                swim_start=earliest_time.isoformat(),
                swim_finish=swim_end.isoformat(),
                bike_start=swim_end.isoformat(),
                bike_finish=bike_end.isoformat(),
                run_start=bike_end.isoformat(),
                run_finish=latest_time.isoformat(),
            )
        
        return None
        
    except Exception as e:
        logger.error(f"Error estimating race record: {e}")
        return None


def _calculate_time_range(race_record: Optional[RaceRecordSchema], offset_minutes: int) -> Optional[Dict[str, datetime]]:
    """時間範囲を計算"""
    if not race_record:
        # 大会記録がない場合のデフォルト範囲（現在時刻の1時間前〜現在時刻）
        now = datetime.now()
        return {
            'start': now - timedelta(hours=1),
            'end': now
        }
    
    # swim開始からrun終了（またはデータの最後）までの範囲を計算
    start_time = None
    end_time = None
    
    if race_record.swim_start:
        start_time = datetime.fromisoformat(race_record.swim_start.replace('Z', '+00:00'))
    elif race_record.bike_start:
        start_time = datetime.fromisoformat(race_record.bike_start.replace('Z', '+00:00'))
    elif race_record.run_start:
        start_time = datetime.fromisoformat(race_record.run_start.replace('Z', '+00:00'))
    
    if race_record.run_finish:
        end_time = datetime.fromisoformat(race_record.run_finish.replace('Z', '+00:00'))
    elif race_record.bike_finish:
        end_time = datetime.fromisoformat(race_record.bike_finish.replace('Z', '+00:00'))
    elif race_record.run_start:
        # run開始から1時間後と仮定
        end_time = datetime.fromisoformat(race_record.run_start.replace('Z', '+00:00')) + timedelta(hours=1)
    
    if start_time and end_time:
        # オフセットを適用
        offset_delta = timedelta(minutes=offset_minutes)
        return {
            'start': start_time - offset_delta,
            'end': end_time + offset_delta
        }
    
    return None


def _convert_to_sensor_data_point(data) -> SensorDataPoint:
    """各種センサーデータをSensorDataPointに変換"""
    # この関数は新しい実装では不要ですが、互換性のため残します
    pass