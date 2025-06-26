from __future__ import annotations

import hashlib
from typing import List

from core.embedding_manager import EmbeddingManager


def _byte_embedding_model(byte_input: bytes, dim: int = 8) -> List[float]:
    h = hashlib.sha256(byte_input).digest()
    return [b / 255 for b in h[:dim]]


def get_embedding(text: str, model_type: str = "default") -> List[float]:
    """Return an embedding using byte or token mode."""
    if model_type == "byte":
        return _byte_embedding_model(text.encode("utf-8"))
    manager = EmbeddingManager()
    return manager.embed(text)
