"""
app/routers/admin/data_uploads.py
データアップロード機能
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import xml.etree.ElementTree as ET
import io

from app.database import get_db
from app.models.user import AdminUser
from app.models.competition import Competition, RaceRecord
from app.models.flexible_sensor_data import FlexibleSensorMapping
from app.schemas.sensor_data import UploadResponse
from app.utils.dependencies import get_current_admin
from app.services.flexible_csv_service import FlexibleCSVService
from .utils import generate_batch_id, detect_encoding

import traceback

router = APIRouter()


@router.post("/upload/skin-temperature")
async def upload_skin_temperature_data(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """体表温データアップロード（halshare形式）"""
    # 大会存在チェック
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="指定された大会が見つかりません")
    try:
        service = FlexibleCSVService(db)
        results = []
        
        for file in files:
            if not file.filename.endswith('.csv'):
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "CSVファイルではありません"
                })
                continue
            
            # ファイル読み込み
            content = await file.read()
            encoding = detect_encoding(content)
            csv_string = content.decode(encoding)
            
            # バッチID生成
            batch_id = generate_batch_id(file.filename)
            
            # データ処理
            print("===================")
            result = service.process_skin_temperature_csv(
                csv_string=csv_string,
                competition_id=competition_id,
                batch_id=batch_id,
                filename=file.filename
            )

            print("===================")
            
            results.append(result)
        
        # return UploadResponse(
        #     message=f"{len(files)}個のファイルを処理しました",
        #     results=results
        # )
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"体表温データアップロードエラー: {str(e)}"
        )
        traceback.print_exc()


@router.post("/upload/core-temperature")
async def upload_core_temperature_data(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """カプセル体温データアップロード（e-Celcius形式）"""
    
    # 大会存在チェック
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="指定された大会が見つかりません")
    
    try:
        service = FlexibleCSVService(db)
        results = []
        
        for file in files:
            if not file.filename.endswith('.csv'):
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "CSVファイルではありません"
                })
                continue
            
            # ファイル読み込み
            content = await file.read()
            encoding = detect_encoding(content)
            csv_string = content.decode(encoding)
            
            # バッチID生成
            batch_id = generate_batch_id(file.filename)
            
            # データ処理
            result = service.process_core_temperature_csv(
                csv_string=csv_string,
                competition_id=competition_id,
                batch_id=batch_id,
                filename=file.filename
            )
            
            results.append(result)
        
        # return UploadResponse(
        #     message=f"{len(files)}個のファイルを処理しました",
        #     results=results
        # )
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"カプセル体温データアップロードエラー: {str(e)}"
        )


@router.post("/upload/heart-rate")
async def upload_heart_rate_data(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """心拍データアップロード（Garmin TCX形式）"""
    
    # 大会存在チェック
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="指定された大会が見つかりません")
    
    try:
        service = FlexibleCSVService(db)
        results = []
        
        for file in files:
            if not file.filename.lower().endswith('.tcx'):
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "TCXファイルではありません"
                })
                continue
            
            # ファイル読み込み
            content = await file.read()
            tcx_string = content.decode('utf-8')
            
            # バッチID生成
            batch_id = generate_batch_id(file.filename)
            
            # データ処理
            result = service.process_heart_rate_tcx(
                tcx_string=tcx_string,
                competition_id=competition_id,
                batch_id=batch_id,
                filename=file.filename
            )
            
            results.append(result)
        
        # return UploadResponse(
        #     message=f"{len(files)}個のファイルを処理しました",
        #     results=results
        # )
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"心拍データアップロードエラー: {str(e)}"
        )


@router.post("/upload/wbgt", response_model=UploadResponse)
async def upload_wbgt_data(
    competition_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """WBGTデータアップロード（仕様書2.4対応）"""
    
    # 大会存在チェック
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="指定された大会が見つかりません")
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSVファイルをアップロードしてください")
    
    try:
        # ファイル読み込み
        content = await file.read()
        encoding = detect_encoding(content)
        csv_string = content.decode(encoding)
        
        # バッチID生成
        batch_id = generate_batch_id(file.filename)
        
        # データ処理
        service = FlexibleCSVService(db)
        result = service.process_wbgt_csv(
            csv_string=csv_string,
            competition_id=competition_id,
            batch_id=batch_id,
            filename=file.filename
        )
        
        return UploadResponse(
            message="WBGTデータを処理しました",
            results=[result]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"WBGTデータアップロードエラー: {str(e)}"
        )


@router.post("/upload/race-records", response_model=UploadResponse)
async def upload_race_records(
    competition_id: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会記録データアップロード（仕様書2.5対応）"""
    
    # 大会存在チェック
    competition = db.query(Competition).filter_by(competition_id=competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="指定された大会が見つかりません")
    
    try:
        service = FlexibleCSVService(db)
        results = []
        
        for file in files:
            if not file.filename.endswith('.csv'):
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "CSVファイルではありません"
                })
                continue
            
            # ファイル読み込み
            content = await file.read()
            encoding = detect_encoding(content)
            csv_string = content.decode(encoding)
            
            # バッチID生成
            batch_id = generate_batch_id(file.filename)
            
            # データ処理
            result = service.process_race_record_csv(
                csv_string=csv_string,
                competition_id=competition_id,
                batch_id=batch_id,
                filename=file.filename
            )
            
            results.append(result)
        
        return UploadResponse(
            message=f"{len(files)}個のファイルを処理しました",
            results=results
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"大会記録データアップロードエラー: {str(e)}"
        )


@router.get("/upload/history")
async def get_upload_history(
    competition_id: str = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """アップロード履歴取得"""
    try:
        # アップロード履歴の簡易実装
        # 実際のプロダクションでは専用のアップロード履歴テーブルを作成することを推奨
        
        from app.models.flexible_sensor_data import (
            SkinTemperatureData, CoreTemperatureData, HeartRateData, WBGTData
        )
        from sqlalchemy import desc
        
        # 各データ型の最新アップロード情報を取得
        upload_summary = []
        
        # 体表温データ
        if competition_id:
            skin_temp_latest = db.query(SkinTemperatureData)\
                .filter_by(competition_id=competition_id)\
                .order_by(desc(SkinTemperatureData.created_at))\
                .first()
        else:
            skin_temp_latest = db.query(SkinTemperatureData)\
                .order_by(desc(SkinTemperatureData.created_at))\
                .first()
        
        if skin_temp_latest:
            upload_summary.append({
                "data_type": "skin_temperature",
                "competition_id": skin_temp_latest.competition_id,
                "latest_upload": skin_temp_latest.created_at.isoformat() if skin_temp_latest.created_at else None,
                "batch_id": getattr(skin_temp_latest, 'batch_id', None)
            })
        
        # 同様に他のデータ型についても処理...
        
        return {
            "upload_history": upload_summary,
            "note": "簡易実装版 - 詳細な履歴管理にはアップロード履歴テーブルの追加を推奨"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"アップロード履歴取得エラー: {str(e)}"
        )


@router.delete("/upload/batch/{batch_id}")
async def delete_upload_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """バッチ単位でアップロードデータを削除"""
    try:
        from app.models.flexible_sensor_data import (
            SkinTemperatureData, CoreTemperatureData, HeartRateData, WBGTData
        )
        
        # 各データ型からバッチIDに一致するデータを削除
        deleted_counts = {}
        
        # 体表温データ
        skin_temp_count = db.query(SkinTemperatureData)\
            .filter_by(batch_id=batch_id).count()
        db.query(SkinTemperatureData).filter_by(batch_id=batch_id).delete()
        deleted_counts["skin_temperature"] = skin_temp_count
        
        # カプセル体温データ
        core_temp_count = db.query(CoreTemperatureData)\
            .filter_by(batch_id=batch_id).count()
        db.query(CoreTemperatureData).filter_by(batch_id=batch_id).delete()
        deleted_counts["core_temperature"] = core_temp_count
        
        # 心拍データ
        heart_rate_count = db.query(HeartRateData)\
            .filter_by(batch_id=batch_id).count()
        db.query(HeartRateData).filter_by(batch_id=batch_id).delete()
        deleted_counts["heart_rate"] = heart_rate_count
        
        # WBGTデータ
        wbgt_count = db.query(WBGTData)\
            .filter_by(batch_id=batch_id).count()
        db.query(WBGTData).filter_by(batch_id=batch_id).delete()
        deleted_counts["wbgt"] = wbgt_count
        
        db.commit()
        
        total_deleted = sum(deleted_counts.values())
        
        if total_deleted == 0:
            raise HTTPException(
                status_code=404,
                detail=f"バッチID '{batch_id}' のデータが見つかりません"
            )
        
        return {
            "message": f"バッチID '{batch_id}' のデータ {total_deleted} 件を削除しました",
            "deleted_counts": deleted_counts
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"バッチ削除エラー: {str(e)}"
        )

@router.get("/race-records/status")
async def get_race_record_status(
    competition_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """大会記録状況取得（フロントエンド用）"""
    
    try:
        # 大会存在チェック
        competition = db.query(Competition).filter_by(competition_id=competition_id).first()
        if not competition:
            raise HTTPException(status_code=404, detail="指定された大会が見つかりません")
        
        # 該当大会の大会記録取得
        race_records = db.query(RaceRecord).filter_by(
            competition_id=competition_id
        ).all()
        
        total_records = len(race_records)
        
        # マッピングされている記録数を計算
        mapped_records = 0
        unmapped_records = 0
        
        for record in race_records:
            # このuser_idと大会でマッピングが存在するかチェック
            mapping_exists = db.query(FlexibleSensorMapping).filter_by(
                user_id=record.user_id,
                competition_id=competition_id
            ).first()
            
            if mapping_exists:
                mapped_records += 1
            else:
                unmapped_records += 1
        
        # マッピングカバレッジ計算
        mapping_coverage = (mapped_records / total_records * 100) if total_records > 0 else 0
        
        return {
            "total_records": total_records,
            "mapped_records": mapped_records,
            "unmapped_records": unmapped_records,
            "mapping_coverage": round(mapping_coverage, 1),
            "competition_id": competition_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"大会記録状況取得エラー: {str(e)}"
        )