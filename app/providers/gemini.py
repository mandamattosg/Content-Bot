from __future__ import annotations

import json
import re
from typing import Any

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from app.config.settings import settings
from app.models.signal import Signal
from app.prompts.daily_analysis import load_daily_analysis_prompt
from app.providers.base import AIProvider


class GeminiQuotaError(RuntimeError):
    pass


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str | None = None, model_name: str | None = None) -> None:
        self._api_key = api_key or settings.gemini_api_key
        self._model_name = model_name or settings.gemini_model_name or "gemini-2.0-flash"
        self._fallback_models = self._candidate_models(self._model_name)
        if self._api_key:
            genai.configure(api_key=self._api_key)

    def analyze(self, signals: list[Signal]) -> dict[str, Any]:
        if not self._api_key:
            raise ValueError("GEMINI_API_KEY is required")

        prompt = load_daily_analysis_prompt()
        payload = self._build_payload(signals)
        request_text = f"{prompt}\n\nSignals:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"

        last_error: Exception | None = None
        for model_name in self._fallback_models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(request_text)
                return self._parse_response(response.text)
            except Exception as exc:  # pragma: no cover - exercised in runtime
                last_error = exc
                if self._is_quota_error(exc):
                    raise GeminiQuotaError(str(exc)) from exc
                if not self._is_model_unavailable(exc):
                    raise

        if last_error is not None:
            if self._is_quota_error(last_error):
                raise GeminiQuotaError(str(last_error)) from last_error
            raise last_error
        raise RuntimeError("Gemini analysis failed")

    def _candidate_models(self, preferred_model: str) -> list[str]:
        preferred = preferred_model.strip()
        fallback_models = [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro",
        ]
        if preferred:
            fallback_models.insert(0, preferred)
        return list(dict.fromkeys(model for model in fallback_models if model))

    def _is_model_unavailable(self, exc: Exception) -> bool:
        return isinstance(exc, google_exceptions.NotFound) or "not found" in str(exc).lower()

    def _is_quota_error(self, exc: Exception) -> bool:
        message = str(exc).lower()
        return isinstance(exc, google_exceptions.ResourceExhausted) or "quota" in message or "rate limit" in message

    def _build_payload(self, signals: list[Signal]) -> list[dict[str, Any]]:
        return [
            {
                "source": signal.source,
                "title": signal.title,
                "content": signal.content,
                "url": str(signal.url),
                "published_at": signal.published_at.isoformat(),
                "metadata": signal.metadata,
            }
            for signal in signals
        ]

    def _parse_response(self, response_text: str) -> dict[str, Any]:
        cleaned = response_text.strip()
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL | re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()

        return json.loads(cleaned)
