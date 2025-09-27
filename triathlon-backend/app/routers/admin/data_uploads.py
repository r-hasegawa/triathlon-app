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

from app.database import get_db
from app.models.user import AdminUser
from app.models.competition import Competition
from app.utils.dependencies import get_current_admin
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
            
            # UploadBatch作成
            from app.models.flexible_sensor_data import UploadBatch, SensorType, UploadStatus, SkinTemperatureData
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
            
            # UploadBatch作成
            from app.models.flexible_sensor_data import UploadBatch, SensorType, UploadStatus, CoreTemperatureData
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
            
            # UploadBatch作成
            from app.models.flexible_sensor_data import UploadBatch, SensorType, UploadStatus, HeartRateData
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
            print("================================")
            results.append({
                "file": file.filename,
                "batch_id": batch_id,
                "total": success_count + failed_count,
                "success": success_count,
                "failed": failed_count,
                "status": batch.status.value
            })
            print("|||||||||||||||||||||||||||||||")
            print(batch.status.value)
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
            from app.models.flexible_sensor_data import WBGTData
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
        from app.models.flexible_sensor_data import UploadBatch, SensorType, UploadStatus, WBGTData
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


@router.post("/upload/race-records")
async def upload_race_records(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    overwrite: bool = Form(True),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会記録データアップロード - 元のadmin.py方式"""
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="大会が見つかりません")
    
    try:
        # 上書き処理：既存データを削除
        if overwrite:
            from app.models.competition import RaceRecord
            deleted_count = db.query(RaceRecord).filter_by(competition_id=competition_id).delete()
            db.commit()
            print(f"既存大会記録データ{deleted_count}件を削除しました")
        
        total_csv_records = 0
        saved_records = 0
        failed_records = 0
        errors = []
        
        for file in files:
            if not file.filename.endswith('.csv'):
                errors.append(f"ファイル '{file.filename}' はCSVではありません")
                continue
            
            try:
                # CSVファイル読み込み
                content = await file.read()
                encoding = detect_encoding(content)
                
                try:
                    df = pd.read_csv(io.BytesIO(content), encoding=encoding)
                except UnicodeDecodeError:
                    # フォールバック処理
                    for fallback_encoding in ['utf-8', 'shift_jis', 'cp932']:
                        try:
                            df = pd.read_csv(io.BytesIO(content), encoding=fallback_encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        errors.append(f"ファイル '{file.filename}' の文字コードを認識できませんでした")
                        continue
                
                print(f"📊 {file.filename}: {len(df)}行, 列: {list(df.columns)}")
                
                # 列名の空白除去
                df.columns = df.columns.str.strip()
                
                # ゼッケン番号列の検索
                bib_number_col = None
                for col in df.columns:
                    if any(keyword in str(col).lower() for keyword in ['no.', 'no', 'ゼッケン', 'bib', '番号']):
                        bib_number_col = col
                        break
                
                if not bib_number_col:
                    errors.append(f"ファイル '{file.filename}' にゼッケン番号列が見つかりません")
                    continue
                
                # 認識可能な列マッピング
                column_mapping = {
                    'swim_start': None,
                    'swim_finish': None,
                    'bike_start': None,
                    'bike_finish': None,
                    'run_start': None,
                    'run_finish': None
                }
                
                # LAP列の検索
                lap_columns = []
                
                for col in df.columns:
                    col_lower = str(col).lower()
                    if 'swim' in col_lower and 'start' in col_lower:
                        column_mapping['swim_start'] = col
                    elif 'swim' in col_lower and ('finish' in col_lower or 'end' in col_lower):
                        column_mapping['swim_finish'] = col
                    elif 'bike' in col_lower and 'start' in col_lower:
                        column_mapping['bike_start'] = col
                    elif 'bike' in col_lower and ('finish' in col_lower or 'end' in col_lower):
                        column_mapping['bike_finish'] = col
                    elif 'run' in col_lower and 'start' in col_lower:
                        column_mapping['run_start'] = col
                    elif 'run' in col_lower and ('finish' in col_lower or 'end' in col_lower):
                        column_mapping['run_finish'] = col
                    elif any(lap_keyword in col_lower for lap_keyword in ['lap', 'bl', 'checkpoint']):
                        lap_columns.append(col)
                
                # データ処理
                file_records = 0
                for index, row in df.iterrows():
                    try:
                        # ゼッケン番号取得
                        bib_number = str(row[bib_number_col]).strip()
                        if not bib_number or bib_number == 'nan':
                            continue
                        
                        # 時刻データの解析
                        def parse_time(time_str):
                            if pd.isna(time_str) or str(time_str).strip() == '':
                                return None
                            try:
                                return pd.to_datetime(str(time_str).strip())
                            except:
                                return None
                        
                        # 基本競技時刻
                        swim_start = parse_time(row.get(column_mapping['swim_start']))
                        swim_finish = parse_time(row.get(column_mapping['swim_finish']))
                        bike_start = parse_time(row.get(column_mapping['bike_start']))
                        bike_finish = parse_time(row.get(column_mapping['bike_finish']))
                        run_start = parse_time(row.get(column_mapping['run_start']))
                        run_finish = parse_time(row.get(column_mapping['run_finish']))
                        
                        # LAP時刻データ収集
                        lap_times = {}
                        for lap_col in lap_columns:
                            lap_time = parse_time(row.get(lap_col))
                            if lap_time:
                                lap_times[lap_col] = lap_time.isoformat()
                        
                        # RaceRecordオブジェクト作成
                        from app.models.competition import RaceRecord
                        race_record = RaceRecord(
                            competition_id=competition_id,
                            race_number=bib_number,  # ゼッケン番号
                            user_id=None,  # マッピング前は空
                            swim_start=swim_start,
                            swim_finish=swim_finish,
                            bike_start=bike_start,
                            bike_finish=bike_finish,
                            run_start=run_start,
                            run_finish=run_finish,
                            lap_times=lap_times if lap_times else None,
                            source_file=file.filename
                        )
                        
                        db.add(race_record)
                        file_records += 1
                        saved_records += 1
                        
                    except Exception as e:
                        failed_records += 1
                        errors.append(f"ファイル '{file.filename}' 行{index+1}: {str(e)}")
                
                total_csv_records += len(df)
                print(f"✅ {file.filename}: {file_records}件保存")
                
            except Exception as e:
                errors.append(f"ファイル '{file.filename}' 処理エラー: {str(e)}")
        
        db.commit()
        
        return {
            "success": saved_records > 0,
            "message": f"大会記録アップロード完了: {saved_records}件保存",
            "total_csv_records": total_csv_records,
            "saved_records": saved_records,
            "failed_records": failed_records,
            "errors": errors
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"大会記録アップロードエラー: {str(e)}"
        )


@router.post("/upload/mapping")
async def upload_mapping_data(
    mapping_file: UploadFile = File(...),
    competition_id: str = Form(...),
    overwrite: bool = Form(True),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """マッピングデータアップロード - 元のadmin.py方式"""
    
    if not mapping_file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSVファイルのみアップロード可能です")
    
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
    
    try:
        # 上書き処理：既存マッピングを削除
        if overwrite:
            from app.models.flexible_sensor_data import FlexibleSensorMapping
            existing_count = db.query(FlexibleSensorMapping).filter_by(competition_id=competition_id).delete()
            db.commit()
            print(f"既存マッピング削除: {existing_count}件")
        
        # CSVファイル読み込み
        content = await mapping_file.read()
        encoding = detect_encoding(content)
        
        try:
            df = pd.read_csv(io.BytesIO(content), encoding=encoding)
        except UnicodeDecodeError:
            # フォールバック処理
            for fallback_encoding in ['utf-8', 'shift_jis', 'cp932']:
                try:
                    df = pd.read_csv(io.BytesIO(content), encoding=fallback_encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise HTTPException(status_code=400, detail="CSVファイル読み込み失敗")
        
        if df.empty:
            raise HTTPException(status_code=400, detail="CSVファイルが空です")
        
        # 列名の空白除去
        df.columns = df.columns.str.strip()
        
        # 必須列チェック
        if 'user_id' not in df.columns:
            raise HTTPException(status_code=400, detail="user_id列が必要です")
        
        # 認識するセンサー列
        sensor_column_mapping = {
            'skin_temp_sensor_id': 'skin_temperature_sensor_id',
            'core_temp_sensor_id': 'core_temperature_sensor_id',
            'heart_rate_sensor_id': 'heart_rate_sensor_id',
            'skin_temperature_sensor_id': 'skin_temperature_sensor_id',
            'core_temperature_sensor_id': 'core_temperature_sensor_id',
            'heart_rate_id': 'heart_rate_sensor_id',
        }
        
        # 大会記録列
        race_number_col = None
        for col in df.columns:
            if any(keyword in str(col).lower() for keyword in ['race_number', 'ゼッケン', 'bib', 'no']):
                race_number_col = col
                break
        
        processed = 0
        skipped = 0
        errors = []
        race_number_mappings = 0
        
        for index, row in df.iterrows():
            try:
                user_id = str(row.get('user_id', '')).strip()
                
                if not user_id or user_id == 'nan':
                    skipped += 1
                    continue
                
                # ユーザー存在チェック
                from app.models.user import User
                user = db.query(User).filter_by(user_id=user_id).first()
                if not user:
                    errors.append(f"行{index+1}: ユーザーID '{user_id}' が見つかりません")
                    skipped += 1
                    continue
                
                # センサーIDの収集
                sensor_data = {}
                for csv_col, mapped_col in sensor_column_mapping.items():
                    if csv_col in df.columns:
                        sensor_id = str(row.get(csv_col, '')).strip()
                        if sensor_id and sensor_id != 'nan':
                            sensor_data[mapped_col] = sensor_id
                
                # ゼッケン番号の処理
                race_number = None
                if race_number_col and race_number_col in df.columns:
                    race_num_value = str(row.get(race_number_col, '')).strip()
                    if race_num_value and race_num_value != 'nan':
                        race_number = race_num_value
                
                # マッピング作成
                from app.models.flexible_sensor_data import FlexibleSensorMapping
                mapping = FlexibleSensorMapping(
                    user_id=user_id,
                    competition_id=competition_id,
                    skin_temperature_sensor_id=sensor_data.get('skin_temperature_sensor_id'),
                    core_temperature_sensor_id=sensor_data.get('core_temperature_sensor_id'),
                    heart_rate_sensor_id=sensor_data.get('heart_rate_sensor_id'),
                    race_number=race_number
                )
                
                db.add(mapping)
                processed += 1
                
                # 大会記録にuser_idを適用
                if race_number:
                    from app.models.competition import RaceRecord
                    race_records = db.query(RaceRecord).filter_by(
                        competition_id=competition_id,
                        race_number=race_number
                    ).all()
                    
                    for record in race_records:
                        record.user_id = user_id
                        race_number_mappings += 1
                
            except Exception as e:
                errors.append(f"行{index+1}: {str(e)}")
                skipped += 1
        
        db.commit()
        
        return {
            "success": processed > 0,
            "message": f"マッピング処理完了: {processed}件作成",
            "total_records": len(df),
            "processed_records": processed,
            "skipped_records": skipped,
            "race_number_mappings": race_number_mappings,
            "errors": errors
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"マッピングアップロード失敗: {str(e)}")

# data_uploads.py に追加するエンドポイント

@router.get("/race-records/status")
async def get_race_records_status(
    competition_id: str = Query(None),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会記録アップロード状況取得"""
    
    try:
        # クエリ構築
        from app.models.competition import RaceRecord
        query = db.query(RaceRecord)
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        
        records = query.all()
        
        # 統計計算
        total_records = len(records)
        mapped_records = len([r for r in records if r.user_id is not None])
        unmapped_records = total_records - mapped_records
        
        # 大会別統計
        by_competition = {}
        for record in records:
            comp_id = record.competition_id
            if comp_id not in by_competition:
                competition = db.query(Competition).filter_by(competition_id=comp_id).first()
                by_competition[comp_id] = {
                    "competition_name": competition.name if competition else "Unknown",
                    "total_records": 0,
                    "mapped_records": 0,
                    "unmapped_records": 0,
                    "latest_upload": None
                }
            
            by_competition[comp_id]["total_records"] += 1
            if record.user_id:
                by_competition[comp_id]["mapped_records"] += 1
            else:
                by_competition[comp_id]["unmapped_records"] += 1
            
            # 最新アップロード時刻（created_atがある場合）
            if hasattr(record, 'created_at') and record.created_at:
                current_latest = by_competition[comp_id]["latest_upload"]
                record_time_str = record.created_at.isoformat()
                if current_latest is None or record_time_str > current_latest:
                    by_competition[comp_id]["latest_upload"] = record_time_str
        
        # レスポンス構築
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
        error_message = f"大会記録状況取得エラー: {str(e)}"
        print(f"❌ {error_message}")
        raise HTTPException(status_code=500, detail=error_message)


@router.get("/race-records/details")
async def get_race_records_details(
    competition_id: str = Query(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会記録詳細情報取得"""
    
    try:
        # 大会存在チェック
        competition = db.query(Competition).filter_by(competition_id=competition_id).first()
        if not competition:
            raise HTTPException(status_code=404, detail="Competition not found")
        
        # 大会記録取得
        from app.models.competition import RaceRecord
        records = db.query(RaceRecord).filter_by(competition_id=competition_id).all()
        
        race_details = []
        for record in records:
            # 競技時間計算
            swim_duration = None
            bike_duration = None
            run_duration = None
            total_duration = None
            
            if record.swim_start and record.swim_finish:
                swim_duration = (record.swim_finish - record.swim_start).total_seconds()
            
            if record.bike_start and record.bike_finish:
                bike_duration = (record.bike_finish - record.bike_start).total_seconds()
            
            if record.run_start and record.run_finish:
                run_duration = (record.run_finish - record.run_start).total_seconds()
            
            # 全体時間の計算
            if record.swim_start and record.run_finish:
                total_duration = (record.run_finish - record.swim_start).total_seconds()
            
            # ユーザー情報取得
            user_info = None
            if record.user_id:
                from app.models.user import User
                user = db.query(User).filter_by(user_id=record.user_id).first()
                if user:
                    user_info = {
                        "user_id": user.user_id,
                        "full_name": user.full_name,
                        "email": user.email
                    }
            
            race_details.append({
                "id": record.id,
                "race_number": record.race_number,
                "user_id": record.user_id,
                "user_info": user_info,
                "is_mapped": record.user_id is not None,
                "swim_start": record.swim_start.isoformat() if record.swim_start else None,
                "swim_finish": record.swim_finish.isoformat() if record.swim_finish else None,
                "bike_start": record.bike_start.isoformat() if record.bike_start else None,
                "bike_finish": record.bike_finish.isoformat() if record.bike_finish else None,
                "run_start": record.run_start.isoformat() if record.run_start else None,
                "run_finish": record.run_finish.isoformat() if record.run_finish else None,
                "swim_duration_seconds": swim_duration,
                "bike_duration_seconds": bike_duration,
                "run_duration_seconds": run_duration,
                "total_duration_seconds": total_duration,
                "lap_times": record.lap_times,  # JSON形式のLAPデータ
                "source_file": record.source_file,
                "created_at": record.created_at.isoformat() if hasattr(record, 'created_at') and record.created_at else None
            })
        
        return {
            "success": True,
            "competition_id": competition_id,
            "competition_name": competition.name,
            "total_records": len(records),
            "records": race_details
        }
        
    except Exception as e:
        error_message = f"大会記録詳細取得エラー: {str(e)}"
        print(f"❌ {error_message}")
        raise HTTPException(status_code=500, detail=error_message)


@router.delete("/race-records/{competition_id}")
async def delete_race_records(
    competition_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会記録削除"""
    
    try:
        # 大会存在チェック
        competition = db.query(Competition).filter_by(competition_id=competition_id).first()
        if not competition:
            raise HTTPException(status_code=404, detail="Competition not found")
        
        # 削除実行
        from app.models.competition import RaceRecord
        deleted_count = db.query(RaceRecord).filter_by(competition_id=competition_id).delete()
        db.commit()
        
        return {
            "success": True,
            "message": f"大会'{competition.name}'の記録{deleted_count}件を削除しました",
            "deleted_records": deleted_count,
            "competition_id": competition_id
        }
        
    except Exception as e:
        db.rollback()
        error_message = f"大会記録削除エラー: {str(e)}"
        print(f"❌ {error_message}")
        raise HTTPException(status_code=500, detail=error_message)
