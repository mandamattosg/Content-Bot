from __future__ import annotations

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from json import JSONDecodeError
from typing import Any

import feedparser
import requests

from app.collectors.base import Collector
from app.config.settings import settings
from app.config.source_config import load_source_config
from app.models.signal import Signal


logger = logging.getLogger(__name__)


class RedditRateLimitError(RuntimeError):
    def __init__(self, subreddit: str, retry_after_seconds: float | None = None) -> None:
        super().__init__(f"Reddit rate limit for subreddit {subreddit}")
        self.retry_after_seconds = retry_after_seconds


class RedditCollector(Collector):
    def __init__(self, subreddits: list[str] | None = None) -> None:
        source_config = load_source_config()
        self._subreddits = subreddits or source_config.reddit_subreddits
        self._session = requests.Session()
        self._subreddit_cache: dict[str, list[dict[str, Any]]] = {}
        self._session.headers.update(
            {
                "User-Agent": settings.reddit_user_agent,
                "Accept": "application/atom+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
            }
        )

    def collect(self) -> list[Signal]:
        signals: list[Signal] = []

        for subreddit in self._subreddits:
            posts = self._collect_subreddit_posts(subreddit)
            if not posts:
                continue

            for post in posts:
                signal = self._post_to_signal(subreddit, post)
                if signal is not None:
                    signals.append(signal)

        return signals

    def _collect_subreddit_posts(self, subreddit: str) -> list[dict[str, Any]]:
        cached_posts = self._subreddit_cache.get(subreddit)
        if cached_posts:
            return cached_posts

        attempts = max(settings.collector_retry_attempts, 2)
        base_delay = max(settings.collector_retry_delay_seconds, 1.0)

        for attempt in range(1, attempts + 1):
            try:
                posts = self._fetch_subreddit_posts(subreddit)
                self._subreddit_cache[subreddit] = posts
                return posts
            except RedditRateLimitError as error:
                retry_after = error.retry_after_seconds or 0.0
                sleep_seconds = max(retry_after, base_delay * attempt)
                logger.info("Reddit rate limited for r/%s; skipping after %.1fs", subreddit, sleep_seconds)
                break
            except (requests.RequestException, RuntimeError, ValueError, JSONDecodeError):
                if attempt < attempts:
                    import time

                    time.sleep(base_delay * attempt)
                continue

        return cached_posts or []

    def _fetch_subreddit_posts(self, subreddit: str) -> list[dict[str, Any]]:
        url = f"https://www.reddit.com/r/{subreddit}/.rss"
        response = self._session.get(url, timeout=settings.collector_timeout_seconds)
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_after_seconds = float(retry_after) if retry_after and retry_after.isdigit() else None
            raise RedditRateLimitError(subreddit, retry_after_seconds=retry_after_seconds)
        response.raise_for_status()

        feed = feedparser.parse(response.text)
        if getattr(feed, "bozo", False) and getattr(feed, "bozo_exception", None) is not None:
            raise RuntimeError(f"Failed to parse Reddit RSS for subreddit {subreddit}: {feed.bozo_exception}")

        entries = []
        for entry in getattr(feed, "entries", []):
            entries.append(
                {
                    "title": getattr(entry, "title", ""),
                    "url": getattr(entry, "link", ""),
                    "selftext": getattr(entry, "summary", ""),
                    "permalink": getattr(entry, "link", ""),
                    "score": None,
                    "num_comments": None,
                    "upvote_ratio": None,
                    "author": getattr(entry, "author", None),
                    "created_utc": self._entry_time_to_utc(getattr(entry, "published", None)),
                }
            )

        return entries

    def _entry_time_to_utc(self, published: str | None) -> float | None:
        if not published:
            return None

        try:
            return parsedate_to_datetime(published).astimezone(timezone.utc).timestamp()
        except (TypeError, ValueError, AttributeError):
            return None

    def _post_to_signal(self, subreddit: str, post: dict[str, Any]) -> Signal | None:
        title = str(post.get("title", "")).strip()
        permalink = str(post.get("permalink", "")).strip()
        url_value = str(post.get("url", "")).strip()
        if not url_value and permalink:
            url_value = f"https://www.reddit.com{permalink}"
        content = str(post.get("selftext", "")).strip()

        if not title or not url_value:
            return None

        created_utc = post.get("created_utc")
        published_at = datetime.fromtimestamp(created_utc, tz=timezone.utc) if created_utc else datetime.now(timezone.utc)

        metadata = {
            "subreddit": subreddit,
            "score": post.get("score"),
            "num_comments": post.get("num_comments"),
            "upvote_ratio": post.get("upvote_ratio"),
            "author": post.get("author"),
            "permalink": permalink,
        }

        return Signal(
            source="reddit",
            title=title,
            content=content,
            url=url_value,
            published_at=published_at,
            metadata=metadata,
        )
