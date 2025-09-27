"""
app/routers/admin/data_upload/wbgt.py
WBGT環境データアップロード機能
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import pandas as pd
import io

from app.database import get_db
from app.models.user import AdminUser
from app.models.competition import Competition
from app.models.flexible_sensor_data import (
    WBGTData, 
    UploadBatch, 
    SensorType,
    UploadStatus
)
from app.utils.dependencies import get_current_admin
from ..utils import generate_batch_id, detect_encoding


router = APIRouter()


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