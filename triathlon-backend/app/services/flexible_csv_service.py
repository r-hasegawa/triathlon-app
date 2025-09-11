import pandas as pd
import io
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.flexible_sensor_data import (
    RawSensorData, FlexibleSensorMapping,
    SkinTemperatureData, CoreTemperatureData, 
    HeartRateData, WBGTData, SensorDataStatus, SensorType
)
from app.schemas.sensor_data import (
    UploadResponse, MappingResponse,
    DataSummaryResponse, MappingStatusResponse
)

class FlexibleCSVService:
    
    async def process_sensor_data_only(
        self,
        sensor_file: UploadFile,
        sensor_type: SensorType,
        competition_id: str,  # ✅ Optional[str] → str (必須)
        db: Session
    ) -> UploadResponse:
        """センサーデータのみ処理"""
        try:
            # ✅ 大会存在チェック追加
            from app.models import Competition
            competition = db.query(Competition).filter_by(competition_id=competition_id).first()
            if not competition:
                raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
            
            content = await sensor_file.read()
            df = pd.read_csv(io.BytesIO(content))
            
            processed = 0
            
            for _, row in df.iterrows():
                raw_data = RawSensorData(
                    sensor_type=sensor_type,
                    sensor_id=str(row.get('sensor_id', '')),
                    timestamp=pd.to_datetime(row.get('timestamp')),
                    data_values=str(row.get('value', 0)),
                    competition_id=competition_id,  # ✅ 必須で設定
                    mapping_status=SensorDataStatus.UNMAPPED,
                    raw_data=row.to_json()
                )
                db.add(raw_data)
                processed += 1
            
            db.commit()
            
            return UploadResponse(
                success=True,
                message=f"{sensor_type.value}データを{processed}件処理しました（大会: {competition.name}）",
                total_records=len(df),
                processed_records=processed
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"データ処理エラー: {str(e)}")

    async def process_wbgt_data(
        self,
        wbgt_file: UploadFile,
        competition_id: Optional[str],
        db: Session,
        overwrite: bool = True
    ) -> UploadResponse:
        """WBGT環境データ処理（1大会1つ、上書き対応）"""
        try:
            # 上書き処理：既存データを削除
            if overwrite and competition_id:
                deleted_count = db.query(WBGTData).filter_by(competition_id=competition_id).delete()
                db.commit()
                print(f"既存WBGTデータ{deleted_count}件を削除しました")
            
            content = await wbgt_file.read()
            df = pd.read_csv(io.BytesIO(content))
            
            processed = 0
            
            for _, row in df.iterrows():
                wbgt_data = WBGTData(
                    timestamp=pd.to_datetime(row.get('timestamp')),
                    wbgt_value=float(row.get('wbgt_value', 0)),
                    air_temperature=float(row.get('temperature', 0)) if pd.notna(row.get('temperature')) else None,
                    humidity=float(row.get('humidity', 0)) if pd.notna(row.get('humidity')) else None,
                    location=str(row.get('location', '')),
                    competition_id=competition_id,
                    station_id=str(row.get('station_id', 'WBGT_STATION'))
                )
                db.add(wbgt_data)
                processed += 1
            
            db.commit()
            
            return UploadResponse(
                success=True,
                message=f"WBGTデータを{processed}件処理しました（上書き: {overwrite}）",
                total_records=len(df),
                processed_records=processed
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"WBGT処理エラー: {str(e)}")


    async def process_mapping_data(
        self,
        mapping_file: UploadFile,
        competition_id: str,  # 必須
        db: Session,
        overwrite: bool = True
    ) -> MappingResponse:
        """柔軟なマッピングデータ処理"""
        try:
            # 大会存在チェック
            from app.models import Competition
            competition = db.query(Competition).filter_by(competition_id=competition_id).first()
            if not competition:
                raise HTTPException(status_code=400, detail=f"大会ID '{competition_id}' が見つかりません")
            
            if overwrite and competition_id:
                db.query(FlexibleSensorMapping).filter_by(competition_id=competition_id).delete()
            
            content = await mapping_file.read()
            df = pd.read_csv(io.BytesIO(content))
            
            # 必須列チェック
            if 'user_id' not in df.columns:
                raise HTTPException(status_code=400, detail="user_id列が必要です")
            
            # user_id重複チェック
            duplicate_users = df[df['user_id'].duplicated()]['user_id'].tolist()
            if duplicate_users:
                raise HTTPException(
                    status_code=400, 
                    detail=f"user_idに重複があります: {duplicate_users}"
                )
            
            # 認識するセンサー列のみ（固定列名）- 個人データのみ
            recognized_sensor_columns = {
                'skin_temp_sensor_id': SensorType.SKIN_TEMPERATURE,
                'core_temp_sensor_id': SensorType.CORE_TEMPERATURE,
                'heart_rate_sensor_id': SensorType.HEART_RATE
                # WBGTは環境データなのでマッピング不要
            }
            
            # 認識する列リスト（user_id + センサー列のみ）
            recognized_columns = {'user_id'} | set(recognized_sensor_columns.keys())
            
            # 破棄される列をログ出力
            ignored_columns = set(df.columns) - recognized_columns
            if ignored_columns:
                print(f"🗑️  無視される列: {list(ignored_columns)}")
            
            processed_mappings = 0
            processed_users = 0
            updated_sensor_data = 0
            
            for _, row in df.iterrows():
                user_id = str(row.get('user_id', '')).strip()
                if not user_id:
                    continue
                
                processed_users += 1
                
                # 認識されるセンサー列のみ処理
                for col_name, sensor_type in recognized_sensor_columns.items():
                    if col_name in df.columns and pd.notna(row.get(col_name)):
                        sensor_id = str(row[col_name]).strip()
                        if sensor_id:
                            # ユーザー存在チェック
                            from app.models import User
                            user = db.query(User).filter_by(user_id=user_id).first()
                            if not user:
                                print(f"⚠️  User {user_id} not found, skipping mapping")
                                continue
                            
                            # 同一大会内での重複センサーチェック
                            existing_mapping = db.query(FlexibleSensorMapping).filter_by(
                                sensor_id=sensor_id,
                                sensor_type=sensor_type,
                                competition_id=competition_id
                            ).first()
                            
                            if existing_mapping:
                                print(f"⚠️  Sensor {sensor_id} already mapped to {existing_mapping.user_id}")
                                continue
                            
                            # 1. マッピングテーブルに保存
                            mapping_data = FlexibleSensorMapping(
                                user_id=user_id,
                                sensor_id=sensor_id,
                                sensor_type=sensor_type,
                                competition_id=competition_id
                                # subject_nameなどの関係ない列は保存しない
                            )
                            db.add(mapping_data)
                            processed_mappings += 1
                            
                            # 🆕 2. 対応するセンサーデータの状態を更新
                            from datetime import datetime
                            updated_records = db.query(RawSensorData).filter_by(
                                sensor_id=sensor_id,
                                sensor_type=sensor_type,
                                competition_id=competition_id,
                                mapping_status=SensorDataStatus.UNMAPPED
                            ).update({
                                'mapping_status': SensorDataStatus.MAPPED,
                                'mapped_user_id': user_id,
                                'mapped_at': datetime.now()
                            })
                            
                            updated_sensor_data += updated_records
                            print(f"✅ Mapped {sensor_id} to {user_id}, updated {updated_records} sensor records")
            
            db.commit()
            
            return MappingResponse(
                success=True,
                message=f"ユーザー{processed_users}人、センサーマッピング{processed_mappings}件を処理し、センサーデータ{updated_sensor_data}件を更新しました（大会: {competition.name}）",
                mapped_sensors=processed_mappings
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"マッピング処理エラー: {str(e)}")

    def get_data_summary(
        self,
        db: Session,
        competition_id: Optional[str] = None
    ) -> DataSummaryResponse:
        """データ状況サマリー"""
        
        query = db.query(RawSensorData)
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        
        total_records = query.count()
        mapped_records = query.filter_by(mapping_status=SensorDataStatus.MAPPED).count()
        unmapped_records = query.filter_by(mapping_status=SensorDataStatus.UNMAPPED).count()
        
        sensor_counts = {}
        for sensor_type in SensorType:
            count = query.filter_by(sensor_type=sensor_type).count()
            sensor_counts[sensor_type.value] = count
        
        wbgt_count = db.query(WBGTData)
        if competition_id:
            wbgt_count = wbgt_count.filter_by(competition_id=competition_id)
        wbgt_count = wbgt_count.count()
        
        mapping_count = db.query(FlexibleSensorMapping)
        if competition_id:
            mapping_count = mapping_count.filter_by(competition_id=competition_id)
        mapping_count = mapping_count.count()
        
        return DataSummaryResponse(
            total_sensor_records=total_records,
            mapped_records=mapped_records,
            unmapped_records=unmapped_records,
            sensor_type_counts=sensor_counts,
            wbgt_records=wbgt_count,
            mapping_records=mapping_count,
            competition_id=competition_id
        )

    def get_mapping_status(
        self,
        db: Session,
        competition_id: Optional[str] = None
    ) -> MappingStatusResponse:
        """マッピング状況確認"""
        
        query = db.query(RawSensorData)
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        
        status_counts = {}
        for status in SensorDataStatus:
            count = query.filter_by(mapping_status=status).count()
            status_counts[status.value] = count
        
        unmapped_by_type = {}
        for sensor_type in SensorType:
            count = query.filter(
                RawSensorData.sensor_type == sensor_type,
                RawSensorData.mapping_status == SensorDataStatus.UNMAPPED
            ).count()
            unmapped_by_type[sensor_type.value] = count
        
        return MappingStatusResponse(
            status_counts=status_counts,
            unmapped_by_sensor_type=unmapped_by_type,
            competition_id=competition_id
        )

    def get_unmapped_sensors(
        self,
        db: Session,
        sensor_type: Optional[SensorType] = None,
        competition_id: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """未マッピングセンサー一覧"""
        
        query = db.query(RawSensorData).filter_by(mapping_status=SensorDataStatus.UNMAPPED)
        
        if competition_id:
            query = query.filter_by(competition_id=competition_id)
        
        if sensor_type:
            query = query.filter_by(sensor_type=sensor_type)
        
        results = query.distinct(RawSensorData.sensor_id, RawSensorData.sensor_type).all()
        
        unmapped_sensors = {}
        for record in results:
            type_key = record.sensor_type.value
            if type_key not in unmapped_sensors:
                unmapped_sensors[type_key] = []
            if record.sensor_id not in unmapped_sensors[type_key]:
                unmapped_sensors[type_key].append(record.sensor_id)
        
        return unmapped_sensors

    # === サンプルCSVフォーマット例 ===

    def get_mapping_csv_examples():
        """マッピングCSVの例を返す"""
        return {
            "minimal": """user_id
    test_user_001
    user002
    user003""",
            
            "with_ignored_columns": """user_id,subject_name,department,age
    test_user_001,田中太郎,開発部,25
    user002,佐藤花子,営業部,30
    user003,山田次郎,総務部,28""",
            
            "with_single_sensor": """user_id,subject_name,skin_temp_sensor_id,other_info
    test_user_001,田中太郎,SKIN_SENSOR_001,備考1
    user002,佐藤花子,SKIN_SENSOR_002,備考2
    user003,山田次郎,SKIN_SENSOR_003,備考3""",
            
            "with_multiple_sensors": """user_id,skin_temp_sensor_id,core_temp_sensor_id,heart_rate_sensor_id,extra_column
    test_user_001,SKIN_SENSOR_001,CORE_SENSOR_001,HR_SENSOR_001,無視される
    user002,SKIN_SENSOR_002,CORE_SENSOR_002,HR_SENSOR_002,これも無視
    user003,SKIN_SENSOR_003,,HR_SENSOR_003,""",
            
            "partial_mapping": """user_id,subject_name,notes,skin_temp_sensor_id
    test_user_001,田中太郎,メモ1,SKIN_SENSOR_001
    user002,佐藤花子,メモ2,
    user003,山田次郎,メモ3,SKIN_SENSOR_003"""
        }