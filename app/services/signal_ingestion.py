from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.signal import Signal
from app.repositories.signal_repository import SaveSignalsResult, SignalRepository
from app.services.signal_normalizer import SignalNormalizer


@dataclass
class IngestionResult:
    collected: int
    normalized: int
    inserted: int
    skipped_duplicates: int


class SignalIngestionService:
    def __init__(self, db: Session, normalizer: SignalNormalizer | None = None) -> None:
        self._db = db
        self._normalizer = normalizer or SignalNormalizer()
        self._repository = SignalRepository(db)

    def ingest(self, signals: list[Signal]) -> IngestionResult:
        normalized_signals = self._normalizer.enrich_for_analysis(signals)
        save_result: SaveSignalsResult = self._repository.save_signals(normalized_signals)

        return IngestionResult(
            collected=len(signals),
            normalized=len(normalized_signals),
            inserted=save_result.inserted,
            skipped_duplicates=save_result.skipped_duplicates,
        )
