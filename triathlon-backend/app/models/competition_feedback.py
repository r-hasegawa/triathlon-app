# app/models/competition_feedback.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, func
from app.database import Base

class CompetitionFeedback(Base):
    """管理者から個人への大会単位フィードバックコメント"""
    __tablename__ = "competition_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    competition_id = Column(String(50), ForeignKey("competitions.competition_id"), nullable=False, index=True)
    admin_id = Column(String(50), ForeignKey("admin_users.admin_id"), nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    __table_args__ = (
        Index('idx_feedback_unique_user_competition', 'user_id', 'competition_id', unique=True),
    )