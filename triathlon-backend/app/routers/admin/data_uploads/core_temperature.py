"""
app/routers/admin/data_upload/core_temperature.py
カプセル体温データ（e-Celcius）アップロード機能 - 詳細レポート版
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Dict
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
    """カプセル体温データ（e-Celcius）アップロード - 詳細レポート版"""
    
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
            
            # センサーID行を動的に検索（"Pill"を含む行）
            sensor_id_line_index = None
            for i, line in enumerate(lines):
                if 'Pill' in line:
                    sensor_id_line_index = i
                    break
            
            if sensor_id_line_index is None:
                raise ValueError("センサーID行（'Pill'を含む行）が見つかりませんでした")
            
            # センサーIDを抽出
            sensor_ids = {}
            header_line = lines[sensor_id_line_index]
            parts = header_line.split(',')
            
            for i, part in enumerate(parts):
                if 'Pill' in part and i + 1 < len(parts):
                    sensor_id = parts[i + 1].strip()
                    if sensor_id:
                        sensor_ids[i] = sensor_id
            
            # データヘッダー行はセンサーID行の次の行
            data_header_line_index = sensor_id_line_index + 1
            
            # データ開始行はヘッダー行の次の行
            data_start_line_index = data_header_line_index + 1
            
            # センサーごとの成功・失敗カウント
            sensor_stats: Dict[str, Dict[str, int]] = {}
            for sensor_id in sensor_ids.values():
                sensor_stats[sensor_id] = {"success": 0, "failed": 0}
            
            total_success = 0
            total_failed = 0
            
            # データ開始行以降を処理
            for line_num, line in enumerate(lines[data_start_line_index:], start=data_start_line_index + 1):
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
                        sensor_id = sensor_ids[sensor_col]
                        try:
                            date_str = parts[sensor_col + 1].strip()
                            hour_str = parts[sensor_col + 2].strip()
                            temp_str = parts[sensor_col + 3].strip()
                            
                            if temp_str and temp_str != '---':
                                # 日付フォーマットの統一処理（2025/7/26 と 2025-07-26 の両方に対応）
                                date_str = date_str.replace('/', '-')
                                datetime_obj = pd.to_datetime(f"{date_str} {hour_str}")
                                temperature = float(temp_str)
                                
                                core_data = CoreTemperatureData(
                                    capsule_id=sensor_id,
                                    datetime=datetime_obj,
                                    temperature=temperature,
                                    upload_batch_id=batch_id,
                                    competition_id=competition_id
                                )
                                db.add(core_data)
                                sensor_stats[sensor_id]["success"] += 1
                                total_success += 1
                                
                        except (ValueError, IndexError) as e:
                            sensor_stats[sensor_id]["failed"] += 1
                            total_failed += 1
                            continue
            
            # バッチ情報を保存
            batch = UploadBatch(
                batch_id=batch_id,
                sensor_type=SensorType.CORE_TEMPERATURE,
                file_name=file.filename,
                competition_id=competition_id,
                total_records=total_success + total_failed,
                success_records=total_success,
                failed_records=total_failed,
                status=UploadStatus.SUCCESS if total_failed == 0 else UploadStatus.PARTIAL
            )
            db.add(batch)
            db.commit()
            
            # センサーごとの詳細情報を整形
            sensor_details = []
            for idx, (sensor_id, stats) in enumerate(sensor_stats.items(), 1):
                sensor_details.append({
                    "sensor_number": idx,
                    "sensor_id": sensor_id,
                    "success_count": stats["success"],
                    "failed_count": stats["failed"],
                    "total_count": stats["success"] + stats["failed"]
                })
            
            results.append({
                "file_name": file.filename,
                "batch_id": batch_id,
                "status": batch.status.value,
                "total_success": total_success,
                "total_failed": total_failed,
                "sensor_details": sensor_details,
                "sensor_id_line": sensor_id_line_index,
                "data_start_line": data_start_line_index
            })
            
        except Exception as e:
            db.rollback()
            results.append({
                "file_name": file.filename,
                "batch_id": batch_id,
                "status": "failed",
                "error": str(e),
                "sensor_details": []
            })
    
    return {
        "message": f"{len(files)}個のファイルをアップロードしました",
        "competition_id": competition_id,
        "results": results
    }