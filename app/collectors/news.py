from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser

from app.collectors.base import Collector
from app.config.settings import settings
from app.config.source_config import load_source_config
from app.models.signal import Signal
from app.utils.retry import retry_call


class NewsCollector(Collector):
    def __init__(self, feeds: list[str] | None = None) -> None:
        source_config = load_source_config()
        self._feeds = feeds or source_config.rss_feeds

    def collect(self) -> list[Signal]:
        signals: list[Signal] = []

        for feed_url in self._feeds:
            try:
                feed = retry_call(
                    lambda: self._parse_feed(feed_url),
                    attempts=settings.collector_retry_attempts,
                    delay_seconds=settings.collector_retry_delay_seconds,
                )
            except Exception:
                continue

            feed_title = getattr(feed.feed, "title", feed_url)
            for entry in getattr(feed, "entries", []):
                signal = self._entry_to_signal(feed_url, feed_title, entry)
                if signal is not None:
                    signals.append(signal)

        return signals

    def _parse_feed(self, feed_url: str) -> Any:
        feed = feedparser.parse(feed_url)
        bozo_exception = getattr(feed, "bozo_exception", None)
        if getattr(feed, "bozo", False) and bozo_exception is not None:
            raise RuntimeError(f"Failed to parse RSS feed {feed_url}: {bozo_exception}")
        return feed

    def _entry_to_signal(self, feed_url: str, feed_title: str, entry: Any) -> Signal | None:
        title = getattr(entry, "title", "").strip()
        link = getattr(entry, "link", "").strip()
        summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
        published_at = self._parse_published_at(entry)

        if not title or not link:
            return None

        metadata = {
            "feed_url": feed_url,
            "feed_title": feed_title,
            "entry_id": getattr(entry, "id", None),
            "authors": getattr(entry, "authors", None),
            "tags": getattr(entry, "tags", None),
        }

        return Signal(
            source="news",
            title=title,
            content=summary,
            url=link,
            published_at=published_at,
            metadata=metadata,
        )

    def _parse_published_at(self, entry: Any) -> datetime:
        for field_name in ("published", "updated"):
            raw_value = getattr(entry, field_name, None)
            if raw_value:
                try:
                    return parsedate_to_datetime(raw_value).astimezone(timezone.utc)
                except (TypeError, ValueError, AttributeError):
                    pass

        for field_name in ("published_parsed", "updated_parsed"):
            parsed_value = getattr(entry, field_name, None)
            if parsed_value:
                return datetime(*parsed_value[:6], tzinfo=timezone.utc)

        return datetime.now(timezone.utc)
