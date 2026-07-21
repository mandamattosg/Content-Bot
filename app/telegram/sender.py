from __future__ import annotations

import html
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
            "chat_id": str(self._chat_id).strip(),
            "text": text,
            "disable_web_page_preview": True,
            "disable_notification": False,
        }
        try:
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            try:
                detail = response.json() if response is not None else {}
            except ValueError:
                detail = {"raw": response.text if response is not None else ""}
            return {
                "ok": False,
                "error": "telegram_send_failed",
                "status_code": response.status_code if response is not None else None,
                "message": str(exc),
                "details": detail,
            }

    def send_messages(self, texts: list[str]) -> list[dict[str, Any]]:
        return [self.send_message(text) for text in texts]

    def build_summary_message(self, analysis: dict[str, Any], *, signals_count: int) -> str:
        messages = self.build_summary_messages(analysis, signals_count=signals_count)
        return messages[0] if messages else ""

    def build_summary_messages(self, analysis: dict[str, Any], *, signals_count: int) -> list[str]:
        topics = analysis.get("topics", [])
        header_lines = [
            "📚 Content Radar",
            "",
            f"Foram analisados {signals_count} sinais recentes.",
            "",
        ]

        if not topics:
            return ["\n".join(header_lines + ["Nenhum tópico relevante foi identificado no momento."])]

        first_block_topics = topics[:3]
        second_block_topics = topics[3:6]

        blocks = []
        for block_topics in (first_block_topics, second_block_topics):
            if not block_topics:
                continue
            lines = list(header_lines)
            for topic in block_topics:
                score = topic.get("score", 0)
                stars = "★" * int(round(score / 2))
                lines.append(html.escape(str(topic.get("topic", "Tema"))))
                lines.append(f"Nota: {score}/10 {stars}")
                reason = html.escape(str(topic.get("reason", "")))
                lines.append(f"Motivo: {reason[:220]}")
                source_trace = topic.get("source_trace", [])[:1]
                if source_trace:
                    lines.append("Origem:")
                    for entry in source_trace:
                        label = html.escape(str(entry.get("source_name") or entry.get("source") or "Fonte"))
                        title = html.escape(str(entry.get("title") or ""))
                        url = entry.get("url") or ""
                        if url:
                            lines.append(f"• {label}: {title} ({url})")
                        else:
                            lines.append(f"• {label}: {title}")
                ideas = topic.get("video_ideas", [])[:1]
                if ideas:
                    lines.append("Ideias:")
                    for idea in ideas:
                        lines.append(f"• {html.escape(str(idea))}")
                lines.append("")
            blocks.append("\n".join(lines).strip())

        return blocks
