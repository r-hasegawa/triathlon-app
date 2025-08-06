from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os

from app.database import get_db
from app.models.user import AdminUser, User
from app.models.sensor_data import UploadHistory, SensorMapping
from app.schemas.user import UserResponse, UserCreate
from app.schemas.sensor_data import SensorMappingResponse
from app.utils.dependencies import get_current_admin
from app.utils.security import validate_file_upload, get_password_hash
from app.services.csv_service import CSVProcessingService

router = APIRouter()

@router.post("/upload/csv")
async def upload_csv_files(
    sensor_data_file: UploadFile = File(..., description="センサデータCSVファイル"),
    sensor_mapping_file: UploadFile = File(..., description="センサマッピングCSVファイル"),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """CSVファイル同時アップロード・処理"""
    
    csv_service = CSVProcessingService()
    
    try:
        # ファイル検証
        if not sensor_data_file.filename or not sensor_data_file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="センサデータファイルはCSV形式である必要があります"
            )
            
        if not sensor_mapping_file.filename or not sensor_mapping_file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="センサマッピングファイルはCSV形式である必要があります"
            )

        # ファイルサイズチェック（内容を読み込んでサイズ確認）
        sensor_data_content = await sensor_data_file.read()
        mapping_content = await sensor_mapping_file.read()
        
        # ファイルポインタをリセット
        sensor_data_file.file.seek(0)
        sensor_mapping_file.file.seek(0)
        
        max_size = 10 * 1024 * 1024  # 10MB
        if len(sensor_data_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="センサデータファイルのサイズが10MBを超えています"
            )
            
        if len(mapping_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="マッピングファイルのサイズが10MBを超えています"
            )
        
        # ファイル保存
        sensor_data_path, sensor_data_filename = await csv_service.save_uploaded_file(sensor_data_file)
        mapping_path, mapping_filename = await csv_service.save_uploaded_file(sensor_mapping_file)
        
        # アップロード履歴作成
        sensor_upload = csv_service.create_upload_history(
            admin_id=current_admin.admin_id,
            filename=sensor_data_filename,
            file_path=sensor_data_path,
            file_size=len(sensor_data_content),
            db=db
        )
        
        mapping_upload = csv_service.create_upload_history(
            admin_id=current_admin.admin_id,
            filename=mapping_filename,
            file_path=mapping_path,
            file_size=len(mapping_content),
            db=db
        )
        
        # CSV構造検証
        sensor_df = csv_service.validate_csv_structure(sensor_data_path, "sensor_data")
        mapping_df = csv_service.validate_csv_structure(mapping_path, "sensor_mapping")
        
        # センサマッピング処理
        mapping_count, mapping_errors = csv_service.process_sensor_mapping_csv(mapping_df, db)
        
        # センサデータ処理
        data_count, data_errors = csv_service.process_sensor_data_csv(sensor_df, mapping_df, db)
        
        # アップロード履歴更新
        sensor_upload.status = "completed" if not data_errors else "completed_with_errors"
        sensor_upload.records_count = data_count
        sensor_upload.processed_at = datetime.utcnow()
        if data_errors:
            sensor_upload.error_message = "\n".join(data_errors[:10])  # 最初の10エラーのみ保存
        
        mapping_upload.status = "completed" if not mapping_errors else "completed_with_errors"
        mapping_upload.records_count = mapping_count
        mapping_upload.processed_at = datetime.utcnow()
        if mapping_errors:
            mapping_upload.error_message = "\n".join(mapping_errors[:10])
        
        db.commit()
        
        return {
            "message": "CSV files processed successfully",
            "sensor_data": {
                "processed_records": data_count,
                "errors": data_errors[:5] if data_errors else [],
                "total_errors": len(data_errors)
            },
            "sensor_mapping": {
                "processed_records": mapping_count,
                "errors": mapping_errors[:5] if mapping_errors else [],
                "total_errors": len(mapping_errors)
            },
            "upload_ids": {
                "sensor_data": sensor_upload.upload_id,
                "sensor_mapping": mapping_upload.upload_id
            }
        }
        
    except HTTPException:
        # HTTPExceptionはそのまま再発生
        raise
    except Exception as e:
        # エラー時はアップロード履歴を失敗に更新
        print(f"CSV upload error: {str(e)}")  # デバッグ用ログ
        
        try:
            if 'sensor_upload' in locals():
                sensor_upload.status = "failed"
                sensor_upload.error_message = str(e)
            if 'mapping_upload' in locals():
                mapping_upload.status = "failed"
                mapping_upload.error_message = str(e)
            db.commit()
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CSV processing failed: {str(e)}"
        )

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """ユーザー一覧取得"""
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.user_id.contains(search)) |
            (User.full_name.contains(search))
        )
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """ユーザー作成"""
    # 既存ユーザーチェック
    existing_user = db.query(User).filter(
        (User.user_id == user_data.user_id) | 
        (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID or username already exists"
        )
    
    # 新規ユーザー作成
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

@router.get("/upload-history")
async def get_upload_history(
    skip: int = 0,
    limit: int = 50,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """アップロード履歴取得"""
    uploads = db.query(UploadHistory)\
                .order_by(UploadHistory.uploaded_at.desc())\
                .offset(skip)\
                .limit(limit)\
                .all()
    
    return [
        {
            "upload_id": upload.upload_id,
            "filename": upload.filename,
            "status": upload.status,
            "records_count": upload.records_count,
            "file_size": upload.file_size,
            "uploaded_at": upload.uploaded_at.isoformat(),
            "processed_at": upload.processed_at.isoformat() if upload.processed_at else None,
            "error_message": upload.error_message
        }
        for upload in uploads
    ]

@router.get("/sensor-mappings", response_model=List[SensorMappingResponse])
async def get_sensor_mappings(
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """センサマッピング一覧取得"""
    mappings = db.query(SensorMapping).filter_by(is_active=True).all()
    return mappings

@router.get("/users-with-stats")
async def get_users_with_stats(
    skip: int = 0,
    limit: int = 1000,
    search: Optional[str] = None,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """統計情報付きユーザー一覧取得"""
    from sqlalchemy import func, and_
    from app.models.sensor_data import SensorMapping, SensorData
    
    try:
        # 基本クエリ
        query = db.query(User)
        
        # 検索フィルター
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.user_id.like(search_term)) |
                (User.username.like(search_term)) |
                (User.full_name.like(search_term))
            )
        
        # ユーザー一覧取得
        users = query.offset(skip).limit(limit).all()
        
        # 各ユーザーの統計情報を取得
        users_with_stats = []
        for user in users:
            # センサー数
            sensor_count = db.query(func.count(SensorMapping.id))\
                            .filter_by(user_id=user.user_id, is_active=True)\
                            .scalar() or 0
            
            # 最終データ日時
            last_data = db.query(func.max(SensorData.timestamp))\
                          .filter_by(user_id=user.user_id)\
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
        
    except Exception as e:
        print(f"Error getting users with stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user stats: {str(e)}"
        )

@router.get("/dashboard-stats")
async def get_admin_dashboard_stats(
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """管理者ダッシュボード用の統計情報取得"""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    try:
        # 基本統計
        total_users = db.query(func.count(User.id)).scalar() or 0
        active_users = db.query(func.count(User.id)).filter_by(is_active=True).scalar() or 0
        total_sensors = db.query(func.count(SensorMapping.id)).filter_by(is_active=True).scalar() or 0
        total_data_records = db.query(func.count(SensorData.id)).scalar() or 0
        
        # 直近7日間のデータ統計
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_data_count = db.query(func.count(SensorData.id))\
                           .filter(SensorData.timestamp >= week_ago)\
                           .scalar() or 0
        
        # 直近のアップロード
        recent_uploads = db.query(func.count(UploadHistory.id))\
                          .filter(UploadHistory.uploaded_at >= week_ago)\
                          .scalar() or 0
        
        # データを持つユーザー数
        users_with_data = db.query(func.count(func.distinct(SensorData.user_id)))\
                           .scalar() or 0
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "total_sensors": total_sensors,
            "total_data_records": total_data_records,
            "users_with_data": users_with_data,
            "users_without_data": total_users - users_with_data,
            "recent_data_count": recent_data_count,
            "recent_uploads": recent_uploads,
            "avg_sensors_per_user": round(total_sensors / total_users, 1) if total_users > 0 else 0,
            "avg_records_per_user": round(total_data_records / total_users, 1) if total_users > 0 else 0
        }
        
    except Exception as e:
        print(f"Error getting dashboard stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard stats: {str(e)}"
        )