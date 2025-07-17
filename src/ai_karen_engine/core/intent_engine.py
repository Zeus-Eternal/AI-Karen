"""Simple regex-based IntentEngine."""

from __future__ import annotations

import re
from typing import Dict, Pattern, Tuple, Optional


class IntentEngine:
    """Regex intent matcher with runtime registration."""

    def __init__(self) -> None:
        self._intents: Dict[str, Pattern[str]] = {
            "greet": re.compile(r"\b(hello|hi|hey|ping)\b", re.I),
            "deep_reasoning": re.compile(r"\bwhy\b", re.I),
            "time_query": re.compile(r"\btime\b", re.I),
        }

    def add_intent(self, name: str, pattern: str) -> None:
        """Register a new intent regex at runtime."""
        self._intents[name] = re.compile(pattern, re.I)

    def remove_intent(self, name: str) -> None:
        """Remove a runtime intent if present."""
        self._intents.pop(name, None)

    def detect_intent(self, text: str) -> Tuple[str, float, Dict[str, str]]:
        """Return (intent, confidence, meta) for a text."""
        query = text.lower()
        for intent, pattern in self._intents.items():
            if pattern.search(query):
                return intent, 1.0, {"pattern": pattern.pattern}
        return "unknown", 0.0, {}


__all__ = ["IntentEngine"]
