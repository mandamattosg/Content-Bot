from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class SourceConfig:
    rss_feeds: list[str]
    reddit_subreddits: list[str]
    trend_keywords: list[str]


def load_source_config(path: Path | None = None) -> SourceConfig:
    config_path = path or Path(__file__).with_name("sources.yaml")
    with config_path.open("r", encoding="utf-8") as file_handle:
        raw_config = yaml.safe_load(file_handle) or {}

    return SourceConfig(
        rss_feeds=list(raw_config.get("rss_feeds", [])),
        reddit_subreddits=list(raw_config.get("reddit_subreddits", [])),
        trend_keywords=list(raw_config.get("trend_keywords", [])),
    )
