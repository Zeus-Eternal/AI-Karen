"""
Unified MemoryManager: context recall and update
- Local-first: Elastic, Milvus, Postgres, Redis, DuckDB
- Handles short/long-term, hot-pluggable
- All ops logged/audited for observability
"""

from typing import Any, Dict, List, Optional
import os
import time
import logging
import json

# ========== Backend Imports ==========
try:
    from ai_karen_engine.clients.database.milvus_client import (
        recall_vectors,
        store_vector,
    )
except ImportError:
    recall_vectors = store_vector = None

try:
    from ai_karen_engine.clients.database.postgres_client import PostgresClient
except Exception:
    PostgresClient = None

try:
    import redis
except ImportError:
    redis = None

try:
    import duckdb
except ImportError:
    duckdb = None

try:
    from ai_karen_engine.clients.database.elastic_client import ElasticClient
except Exception:
    ElasticClient = None

# ========== Logging ==========
logger = logging.getLogger("kari.memory.manager")
logger.setLevel(logging.INFO)

# ========== Backend Init ==========
postgres = PostgresClient(use_sqlite=True) if PostgresClient else None


def recall_context(
    user_ctx: Dict[str, Any], query: str, limit: int = 10
) -> Optional[List[Dict[str, Any]]]:
    """
    Recall the most relevant context for user/query from the memory stack.
    Priority: Elastic > Milvus > Postgres > Redis > DuckDB
    """
    user_id = user_ctx.get("user_id") or "anonymous"

    # ==== 1. ElasticSearch (optional, semantic/keyword) ====
    if ElasticClient:
        try:
            es_host = os.getenv("ELASTIC_HOST", "localhost")
            es_port = int(os.getenv("ELASTIC_PORT", "9200"))
            es_index = os.getenv("ELASTIC_INDEX", "kari_memory")
            es_user = os.getenv("ELASTIC_USER")
            es_password = os.getenv("ELASTIC_PASSWORD")
            es = ElasticClient(es_host, es_port, es_index, es_user, es_password)
            records = es.search(user_id, query, limit=limit)
            if records:
                logger.info(
                    f"[MemoryManager] Elastic recall: {len(records)} results for user {user_id}"
                )
                return records
        except Exception as ex:
            logger.warning(f"[MemoryManager] Elastic recall failed: {ex}")

    # ==== 2. Milvus ====
    if recall_vectors:
        try:
            vec_results = recall_vectors(user_id, query, top_k=limit)
            records = []
            for r in vec_results:
                meta = postgres.get_by_vector(r.get("id")) if postgres else None
                records.append(meta or r)
            if records:
                logger.info(
                    f"[MemoryManager] Milvus recall: {len(records)} results for user {user_id}"
                )
                return records
        except Exception as ex:
            logger.warning(f"[MemoryManager] Milvus recall failed: {ex}")

    # ==== 2. Postgres ====
    if postgres:
        try:
            db_results = postgres.recall_memory(
                user_id=user_id, query=query, limit=limit
            )
            if db_results:
                logger.info(
                    f"[MemoryManager] Postgres recall: {len(db_results)} results for user {user_id}"
                )
                return db_results
        except Exception as ex:
            logger.warning(f"[MemoryManager] Postgres recall failed: {ex}")

    # ==== 3. Redis ====
    if redis:
        try:
            r = redis.Redis()
            raw = r.lrange(f"kari:mem:{user_id}", 0, limit - 1)
            records = []
            for b in raw:
                try:
                    records.append(json.loads(b.decode()))
                except Exception as jex:
                    logger.warning(f"[MemoryManager] Redis decode error: {jex}")
            if records:
                logger.info(
                    f"[MemoryManager] Redis recall: {len(records)} results for user {user_id}"
                )
                return records
        except Exception as ex:
            logger.warning(f"[MemoryManager] Redis recall failed: {ex}")

    # ==== 4. DuckDB (optional, local OLAP) ====
    if duckdb:
        try:
            db_path = os.getenv("DUCKDB_PATH", "kari_mem.duckdb")
            con = duckdb.connect(db_path, read_only=True)
            query_sql = """
                SELECT * FROM memory 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """
            res = con.execute(query_sql, [user_id, limit]).fetchdf()
            records = res.to_dict("records")
            if records:
                logger.info(
                    f"[MemoryManager] DuckDB recall: {len(records)} results for user {user_id}"
                )
                return records
        except Exception as ex:
            logger.warning(f"[MemoryManager] DuckDB recall failed: {ex}")

    logger.info(
        f"[MemoryManager] No recall results for user {user_id} (all backends empty)"
    )
    return None


def update_memory(user_ctx: Dict[str, Any], query: str, result: Any) -> bool:
    """
    Store context/result to all available memory backends.
    Returns True if at least one backend succeeds.
    """
    user_id = user_ctx.get("user_id") or "anonymous"
    session_id = user_ctx.get("session_id")
    entry = {
        "user_id": user_id,
        "session_id": session_id,
        "query": query,
        "result": result,
        "timestamp": int(time.time()),
    }
    ok = False
    vector_id = None

    # ==== 1. Milvus ====
    if store_vector:
        try:
            vector_id = store_vector(user_id, query, result)
            ok = True
            logger.info(f"[MemoryManager] Milvus stored vector for user {user_id}")
        except Exception as ex:
            logger.warning(f"[MemoryManager] Milvus store failed: {ex}")

    # ==== 2. Postgres ====
    if postgres:
        try:
            postgres.upsert_memory(
                vector_id or -1,
                user_id,
                session_id,
                query,
                result,
                entry["timestamp"],
            )
            ok = True
            logger.info(f"[MemoryManager] Postgres upserted memory for user {user_id}")
        except Exception as ex:
            logger.warning(f"[MemoryManager] Postgres store failed: {ex}")

    # ==== 3. Redis ====
    if redis:
        try:
            r = redis.Redis()
            r.lpush(f"kari:mem:{user_id}", json.dumps(entry))
            ok = True
            logger.info(f"[MemoryManager] Redis pushed memory for user {user_id}")
        except Exception as ex:
            logger.warning(f"[MemoryManager] Redis store failed: {ex}")

    # ==== 4. DuckDB (optional, local OLAP) ====
    if duckdb:
        try:
            db_path = os.getenv("DUCKDB_PATH", "kari_mem.duckdb")
            con = duckdb.connect(db_path, read_only=False)
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    user_id VARCHAR,
                    session_id VARCHAR,
                    query VARCHAR,
                    result VARCHAR,
                    timestamp BIGINT
                )
            """
            )
            con.execute(
                "INSERT INTO memory (user_id, session_id, query, result, timestamp) VALUES (?, ?, ?, ?, ?)",
                [user_id, session_id, query, json.dumps(result), entry["timestamp"]],
            )
            ok = True
            logger.info(f"[MemoryManager] DuckDB stored memory for user {user_id}")
        except Exception as ex:
            logger.warning(f"[MemoryManager] DuckDB store failed: {ex}")

    # ==== 5. ElasticSearch (optional, document index) ====
    if ElasticClient:
        try:
            es_host = os.getenv("ELASTIC_HOST", "localhost")
            es_port = int(os.getenv("ELASTIC_PORT", "9200"))
            es_index = os.getenv("ELASTIC_INDEX", "kari_memory")
            es_user = os.getenv("ELASTIC_USER")
            es_password = os.getenv("ELASTIC_PASSWORD")
            es = ElasticClient(es_host, es_port, es_index, es_user, es_password)
            es.index_entry(entry)
            ok = True
            logger.info(f"[MemoryManager] Elastic indexed memory for user {user_id}")
        except Exception as ex:
            logger.warning(f"[MemoryManager] Elastic store failed: {ex}")

    if not ok:
        logger.error(
            f"[MemoryManager] FAILED to store memory for user {user_id} on all backends"
        )
    return ok


__all__ = ["recall_context", "update_memory"]
