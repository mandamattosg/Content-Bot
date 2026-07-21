from datetime import datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.analysis_run import AnalysisRun
from app.models.signal_record import SignalRecord
from app.models.topic_summary import TopicSummary


def purge_old_data(db: Session) -> None:
    cutoff = datetime.now() - timedelta(days=settings.data_retention_days)

    db.execute(delete(TopicSummary).where(TopicSummary.created_at < cutoff))
    db.execute(delete(AnalysisRun).where(AnalysisRun.created_at < cutoff))
    db.execute(delete(SignalRecord).where(SignalRecord.created_at < cutoff))
    db.commit()
