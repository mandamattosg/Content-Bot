from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.signal import Signal
from app.models.signal_record import SignalRecord
from app.utils.signal_hash import build_signal_hash


@dataclass
class SaveSignalsResult:
    inserted: int
    skipped_duplicates: int


class SignalRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def save_signals(self, signals: list[Signal]) -> SaveSignalsResult:
        inserted = 0
        skipped_duplicates = 0

        for signal in signals:
            if self._is_duplicate(signal):
                skipped_duplicates += 1
                continue

            record = self._to_record(signal)
            self._db.add(record)
            inserted += 1

        self._db.commit()
        return SaveSignalsResult(inserted=inserted, skipped_duplicates=skipped_duplicates)

    def get_signals_since(self, since: datetime) -> list[SignalRecord]:
        statement = (
            select(SignalRecord)
            .where(SignalRecord.published_at >= since)
            .order_by(SignalRecord.published_at.desc())
        )
        return list(self._db.scalars(statement).all())

    def _is_duplicate(self, signal: Signal) -> bool:
        signal_hash = build_signal_hash(signal)
        signal_date = signal.published_at.date()

        filters = [
            SignalRecord.content_hash == signal_hash,
            and_(
                SignalRecord.title == signal.title,
                func.date(SignalRecord.published_at) == signal_date,
            ),
        ]

        signal_url = str(signal.url).strip()
        if signal_url:
            filters.append(SignalRecord.url == signal_url)

        statement = select(SignalRecord.id).where(or_(*filters)).limit(1)
        return self._db.execute(statement).first() is not None

    def _to_record(self, signal: Signal) -> SignalRecord:
        metadata = dict(signal.metadata)
        metadata.setdefault("content_hash", build_signal_hash(signal))

        return SignalRecord(
            source=signal.source,
            title=signal.title,
            content=signal.content,
            url=str(signal.url),
            published_at=signal.published_at,
            topic=None,
            content_hash=metadata["content_hash"],
            metadata_=metadata,
        )
