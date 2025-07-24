"""Eco Mode responder using lightweight local NLP models."""

from __future__ import annotations

from pathlib import Path
from typing import List

from ai_karen_engine.clients.nlp.basic_classifier import BasicClassifier
from ai_karen_engine.clients.nlp.spacy_client import SpaCyClient
from ai_karen_engine.clients.transformers.lnm_client import LNMClient


class EcoModeResponder:
    """Generate simple responses using local models."""

    def __init__(self) -> None:
        self.classifier = BasicClassifier(Path("models/basic_cls"))
        self.spacy = SpaCyClient()
        self.lnm = LNMClient(Path("models/distilbert-base-uncased"))

    def respond(self, text: str) -> str:
        label, confidence = self.classifier.predict(text)
        ents: List[str] = [e["text"] for e in self.spacy.extract_entities(text)]
        context = f"intent: {label} (conf {confidence:.2f}); entities: {', '.join(ents)}"
        return self.lnm.generate(text, context=context)
