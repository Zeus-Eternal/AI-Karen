"""
Kari AI Memory Manager (CORTEX)
- Unified API for context recall and memory update
- Local-first: uses Milvus, DuckDB, Redis (as available)
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
    import duckdb
except ImportError:
    duckdb = None

try:
    import psycopg
except ImportError:
    psycopg = None

try:
    import redis
except ImportError:
    redis = None

def recall_context(user_ctx: Dict[str, Any], query: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
    """
    Recall recent or most relevant context for the user/query.
    Tries Milvus first, then Postgres, then DuckDB, then Redis.
    """
    user_id = user_ctx.get("user_id") or "anonymous"
    # 1. Milvus
    if recall_vectors:
        try:
            results = recall_vectors(user_id, query, top_k=limit)
            if results:
                return results
        except Exception as ex:
            print(f"[MemoryManager] Milvus recall failed: {ex}")

    # 2. Postgres
    if psycopg:
        try:
            with psycopg.connect(
                dbname=os.getenv("POSTGRES_DB", "postgres"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres"),
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT user_id, query, result, timestamp FROM memory WHERE user_id=%s ORDER BY timestamp DESC LIMIT %s",
                        (user_id, limit),
                    )
                    rows = cur.fetchall()
            return [
                {"user_id": uid, "query": q, "result": r, "timestamp": ts}
                for uid, q, r, ts in rows
            ]
        except Exception as ex:
            print(f"[MemoryManager] Postgres recall failed: {ex}")

    # 3. DuckDB
    if duckdb:
        try:
            db_path = os.getenv("DUCKDB_PATH", "kari_mem.duckdb")
            con = duckdb.connect(db_path, read_only=True)
            query_sql = "SELECT * FROM memory WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?"
            res = con.execute(query_sql, [user_id, limit]).fetchdf()
            return res.to_dict("records")
        except Exception as ex:
            print(f"[MemoryManager] DuckDB recall failed: {ex}")

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
    if store_vector:
        try:
            store_vector(user_id, query, result)
            ok = True
        except Exception as ex:
            print(f"[MemoryManager] Milvus store failed: {ex}")

    # 2. Postgres
    if psycopg:
        try:
            with psycopg.connect(
                dbname=os.getenv("POSTGRES_DB", "postgres"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres"),
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "CREATE TABLE IF NOT EXISTS memory (user_id VARCHAR, query VARCHAR, result TEXT, timestamp BIGINT)"
                    )
                    cur.execute(
                        "INSERT INTO memory (user_id, query, result, timestamp) VALUES (%s, %s, %s, %s)",
                        (user_id, query, str(result), entry["timestamp"]),
                    )
                    conn.commit()
            ok = True
        except Exception as ex:
            print(f"[MemoryManager] Postgres store failed: {ex}")

    # 3. DuckDB
    if duckdb:
        try:
            db_path = os.getenv("DUCKDB_PATH", "kari_mem.duckdb")
            con = duckdb.connect(db_path)
            con.execute(
                "CREATE TABLE IF NOT EXISTS memory (user_id VARCHAR, query VARCHAR, result VARCHAR, timestamp BIGINT)"
            )
            con.execute(
                "INSERT INTO memory VALUES (?, ?, ?, ?)",
                [user_id, query, str(result), entry["timestamp"]],
            )
            ok = True
        except Exception as ex:
            print(f"[MemoryManager] DuckDB store failed: {ex}")

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
