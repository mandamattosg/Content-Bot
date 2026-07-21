from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.models.signal import Signal


class AIProvider(ABC):
    @abstractmethod
    def analyze(self, signals: list[Signal]) -> dict[str, Any]:
        """Analyze a list of signals and return a structured payload."""
        raise NotImplementedError
