"""spaCy NLP service with graceful degradation."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

try:  # pragma: no cover - optional dep
    import spacy  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    spacy = None

logger = logging.getLogger(__name__)


@dataclass
class _ServiceState:
    model_name: str = "en_core_web_sm"
    model_loaded: bool = False


class NLPService:
    """Provide common NLP operations using spaCy with fallbacks."""

    def __init__(self, model_name: str | None = None) -> None:
        self.state = _ServiceState(model_name or _ServiceState.model_name)
        self.nlp = None
        self._load_spacy_model()

    def _load_spacy_model(self) -> None:
        if spacy is None:
            logger.warning("spaCy not installed; using basic tokenization")
            return
        try:
            self.nlp = spacy.load(self.state.model_name)
            self.state.model_loaded = True
        except Exception as exc:
            logger.error(
                "Failed to load spaCy model %s: %s", self.state.model_name, exc
            )
            self.nlp = None
            self.state.model_loaded = False

    def tokenize(self, text: str) -> List[str]:
        if self.nlp:
            return [t.text for t in self.nlp(text)]
        return text.split()

    def get_pos_tags(self, text: str) -> List[Dict[str, str]]:
        if not self.nlp:
            return []
        doc = self.nlp(text)
        return [{"text": t.text, "pos": t.pos_} for t in doc]

    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        if not self.nlp:
            return []
        doc = self.nlp(text)
        return [{"text": ent.text, "label": ent.label_} for ent in doc.ents]

    def process_text(self, text: str) -> Dict[str, Any]:
        if not self.nlp:
            return {"tokens": self.tokenize(text)}
        doc = self.nlp(text)
        return {
            "tokens": [t.text for t in doc],
            "entities": [{"text": e.text, "label": e.label_} for e in doc.ents],
            "pos_tags": [{"text": t.text, "pos": t.pos_} for t in doc],
        }
