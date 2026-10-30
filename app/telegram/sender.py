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
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "disable_notification": False,
        }
        try:
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError:
            try:
                detail = response.json() if response is not None else {}
            except ValueError:
                detail = {"raw": response.text if response is not None else ""}
            status_code = response.status_code if response is not None else None
            return {
                "ok": False,
                "error": "telegram_send_failed",
                "status_code": status_code,
                "message": f"Telegram API returned HTTP {status_code}",
                "details": detail,
            }
        # str(exc) from requests includes the URL, which contains the bot token.
        except requests.RequestException as exc:
            return {
                "ok": False,
                "error": "telegram_send_failed",
                "status_code": None,
                "message": f"Telegram request failed: {type(exc).__name__}",
                "details": {},
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

        split_index = max(1, len(topics) // 2)
        topic_blocks = [topics[:split_index], topics[split_index:]]

        blocks = []
        for block_topics in topic_blocks:
            if not block_topics:
                continue
            lines = list(header_lines)
            for topic in block_topics:
                score = topic.get("score", 0)
                stars = "★" * int(round(score / 2))
                lines.append(f"• {html.escape(str(topic.get('topic', 'Tema')))}")
                lines.append(f"Nota: {score}/10 {stars}")

                reason = str(topic.get("reason", "")).strip()
                if reason:
                    lines.append(f"Motivo: {html.escape(reason)}")

                source_trace = topic.get("source_trace", [])[:1]
                if source_trace:
                    lines.append("Origem:")
                    for entry in source_trace:
                        label = str(entry.get("source_name") or entry.get("source") or "Fonte")
                        lines.append(f"  • {html.escape(label)}")

                ideas = topic.get("video_ideas", [])[:3]
                if ideas:
                    lines.append("Ideias:")
                    for idea in ideas:
                        lines.append(f"  • {html.escape(str(idea))}")

                lines.append("")
            blocks.append("\n".join(lines).strip())

        return blocks
