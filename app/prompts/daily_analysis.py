from __future__ import annotations

from pathlib import Path


PROMPT_PATH = Path(__file__).with_name("daily_analysis.md")


def load_daily_analysis_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")
