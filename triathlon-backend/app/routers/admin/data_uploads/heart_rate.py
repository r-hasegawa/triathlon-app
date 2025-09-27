"""
app/routers/admin/data_upload/heart_rate.py
心拍データ（TCX/XML）アップロード機能 - JST変換対応版
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

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


def parse_tcx_time_to_jst(time_str: str) -> Optional[datetime]:
    """
    TCXの時刻文字列を日本時間（JST）に変換
    
    Args:
        time_str: TCXの時刻文字列（例: "2023-07-15T08:30:00Z"）
    
    Returns:
        datetime: 日本時間（JST）のdatetimeオブジェクト
    """
    try:
        # ISO8601形式の解析
        if time_str.endswith('Z'):
            # UTC時刻の場合（例: "2023-07-15T08:30:00Z"）
            utc_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            
            # UTC → JST変換（+9時間）
            jst_time = utc_time.astimezone(timezone(timedelta(hours=9)))
            
            # タイムゾーン情報を除去してnaive datetimeとして返す
            return jst_time.replace(tzinfo=None)
            
        elif '+' in time_str or '-' in time_str[-6:]:
            # タイムゾーン付きの場合（例: "2023-07-15T08:30:00+00:00"）
            aware_time = datetime.fromisoformat(time_str)
            
            # JST に変換
            jst_time = aware_time.astimezone(timezone(timedelta(hours=9)))
            
            # タイムゾーン情報を除去
            return jst_time.replace(tzinfo=None)
            
        else:
            # タイムゾーン情報がない場合
            naive_time = datetime.fromisoformat(time_str)
            
            # ⚠️ この場合、元データがUTCかJSTか判断が困難
            # 仕様書に基づき、+9時間してJSTとして扱う
            jst_time = naive_time + timedelta(hours=9)
            
            print(f"⚠️ タイムゾーン不明の時刻を+9時間してJST扱い: {time_str} → {jst_time}")
            
            return jst_time
            
    except Exception as e:
        print(f"❌ 時刻解析エラー: {time_str} - {str(e)}")
        return None


@router.post("/upload/heart-rate")
async def upload_heart_rate(
    competition_id: str = Form(...),
    sensor_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """心拍データ（TCX/XML）アップロード - JST変換対応版"""
    
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
            errors = []
            
            # TCX名前空間
            namespaces = {
                'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'
            }
            
            # TrackPointデータを抽出
            trackpoints = root.findall('.//tcx:Trackpoint', namespaces)
            
            print(f"📊 TCX解析開始: {file.filename}")
            print(f"   - センサーID: {sensor_id}")
            print(f"   - Trackpoint数: {len(trackpoints)}")
            
            for idx, trackpoint in enumerate(trackpoints):
                try:
                    # 時刻取得
                    time_elem = trackpoint.find('tcx:Time', namespaces)
                    if time_elem is None:
                        failed_count += 1
                        continue
                    
                    time_str = time_elem.text
                    
                    # 🔧 日本時間変換処理（統合されたメソッドを使用）
                    parsed_time = parse_tcx_time_to_jst(time_str)
                    
                    if parsed_time is None:
                        errors.append(f"Trackpoint {idx+1}: 時刻解析失敗 ({time_str})")
                        failed_count += 1
                        continue
                    
                    # 心拍数取得
                    hr_elem = trackpoint.find('.//tcx:HeartRateBpm/tcx:Value', namespaces)
                    if hr_elem is None:
                        failed_count += 1
                        continue
                    
                    try:
                        heart_rate = int(hr_elem.text)
                    except (ValueError, TypeError):
                        failed_count += 1
                        continue
                    
                    # データベースに保存
                    heart_rate_data = HeartRateData(
                        sensor_id=sensor_id,
                        time=parsed_time,  # 日本時間に変換済み
                        heart_rate=heart_rate,
                        upload_batch_id=batch_id,
                        competition_id=competition_id
                    )
                    db.add(heart_rate_data)
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Trackpoint {idx+1}: {str(e)}")
                    failed_count += 1
                    continue
            
            # バッチステータス更新
            if success_count > 0:
                batch.status = UploadStatus.SUCCESS if failed_count == 0 else UploadStatus.PARTIAL
                batch.total_records = len(trackpoints)
                batch.success_records = success_count
                batch.failed_records = failed_count
                batch.notes = f"センサーID: {sensor_id}, 日本時間変換適用"
            else:
                batch.status = UploadStatus.FAILED
                batch.total_records = len(trackpoints)
                batch.success_records = 0
                batch.failed_records = failed_count
                batch.notes = f"全件失敗: {errors[0] if errors else '不明なエラー'}"
            
            db.commit()
            
            print(f"✅ TCX処理完了: {success_count}件成功, {failed_count}件失敗")
            
            results.append({
                "file": file.filename,
                "status": "success" if success_count > 0 else "failed",
                "batch_id": batch_id,
                "total": len(trackpoints),
                "success": success_count,
                "failed": failed_count,
                "sensor_id": sensor_id,
                "error": errors[0] if errors and success_count == 0 else None,
                "message": f"心拍データ {success_count}件を日本時間で保存しました"
            })
            
        except Exception as e:
            results.append({
                "file": file.filename,
                "status": "failed",
                "error": f"ファイル処理エラー: {str(e)}",
                "total": 0,
                "success": 0,
                "failed": 0
            })
    
    return {
        "message": f"{len(files)}個のTCXファイルを処理しました",
        "results": results,
        "competition_id": competition_id
    }
