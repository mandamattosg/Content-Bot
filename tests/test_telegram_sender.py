from app.telegram.sender import TelegramSender


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
                    }
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
