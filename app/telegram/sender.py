from __future__ import annotations

from typing import Any

import requests

from app.config.settings import settings


class TelegramSender:
    def __init__(self, token: str | None = None, chat_id: str | None = None) -> None:
        self._token = token or settings.telegram_token
        self._chat_id = chat_id or settings.telegram_chat_id

    def send_message(self, text: str) -> dict[str, Any]:
        if not self._token or not self._chat_id:
            raise ValueError("TELEGRAM_TOKEN and TELEGRAM_CHAT_ID are required")

        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()

    def build_summary_message(self, analysis: dict[str, Any], *, signals_count: int) -> str:
        topics = analysis.get("topics", [])
        lines = [
            "📚 <b>Content Radar</b>",
            "",
            f"Foram analisados <b>{signals_count}</b> sinais recentes.",
            "",
        ]

        if not topics:
            lines.append("Nenhum tópico relevante foi identificado no momento.")
            return "\n".join(lines)

        for topic in topics:
            score = topic.get("score", 0)
            stars = "★" * int(round(score / 2))
            lines.append(f"<b>{topic.get('topic', 'Tema')}</b>")
            lines.append(f"Nota: {score}/10 {stars}")
            lines.append(f"Motivo: {topic.get('reason', '')}")
            source_trace = topic.get("source_trace", [])
            if source_trace:
                lines.append("Origem:")
                for entry in source_trace:
                    label = entry.get("source_name") or entry.get("source") or "Fonte"
                    title = entry.get("title") or ""
                    url = entry.get("url") or ""
                    if url:
                        lines.append(f"• {label}: {title} ({url})")
                    else:
                        lines.append(f"• {label}: {title}")
            ideas = topic.get("video_ideas", [])
            if ideas:
                lines.append("Ideias:")
                for idea in ideas:
                    lines.append(f"• {idea}")
            lines.append("")

        return "\n".join(lines).strip()
