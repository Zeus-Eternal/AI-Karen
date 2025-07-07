"""
- Unified API for context recall and memory update
- Local-first: uses Milvus, Postgres, Redis (as available)
- Handles both short-term and long-term context
- Pluggable backend adapters for future-proofing
"""

from typing import Any, Dict, List, Optional
import os

# Import your memory backends
try:
    from ai_karen_engine.core.milvus_client import recall_vectors, store_vector
except ImportError:
    recall_vectors = store_vector = None

try:
    from ai_karen_engine.clients.database.postgres_client import PostgresClient
except Exception:  # pragma: no cover - optional dependency
    PostgresClient = None

try:
    import redis
except ImportError:
    redis = None

postgres = PostgresClient(use_sqlite=True) if PostgresClient else None

def recall_context(user_ctx: Dict[str, Any], query: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
    """
    Recall recent or most relevant context for the user/query.
    Tries Milvus with Postgres metadata first, then Redis, else returns None.
    """
    user_id = user_ctx.get("user_id") or "anonymous"
    results = None
    # 1. Milvus + Postgres metadata
    if recall_vectors:
        try:
            vec_results = recall_vectors(user_id, query, top_k=limit)
            if vec_results:
                results = []
                for r in vec_results:
                    meta = postgres.get_by_vector(r.get("id")) if postgres else None
                    results.append(meta or r)
                return results
        except Exception as ex:  # pragma: no cover - optional backend
            print(f"[MemoryManager] Milvus recall failed: {ex}")

    # 3. Redis
    if redis:
        try:
            r = redis.Redis()
            keys = r.lrange(f"kari:mem:{user_id}", 0, limit-1)
            return [eval(x.decode()) for x in keys]
        except Exception as ex:
            print(f"[MemoryManager] Redis recall failed: {ex}")

    return None

def update_memory(user_ctx: Dict[str, Any], query: str, result: Any) -> bool:
    """
    Store result/context in all available memory backends.
    Returns True if at least one write succeeded.
    """
    user_id = user_ctx.get("user_id") or "anonymous"
    entry = {
        "user_id": user_id,
        "query": query,
        "result": result,
        "timestamp": int(__import__("time").time())
    }
    ok = False

    # 1. Milvus
    vector_id = None
    if store_vector:
        try:
            vector_id = store_vector(user_id, query, result)
            ok = True
        except Exception as ex:
            print(f"[MemoryManager] Milvus store failed: {ex}")

    # 2. Postgres metadata store
    if postgres:
        try:
            postgres.upsert_memory(
                vector_id or -1,
                user_id,
                user_ctx.get("session_id"),
                query,
                result,
                entry["timestamp"],
            )
            ok = True
        except Exception as ex:  # pragma: no cover - optional backend
            print(f"[MemoryManager] Postgres store failed: {ex}")

    # 3. Redis
    if redis:
        try:
            r = redis.Redis()
            r.lpush(f"kari:mem:{user_id}", str(entry))
            ok = True
        except Exception as ex:
            print(f"[MemoryManager] Redis store failed: {ex}")

    return ok

__all__ = ["recall_context", "update_memory"]
