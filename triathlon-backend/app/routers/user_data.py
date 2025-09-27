# app/routers/user_data.py - 完全書き直し版

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

# ===== スキーマ定義（直接定義） =====

class UserDataSummary(BaseModel):
    total_sensor_records: int
    competitions_participated: int
    avg_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    min_temperature: Optional[float] = None
    latest_data_date: Optional[str] = None

class SensorDataStats(BaseModel):
    total_records: int
    avg_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    min_temperature: Optional[float] = None
    latest_record_date: Optional[str] = None
    earliest_record_date: Optional[str] = None

class SensorMappingInfo(BaseModel):
    sensor_id: str
    sensor_type: str
    competition_id: str
    record_count: int
    subject_name: Optional[str] = None
    device_type: Optional[str] = None
    notes: Optional[str] = None

class ChartDataPoint(BaseModel):
    timestamp: str
    temperature: Optional[float] = None
    sensor_id: str

class SensorDataDetail(BaseModel):
    id: int
    timestamp: str
    sensor_id: str
    data_type: str
    numeric_value: Optional[float] = None
    text_value: Optional[str] = None
    competition_id: str
    context_data: Optional[str] = None

# ===== メインエンドポイント =====

@router.get("/data-summary", response_model=UserDataSummary)
async def get_user_data_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ユーザーのデータサマリーを取得
    """
    try:
        # ユーザーのセンサーマッピングを取得
        mappings = db.query(FlexibleSensorMapping).filter(
            FlexibleSensorMapping.user_id == current_user.user_id
        ).all()
        
        if not mappings:
            return UserDataSummary(
                total_sensor_records=0,
                competitions_participated=0,
                avg_temperature=None,
                max_temperature=None,
                min_temperature=None,
                latest_data_date=None
            )
        
        # データ統計を収集
        total_records = 0
        temperature_values = []
        all_timestamps = []
        
        # 参加大会数
        competitions_participated = len(set(m.competition_id for m in mappings))
        
        # 体表温度データ
        skin_mappings = [m for m in mappings if m.sensor_type == SensorType.SKIN_TEMPERATURE]
        for mapping in skin_mappings:
            skin_data = db.query(SkinTemperatureData).filter(
                SkinTemperatureData.halshare_id == mapping.sensor_id
            ).all()
            
            total_records += len(skin_data)
            temperature_values.extend([d.temperature for d in skin_data if d.temperature])
            all_timestamps.extend([d.datetime for d in skin_data])
        
        # カプセル体温データ
        core_mappings = [m for m in mappings if m.sensor_type == SensorType.CORE_TEMPERATURE]
        for mapping in core_mappings:
            core_data = db.query(CoreTemperatureData).filter(
                CoreTemperatureData.capsule_id == mapping.sensor_id
            ).all()
            
            total_records += len(core_data)
            temperature_values.extend([d.temperature for d in core_data if d.temperature])
            all_timestamps.extend([d.datetime for d in core_data])
        
        # 心拍データ
        hr_mappings = [m for m in mappings if m.sensor_type == SensorType.HEART_RATE]
        for mapping in hr_mappings:
            hr_data = db.query(HeartRateData).filter(
                HeartRateData.sensor_id == mapping.sensor_id
            ).all()
            
            total_records += len(hr_data)
            all_timestamps.extend([d.time for d in hr_data])
        
        # 統計計算
        avg_temp = sum(temperature_values) / len(temperature_values) if temperature_values else None
        max_temp = max(temperature_values) if temperature_values else None
        min_temp = min(temperature_values) if temperature_values else None
        latest_date = max(all_timestamps).isoformat() if all_timestamps else None
        
        return UserDataSummary(
            total_sensor_records=total_records,
            competitions_participated=competitions_participated,
            avg_temperature=avg_temp,
            max_temperature=max_temp,
            min_temperature=min_temp,
            latest_data_date=latest_date
        )
        
    except Exception as e:
        logger.error(f"Error fetching user data summary: {e}")
        raise HTTPException(status_code=500, detail="データサマリーの取得に失敗しました")


@router.get("/stats", response_model=SensorDataStats)
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
            return SensorDataStats(
                total_records=0,
                avg_temperature=None,
                max_temperature=None,
                min_temperature=None,
                latest_record_date=None,
                earliest_record_date=None
            )
        
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
        
        return SensorDataStats(
            total_records=total_records,
            avg_temperature=avg_temp,
            max_temperature=max_temp,
            min_temperature=min_temp,
            latest_record_date=latest_date,
            earliest_record_date=earliest_date
        )
        
    except Exception as e:
        logger.error(f"Error fetching user stats: {e}")
        raise HTTPException(status_code=500, detail="統計データの取得に失敗しました")


@router.get("/sensor-mappings", response_model=List[SensorMappingInfo])
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
            # 各センサーのレコード数を取得
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
            
            result.append(SensorMappingInfo(
                sensor_id=mapping.sensor_id,
                sensor_type=mapping.sensor_type.value,
                competition_id=mapping.competition_id,
                record_count=record_count,
                subject_name=mapping.subject_name or current_user.full_name or current_user.username,
                device_type=mapping.device_type,
                notes=mapping.notes
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching sensor mappings: {e}")
        raise HTTPException(status_code=500, detail="センサーマッピングの取得に失敗しました")


@router.get("/chart-data")
async def get_chart_data(
    start_date: str,
    end_date: str,
    interval: str = Query("15min", regex="^(1min|5min|15min|1hour|1day)$"),
    sensor_id: Optional[str] = None,
    data_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    チャート用のセンサーデータを取得
    """
    try:
        # 日時範囲の解析
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # ユーザーのマッピングを取得
        mappings_query = db.query(FlexibleSensorMapping).filter(
            FlexibleSensorMapping.user_id == current_user.user_id
        )
        
        if sensor_id:
            mappings_query = mappings_query.filter(FlexibleSensorMapping.sensor_id == sensor_id)
        
        if data_type:
            try:
                sensor_type = SensorType(data_type)
                mappings_query = mappings_query.filter(FlexibleSensorMapping.sensor_type == sensor_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"無効なデータタイプ: {data_type}")
        
        mappings = mappings_query.all()
        
        chart_data = []
        
        # 各センサータイプからデータを取得
        for mapping in mappings:
            if mapping.sensor_type == SensorType.SKIN_TEMPERATURE:
                skin_data = db.query(SkinTemperatureData).filter(
                    SkinTemperatureData.halshare_id == mapping.sensor_id,
                    SkinTemperatureData.datetime >= start_dt,
                    SkinTemperatureData.datetime <= end_dt,
                    SkinTemperatureData.temperature.isnot(None)
                ).order_by(SkinTemperatureData.datetime).all()
                
                for record in skin_data:
                    chart_data.append({
                        "timestamp": record.datetime.isoformat(),
                        "temperature": record.temperature,
                        "sensor_id": record.halshare_id
                    })
            
            elif mapping.sensor_type == SensorType.CORE_TEMPERATURE:
                core_data = db.query(CoreTemperatureData).filter(
                    CoreTemperatureData.capsule_id == mapping.sensor_id,
                    CoreTemperatureData.datetime >= start_dt,
                    CoreTemperatureData.datetime <= end_dt,
                    CoreTemperatureData.temperature.isnot(None)
                ).order_by(CoreTemperatureData.datetime).all()
                
                for record in core_data:
                    chart_data.append({
                        "timestamp": record.datetime.isoformat(),
                        "temperature": record.temperature,
                        "sensor_id": record.capsule_id
                    })
        
        # インターバル処理
        filtered_data = _apply_interval_filter(chart_data, interval)
        
        return {
            "data": filtered_data,
            "total_count": len(filtered_data),
            "date_range": {
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chart data: {e}")
        raise HTTPException(status_code=500, detail="チャートデータの取得に失敗しました")

# user_data.pyの/me/sensor-dataエンドポイント部分を修正

@router.get("/sensor-data")
async def get_user_sensor_data(
    competition_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    data_types: Optional[List[str]] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ユーザーのセンサーデータを取得（修正版）
    """
    try:
        logger.info(f"Fetching sensor data for user: {current_user.user_id}, competition: {competition_id}")
        
        # ユーザーのマッピングを取得
        mappings_query = db.query(FlexibleSensorMapping).filter(
            FlexibleSensorMapping.user_id == current_user.user_id
        )
        
        if competition_id:
            mappings_query = mappings_query.filter(FlexibleSensorMapping.competition_id == competition_id)
        
        mappings = mappings_query.all()
        logger.info(f"Found {len(mappings)} mappings for user")
        
        if not mappings:
            logger.info("No mappings found, returning empty list")
            return []
        
        # 日時フィルター設定
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError as e:
                logger.error(f"Invalid start_date format: {start_date}, error: {e}")
                raise HTTPException(status_code=400, detail=f"無効な開始日時形式: {start_date}")
                
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError as e:
                logger.error(f"Invalid end_date format: {end_date}, error: {e}")
                raise HTTPException(status_code=400, detail=f"無効な終了日時形式: {end_date}")
        
        # データをタイムスタンプごとにグループ化
        grouped_data = {}
        
        for mapping in mappings:
            logger.info(f"Processing mapping: {mapping.sensor_id}, type: {mapping.sensor_type}")
            
            try:
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
                    logger.info(f"Found {len(skin_data)} skin temperature records")
                    
                    for data in skin_data:
                        timestamp_key = data.datetime.isoformat()
                        if timestamp_key not in grouped_data:
                            grouped_data[timestamp_key] = {
                                "timestamp": timestamp_key,
                                "skin_temperature": None,
                                "core_temperature": None,
                                "wbgt_temperature": None,
                                "heart_rate": None,
                                "sensor_id": None,
                                "data_type": None
                            }
                        grouped_data[timestamp_key]["skin_temperature"] = data.temperature
                        grouped_data[timestamp_key]["sensor_id"] = data.halshare_id
                        grouped_data[timestamp_key]["data_type"] = "skin_temperature"
                
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
                    logger.info(f"Found {len(core_data)} core temperature records")
                    
                    for data in core_data:
                        if data.temperature is not None:  # None値をスキップ
                            timestamp_key = data.datetime.isoformat()
                            if timestamp_key not in grouped_data:
                                grouped_data[timestamp_key] = {
                                    "timestamp": timestamp_key,
                                    "skin_temperature": None,
                                    "core_temperature": None,
                                    "wbgt_temperature": None,
                                    "heart_rate": None,
                                    "sensor_id": None,
                                    "data_type": None
                                }
                            grouped_data[timestamp_key]["core_temperature"] = data.temperature
                            grouped_data[timestamp_key]["sensor_id"] = data.capsule_id
                            grouped_data[timestamp_key]["data_type"] = "core_temperature"
                
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
                    logger.info(f"Found {len(hr_data)} heart rate records")
                    
                    for data in hr_data:
                        if data.heart_rate is not None:  # None値をスキップ
                            timestamp_key = data.time.isoformat()
                            if timestamp_key not in grouped_data:
                                grouped_data[timestamp_key] = {
                                    "timestamp": timestamp_key,
                                    "skin_temperature": None,
                                    "core_temperature": None,
                                    "wbgt_temperature": None,
                                    "heart_rate": None,
                                    "sensor_id": None,
                                    "data_type": None
                                }
                            grouped_data[timestamp_key]["heart_rate"] = data.heart_rate
                            grouped_data[timestamp_key]["sensor_id"] = data.sensor_id
                            grouped_data[timestamp_key]["data_type"] = "heart_rate"
                            
            except Exception as mapping_error:
                logger.error(f"Error processing mapping {mapping.sensor_id}: {mapping_error}")
                continue  # このマッピングのエラーはスキップして続行
        
        # WBGTデータを追加（競技環境データ）
        if competition_id:
            try:
                wbgt_query = db.query(WBGTData).filter(
                    WBGTData.competition_id == competition_id
                )
                if start_dt:
                    wbgt_query = wbgt_query.filter(WBGTData.datetime >= start_dt)
                if end_dt:
                    wbgt_query = wbgt_query.filter(WBGTData.datetime <= end_dt)
                
                wbgt_data = wbgt_query.order_by(WBGTData.datetime).all()
                logger.info(f"Found {len(wbgt_data)} WBGT records")
                
                for data in wbgt_data:
                    if data.wbgt_value is not None:  # None値をスキップ
                        timestamp_key = data.datetime.isoformat()
                        if timestamp_key not in grouped_data:
                            grouped_data[timestamp_key] = {
                                "timestamp": timestamp_key,
                                "skin_temperature": None,
                                "core_temperature": None,
                                "wbgt_temperature": None,
                                "heart_rate": None,
                                "sensor_id": None,
                                "data_type": None
                            }
                        grouped_data[timestamp_key]["wbgt_temperature"] = data.wbgt_value
                        grouped_data[timestamp_key]["sensor_id"] = "WBGT_ENV"
                        grouped_data[timestamp_key]["data_type"] = "wbgt"
                        
            except Exception as wbgt_error:
                logger.error(f"Error processing WBGT data: {wbgt_error}")
                # WBGT データのエラーは無視して続行
        
        result = list(grouped_data.values())
        logger.info(f"Returning {len(result)} sensor data points")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_user_sensor_data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"センサーデータの取得中にエラーが発生しました: {str(e)}")
        
@router.get("/sensor-data-details")
async def get_sensor_data_details(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    sensor_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    センサーデータの詳細一覧を取得（ページネーション対応）
    """
    try:
        # ユーザーのマッピングを取得
        mappings_query = db.query(FlexibleSensorMapping).filter(
            FlexibleSensorMapping.user_id == current_user.user_id
        )
        
        if sensor_id:
            mappings_query = mappings_query.filter(FlexibleSensorMapping.sensor_id == sensor_id)
        
        if data_type:
            try:
                sensor_type = SensorType(data_type)
                mappings_query = mappings_query.filter(FlexibleSensorMapping.sensor_type == sensor_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"無効なデータタイプ: {data_type}")
        
        mappings = mappings_query.all()
        
        # 日時フィルター設定
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        all_data = []
        
        # 各センサータイプのデータを収集
        for mapping in mappings:
            if mapping.sensor_type == SensorType.SKIN_TEMPERATURE:
                query = db.query(SkinTemperatureData).filter(
                    SkinTemperatureData.halshare_id == mapping.sensor_id
                )
                
                if start_dt:
                    query = query.filter(SkinTemperatureData.datetime >= start_dt)
                if end_dt:
                    query = query.filter(SkinTemperatureData.datetime <= end_dt)
                
                skin_data = query.order_by(desc(SkinTemperatureData.datetime)).all()
                
                for record in skin_data:
                    all_data.append({
                        "id": record.id,
                        "timestamp": record.datetime.isoformat(),
                        "sensor_id": record.halshare_id,
                        "data_type": "skin_temperature",
                        "numeric_value": record.temperature,
                        "text_value": None,
                        "competition_id": record.competition_id,
                        "context_data": f"upload_batch_id: {record.upload_batch_id}"
                    })
            
            elif mapping.sensor_type == SensorType.CORE_TEMPERATURE:
                query = db.query(CoreTemperatureData).filter(
                    CoreTemperatureData.capsule_id == mapping.sensor_id
                )
                
                if start_dt:
                    query = query.filter(CoreTemperatureData.datetime >= start_dt)
                if end_dt:
                    query = query.filter(CoreTemperatureData.datetime <= end_dt)
                
                core_data = query.order_by(desc(CoreTemperatureData.datetime)).all()
                
                for record in core_data:
                    all_data.append({
                        "id": record.id,
                        "timestamp": record.datetime.isoformat(),
                        "sensor_id": record.capsule_id,
                        "data_type": "core_temperature",
                        "numeric_value": record.temperature,
                        "text_value": record.status,
                        "competition_id": record.competition_id,
                        "context_data": f"monitor_id: {record.monitor_id}, upload_batch_id: {record.upload_batch_id}"
                    })
            
            elif mapping.sensor_type == SensorType.HEART_RATE:
                query = db.query(HeartRateData).filter(
                    HeartRateData.sensor_id == mapping.sensor_id
                )
                
                if start_dt:
                    query = query.filter(HeartRateData.time >= start_dt)
                if end_dt:
                    query = query.filter(HeartRateData.time <= end_dt)
                
                hr_data = query.order_by(desc(HeartRateData.time)).all()
                
                for record in hr_data:
                    all_data.append({
                        "id": record.id,
                        "timestamp": record.time.isoformat(),
                        "sensor_id": record.sensor_id,
                        "data_type": "heart_rate",
                        "numeric_value": record.heart_rate,
                        "text_value": None,
                        "competition_id": record.competition_id,
                        "context_data": f"upload_batch_id: {record.upload_batch_id}"
                    })
        
        # データをタイムスタンプでソート
        all_data.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # ページネーション
        total_count = len(all_data)
        offset = (page - 1) * page_size
        paginated_data = all_data[offset:offset + page_size]
        
        return {
            "data": paginated_data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sensor data details: {e}")
        raise HTTPException(status_code=500, detail="詳細データの取得に失敗しました")


@router.get("/competitions/{competition_id}/summary")
async def get_competition_data_summary(
    competition_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    指定大会のデータサマリーを取得
    """
    try:
        # 大会情報取得
        competition = db.query(Competition).filter(
            Competition.competition_id == competition_id
        ).first()
        
        if not competition:
            raise HTTPException(status_code=404, detail="指定された大会が見つかりません")
        
        # ユーザーの該当大会マッピング取得
        mappings = db.query(FlexibleSensorMapping).filter(
            FlexibleSensorMapping.user_id == current_user.user_id,
            FlexibleSensorMapping.competition_id == competition_id
        ).all()
        
        if not mappings:
            raise HTTPException(status_code=404, detail="この大会のデータが見つかりません")
        
        # データ統計収集
        total_records = 0
        data_types = set()
        temp_values = []
        hr_values = []
        all_times = []
        
        for mapping in mappings:
            data_types.add(mapping.sensor_type.value)
            
            if mapping.sensor_type == SensorType.SKIN_TEMPERATURE:
                skin_data = db.query(SkinTemperatureData).filter(
                    SkinTemperatureData.halshare_id == mapping.sensor_id,
                    SkinTemperatureData.competition_id == competition_id
                ).all()
                
                total_records += len(skin_data)
                temp_values.extend([d.temperature for d in skin_data if d.temperature])
                all_times.extend([d.datetime for d in skin_data])
                
            elif mapping.sensor_type == SensorType.CORE_TEMPERATURE:
                core_data = db.query(CoreTemperatureData).filter(
                    CoreTemperatureData.capsule_id == mapping.sensor_id,
                    CoreTemperatureData.competition_id == competition_id
                ).all()
                
                total_records += len(core_data)
                temp_values.extend([d.temperature for d in core_data if d.temperature])
                all_times.extend([d.datetime for d in core_data])
                
            elif mapping.sensor_type == SensorType.HEART_RATE:
                hr_data = db.query(HeartRateData).filter(
                    HeartRateData.sensor_id == mapping.sensor_id,
                    HeartRateData.competition_id == competition_id
                ).all()
                
                total_records += len(hr_data)
                hr_values.extend([d.heart_rate for d in hr_data if d.heart_rate])
                all_times.extend([d.time for d in hr_data])
        
        # 継続時間計算
        duration_minutes = 0
        start_time = None
        end_time = None
        
        if all_times:
            start_time = min(all_times)
            end_time = max(all_times)
            duration = end_time - start_time
            duration_minutes = duration.total_seconds() / 60
        
        return {
            "competition_id": competition_id,
            "competition_name": competition.name,
            "participation_date": competition.created_at.isoformat(),
            "total_records": total_records,
            "data_types": list(data_types),
            "duration": {
                "start": start_time.isoformat() if start_time else None,
                "end": end_time.isoformat() if end_time else None,
                "total_minutes": duration_minutes
            },
            "statistics": {
                "avg_temperature": sum(temp_values) / len(temp_values) if temp_values else None,
                "max_temperature": max(temp_values) if temp_values else None,
                "min_temperature": min(temp_values) if temp_values else None,
                "avg_heart_rate": sum(hr_values) / len(hr_values) if hr_values else None,
                "max_heart_rate": max(hr_values) if hr_values else None,
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching competition summary: {e}")
        raise HTTPException(status_code=500, detail="大会サマリーの取得に失敗しました")


# ===== ユーティリティ関数 =====

def _apply_interval_filter(data: List[Dict], interval: str) -> List[Dict]:
    """
    指定されたインターバルに応じてデータを間引く
    """
    if not data:
        return data
    
    if interval == "1min":
        return data  # 全データを返す
    
    # インターバルに応じた間隔を設定
    interval_minutes = {
        "5min": 5,
        "15min": 15,
        "1hour": 60,
        "1day": 1440
    }.get(interval, 15)
    
    # データをタイムスタンプでソート
    sorted_data = sorted(data, key=lambda x: x["timestamp"])
    
    filtered = []
    last_time = None
    
    for record in sorted_data:
        current_time = datetime.fromisoformat(record["timestamp"].replace('Z', '+00:00'))
        
        if last_time is None:
            filtered.append(record)
            last_time = current_time
        else:
            diff = (current_time - last_time).total_seconds() / 60
            if diff >= interval_minutes:
                filtered.append(record)
                last_time = current_time
    
    return filtered