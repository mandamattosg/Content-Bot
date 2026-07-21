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

        message = self._sender.build_summary_message(analysis, signals_count=signals_count)
        return self._sender.send_message(message)
