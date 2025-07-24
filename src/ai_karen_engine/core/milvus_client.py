"""Production-grade in-memory vector store simulating Milvus for Kari AI."""
from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from ai_karen_engine.core.embedding_manager import record_metric

# === IN-MEMORY VECTOR STORE CORE ===
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

    def search_sync(
        self, vector: List[float], top_k: int = 3, metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Synchronous search method (original implementation)."""
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
    
    async def search(
        self, vector: Optional[List[float]] = None, top_k: int = 3, metadata_filter: Optional[Dict[str, Any]] = None, 
        collection_name: Optional[str] = None, query_vectors: Optional[List[List[float]]] = None, **kwargs
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
            mock_result = type('MockResult', (), {
                'distance': result['score'],
                'entity': {'memory_id': str(result['id'])}
            })()
            formatted_results.append(mock_result)
        
        # Return as nested list (first query results)
        return [formatted_results]
    
    async def insert(self, collection_name: Optional[str] = None, vectors: Optional[List[List[float]]] = None, 
                    metadata: Optional[List[Dict[str, Any]]] = None, **kwargs) -> str:
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
    from ai_karen_engine.core.embedding_manager import embed_text
    vec = embed_text(query)
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
    from ai_karen_engine.core.embedding_manager import embed_text
    vec = embed_text(query)
    tenant = tenant_id or "default"
    store = _get_store(tenant)
    metadata = {"user_id": user_id, "tenant_id": tenant}
    results = store.search(vec, top_k=top_k, metadata_filter=metadata)
    # Include vector id so external stores can reference metadata
    return [{"id": r["id"], **r["payload"]} for r in results]

__all__ = ["store_vector", "recall_vectors", "MilvusClient"]
