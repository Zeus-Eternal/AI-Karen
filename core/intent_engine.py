"""Simple intent detection engine."""

import re
from typing import Tuple


class IntentEngine:
    """Naive intent detector using regex rules."""

    def __init__(self) -> None:
        patterns = {
            "greet": re.compile(r"\b(hello|hi|ping)\b", re.I),
            "deep_reasoning": re.compile(r"\b(why|reason|because)\b", re.I),
        }
        self.patterns = patterns

    def detect_intent(self, text: str) -> Tuple[str, float, str]:
        """Return (intent, confidence, category)."""
        for intent, pattern in self.patterns.items():
            if pattern.search(text):
                return intent, 0.9, "default"
        return "unknown", 0.0, "default"
