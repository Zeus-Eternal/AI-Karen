"""Inference helper for personalised DistilBERT models."""
from __future__ import annotations

from pathlib import Path
from typing import List

try:
    import torch
except Exception:  # pragma: no cover - optional dep
    torch = None
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
except Exception:  # pragma: no cover - optional dep
    AutoTokenizer = AutoModelForSequenceClassification = pipeline = None


class LNMClient:
    """Thin wrapper around transformers pipelines."""

    def __init__(self, model_dir: Path) -> None:
        if AutoTokenizer is None or AutoModelForSequenceClassification is None or pipeline is None:
            raise RuntimeError("transformers library is required for LNMClient")
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        device = 0 if (torch and torch.cuda.is_available()) else -1
        self.cls_pipe = pipeline(
            "text-classification", model=self.model, tokenizer=self.tokenizer, device=device
        )
        self.feat_pipe = pipeline(
            "feature-extraction", model=self.model, tokenizer=self.tokenizer, device=device
        )

    def classify(self, text: str) -> str:
        """Return the predicted label."""
        return max(self.cls_pipe(text), key=lambda x: x["score"])["label"]

    def embed(self, text: str) -> List[float]:
        """Return mean-pooled embedding."""
        emb = self.feat_pipe(text, truncation=True, padding=True, return_tensors="pt")[0]
        return emb.mean(dim=0).tolist()

    def generate(self, text: str, context: str | None = None) -> str:
        """Simplistic echo generation with intent filter."""
        label = self.classify(text)
        if label == "chit_chat" and context:
            return f"{context} … {text}"
        return f"Intent '{label}' acknowledged."
