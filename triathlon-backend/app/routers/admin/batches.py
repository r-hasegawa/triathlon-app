# app/routers/admin/batches.py (完全修正版)

"""
管理者用バッチ管理エンドポイント
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.user import AdminUser
from app.models.flexible_sensor_data import (
    UploadBatch, SkinTemperatureData, CoreTemperatureData, 
    HeartRateData, WBGTData, FlexibleSensorMapping, SensorType
)
from app.utils.dependencies import get_current_admin

router = APIRouter()

@router.get("/batches")
async def get_upload_batches(
    competition_id: Optional[str] = Query(None, description="大会IDでフィルタ"),
    sensor_type: Optional[str] = Query(None, description="センサータイプでフィルタ"), 
    limit: int = Query(50, description="取得件数制限"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """アップロードバッチ履歴取得"""
    try:
        query = db.query(UploadBatch).order_by(desc(UploadBatch.uploaded_at))
        
        if competition_id:
            query = query.filter(UploadBatch.competition_id == competition_id)
            
        if sensor_type:
            query = query.filter(UploadBatch.sensor_type == sensor_type)
        
        batches = query.limit(limit).all()
        
        batch_list = []
        for batch in batches:
            batch_data = {
                "batch_id": batch.batch_id,
                "sensor_type": batch.sensor_type.value if batch.sensor_type else None,
                "competition_id": batch.competition_id,
                "file_name": batch.file_name,
                "total_records": batch.total_records,
                "success_records": batch.success_records,
                "failed_records": batch.failed_records,
                "status": batch.status.value if batch.status else None,
                "uploaded_at": batch.uploaded_at.isoformat() if batch.uploaded_at else None
            }
            batch_list.append(batch_data)
        
        return {
            "batches": batch_list,
            "total": len(batch_list),
            "filtered": {
                "competition_id": competition_id,
                "sensor_type": sensor_type
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"バッチ履歴取得エラー: {str(e)}"
        )


@router.delete("/batches/{batch_id}")
async def delete_upload_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """バッチ単位でアップロードデータを削除（マッピング対応版）"""
    
    try:
        # バッチ存在確認
        batch = db.query(UploadBatch).filter_by(batch_id=batch_id).first()
        if not batch:
            raise HTTPException(
                status_code=404,
                detail=f"バッチID '{batch_id}' が見つかりません"
            )
        
        deleted_counts = {}
        
        # センサータイプ別にデータ削除
        if batch.sensor_type == SensorType.SKIN_TEMPERATURE:
            count = db.query(SkinTemperatureData)\
                .filter_by(upload_batch_id=batch_id).count()
            db.query(SkinTemperatureData)\
                .filter_by(upload_batch_id=batch_id).delete()
            deleted_counts["skin_temperature_data"] = count
            
        elif batch.sensor_type == SensorType.CORE_TEMPERATURE:
            count = db.query(CoreTemperatureData)\
                .filter_by(upload_batch_id=batch_id).count()
            db.query(CoreTemperatureData)\
                .filter_by(upload_batch_id=batch_id).delete()
            deleted_counts["core_temperature_data"] = count
            
        elif batch.sensor_type == SensorType.HEART_RATE:
            count = db.query(HeartRateData)\
                .filter_by(upload_batch_id=batch_id).count()
            db.query(HeartRateData)\
                .filter_by(upload_batch_id=batch_id).delete()
            deleted_counts["heart_rate_data"] = count
            
        elif batch.sensor_type == SensorType.WBGT:
            count = db.query(WBGTData)\
                .filter_by(upload_batch_id=batch_id).count()
            db.query(WBGTData)\
                .filter_by(upload_batch_id=batch_id).delete()
            deleted_counts["wbgt_data"] = count
        
        # 🆕 マッピングデータの削除処理を追加
        elif batch.sensor_type == SensorType.OTHER:
            count = db.query(FlexibleSensorMapping)\
                .filter_by(upload_batch_id=batch_id).count()
            db.query(FlexibleSensorMapping)\
                .filter_by(upload_batch_id=batch_id).delete()
            deleted_counts["mapping_data"] = count

        # 🆕 大会記録データの削除処理を追加
        elif batch.sensor_type == SensorType.RACE_RECORD:
            from app.models.competition import RaceRecord
            count = db.query(RaceRecord)\
                .filter_by(upload_batch_id=batch_id).count()
            db.query(RaceRecord)\
                .filter_by(upload_batch_id=batch_id).delete()
            deleted_counts["race_record_data"] = count
        
        # バッチレコード自体も削除
        db.delete(batch)
        db.commit()
        
        total_deleted = sum(deleted_counts.values())
        
        return {
            "message": f"バッチ '{batch_id}' とデータ {total_deleted} 件を削除しました",
            "batch_info": {
                "batch_id": batch_id,
                "sensor_type": batch.sensor_type.value if batch.sensor_type else None,
                "file_name": batch.file_name
            },
            "deleted_counts": deleted_counts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"バッチ削除エラー: {str(e)}"
        )