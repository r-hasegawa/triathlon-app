"""
app/routers/admin/upload.py

実際のデータ形式に対応したアップロードエンドポイント
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.sensor_data import *
from app.models.competition import Competition
from app.utils.auth import get_current_admin
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional
import io
import re

router = APIRouter(prefix="/admin/upload", tags=["upload"])

def generate_batch_id(filename: str) -> str:
    """バッチIDを生成"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{filename}"

# === 1. 体表温データアップロード ===
@router.post("/skin-temperature")
async def upload_skin_temperature(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """体表温データ（halshare）を複数ファイル同時アップロード"""
    
    # 大会存在確認
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    results = []
    
    for file in files:
        batch_id = generate_batch_id(file.filename)
        
        try:
            # ファイル読み取り
            content = await file.read()
            df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
            
            # バッチ記録作成
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
            
            # データ処理
            for _, row in df.iterrows():
                try:
                    # データクリーニング
                    halshare_id = str(row['halshareId']).strip().strip('"')
                    datetime_str = str(row['datetime']).strip().strip('"')
                    
                    # 日時パース
                    dt = datetime.strptime(datetime_str, "%Y/%m/%d %H:%M:%S")
                    
                    # データ保存
                    data = SkinTemperatureData(
                        halshare_wearer_name=str(row['halshareWearerName']).strip(),
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
                    print(f"Row error: {e}")
            
            # バッチ更新
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
                "status": batch.status
            })
            
        except Exception as e:
            db.rollback()
            results.append({
                "file": file.filename,
                "error": str(e),
                "status": "failed"
            })
    
    return {"results": results}

# === 2. カプセル体温データアップロード ===
@router.post("/core-temperature")
async def upload_core_temperature(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """カプセル体温データ（e-Celcius）をアップロード"""
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    results = []
    
    for file in files:
        batch_id = generate_batch_id(file.filename)
        
        try:
            content = await file.read()
            lines = content.decode('utf-8').splitlines()
            
            # センサーIDを5行目から抽出
            sensor_ids = {}
            if len(lines) > 4:
                header_line = lines[4]  # Pill n-1, n-2, n-3の行
                parts = header_line.split(',')
                
                # 各センサーの位置とIDを特定
                for i, part in enumerate(parts):
                    if 'Pill' in part and i + 1 < len(parts):
                        sensor_ids[i] = parts[i + 1].strip()  # 右隣のセルがセンサーID
            
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
            
            # データ行を処理（6行目以降）
            for line_num, line in enumerate(lines[6:], start=7):
                parts = line.split(',')
                
                # 各センサーのデータを処理（5列ごと）
                for sensor_col in [0, 7, 14]:  # 1列目、8列目、15列目から始まる
                    if sensor_col in sensor_ids and sensor_col + 4 < len(parts):
                        try:
                            date_str = parts[sensor_col + 1].strip()
                            hour_str = parts[sensor_col + 2].strip()
                            temp_str = parts[sensor_col + 3].strip()
                            status_str = parts[sensor_col + 4].strip()
                            
                            if date_str and hour_str:
                                # 日時結合
                                dt = datetime.strptime(f"{date_str} {hour_str}", "%Y/%m/%d %H:%M:%S")
                                
                                # 温度値処理
                                temperature = None
                                if temp_str and temp_str != "Missing data":
                                    temperature = float(temp_str)
                                
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
                            print(f"Core temp row error: {e}")
            
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
                "sensor_ids": list(sensor_ids.values())
            })
            
        except Exception as e:
            db.rollback()
            results.append({
                "file": file.filename,
                "error": str(e),
                "status": "failed"
            })
    
    return {"results": results}

# === 3. 心拍データアップロード ===
@router.post("/heart-rate")
async def upload_heart_rate(
    competition_id: str = Form(...),
    sensor_id: str = Form(...),  # 手動入力のセンサーID
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """心拍データ（TCX）をアップロード（同じsensor_idで複数ファイル可能）"""
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    results = []
    
    for file in files:
        batch_id = generate_batch_id(file.filename)
        
        try:
            content = await file.read()
            root = ET.fromstring(content.decode('utf-8'))
            
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
            
            # Trackpointを探索
            trackpoints = root.findall('.//tcx:Trackpoint', ns)
            
            for trackpoint in trackpoints:
                try:
                    time_elem = trackpoint.find('tcx:Time', ns)
                    hr_elem = trackpoint.find('.//tcx:HeartRateBpm/tcx:Value', ns)
                    
                    if time_elem is not None:
                        # 時刻パース
                        time_str = time_elem.text
                        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        
                        # 心拍数取得
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
                    print(f"TCX trackpoint error: {e}")
            
            batch.total_records = success_count + failed_count
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
                "failed": failed_count
            })
            
        except Exception as e:
            db.rollback()
            results.append({
                "file": file.filename,
                "error": str(e),
                "status": "failed"
            })
    
    return {"results": results}

# === 4. バッチ削除エンドポイント ===
@router.delete("/batch/{batch_id}")
async def delete_upload_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """アップロードバッチとそのデータを完全削除"""
    
    batch = db.query(UploadBatch).filter_by(batch_id=batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    try:
        # センサータイプに応じてデータ削除
        if batch.sensor_type == SensorType.SKIN_TEMPERATURE:
            db.query(SkinTemperatureData).filter_by(upload_batch_id=batch_id).delete()
        elif batch.sensor_type == SensorType.CORE_TEMPERATURE:
            db.query(CoreTemperatureData).filter_by(upload_batch_id=batch_id).delete()
        elif batch.sensor_type == SensorType.HEART_RATE:
            db.query(HeartRateData).filter_by(upload_batch_id=batch_id).delete()
        
        # バッチ記録削除
        db.delete(batch)
        db.commit()
        
        return {
            "message": f"Batch {batch_id} deleted successfully",
            "sensor_type": batch.sensor_type,
            "file_name": batch.file_name
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

# === 5. バッチ一覧取得 ===
@router.get("/batches")
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
                "sensor_type": b.sensor_type,
                "file_name": b.file_name,
                "competition_id": b.competition_id,
                "total_records": b.total_records,
                "success_records": b.success_records,
                "failed_records": b.failed_records,
                "status": b.status,
                "uploaded_at": b.uploaded_at,
                "uploaded_by": b.uploaded_by
            }
            for b in batches
        ]
    }