from app.telegram.sender import TelegramSender


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
    assert "Motivo &amp; &lt;script&gt;" in message
    assert "Ideia &lt;x&gt;" in message
    assert "Portal &lt;A&gt;" in message
