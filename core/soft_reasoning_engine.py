"""Recency-aware reasoning engine with automated TTL pruning."""

from __future__ import annotations

 
import asyncio
import math
import time
from typing import Any, Dict, List, Optional

import time
from typing import Any, Dict, List
 

from .embedding_manager import EmbeddingManager
from .milvus_client import MilvusClient


class SoftReasoningEngine:
    """Combine embeddings with a surprise score heuristic."""

 
    def __init__(self, ttl_seconds: float = 3600, recency_alpha: float = 0.7) -> None:
        self.embeddings = EmbeddingManager()
        self.store = MilvusClient(ttl_seconds=ttl_seconds)
        self.ttl_seconds = ttl_seconds
        self.recency_alpha = recency_alpha

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
 
        ids = []
        for rid, rec in list(self.store._data.items()):
            ts = rec.payload.get("timestamp", rec.timestamp)
            ttl = rec.payload.get("ttl_override", self.ttl_seconds)
            if time.time() - ts > ttl:
                ids.append(rid)
        if ids:
            self.store.delete(ids)

    def ingest(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        *,
        ttl_seconds: Optional[float] = None,
    ) -> int | None:
        metadata = dict(metadata or {})
        metadata.setdefault("timestamp", time.time())
        if ttl_seconds is not None:
            metadata["ttl_override"] = ttl_seconds

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

    def query(
        self,
        text: str,
        *,
        top_k: int = 3,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        vector = self.embeddings.embed(text)
 scxyql-codex/implement-self-refactor-engine-workflow
        results = self.store.search(
            vector, top_k=top_k * 5, metadata_filter=metadata_filter
        )
        now = time.time()

        for r in results:
            ts = r["payload"].get("timestamp", now)
            recency = math.exp(-(now - ts) / self.ttl_seconds)
            r["score"] = self.recency_alpha * r["score"] + (1 - self.recency_alpha) * recency

        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:top_k]

    async def aquery(
        self,
        text: str,
        *,
        top_k: int = 3,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(
            self.query, text, top_k=top_k, metadata_filter=metadata_filter
        )

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
 
