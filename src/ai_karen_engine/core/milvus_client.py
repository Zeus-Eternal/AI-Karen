"""Production-grade in-memory vector store simulating Milvus for Kari AI."""
from __future__ import annotations

import math
import os
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np  # type: ignore

from ai_karen_engine.core.embedding_manager import record_metric  # type: ignore

try:  # Optional approximate nearest neighbor backend
    import hnswlib  # type: ignore
except Exception:  # pragma: no cover - hnswlib may be missing at runtime
    hnswlib = None


# === IN-MEMORY VECTOR STORE CORE ===
@dataclass
class _Record:
    id: int
    vector: List[float]
    payload: Dict[str, Any]
    norm: float
    timestamp: float


class MilvusClient:
    """Thread-safe vector database with optional ANN index and result caching."""

    def __init__(
        self,
        dim: Optional[int] = None,
        ttl_seconds: Optional[float] = None,
        *,
        index_type: str = os.getenv("KARI_MILVUS_INDEX", "flat"),
        cache_size: int = int(os.getenv("KARI_MILVUS_CACHE_SIZE", "0")),
    ) -> None:
        self.dim = dim
        self.ttl_seconds = ttl_seconds
        self.index_type = index_type
        self.cache_size = cache_size
        self._data: Dict[int, _Record] = {}
        self._id = 0
        self._lock = threading.Lock()
        self._connected = True
        self._index: Optional["hnswlib.Index"] = None
        self._cache: Optional[OrderedDict[Tuple[Any, Any], List[Dict[str, Any]]]] = (
            OrderedDict() if cache_size > 0 else None
        )

    def pool_utilization(self) -> float:
        return 0.0

    async def connect(self) -> None:
        """Async connection hook for API compatibility."""
        self._connected = True

    async def disconnect(self) -> None:
        """Async disconnect hook clearing all state."""
        self._connected = False
        # No real connection so nothing to close.

    async def health_check(self) -> Dict[str, str]:
        """Return simple health information."""
        status = "healthy" if self._connected else "disconnected"
        return {"status": status, "records": str(len(self._data))}

    def _prune(self) -> None:
        if self.ttl_seconds is None:
            return
        cutoff = time.time() - self.ttl_seconds
        expired = [rid for rid, rec in self._data.items() if rec.timestamp < cutoff]
        for rid in expired:
            del self._data[rid]
            if self.index_type == "hnsw" and self._index is not None:
                try:
                    self._index.mark_deleted(rid)
                except Exception:
                    pass
        if self._cache is not None and expired:
            self._cache.clear()

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
            self._data[self._id] = _Record(
                self._id, list(vector), payload, norm, time.time()
            )
            if self.index_type == "hnsw":
                if hnswlib is None:
                    raise ImportError("hnswlib is required for hnsw index")
                if self._index is None:
                    self._index = hnswlib.Index(space="cosine", dim=self.dim)
                    self._index.init_index(
                        max_elements=100_000, ef_construction=200, M=16
                    )
                    self._index.set_ef(50)
                self._index.add_items(
                    np.array([vector], dtype=np.float32), ids=np.array([self._id])
                )
            if self._cache is not None:
                self._cache.clear()
        record_metric("vector_upsert_seconds", time.time() - start)
        return self._id

    def delete_sync(self, ids: Iterable[int]) -> None:
        start = time.time()
        with self._lock:
            for rid in list(ids):
                self._data.pop(int(rid), None)
                if self.index_type == "hnsw" and self._index is not None:
                    try:
                        self._index.mark_deleted(int(rid))
                    except Exception:
                        pass
            if self._cache is not None:
                self._cache.clear()
        record_metric("vector_delete_seconds", time.time() - start)

    async def delete(
        self,
        collection_name: Optional[str] = None,
        ids: Optional[Iterable[int]] = None,
        filter_expr: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Async delete wrapper compatible with memory manager."""
        if ids is None and filter_expr:
            key = filter_expr.split("==")[-1].strip().strip("'")
            ids = [
                rid
                for rid, rec in self._data.items()
                if rec.payload.get("memory_id") == key
            ]

        if ids:
            self.delete_sync(ids)

    @staticmethod
    def _similarity(
        v1: List[float], norm1: float, v2: List[float], norm2: float
    ) -> float:
        if norm1 == 0 or norm2 == 0:
            return 0.0
        dot = sum(x * y for x, y in zip(v1, v2))
        return dot / (norm1 * norm2)

    def search_sync(
        self,
        vector: List[float],
        top_k: int = 3,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Synchronous search with optional ANN index and result caching."""
        cache_key: Optional[Tuple[Any, Any]] = None
        if self._cache is not None:
            meta_key = (
                tuple(sorted(metadata_filter.items())) if metadata_filter else None
            )
            cache_key = (tuple(vector), meta_key)
            if cache_key in self._cache:
                return list(self._cache[cache_key])

        start = time.time()
        status = "success"
        try:
            with self._lock:
                self._prune()
                norm = math.sqrt(sum(v * v for v in vector))
                results: List[Dict[str, Any]] = []
                if self.index_type == "hnsw" and self._index is not None:
                    search_k = min(top_k * 5, max(len(self._data), top_k)) or top_k
                    labels, distances = self._index.knn_query(
                        np.array([vector], dtype=np.float32), k=search_k
                    )
                    for label, dist in zip(labels[0], distances[0]):
                        rec = self._data.get(int(label))
                        if rec is None:
                            continue
                        if metadata_filter and any(
                            rec.payload.get(k) != v for k, v in metadata_filter.items()
                        ):
                            continue
                        sim = 1.0 - float(dist)
                        results.append(
                            {"id": rec.id, "score": sim, "payload": rec.payload}
                        )
                else:
                    for rec in self._data.values():
                        if metadata_filter and any(
                            rec.payload.get(k) != v for k, v in metadata_filter.items()
                        ):
                            continue
                        sim = self._similarity(vector, norm, rec.vector, rec.norm)
                        results.append(
                            {"id": rec.id, "score": sim, "payload": rec.payload}
                        )
                results.sort(key=lambda r: r["score"], reverse=True)
                results = results[:top_k]

            if self._cache is not None and cache_key is not None:
                self._cache[cache_key] = results
                if len(self._cache) > self.cache_size:
                    self._cache.popitem(last=False)
            return results
        except Exception:
            status = "error"
            raise
        finally:
            duration = time.time() - start
            record_metric("vector_search_latency_seconds", duration)
            try:
                from ai_karen_engine.services.metrics_service import get_metrics_service

                get_metrics_service().record_vector_latency(duration, status=status)
            except Exception:
                pass

    async def search(
        self,
        vector: Optional[List[float]] = None,
        top_k: int = 3,
        metadata_filter: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None,
        query_vectors: Optional[List[List[float]]] = None,
        **kwargs: Any,
    ) -> List[List[Dict[str, Any]]]:
        """Async search for similar vectors with memory manager compatible format."""
        # Handle different calling conventions
        if query_vectors and len(query_vectors) > 0:
            vector = query_vectors[0]  # Use first query vector

        if vector is None:
            return [[]]  # Return nested list format expected by memory manager

        # Call the synchronous implementation
        raw_results = self.search_sync(vector, top_k, metadata_filter)

        # Convert to memory manager expected format
        formatted_results = []
        for result in raw_results:
            # Create mock result object with expected attributes
            mock_result = type(
                "MockResult",
                (),
                {
                    "distance": result["score"],
                    "entity": {"memory_id": str(result["id"])},
                },
            )()
            formatted_results.append(mock_result)

        # Return as nested list (first query results)
        return [formatted_results]

    async def insert(
        self,
        collection_name: Optional[str] = None,
        vectors: Optional[List[List[float]]] = None,
        metadata: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Optional[str]:
        """Async wrapper for upsert operations to maintain contract compatibility."""
        try:
            if vectors and len(vectors) > 0 and metadata and len(metadata) > 0:
                # Use the first vector and metadata
                vector = vectors[0]
                payload = metadata[0]
                record_id = self.upsert(vector, payload)
                return str(record_id)
            return None
        except Exception as e:
            raise Exception(f"Milvus insert failed: {e}")


# === KARI AI ADAPTERS: PLUG FOR MEMORY MANAGER ===
# ⚡ This is what you import elsewhere!
_vector_stores: Dict[str, MilvusClient] = {}


def _get_store(tenant_id: str) -> MilvusClient:
    if tenant_id not in _vector_stores:
        _vector_stores[tenant_id] = MilvusClient()
    return _vector_stores[tenant_id]


def store_vector(
    user_id: str, query: str, result: Any, tenant_id: Optional[str] = None
) -> int:
    """
    Store a query/result in the vector DB using the embedding as vector.
    For demo: simulate with dummy embedding. Replace with real embedder.
    """
    try:
        from ai_karen_engine.core.embedding_manager import embed_text

        vec = embed_text(query)
    except Exception:
        vec = [float(len(query))]
    tenant = tenant_id or "default"
    store = _get_store(tenant)
    payload = {
        "tenant_id": tenant,
        "user_id": user_id,
        "query": query,
        "result": result,
        "timestamp": int(time.time()),
    }
    return store.upsert(vec, payload)


def recall_vectors(
    user_id: str, query: str, top_k: int = 5, tenant_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve most relevant memory/context for user/query using vector search.
    """
    try:
        from ai_karen_engine.core.embedding_manager import embed_text

        vec = embed_text(query)
    except Exception:
        vec = [float(len(query))]
    tenant = tenant_id or "default"
    store = _get_store(tenant)
    metadata = {"user_id": user_id, "tenant_id": tenant}
    results = store.search_sync(vec, top_k=top_k, metadata_filter=metadata)
    record_metric(
        "milvus_pool_utilization", getattr(store, "pool_utilization", lambda: 0.0)()
    )
    # Include vector id so external stores can reference metadata
    return [{"id": r["id"], **r["payload"]} for r in results]


__all__ = ["store_vector", "recall_vectors", "MilvusClient"]
