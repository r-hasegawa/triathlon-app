"""
app/routers/admin.py (統合版 - admin/upload.py の内容も含む)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, date
import pandas as pd
import xml.etree.ElementTree as ET
import io
import re

from app.database import get_db
from app.models.user import User, AdminUser
from app.models.competition import Competition
from app.models.flexible_sensor_data import RawSensorData, FlexibleSensorMapping
from app.schemas.user import UserCreate, UserUpdate, UserResponse, AdminResponse
from app.utils.dependencies import get_current_admin
from app.utils.security import get_password_hash

router = APIRouter(prefix="/admin", tags=["admin"])

# === 管理者情報取得 ===
@router.get("/me", response_model=AdminResponse)
async def get_admin_info(current_admin: AdminUser = Depends(get_current_admin)):
    return current_admin

# === ユーザー管理 ===
@router.get("/users")
async def get_users_with_stats(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """ユーザー一覧取得"""
    
    query = db.query(User)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.user_id.like(search_term)) |
            (User.username.like(search_term)) |
            (User.full_name.like(search_term))
        )
    
    users = query.offset(skip).limit(limit).all()
    
    # 新システムでの統計情報取得
    users_with_stats = []
    for user in users:
        # 新システムでのセンサー数取得
        sensor_count = db.query(func.count(FlexibleSensorMapping.id))\
                        .filter_by(user_id=user.user_id, is_active=True)\
                        .scalar() or 0
        
        # 最新データ日時取得
        last_data = db.query(func.max(RawSensorData.timestamp))\
                    .filter_by(mapped_user_id=user.user_id)\
                    .scalar()
        
        user_data = {
            "id": user.id,
            "user_id": user.user_id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "sensor_count": sensor_count,
            "last_data_at": last_data.isoformat() if last_data else None
        }
        users_with_stats.append(user_data)
    
    return users_with_stats

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """ユーザー作成"""
    existing_user = db.query(User).filter(
        (User.user_id == user_data.user_id) | 
        (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID or username already exists"
        )
    
    user = User(
        user_id=user_data.user_id,
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """ユーザー更新"""
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    for field, value in user_data.dict(exclude_unset=True).items():
        if field == "password" and value:
            setattr(user, "hashed_password", get_password_hash(value))
        elif hasattr(user, field):
            setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user

# === 大会管理 ===
@router.get("/competitions")
async def get_competitions_admin(
    include_inactive: bool = Query(False),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """大会一覧取得（管理者用）"""
    
    query = db.query(Competition)
    
    if not include_inactive:
        query = query.filter(Competition.is_active == True)
    
    competitions = query.order_by(Competition.created_at.desc()).all()
    
    # 参加者数やデータ数も含める
    competitions_with_stats = []
    for comp in competitions:
        participant_count = db.query(func.count(FlexibleSensorMapping.user_id.distinct()))\
                             .filter_by(competition_id=comp.competition_id, is_active=True)\
                             .scalar() or 0
        
        sensor_data_count = db.query(func.count(RawSensorData.id))\
                             .filter_by(competition_id=comp.competition_id)\
                             .scalar() or 0
        
        competitions_with_stats.append({
            "competition_id": comp.competition_id,
            "name": comp.name,
            "date": comp.date,
            "location": comp.location,
            "description": comp.description,
            "is_active": comp.is_active,
            "created_at": comp.created_at,
            "participant_count": participant_count,
            "sensor_data_count": sensor_data_count
        })
    
    return {
        "competitions": competitions_with_stats,
        "total": len(competitions_with_stats)
    }

@router.post("/competitions")
async def create_competition(
    name: str = Form(...),
    date: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """大会作成"""
    
    # 大会名の重複チェック
    existing = db.query(Competition).filter_by(name=name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Competition with name '{name}' already exists"
        )
    
    # 大会IDを生成
    competition_id = f"comp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 日付の変換
    competition_date = None
    if date:
        try:
            competition_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    
    competition = Competition(
        competition_id=competition_id,
        name=name,
        date=competition_date,
        location=location,
        description=description
    )
    
    db.add(competition)
    db.commit()
    db.refresh(competition)
    
    return {
        "competition_id": competition.competition_id,
        "name": competition.name,
        "date": competition.date,
        "location": competition.location,
        "description": competition.description,
        "message": "Competition created successfully"
    }

@router.delete("/competitions/{competition_id}")
async def delete_competition(
    competition_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """大会削除"""
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competition not found"
        )
    
    # 関連データも削除
    db.query(RawSensorData).filter_by(competition_id=competition_id).delete()
    db.query(FlexibleSensorMapping).filter_by(competition_id=competition_id).delete()
    
    db.delete(competition)
    db.commit()
    
    return {
        "message": f"Competition '{competition.name}' and all related data deleted successfully"
    }

# === システム統計 ===
@router.get("/stats")
async def get_system_stats(
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """システム統計情報取得（新システム版）"""
    
    try:
        # 基本統計（確実に存在するテーブルのみ）
        stats = {
            "total_users": db.query(func.count(User.id)).scalar() or 0,
            "active_users": db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0,
            "total_competitions": db.query(func.count(Competition.id)).scalar() or 0,
            "active_competitions": db.query(func.count(Competition.id)).filter(Competition.is_active == True).scalar() or 0,
        }
        
        # センサーデータ統計（テーブル存在チェック付き）
        try:
            # RawSensorDataテーブルが存在するかチェック
            total_sensor_records = db.query(func.count(RawSensorData.id)).scalar() or 0
            mapped_sensor_records = db.query(func.count(RawSensorData.id))\
                                      .filter(RawSensorData.mapping_status == "mapped")\
                                      .scalar() or 0
            unmapped_sensor_records = db.query(func.count(RawSensorData.id))\
                                        .filter(RawSensorData.mapping_status == "unmapped")\
                                        .scalar() or 0
            
            stats.update({
                "total_sensor_records": total_sensor_records,
                "mapped_sensor_records": mapped_sensor_records,
                "unmapped_sensor_records": unmapped_sensor_records
            })
        except Exception as sensor_error:
            print(f"Sensor data tables not available: {sensor_error}")
            # センサーデータテーブルが存在しない場合はデフォルト値
            stats.update({
                "total_sensor_records": 0,
                "mapped_sensor_records": 0,
                "unmapped_sensor_records": 0
            })
        
        return stats
        
    except Exception as e:
        print(f"Error in get_system_stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )

# === 🆕 新システム専用エンドポイント ===
@router.get("/unmapped-data-summary")
async def get_unmapped_data_summary_admin(
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """未マッピングデータサマリー（管理者用）"""
    
    try:
        # FlexibleCSVServiceが存在するかチェック
        try:
            from app.services.flexible_csv_service import FlexibleCSVService
            csv_service = FlexibleCSVService()
            return csv_service.get_unmapped_data_summary(db)
        except ImportError:
            # サービスクラスが存在しない場合は基本的なサマリーを返す
            try:
                unmapped_count = db.query(func.count(RawSensorData.id))\
                                  .filter(RawSensorData.mapping_status == "unmapped")\
                                  .scalar() or 0
                
                return {
                    "total_unmapped_records": unmapped_count,
                    "by_sensor_type": {},
                    "competition_id": None
                }
            except Exception:
                # RawSensorDataテーブルも存在しない場合
                return {
                    "total_unmapped_records": 0,
                    "by_sensor_type": {},
                    "competition_id": None
                }
        
    except Exception as e:
        print(f"Error in get_unmapped_data_summary: {e}")
        # エラーが発生してもダッシュボードを表示できるよう、空のデータを返す
        return {
            "total_unmapped_records": 0,
            "by_sensor_type": {},
            "competition_id": None
        }

# === 🔧 アップロード機能（旧admin/upload.pyから統合） ===

def generate_batch_id(filename: str) -> str:
    """バッチIDを生成"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{filename}"

# === 体表温データアップロード ===
@router.post("/upload/skin-temperature")
async def upload_skin_temperature(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """体表温データ（halshare）を複数ファイル同時アップロード"""
    
    # 大会存在確認
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    results = []
    
    for file in files:
        batch_id = generate_batch_id(file.filename or "unknown")
        
        try:
            # ファイル読み取り
            content = await file.read()
            df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
            
            success_count = 0
            failed_count = 0
            
            # データ処理
            for _, row in df.iterrows():
                try:
                    # データクリーニング
                    halshare_id = str(row['halshareId']).strip().strip('"')
                    datetime_str = str(row['datetime']).strip().strip('"')
                    
                    # 日時パース
                    dt = datetime.strptime(datetime_str, "%Y/%m/%d %H:%M:%S")
                    
                    # RawSensorDataとして保存
                    data = RawSensorData(
                        sensor_id=halshare_id,
                        sensor_type="skin_temperature",
                        timestamp=dt,
                        temperature_value=float(row['temperature']),
                        competition_id=competition_id,
                        batch_id=batch_id,
                        raw_data=row.to_json(),
                        mapping_status="unmapped"
                    )
                    
                    db.add(data)
                    success_count += 1
                    
                except Exception as row_error:
                    print(f"Row processing error: {row_error}")
                    failed_count += 1
                    continue
            
            db.commit()
            
            results.append({
                "file_name": file.filename,
                "batch_id": batch_id,
                "success_count": success_count,
                "failed_count": failed_count,
                "status": "completed"
            })
            
        except Exception as file_error:
            print(f"File processing error: {file_error}")
            results.append({
                "file_name": file.filename,
                "batch_id": batch_id,
                "error": str(file_error),
                "status": "failed"
            })
    
    return {"results": results}

# === コア体温データアップロード ===
@router.post("/upload/core-temperature")
async def upload_core_temperature(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """コア体温データ（e-Celcius）を複数ファイル同時アップロード"""
    
    # 大会存在確認
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    results = []
    
    for file in files:
        batch_id = generate_batch_id(file.filename or "unknown")
        
        try:
            # ファイル読み取り
            content = await file.read()
            df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
            
            success_count = 0
            failed_count = 0
            
            # データ処理
            for _, row in df.iterrows():
                try:
                    # 日時パース
                    dt = datetime.strptime(str(row['datetime']), "%Y/%m/%d %H:%M:%S")
                    
                    # RawSensorDataとして保存
                    data = RawSensorData(
                        sensor_id=str(row['capsule_id']),
                        sensor_type="core_temperature",
                        timestamp=dt,
                        temperature_value=float(row['temperature']),
                        competition_id=competition_id,
                        batch_id=batch_id,
                        raw_data=row.to_json(),
                        mapping_status="unmapped"
                    )
                    
                    db.add(data)
                    success_count += 1
                    
                except Exception as row_error:
                    print(f"Row processing error: {row_error}")
                    failed_count += 1
                    continue
            
            db.commit()
            
            results.append({
                "file_name": file.filename,
                "batch_id": batch_id,
                "success_count": success_count,
                "failed_count": failed_count,
                "status": "completed"
            })
            
        except Exception as file_error:
            print(f"File processing error: {file_error}")
            results.append({
                "file_name": file.filename,
                "batch_id": batch_id,
                "error": str(file_error),
                "status": "failed"
            })
    
    return {"results": results}

# === 心拍データアップロード ===
@router.post("/upload/heart-rate")
async def upload_heart_rate(
    competition_id: str = Form(...),
    sensor_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """心拍データ（TCX）を複数ファイル同時アップロード"""
    
    # 大会存在確認
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    results = []
    
    for file in files:
        batch_id = generate_batch_id(file.filename or "unknown")
        
        try:
            # ファイル読み取り
            content = await file.read()
            
            # TCXファイル解析
            root = ET.fromstring(content.decode('utf-8'))
            
            success_count = 0
            failed_count = 0
            
            # TCXデータ処理
            for trackpoint in root.findall(".//Trackpoint", {"": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}):
                try:
                    time_elem = trackpoint.find("Time", {"": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"})
                    hr_elem = trackpoint.find(".//HeartRateBpm/Value", {"": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"})
                    
                    if time_elem is not None and hr_elem is not None:
                        # 日時パース
                        dt = datetime.fromisoformat(time_elem.text.replace('Z', '+00:00'))
                        
                        # RawSensorDataとして保存
                        data = RawSensorData(
                            sensor_id=sensor_id,
                            sensor_type="heart_rate",
                            timestamp=dt,
                            heart_rate_value=int(hr_elem.text),
                            competition_id=competition_id,
                            batch_id=batch_id,
                            raw_data=ET.tostring(trackpoint, encoding='unicode'),
                            mapping_status="unmapped"
                        )
                        
                        db.add(data)
                        success_count += 1
                    
                except Exception as row_error:
                    print(f"Trackpoint processing error: {row_error}")
                    failed_count += 1
                    continue
            
            db.commit()
            
            results.append({
                "file_name": file.filename,
                "batch_id": batch_id,
                "success_count": success_count,
                "failed_count": failed_count,
                "status": "completed"
            })
            
        except Exception as file_error:
            print(f"File processing error: {file_error}")
            results.append({
                "file_name": file.filename,
                "batch_id": batch_id,
                "error": str(file_error),
                "status": "failed"
            })
    
    return {"results": results}

# === WBGT環境データアップロード ===
@router.post("/upload/wbgt")
async def upload_wbgt(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """WBGT環境データアップロード"""
    
    # 大会存在確認
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    results = []
    
    for file in files:
        batch_id = generate_batch_id(file.filename or "unknown")
        
        try:
            # ファイル読み取り
            content = await file.read()
            df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
            
            success_count = 0
            failed_count = 0
            
            # データ処理
            for _, row in df.iterrows():
                try:
                    # 日時パース
                    dt = datetime.strptime(str(row['datetime']), "%Y/%m/%d %H:%M:%S")
                    
                    # RawSensorDataとして保存
                    data = RawSensorData(
                        sensor_id="wbgt_sensor",
                        sensor_type="wbgt",
                        timestamp=dt,
                        wbgt_value=float(row['wbgt']),
                        competition_id=competition_id,
                        batch_id=batch_id,
                        raw_data=row.to_json(),
                        mapping_status="mapped"  # WBGTは環境データなので自動マッピング
                    )
                    
                    db.add(data)
                    success_count += 1
                    
                except Exception as row_error:
                    print(f"Row processing error: {row_error}")
                    failed_count += 1
                    continue
            
            db.commit()
            
            results.append({
                "file_name": file.filename,
                "batch_id": batch_id,
                "success_count": success_count,
                "failed_count": failed_count,
                "status": "completed"
            })
            
        except Exception as file_error:
            print(f"File processing error: {file_error}")
            results.append({
                "file_name": file.filename,
                "batch_id": batch_id,
                "error": str(file_error),
                "status": "failed"
            })
    
    return {"results": results}

# === マッピングデータアップロード ===
@router.post("/upload/mapping")
async def upload_mapping(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """マッピングデータアップロード"""
    
    # 大会存在確認
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    results = []
    
    for file in files:
        try:
            # ファイル読み取り
            content = await file.read()
            df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
            
            success_count = 0
            failed_count = 0
            
            # マッピングデータ処理
            for _, row in df.iterrows():
                try:
                    user_id = str(row['user_id'])
                    
                    # ユーザー存在確認
                    user = db.query(User).filter_by(user_id=user_id).first()
                    if not user:
                        print(f"User not found: {user_id}")
                        failed_count += 1
                        continue
                    
                    # 各センサーIDのマッピング作成
                    sensor_mappings = [
                        ('skin_temperature_sensor_id', 'skin_temperature'),
                        ('core_temperature_sensor_id', 'core_temperature'),
                        ('heart_rate_sensor_id', 'heart_rate')
                    ]
                    
                    for csv_column, sensor_type in sensor_mappings:
                        if csv_column in row and pd.notna(row[csv_column]):
                            sensor_id = str(row[csv_column])
                            
                            # 既存マッピング確認
                            existing = db.query(FlexibleSensorMapping).filter_by(
                                competition_id=competition_id,
                                sensor_id=sensor_id,
                                sensor_type=sensor_type
                            ).first()
                            
                            if not existing:
                                mapping = FlexibleSensorMapping(
                                    competition_id=competition_id,
                                    user_id=user_id,
                                    sensor_id=sensor_id,
                                    sensor_type=sensor_type
                                )
                                db.add(mapping)
                    
                    # 該当するRawSensorDataのmapping_statusを更新
                    db.query(RawSensorData).filter(
                        RawSensorData.competition_id == competition_id,
                        RawSensorData.sensor_id.in_([
                            str(row.get('skin_temperature_sensor_id', '')),
                            str(row.get('core_temperature_sensor_id', '')),
                            str(row.get('heart_rate_sensor_id', ''))
                        ])
                    ).update(
                        {
                            "mapping_status": "mapped",
                            "mapped_user_id": user_id
                        },
                        synchronize_session=False
                    )
                    
                    success_count += 1
                    
                except Exception as row_error:
                    print(f"Mapping row processing error: {row_error}")
                    failed_count += 1
                    continue
            
            db.commit()
            
            results.append({
                "file_name": file.filename,
                "success_count": success_count,
                "failed_count": failed_count,
                "status": "completed"
            })
            
        except Exception as file_error:
            print(f"Mapping file processing error: {file_error}")
            results.append({
                "file_name": file.filename,
                "error": str(file_error),
                "status": "failed"
            })
    
    return {"results": results}

# === 📋 バッチ管理機能 ===
@router.get("/upload/batches")
async def get_upload_batches(
    competition_id: Optional[str] = Query(None),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """アップロードバッチ一覧取得"""
    
    try:
        # RawSensorDataからバッチ情報を取得
        query = db.query(RawSensorData.batch_id, 
                        RawSensorData.sensor_type, 
                        RawSensorData.competition_id,
                        func.count(RawSensorData.id).label('total_records'),
                        func.sum(func.case([(RawSensorData.mapping_status == 'mapped', 1)], else_=0)).label('success_records'),
                        func.sum(func.case([(RawSensorData.mapping_status == 'unmapped', 1)], else_=0)).label('failed_records'),
                        func.max(RawSensorData.created_at).label('uploaded_at'))
        
        if competition_id:
            query = query.filter(RawSensorData.competition_id == competition_id)
        
        batch_data = query.group_by(RawSensorData.batch_id, 
                                   RawSensorData.sensor_type, 
                                   RawSensorData.competition_id).all()
        
        batches = []
        for batch in batch_data:
            batch_info = {
                "batch_id": batch.batch_id,
                "sensor_type": batch.sensor_type,
                "competition_id": batch.competition_id,
                "file_name": f"{batch.batch_id}.csv",  # 実際のファイル名が保存されていない場合
                "total_records": batch.total_records,
                "success_records": batch.success_records,
                "failed_records": batch.failed_records,
                "status": "completed" if batch.failed_records == 0 else "partial",
                "uploaded_at": batch.uploaded_at.isoformat() if batch.uploaded_at else None,
                "uploaded_by": "admin"  # 実際の管理者IDが保存されていない場合
            }
            batches.append(batch_info)
        
        return {"batches": batches}
        
    except Exception as e:
        print(f"Error in get_upload_batches: {e}")
        # エラーが発生した場合は空のリストを返す
        return {"batches": []}

@router.delete("/upload/batch/{batch_id}")
async def delete_upload_batch(
    batch_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """アップロードバッチ削除"""
    
    try:
        # バッチIDに関連するすべてのRawSensorDataを削除
        deleted_count = db.query(RawSensorData).filter_by(batch_id=batch_id).delete()
        
        if deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found"
            )
        
        # 関連するマッピングデータも削除（必要に応じて）
        db.query(FlexibleSensorMapping).filter(
            FlexibleSensorMapping.sensor_id.in_(
                db.query(RawSensorData.sensor_id).filter_by(batch_id=batch_id)
            )
        ).delete(synchronize_session=False)
        
        db.commit()
        
        return {
            "message": f"Batch {batch_id} deleted successfully",
            "deleted_records": deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error deleting batch {batch_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete batch: {str(e)}"
        )