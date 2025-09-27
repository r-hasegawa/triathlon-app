"""
app/routers/admin/data_uploads.py
データアップロード機能（FlexibleCSVService不使用 - 元のadmin.py方式）
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import xml.etree.ElementTree as ET
import io
from datetime import datetime

from app.database import get_db
from app.models.user import AdminUser
from app.models.competition import Competition, RaceRecord
from app.models.flexible_sensor_data import (
    FlexibleSensorMapping,
    SkinTemperatureData, 
    CoreTemperatureData, 
    HeartRateData, 
    WBGTData, 
    SensorDataStatus, 
    SensorType,
    UploadBatch, 
    SensorType, 
    UploadStatus
)
from app.utils.dependencies import get_current_admin
from app.services.flexible_csv_service import FlexibleCSVService
from .utils import generate_batch_id, detect_encoding


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


@router.post("/upload/wbgt")
async def upload_wbgt_data(
    competition_id: str = Form(...),
    wbgt_file: UploadFile = File(...),
    overwrite: bool = Form(True),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """WBGT環境データアップロード - 元のadmin.py方式"""
    
    if not wbgt_file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSVファイルのみアップロード可能です")
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
    
    try:
        # 上書き処理：既存データを削除
        if overwrite:
            deleted_count = db.query(WBGTData).filter_by(competition_id=competition_id).delete()
            db.commit()
            print(f"既存WBGTデータ{deleted_count}件を削除しました")
        
        # CSVファイル読み込み
        content = await wbgt_file.read()
        
        # エンコーディング検出・読み込み
        encoding = detect_encoding(content)
        try:
            decoded_content = content.decode(encoding)
        except UnicodeDecodeError:
            # フォールバック：Shift_JIS（日本の機器）
            try:
                decoded_content = content.decode('shift_jis')
            except UnicodeDecodeError:
                decoded_content = content.decode('utf-8', errors='replace')
        
        # CSVパース
        df = pd.read_csv(io.StringIO(decoded_content))
        
        # 列名マッピング（日本語・英語両対応）
        column_mapping = {
            'date': None,
            'time': None,
            'wbgt': None,
            'air_temperature': None,
            'humidity': None,
            'globe_temperature': None
        }
        
        # 列名を正規化して検索
        for col in df.columns:
            col_clean = str(col).strip().lower()
            if '日付' in col or 'date' in col_clean:
                column_mapping['date'] = col
            elif '時刻' in col or 'time' in col_clean:
                column_mapping['time'] = col
            elif 'wbgt' in col_clean:
                column_mapping['wbgt'] = col
            elif '気温' in col or 'air' in col_clean:
                column_mapping['air_temperature'] = col
            elif '湿度' in col or 'humidity' in col_clean:
                column_mapping['humidity'] = col
            elif '黒球' in col or 'globe' in col_clean:
                column_mapping['globe_temperature'] = col
        
        # 必須列チェック
        if not column_mapping['date'] or not column_mapping['time'] or not column_mapping['wbgt']:
            raise HTTPException(
                status_code=400,
                detail=f"必須列が見つかりません。現在の列: {list(df.columns)}"
            )
        
        # バッチID生成
        batch_id = generate_batch_id(wbgt_file.filename)
        
        # UploadBatch作成
        batch = UploadBatch(
            batch_id=batch_id,
            sensor_type=SensorType.WBGT,
            file_name=wbgt_file.filename,
            competition_id=competition_id,
        )
        db.add(batch)
        
        success_count = 0
        failed_count = 0
        
        # データ処理
        for index, row in df.iterrows():
            try:
                # 日付と時刻の結合
                date_str = str(row[column_mapping['date']]).strip()
                time_str = str(row[column_mapping['time']]).strip()
                
                if pd.isna(row[column_mapping['date']]) or pd.isna(row[column_mapping['time']]):
                    failed_count += 1
                    continue
                
                # 日時パース
                datetime_str = f"{date_str} {time_str}"
                datetime_obj = pd.to_datetime(datetime_str)
                
                # WBGT値取得
                wbgt_value = float(row[column_mapping['wbgt']])
                
                # オプション値取得
                air_temp = None
                humidity = None
                globe_temp = None
                
                if column_mapping['air_temperature']:
                    try:
                        air_temp = float(row[column_mapping['air_temperature']])
                    except (ValueError, TypeError):
                        pass
                
                if column_mapping['humidity']:
                    try:
                        humidity = float(row[column_mapping['humidity']])
                    except (ValueError, TypeError):
                        pass
                
                if column_mapping['globe_temperature']:
                    try:
                        globe_temp = float(row[column_mapping['globe_temperature']])
                    except (ValueError, TypeError):
                        pass
                
                # WBGTDataオブジェクト作成
                wbgt_data = WBGTData(
                    timestamp=datetime_obj,
                    wbgt_value=wbgt_value,
                    air_temperature=air_temp,
                    humidity=humidity,
                    globe_temperature=globe_temp,
                    competition_id=competition_id,
                    upload_batch_id=batch_id
                )
                db.add(wbgt_data)
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                print(f"行{index+1}処理エラー: {e}")
        
        # バッチ情報更新
        batch.total_records = success_count + failed_count
        batch.success_records = success_count
        batch.failed_records = failed_count
        batch.status = UploadStatus.SUCCESS if failed_count == 0 else UploadStatus.PARTIAL
        
        db.commit()
        
        return {
            "success": success_count > 0,
            "message": f"WBGT環境データアップロード完了",
            "total_records": success_count + failed_count,
            "processed_records": success_count,
            "failed_records": failed_count,
            "batch_id": batch_id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"WBGTアップロード失敗: {str(e)}")



@router.get("/race-records/status")
async def get_race_records_status(
    competition_id: str = Query(None),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会記録アップロード状況取得"""
    
    try:
        from app.models.competition import RaceRecord
        query = db.query(RaceRecord)
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        
        records = query.all()
        
        total_records = len(records)
        mapped_records = len([r for r in records if r.user_id is not None])
        unmapped_records = total_records - mapped_records
        
        by_competition = {}
        for record in records:
            comp_id = record.competition_id
            if comp_id not in by_competition:
                competition = db.query(Competition).filter_by(competition_id=comp_id).first()
                by_competition[comp_id] = {
                    "competition_name": competition.name if competition else "Unknown",
                    "total_records": 0,
                    "mapped_records": 0,
                    "unmapped_records": 0
                }
            
            by_competition[comp_id]["total_records"] += 1
            if record.user_id:
                by_competition[comp_id]["mapped_records"] += 1
            else:
                by_competition[comp_id]["unmapped_records"] += 1
        
        return {
            "success": True,
            "total_records": total_records,
            "mapped_records": mapped_records,
            "unmapped_records": unmapped_records,
            "mapping_coverage": round((mapped_records / total_records * 100), 2) if total_records > 0 else 0,
            "competitions": by_competition,
            "competition_count": len(by_competition)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"大会記録状況取得エラー: {str(e)}")


# ===== マッピング関連エンドポイント =====

@router.post("/upload/mapping")
async def upload_mapping_data(
    mapping_file: UploadFile = File(...),
    competition_id: str = Form(...),
    overwrite: bool = Form(True),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """マッピングデータアップロード（FlexibleCSVService使用）"""
    
    if not mapping_file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSVファイルのみアップロード可能です")
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
    
    csv_service = FlexibleCSVService()
    
    try:
        content = await mapping_file.read()
        await mapping_file.seek(0)
        
        result = await csv_service.process_mapping_data(
            mapping_file=mapping_file,
            competition_id=competition_id,
            db=db,
            overwrite=overwrite
        )
        
        batch_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{mapping_file.filename}"
        
        batch = UploadBatch(
            batch_id=batch_id,
            sensor_type=SensorType.OTHER,
            competition_id=competition_id,
            file_name=mapping_file.filename,
            total_records=result["total_records"],
            success_records=result["processed_records"],
            failed_records=result["skipped_records"],
            status=UploadStatus.SUCCESS if result["success"] else UploadStatus.PARTIAL
        )
        db.add(batch)
        db.commit()
        
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


@router.post("/upload/race-records")
async def upload_race_records(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会記録データアップロード（FlexibleCSVService使用）"""
    
    for file in files:
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail=f"CSVファイルのみアップロード可能です: {file.filename}")
    
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="最低1つのCSVファイルが必要です")
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
    
    csv_service = FlexibleCSVService()
    
    try:
        file_info = []
        
        for file in files:
            content = await file.read()
            await file.seek(0)
        
        result = await csv_service.process_race_record_data(
            race_files=files,
            competition_id=competition_id,
            db=db
        )
        
        result.update({
            "competition_id": competition_id,
            "competition_name": competition.name,
            "uploaded_files": file_info,
            "upload_time": datetime.now().isoformat(),
            "uploaded_by": current_admin.admin_id
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"大会記録アップロード失敗: {str(e)}")
