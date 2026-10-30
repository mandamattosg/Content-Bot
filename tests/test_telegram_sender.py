import requests

from app.telegram.sender import TelegramSender


def test_send_message_http_error_does_not_expose_token(monkeypatch) -> None:
    sender = TelegramSender(token="SECRET-TOKEN", chat_id="chat")

    class DummyResponse:
        status_code = 404
        text = "not found"

        def raise_for_status(self) -> None:
            raise requests.HTTPError("404 for url: https://api.telegram.org/botSECRET-TOKEN/sendMessage")

        def json(self) -> dict[str, object]:
            return {"ok": False, "description": "Not Found"}

    monkeypatch.setattr("app.telegram.sender.requests.post", lambda *args, **kwargs: DummyResponse())

    result = sender.send_message("Olá")

    assert result["ok"] is False
    assert result["status_code"] == 404
    assert "SECRET-TOKEN" not in str(result)


def test_send_message_connection_error_does_not_expose_token(monkeypatch) -> None:
    sender = TelegramSender(token="SECRET-TOKEN", chat_id="chat")

    def fake_post(*args: object, **kwargs: object) -> None:
        raise requests.ConnectionError("Max retries exceeded with url: /botSECRET-TOKEN/sendMessage")

    monkeypatch.setattr("app.telegram.sender.requests.post", fake_post)

    result = sender.send_message("Olá")

    assert result["ok"] is False
    assert result["message"] == "Telegram request failed: ConnectionError"
    assert "SECRET-TOKEN" not in str(result)


def test_send_message_uses_html_parse_mode(monkeypatch) -> None:
    sender = TelegramSender(token="token", chat_id="chat")
    captured = {}

    class DummyResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, bool]:
            return {"ok": True}

    def fake_post(url: str, json: dict[str, object] | None = None, timeout: int | None = None) -> DummyResponse:
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return DummyResponse()

    monkeypatch.setattr("app.telegram.sender.requests.post", fake_post)

    sender.send_message("Olá")

    assert captured["json"]["parse_mode"] == "HTML"


def test_build_summary_message_escapes_html_special_chars() -> None:
    sender = TelegramSender(token="token", chat_id="chat")
    analysis = {
        "topics": [
            {
                "topic": "Tema <tag>",
                "score": 8,
                "reason": "Motivo & <script>",
                "video_ideas": ["Ideia <x>"],
                "source_trace": [
                    {
                        "source_name": "Portal <A>",
                        "title": "Título <B>",
                        "url": "https://example.com/?a=1&b=2",
                    },
                    {
                        "source_name": "Outro Portal <C>",
                        "title": "Outro Título <D>",
                        "url": "https://example.com/2",
                    },
                ],
            }
        ],
        "signals_count": 1,
    }

    message = sender.build_summary_message(analysis, signals_count=1)

    assert "Tema &lt;tag&gt;" in message
    assert "Motivo: Motivo &amp; &lt;script&gt;" in message
    assert "Ideias:" in message
    assert "Ideia &lt;x&gt;" in message
    assert "Portal &lt;A&gt;" in message
    assert "Outro Portal &lt;C&gt;" not in message
