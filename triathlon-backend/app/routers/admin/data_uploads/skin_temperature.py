"""
app/routers/admin/data_upload/skin_temperature.py
体表温データ（halshare）アップロード機能
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import io

from app.database import get_db
from app.models.user import AdminUser
from app.models.competition import Competition
from app.models.flexible_sensor_data import (
    SkinTemperatureData, 
    UploadBatch, 
    SensorType,
    UploadStatus
)
from app.utils.dependencies import get_current_admin
from ..utils import generate_batch_id, detect_encoding


router = APIRouter()


@router.post("/upload/skin-temperature")
async def upload_skin_temperature(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """体表温データ（halshare）アップロード - 元のadmin.py方式"""
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    results = []
    
    for file in files:
        batch_id = generate_batch_id(file.filename)
        
        try:
            content = await file.read()
            encoding = detect_encoding(content)
            
            # CSVファイル読み込み（エンコーディング対応）
            try:
                df = pd.read_csv(io.BytesIO(content), encoding=encoding)
            except UnicodeDecodeError:
                # フォールバック処理
                try:
                    df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
                except Exception:
                    df = pd.read_csv(io.BytesIO(content), encoding='shift-jis')
            
            # 必要な列の確認
            required_cols = ['halshareWearerName', 'halshareId', 'datetime', 'temperature']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                results.append({
                    "file": file.filename,
                    "error": f"必須列が不足: {missing_cols}",
                    "status": "failed"
                })
                continue
            
            batch = UploadBatch(
                batch_id=batch_id,
                sensor_type=SensorType.SKIN_TEMPERATURE,
                file_name=file.filename,
                competition_id=competition_id,
            )
            db.add(batch)
            
            success_count = 0
            failed_count = 0
            
            # データ処理
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
                    print(f"行データ処理エラー: {e}")
            
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