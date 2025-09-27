# app/schemas/feedback.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

class CompetitionRace(BaseModel):
    """大会情報"""
    id: str = Field(..., description="大会ID")
    name: str = Field(..., description="大会名")
    date: str = Field(..., description="大会日時（ISO形式）")
    description: Optional[str] = Field(None, description="大会説明")

class SensorDataPoint(BaseModel):
    """センサーデータポイント"""
    timestamp: str = Field(..., description="タイムスタンプ（ISO形式）")
    skin_temperature: Optional[float] = Field(None, description="体表温度（°C）")
    core_temperature: Optional[float] = Field(None, description="カプセル体温（°C）")
    wbgt_temperature: Optional[float] = Field(None, description="WBGT温度（°C）")
    heart_rate: Optional[int] = Field(None, description="心拍数（bpm）")
    sensor_id: Optional[str] = Field(None, description="センサーID")
    data_type: Optional[str] = Field(None, description="データタイプ")

class LapRecord(BaseModel):
    """LAP記録"""
    lap_number: int = Field(..., description="LAP番号")
    lap_time: str = Field(..., description="LAP時刻（ISO形式）")
    split_time: Optional[str] = Field(None, description="スプリット時間")
    segment_type: Optional[str] = Field(None, description="区間タイプ（swim/bike/run）")

class RaceRecord(BaseModel):
    """大会記録"""
    competition_id: str = Field(..., description="大会ID")
    user_id: str = Field(..., description="ユーザーID")
    
    # 競技区間の開始・終了時刻
    swim_start: Optional[str] = Field(None, description="スイム開始時刻（ISO形式）")
    swim_finish: Optional[str] = Field(None, description="スイム終了時刻（ISO形式）")
    bike_start: Optional[str] = Field(None, description="バイク開始時刻（ISO形式）")
    bike_finish: Optional[str] = Field(None, description="バイク終了時刻（ISO形式）")
    run_start: Optional[str] = Field(None, description="ラン開始時刻（ISO形式）")
    run_finish: Optional[str] = Field(None, description="ラン終了時刻（ISO形式）")
    
    # LAP記録（可変数）
    lap_records: Optional[List[LapRecord]] = Field(None, description="LAP記録一覧")

class FeedbackStatistics(BaseModel):
    """フィードバック統計情報"""
    total_records: int = Field(..., description="総レコード数")
    date_range: Dict[str, str] = Field(..., description="データ日時範囲")
    data_types: List[str] = Field(..., description="含まれるデータタイプ")

class FeedbackDataResponse(BaseModel):
    """フィードバックデータレスポンス"""
    sensor_data: List[SensorDataPoint] = Field(..., description="センサーデータ一覧")
    race_record: Optional[RaceRecord] = Field(None, description="大会記録")
    competition: CompetitionRace = Field(..., description="大会情報")
    statistics: Optional[FeedbackStatistics] = Field(None, description="統計情報")

class SensorDataQuery(BaseModel):
    """センサーデータクエリ"""
    competition_id: Optional[str] = Field(None, description="大会ID")
    start_date: Optional[str] = Field(None, description="開始日時（ISO形式）")
    end_date: Optional[str] = Field(None, description="終了日時（ISO形式）")
    data_types: Optional[List[str]] = Field(None, description="データタイプフィルター")
    sensor_ids: Optional[List[str]] = Field(None, description="センサーIDフィルター")

class FeedbackChartSegment(BaseModel):
    """チャート区間情報"""
    start: int = Field(..., description="開始時刻（timestamp）")
    end: int = Field(..., description="終了時刻（timestamp）")
    color: str = Field(..., description="背景色")
    type: str = Field(..., description="区間タイプ（swim/bike/run）")
    label: str = Field(..., description="ラベル")

class ChartTimeRange(BaseModel):
    """チャート時間範囲"""
    start: str = Field(..., description="開始時刻（ISO形式）")
    end: str = Field(..., description="終了時刻（ISO形式）")

# APIリクエスト用スキーマ
class FeedbackDataRequest(BaseModel):
    """フィードバックデータリクエスト"""
    competition_id: str = Field(..., description="大会ID")
    user_id: Optional[str] = Field(None, description="ユーザーID（管理者用）")
    offset_minutes: Optional[int] = Field(10, description="前後オフセット時間（分）")
    include_race_records: Optional[bool] = Field(True, description="大会記録を含むかどうか")

class UserDataSummary(BaseModel):
    """ユーザーデータサマリー"""
    total_sensor_records: int = Field(..., description="総センサーデータ数")
    competitions_participated: int = Field(..., description="参加大会数")
    avg_temperature: Optional[float] = Field(None, description="平均体温")
    max_temperature: Optional[float] = Field(None, description="最高体温")
    min_temperature: Optional[float] = Field(None, description="最低体温")
    latest_data_date: Optional[str] = Field(None, description="最新データ日時")

# レスポンス用の基底クラス
class BaseResponse(BaseModel):
    """基底レスポンス"""
    success: bool = Field(True, description="成功フラグ")
    message: Optional[str] = Field(None, description="メッセージ")
    data: Optional[Any] = Field(None, description="データ")

class FeedbackDataListResponse(BaseResponse):
    """フィードバックデータ一覧レスポンス"""
    data: List[FeedbackDataResponse] = Field(..., description="フィードバックデータ一覧")

class CompetitionListResponse(BaseResponse):
    """大会一覧レスポンス"""
    data: List[CompetitionRace] = Field(..., description="大会一覧")

class SensorDataListResponse(BaseResponse):
    """センサーデータ一覧レスポンス"""
    data: List[SensorDataPoint] = Field(..., description="センサーデータ一覧")