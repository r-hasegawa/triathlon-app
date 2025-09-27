"""
app/routers/admin/data_upload/heart_rate.py
心拍データ（TCX/XML）アップロード機能
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import xml.etree.ElementTree as ET

from app.database import get_db
from app.models.user import AdminUser
from app.models.competition import Competition
from app.models.flexible_sensor_data import (
    HeartRateData, 
    UploadBatch, 
    SensorType,
    UploadStatus
)
from app.utils.dependencies import get_current_admin
from ..utils import generate_batch_id


router = APIRouter()


@router.post("/upload/heart-rate")
async def upload_heart_rate(
    competition_id: str = Form(...),
    sensor_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """心拍データ（TCX/XML）アップロード - 元のadmin.py方式"""
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    results = []
    
    for file in files:
        batch_id = generate_batch_id(file.filename)
        
        try:
            content = await file.read()
            
            # XML解析
            try:
                root = ET.fromstring(content)
            except ET.ParseError as e:
                results.append({
                    "file": file.filename,
                    "error": f"XML解析エラー: {str(e)}",
                    "status": "failed"
                })
                continue
            
            batch = UploadBatch(
                batch_id=batch_id,
                sensor_type=SensorType.HEART_RATE,
                file_name=file.filename,
                competition_id=competition_id,
            )
            db.add(batch)
            
            success_count = 0
            failed_count = 0
            
            # TCX名前空間
            namespaces = {
                'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'
            }
            
            # TrackPointデータを抽出
            trackpoints = root.findall('.//tcx:Trackpoint', namespaces)
            
            for trackpoint in trackpoints:
                try:
                    # 時刻
                    time_elem = trackpoint.find('tcx:Time', namespaces)
                    if time_elem is None:
                        continue
                    
                    time_str = time_elem.text
                    time_obj = pd.to_datetime(time_str)
                    
                    # 心拍数
                    hr_elem = trackpoint.find('.//tcx:HeartRateBpm/tcx:Value', namespaces)
                    if hr_elem is None:
                        continue
                    
                    heart_rate = int(hr_elem.text)
                    
                    # HeartRateDataオブジェクト作成
                    hr_data = HeartRateData(
                        sensor_id=sensor_id,
                        time=time_obj,
                        heart_rate=heart_rate,
                        upload_batch_id=batch_id,
                        competition_id=competition_id
                    )
                    db.add(hr_data)
                    success_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    print(f"TrackPoint処理エラー: {e}")
            
            # バッチ情報更新
            batch.total_records = success_count + failed_count
            batch.success_records = success_count
            batch.failed_records = failed_count
            batch.status = UploadStatus.SUCCESS if failed_count == 0 else UploadStatus.PARTIAL
            
            db.commit()

            results.append({
                "file": file.filename,
                "batch_id": batch_id,
                "total": success_count + failed_count,
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