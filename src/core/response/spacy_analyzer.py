"""spaCy-based analyzer with persona logic and profile gap detection."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

try:
    import spacy
except Exception:  # pragma: no cover - optional dependency
    spacy = None


class SpaCyAnalyzer:
    """Perform lightweight analysis using spaCy when available."""

    def __init__(self) -> None:
        if spacy is not None:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except Exception:  # pragma: no cover - model may be missing
                self.nlp = spacy.blank("en")
        else:
            self.nlp = None

        # simple persona mapping based on intent and sentiment
        self.persona_map = {
            ("greeting", "positive"): "cheerful",
            ("greeting", "negative"): "formal",
            ("request", "positive"): "helpful",
            ("request", "negative"): "direct",
        }

    # --- helpers -----------------------------------------------------
    def _detect_intent(self, text: str) -> str:
        lower = text.lower()
        if any(g in lower for g in ["hi", "hello", "hey"]):
            return "greeting"
        if any(f in lower for f in ["bye", "goodbye"]):
            return "farewell"
        if "?" in text or "please" in lower or "could you" in lower:
            return "request"
        return "statement"

    def _sentiment(self, text: str) -> str:
        positives = {"good", "great", "awesome", "thanks"}
        negatives = {"bad", "hate", "terrible", "no"}
        tokens = set(text.lower().split())
        score = len(tokens & positives) - len(tokens & negatives)
        return "positive" if score >= 0 else "negative"

    # --- public API --------------------------------------------------
    def analyze(self, text: str) -> Dict[str, Any]:
        """Return analysis data for ``text``."""

        doc = self.nlp(text) if self.nlp is not None else None
        entities: List[Tuple[str, str]] = []
        if doc is not None:
            entities = [(ent.text, ent.label_) for ent in doc.ents]

        intent = self._detect_intent(text)
        sentiment = self._sentiment(text)
        persona = self.persona_map.get((intent, sentiment), "neutral")

        profile_gaps: List[str] = []
        if intent == "greeting" and "name" not in text.lower():
            profile_gaps.append("name")

        return {
            "intent": intent,
            "sentiment": sentiment,
            "entities": entities,
            "persona": persona,
            "profile_gaps": profile_gaps,
        }
