"""
app/routers/admin.py (完全版 - 大会記録アップロード対応)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, date
import pandas as pd
import xml.etree.ElementTree as ET
import io
import chardet
import secrets
import string

from app.database import get_db
from app.models.user import User, AdminUser
from app.models.competition import Competition, RaceRecord
from app.models.flexible_sensor_data import *
from app.schemas.user import UserCreate, UserUpdate, UserResponse, AdminResponse
from app.schemas.sensor_data import UploadResponse, MappingResponse, DataSummaryResponse
from app.utils.dependencies import get_current_admin
from app.utils.security import get_password_hash
from app.services.flexible_csv_service import FlexibleCSVService

router = APIRouter(prefix="/admin", tags=["admin"])

# ===== ユーティリティ関数 =====

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

# ===== ユーザー管理用のユーティリティ関数 =====

def generate_user_id() -> str:
    """ユニークなユーザーIDを生成"""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_suffix = ''.join(secrets.choice(string.digits) for _ in range(4))
    return f"user_{timestamp}_{random_suffix}"

def generate_password() -> str:
    """安全なパスワードを生成（8文字、英数字混合）"""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(8))


# ===== システム統計 =====

@router.get("/stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """管理者向けシステム統計情報（シンプル化版）"""
    try:
        # ユーザー統計
        total_users = db.query(User).count()
        total_admins = db.query(AdminUser).count()
        
        # 大会統計
        total_competitions = db.query(Competition).count()
        
        # センサーデータ統計（シンプル）
        total_skin_temp = db.query(SkinTemperatureData).count()
        total_core_temp = db.query(CoreTemperatureData).count()
        total_heart_rate = db.query(HeartRateData).count()
        total_wbgt = db.query(WBGTData).count()
        total_race_records = db.query(RaceRecord).count()
        
        # マッピング統計（物理削除ベース）
        total_mappings = db.query(FlexibleSensorMapping).count()
        
        # センサーID別のマッピング統計
        mapped_sensors_count = db.query(
            FlexibleSensorMapping.sensor_id
        ).distinct().count()
        
        # ユーザー別マッピング統計
        users_with_mappings = db.query(
            FlexibleSensorMapping.user_id
        ).distinct().count()
        
        # アップロードバッチ統計
        total_batches = db.query(UploadBatch).count()
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        recent_batches = db.query(UploadBatch).filter(
            UploadBatch.uploaded_at >= today_start
        ).count()
        
        return {
            "users": {
                "total_users": total_users,
                "total_admins": total_admins
            },
            "competitions": {
                "total_competitions": total_competitions
            },
            "sensor_data": {
                "skin_temperature": total_skin_temp,
                "core_temperature": total_core_temp,
                "heart_rate": total_heart_rate,
                "wbgt": total_wbgt,
                "race_records": total_race_records,
                "total_records": total_skin_temp + total_core_temp + total_heart_rate + total_wbgt
            },
            "mappings": {
                "total_mappings": total_mappings,
                "mapped_sensors": mapped_sensors_count,
                "users_with_mappings": users_with_mappings
            },
            "upload_activity": {
                "total_batches": total_batches,
                "today_batches": recent_batches
            }
        }
        
    except Exception as e:
        error_message = f"統計情報取得エラー: {str(e)}"
        print(f"❌ {error_message}")
        raise HTTPException(status_code=500, detail=error_message)

# ===== ユーザー管理 =====

@router.get("/users")
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """ユーザー一覧取得（JOIN修正版）"""
    try:
        query = db.query(User)
        
        # 検索機能
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.username.ilike(search_term)) |
                (User.full_name.ilike(search_term)) |
                (User.email.ilike(search_term)) |
                (User.user_id.ilike(search_term))
            )
        
        # ページネーション
        total_count = query.count()
        users = query.offset(skip).limit(limit).all()
        
        # レスポンス形式を修正（JOINベース）
        user_list = []
        for user in users:
            # JOINクエリでセンサーデータ数を取得
            skin_temp_count = get_user_sensor_data_count(db, user.user_id, "skin_temperature")
            core_temp_count = get_user_sensor_data_count(db, user.user_id, "core_temperature")
            heart_rate_count = get_user_sensor_data_count(db, user.user_id, "heart_rate")
            
            # マッピング情報取得
            mapping_count = db.query(FlexibleSensorMapping).filter_by(
                user_id=user.user_id
            ).count()
            
            user_list.append({
                "id": user.id,
                "user_id": user.user_id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "sensor_data_count": skin_temp_count + core_temp_count + heart_rate_count,
                "mapping_count": mapping_count,
                "sensor_breakdown": {
                    "skin_temperature": skin_temp_count,
                    "core_temperature": core_temp_count,
                    "heart_rate": heart_rate_count
                }
            })
        
        return {
            "users": user_list,
            "pagination": {
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "has_more": total_count > (skip + limit)
            }
        }
        
    except Exception as e:
        error_message = f"ユーザー一覧取得エラー: {str(e)}"
        print(f"❌ {error_message}")
        raise HTTPException(status_code=500, detail=error_message)

@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """ユーザー詳細取得（JOIN修正版）"""
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
        # JOINクエリでセンサーデータ数を取得
        skin_temp_count = get_user_sensor_data_count(db, user.user_id, "skin_temperature")
        core_temp_count = get_user_sensor_data_count(db, user.user_id, "core_temperature")
        heart_rate_count = get_user_sensor_data_count(db, user.user_id, "heart_rate")
        
        # 参加大会一覧
        race_records = db.query(RaceRecord).filter_by(user_id=user.user_id).all()
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
                    "race_number": record.race_number
                })
        
        # マッピング情報（is_activeフィルタ削除）
        mappings = db.query(FlexibleSensorMapping).filter_by(
            user_id=user.user_id
        ).all()
        
        mapping_info = {}
        for mapping in mappings:
            sensor_type = mapping.sensor_type.value
            if sensor_type not in mapping_info:
                mapping_info[sensor_type] = []
            mapping_info[sensor_type].append({
                "sensor_id": mapping.sensor_id,
                "competition_id": mapping.competition_id,
                "device_type": mapping.device_type,
                "subject_name": mapping.subject_name
            })
        
        return {
            "user_info": {
                "id": user.id,
                "user_id": user.user_id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            "sensor_data_summary": {
                "skin_temperature": skin_temp_count,
                "core_temperature": core_temp_count,
                "heart_rate": heart_rate_count,
                "total": skin_temp_count + core_temp_count + heart_rate_count
            },
            "competitions": competitions_data,
            "sensor_mappings": mapping_info,
            "statistics": {
                "total_competitions": len(competitions_data),
                "total_sensor_data": skin_temp_count + core_temp_count + heart_rate_count,
                "total_mappings": len(mappings)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_message = f"ユーザー詳細取得エラー: {str(e)}"
        print(f"❌ {error_message}")
        raise HTTPException(status_code=500, detail=error_message)

@router.get("/users/{user_id}/dashboard")
async def get_user_dashboard_as_admin(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Admin権限でユーザーダッシュボードデータ取得（JOIN修正版）"""
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # JOINクエリでセンサーデータを取得
        skin_temp_data = get_user_sensor_data(db, user.user_id, "skin_temperature")
        core_temp_data = get_user_sensor_data(db, user.user_id, "core_temperature")
        heart_rate_data = get_user_sensor_data(db, user.user_id, "heart_rate")
        
        # 参加大会一覧
        race_records = db.query(RaceRecord).filter_by(user_id=user.user_id).all()
        competitions_list = []
        
        for record in race_records:
            competition = db.query(Competition).filter_by(competition_id=record.competition_id).first()
            if competition:
                competitions_list.append({
                    "competition_id": competition.competition_id,
                    "name": competition.name,
                    "date": competition.date.isoformat() if competition.date else None,
                    "location": competition.location,
                    "race_number": record.race_number,
                    "has_sensor_data": len(skin_temp_data) > 0 or len(core_temp_data) > 0 or len(heart_rate_data) > 0
                })
        
        # 最新のセンサーデータ（サンプル）
        latest_data = []
        if skin_temp_data:
            latest_skin = sorted(skin_temp_data, key=lambda x: x.datetime, reverse=True)[:5]
            for data in latest_skin:
                latest_data.append({
                    "type": "skin_temperature",
                    "datetime": data.datetime.isoformat(),
                    "value": data.temperature,
                    "sensor_id": data.halshare_id,
                    "competition_id": data.competition_id
                })
        
        return {
            "user_info": {
                "user_id": user.user_id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email
            },
            "sensor_data_summary": {
                "skin_temperature_count": len(skin_temp_data),
                "core_temperature_count": len(core_temp_data),
                "heart_rate_count": len(heart_rate_data),
                "total_records": len(skin_temp_data) + len(core_temp_data) + len(heart_rate_data)
            },
            "competitions": competitions_list,
            "recent_sensor_data": latest_data[:10],  # 最新10件
            "access_info": {
                "accessed_by_admin": current_admin.admin_id,
                "access_time": datetime.now().isoformat(),
                "access_type": "admin_view"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_message = f"ユーザーダッシュボード取得エラー: {str(e)}"
        print(f"❌ {error_message}")
        raise HTTPException(status_code=500, detail=error_message)

@router.get("/users/{user_id}/sensor-data")
async def get_user_sensor_data(
    user_id: str,
    competition_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """ユーザーのセンサーデータ詳細取得（JOINベース修正版）"""
    
    # ユーザー存在チェック
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    try:
        sensor_data = []
        
        # JOINクエリで体表温データを取得
        skin_temp_data = _get_user_sensor_data_helper(db, user_id, "skin_temperature", competition_id)
        if skin_temp_data:
            latest_record = max(skin_temp_data, key=lambda x: x.datetime)
            earliest_record = min(skin_temp_data, key=lambda x: x.datetime)
            
            sensor_data.append({
                "sensor_type": "体表温センサー",
                "sensor_id": skin_temp_data[0].halshare_id,
                "record_count": len(skin_temp_data),
                "latest_record": latest_record.datetime.isoformat(),
                "earliest_record": earliest_record.datetime.isoformat(),
                "latest_value": latest_record.temperature,
                "sensor_location": "halshare"
            })
        
        # JOINクエリでカプセル体温データを取得
        core_temp_data = _get_user_sensor_data_helper(db, user_id, "core_temperature", competition_id)
        if core_temp_data:
            latest_record = max(core_temp_data, key=lambda x: x.datetime)
            earliest_record = min(core_temp_data, key=lambda x: x.datetime)
            
            sensor_data.append({
                "sensor_type": "カプセル体温センサー",
                "sensor_id": core_temp_data[0].capsule_id,
                "record_count": len(core_temp_data),
                "latest_record": latest_record.datetime.isoformat(),
                "earliest_record": earliest_record.datetime.isoformat(),
                "latest_value": latest_record.temperature,
                "sensor_location": "e-Celcius"
            })
        
        # JOINクエリで心拍データを取得
        heart_rate_data = _get_user_sensor_data_helper(db, user_id, "heart_rate", competition_id)
        if heart_rate_data:
            latest_record = max(heart_rate_data, key=lambda x: x.time)
            earliest_record = min(heart_rate_data, key=lambda x: x.time)
            
            sensor_data.append({
                "sensor_type": "心拍センサー",
                "sensor_id": heart_rate_data[0].sensor_id,
                "record_count": len(heart_rate_data),
                "latest_record": latest_record.time.isoformat(),
                "earliest_record": earliest_record.time.isoformat(),
                "latest_value": latest_record.heart_rate,
                "sensor_location": "Garmin"
            })
        
        return {
            "user_id": user_id,
            "competition_id": competition_id,
            "sensor_data": sensor_data,
            "total_sensors": len(sensor_data),
            "access_info": {
                "accessed_by_admin": current_admin.admin_id,
                "access_time": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        error_message = f"ユーザーセンサーデータ取得エラー: {str(e)}"
        print(f"❌ {error_message}")
        raise HTTPException(status_code=500, detail=error_message)

def get_user_sensor_data_count(db: Session, user_id: str, sensor_type: str, competition_id: str = None) -> int:
    """JOINクエリでユーザーのセンサーデータ数を取得"""
    
    # マッピング取得
    mapping_query = db.query(FlexibleSensorMapping).filter_by(
        user_id=user_id,
        sensor_type=sensor_type
    )
    if competition_id:
        mapping_query = mapping_query.filter_by(competition_id=competition_id)
    
    mappings = mapping_query.all()
    if not mappings:
        return 0
    
    sensor_ids = [m.sensor_id for m in mappings]
    
    # センサータイプ別データ数取得
    if sensor_type == "skin_temperature":
        return db.query(SkinTemperatureData).filter(
            SkinTemperatureData.halshare_id.in_(sensor_ids)
        ).count() if sensor_ids else 0
        
    elif sensor_type == "core_temperature":
        return db.query(CoreTemperatureData).filter(
            CoreTemperatureData.capsule_id.in_(sensor_ids)
        ).count() if sensor_ids else 0
        
    elif sensor_type == "heart_rate":
        return db.query(HeartRateData).filter(
            HeartRateData.sensor_id.in_(sensor_ids)
        ).count() if sensor_ids else 0
    
    return 0

def get_user_sensor_data(db: Session, user_id: str, sensor_type: str, competition_id: str = None) -> list:
    """JOINクエリでユーザーのセンサーデータを取得"""
    
    # マッピング取得
    mapping_query = db.query(FlexibleSensorMapping).filter_by(
        user_id=user_id,
        sensor_type=sensor_type
    )
    if competition_id:
        mapping_query = mapping_query.filter_by(competition_id=competition_id)
    
    mappings = mapping_query.all()
    if not mappings:
        return []
    
    sensor_ids = [m.sensor_id for m in mappings]
    
    # センサータイプ別データ取得
    if sensor_type == "skin_temperature":
        query = db.query(SkinTemperatureData).filter(
            SkinTemperatureData.halshare_id.in_(sensor_ids)
        )
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        return query.order_by(SkinTemperatureData.datetime).all()
        
    elif sensor_type == "core_temperature":
        query = db.query(CoreTemperatureData).filter(
            CoreTemperatureData.capsule_id.in_(sensor_ids)
        )
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        return query.order_by(CoreTemperatureData.datetime).all()
        
    elif sensor_type == "heart_rate":
        query = db.query(HeartRateData).filter(
            HeartRateData.sensor_id.in_(sensor_ids)
        )
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        return query.order_by(HeartRateData.time).all()
    
    return []

# ===== 大会管理 =====

@router.get("/competitions")
async def get_competitions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会一覧取得"""
    competitions = db.query(Competition).offset(skip).limit(limit).all()
    
    results = []
    for comp in competitions:
        # 参加者数とデータ数の計算
        participant_count = db.query(RaceRecord).filter_by(competition_id=comp.competition_id).count()
        sensor_data_count = (
            db.query(SkinTemperatureData).filter_by(competition_id=comp.competition_id).count() +
            db.query(CoreTemperatureData).filter_by(competition_id=comp.competition_id).count() +
            db.query(HeartRateData).filter_by(competition_id=comp.competition_id).count()
        )
        
        results.append({
            "id": comp.id,
            "competition_id": comp.competition_id,
            "name": comp.name,
            "date": comp.date,
            "location": comp.location,
            "description": comp.description,
            "created_at": comp.created_at,
            "participant_count": participant_count,
            "sensor_data_count": sensor_data_count
        })
    
    return results

@router.post("/competitions")
async def create_competition(
    name: str = Form(...),
    date: Optional[date] = Form(None),
    location: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会作成"""
    competition = Competition(
        name=name,
        date=date,
        location=location,
        description=description
    )
    
    db.add(competition)
    db.commit()
    db.refresh(competition)
    
    return {
        "message": f"大会 '{name}' を作成しました",
        "competition_id": competition.competition_id,
        "name": competition.name
    }

@router.delete("/competitions/{competition_id}")
async def delete_competition(
    competition_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会削除"""
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    # 関連データ数をカウント
    sensor_data_count = (
        db.query(SkinTemperatureData).filter_by(competition_id=competition_id).count() +
        db.query(CoreTemperatureData).filter_by(competition_id=competition_id).count() +
        db.query(HeartRateData).filter_by(competition_id=competition_id).count() +
        db.query(WBGTData).filter_by(competition_id=competition_id).count()
    )
    race_record_count = db.query(RaceRecord).filter_by(competition_id=competition_id).count()
    mapping_count = db.query(FlexibleSensorMapping).filter_by(competition_id=competition_id).count()
    
    # 関連データを削除
    db.query(SkinTemperatureData).filter_by(competition_id=competition_id).delete()
    db.query(CoreTemperatureData).filter_by(competition_id=competition_id).delete()
    db.query(HeartRateData).filter_by(competition_id=competition_id).delete()
    db.query(WBGTData).filter_by(competition_id=competition_id).delete()
    db.query(RaceRecord).filter_by(competition_id=competition_id).delete()
    db.query(FlexibleSensorMapping).filter_by(competition_id=competition_id).delete()
    
    # 大会削除
    db.delete(competition)
    db.commit()
    
    return {
        "message": f"大会 '{competition.name}' と関連データを削除しました",
        "deleted_sensor_data": sensor_data_count,
        "deleted_race_records": race_record_count,
        "deleted_mappings": mapping_count
    }

# ===== データアップロード =====

# app/routers/admin.py - 最終修正版（クォート処理対応）

@router.post("/upload/skin-temperature")
async def upload_skin_temperature(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """体表温データ（halshare）アップロード - 最終修正版"""
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    results = []
    
    for file in files:
        batch_id = generate_batch_id(file.filename)
        
        try:
            content = await file.read()
            encoding = detect_encoding(content)
            
            # CSVファイル読み込み
            try:
                df = pd.read_csv(io.BytesIO(content), encoding=encoding)
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
                except Exception as e:
                    df = pd.read_csv(io.BytesIO(content), encoding='shift-jis')
            
            # 必要な列の確認
            required_cols = ['halshareWearerName', 'halshareId', 'datetime', 'temperature']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise HTTPException(status_code=400, detail=f"Missing columns: {missing_cols}")
            
            # バッチ作成
            batch = UploadBatch(
                batch_id=batch_id,
                sensor_type=SensorType.SKIN_TEMPERATURE,
                file_name=file.filename,
                file_size=len(content),
                competition_id=competition_id,
                uploaded_by=current_admin.admin_id
            )
            db.add(batch)
            
            success_count = 0
            failed_count = 0
            
            for _, row in df.iterrows():
                try:
                    # データ抽出と正規化（クォート・スペース除去）
                    wearer_name = str(row['halshareWearerName']).strip()
                    sensor_id = str(row['halshareId']).strip()
                    datetime_str = str(row['datetime']).strip()
                    
                    # クォート除去処理
                    if sensor_id.startswith(' "') and sensor_id.endswith('"'):
                        sensor_id = sensor_id[2:-1]  # ' "値" → 値
                    elif sensor_id.startswith('"') and sensor_id.endswith('"'):
                        sensor_id = sensor_id[1:-1]   # "値" → 値
                    
                    if datetime_str.startswith(' "') and datetime_str.endswith('"'):
                        datetime_str = datetime_str[2:-1]  # ' "日時" → 日時
                    elif datetime_str.startswith('"') and datetime_str.endswith('"'):
                        datetime_str = datetime_str[1:-1]   # "日時" → 日時
                    
                    # 最終的な空白除去
                    wearer_name = wearer_name.strip()
                    sensor_id = sensor_id.strip()
                    datetime_str = datetime_str.strip()
                    
                    # 空値チェック
                    if not wearer_name or wearer_name in ['nan', 'None']:
                        raise ValueError("着用者名が空")
                    
                    if not sensor_id or sensor_id in ['nan', 'None']:
                        raise ValueError("センサーIDが空")
                    
                    if not datetime_str or datetime_str in ['nan', 'None']:
                        raise ValueError("日時が空")
                    
                    if pd.isna(row['temperature']):
                        raise ValueError("温度が空")
                    
                    # 日時パース（正規化後）
                    try:
                        parsed_datetime = pd.to_datetime(datetime_str)
                    except Exception as e:
                        raise ValueError(f"日時パースエラー: '{datetime_str}'")
                    
                    # 温度変換
                    temperature = float(row['temperature'])
                    
                    # データ保存
                    skin_data = SkinTemperatureData(
                        halshare_wearer_name=wearer_name,
                        halshare_id=sensor_id,
                        datetime=parsed_datetime,
                        temperature=temperature,
                        upload_batch_id=batch_id,
                        competition_id=competition_id
                    )
                    db.add(skin_data)
                    success_count += 1
                    
                except Exception as e:
                    failed_count += 1
            
            # バッチ情報更新
            batch.total_records = len(df)
            batch.success_records = success_count
            batch.failed_records = failed_count
            batch.status = UploadStatus.SUCCESS if failed_count == 0 else UploadStatus.PARTIAL
            
            db.commit()
            
            results.append({
                "file": file.filename,
                "batch_id": batch_id,
                "total": len(df),
                "success": success_count,
                "failed": failed_count,
                "status": batch.status.value
            })
            
        except Exception as e:
            db.rollback()
            results.append({
                "file": file.filename,
                "error": str(e),
                "status": "failed"
            })
    
    return {"results": results}

@router.post("/upload/core-temperature")
async def upload_core_temperature(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """カプセル体温データ（e-Celcius）アップロード"""
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    results = []
    
    for file in files:
        batch_id = generate_batch_id(file.filename)
        
        try:
            content = await file.read()
            encoding = detect_encoding(content)
            
            text_content = content.decode(encoding)
            lines = text_content.splitlines()
            
            # センサーIDを5行目から抽出
            sensor_ids = {}
            if len(lines) > 4:
                header_line = lines[4]
                parts = header_line.split(',')
                
                for i, part in enumerate(parts):
                    if 'Pill' in part and i + 1 < len(parts):
                        sensor_id = parts[i + 1].strip()
                        if sensor_id:
                            sensor_ids[i] = sensor_id
            
            batch = UploadBatch(
                batch_id=batch_id,
                sensor_type=SensorType.CORE_TEMPERATURE,
                file_name=file.filename,
                file_size=len(content),
                competition_id=competition_id,
                uploaded_by=current_admin.admin_id
            )
            
            success_count = 0
            failed_count = 0
            
            for line_num, line in enumerate(lines[6:], start=7):
                line = line.strip()
                if not line:
                    continue
                
                if any(msg in line.upper() for msg in ['CRITICAL', 'LOW BATTERY', 'MONITOR WAKE-UP', 'SYSTEM']):
                    continue
                    
                parts = line.split(',')
                
                if len(parts) < 15:
                    continue
                
                sensor_columns = [0, 7, 14]
                for sensor_col in sensor_columns:
                    if sensor_col in sensor_ids and sensor_col + 4 < len(parts):
                        try:
                            date_str = parts[sensor_col + 1].strip()
                            hour_str = parts[sensor_col + 2].strip()
                            temp_str = parts[sensor_col + 3].strip()
                            status_str = parts[sensor_col + 4].strip()
                            
                            if temp_str and temp_str != '---':
                                datetime_obj = pd.to_datetime(f"{date_str} {hour_str}")
                                temperature = float(temp_str)
                                
                                core_data = CoreTemperatureData(
                                    capsule_id=sensor_ids[sensor_col],
                                    monitor_id=f"monitor_{sensor_col}",
                                    datetime=datetime_obj,
                                    temperature=temperature,
                                    status=status_str,
                                    upload_batch_id=batch_id,
                                    competition_id=competition_id
                                )
                                db.add(core_data)
                                success_count += 1
                                
                        except Exception as e:
                            failed_count += 1
                            continue
            
            batch.total_records = success_count + failed_count
            batch.success_records = success_count
            batch.failed_records = failed_count
            batch.status = UploadStatus.SUCCESS if failed_count == 0 else UploadStatus.PARTIAL
            
            db.add(batch)
            db.commit()
            
            results.append({
                "file": file.filename,
                "batch_id": batch_id,
                "sensors_found": len(sensor_ids),
                "success": success_count,
                "failed": failed_count,
                "status": batch.status.value
            })
            
        except Exception as e:
            db.rollback()
            results.append({
                "file": file.filename,
                "error": str(e),
                "status": "failed"
            })
    
    return {"results": results}

@router.post("/upload/heart-rate")
async def upload_heart_rate(
    competition_id: str = Form(...),
    sensor_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """心拍データ（TCX）アップロード"""
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    results = []
    
    for file in files:
        batch_id = generate_batch_id(file.filename)
        
        try:
            content = await file.read()
            
            try:
                root = ET.fromstring(content.decode('utf-8'))
            except ET.ParseError as e:
                raise HTTPException(status_code=400, detail=f"Invalid XML format: {str(e)}")
            
            ns = {'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}
            
            batch = UploadBatch(
                batch_id=batch_id,
                sensor_type=SensorType.HEART_RATE,
                file_name=file.filename,
                file_size=len(content),
                competition_id=competition_id,
                uploaded_by=current_admin.admin_id
            )
            
            success_count = 0
            failed_count = 0
            
            trackpoints = root.findall('.//tcx:Trackpoint', ns)
            
            for trackpoint in trackpoints:
                try:
                    time_elem = trackpoint.find('tcx:Time', ns)
                    hr_elem = trackpoint.find('.//tcx:HeartRateBpm/tcx:Value', ns)
                    
                    if time_elem is not None:
                        time_str = time_elem.text
                        dt = pd.to_datetime(time_str)
                        
                        heart_rate = None
                        if hr_elem is not None:
                            heart_rate = int(hr_elem.text)
                        
                        data = HeartRateData(
                            sensor_id=sensor_id,
                            time=dt,
                            heart_rate=heart_rate,
                            upload_batch_id=batch_id,
                            competition_id=competition_id
                        )
                        db.add(data)
                        success_count += 1
                        
                except Exception as e:
                    failed_count += 1
                    continue
            
            batch.total_records = len(trackpoints)
            batch.success_records = success_count
            batch.failed_records = failed_count
            batch.status = UploadStatus.SUCCESS if failed_count == 0 else UploadStatus.PARTIAL
            
            db.add(batch)
            db.commit()
            
            results.append({
                "file": file.filename,
                "batch_id": batch_id,
                "sensor_id": sensor_id,
                "trackpoints_total": len(trackpoints),
                "success": success_count,
                "failed": failed_count,
                "status": batch.status.value
            })
            
        except Exception as e:
            db.rollback()
            results.append({
                "file": file.filename,
                "error": str(e),
                "status": "failed"
            })
    
    return {"results": results}

@router.post("/upload/wbgt", response_model=UploadResponse)
async def upload_wbgt_data(
    wbgt_file: UploadFile = File(...),
    competition_id: str = Form(...),
    overwrite: bool = Form(True),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """WBGT環境データアップロード"""
    if not wbgt_file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSVファイルのみアップロード可能です")
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
    
    csv_service = FlexibleCSVService()
    
    try:
        result = await csv_service.process_wbgt_data(
            wbgt_file=wbgt_file,
            competition_id=competition_id,
            db=db,
            overwrite=overwrite
        )
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"WBGTアップロード失敗: {str(e)}")

@router.post("/upload/mapping")
async def upload_mapping_data(
    mapping_file: UploadFile = File(...),
    competition_id: str = Form(...),
    overwrite: bool = Form(True),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """マッピングデータアップロード"""
    if not mapping_file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSVファイルのみアップロード可能です")
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
    
    csv_service = FlexibleCSVService()
    
    try:
        content = await mapping_file.read()
        file_size = len(content)
        
        await mapping_file.seek(0)
        
        result = await csv_service.process_mapping_data(
            mapping_file=mapping_file,
            competition_id=competition_id,
            db=db,
            overwrite=overwrite
        )
        
        batch_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{mapping_file.filename}"
        
        batch = UploadBatch(
            batch_id=batch_id,
            sensor_type=SensorType.OTHER,
            competition_id=competition_id,
            file_name=mapping_file.filename,
            file_size=file_size,
            total_records=result["total_records"],
            success_records=result["processed_records"],
            failed_records=result["skipped_records"],
            status=UploadStatus.SUCCESS if result["success"] else UploadStatus.PARTIAL,
            uploaded_by=current_admin.admin_id,
            notes=f"スキップ: {result['skipped_records']}件" if result["skipped_records"] > 0 else None
        )
        db.add(batch)
        db.commit()
        
        return {
            "success": result["success"],
            "message": result["message"],
            "total_records": result["total_records"],
            "processed_records": result["processed_records"],
            "skipped_records": result["skipped_records"],
            "errors": result.get("errors", []),
            "batch_id": batch_id
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"マッピングアップロード失敗: {str(e)}")

# ===== 🆕 大会記録アップロード =====

@router.post("/upload/race-records")
async def upload_race_records(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    大会記録データアップロード（簡素版）
    
    - 上書き機能削除
    - シンプルな追加のみ
    - ログから削除可能
    """
    
    # ファイル形式チェック
    for file in files:
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(
                status_code=400, 
                detail=f"CSVファイルのみアップロード可能です: {file.filename}"
            )
    
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="最低1つのCSVファイルが必要です")
    
    # 大会存在チェック
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
    
    # 大会記録処理サービス呼び出し
    csv_service = FlexibleCSVService()
    
    try:
        # ファイル情報計算
        total_file_size = 0
        file_info = []
        
        for file in files:
            content = await file.read()
            file_size = len(content)
            total_file_size += file_size
            file_info.append({"name": file.filename, "size": file_size})
            await file.seek(0)  # ファイルポインタをリセット
        
        print(f"大会記録アップロード開始: {len(files)}ファイル, 合計{total_file_size}bytes")
        
        # 大会記録処理（overwrite引数削除）
        result = await csv_service.process_race_record_data(
            race_files=files,
            competition_id=competition_id,
            db=db
        )
        
        # レスポンス情報の拡張
        result.update({
            "competition_id": competition_id,
            "competition_name": competition.name,
            "uploaded_files": file_info,
            "total_file_size": total_file_size,
            "upload_time": datetime.now().isoformat(),
            "uploaded_by": current_admin.admin_id
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        error_message = f"大会記録アップロード失敗: {str(e)}"
        print(f"❌ {error_message}")
        raise HTTPException(status_code=500, detail=error_message)

@router.get("/race-records/status")
async def get_race_records_status(
    competition_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会記録アップロード状況取得"""
    
    try:
        query = db.query(RaceRecord)
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        
        records = query.all()
        
        # 統計計算
        total_records = len(records)
        mapped_records = len([r for r in records if r.user_id is not None])
        unmapped_records = total_records - mapped_records
        
        # 大会別統計
        by_competition = {}
        for record in records:
            comp_id = record.competition_id
            if comp_id not in by_competition:
                competition = db.query(Competition).filter_by(competition_id=comp_id).first()
                by_competition[comp_id] = {
                    "competition_name": competition.name if competition else "Unknown",
                    "total_records": 0,
                    "mapped_records": 0,
                    "unmapped_records": 0,
                    "latest_upload": None
                }
            
            by_competition[comp_id]["total_records"] += 1
            if record.user_id:
                by_competition[comp_id]["mapped_records"] += 1
            else:
                by_competition[comp_id]["unmapped_records"] += 1
            
            # 🔧 修正：最新アップロード時刻（created_atがある場合）
            if hasattr(record, 'created_at') and record.created_at:
                current_latest = by_competition[comp_id]["latest_upload"]
                record_time_str = record.created_at.isoformat()  # ✅ 文字列に変換
                if current_latest is None or record_time_str > current_latest:
                    by_competition[comp_id]["latest_upload"] = record_time_str
        
        # レスポンス構築
        return {
            "success": True,
            "total_records": total_records,
            "mapped_records": mapped_records,
            "unmapped_records": unmapped_records,
            "mapping_coverage": round((mapped_records / total_records * 100), 2) if total_records > 0 else 0,
            "competitions": by_competition,
            "competition_count": len(by_competition)
        }
        
    except Exception as e:
        error_message = f"大会記録状況取得エラー: {str(e)}"
        print(f"❌ {error_message}")
        raise HTTPException(status_code=500, detail=error_message)

@router.get("/race-records/details")
async def get_race_records_details(
    competition_id: str = Query(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会記録詳細情報取得"""
    
    try:
        # 大会存在チェック
        competition = db.query(Competition).filter_by(competition_id=competition_id).first()
        if not competition:
            raise HTTPException(status_code=404, detail="Competition not found")
        
        # 大会記録取得
        records = db.query(RaceRecord).filter_by(competition_id=competition_id).all()
        
        race_details = []
        for record in records:
            # 競技時間計算
            swim_duration = None
            bike_duration = None
            run_duration = None
            total_duration = None
            
            if record.swim_start_time and record.swim_finish_time:
                swim_duration = (record.swim_finish_time - record.swim_start_time).total_seconds()
            
            if record.bike_start_time and record.bike_finish_time:
                bike_duration = (record.bike_finish_time - record.bike_start_time).total_seconds()
            
            if record.run_start_time and record.run_finish_time:
                run_duration = (record.run_finish_time - record.run_start_time).total_seconds()
            
            # 全体時間（プロパティを使用）
            if record.total_start_time and record.total_finish_time:
                total_duration = (record.total_finish_time - record.total_start_time).total_seconds()
            
            race_details.append({
                "id": record.id,
                "race_number": record.race_number,
                "user_id": record.user_id,
                "is_mapped": record.user_id is not None,
                "swim_start_time": record.swim_start_time.isoformat() if record.swim_start_time else None,
                "swim_finish_time": record.swim_finish_time.isoformat() if record.swim_finish_time else None,
                "bike_start_time": record.bike_start_time.isoformat() if record.bike_start_time else None,
                "bike_finish_time": record.bike_finish_time.isoformat() if record.bike_finish_time else None,
                "run_start_time": record.run_start_time.isoformat() if record.run_start_time else None,
                "run_finish_time": record.run_finish_time.isoformat() if record.run_finish_time else None,
                "total_start_time": record.total_start_time.isoformat() if record.total_start_time else None,
                "total_finish_time": record.total_finish_time.isoformat() if record.total_finish_time else None,
                "swim_duration_seconds": swim_duration,
                "bike_duration_seconds": bike_duration,
                "run_duration_seconds": run_duration,
                "total_duration_seconds": total_duration,
                "lap_data": record.parsed_lap_data,
                "calculated_phases": record.parsed_phases,
                "notes": record.notes,
                "created_at": record.created_at.isoformat() if hasattr(record, 'created_at') and record.created_at else None
            })
        
        return {
            "success": True,
            "competition_id": competition_id,
            "competition_name": competition.name,
            "total_records": len(records),
            "records": race_details
        }
        
    except Exception as e:
        error_message = f"大会記録詳細取得エラー: {str(e)}"
        print(f"❌ {error_message}")
        raise HTTPException(status_code=500, detail=error_message)

@router.delete("/race-records/{competition_id}")
async def delete_race_records(
    competition_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会記録削除"""
    
    try:
        # 大会存在チェック
        competition = db.query(Competition).filter_by(competition_id=competition_id).first()
        if not competition:
            raise HTTPException(status_code=404, detail="Competition not found")
        
        # 削除実行
        deleted_count = db.query(RaceRecord).filter_by(competition_id=competition_id).delete()
        db.commit()
        
        return {
            "success": True,
            "message": f"大会'{competition.name}'の記録{deleted_count}件を削除しました",
            "deleted_records": deleted_count,
            "competition_id": competition_id
        }
        
    except Exception as e:
        db.rollback()
        error_message = f"大会記録削除エラー: {str(e)}"
        print(f"❌ {error_message}")
        raise HTTPException(status_code=500, detail=error_message)

# ===== バッチ管理 =====

@router.get("/batches")
async def get_upload_batches(
    competition_id: Optional[str] = Query(None),
    sensor_type: Optional[SensorType] = Query(None),
    limit: int = Query(50, le=200),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """アップロードバッチ一覧取得"""
    
    query = db.query(UploadBatch)
    
    if competition_id:
        query = query.filter_by(competition_id=competition_id)
    
    if sensor_type:
        query = query.filter_by(sensor_type=sensor_type)
    
    batches = query.order_by(desc(UploadBatch.uploaded_at)).offset(skip).limit(limit).all()
    
    results = []
    for batch in batches:
        # 大会名取得
        competition_name = None
        if batch.competition_id:
            competition = db.query(Competition).filter_by(competition_id=batch.competition_id).first()
            competition_name = competition.name if competition else None
        
        results.append({
            "batch_id": batch.batch_id,
            "sensor_type": batch.sensor_type.value if hasattr(batch.sensor_type, 'value') else str(batch.sensor_type),
            "competition_id": batch.competition_id,
            "competition_name": competition_name,
            "file_name": batch.file_name,
            "file_size": batch.file_size,
            "total_records": batch.total_records,
            "success_records": batch.success_records,
            "failed_records": batch.failed_records,
            "status": batch.status.value if hasattr(batch.status, 'value') else str(batch.status),
            "uploaded_by": batch.uploaded_by,
            "notes": batch.notes,
            "created_at": batch.uploaded_at.isoformat() if batch.uploaded_at else None
        })
    
    return {
        "batches": results,
        "total_count": len(results),
        "has_more": len(results) == limit
    }

@router.delete("/batches/{batch_id}")
async def delete_upload_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """アップロードバッチとその関連データを削除"""
    
    try:
        # バッチ存在チェック
        batch = db.query(UploadBatch).filter_by(batch_id=batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # 関連センサーデータを削除
        deleted_counts = {}
        
        if batch.sensor_type == SensorType.SKIN_TEMPERATURE:
            deleted_counts['skin_temperature'] = db.query(SkinTemperatureData).filter_by(upload_batch_id=batch_id).delete()
        elif batch.sensor_type == SensorType.CORE_TEMPERATURE:
            deleted_counts['core_temperature'] = db.query(CoreTemperatureData).filter_by(upload_batch_id=batch_id).delete()
        elif batch.sensor_type == SensorType.HEART_RATE:
            deleted_counts['heart_rate'] = db.query(HeartRateData).filter_by(upload_batch_id=batch_id).delete()
        elif batch.sensor_type == SensorType.WBGT:
            deleted_counts['wbgt'] = db.query(WBGTData).filter_by(upload_batch_id=batch_id).delete()
        
        # バッチ自体を削除
        db.delete(batch)
        db.commit()
        
        return {
            "success": True,
            "message": f"バッチ '{batch.file_name}' とその関連データを削除しました",
            "batch_id": batch_id,
            "deleted_data_counts": deleted_counts
        }
        
    except Exception as e:
        db.rollback()
        error_message = f"バッチ削除エラー: {str(e)}"
        print(f"❌ {error_message}")
        raise HTTPException(status_code=500, detail=error_message)

# ===== マッピング状況管理 =====

@router.get("/mapping/status")
async def get_mapping_status(
    competition_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """マッピング状況取得（シンプル化版）"""
    
    query = db.query(FlexibleSensorMapping)
    if competition_id:
        query = query.filter_by(competition_id=competition_id)
    
    mappings = query.all()
    
    # 基本統計
    total_mappings = len(mappings)
    
    # センサータイプ別統計
    by_sensor_type = {}
    for sensor_type in SensorType:
        if sensor_type == SensorType.WBGT:  # 環境データはマッピング対象外
            continue
        count = len([m for m in mappings if m.sensor_type == sensor_type])
        by_sensor_type[sensor_type.value] = count
    
    # ユーザー別マッピング状況
    user_mapping_status = {}
    for mapping in mappings:
        user_id = mapping.user_id
        if user_id not in user_mapping_status:
            user_mapping_status[user_id] = {
                'skin_temperature': False,
                'core_temperature': False,
                'heart_rate': False,
                'race_record': False
            }
        
        if mapping.sensor_type.value in user_mapping_status[user_id]:
            user_mapping_status[user_id][mapping.sensor_type.value] = True
    
    # 完全マッピング済みユーザー数（3つのセンサー全てマップ済み）
    fully_mapped_users = len([
        user for user, status in user_mapping_status.items()
        if status['skin_temperature'] and status['core_temperature'] and status['heart_rate']
    ])
    
    return {
        "total_mappings": total_mappings,
        "mappings_by_sensor_type": by_sensor_type,
        "total_users_with_mappings": len(user_mapping_status),
        "fully_mapped_users": fully_mapped_users,
        "competition_id": competition_id,
        "user_mapping_details": user_mapping_status
    }

@router.get("/sensor-data/coverage")  
async def get_sensor_data_coverage(
    competition_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """センサーデータのカバレッジ統計（新機能）"""
    
    try:
        # マッピングされているセンサーIDを取得
        mapping_query = db.query(FlexibleSensorMapping)
        if competition_id:
            mapping_query = mapping_query.filter_by(competition_id=competition_id)
        
        mappings = mapping_query.all()
        
        # センサータイプ別にマッピング済みセンサーIDを分類
        mapped_skin_sensors = {m.sensor_id for m in mappings if m.sensor_type == SensorType.SKIN_TEMPERATURE}
        mapped_core_sensors = {m.sensor_id for m in mappings if m.sensor_type == SensorType.CORE_TEMPERATURE}
        mapped_heart_sensors = {m.sensor_id for m in mappings if m.sensor_type == SensorType.HEART_RATE}
        
        # 実際のセンサーデータから全センサーIDを取得
        skin_query = db.query(SkinTemperatureData.halshare_id).distinct()
        core_query = db.query(CoreTemperatureData.capsule_id).distinct()
        heart_query = db.query(HeartRateData.sensor_id).distinct()
        
        if competition_id:
            skin_query = skin_query.filter_by(competition_id=competition_id)
            core_query = core_query.filter_by(competition_id=competition_id)  
            heart_query = heart_query.filter_by(competition_id=competition_id)
        
        all_skin_sensors = {row[0] for row in skin_query.all()}
        all_core_sensors = {row[0] for row in core_query.all()}
        all_heart_sensors = {row[0] for row in heart_query.all()}
        
        # マッピング済み・未マッピングの集計
        def calculate_coverage(all_sensors, mapped_sensors):
            total = len(all_sensors)
            mapped = len(all_sensors & mapped_sensors)  # 交集合
            unmapped = total - mapped
            coverage_rate = round((mapped / max(total, 1)) * 100, 2)
            return {
                "total_sensors": total,
                "mapped_sensors": mapped,
                "unmapped_sensors": unmapped,
                "coverage_rate": coverage_rate,
                "unmapped_sensor_ids": list(all_sensors - mapped_sensors)
            }
        
        return {
            "competition_id": competition_id,
            "skin_temperature": calculate_coverage(all_skin_sensors, mapped_skin_sensors),
            "core_temperature": calculate_coverage(all_core_sensors, mapped_core_sensors),
            "heart_rate": calculate_coverage(all_heart_sensors, mapped_heart_sensors),
            "summary": {
                "total_unique_sensors": len(all_skin_sensors) + len(all_core_sensors) + len(all_heart_sensors),
                "total_mapped_sensors": len(mapped_skin_sensors) + len(mapped_core_sensors) + len(mapped_heart_sensors),
                "overall_coverage_rate": round((
                    (len(mapped_skin_sensors) + len(mapped_core_sensors) + len(mapped_heart_sensors)) / 
                    max(len(all_skin_sensors) + len(all_core_sensors) + len(all_heart_sensors), 1)
                ) * 100, 2)
            }
        }
        
    except Exception as e:
        error_message = f"センサーデータカバレッジ取得エラー: {str(e)}"
        print(f"❌ {error_message}")
        raise HTTPException(status_code=500, detail=error_message)


# ===== 未マッピングデータサマリー =====

@router.get("/unmapped-data-summary")
async def get_unmapped_data_summary(
    competition_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """未マッピングデータサマリー取得"""
    
    try:
        summary = {}
        
        # 体表温データ
        skin_query = db.query(SkinTemperatureData).filter(SkinTemperatureData.mapped_user_id.is_(None))
        if competition_id:
            skin_query = skin_query.filter_by(competition_id=competition_id)
        
        skin_count = skin_query.count()
        unique_skin_sensors = skin_query.with_entities(SkinTemperatureData.halshare_id).distinct().count()
        
        summary['skin_temperature'] = {
            'unmapped_records': skin_count,
            'unique_sensors': unique_skin_sensors
        }
        
        # カプセル体温データ
        core_query = db.query(CoreTemperatureData).filter(CoreTemperatureData.mapped_user_id.is_(None))
        if competition_id:
            core_query = core_query.filter_by(competition_id=competition_id)
        
        core_count = core_query.count()
        unique_core_sensors = core_query.with_entities(CoreTemperatureData.capsule_id).distinct().count()
        
        summary['core_temperature'] = {
            'unmapped_records': core_count,
            'unique_sensors': unique_core_sensors
        }
        
        # 心拍データ
        heart_query = db.query(HeartRateData).filter(HeartRateData.mapped_user_id.is_(None))
        if competition_id:
            heart_query = heart_query.filter_by(competition_id=competition_id)
        
        heart_count = heart_query.count()
        unique_heart_sensors = heart_query.with_entities(HeartRateData.sensor_id).distinct().count()
        
        summary['heart_rate'] = {
            'unmapped_records': heart_count,
            'unique_sensors': unique_heart_sensors
        }
        
        # 大会記録
        race_query = db.query(RaceRecord).filter(RaceRecord.user_id.is_(None))
        if competition_id:
            race_query = race_query.filter_by(competition_id=competition_id)
        
        race_count = race_query.count()
        
        summary['race_records'] = {
            'unmapped_records': race_count
        }
        
        # 全体統計
        total_unmapped = skin_count + core_count + heart_count + race_count
        total_sensors = unique_skin_sensors + unique_core_sensors + unique_heart_sensors
        
        return {
            "competition_id": competition_id,
            "summary": summary,
            "totals": {
                "total_unmapped_records": total_unmapped,
                "total_unique_sensors": total_sensors,
                "unmapped_race_records": race_count
            }
        }
        
    except Exception as e:
        error_message = f"未マッピングデータサマリー取得エラー: {str(e)}"
        print(f"❌ {error_message}")
        raise HTTPException(status_code=500, detail=error_message)


@router.post("/mapping/apply")
async def apply_sensor_mapping(
    competition_id: str = Form(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    🆕 拡張マッピング適用（センサーデータ + 大会記録）
    
    処理内容:
    1. センサーデータマッピング適用（既存機能）
    2. 🆕 大会記録マッピング適用（改善版）
    """
    
    try:
        # 大会存在チェック
        competition = db.query(Competition).filter_by(competition_id=competition_id).first()
        if not competition:
            raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
        
        print(f"🚀 拡張マッピング適用開始: 大会 '{competition.name}' ({competition_id})")
        
        # === 1. 既存のセンサーデータマッピング適用 ===
        sensor_results = await apply_existing_sensor_mapping(competition_id, db)
        
        # === 2. 🆕 大会記録マッピング適用（改善版） ===
        race_results = await apply_race_number_mapping(competition_id, db)
        
        # 結果の統合
        total_applied = sensor_results.get("applied_count", 0) + race_results.get("applied_race_records", 0)
        
        success_message = f"マッピング適用完了 - "
        details = []
        
        if sensor_results.get("applied_count", 0) > 0:
            details.append(f"センサーデータ: {sensor_results['applied_count']}件")
        
        if race_results.get("applied_race_records", 0) > 0:
            details.append(f"大会記録: {race_results['applied_race_records']}件")
        
        success_message += ", ".join(details) if details else "適用対象なし"
        
        return {
            "success": True,
            "message": success_message,
            "total_applied": total_applied,
            "sensor_mapping_result": sensor_results,
            "race_mapping_result": race_results,
            "competition_id": competition_id,
            "competition_name": competition.name
        }
        
    except Exception as e:
        db.rollback()
        error_message = f"拡張マッピング適用エラー: {str(e)}"
        print(f"❌ {error_message}")
        raise HTTPException(status_code=500, detail=error_message)


async def apply_existing_sensor_mapping(competition_id: str, db: Session) -> dict:
    """センサーデータマッピング適用処理（既存機能）"""
    
    try:
        applied_count = 0
        
        # 体表温データマッピング適用
        skin_mappings = db.query(FlexibleSensorMapping).filter_by(
            competition_id=competition_id,
            sensor_type=SensorType.SKIN_TEMPERATURE
        ).all()
        
        for mapping in skin_mappings:
            updated = db.query(SkinTemperatureData).filter_by(
                halshare_id=mapping.sensor_id,
                competition_id=competition_id,
                mapped_user_id=None
            ).update({"mapped_user_id": mapping.user_id})
            applied_count += updated
        
        # カプセル体温データマッピング適用
        core_mappings = db.query(FlexibleSensorMapping).filter_by(
            competition_id=competition_id,
            sensor_type=SensorType.CORE_TEMPERATURE
        ).all()
        
        for mapping in core_mappings:
            updated = db.query(CoreTemperatureData).filter_by(
                capsule_id=mapping.sensor_id,
                competition_id=competition_id,
                mapped_user_id=None
            ).update({"mapped_user_id": mapping.user_id})
            applied_count += updated
        
        # 心拍データマッピング適用
        heart_mappings = db.query(FlexibleSensorMapping).filter_by(
            competition_id=competition_id,
            sensor_type=SensorType.HEART_RATE
        ).all()
        
        for mapping in heart_mappings:
            updated = db.query(HeartRateData).filter_by(
                sensor_id=mapping.sensor_id,
                competition_id=competition_id,
                mapped_user_id=None
            ).update({"mapped_user_id": mapping.user_id})
            applied_count += updated
        
        db.commit()
        
        return {
            "success": True,
            "applied_count": applied_count,
            "message": f"センサーデータマッピング適用完了: {applied_count}件"
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "applied_count": 0,
            "message": f"センサーマッピング適用エラー: {str(e)}"
        }


async def apply_race_number_mapping(competition_id: str, db: Session) -> dict:
    """🆕 大会記録マッピング適用処理（改善版）"""
    
    try:
        from app.models.competition import RaceRecord
        
        # 🆕 RACE_RECORDタイプのマッピングを取得
        race_mappings = db.query(FlexibleSensorMapping).filter_by(
            competition_id=competition_id,
            sensor_type=SensorType.RACE_RECORD
        ).all()
        
        print(f"🏃 大会記録マッピング数: {len(race_mappings)}")
        
        applied_count = 0
        errors = []
        
        for mapping in race_mappings:
            race_number = mapping.sensor_id  # 🔄 sensor_idから取得
            user_id = mapping.user_id
            
            # 対応する大会記録を検索・更新
            updated = db.query(RaceRecord).filter_by(
                competition_id=competition_id,
                race_number=race_number,
                user_id=None  # 未マッピングのもののみ
            ).update({"user_id": user_id})
            
            applied_count += updated
            if updated > 0:
                print(f"✅ 大会記録マッピング適用: race_number={race_number} → user_id={user_id} ({updated}件)")
        
        db.commit()
        
        return {
            "success": True,
            "applied_race_records": applied_count,
            "total_mappings": len(race_mappings),
            "message": f"大会記録マッピング適用完了: {applied_count}件",
            "errors": errors
        }
        
    except Exception as e:
        db.rollback()
        error_message = f"大会記録マッピング適用エラー: {str(e)}"
        print(f"❌ {error_message}")
        return {
            "success": False,
            "applied_race_records": 0,
            "errors": [error_message]
        }

# ===== 新しいユーザー管理エンドポイント =====

@router.post("/users/bulk-create")
async def bulk_create_users(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """CSVファイルからユーザーを一括作成（仕様書1.1対応）"""
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400, 
            detail="CSVファイルのみサポートされています"
        )
    
    try:
        # CSVファイル読み込み
        content = await file.read()
        encoding = detect_encoding(content)
        
        try:
            df = pd.read_csv(io.BytesIO(content), encoding=encoding, header=None)
        except UnicodeDecodeError:
            # フォールバック: UTF-8とShift-JISを試す
            try:
                df = pd.read_csv(io.BytesIO(content), encoding='utf-8', header=None)
            except Exception:
                df = pd.read_csv(io.BytesIO(content), encoding='shift_jis', header=None)
        
        # 列数チェック（氏名、メールアドレスの2列）
        if df.shape[1] < 2:
            raise HTTPException(
                status_code=400,
                detail="CSVファイルは2列（氏名、メールアドレス）が必要です"
            )
        
        # 列名を設定
        df.columns = ['name', 'email'] + [f'col_{i}' for i in range(2, df.shape[1])]
        
        created_users = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                name = str(row['name']).strip()
                email = str(row['email']).strip()
                
                # 入力値検証
                if pd.isna(row['name']) or not name or name == 'nan':
                    errors.append({
                        "row": index + 1,
                        "error": "氏名が空です"
                    })
                    continue
                
                if pd.isna(row['email']) or not email or email == 'nan':
                    errors.append({
                        "row": index + 1,
                        "error": "メールアドレスが空です"
                    })
                    continue
                
                # 簡単なメールアドレス形式チェック
                if '@' not in email or '.' not in email.split('@')[-1]:
                    errors.append({
                        "row": index + 1,
                        "error": f"無効なメールアドレス形式: {email}"
                    })
                    continue
                
                # 重複チェック（既存ユーザー）
                existing_user = db.query(User).filter(
                    (User.email == email)
                ).first()
                
                if existing_user:
                    errors.append({
                        "row": index + 1,
                        "error": f"メールアドレスが既に登録されています: {email}"
                    })
                    continue
                
                # ユニークなuser_idを生成（重複チェック）
                max_attempts = 10
                user_id = None
                for _ in range(max_attempts):
                    candidate_id = generate_user_id()
                    if not db.query(User).filter_by(user_id=candidate_id).first():
                        user_id = candidate_id
                        break
                
                if not user_id:
                    errors.append({
                        "row": index + 1,
                        "error": "ユニークなユーザーIDを生成できませんでした"
                    })
                    continue
                
                # パスワード生成
                password = generate_password()
                
                # ユーザー作成
                new_user = User(
                    user_id=user_id,
                    username=user_id,  # usernameはuser_idと同じに設定
                    full_name=name,
                    email=email,
                    is_active=True,
                    hashed_password=get_password_hash(password),
                    created_at=datetime.utcnow()
                )
                
                db.add(new_user)
                db.flush()  # IDを取得するために一時的にコミット
                
                created_users.append({
                    "name": name,
                    "email": email,
                    "user_id": user_id,
                    "password": password
                })
                
            except Exception as e:
                errors.append({
                    "row": index + 1,
                    "error": f"処理エラー: {str(e)}"
                })
        
        # 最終コミット
        db.commit()
        
        return {
            "message": f"{len(created_users)}人のユーザーを作成しました",
            "created_users": created_users,
            "errors": errors,
            "summary": {
                "total_rows": len(df),
                "created": len(created_users),
                "failed": len(errors)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()  # エラー時はロールバック
        raise HTTPException(
            status_code=500,
            detail=f"CSV処理エラー: {str(e)}"
        )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """ユーザーを削除（JOIN修正版）"""
    
    # ユーザー存在チェック
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="ユーザーが見つかりません"
        )
    
    try:
        # JOINベースで関連データ数を確認
        skin_temp_count = get_user_sensor_data_count(db, user_id, "skin_temperature")
        core_temp_count = get_user_sensor_data_count(db, user_id, "core_temperature")
        heart_rate_count = get_user_sensor_data_count(db, user_id, "heart_rate")
        
        race_records_count = db.query(RaceRecord).filter_by(user_id=user_id).count()
        mapping_count = db.query(FlexibleSensorMapping).filter_by(user_id=user_id).count()
        
        # マッピングを削除（センサーデータは残す - 正規化設計）
        db.query(FlexibleSensorMapping).filter_by(user_id=user_id).delete()
        
        # 大会記録は削除（user_idと直接関連）
        if race_records_count > 0:
            db.query(RaceRecord).filter_by(user_id=user_id).delete()
        
        # ユーザー削除
        user_name = user.full_name or user.username
        db.delete(user)
        db.commit()
        
        return {
            "message": f"ユーザー '{user_name}' (ID: {user_id}) を削除しました",
            "deleted_data": {
                "race_records": race_records_count,
                "mappings": mapping_count
            },
            "note": f"センサーデータ {skin_temp_count + core_temp_count + heart_rate_count} 件は保持されます（正規化設計）"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"ユーザー削除エラー: {str(e)}"
        )

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """ユーザーのパスワードをリセット（仕様書5.1対応）"""
    
    # ユーザー存在チェック
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="ユーザーが見つかりません"
        )
    
    try:
        # 新しいパスワードを生成
        new_password = generate_password()
        
        # パスワードハッシュを更新
        user.hashed_password = get_password_hash(new_password)
        
        # updated_atが存在する場合は更新
        if hasattr(user, 'updated_at'):
            user.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": f"ユーザー '{user.full_name or user.username}' のパスワードをリセットしました",
            "user_id": user_id,
            "new_password": new_password,
            "note": "新しいパスワードをユーザーに安全に伝達してください"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"パスワードリセットエラー: {str(e)}"
        )

@router.get("/users/{user_id}/data-summary")
async def get_user_data_summary(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """ユーザーのデータサマリー取得（JOINベース修正版）"""
    
    # ユーザー存在チェック
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    try:
        # JOINクエリでセンサーデータ統計を取得
        skin_temp_count = _get_user_sensor_data_count_helper(db, user_id, "skin_temperature")
        core_temp_count = _get_user_sensor_data_count_helper(db, user_id, "core_temperature") 
        heart_rate_count = _get_user_sensor_data_count_helper(db, user_id, "heart_rate")
        
        # 参加大会一覧
        race_records = db.query(RaceRecord).filter_by(user_id=user_id).all()
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
                    "status": "completed" if record.run_finish_time else "incomplete"
                })
        
        return {
            "user_id": user_id,
            "skin_temperature_records": skin_temp_count,
            "core_temperature_records": core_temp_count,
            "heart_rate_records": heart_rate_count,
            "total_competitions": len(competitions_data),
            "competitions": competitions_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"データサマリー取得エラー: {str(e)}"
        )

# 🔧 センサーデータ取得用のヘルパー関数
def _get_user_sensor_data_count_helper(db: Session, user_id: str, sensor_type: str, competition_id: str = None) -> int:
    """JOINクエリでユーザーのセンサーデータ数を取得"""
    
    # マッピング取得
    mapping_query = db.query(FlexibleSensorMapping).filter_by(
        user_id=user_id,
        sensor_type=sensor_type
    )
    if competition_id:
        mapping_query = mapping_query.filter_by(competition_id=competition_id)
    
    mappings = mapping_query.all()
    if not mappings:
        return 0
    
    sensor_ids = [m.sensor_id for m in mappings]
    
    # センサータイプ別データ数取得
    if sensor_type == "skin_temperature":
        return db.query(SkinTemperatureData).filter(
            SkinTemperatureData.halshare_id.in_(sensor_ids)
        ).count() if sensor_ids else 0
        
    elif sensor_type == "core_temperature":
        return db.query(CoreTemperatureData).filter(
            CoreTemperatureData.capsule_id.in_(sensor_ids)
        ).count() if sensor_ids else 0
        
    elif sensor_type == "heart_rate":
        return db.query(HeartRateData).filter(
            HeartRateData.sensor_id.in_(sensor_ids)
        ).count() if sensor_ids else 0
    
    return 0

def _get_user_sensor_data_helper(db: Session, user_id: str, sensor_type: str, competition_id: str = None) -> list:
    """JOINクエリでユーザーのセンサーデータを取得"""
    
    # マッピング取得
    mapping_query = db.query(FlexibleSensorMapping).filter_by(
        user_id=user_id,
        sensor_type=sensor_type
    )
    if competition_id:
        mapping_query = mapping_query.filter_by(competition_id=competition_id)
    
    mappings = mapping_query.all()
    if not mappings:
        return []
    
    sensor_ids = [m.sensor_id for m in mappings]
    
    # センサータイプ別データ取得
    if sensor_type == "skin_temperature":
        query = db.query(SkinTemperatureData).filter(
            SkinTemperatureData.halshare_id.in_(sensor_ids)
        )
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        return query.order_by(SkinTemperatureData.datetime).all()
        
    elif sensor_type == "core_temperature":
        query = db.query(CoreTemperatureData).filter(
            CoreTemperatureData.capsule_id.in_(sensor_ids)
        )
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        return query.order_by(CoreTemperatureData.datetime).all()
        
    elif sensor_type == "heart_rate":
        query = db.query(HeartRateData).filter(
            HeartRateData.sensor_id.in_(sensor_ids)
        )
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        return query.order_by(HeartRateData.time).all()
    
    return []