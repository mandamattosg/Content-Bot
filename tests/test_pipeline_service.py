from app.models.signal import Signal
from app.services.pipeline_service import PipelineService


class DummyCollector:
    def __init__(self, signals):
        self._signals = signals

    def collect(self):
        return self._signals


class DummyIngestionService:
    def __init__(self):
        self.calls = []

    def ingest(self, signals):
        self.calls.append(signals)
        return type("Result", (), {"collected": len(signals), "normalized": len(signals), "inserted": len(signals), "skipped_duplicates": 0})()


class DummyAnalysisService:
    def __init__(self):
        self.calls = []

    def analyze_recent_signals(self):
        self.calls.append(True)
        return {"topics": [{"topic": "Teste", "score": 8.5, "reason": "motivo"}], "analysis_run_id": 1, "signals_count": 1}


class DummyTelegramService:
    def __init__(self):
        self.calls = []

    def send_analysis_summary(self, analysis, *, signals_count):
        self.calls.append((analysis, signals_count))
        return {"ok": True}


def test_pipeline_service_runs_collect_analysis_and_telegram() -> None:
    signal = Signal(
        source="news",
        title="Titulo",
        content="Conteudo",
        url="https://example.com/1",
        published_at="2026-07-21T00:00:00",
        metadata={},
    )
    ingestion = DummyIngestionService()
    analysis = DummyAnalysisService()
    telegram = DummyTelegramService()

    pipeline = PipelineService(
        db=None,
        collectors=[DummyCollector([signal])],
        ingestion_service=ingestion,
        analysis_service=analysis,
        telegram_service=telegram,
    )

    result = pipeline.run()

    assert result["ingestion"]["inserted"] == 1
    assert result["analysis"]["signals_count"] == 1
    assert result["telegram"] == {"ok": True}
    assert ingestion.calls[0][0].title == "Titulo"
    assert analysis.calls
    assert telegram.calls[0][1] == 1
