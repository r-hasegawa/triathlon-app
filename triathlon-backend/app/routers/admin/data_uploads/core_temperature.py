"""
app/routers/admin/data_upload/core_temperature.py
カプセル体温データ（e-Celcius）アップロード機能
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import pandas as pd

from app.database import get_db
from app.models.user import AdminUser
from app.models.competition import Competition
from app.models.flexible_sensor_data import (
    CoreTemperatureData, 
    UploadBatch, 
    SensorType,
    UploadStatus
)
from app.utils.dependencies import get_current_admin
from ..utils import generate_batch_id, detect_encoding


router = APIRouter()


@router.post("/upload/core-temperature")
async def upload_core_temperature(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """カプセル体温データ（e-Celcius）アップロード - 元のadmin.py方式"""
    
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
                competition_id=competition_id,
            )
            db.add(batch)
            
            success_count = 0
            failed_count = 0
            
            # 6行目以降のデータを処理
            for line_num, line in enumerate(lines[6:], start=7):
                line = line.strip()
                if not line:
                    continue
                
                # システムメッセージをスキップ
                if any(msg in line.upper() for msg in ['CRITICAL', 'LOW BATTERY', 'MONITOR WAKE-UP', 'SYSTEM']):
                    continue
                    
                parts = line.split(',')
                
                if len(parts) < 15:
                    continue
                
                # 3つのセンサー列を処理（0, 7, 14列目）
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
                            print(f"行{line_num}データ処理エラー: {e}")
            
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