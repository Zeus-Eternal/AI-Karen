"""Simple reasoning engine that stores and retrieves memories."""

from __future__ import annotations

import time
from typing import Any, Dict, List

from .embedding_manager import EmbeddingManager
from .milvus_client import MilvusClient


class SoftReasoningEngine:
    """Combine embeddings with a surprise score heuristic."""

    def __init__(self, ttl_seconds: float = 3600) -> None:
        self.embeddings = EmbeddingManager()
        self.store = MilvusClient()
        self.ttl_seconds = ttl_seconds

    def _surprise(self, vector: List[float]) -> float:
        results = self.store.search(vector, top_k=1)
        if not results:
            return 1.0
        return 1.0 - results[0]["score"]

    def prune(self) -> None:
        cutoff = time.time() - self.ttl_seconds
        ids = [r["id"] for r in self.store._data if r["payload"].get("timestamp", 0) < cutoff]
        if ids:
            self.store.delete(ids)

    def ingest(self, text: str, metadata: Dict[str, Any] | None = None) -> int | None:
        metadata = metadata or {}
        metadata["timestamp"] = time.time()
        vector = self.embeddings.embed(text)
        if self._surprise(vector) < 0.1:
            return None
        self.prune()
        return self.store.upsert(vector, {"text": text, **metadata})

    def query(self, text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        vector = self.embeddings.embed(text)
        results = self.store.search(vector, top_k=top_k * 3)
        now = time.time()
        def recency_score(ts: float) -> float:
            age = now - ts
            return 1.0 / (1.0 + age / self.ttl_seconds)

        for r in results:
            ts = r["payload"].get("timestamp", now)
            r["score"] = 0.7 * r["score"] + 0.3 * recency_score(ts)
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:top_k]
