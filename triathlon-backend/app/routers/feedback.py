# app/routers/feedback.py - Gemini無料枠を使ったAIコメント生成 + Bike体表温分析機能版

import os
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel
import google.generativeai as genai

from ..database import get_db
from ..utils.dependencies import get_current_user, get_current_admin
from ..models.user import User, AdminUser
from ..models.competition import Competition, RaceRecord
from ..models.flexible_sensor_data import (
    FlexibleSensorMapping, SkinTemperatureData, 
    CoreTemperatureData, HeartRateData, WBGTData, SensorType
)
from ..models.competition_feedback import CompetitionFeedback

router = APIRouter()
logger = logging.getLogger(__name__)

# 🆕 Gemini APIの設定（無料枠：Gemini 2.5 Flash、1日1,500リクエストまで）
GEMINI_MODEL_NAME = "gemini-flash-latest"

# 🆕 Bikeパート体表温分析の閾値（自社知見に基づく固定値）
BIKE_SKIN_TEMP_RISK_THRESHOLD = 1.5
BIKE_PLUS_MINUTES = 10  # 「Bike開始◯分後」の◯分
SKIN_TEMP_MATCH_TOLERANCE_MINUTES = 3  # 目標時刻に一致するデータを探す際の許容誤差

# ===== スキーマ定義 =====

class CompetitionRace(BaseModel):
    id: str
    name: str
    date: str
    description: Optional[str] = None

class SensorDataPoint(BaseModel):
    timestamp: str
    skin_temperature: Optional[float] = None
    core_temperature: Optional[float] = None
    wbgt_temperature: Optional[float] = None
    heart_rate: Optional[int] = None
    sensor_id: Optional[str] = None
    data_type: Optional[str] = None

class RaceRecordSchema(BaseModel):
    competition_id: str
    user_id: str
    swim_start: Optional[str] = None
    swim_finish: Optional[str] = None
    bike_start: Optional[str] = None
    bike_finish: Optional[str] = None
    run_start: Optional[str] = None
    run_finish: Optional[str] = None

class FeedbackDataResponse(BaseModel):
    sensor_data: List[SensorDataPoint]
    race_record: Optional[RaceRecordSchema] = None
    competition: CompetitionRace
    statistics: Optional[Dict[str, Any]] = None
    comment: Optional[str] = None  # 管理者コメント

class CommentUpsert(BaseModel):
    comment: str

class CommentResponse(BaseModel):
    comment: str
    updated_at: Optional[str] = None

class CommentDraftResponse(BaseModel):
    draft_comment: str

# ===== 一般ユーザー用エンドポイント =====

@router.get("/me/competitions", response_model=List[CompetitionRace])
async def get_user_competitions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """現在のユーザーが参加している大会一覧を取得"""
    try:
        logger.info(f"Getting competitions for user: {current_user.user_id}")
        
        # ユーザーがマッピングを持っている大会を取得
        competitions = db.query(Competition).join(
            FlexibleSensorMapping,
            Competition.competition_id == FlexibleSensorMapping.competition_id
        ).filter(
            FlexibleSensorMapping.user_id == current_user.user_id
        ).distinct().order_by(Competition.date.desc()).all()
        
        logger.info(f"Found {len(competitions)} competitions for user {current_user.user_id}")
        
        result = [
            CompetitionRace(
                id=comp.competition_id,
                name=comp.name,
                date=comp.date.isoformat(),
            )
            for comp in competitions
        ]
        
        logger.info(f"Returning competitions: {[c.id for c in result]}")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching user competitions: {e}")
        raise HTTPException(status_code=500, detail="大会一覧の取得に失敗しました")


@router.get("/me/feedback-data/{competition_id}", response_model=FeedbackDataResponse)
async def get_user_feedback_data(
    competition_id: str,
    offset_minutes: int = Query(10, ge=0, le=60),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """指定された大会のフィードバックデータを取得（エラーハンドリング強化版）"""
    try:
        logger.info(f"Getting feedback data for user: {current_user.user_id}, competition: {competition_id}")
        
        # 大会の存在確認
        competition = db.query(Competition).filter(
            Competition.competition_id == competition_id
        ).first()
        
        if not competition:
            logger.error(f"Competition not found: {competition_id}")
            raise HTTPException(status_code=404, detail="指定された大会が見つかりません")
        
        # センサーデータを取得
        try:
            sensor_data = get_sensor_data(db, current_user.user_id, competition_id)
            logger.info(f"Retrieved {len(sensor_data)} sensor data points")
        except Exception as sensor_error:
            logger.error(f"Error retrieving sensor data: {sensor_error}")
            sensor_data = []  # エラーが発生しても空のリストを返す
        
        # 大会記録を取得
        try:
            race_record = get_race_record(db, current_user.user_id, competition_id)
            logger.info(f"Race record found: {race_record is not None}")
        except Exception as race_error:
            logger.error(f"Error retrieving race record: {race_error}")
            race_record = None  # エラーが発生してもNoneを返す

        # 管理者コメントを取得
        comment_text = get_feedback_comment(db, current_user.user_id, competition_id)

        return FeedbackDataResponse(
            sensor_data=sensor_data,
            race_record=race_record,
            competition=CompetitionRace(
                id=competition.competition_id,
                name=competition.name,
                date=competition.date.isoformat() if competition.date else datetime.now().isoformat(),
                description=getattr(competition, 'description', None)
            ),
            statistics={
                "total_records": len(sensor_data),
                "data_types": list(set([data.data_type for data in sensor_data if data.data_type]))
            },
            comment=comment_text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching feedback data: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"フィードバックデータの取得に失敗しました: {str(e)}")


@router.get("/me/sensor-data", response_model=List[SensorDataPoint])
async def get_user_sensor_data(
    competition_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ユーザーのセンサーデータを取得"""
    try:
        logger.info(f"Getting sensor data for user: {current_user.user_id}, competition: {competition_id}")
        return get_sensor_data(db, current_user.user_id, competition_id)
    except Exception as e:
        logger.error(f"Error fetching sensor data: {e}")
        raise HTTPException(status_code=500, detail="センサーデータの取得に失敗しました")


# ===== 管理者用エンドポイント =====

@router.get("/admin/users/{user_id}/competitions", response_model=List[CompetitionRace])
async def get_admin_user_competitions(
    user_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """管理者用：指定ユーザーの参加大会一覧を取得"""
    try:
        logger.info(f"Admin getting competitions for user: {user_id}")
        
        competitions = db.query(Competition).join(
            FlexibleSensorMapping,
            Competition.competition_id == FlexibleSensorMapping.competition_id
        ).filter(
            FlexibleSensorMapping.user_id == user_id
        ).distinct().order_by(Competition.date.desc()).all()
        
        return [
            CompetitionRace(
                id=comp.competition_id,
                name=comp.name,
                date=comp.date.isoformat(),
            )
            for comp in competitions
        ]
    except Exception as e:
        logger.error(f"Error fetching admin user competitions: {e}")
        raise HTTPException(status_code=500, detail="大会一覧の取得に失敗しました")


@router.get("/admin/users/{user_id}/feedback-data/{competition_id}", response_model=FeedbackDataResponse)
async def get_admin_user_feedback_data(
    user_id: str,
    competition_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """管理者用：指定ユーザーの大会フィードバックデータを取得"""
    try:
        logger.info(f"Admin getting feedback data for user: {user_id}, competition: {competition_id}")
        
        # ユーザーと大会の存在確認
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="指定されたユーザーが見つかりません")
            
        competition = db.query(Competition).filter(
            Competition.competition_id == competition_id
        ).first()
        if not competition:
            raise HTTPException(status_code=404, detail="指定された大会が見つかりません")
        
        # データ取得
        sensor_data = get_sensor_data(db, user_id, competition_id)
        race_record = get_race_record(db, user_id, competition_id)

        # 管理者コメントを取得
        comment_text = get_feedback_comment(db, user_id, competition_id)

        return FeedbackDataResponse(
            sensor_data=sensor_data,
            race_record=race_record,
            competition=CompetitionRace(
                id=competition.competition_id,
                name=competition.name,
                date=competition.date.isoformat(),
            ),
            statistics={
                "total_records": len(sensor_data),
                "data_types": list(set([data.data_type for data in sensor_data if data.data_type]))
            },
            comment=comment_text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching admin feedback data: {e}")
        raise HTTPException(status_code=500, detail="フィードバックデータの取得に失敗しました")


@router.post("/admin/users/{user_id}/feedback-data/{competition_id}/comment", response_model=CommentResponse)
async def upsert_feedback_comment(
    user_id: str,
    competition_id: str,
    payload: CommentUpsert,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """管理者用：指定ユーザー・大会へのコメントを作成/更新"""
    try:
        # ユーザーと大会の存在確認
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="指定されたユーザーが見つかりません")

        competition = db.query(Competition).filter(
            Competition.competition_id == competition_id
        ).first()
        if not competition:
            raise HTTPException(status_code=404, detail="指定された大会が見つかりません")

        existing = db.query(CompetitionFeedback).filter_by(
            user_id=user_id, competition_id=competition_id
        ).first()

        if existing:
            existing.comment = payload.comment
            existing.admin_id = current_admin.admin_id
        else:
            existing = CompetitionFeedback(
                user_id=user_id,
                competition_id=competition_id,
                admin_id=current_admin.admin_id,
                comment=payload.comment
            )
            db.add(existing)

        db.commit()
        db.refresh(existing)

        return CommentResponse(
            comment=existing.comment,
            updated_at=existing.updated_at.isoformat() if existing.updated_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upserting feedback comment: {e}")
        raise HTTPException(status_code=500, detail="コメントの保存に失敗しました")


@router.delete("/admin/users/{user_id}/feedback-data/{competition_id}/comment")
async def delete_feedback_comment(
    user_id: str,
    competition_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """管理者用：指定ユーザー・大会へのコメントを削除"""
    try:
        deleted = db.query(CompetitionFeedback).filter_by(
            user_id=user_id, competition_id=competition_id
        ).delete()
        db.commit()
        return {"deleted": bool(deleted)}
    except Exception as e:
        logger.error(f"Error deleting feedback comment: {e}")
        raise HTTPException(status_code=500, detail="コメントの削除に失敗しました")


@router.post("/admin/users/{user_id}/feedback-data/{competition_id}/comment/generate", response_model=CommentDraftResponse)
async def generate_feedback_comment_draft(
    user_id: str,
    competition_id: str,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    管理者用：大会期間のデータからAIにコメント案を生成してもらう（保存はしない）

    Bikeパートの体表温変化（Swim終了時→Bike+10分の低下量、Bike+10分→Bikeパート終盤の再上昇量）は
    自社の固定ロジックで判定し、AIには一切計算させない。AIには心拍・カプセル体温・WBGTなど
    残りの指標の傾向コメントのみを書かせ、固定文と結合して返す。
    """
    try:
        sensor_data = get_sensor_data(db, user_id, competition_id)
        race_record = get_race_record(db, user_id, competition_id)

        if not sensor_data:
            raise HTTPException(status_code=400, detail="対象のセンサーデータがありません")

        # 🆕 固定ロジックによるBike体表温分析（AIには渡さず、確定文を別枠で用意）
        bike_skin_analysis = analyze_bike_skin_temperature(sensor_data, race_record)
        fixed_sentence = format_bike_skin_temp_sentence(bike_skin_analysis) if bike_skin_analysis else None

        # 区間境界（既存の背景色ロジックと同じ規則：フィニッシュがなければ次パートのスタートで代用）
        swim_start = race_record.swim_start if race_record else None
        swim_end = (race_record.swim_finish or (race_record.bike_start if race_record else None)) if race_record else None
        bike_start = race_record.bike_start if race_record else None
        bike_end = (race_record.bike_finish or (race_record.run_start if race_record else None)) if race_record else None
        run_start = race_record.run_start if race_record else None
        run_end = race_record.run_finish if race_record else None

        summary = {
            "swim": _segment_stats(sensor_data, swim_start, swim_end),
            "bike": _segment_stats(sensor_data, bike_start, bike_end),
            "run": _segment_stats(sensor_data, run_start, run_end),
        }

        prompt = (
            "あなたはトライアスロンのコーチです。以下は選手の大会中センサーデータを、"
            "Swim/Bike/Runの区間ごとに平均・最大・最小値へ要約したものです。\n"
            "このデータから客観的に読み取れることだけをもとに、心拍数・カプセル体温・WBGTの傾向について"
            "日本語で2〜3文のコメントを書いてください。体表温のBikeパートでの変化については別途"
            "固定の分析結果があるので、あなたはそれ以外の指標についてのみ言及してください。"
            "データに無い推測は書かないでください。\n\n"
            f"データ:\n{json.dumps(summary, ensure_ascii=False, indent=2)}"
        )

        ai_text = ""
        try:
            genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
            model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            response = model.generate_content(prompt)
            ai_text = (response.text or "").strip()
        except Exception as api_error:
            logger.error(f"Gemini API error: {api_error}")
            ai_text = ""

        # 固定文（体表温リスク判定）を必ず先頭に、AI生成文を後に結合
        parts = [p for p in [fixed_sentence, ai_text] if p]

        if not parts:
            raise HTTPException(status_code=502, detail="コメント案を生成できませんでした")

        draft = "\n\n".join(parts)

        return CommentDraftResponse(draft_comment=draft)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating comment draft: {e}")
        raise HTTPException(status_code=502, detail="AIコメント案の生成に失敗しました")


# ===== 内部関数 =====

def get_feedback_comment(db: Session, user_id: str, competition_id: str) -> Optional[str]:
    """指定ユーザー・大会の管理者コメントを取得"""
    try:
        feedback = db.query(CompetitionFeedback).filter_by(
            user_id=user_id, competition_id=competition_id
        ).first()
        return feedback.comment if feedback else None
    except Exception as e:
        logger.error(f"Error getting feedback comment: {e}")
        return None


def _segment_stats(sensor_data: List[SensorDataPoint], start: Optional[str], end: Optional[str]) -> Dict[str, Any]:
    """指定区間のセンサーデータを統計値（min/max/avg）に要約"""
    if not start or not end:
        return {}

    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    points = [p for p in sensor_data if start_dt <= datetime.fromisoformat(p.timestamp) <= end_dt]

    def stat(values: List[Optional[float]]):
        values = [v for v in values if v is not None]
        if not values:
            return None
        return {
            "min": round(min(values), 1),
            "max": round(max(values), 1),
            "avg": round(sum(values) / len(values), 1),
        }

    return {
        "skin_temperature": stat([p.skin_temperature for p in points]),
        "core_temperature": stat([p.core_temperature for p in points]),
        "heart_rate": stat([p.heart_rate for p in points]),
        "wbgt_temperature": stat([p.wbgt_temperature for p in points]),
    }


def _find_nearest_skin_temp(
    sensor_data: List[SensorDataPoint],
    target_time_iso: Optional[str],
    tolerance_minutes: int = SKIN_TEMP_MATCH_TOLERANCE_MINUTES
) -> Optional[float]:
    """指定時刻に最も近い体表温データ点を探す（許容誤差内のみ有効とみなす）"""
    if not target_time_iso:
        return None
    target = datetime.fromisoformat(target_time_iso)
    candidates = [p for p in sensor_data if p.skin_temperature is not None]
    if not candidates:
        return None
    nearest = min(candidates, key=lambda p: abs((datetime.fromisoformat(p.timestamp) - target).total_seconds()))
    if abs((datetime.fromisoformat(nearest.timestamp) - target).total_seconds()) > tolerance_minutes * 60:
        return None
    return nearest.skin_temperature


def analyze_bike_skin_temperature(
    sensor_data: List[SensorDataPoint],
    race_record: Optional[RaceRecordSchema]
) -> Optional[Dict[str, Any]]:
    """
    Bikeパートの体表温変化分析（自社知見に基づく固定ロジック）

    ① Swim終了時 → Bike開始10分後 の低下量
    ② Bike開始10分後 → Bikeパート終盤（最高値）までの上昇量
    の2軸で4分類のリスク判定を行う。

    体表温がしっかり下がる（①が閾値以上）ことは体冷却ができている証拠、
    その後上がりすぎる（②が閾値以上）ことは熱中症リスクの兆候として扱う。

    体表温データが必要な時点に存在しない場合は None を返し、
    呼び出し側はこの分析結果自体を表示しない（欠損対応の原則に準拠）。
    """
    if not race_record:
        return None

    swim_end = race_record.swim_finish or race_record.bike_start
    bike_start = race_record.bike_start
    bike_end = race_record.bike_finish or race_record.run_start

    if not swim_end or not bike_start:
        return None

    bike_start_dt = datetime.fromisoformat(bike_start)
    bike_plus10_iso = (bike_start_dt + timedelta(minutes=BIKE_PLUS_MINUTES)).isoformat()

    swim_end_temp = _find_nearest_skin_temp(sensor_data, swim_end)
    bike_plus10_temp = _find_nearest_skin_temp(sensor_data, bike_plus10_iso)

    # 体表温データが揃っていない場合は分析自体を行わない
    if swim_end_temp is None or bike_plus10_temp is None:
        return None

    bike_end_dt = datetime.fromisoformat(bike_end) if bike_end else None
    later_temps = [
        p.skin_temperature for p in sensor_data
        if p.skin_temperature is not None
        and datetime.fromisoformat(p.timestamp) >= (bike_start_dt + timedelta(minutes=BIKE_PLUS_MINUTES))
        and (bike_end_dt is None or datetime.fromisoformat(p.timestamp) <= bike_end_dt)
    ]

    if not later_temps:
        return None

    bike_max_after10 = max(later_temps)

    drop1 = round(swim_end_temp - bike_plus10_temp, 1)      # ① 低下量
    rise2 = round(bike_max_after10 - bike_plus10_temp, 1)   # ② 再上昇量

    if drop1 < BIKE_SKIN_TEMP_RISK_THRESHOLD and rise2 >= BIKE_SKIN_TEMP_RISK_THRESHOLD:
        risk_label = "熱中症リスクが高いおそれがあります（体表温が下がりにくく、上がりやすい状態）"
    elif drop1 < BIKE_SKIN_TEMP_RISK_THRESHOLD and rise2 < BIKE_SKIN_TEMP_RISK_THRESHOLD:
        risk_label = "体表温が変化しづらい状態です"
    elif drop1 >= BIKE_SKIN_TEMP_RISK_THRESHOLD and rise2 >= BIKE_SKIN_TEMP_RISK_THRESHOLD:
        risk_label = "体表温が変化しやすい状態です（一度下がった後、再び上がっています）"
    else:  # drop1 >= threshold and rise2 < threshold
        risk_label = "体表温が下がりやすく上がりにくい状態で、リスクは低いと考えられます"

    return {
        "swim_end_temp": round(swim_end_temp, 1),
        "bike_plus10_temp": round(bike_plus10_temp, 1),
        "bike_max_after10_temp": round(bike_max_after10, 1),
        "drop1": drop1,
        "rise2": rise2,
        "risk_label": risk_label,
    }


def format_bike_skin_temp_sentence(analysis: Dict[str, Any]) -> str:
    """Bike体表温分析の固定テンプレート文（AIには書き換えさせない）"""
    return (
        f"体表温について、Swim終了時点で{analysis['swim_end_temp']}°C、"
        f"Bike開始{BIKE_PLUS_MINUTES}分後には{analysis['bike_plus10_temp']}°C"
        f"（{analysis['drop1']}°Cの低下）でした。"
        f"その後Bikeパート終盤にかけて最高{analysis['bike_max_after10_temp']}°C"
        f"（{analysis['rise2']}°Cの再上昇）が見られます。"
        f"{analysis['risk_label']}。"
    )


def get_sensor_data(db: Session, user_id: str, competition_id: Optional[str] = None) -> List[SensorDataPoint]:
    """センサーデータを取得して統合形式に変換"""
    try:
        logger.info(f"Getting sensor data for user: {user_id}, competition: {competition_id}")
        
        # ユーザーのマッピングを取得
        mappings_query = db.query(FlexibleSensorMapping).filter(
            FlexibleSensorMapping.user_id == user_id
        )
        if competition_id:
            mappings_query = mappings_query.filter(
                FlexibleSensorMapping.competition_id == competition_id
            )
        
        mappings = mappings_query.all()
        logger.info(f"Found {len(mappings)} mappings for user {user_id}")
        
        if not mappings:
            logger.warning(f"No mappings found for user {user_id}, competition {competition_id}")
            return []
        
        # データをタイムスタンプごとにグループ化
        grouped_data = {}
        
        # 体表温度データ処理
        skin_mappings = [m for m in mappings if m.sensor_type == SensorType.SKIN_TEMPERATURE]
        logger.info(f"Processing {len(skin_mappings)} skin temperature mappings")
        
        for mapping in skin_mappings:
            try:
                logger.info(f"Processing skin temp sensor: {mapping.sensor_id}")
                
                query = db.query(SkinTemperatureData).filter(
                    SkinTemperatureData.halshare_id == mapping.sensor_id
                )
                if competition_id:
                    query = query.filter(SkinTemperatureData.competition_id == competition_id)
                
                skin_data = query.order_by(SkinTemperatureData.datetime).all()
                logger.info(f"Found {len(skin_data)} skin temperature records for sensor {mapping.sensor_id}")
                
                for data in skin_data:
                    timestamp_key = data.datetime.isoformat()
                    if timestamp_key not in grouped_data:
                        grouped_data[timestamp_key] = SensorDataPoint(
                            timestamp=timestamp_key,
                            sensor_id=mapping.sensor_id
                        )
                    grouped_data[timestamp_key].skin_temperature = data.temperature
                    grouped_data[timestamp_key].data_type = "skin_temperature"
                    
            except Exception as e:
                logger.error(f"Error processing skin temp mapping {mapping.sensor_id}: {e}")
        
        # カプセル体温データ処理
        core_mappings = [m for m in mappings if m.sensor_type == SensorType.CORE_TEMPERATURE]
        logger.info(f"Processing {len(core_mappings)} core temperature mappings")
        
        for mapping in core_mappings:
            try:
                logger.info(f"Processing core temp sensor: {mapping.sensor_id}")
                
                query = db.query(CoreTemperatureData).filter(
                    CoreTemperatureData.capsule_id == mapping.sensor_id
                )
                if competition_id:
                    query = query.filter(CoreTemperatureData.competition_id == competition_id)
                
                core_data = query.order_by(CoreTemperatureData.datetime).all()
                logger.info(f"Found {len(core_data)} core temperature records for sensor {mapping.sensor_id}")
                
                for data in core_data:
                    timestamp_key = data.datetime.isoformat()
                    if timestamp_key not in grouped_data:
                        grouped_data[timestamp_key] = SensorDataPoint(
                            timestamp=timestamp_key,
                            sensor_id=mapping.sensor_id
                        )
                    grouped_data[timestamp_key].core_temperature = data.temperature
                    grouped_data[timestamp_key].data_type = "core_temperature"
                    
            except Exception as e:
                logger.error(f"Error processing core temp mapping {mapping.sensor_id}: {e}")
        
        # 心拍データ処理
        hr_mappings = [m for m in mappings if m.sensor_type == SensorType.HEART_RATE]
        logger.info(f"Processing {len(hr_mappings)} heart rate mappings")
        
        for mapping in hr_mappings:
            try:
                logger.info(f"Processing heart rate sensor: {mapping.sensor_id}")
                
                query = db.query(HeartRateData).filter(
                    HeartRateData.sensor_id == mapping.sensor_id
                )
                if competition_id:
                    query = query.filter(HeartRateData.competition_id == competition_id)
                
                hr_data = query.order_by(HeartRateData.time).all()
                logger.info(f"Found {len(hr_data)} heart rate records for sensor {mapping.sensor_id}")
                
                for data in hr_data:
                    timestamp_key = data.time.isoformat()
                    if timestamp_key not in grouped_data:
                        grouped_data[timestamp_key] = SensorDataPoint(
                            timestamp=timestamp_key,
                            sensor_id=mapping.sensor_id
                        )
                    grouped_data[timestamp_key].heart_rate = data.heart_rate
                    grouped_data[timestamp_key].data_type = "heart_rate"
                    
            except Exception as e:
                logger.error(f"Error processing heart rate mapping {mapping.sensor_id}: {e}")
        
        # WBGT データ（大会全体で共有）
        if competition_id:
            try:
                wbgt_data = db.query(WBGTData).filter(
                    WBGTData.competition_id == competition_id
                ).order_by(WBGTData.timestamp).all()
                
                logger.info(f"Found {len(wbgt_data)} WBGT records for competition {competition_id}")
                
                for data in wbgt_data:
                    timestamp_key = data.timestamp.isoformat()
                    if timestamp_key not in grouped_data:
                        grouped_data[timestamp_key] = SensorDataPoint(
                            timestamp=timestamp_key,
                            sensor_id="wbgt_sensor"
                        )
                    grouped_data[timestamp_key].wbgt_temperature = data.wbgt_value
                    if not grouped_data[timestamp_key].data_type:
                        grouped_data[timestamp_key].data_type = "wbgt"
                        
            except Exception as e:
                logger.error(f"Error processing WBGT data: {e}")
        
        # ソートして返す
        result = sorted(grouped_data.values(), key=lambda x: x.timestamp)
        logger.info(f"Returning {len(result)} sensor data points")
        
        # デバッグ: 最初の数件をログ出力
        for i, point in enumerate(result[:3]):
            logger.info(f"Sample data {i}: {point.timestamp}, skin: {point.skin_temperature}, core: {point.core_temperature}, hr: {point.heart_rate}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting sensor data: {e}")
        return []


def get_race_record(db: Session, user_id: str, competition_id: str) -> Optional[RaceRecordSchema]:
    """大会記録を取得"""
    try:
        logger.info(f"Getting race record for user: {user_id}, competition: {competition_id}")
        
        # ユーザーのマッピングからゼッケン番号を取得
        mapping = db.query(FlexibleSensorMapping).filter(
            FlexibleSensorMapping.user_id == user_id,
            FlexibleSensorMapping.competition_id == competition_id,
            FlexibleSensorMapping.sensor_type == SensorType.RACE_RECORD
        ).first()
        
        if not mapping:
            logger.warning(f"No race record mapping found for user {user_id} in competition {competition_id}")
            return None
        
        race_number = mapping.sensor_id  # RACE_RECORDタイプの場合、sensor_idがゼッケン番号
        logger.info(f"Found race number: {race_number}")
        
        # 大会記録を取得
        race_record = db.query(RaceRecord).filter(
            RaceRecord.competition_id == competition_id,
            RaceRecord.race_number == race_number
        ).first()
        
        if not race_record:
            logger.warning(f"No race record found for race number {race_number}")
            return None
        
        logger.info(f"Found race record for race number {race_number}")
        
        return RaceRecordSchema(
            competition_id=race_record.competition_id,
            user_id=user_id,
            swim_start=race_record.swim_start_time.isoformat() if race_record.swim_start_time else None,
            swim_finish=race_record.swim_finish_time.isoformat() if race_record.swim_finish_time else None,
            bike_start=race_record.bike_start_time.isoformat() if race_record.bike_start_time else None,
            bike_finish=race_record.bike_finish_time.isoformat() if race_record.bike_finish_time else None,
            run_start=race_record.run_start_time.isoformat() if race_record.run_start_time else None,
            run_finish=race_record.run_finish_time.isoformat() if race_record.run_finish_time else None,
        )
        
    except Exception as e:
        logger.error(f"Error getting race record: {e}")
        return None