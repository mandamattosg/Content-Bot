from app.collectors.base import Collector
from app.collectors.news import NewsCollector
from app.collectors.reddit import RedditCollector
from app.collectors.trends import TrendsCollector

__all__ = ["Collector", "NewsCollector", "RedditCollector", "TrendsCollector"]
