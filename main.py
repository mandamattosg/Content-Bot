import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.orm import Session

from fastapi import HTTPException

from app.models.signal import Signal

from app.collectors import NewsCollector, RedditCollector, TrendsCollector
from app.config.settings import settings
from app.database.session import SessionLocal
from app.providers.gemini import GeminiProvider, GeminiQuotaError
from app.scheduler.scheduler import scheduler_service
from app.services.analysis_service import AnalysisService
from app.services.pipeline_service import PipelineService
from app.services.signal_ingestion import SignalIngestionService
from app.services.telegram_delivery import TelegramDeliveryService

logger = logging.getLogger("content_radar.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.enable_scheduler:
        scheduler_service.start()
    try:
        yield
    finally:
        scheduler_service.shutdown()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Content Radar API is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.environment,
        "timezone": settings.timezone,
    }


@app.post("/pipeline/collect-and-ingest")
def collect_and_ingest() -> dict[str, int]:
    logger.info("Starting endpoint: /pipeline/collect-and-ingest")
    collectors = [NewsCollector(), RedditCollector(), TrendsCollector()]
    collected_signals = []

    for collector in collectors:
        collected_signals.extend(collector.collect())

    db: Session = SessionLocal()
    try:
        result = SignalIngestionService(db).ingest(collected_signals)
    finally:
        db.close()

    logger.info("Completed endpoint: /pipeline/collect-and-ingest")
    return {
        "collected": result.collected,
        "normalized": result.normalized,
        "inserted": result.inserted,
        "skipped_duplicates": result.skipped_duplicates,
    }


@app.post("/pipeline/analyze")
def analyze_recent_signals() -> dict[str, object]:
    logger.info("Starting endpoint: /pipeline/analyze")
    db: Session = SessionLocal()
    try:
        provider = GeminiProvider(api_key=settings.gemini_api_key)
        result = AnalysisService(db, provider).analyze_recent_signals()
    except GeminiQuotaError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    finally:
        db.close()

    logger.info("Completed endpoint: /pipeline/analyze")
    return result


@app.post("/pipeline/gemini-test")
def gemini_test() -> dict[str, object]:
    logger.info("Starting endpoint: /pipeline/gemini-test")
    provider = GeminiProvider(api_key=settings.gemini_api_key)
    try:
        payload = provider.analyze(
            [
                Signal(
                    source="test",
                    title="Smoke test",
                    content="Responda com a palavra OK.",
                    url="https://example.com/test",
                    published_at="2026-07-21T00:00:00",
                    metadata={},
                )
            ]
        )
    except GeminiQuotaError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    logger.info("Completed endpoint: /pipeline/gemini-test")
    return {"status": "ok", "response": payload}


@app.post("/pipeline/send-telegram")
def send_telegram_message() -> dict[str, object]:
    logger.info("Starting endpoint: /pipeline/send-telegram")
    db: Session = SessionLocal()
    try:
        provider = GeminiProvider(api_key=settings.gemini_api_key)
        analysis = AnalysisService(db, provider).analyze_recent_signals()
        delivery = TelegramDeliveryService()
        signals_count = analysis.get("signals_count", 0) if isinstance(analysis, dict) else 0
        result = delivery.send_analysis_summary(analysis, signals_count=signals_count)
    except GeminiQuotaError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    finally:
        db.close()

    logger.info("Completed endpoint: /pipeline/send-telegram")
    return {"status": "sent", "telegram": result}


@app.post("/pipeline/run")
def run_pipeline() -> dict[str, object]:
    logger.info("Starting endpoint: /pipeline/run")
    db: Session = SessionLocal()
    try:
        provider = GeminiProvider(api_key=settings.gemini_api_key)
        collectors = [NewsCollector(), RedditCollector(), TrendsCollector()]
        ingestion_service = SignalIngestionService(db)
        analysis_service = AnalysisService(db, provider)
        telegram_service = TelegramDeliveryService()

        pipeline = PipelineService(
            db=db,
            collectors=collectors,
            ingestion_service=ingestion_service,
            analysis_service=analysis_service,
            telegram_service=telegram_service,
        )
        result = pipeline.run()
    except GeminiQuotaError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    finally:
        db.close()

    logger.info("Completed endpoint: /pipeline/run")
    return {"status": "ok", "pipeline": result}
