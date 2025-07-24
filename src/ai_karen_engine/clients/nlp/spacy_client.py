"""spaCy wrapper for deeper NLP analysis."""

from __future__ import annotations

from typing import Dict, List
import logging


logger = logging.getLogger(__name__)

try:
    import spacy
except Exception:  # pragma: no cover - optional dep
    spacy = None


DEFAULT_MODEL = "en_core_web_sm"


class SpaCyClient:
    """Expose common spaCy pipeline hooks."""

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        if spacy is None:
            raise RuntimeError("spaCy is required for SpaCyClient")
        try:
            self.nlp = spacy.load(model_name)
        except Exception:
            logger.warning(
                "[SpaCyClient] ⚠️ Failed to load %s. Falling back to en_core_web_sm.",
                model_name,
            )
            self.nlp = spacy.load("en_core_web_sm")

    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        doc = self.nlp(text)
        return [{"text": ent.text, "label": ent.label_} for ent in doc.ents]

    def pos_tags(self, text: str) -> List[Dict[str, str]]:
        doc = self.nlp(text)
        return [{"text": tok.text, "pos": tok.pos_} for tok in doc]

    def dependency_tree(self, text: str) -> List[Dict[str, str]]:
        doc = self.nlp(text)
        return [
            {"text": tok.text, "dep": tok.dep_, "head": tok.head.text} for tok in doc
        ]
