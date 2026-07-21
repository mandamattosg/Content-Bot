from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.collectors.base import Collector
from app.models.signal import Signal
from app.services.analysis_service import AnalysisService
from app.services.signal_ingestion import SignalIngestionService
from app.services.telegram_delivery import TelegramDeliveryService


class PipelineService:
    def __init__(
        self,
        db: Session | None,
        collectors: list[Collector] | None = None,
        ingestion_service: SignalIngestionService | None = None,
        analysis_service: AnalysisService | None = None,
        telegram_service: TelegramDeliveryService | None = None,
    ) -> None:
        self._db = db
        self._collectors = collectors or []
        self._ingestion_service = ingestion_service
        self._analysis_service = analysis_service
        self._telegram_service = telegram_service

    def run(self) -> dict[str, Any]:
        collected_signals: list[Signal] = []
        for collector in self._collectors:
            collected_signals.extend(collector.collect())

        ingestion_result = self._ingestion_service.ingest(collected_signals) if self._ingestion_service else None

        analysis_result = None
        if self._analysis_service is not None:
            analysis_result = self._analysis_service.analyze_recent_signals()

        telegram_result = None
        if self._telegram_service is not None and analysis_result is not None:
            telegram_result = self._telegram_service.send_analysis_summary(
                analysis_result,
                signals_count=analysis_result.get("signals_count", 0),
            )

        return {
            "ingestion": {
                "collected": ingestion_result.collected if ingestion_result else 0,
                "normalized": ingestion_result.normalized if ingestion_result else 0,
                "inserted": ingestion_result.inserted if ingestion_result else 0,
                "skipped_duplicates": ingestion_result.skipped_duplicates if ingestion_result else 0,
            },
            "analysis": analysis_result or {},
            "telegram": telegram_result or {},
        }
