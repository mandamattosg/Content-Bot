from __future__ import annotations

import hashlib

from app.models.signal import Signal
from app.utils.text import normalize_text


def build_signal_hash(signal: Signal) -> str:
    canonical_parts = [
        signal.source.lower().strip(),
        normalize_text(signal.title).lower(),
        normalize_text(signal.content).lower(),
        str(signal.url).strip().lower(),
        signal.published_at.isoformat(),
    ]
    canonical_value = "|".join(canonical_parts)
    return hashlib.sha256(canonical_value.encode("utf-8")).hexdigest()
