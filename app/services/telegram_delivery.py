from __future__ import annotations

from typing import Any

from app.config.settings import settings
from app.telegram.sender import TelegramSender


class TelegramDeliveryService:
    def __init__(self, sender: TelegramSender | None = None) -> None:
        self._sender = sender or TelegramSender()

    def send_analysis_summary(self, analysis: dict[str, Any], *, signals_count: int) -> dict[str, Any]:
        if not settings.telegram_token or not settings.telegram_chat_id:
            raise ValueError("Telegram credentials are not configured")

        messages = self._sender.build_summary_messages(analysis, signals_count=signals_count)
        if len(messages) == 1:
            return self._sender.send_message(messages[0])

        results = self._sender.send_messages(messages)
        return {
            "ok": all(result.get("ok") for result in results),
            "sent_messages": len(results),
            "results": results,
        }
