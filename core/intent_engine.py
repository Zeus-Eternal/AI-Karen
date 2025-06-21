"""Configurable intent detection engine."""

import re
from typing import Dict, List, Tuple


class IntentEngine:
    """Runtime-configurable regex intent detector."""

    def __init__(self, pattern_file: str | None = None) -> None:
        self.patterns: Dict[str, Tuple[re.Pattern, str]] = {}
        if pattern_file:
            self._load_from_file(pattern_file)
        else:
            self.add_intent("greet", r"\b(hello|hi|ping)\b")
            self.add_intent("deep_reasoning", r"\b(why|reason|because)\b")

    def _load_from_file(self, path: str) -> None:
        import json

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for intent, cfg in data.items():
            pattern = cfg["pattern"] if isinstance(cfg, dict) else str(cfg)
            category = cfg.get("category", "default") if isinstance(cfg, dict) else "default"
            self.add_intent(intent, pattern, category)

    def add_intent(self, name: str, pattern: str, category: str = "default") -> None:
        """Register a new intent at runtime."""
        self.patterns[name] = (re.compile(pattern, re.I), category)

    def remove_intent(self, name: str) -> None:
        self.patterns.pop(name, None)

    def list_intents(self) -> List[str]:
        return list(self.patterns.keys())

    def detect_intent(self, text: str) -> Tuple[str, float, str]:
        """Return ``(intent, confidence, category)`` for the given text."""
        for intent, (pattern, category) in self.patterns.items():
            m = pattern.search(text)
            if m:
                confidence = 1.0 if m.group(0).lower() == text.lower() else 0.8
                return intent, confidence, category
        return "unknown", 0.0, "default"
