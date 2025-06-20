"""In-memory vector store simulating Milvus operations."""

from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional

from .embedding_manager import record_metric


class MilvusClient:
    """Very small in-memory vector database."""

    def __init__(self) -> None:
        self._data: List[Dict[str, Any]] = []
        self._id = 0

    def upsert(self, vector: List[float], payload: Dict[str, Any]) -> int:
        start = time.time()
        self._id += 1
        self._data.append({"id": self._id, "vector": vector, "payload": payload})
        record_metric("vector_upsert_seconds", time.time() - start)
        return self._id

    def delete(self, ids: List[int]) -> None:
        """Delete records by ID."""
        start = time.time()
        self._data = [r for r in self._data if r["id"] not in ids]
        record_metric("vector_delete_seconds", time.time() - start)

    @staticmethod
    def _similarity(v1: List[float], v2: List[float]) -> float:
        dot = sum(x * y for x, y in zip(v1, v2))
        norm1 = math.sqrt(sum(x * x for x in v1))
        norm2 = math.sqrt(sum(x * x for x in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def search(
        self, vector: List[float], top_k: int = 3, metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        start = time.time()
        results = []
        for record in self._data:
            if metadata_filter:
                if any(record["payload"].get(k) != v for k, v in metadata_filter.items()):
                    continue
            sim = self._similarity(vector, record["vector"])
            results.append({"id": record["id"], "score": sim, "payload": record["payload"]})
        results.sort(key=lambda r: r["score"], reverse=True)
        record_metric("vector_search_latency_seconds", time.time() - start)
        return results[:top_k]
