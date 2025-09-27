"""
app/routers/admin/mappings.py
センサーマッピング管理機能
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import io

from app.database import get_db
from app.models.user import User, AdminUser
from app.models.competition import Competition
from app.models.flexible_sensor_data import FlexibleSensorMapping
from app.schemas.sensor_data import MappingResponse
from app.utils.dependencies import get_current_admin
from .utils import detect_encoding

router = APIRouter()


@router.post("/mappings", response_model=MappingResponse)
async def upload_mapping_data(
    competition_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """センサーマッピングデータアップロード（仕様書2.6対応）"""
    
    # 大会存在チェック
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="指定された大会が見つかりません")
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSVファイルをアップロードしてください")
    
    try:
        # ファイル読み込み
        content = await file.read()
        encoding = detect_encoding(content)
        csv_string = content.decode(encoding)
        
        # CSVパース
        df = pd.read_csv(io.StringIO(csv_string))
        
        # 列名の前後空白を削除
        df.columns = df.columns.str.strip()
        
        # User ID列の存在チェック
        if 'User ID' not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="CSVに 'User ID' 列が必要です"
            )
        
        # 使用可能な列名を定義（実際のスキーマに合わせて修正）
        available_columns = {
            'User ID': 'user_id',
            'Sensor ID': 'sensor_id',
            'Sensor Type': 'sensor_type',
            'Competition ID': 'competition_id',
            'Subject Name': 'subject_name',
            'Device Type': 'device_type',
            'Notes': 'notes'
        }
        
        created_mappings = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                # User ID必須チェック
                user_id = row.get('User ID')
                if pd.isna(user_id) or str(user_id).strip() == '':
                    errors.append(f"行 {index + 1}: User ID が空です")
                    continue
                
                user_id = str(user_id).strip()
                
                # ユーザー存在チェック
                user = db.query(User).filter_by(user_id=user_id).first()
                if not user:
                    errors.append(f"行 {index + 1}: ユーザー '{user_id}' が見つかりません")
                    continue
                
                # Sensor ID必須チェック
                sensor_id = row.get('Sensor ID')
                if pd.isna(sensor_id) or str(sensor_id).strip() == '':
                    errors.append(f"行 {index + 1}: Sensor ID が空です")
                    continue
                
                sensor_id = str(sensor_id).strip()
                
                # Sensor Type必須チェック
                sensor_type = row.get('Sensor Type')
                if pd.isna(sensor_type) or str(sensor_type).strip() == '':
                    errors.append(f"行 {index + 1}: Sensor Type が空です")
                    continue
                
                sensor_type = str(sensor_type).strip()
                
                # 既存マッピング削除（更新対応）
                db.query(FlexibleSensorMapping).filter_by(
                    sensor_id=sensor_id,
                    sensor_type=sensor_type,
                    competition_id=competition_id
                ).delete()
                
                # マッピングデータ構築
                mapping_data = {
                    'user_id': user_id,
                    'sensor_id': sensor_id,
                    'sensor_type': sensor_type,
                    'competition_id': competition_id
                }
                
                # オプション列の処理
                for csv_col, db_col in available_columns.items():
                    if csv_col in df.columns and csv_col not in ['User ID', 'Sensor ID', 'Sensor Type']:
                        value = row.get(csv_col)
                        if not pd.isna(value) and str(value).strip() != '':
                            mapping_data[db_col] = str(value).strip()
                
                # マッピング作成
                mapping = FlexibleSensorMapping(**mapping_data)
                db.add(mapping)
                
                created_mappings.append({
                    "user_id": user_id,
                    "sensor_id": sensor_id,
                    "sensor_type": sensor_type,
                    "mapping_data": mapping_data
                })
                
            except Exception as e:
                errors.append(f"行 {index + 1}: {str(e)}")
                continue
        
        db.commit()
        
        return MappingResponse(
            message=f"{len(created_mappings)}件のマッピングを作成しました",
            created_count=len(created_mappings),
            error_count=len(errors),
            errors=errors
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"マッピングデータアップロードエラー: {str(e)}"
        )


@router.get("/mappings")
async def list_mappings(
    competition_id: str = None,
    user_id: str = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """マッピング一覧取得"""
    try:
        query = db.query(FlexibleSensorMapping)
        
        # フィルタ適用
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        mappings = query.limit(limit).all()
        
        mapping_list = []
        for mapping in mappings:
            # ユーザー情報取得
            user = db.query(User).filter_by(user_id=mapping.user_id).first()
            
            # 大会情報取得
            competition = db.query(Competition).filter_by(
                competition_id=mapping.competition_id
            ).first()
            
            mapping_data = {
                "id": mapping.id,
                "user_id": mapping.user_id,
                "user_name": user.full_name if user else "不明",
                "competition_id": mapping.competition_id,
                "competition_name": competition.name if competition else "不明",
                "skin_temp_sensor_id": mapping.skin_temp_sensor_id,
                "core_temp_sensor_id": mapping.core_temp_sensor_id,
                "heart_rate_sensor_id": mapping.heart_rate_sensor_id,
                "race_record_id": mapping.race_record_id,
                "created_at": mapping.created_at.isoformat() if mapping.created_at else None
            }
            
            mapping_list.append(mapping_data)
        
        return {
            "mappings": mapping_list,
            "total": len(mapping_list),
            "filters": {
                "competition_id": competition_id,
                "user_id": user_id
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"マッピング一覧取得エラー: {str(e)}"
        )


@router.get("/mappings/{mapping_id}")
async def get_mapping_detail(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """マッピング詳細取得"""
    
    mapping = db.query(FlexibleSensorMapping).filter_by(id=mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="マッピングが見つかりません")
    
    try:
        # 関連情報取得
        user = db.query(User).filter_by(user_id=mapping.user_id).first()
        competition = db.query(Competition).filter_by(
            competition_id=mapping.competition_id
        ).first()
        
        # センサーデータ統計
        from .utils import get_user_sensor_data_count
        
        sensor_stats = {
            "skin_temperature": get_user_sensor_data_count(db, mapping.user_id, "skin_temperature"),
            "core_temperature": get_user_sensor_data_count(db, mapping.user_id, "core_temperature"),
            "heart_rate": get_user_sensor_data_count(db, mapping.user_id, "heart_rate")
        }
        
        return {
            "mapping": {
                "id": mapping.id,
                "user_id": mapping.user_id,
                "competition_id": mapping.competition_id,
                "skin_temp_sensor_id": mapping.skin_temp_sensor_id,
                "core_temp_sensor_id": mapping.core_temp_sensor_id,
                "heart_rate_sensor_id": mapping.heart_rate_sensor_id,
                "race_record_id": mapping.race_record_id,
                "created_at": mapping.created_at.isoformat() if mapping.created_at else None
            },
            "user_info": {
                "user_id": user.user_id if user else None,
                "full_name": user.full_name if user else "不明",
                "email": user.email if user else None
            },
            "competition_info": {
                "competition_id": competition.competition_id if competition else None,
                "name": competition.name if competition else "不明",
                "date": competition.date.isoformat() if competition and competition.date else None
            },
            "sensor_data_stats": sensor_stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"マッピング詳細取得エラー: {str(e)}"
        )


@router.delete("/mappings/{mapping_id}")
async def delete_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """マッピング削除"""
    
    mapping = db.query(FlexibleSensorMapping).filter_by(id=mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="マッピングが見つかりません")
    
    try:
        user_id = mapping.user_id
        competition_id = mapping.competition_id
        
        db.delete(mapping)
        db.commit()
        
        return {
            "message": f"マッピング（ユーザー: {user_id}, 大会: {competition_id}）を削除しました",
            "deleted_mapping_id": mapping_id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"マッピング削除エラー: {str(e)}"
        )


@router.delete("/mappings/competition/{competition_id}")
async def delete_competition_mappings(
    competition_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会のマッピングを一括削除"""
    
    # 大会存在チェック
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="指定された大会が見つかりません")
    
    try:
        # 削除前にカウント
        mapping_count = db.query(FlexibleSensorMapping).filter_by(
            competition_id=competition_id
        ).count()
        
        if mapping_count == 0:
            return {
                "message": f"大会 '{competition.name}' にマッピングデータがありません",
                "deleted_count": 0
            }
        
        # 一括削除
        db.query(FlexibleSensorMapping).filter_by(competition_id=competition_id).delete()
        db.commit()
        
        return {
            "message": f"大会 '{competition.name}' のマッピング {mapping_count} 件を削除しました",
            "competition_id": competition_id,
            "deleted_count": mapping_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"大会マッピング一括削除エラー: {str(e)}"
        )


@router.get("/mappings/validation/{competition_id}")
async def validate_mappings(
    competition_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """マッピングデータの整合性チェック"""
    
    # 大会存在チェック
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="指定された大会が見つかりません")
    
    try:
        # 大会のマッピング取得
        mappings = db.query(FlexibleSensorMapping).filter_by(
            competition_id=competition_id
        ).all()
        
        validation_results = {
            "valid_mappings": [],
            "invalid_mappings": [],
            "missing_data": {
                "users_without_sensors": [],
                "sensors_without_users": []
            }
        }
        
        for mapping in mappings:
            issues = []
            
            # ユーザー存在チェック
            user = db.query(User).filter_by(user_id=mapping.user_id).first()
            if not user:
                issues.append("ユーザーが存在しません")
            
            # センサーデータ存在チェック
            if mapping.skin_temp_sensor_id:
                from app.models.flexible_sensor_data import SkinTemperatureData
                skin_data_exists = db.query(SkinTemperatureData).filter_by(
                    sensor_id=mapping.skin_temp_sensor_id,
                    competition_id=competition_id
                ).first()
                if not skin_data_exists:
                    issues.append(f"体表温センサーID '{mapping.skin_temp_sensor_id}' のデータが存在しません")
            
            if mapping.core_temp_sensor_id:
                from app.models.flexible_sensor_data import CoreTemperatureData
                core_data_exists = db.query(CoreTemperatureData).filter_by(
                    sensor_id=mapping.core_temp_sensor_id,
                    competition_id=competition_id
                ).first()
                if not core_data_exists:
                    issues.append(f"カプセル温センサーID '{mapping.core_temp_sensor_id}' のデータが存在しません")
            
            if mapping.heart_rate_sensor_id:
                from app.models.flexible_sensor_data import HeartRateData
                hr_data_exists = db.query(HeartRateData).filter_by(
                    sensor_id=mapping.heart_rate_sensor_id,
                    competition_id=competition_id
                ).first()
                if not hr_data_exists:
                    issues.append(f"心拍センサーID '{mapping.heart_rate_sensor_id}' のデータが存在しません")
            
            # 結果分類
            mapping_info = {
                "mapping_id": mapping.id,
                "user_id": mapping.user_id,
                "user_name": user.full_name if user else "不明",
                "issues": issues
            }
            
            if issues:
                validation_results["invalid_mappings"].append(mapping_info)
            else:
                validation_results["valid_mappings"].append(mapping_info)
        
        return {
            "competition_name": competition.name,
            "total_mappings": len(mappings),
            "validation_summary": {
                "valid_count": len(validation_results["valid_mappings"]),
                "invalid_count": len(validation_results["invalid_mappings"])
            },
            "validation_details": validation_results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"マッピング検証エラー: {str(e)}"
        )

@router.get("/mapping/status")
async def get_mapping_status(
    competition_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """マッピング状況取得（フロントエンド用）"""
    
    try:
        # 大会存在チェック
        competition = db.query(Competition).filter_by(competition_id=competition_id).first()
        if not competition:
            raise HTTPException(status_code=404, detail="指定された大会が見つかりません")
        
        # 該当大会のマッピング取得
        mappings = db.query(FlexibleSensorMapping).filter_by(
            competition_id=competition_id
        ).all()
        
        # 統計計算
        total_mappings = len(mappings)
        active_mappings = total_mappings  # 物理削除なので全て有効
        
        # ユーザー単位での集計
        users_with_mappings = set()
        fully_mapped_users = []
        mappings_by_sensor_type = {
            "skin_temperature": 0,
            "core_temperature": 0, 
            "heart_rate": 0,
            "race_record": 0
        }
        
        for mapping in mappings:
            users_with_mappings.add(mapping.user_id)
            
            # センサータイプ別カウント
            if mapping.skin_temp_sensor_id:
                mappings_by_sensor_type["skin_temperature"] += 1
            if mapping.core_temp_sensor_id:
                mappings_by_sensor_type["core_temperature"] += 1
            if mapping.heart_rate_sensor_id:
                mappings_by_sensor_type["heart_rate"] += 1
            if mapping.race_record_id:
                mappings_by_sensor_type["race_record"] += 1
            
            # 完全マッピングユーザー判定（必要なセンサーがすべて設定されている）
            if (mapping.skin_temp_sensor_id and 
                mapping.core_temp_sensor_id and 
                mapping.heart_rate_sensor_id and 
                mapping.race_record_id):
                fully_mapped_users.append(mapping.user_id)
        
        return {
            "total_mappings": total_mappings,
            "active_mappings": active_mappings,
            "total_users_with_mappings": len(users_with_mappings),
            "fully_mapped_users": len(set(fully_mapped_users)),
            "mappings_by_sensor_type": mappings_by_sensor_type,
            "competition_id": competition_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"マッピング状況取得エラー: {str(e)}"
        )