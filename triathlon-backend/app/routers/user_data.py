# app/routers/user_data.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from app.utils.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.flexible_sensor_data import (
    RawSensorData, FlexibleSensorMapping, SensorType, SensorDataStatus
)
from app.models.competition import Competition, RaceRecord
from pydantic import BaseModel

router = APIRouter(prefix="/me", tags=["ユーザーデータ"])

class UserSensorSummary(BaseModel):
    sensor_type: str
    total_records: int
    latest_timestamp: Optional[datetime]
    sensor_id: str

class CompetitionDetail(BaseModel):
    competition_id: str
    name: str
    date: Optional[datetime]
    location: Optional[str]
    mapped_sensors: List[UserSensorSummary]
    total_records: int
    has_race_record: bool

class UserDataSummary(BaseModel):
    total_records: int
    total_competitions: int
    mapped_sensor_types: List[str]
    competitions: List[CompetitionDetail]
    latest_data_date: Optional[datetime]

@router.get("/data-summary", response_model=UserDataSummary)
async def get_user_data_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ユーザーのセンサーデータサマリー取得"""
    
    # マッピング済みセンサーデータを取得
    user_sensor_data = db.query(RawSensorData).filter(
        RawSensorData.mapped_user_id == current_user.user_id,
        RawSensorData.mapping_status == SensorDataStatus.MAPPED
    ).all()
    
    total_records = len(user_sensor_data)
    
    # デバッグ用ログ
    print(f"User {current_user.user_id} has {total_records} mapped sensor records")
    
    # 大会ごとのデータをまとめる
    competitions_data = {}
    sensor_types = set()
    latest_timestamp = None
    
    for data in user_sensor_data:
        comp_id = data.competition_id
        if comp_id not in competitions_data:
            competitions_data[comp_id] = {
                'records': [],
                'sensor_types': {}
            }
        
        competitions_data[comp_id]['records'].append(data)
        
        # センサータイプ別カウント
        sensor_type = data.sensor_type.value
        sensor_types.add(sensor_type)
        
        if sensor_type not in competitions_data[comp_id]['sensor_types']:
            competitions_data[comp_id]['sensor_types'][sensor_type] = {
                'count': 0,
                'sensor_id': data.sensor_id,
                'latest_timestamp': data.timestamp
            }
        
        competitions_data[comp_id]['sensor_types'][sensor_type]['count'] += 1
        
        # 最新タイムスタンプ更新
        if latest_timestamp is None or data.timestamp > latest_timestamp:
            latest_timestamp = data.timestamp
    
    # 大会詳細情報を取得
    competitions = []
    for comp_id, comp_data in competitions_data.items():
        competition = db.query(Competition).filter_by(competition_id=comp_id).first()
        if not competition:
            continue
        
        # レース記録の有無チェック
        race_record = db.query(RaceRecord).filter_by(
            competition_id=comp_id,
            user_id=current_user.user_id
        ).first()
        
        # センサーサマリー作成
        mapped_sensors = []
        for sensor_type, sensor_info in comp_data['sensor_types'].items():
            mapped_sensors.append(UserSensorSummary(
                sensor_type=sensor_type,
                total_records=sensor_info['count'],
                latest_timestamp=sensor_info['latest_timestamp'],
                sensor_id=sensor_info['sensor_id']
            ))
        
        competitions.append(CompetitionDetail(
            competition_id=comp_id,
            name=competition.name,
            date=competition.date,
            location=competition.location,
            mapped_sensors=mapped_sensors,
            total_records=len(comp_data['records']),
            has_race_record=race_record is not None
        ))
    
    return UserDataSummary(
        total_records=total_records,
        total_competitions=len(competitions),
        mapped_sensor_types=list(sensor_types),
        competitions=competitions,
        latest_data_date=latest_timestamp
    )

@router.get("/competition/{competition_id}/sensor-data")
async def get_user_competition_data(
    competition_id: str,
    sensor_type: Optional[SensorType] = Query(None),
    limit: int = Query(1000, le=5000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """特定大会のユーザーセンサーデータ取得"""
    
    query = db.query(RawSensorData).filter(
        RawSensorData.mapped_user_id == current_user.user_id,
        RawSensorData.competition_id == competition_id,
        RawSensorData.mapping_status == SensorDataStatus.MAPPED
    )
    
    if sensor_type:
        query = query.filter(RawSensorData.sensor_type == sensor_type)
    
    sensor_data = query.order_by(RawSensorData.timestamp).limit(limit).all()
    
    # データ変換
    result = []
    for data in sensor_data:
        values = data.get_data_as_dict()
        result.append({
            'timestamp': data.timestamp.isoformat(),
            'sensor_id': data.sensor_id,
            'sensor_type': data.sensor_type.value,
            'values': values
        })
    
    return {
        'competition_id': competition_id,
        'user_id': current_user.user_id,
        'total_records': len(result),
        'sensor_data': result
    }