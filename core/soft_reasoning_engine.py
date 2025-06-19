"""Simple reasoning engine that stores and retrieves memories."""

from __future__ import annotations

from typing import Any, Dict, List

from .embedding_manager import EmbeddingManager
from .milvus_client import MilvusClient


class SoftReasoningEngine:
    """Combine embeddings with a surprise score heuristic."""

    def __init__(self) -> None:
        self.embeddings = EmbeddingManager()
        self.store = MilvusClient()

    def _surprise(self, vector: List[float]) -> float:
        results = self.store.search(vector, top_k=1)
        if not results:
            return 1.0
        return 1.0 - results[0]["score"]

    def ingest(self, text: str, metadata: Dict[str, Any] | None = None) -> int | None:
        metadata = metadata or {}
        vector = self.embeddings.embed(text)
        if self._surprise(vector) < 0.1:
            return None
        return self.store.upsert(vector, {"text": text, **metadata})

    def query(self, text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        vector = self.embeddings.embed(text)
        return self.store.search(vector, top_k=top_k)
