# triathlon-backend/app/routers/admin/batches.py
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
    HeartRateData, WBGTData, SensorType
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
    """
    アップロードバッチ履歴取得
    
    Args:
        competition_id: 大会IDでフィルタ（オプション）
        sensor_type: センサータイプでフィルタ（オプション）
        limit: 取得件数制限（デフォルト50）
        
    Returns:
        バッチ履歴のリスト
    """
    try:
        # クエリ構築
        query = db.query(UploadBatch).order_by(desc(UploadBatch.uploaded_at))
        
        # フィルタ適用
        if competition_id:
            query = query.filter(UploadBatch.competition_id == competition_id)
            
        if sensor_type:
            query = query.filter(UploadBatch.sensor_type == sensor_type)
        
        # 件数制限
        batches = query.limit(limit).all()
        
        # レスポンス用データ作成
        batch_list = []
        for batch in batches:
            batch_data = {
                "batch_id": batch.batch_id,
                "sensor_type": batch.sensor_type.value if batch.sensor_type else None,
                "competition_id": batch.competition_id,
                "file_name": batch.file_name,
                "file_size": batch.file_size,
                "total_records": batch.total_records,
                "success_records": batch.success_records,
                "failed_records": batch.failed_records,
                "status": batch.status.value if batch.status else None,
                "uploaded_at": batch.uploaded_at.isoformat() if batch.uploaded_at else None,
                "uploaded_by": batch.uploaded_by,
                "notes": batch.notes,
                "error_message": batch.error_message
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
    """
    バッチ単位でアップロードデータを削除
    
    Args:
        batch_id: 削除対象のバッチID
        
    Returns:
        削除結果
    """
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

@router.get("/batches/summary")
async def get_batches_summary(
    competition_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    バッチ統計サマリー取得
    
    Args:
        competition_id: 大会IDでフィルタ（オプション）
        
    Returns:
        センサータイプ別の統計情報
    """
    try:
        query = db.query(UploadBatch)
        
        if competition_id:
            query = query.filter(UploadBatch.competition_id == competition_id)
        
        batches = query.all()
        
        # センサータイプ別集計
        summary = {}
        for sensor_type in SensorType:
            type_batches = [b for b in batches if b.sensor_type == sensor_type]
            
            summary[sensor_type.value] = {
                "batch_count": len(type_batches),
                "total_records": sum(b.total_records or 0 for b in type_batches),
                "success_records": sum(b.success_records or 0 for b in type_batches),
                "failed_records": sum(b.failed_records or 0 for b in type_batches),
                "last_upload": max(
                    (b.uploaded_at for b in type_batches if b.uploaded_at), 
                    default=None
                ).isoformat() if type_batches else None
            }
        
        return {
            "summary": summary,
            "competition_id": competition_id,
            "total_batches": len(batches)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"バッチサマリー取得エラー: {str(e)}"
        )