from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models.analysis_run import AnalysisRun
from app.models.signal_record import SignalRecord
from app.models.topic_summary import TopicSummary
from app.providers.base import AIProvider
from app.repositories.signal_repository import SignalRepository


class AnalysisService:
    def __init__(self, db: Session, ai_provider: AIProvider) -> None:
        self._db = db
        self._ai_provider = ai_provider
        self._repository = SignalRepository(db)

    def analyze_recent_signals(self, since: datetime | None = None) -> dict[str, Any]:
        if since is None:
            since = datetime.now() - timedelta(hours=24)

        signals = self._repository.get_signals_since(since)
        if not signals:
            return {"topics": [], "analysis_run_id": None, "signals_count": 0}

        analyzed_signals = [self._to_signal(signal) for signal in signals]
        analysis = self._ai_provider.analyze(analyzed_signals)

        run = AnalysisRun(
            executed_at=datetime.now(),
            model="gemini-1.5-flash",
            prompt_version="daily_analysis_v1",
            raw_response=str(analysis),
        )
        self._db.add(run)
        self._db.flush()

        for topic in analysis.get("topics", []):
            self._db.add(
                TopicSummary(
                    analysis_run_id=run.id,
                    topic=topic.get("topic", ""),
                    score=float(topic.get("score", 0)),
                    reason=str(topic.get("reason", "")),
                    video_ideas=list(topic.get("video_ideas", [])),
                    sources=list(topic.get("sources", [])),
                )
            )

        self._db.commit()
        enriched_topics = []
        for topic in analysis.get("topics", []):
            enriched_topic = dict(topic)
            enriched_topic["source_trace"] = self._build_source_trace(topic, signals)
            enriched_topics.append(enriched_topic)

        return {
            "topics": enriched_topics,
            "analysis_run_id": run.id,
            "signals_count": len(signals),
        }

    def _to_signal(self, signal_record: SignalRecord) -> Any:
        from app.models.signal import Signal

        return Signal(
            source=signal_record.source,
            title=signal_record.title,
            content=signal_record.content or "",
            url=signal_record.url or "https://example.com",
            published_at=signal_record.published_at,
            metadata=dict(signal_record.metadata_),
        )

    def _build_source_trace(self, topic: dict[str, Any], signals: list[SignalRecord]) -> list[dict[str, Any]]:
        topic_text = str(topic.get("topic", "")).lower()
        matches: list[dict[str, Any]] = []

        for signal in signals:
            title = (signal.title or "").lower()
            content = (signal.content or "").lower()
            if topic_text not in title and topic_text not in content:
                continue

            source_name = self._source_label(signal)
            matches.append(
                {
                    "source": signal.source,
                    "source_name": source_name,
                    "title": signal.title,
                    "url": signal.url,
                    "feed_title": signal.metadata_.get("feed_title") if isinstance(signal.metadata_, dict) else None,
                }
            )

        return matches[:3]

    def _source_label(self, signal: SignalRecord) -> str:
        if signal.source == "news":
            feed_title = signal.metadata_.get("feed_title") if isinstance(signal.metadata_, dict) else None
            if feed_title:
                return str(feed_title)
            return "Notícia"
        if signal.source == "reddit":
            subreddit = signal.metadata_.get("subreddit") if isinstance(signal.metadata_, dict) else None
            if subreddit:
                return f"Reddit /r/{subreddit}"
            return "Reddit"
        if signal.source == "trends":
            return "Google Trends"
        return signal.source
