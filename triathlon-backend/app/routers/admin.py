"""
app/routers/admin.py (実データアップロード統合版)
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

from app.database import get_db
from app.models.user import User, AdminUser
from app.models.competition import Competition
from app.models.flexible_sensor_data import *
from app.schemas.user import UserCreate, UserUpdate, UserResponse, AdminResponse
from app.schemas.sensor_data import UploadResponse, MappingResponse, DataSummaryResponse
from app.utils.dependencies import get_current_admin
from app.utils.security import get_password_hash
from app.services.flexible_csv_service import FlexibleCSVService

router = APIRouter(prefix="/admin", tags=["admin"])

# ===== 🆕 実データアップロード機能 =====

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

# === 実データアップロード ===

@router.post("/upload/skin-temperature")
async def upload_skin_temperature(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """体表温データ（halshare）アップロード"""
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    results = []
    
    for file in files:
        batch_id = generate_batch_id(file.filename)
        
        try:
            content = await file.read()
            encoding = detect_encoding(content)
            
            try:
                df = pd.read_csv(io.BytesIO(content), encoding=encoding)
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
            
            # 必要な列の確認
            required_cols = ['halshareWearerName', 'halshareId', 'datetime', 'temperature']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise HTTPException(status_code=400, detail=f"Missing columns: {missing_cols}")
            
            batch = UploadBatch(
                batch_id=batch_id,
                sensor_type=SensorType.SKIN_TEMPERATURE,
                file_name=file.filename,
                file_size=len(content),
                total_records=len(df),
                competition_id=competition_id,
                uploaded_by=current_admin.admin_id
            )
            
            success_count = 0
            failed_count = 0
            
            for _, row in df.iterrows():
                try:
                    halshare_id = str(row['halshareId']).strip().strip('"').strip()
                    datetime_str = str(row['datetime']).strip().strip('"').strip()
                    wearer_name = str(row['halshareWearerName']).strip().strip('"').strip()
                    
                    try:
                        dt = pd.to_datetime(datetime_str)
                    except:
                        dt = datetime.strptime(datetime_str, "%Y/%m/%d %H:%M:%S")
                    
                    data = SkinTemperatureData(
                        halshare_wearer_name=wearer_name,
                        halshare_id=halshare_id,
                        datetime=dt,
                        temperature=float(row['temperature']),
                        upload_batch_id=batch_id,
                        competition_id=competition_id
                    )
                    
                    db.add(data)
                    success_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    print(f"Row error in {file.filename}: {e}")
            
            batch.success_records = success_count
            batch.failed_records = failed_count
            batch.status = UploadStatus.SUCCESS if failed_count == 0 else UploadStatus.PARTIAL
            
            db.add(batch)
            db.commit()
            
            results.append({
                "file": file.filename,
                "batch_id": batch_id,
                "total": len(df),
                "success": success_count,
                "failed": failed_count,
                "status": batch.status.value if hasattr(batch.status, 'value') else str(batch.status)
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
    current_admin = Depends(get_current_admin)
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
            
            # 🔧 データ行処理（7行目以降、ヘッダー行をスキップ）
            for line_num, line in enumerate(lines[6:], start=7):  # 6行目（0-indexed）からスタート
                line = line.strip()
                if not line:  # 空行スキップ
                    continue
                
                # 🔧 システムメッセージ行をスキップ
                if any(msg in line.upper() for msg in ['CRITICAL', 'LOW BATTERY', 'MONITOR WAKE-UP', 'SYSTEM']):
                    print(f"Skipping system message at line {line_num}: {line}")
                    continue
                    
                parts = line.split(',')
                
                # 行が短すぎる場合はスキップ
                if len(parts) < 15:
                    print(f"Skipping short line {line_num}: {len(parts)} parts")
                    continue
                
                # 各センサーのデータ処理（列位置: 0, 7, 14）
                sensor_columns = [0, 7, 14]
                for sensor_col in sensor_columns:
                    if sensor_col in sensor_ids and sensor_col + 4 < len(parts):
                        try:
                            date_str = parts[sensor_col + 1].strip()
                            hour_str = parts[sensor_col + 2].strip()
                            temp_str = parts[sensor_col + 3].strip()
                            status_str = parts[sensor_col + 4].strip()
                            
                            # 🔧 有効な日時データのみ処理
                            if date_str and hour_str and '/' in date_str and ':' in hour_str:
                                # 日時パース
                                try:
                                    dt = pd.to_datetime(f"{date_str} {hour_str}")
                                except:
                                    print(f"Date parse failed at line {line_num}, col {sensor_col}: '{date_str} {hour_str}'")
                                    continue
                                
                                # 温度値処理
                                temperature = None
                                if temp_str and temp_str.lower() not in ['missing data', '', 'nan', 'temperature (°c)']:
                                    try:
                                        temperature = float(temp_str)
                                    except ValueError:
                                        temperature = None
                                
                                data = CoreTemperatureData(
                                    capsule_id=sensor_ids[sensor_col],
                                    monitor_id=file.filename.replace('.csv', ''),
                                    datetime=dt,
                                    temperature=temperature,
                                    status=status_str if status_str else None,
                                    upload_batch_id=batch_id,
                                    competition_id=competition_id
                                )
                                db.add(data)
                                success_count += 1
                                
                        except Exception as e:
                            failed_count += 1
                            print(f"Core temp error in {file.filename} line {line_num}, col {sensor_col}: {e}")
            
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
                "sensor_ids": list(sensor_ids.values()),
                "status": batch.status.value if hasattr(batch.status, 'value') else str(batch.status)
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
    current_admin = Depends(get_current_admin)
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
            
            # TCX名前空間処理
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
                    print(f"TCX trackpoint error in {file.filename}: {e}")
            
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
                "status": batch.status.value if hasattr(batch.status, 'value') else str(batch.status)
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
    """WBGT環境データアップロード（実データ対応版）"""
    # ファイル形式チェック
    if not wbgt_file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSVファイルのみアップロード可能です")
    
    # 大会存在チェック
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
    
    # WBGT処理サービス呼び出し
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
    # ファイル形式チェック
    if not mapping_file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSVファイルのみアップロード可能です")
    
    # 大会存在チェック
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
    
    # マッピング処理サービス呼び出し
    csv_service = FlexibleCSVService()
    
    try:
        # ファイルサイズ取得のため事前読み込み
        content = await mapping_file.read()
        file_size = len(content)
        
        # ファイルポインタをリセット
        await mapping_file.seek(0)
        
        result = await csv_service.process_mapping_data(
            mapping_file=mapping_file,
            competition_id=competition_id,
            db=db,
            overwrite=overwrite
        )
        
        # バッチ記録も作成（マッピングデータ用）
        batch_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{mapping_file.filename}"
        
        batch = UploadBatch(
            batch_id=batch_id,
            sensor_type=SensorType.OTHER,  # マッピングは特殊なタイプ
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
        
        # フロントエンド互換性のためのレスポンス形式統一
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

@router.get("/mapping/status")
async def get_mapping_status(
    competition_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """マッピング状況取得"""
    
    query = db.query(FlexibleSensorMapping)
    if competition_id:
        query = query.filter_by(competition_id=competition_id)
    
    mappings = query.all()
    
    # 統計計算
    total_mappings = len(mappings)
    active_mappings = len([m for m in mappings if m.is_active])
    
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
                'heart_rate': False
            }
        
        if mapping.sensor_type in [SensorType.SKIN_TEMPERATURE, SensorType.CORE_TEMPERATURE, SensorType.HEART_RATE]:
            user_mapping_status[user_id][mapping.sensor_type.value] = True
    
    # 完全マッピング済みユーザー数
    fully_mapped_users = len([
        user for user, status in user_mapping_status.items()
        if all(status.values())
    ])
    
    return {
        "total_mappings": total_mappings,
        "active_mappings": active_mappings,
        "mappings_by_sensor_type": by_sensor_type,
        "total_users_with_mappings": len(user_mapping_status),
        "fully_mapped_users": fully_mapped_users,
        "competition_id": competition_id,
        "user_mapping_details": user_mapping_status
    }

@router.get("/mapping/unmapped-sensors")
async def get_unmapped_sensors(
    competition_id: Optional[str] = Query(None),
    sensor_type: Optional[SensorType] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """未マッピングセンサー一覧"""
    
    unmapped_sensors = []
    
    # 各センサーテーブルから未マッピングデータを取得
    if not sensor_type or sensor_type == SensorType.SKIN_TEMPERATURE:
        skin_temp_unmapped = db.query(SkinTemperatureData)\
            .filter(SkinTemperatureData.mapped_user_id.is_(None))
        
        if competition_id:
            skin_temp_unmapped = skin_temp_unmapped.filter_by(competition_id=competition_id)
        
        for data in skin_temp_unmapped.limit(limit).all():
            unmapped_sensors.append({
                'sensor_id': data.halshare_id,
                'sensor_type': 'skin_temperature',
                'competition_id': data.competition_id,
                'data_count': db.query(SkinTemperatureData)\
                    .filter_by(halshare_id=data.halshare_id, competition_id=data.competition_id)\
                    .count(),
                'last_timestamp': data.datetime.isoformat() if data.datetime else None
            })
    
    if not sensor_type or sensor_type == SensorType.CORE_TEMPERATURE:
        core_temp_unmapped = db.query(CoreTemperatureData)\
            .filter(CoreTemperatureData.mapped_user_id.is_(None))
        
        if competition_id:
            core_temp_unmapped = core_temp_unmapped.filter_by(competition_id=competition_id)
        
        for data in core_temp_unmapped.limit(limit).all():
            unmapped_sensors.append({
                'sensor_id': data.capsule_id,
                'sensor_type': 'core_temperature',
                'competition_id': data.competition_id,
                'data_count': db.query(CoreTemperatureData)\
                    .filter_by(capsule_id=data.capsule_id, competition_id=data.competition_id)\
                    .count(),
                'last_timestamp': data.datetime.isoformat() if data.datetime else None
            })
    
    if not sensor_type or sensor_type == SensorType.HEART_RATE:
        heart_rate_unmapped = db.query(HeartRateData)\
            .filter(HeartRateData.mapped_user_id.is_(None))
        
        if competition_id:
            heart_rate_unmapped = heart_rate_unmapped.filter_by(competition_id=competition_id)
        
        for data in heart_rate_unmapped.limit(limit).all():
            unmapped_sensors.append({
                'sensor_id': data.sensor_id,
                'sensor_type': 'heart_rate',
                'competition_id': data.competition_id,
                'data_count': db.query(HeartRateData)\
                    .filter_by(sensor_id=data.sensor_id, competition_id=data.competition_id)\
                    .count(),
                'last_timestamp': data.time.isoformat() if data.time else None
            })
    
    return {
        "unmapped_sensors": unmapped_sensors[:limit],
        "total_shown": len(unmapped_sensors[:limit]),
        "competition_id": competition_id,
        "sensor_type_filter": sensor_type.value if sensor_type else None
    }

@router.post("/mapping/apply")
async def apply_mapping(
    competition_id: str = Form(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """マッピングを実際のセンサーデータに適用"""
    
    # 該当大会のマッピングを取得
    mappings = db.query(FlexibleSensorMapping)\
        .filter_by(competition_id=competition_id, is_active=True)\
        .all()
    
    if not mappings:
        raise HTTPException(status_code=404, detail="該当大会にアクティブなマッピングがありません")
    
    applied_count = 0
    errors = []
    
    try:
        for mapping in mappings:
            user_id = mapping.user_id
            sensor_id = mapping.sensor_id
            sensor_type = mapping.sensor_type
            
            # センサータイプに応じてデータを更新
            if sensor_type == SensorType.SKIN_TEMPERATURE:
                updated = db.query(SkinTemperatureData)\
                    .filter_by(halshare_id=sensor_id, competition_id=competition_id)\
                    .update({
                        'mapped_user_id': user_id,
                        'mapped_at': datetime.now()
                    })
                applied_count += updated
                
            elif sensor_type == SensorType.CORE_TEMPERATURE:
                updated = db.query(CoreTemperatureData)\
                    .filter_by(capsule_id=sensor_id, competition_id=competition_id)\
                    .update({
                        'mapped_user_id': user_id,
                        'mapped_at': datetime.now()
                    })
                applied_count += updated
                
            elif sensor_type == SensorType.HEART_RATE:
                updated = db.query(HeartRateData)\
                    .filter_by(sensor_id=sensor_id, competition_id=competition_id)\
                    .update({
                        'mapped_user_id': user_id,
                        'mapped_at': datetime.now()
                    })
                applied_count += updated
        
        db.commit()
        
        return {
            "success": True,
            "message": f"マッピングを{applied_count}件のセンサーデータに適用しました",
            "applied_count": applied_count,
            "mapping_count": len(mappings),
            "competition_id": competition_id,
            "errors": errors
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"マッピング適用エラー: {str(e)}")

@router.delete("/upload/batch/{batch_id}")
async def delete_upload_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """アップロードバッチ削除（マッピング対応版）"""
    
    batch = db.query(UploadBatch).filter_by(batch_id=batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    try:
        deleted_count = 0
        
        if batch.sensor_type == SensorType.SKIN_TEMPERATURE:
            deleted_count = db.query(SkinTemperatureData).filter_by(upload_batch_id=batch_id).delete()
        elif batch.sensor_type == SensorType.CORE_TEMPERATURE:
            deleted_count = db.query(CoreTemperatureData).filter_by(upload_batch_id=batch_id).delete()
        elif batch.sensor_type == SensorType.HEART_RATE:
            deleted_count = db.query(HeartRateData).filter_by(upload_batch_id=batch_id).delete()
        elif batch.sensor_type == SensorType.WBGT:
            deleted_count = db.query(WBGTData).filter_by(upload_batch_id=batch_id).delete()
        elif batch.sensor_type == SensorType.OTHER:  # マッピングデータ
            # マッピングはbatch_idではなくcompetition_idで削除
            deleted_count = db.query(FlexibleSensorMapping).filter_by(competition_id=batch.competition_id).delete()
        
        db.delete(batch)
        db.commit()
        
        return {
            "message": f"Batch {batch_id} deleted successfully",
            "sensor_type": batch.sensor_type.value if hasattr(batch.sensor_type, 'value') else str(batch.sensor_type),
            "file_name": batch.file_name,
            "deleted_records": deleted_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.get("/upload/batches")
async def list_upload_batches(
    competition_id: Optional[str] = None,
    sensor_type: Optional[SensorType] = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """アップロードバッチ一覧取得"""
    
    query = db.query(UploadBatch)
    
    if competition_id:
        query = query.filter_by(competition_id=competition_id)
    if sensor_type:
        query = query.filter_by(sensor_type=sensor_type)
    
    batches = query.order_by(UploadBatch.uploaded_at.desc()).all()
    
    return {
        "batches": [
            {
                "batch_id": b.batch_id,
                "sensor_type": b.sensor_type.value if hasattr(b.sensor_type, 'value') else str(b.sensor_type),
                "file_name": b.file_name,
                "competition_id": b.competition_id,
                "total_records": b.total_records,
                "success_records": b.success_records,
                "failed_records": b.failed_records,
                "status": b.status.value if hasattr(b.status, 'value') else str(b.status),
                "uploaded_at": b.uploaded_at.isoformat(),
                "uploaded_by": b.uploaded_by
            }
            for b in batches
        ]
    }

# ===== 既存の管理機能 =====

@router.get("/me", response_model=AdminResponse)
async def get_admin_info(current_admin: AdminUser = Depends(get_current_admin)):
    return current_admin

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
    
    users_with_stats = []
    for user in users:
        sensor_count = db.query(func.count(FlexibleSensorMapping.id))\
                        .filter_by(user_id=user.user_id, is_active=True)\
                        .scalar() or 0
        
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

@router.get("/competitions")
async def get_competitions(
    active_only: bool = Query(False),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """大会一覧取得"""
    query = db.query(Competition)
    
    if active_only:
        query = query.filter(Competition.is_active == True)
    
    competitions = query.order_by(desc(Competition.created_at)).all()
    
    competitions_data = []
    for comp in competitions:
        # 🆕 新しいテーブルからデータ数を取得
        skin_temp_count = db.query(func.count(SkinTemperatureData.id)).filter_by(competition_id=comp.competition_id).scalar() or 0
        core_temp_count = db.query(func.count(CoreTemperatureData.id)).filter_by(competition_id=comp.competition_id).scalar() or 0
        heart_rate_count = db.query(func.count(HeartRateData.id)).filter_by(competition_id=comp.competition_id).scalar() or 0
        
        competitions_data.append({
            "id": comp.id,
            "competition_id": comp.competition_id,
            "name": comp.name,
            "date": comp.date.isoformat() if comp.date else None,
            "location": comp.location,
            "description": comp.description,
            "is_active": comp.is_active,
            "created_at": comp.created_at.isoformat(),
            "sensor_data_counts": {
                "skin_temperature": skin_temp_count,
                "core_temperature": core_temp_count,
                "heart_rate": heart_rate_count,
                "total": skin_temp_count + core_temp_count + heart_rate_count
            }
        })
    
    return {"competitions": competitions_data}

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
    
    competition_data = {
        "name": name,
        "location": location,
        "description": description
    }
    
    if date:
        try:
            competition_data["date"] = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    
    competition = Competition(**competition_data)
    
    db.add(competition)
    db.commit()
    db.refresh(competition)
    
    return {
        "competition_id": competition.competition_id,
        "name": competition.name,
        "date": competition.date.isoformat() if competition.date else None,
        "location": competition.location,
        "created_at": competition.created_at.isoformat()
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
        raise HTTPException(status_code=404, detail="Competition not found")
    
    try:
        # 🆕 新しいテーブルからもデータ削除
        db.query(SkinTemperatureData).filter_by(competition_id=competition_id).delete()
        db.query(CoreTemperatureData).filter_by(competition_id=competition_id).delete()
        db.query(HeartRateData).filter_by(competition_id=competition_id).delete()
        db.query(UploadBatch).filter_by(competition_id=competition_id).delete()
        
        db.delete(competition)
        db.commit()
        
        return {"message": f"Competition {competition_id} and all related data deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get("/stats")
async def get_admin_stats(
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """システム統計取得"""
    
    # 基本統計
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter_by(is_active=True).scalar() or 0
    total_competitions = db.query(func.count(Competition.id)).scalar() or 0
    active_competitions = db.query(func.count(Competition.id)).filter_by(is_active=True).scalar() or 0
    
    # 🆕 新しいテーブルからセンサーデータ統計
    skin_temp_records = db.query(func.count(SkinTemperatureData.id)).scalar() or 0
    core_temp_records = db.query(func.count(CoreTemperatureData.id)).scalar() or 0
    heart_rate_records = db.query(func.count(HeartRateData.id)).scalar() or 0
    
    total_sensor_records = skin_temp_records + core_temp_records + heart_rate_records
    
    # マッピング統計
    mapped_skin_temp = db.query(func.count(SkinTemperatureData.id)).filter(SkinTemperatureData.mapped_user_id.isnot(None)).scalar() or 0
    mapped_core_temp = db.query(func.count(CoreTemperatureData.id)).filter(CoreTemperatureData.mapped_user_id.isnot(None)).scalar() or 0
    mapped_heart_rate = db.query(func.count(HeartRateData.id)).filter(HeartRateData.mapped_user_id.isnot(None)).scalar() or 0
    
    mapped_sensor_records = mapped_skin_temp + mapped_core_temp + mapped_heart_rate
    unmapped_sensor_records = total_sensor_records - mapped_sensor_records
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_competitions": total_competitions,
        "active_competitions": active_competitions,
        "total_sensor_records": total_sensor_records,
        "mapped_sensor_records": mapped_sensor_records,
        "unmapped_sensor_records": unmapped_sensor_records,
        "sensor_type_breakdown": {
            "skin_temperature": skin_temp_records,
            "core_temperature": core_temp_records,
            "heart_rate": heart_rate_records
        }
    }