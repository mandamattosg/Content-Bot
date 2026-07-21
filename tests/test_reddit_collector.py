import json
from types import SimpleNamespace

from app.collectors.reddit import RedditCollector


class FakeResponse:
    def __init__(self, *, status_code=200, text="", headers=None, json_data=None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}
        self._json_data = json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json_data


def test_reddit_collector_falls_back_to_json_when_rss_is_empty(monkeypatch):
    collector = RedditCollector(["python"])

    responses = iter(
        [
            FakeResponse(status_code=200, text="<html>blocked</html>"),
            FakeResponse(
                status_code=200,
                json_data=[
                    {
                        "data": {
                            "children": [
                                {
                                    "data": {
                                        "title": "Post title",
                                        "url": "https://reddit.com/r/python/comments/1/post",
                                        "selftext": "Body",
                                        "permalink": "/r/python/comments/1/post",
                                        "score": 10,
                                        "num_comments": 3,
                                        "upvote_ratio": 0.9,
                                        "author": "author",
                                        "created_utc": 1710000000,
                                    }
                                }
                            ]
                        }
                    }
                ],
            ),
        ]
    )

    def fake_get(url, timeout=None):
        return next(responses)

    monkeypatch.setattr(collector._session, "get", fake_get)

    posts = collector._fetch_subreddit_posts("python")

    assert len(posts) == 1
    assert posts[0]["title"] == "Post title"
