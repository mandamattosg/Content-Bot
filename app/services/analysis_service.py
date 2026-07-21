from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models.analysis_run import AnalysisRun
from app.models.signal_record import SignalRecord
from app.models.topic_summary import TopicSummary
from app.providers.base import AIProvider
from app.repositories.signal_repository import SignalRepository

logger = logging.getLogger("content_radar.analysis")


class AnalysisService:
    def __init__(self, db: Session, ai_provider: AIProvider) -> None:
        self._db = db
        self._ai_provider = ai_provider
        self._repository = SignalRepository(db)

    def analyze_recent_signals(self, since: datetime | None = None) -> dict[str, Any]:
        if since is None:
            since = datetime.now() - timedelta(hours=24)

        signals = self._repository.get_signals_since(since)
        logger.info("Analysis service received %s signals since %s", len(signals), since)
        if not signals:
            logger.info("No signals available for analysis")
            return {"topics": [], "analysis_run_id": None, "signals_count": 0}

        analyzed_signals = [self._to_signal(signal) for signal in signals]
        logger.info("Sending %s signals to AI provider", len(analyzed_signals))
        analysis = self._ai_provider.analyze(analyzed_signals)
        logger.info("AI provider returned analysis payload: %s", analysis)

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
        keywords = self._extract_keywords(topic_text)
        matches: list[dict[str, Any]] = []

        for signal in signals:
            title = (signal.title or "").lower()
            content = (signal.content or "").lower()
            metadata_text = self._metadata_text(signal)
            combined_text = " ".join([title, content, metadata_text]).lower()

            if topic_text in combined_text:
                score = 3
            elif any(keyword in combined_text for keyword in keywords):
                score = 2
            else:
                continue

            source_name = self._source_label(signal)
            matches.append(
                {
                    "source": signal.source,
                    "source_name": source_name,
                    "title": signal.title,
                    "url": signal.url,
                    "feed_title": signal.metadata_.get("feed_title") if isinstance(signal.metadata_, dict) else None,
                    "match_score": score,
                }
            )

        matches.sort(key=lambda match: match.get("match_score", 0), reverse=True)
        return matches[:3]

    def _extract_keywords(self, topic_text: str) -> list[str]:
        words = [word for word in topic_text.replace("/", " ").replace("-", " ").split() if len(word) > 2]
        return [word for word in words if word.isalnum()]

    def _metadata_text(self, signal: SignalRecord) -> str:
        if not isinstance(signal.metadata_, dict):
            return ""
        metadata_values = []
        for value in signal.metadata_.values():
            if isinstance(value, (str, int, float)):
                metadata_values.append(str(value))
        return " ".join(metadata_values)

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
