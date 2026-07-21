from datetime import datetime

from app.models.signal_record import SignalRecord
from app.providers.base import AIProvider
from app.services.analysis_service import AnalysisService


class DummyAIProvider(AIProvider):
    def analyze(self, signals):
        return {
            "topics": [
                {
                    "topic": "Teste",
                    "score": 8.5,
                    "reason": "Motivo de teste",
                    "video_ideas": [],
                    "sources": [],
                }
            ]
        }


class FakeResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class FakeDB:
    def __init__(self, values):
        self._values = values
        self.added = []
        self.flushed = False
        self.committed = False

    def scalars(self, statement):
        return FakeResult(self._values)

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        self.flushed = True
        for obj in self.added:
            if hasattr(obj, "id") and obj.id is None:
                obj.id = 1

    def commit(self):
        self.committed = True


def test_analysis_service_returns_signals_count() -> None:
    signal = SignalRecord(
        source="news",
        title="Título",
        content="Conteúdo",
        url="https://example.com/1",
        published_at=datetime.now(),
        topic=None,
        content_hash="abc123",
        metadata_={},
    )
    db = FakeDB([signal])

    result = AnalysisService(db, DummyAIProvider()).analyze_recent_signals()

    assert result["signals_count"] == 1
    assert result["analysis_run_id"] is not None
