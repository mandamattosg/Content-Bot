import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)
pipeline_paths = [
    route.path
    for route in main.app.routes
    if isinstance(route, APIRoute) and route.path.startswith("/pipeline/")
]


def test_all_expected_routes_are_checked() -> None:
    assert len(pipeline_paths) == 5


@pytest.mark.parametrize("path", pipeline_paths)
def test_pipeline_routes_reject_missing_or_wrong_key(monkeypatch, path: str) -> None:
    monkeypatch.setattr(main.settings, "pipeline_api_key", "right-key")

    assert client.post(path).status_code == 401
    assert client.post(path, headers={"X-API-Key": "wrong-key"}).status_code == 401


@pytest.mark.parametrize("path", pipeline_paths)
def test_pipeline_routes_fail_closed_without_configured_key(monkeypatch, path: str) -> None:
    monkeypatch.setattr(main.settings, "pipeline_api_key", "")

    assert client.post(path).status_code == 503
    assert client.post(path, headers={"X-API-Key": ""}).status_code == 503


def test_pipeline_route_accepts_right_key(monkeypatch) -> None:
    class FakeProvider:
        def __init__(self, api_key: str) -> None:
            pass

        def analyze(self, signals: list) -> dict[str, bool]:
            return {"called": True}

    monkeypatch.setattr(main.settings, "pipeline_api_key", "right-key")
    monkeypatch.setattr(main, "GeminiProvider", FakeProvider)

    response = client.post("/pipeline/gemini-test", headers={"X-API-Key": "right-key"})

    assert response.status_code == 200
    assert response.json()["response"] == {"called": True}


def test_public_routes_do_not_require_key(monkeypatch) -> None:
    monkeypatch.setattr(main.settings, "pipeline_api_key", "right-key")

    assert client.get("/health").status_code == 200
