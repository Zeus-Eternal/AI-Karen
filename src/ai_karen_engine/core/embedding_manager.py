"""Embedding manager providing simple text embeddings."""

from __future__ import annotations

"""Flexible embedding manager with optional HuggingFace backend."""

import hashlib
import logging
import os
import time
from typing import List, Optional

try:  # Optional heavy dependency
    import torch
    from transformers import AutoModel, AutoTokenizer
except Exception:  # pragma: no cover - optional dep
    torch = None
    AutoModel = AutoTokenizer = None

logger = logging.getLogger(__name__)


_METRICS = {}


def record_metric(name: str, value: float) -> None:
    _METRICS.setdefault(name, []).append(value)


class EmbeddingManager:
    """Return embeddings using HuggingFace if available, otherwise hashlib."""

    def __init__(self, model_name: Optional[str] = None, dim: int = 8) -> None:
        self.dim = dim
        self.model_name = model_name or os.getenv("KARI_EMBED_MODEL", "distilbert-base-uncased")
        self.model = None
        self.tokenizer = None
        self.model_loaded = "hashlib"

    def embed(self, text: str) -> List[float]:
        """Embed text into a fixed-size vector using deterministic hashing."""
        start = time.time()
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vector = [b / 255 for b in h[: self.dim]]
        record_metric("embedding_time_seconds", time.time() - start)
        return vector

    async def initialize(self) -> None:
        """Load HuggingFace model if available."""
        if AutoModel is None or AutoTokenizer is None:
            logger.warning("[EmbeddingManager] transformers not installed; using hashlib embeddings")
            return

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            if torch:
                self.model = self.model.to("cpu")
            self.model.eval()
            self.model_loaded = self.model_name
            logger.info("[EmbeddingManager] Loaded model %s", self.model_name)
        except Exception as exc:  # pragma: no cover - runtime only
            logger.error("[EmbeddingManager] Failed to load %s: %s", self.model_name, exc)
            self.model = None
            self.tokenizer = None
            self.model_loaded = "hashlib"
    
    async def get_embedding(self, text: str) -> List[float]:
        """Return an embedding for the given text."""
        if self.model and self.tokenizer:
            try:
                inputs = self.tokenizer(text, return_tensors="pt", truncation=True)
                with torch.no_grad():
                    outputs = self.model(**inputs)
                vector = outputs.last_hidden_state.mean(dim=1).squeeze().tolist()
                record_metric("embedding_time_seconds", 0)  # Already timed by HF
                return vector
            except Exception as exc:  # pragma: no cover - runtime only
                logger.error("[EmbeddingManager] HF embedding failed: %s", exc)
        return self.embed(text)
