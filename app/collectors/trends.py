from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus

from pytrends.request import TrendReq

from app.collectors.base import Collector
from app.config.settings import settings
from app.config.source_config import load_source_config
from app.models.signal import Signal
from app.utils.retry import retry_call


class TrendsCollector(Collector):
    def __init__(self, keywords: list[str] | None = None) -> None:
        source_config = load_source_config()
        self._keywords = keywords or source_config.trend_keywords
        self._client = TrendReq(hl="pt-BR", tz=-180)

    def collect(self) -> list[Signal]:
        if not self._keywords:
            return []

        try:
            trends_frame = retry_call(
                self._fetch_interest_frame,
                attempts=settings.collector_retry_attempts,
                delay_seconds=settings.collector_retry_delay_seconds,
                exceptions=(Exception,),
            )
        except Exception:
            return []

        signals: list[Signal] = []
        collected_at = datetime.now(timezone.utc)

        for keyword in self._keywords:
            if keyword not in trends_frame.columns:
                continue

            series = trends_frame[keyword].dropna()
            if series.empty:
                continue

            first_value = float(series.iloc[0])
            last_value = float(series.iloc[-1])
            growth = self._calculate_growth(first_value, last_value)

            metadata = {
                "keyword": keyword,
                "growth": growth,
                "interest": int(last_value),
                "average_interest": float(series.mean()),
                "peak_interest": int(series.max()),
                "timeframe": "today 12-m",
            }

            signals.append(
                Signal(
                    source="trends",
                    title=keyword,
                    content=f"Keyword {keyword} with interest {int(last_value)} and growth {growth:.2f}%",
                    url=f"https://trends.google.com/trends/explore?q={quote_plus(keyword)}",
                    published_at=collected_at,
                    metadata=metadata,
                )
            )

        return signals

    def _fetch_interest_frame(self):
        self._client.build_payload(self._keywords, cat=0, timeframe="today 12-m", geo="", gprop="")
        frame = self._client.interest_over_time()
        if frame.empty:
            raise RuntimeError("Google Trends returned no data")
        if "isPartial" in frame.columns:
            frame = frame.drop(columns=["isPartial"])
        return frame

    def _calculate_growth(self, first_value: float, last_value: float) -> float:
        if first_value <= 0:
            return float(last_value)
        return ((last_value - first_value) / first_value) * 100.0
