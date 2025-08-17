"""spaCy wrapper for deeper NLP analysis."""

from __future__ import annotations

from typing import Dict, List
import logging


logger = logging.getLogger(__name__)

try:
    import spacy
except Exception:  # pragma: no cover - optional dep
    spacy = None


TRF_MODEL = "en_core_web_trf"
SM_MODEL = "en_core_web_sm"
DEFAULT_MODEL = TRF_MODEL


class SpaCyClient:
    """Expose common spaCy pipeline hooks."""

    def __init__(self, model_name: str | None = None) -> None:
        if spacy is None:
            raise RuntimeError("spaCy is required for SpaCyClient")

        chosen_model = model_name or DEFAULT_MODEL
        try:
            self.nlp = spacy.load(chosen_model)
            self.model_name = chosen_model
        except Exception:
            if chosen_model != SM_MODEL:
                logger.warning(
                    "[SpaCyClient] ⚠️ Failed to load %s. Falling back to %s.",
                    chosen_model,
                    SM_MODEL,
                )
                self.nlp = spacy.load(SM_MODEL)
                self.model_name = SM_MODEL
            else:
                raise

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
