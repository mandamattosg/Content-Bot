from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.database.base import Base


engine = create_engine(
    settings.sqlalchemy_database_url,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    from app.models.analysis_run import AnalysisRun  # noqa: F401
    from app.models.signal_record import SignalRecord  # noqa: F401
    from app.models.topic_summary import TopicSummary  # noqa: F401

    Base.metadata.create_all(bind=engine)