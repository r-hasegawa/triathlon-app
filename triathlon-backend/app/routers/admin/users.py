"""
app/routers/admin/users.py
ユーザー管理機能（作成・削除・パスワードリセット）
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
import pandas as pd
import io

from app.database import get_db
from app.models.user import User, AdminUser
from app.models.competition import RaceRecord
from app.models.flexible_sensor_data import FlexibleSensorMapping
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.utils.dependencies import get_current_admin
from app.utils.security import get_password_hash
from .utils import generate_user_id, generate_password, get_user_sensor_data_count, detect_encoding

router = APIRouter()


@router.post("/users/batch-create")
async def batch_create_users(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """CSVファイルからユーザーを一括作成（仕様書1.1対応）"""
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="CSVファイルをアップロードしてください"
        )
    
    try:
        # ファイル読み込み
        content = await file.read()
        encoding = detect_encoding(content)
        csv_string = content.decode(encoding)
        
        # CSVパース（2列: 氏名, メールアドレス）
        df = pd.read_csv(io.StringIO(csv_string))
        
        # 列数チェック
        if len(df.columns) != 2:
            raise HTTPException(
                status_code=400,
                detail="CSVは2列（氏名、メールアドレス）である必要があります"
            )
        
        # 列名を標準化
        df.columns = ['full_name', 'email']
        
        created_users = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                # 必須フィールドチェック
                if pd.isna(row['full_name']) or pd.isna(row['email']):
                    errors.append(f"行 {index + 1}: 氏名またはメールアドレスが空です")
                    continue
                
                full_name = str(row['full_name']).strip()
                email = str(row['email']).strip()
                
                # メールアドレス重複チェック
                existing_user = db.query(User).filter_by(email=email).first()
                if existing_user:
                    errors.append(f"行 {index + 1}: メールアドレス '{email}' は既に登録済みです")
                    continue
                
                # ユーザー情報生成
                user_id = generate_user_id()
                password = generate_password()
                username = email.split('@')[0]  # メールアドレスの@より前をユーザー名に
                
                # ユーザー作成
                user = User(
                    user_id=user_id,
                    username=username,
                    email=email,
                    full_name=full_name,
                    hashed_password=get_password_hash(password)
                )
                
                db.add(user)
                db.commit()
                db.refresh(user)
                
                created_users.append({
                    "full_name": full_name,
                    "email": email,
                    "user_id": user_id,
                    "password": password
                })
                
            except Exception as e:
                errors.append(f"行 {index + 1}: {str(e)}")
                continue
        
        return {
            "message": f"{len(created_users)}人のユーザーを作成しました",
            "created_users": created_users,
            "errors": errors,
            "total_processed": len(df),
            "success_count": len(created_users),
            "error_count": len(errors)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ユーザー一括作成エラー: {str(e)}"
        )


@router.get("/users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """ユーザー一覧取得（仕様書5.1対応）"""
    try:
        # 総ユーザー数取得
        total_count = db.query(User).count()
        
        # ページネーション付きでユーザー取得
        users = db.query(User)\
            .order_by(desc(User.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()
        
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
            from app.models.competition import Competition
            competition = db.query(Competition).filter_by(
                competition_id=record.competition_id
            ).first()
            
            if competition:
                competitions_data.append({
                    "competition_id": competition.competition_id,
                    "name": competition.name,
                    "date": competition.date.isoformat() if competition.date else None,
                    "bib_number": record.bib_number
                })
        
        return {
            "user": {
                "id": user.id,
                "user_id": user.user_id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            "sensor_data": {
                "skin_temperature": skin_temp_count,
                "core_temperature": core_temp_count,
                "heart_rate": heart_rate_count,
                "total": skin_temp_count + core_temp_count + heart_rate_count
            },
            "competitions": competitions_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ユーザー詳細取得エラー: {str(e)}"
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """ユーザー削除（仕様書5.1対応）"""
    
    # ユーザー存在チェック
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="ユーザーが見つかりません"
        )
    
    user_name = user.full_name or user.username
    
    try:
        # データ削除統計（削除前にカウント）
        race_records_count = db.query(RaceRecord).filter_by(user_id=user_id).count()
        mapping_count = db.query(FlexibleSensorMapping).filter_by(user_id=user_id).count()
        
        # センサーデータ数（削除はしない、正規化設計のため）
        skin_temp_count = get_user_sensor_data_count(db, user_id, "skin_temperature")
        core_temp_count = get_user_sensor_data_count(db, user_id, "core_temperature")
        heart_rate_count = get_user_sensor_data_count(db, user_id, "heart_rate")
        
        # 1. 大会記録を削除
        db.query(RaceRecord).filter_by(user_id=user_id).delete()
        
        # 2. センサーマッピングを削除
        db.query(FlexibleSensorMapping).filter_by(user_id=user_id).delete()
        
        # 3. ユーザー本体を削除
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
    """ユーザーのデータサマリー取得（実際のスキーマに基づく修正版）"""
    
    # ユーザー存在チェック
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    try:
        # センサーデータ統計を取得
        sensor_data = {
            "skin_temperature": get_user_sensor_data_count(db, user_id, "skin_temperature"),
            "core_temperature": get_user_sensor_data_count(db, user_id, "core_temperature"),
            "heart_rate": get_user_sensor_data_count(db, user_id, "heart_rate")
        }
        
        # マッピング情報
        mappings = db.query(FlexibleSensorMapping).filter_by(user_id=user_id).all()
        
        # 大会参加情報
        race_records = db.query(RaceRecord).filter_by(user_id=user_id).all()
        
        return {
            "user_info": {
                "user_id": user.user_id,
                "full_name": user.full_name,
                "email": user.email
            },
            "sensor_data_summary": sensor_data,
            "total_sensor_records": sum(sensor_data.values()),
            "mappings_count": len(mappings),
            "competitions_participated": len(race_records)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"データサマリー取得エラー: {str(e)}"
        )