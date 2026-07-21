from __future__ import annotations

from collections import defaultdict

from app.config.settings import settings
from app.models.signal import Signal
from app.utils.signal_hash import build_signal_hash
from app.utils.text import normalize_text, truncate_text


class SignalNormalizer:
    def __init__(
        self,
        *,
        max_total_signals: int = 40,
        max_news_signals: int = 20,
        max_reddit_signals: int = 15,
        max_trends_signals: int = 10,
        max_content_length: int = 600,
    ) -> None:
        self.max_total_signals = max_total_signals
        self.max_news_signals = max_news_signals
        self.max_reddit_signals = max_reddit_signals
        self.max_trends_signals = max_trends_signals
        self.max_content_length = max_content_length

    def normalize(self, signals: list[Signal]) -> list[Signal]:
        deduplicated_signals = self._deduplicate(signals)
        curated_signals = self._apply_source_limits(deduplicated_signals)
        return curated_signals[: self.max_total_signals]

    def enrich_for_analysis(self, signals: list[Signal]) -> list[Signal]:
        normalized_signals = self.normalize(signals)
        enriched_signals: list[Signal] = []

        for signal in normalized_signals:
            normalized_title = normalize_text(signal.title)
            normalized_content = normalize_text(signal.content)
            compact_content = truncate_text(normalized_content, self.max_content_length)
            enriched_metadata = {**signal.metadata}
            enriched_metadata["content_hash"] = build_signal_hash(signal)
            enriched_metadata["normalized_title"] = normalized_title
            enriched_metadata["normalized_content_length"] = len(normalized_content)

            enriched_signals.append(
                signal.model_copy(
                    update={
                        "title": normalized_title,
                        "content": compact_content,
                        "metadata": enriched_metadata,
                    }
                )
            )

        return enriched_signals

    def _deduplicate(self, signals: list[Signal]) -> list[Signal]:
        unique_signals: list[Signal] = []
        seen_hashes: set[str] = set()
        seen_titles: set[str] = set()

        for signal in sorted(signals, key=self._sort_key, reverse=True):
            signal_hash = build_signal_hash(signal)
            normalized_title = normalize_text(signal.title).lower()
            if signal_hash in seen_hashes or normalized_title in seen_titles:
                continue

            seen_hashes.add(signal_hash)
            seen_titles.add(normalized_title)
            unique_signals.append(signal)

        return unique_signals

    def _apply_source_limits(self, signals: list[Signal]) -> list[Signal]:
        per_source_counters: dict[str, int] = defaultdict(int)
        curated_signals: list[Signal] = []

        for signal in sorted(signals, key=self._sort_key, reverse=True):
            source = signal.source.lower().strip()
            limit = self._limit_for_source(source)
            if per_source_counters[source] >= limit:
                continue

            per_source_counters[source] += 1
            curated_signals.append(signal)

        return curated_signals

    def _limit_for_source(self, source: str) -> int:
        if source == "news":
            return self.max_news_signals
        if source == "reddit":
            return self.max_reddit_signals
        if source == "trends":
            return self.max_trends_signals
        return self.max_total_signals

    def _sort_key(self, signal: Signal) -> tuple:
        source_priority = {"news": 3, "reddit": 2, "trends": 1}.get(signal.source.lower().strip(), 0)
        return (
            source_priority,
            signal.published_at,
            len(signal.content),
        )


def build_analysis_payload(signals: list[Signal]) -> list[dict[str, object]]:
    normalizer = SignalNormalizer(
        max_total_signals=settings.analysis_max_total_signals,
        max_news_signals=settings.analysis_max_news_signals,
        max_reddit_signals=settings.analysis_max_reddit_signals,
        max_trends_signals=settings.analysis_max_trends_signals,
        max_content_length=settings.analysis_max_content_length,
    )
    normalized_signals = normalizer.enrich_for_analysis(signals)
    return [signal.model_dump(mode="json") for signal in normalized_signals]
