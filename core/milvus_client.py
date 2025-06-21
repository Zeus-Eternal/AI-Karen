"""Production-grade in-memory vector store simulating Milvus."""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from .embedding_manager import record_metric


@dataclass
class _Record:
    id: int
    vector: List[float]
    payload: Dict[str, Any]
    norm: float
    timestamp: float


class MilvusClient:
    """Thread-safe vector database with TTL and metadata filtering."""

    def __init__(self, dim: Optional[int] = None, ttl_seconds: Optional[float] = None) -> None:
        self.dim = dim
        self.ttl_seconds = ttl_seconds
        self._data: Dict[int, _Record] = {}
        self._id = 0
        self._lock = threading.Lock()

    def _prune(self) -> None:
        if self.ttl_seconds is None:
            return
        cutoff = time.time() - self.ttl_seconds
        expired = [rid for rid, rec in self._data.items() if rec.timestamp < cutoff]
        for rid in expired:
            del self._data[rid]

    def upsert(self, vector: List[float], payload: Dict[str, Any]) -> int:
        start = time.time()
        with self._lock:
            if self.dim is None:
                self.dim = len(vector)
            if len(vector) != self.dim:
                raise ValueError("Vector dimension mismatch")
            self._prune()
            self._id += 1
            norm = math.sqrt(sum(v * v for v in vector))
            self._data[self._id] = _Record(self._id, list(vector), payload, norm, time.time())
        record_metric("vector_upsert_seconds", time.time() - start)
        return self._id

    def delete(self, ids: Iterable[int]) -> None:
        start = time.time()
        with self._lock:
            for rid in list(ids):
                self._data.pop(rid, None)
        record_metric("vector_delete_seconds", time.time() - start)

    @staticmethod
    def _similarity(v1: List[float], norm1: float, v2: List[float], norm2: float) -> float:
        if norm1 == 0 or norm2 == 0:
            return 0.0
        dot = sum(x * y for x, y in zip(v1, v2))
        return dot / (norm1 * norm2)

    def search(
        self, vector: List[float], top_k: int = 3, metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        start = time.time()
        with self._lock:
            self._prune()
            norm = math.sqrt(sum(v * v for v in vector))
            results = []
            for rec in self._data.values():
                if metadata_filter and any(rec.payload.get(k) != v for k, v in metadata_filter.items()):
                    continue
                sim = self._similarity(vector, norm, rec.vector, rec.norm)
                results.append({"id": rec.id, "score": sim, "payload": rec.payload})
            results.sort(key=lambda r: r["score"], reverse=True)
        record_metric("vector_search_latency_seconds", time.time() - start)
        return results[:top_k]
