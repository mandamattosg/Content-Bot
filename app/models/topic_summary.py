from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TopicSummary(Base):
    __tablename__ = "topic_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_run_id: Mapped[int] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    topic: Mapped[str] = mapped_column(String(255), index=True)
    score: Mapped[float] = mapped_column(Numeric(4, 2))
    reason: Mapped[str] = mapped_column(Text)
    video_ideas: Mapped[list] = mapped_column(JSONB, default=list)
    sources: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    analysis_run = relationship("AnalysisRun", back_populates="topic_summaries")
