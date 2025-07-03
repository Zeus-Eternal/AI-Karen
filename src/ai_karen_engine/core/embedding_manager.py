"""Embedding manager providing simple text embeddings."""

from __future__ import annotations

import hashlib
import time
from typing import List


_METRICS = {}


def record_metric(name: str, value: float) -> None:
    _METRICS.setdefault(name, []).append(value)


class EmbeddingManager:
    """Return deterministic embeddings using hashlib."""

    def __init__(self, dim: int = 8) -> None:
        self.dim = dim

    def embed(self, text: str) -> List[float]:
        """Embed text into a fixed-size vector."""
        start = time.time()
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vector = [b / 255 for b in h[: self.dim]]
        record_metric("embedding_time_seconds", time.time() - start)
        return vector
