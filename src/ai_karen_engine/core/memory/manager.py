"""
Unified MemoryManager: context recall and update
- Local-first: Elastic, Milvus, Postgres, Redis, DuckDB (hybrid)
- Handles short/long-term, hot-pluggable
- All ops logged/audited for observability
"""

from typing import Any, Dict, List, Optional
import os
import time
import logging
import json
import threading

from ai_karen_engine.core.neuro_vault import NeuroVault

# ========== Logging ==========
logger = logging.getLogger("kari.memory.manager")
logger.setLevel(logging.INFO)

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
    from ai_karen_engine.clients.database.duckdb_client import DuckDBClient
except Exception:
    DuckDBClient = None

try:
    from ai_karen_engine.clients.database.elastic_client import ElasticClient
except Exception:
    ElasticClient = None

try:
    import redis
except ImportError:
    redis = None

REDIS_URL = os.getenv("REDIS_URL")

redis_client = None
if redis and REDIS_URL:
    try:
        redis_client = redis.Redis.from_url(REDIS_URL)
        redis_client.ping()
    except Exception as ex:  # pragma: no cover - network may be down
        logger.warning(f"[MemoryManager] Redis connection failed: {ex}")
        redis_client = None

try:
    import duckdb
except ImportError:
    duckdb = None

# ========== Metrics ==========
_METRICS: Dict[str, int] = {
    "memory_store_total": 0,
    "memory_recall_total": 0,
}


def get_metrics() -> Dict[str, int]:
    """Return a copy of the current memory metrics."""
    return dict(_METRICS)

try:
    from prometheus_client import Counter
    from ai_karen_engine.integrations.llm_utils import PROM_REGISTRY

    MEM_STORE_COUNT = Counter(
        "memory_store_total",
        "Total memory store operations",
        registry=PROM_REGISTRY,
    )
    MEM_RECALL_COUNT = Counter(
        "memory_recall_total",
        "Total memory recall operations",
        registry=PROM_REGISTRY,
    )
except Exception:  # pragma: no cover - optional dependency
    class _DummyCounter:
        def inc(self, amount: int = 1) -> None:
            pass

    MEM_STORE_COUNT = MEM_RECALL_COUNT = _DummyCounter()

def _inc(name: str, amount: int = 1) -> None:
    _METRICS[name] = _METRICS.get(name, 0) + amount

# ========== Backend Init ==========
postgres = PostgresClient(use_sqlite=True) if PostgresClient else None
duckdb_path = os.getenv("DUCKDB_PATH", "kari_mem.duckdb")
pg_syncer: "PostgresSyncer | None" = None

# ---- Postgres Hybrid Flush Logic ----
class PostgresSyncer:
    """Background checker and DuckDB flusher for Postgres connectivity."""

    def __init__(self, client: PostgresClient, db_path: str, interval: float = 5.0) -> None:
        self.client = client
        self.db_path = db_path
        self.interval = interval
        self.postgres_available = client.health() if client else False
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    def start(self) -> None:
        if not self.client:
            return
        with self._lock:
            if self._timer is None:
                self._timer = threading.Timer(self.interval, self._loop)
                self._timer.daemon = True
                self._timer.start()

    def _loop(self) -> None:
        with self._lock:
            self._timer = None
        self.run_once()
        self.start()

    def run_once(self) -> None:
        if not self.client:
            return
        healthy = False
        try:
            healthy = self.client.health()
        except Exception as ex:
            logger.warning(f"[MemoryManager] Postgres health check failed: {ex}")
        if healthy:
            if not self.postgres_available:
                logger.info("[MemoryManager] Postgres reconnected; flushing backlog")
                self.postgres_available = True
                flush_duckdb_to_postgres(self.client, self.db_path)
        else:
            if self.postgres_available:
                logger.warning("[MemoryManager] Postgres connection lost")
            self.postgres_available = False

    def mark_unavailable(self) -> None:
        self.postgres_available = False

    def stop(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None

def flush_duckdb_to_postgres(client: PostgresClient, db_path: str) -> None:
    """Flush unsynced DuckDB entries into Postgres."""
    if not (client and duckdb):
        return
    try:
        con = duckdb.connect(db_path, read_only=False)
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS memory (
                tenant_id VARCHAR,
                user_id VARCHAR,
                session_id VARCHAR,
                query VARCHAR,
                result VARCHAR,
                timestamp BIGINT,
                synced BOOLEAN DEFAULT TRUE
            )
            """
        )
        rows = con.execute(
            "SELECT rowid, tenant_id, user_id, session_id, query, result, timestamp FROM memory WHERE synced=FALSE"
        ).fetchall()
        for rowid, tenant_id, user_id, session_id, query, result, ts in rows:
            try:
                client.upsert_memory(
                    -1,
                    tenant_id or "",
                    user_id,
                    session_id,
                    query,
                    result,
                    ts,
                )
                con.execute("UPDATE memory SET synced=TRUE WHERE rowid=?", [rowid])
                logger.info(f"[MemoryManager] Flushed record {rowid} to Postgres")
            except Exception as ex:
                logger.warning(f"[MemoryManager] Flush failed for record {rowid}: {ex}")
                break
    except Exception as ex:
        logger.warning(f"[MemoryManager] DuckDB flush error: {ex}")


def init_memory() -> None:
    """Initialize memory backends and start background syncer."""
    global pg_syncer
    if postgres and pg_syncer is None:
        pg_syncer = PostgresSyncer(postgres, duckdb_path)
        pg_syncer.start()

# NeuroVault vector index
neuro_vault = NeuroVault()

# ====== Context Recall ======
def recall_context(
    user_ctx: Dict[str, Any], query: str, limit: int = 10, tenant_id: Optional[str] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Recall the most relevant context for user/query from the memory stack.
    Priority: NeuroVault > Elastic > Milvus > Postgres > Redis > DuckDB
    """
    _inc("memory_recall_total")
    MEM_RECALL_COUNT.inc()
    tenant_id = tenant_id or user_ctx.get("tenant_id")
    user_id = user_ctx.get("user_id") or "anonymous"

    # 0. NeuroVault vector recall
    try:
        records = neuro_vault.query(user_id, query, top_k=limit)
        if records:
            logger.info(
                f"[MemoryManager] NeuroVault recall: {len(records)} results for user {user_id}"
            )
            return records
    except Exception as ex:
        logger.warning(f"[MemoryManager] NeuroVault recall failed: {ex}")

    # 1. ElasticSearch (optional, semantic/keyword)
    if ElasticClient:
        try:
            es_host = os.getenv("ELASTIC_HOST", "localhost")
            es_port = int(os.getenv("ELASTIC_PORT", "9200"))
            es_index = os.getenv("ELASTIC_INDEX", "kari_memory")
            es_user = os.getenv("ELASTIC_USER")
            es_password = os.getenv("ELASTIC_PASSWORD")
            es = ElasticClient(es_host, es_port, es_index, es_user, es_password)
            records = es.search(user_id, query, limit=limit, tenant_id=tenant_id or "")
            if records:
                logger.info(
                    f"[MemoryManager] Elastic recall: {len(records)} results for user {user_id}"
                )
                return records
        except Exception as ex:
            logger.warning(f"[MemoryManager] Elastic recall failed: {ex}")

    # 2. Milvus
    if recall_vectors:
        try:
            vec_results = recall_vectors(user_id, query, top_k=limit, tenant_id=tenant_id)
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

    # 3. Postgres
    if postgres and pg_syncer and pg_syncer.postgres_available:
        try:
            db_results = postgres.recall_memory(
                user_id=user_id, query=query, limit=limit, tenant_id=tenant_id
            )
            if db_results:
                logger.info(
                    f"[MemoryManager] Postgres recall: {len(db_results)} results for user {user_id}"
                )
                return db_results
        except Exception as ex:
            logger.warning(f"[MemoryManager] Postgres recall failed: {ex}")

    # 4. Redis
    if redis_client:
        try:
            r = redis_client
            key = f"kari:mem:{tenant_id}:{user_id}" if tenant_id else f"kari:mem:{user_id}"
            raw = r.lrange(key, 0, limit - 1)
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

    # 5. DuckDB (local OLAP/fallback)
    if duckdb:
        try:
            con = duckdb.connect(duckdb_path, read_only=True)
            query_sql = """
                SELECT * FROM memory
                WHERE user_id = ?
                """
            if tenant_id:
                query_sql += " AND tenant_id = ?"
            query_sql += """
                ORDER BY timestamp DESC
                LIMIT ?
            """
            params = [user_id]
            if tenant_id:
                params.append(tenant_id)
            params.append(limit)
            res = con.execute(query_sql, params).fetchdf()
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

# ====== Context Write ======
def update_memory(
    user_ctx: Dict[str, Any], query: str, result: Any, tenant_id: Optional[str] = None
) -> bool:
    """
    Store context/result to all available memory backends.
    Returns True if at least one backend succeeds.
    """
    _inc("memory_store_total")
    MEM_STORE_COUNT.inc()
    tenant_id = tenant_id or user_ctx.get("tenant_id")
    user_id = user_ctx.get("user_id") or "anonymous"
    session_id = user_ctx.get("session_id")
    entry = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "session_id": session_id,
        "query": query,
        "result": result,
        "timestamp": int(time.time()),
    }
    ok = False
    vector_id = None
    postgres_ok = False

    # 0. NeuroVault index
    try:
        neuro_vault.index_text(user_id, query, {"result": result})
    except Exception as ex:
        logger.warning(f"[MemoryManager] NeuroVault index failed: {ex}")

    # 1. Milvus
    if store_vector:
        try:
            vector_id = store_vector(user_id, query, result, tenant_id=tenant_id)
            ok = True
            logger.info(f"[MemoryManager] Milvus stored vector for user {user_id}")
        except Exception as ex:
            logger.warning(f"[MemoryManager] Milvus store failed: {ex}")

    # 2. Postgres (if available, else buffer in DuckDB)
    if postgres and pg_syncer and pg_syncer.postgres_available:
        try:
            postgres.upsert_memory(
                vector_id or -1,
                tenant_id or "",
                user_id,
                session_id,
                query,
                result,
                entry["timestamp"],
            )
            postgres_ok = True
            ok = True
            logger.info(f"[MemoryManager] Postgres upserted memory for user {user_id}")
        except Exception as ex:
            pg_syncer.mark_unavailable()
            logger.warning(f"[MemoryManager] Postgres store failed: {ex}")

    # 3. Redis
    if redis_client:
        try:
            r = redis_client
            key = f"kari:mem:{tenant_id}:{user_id}" if tenant_id else f"kari:mem:{user_id}"
            r.lpush(key, json.dumps(entry))
            ok = True
            logger.info(f"[MemoryManager] Redis pushed memory for user {user_id}")
        except Exception as ex:
            logger.warning(f"[MemoryManager] Redis store failed: {ex}")

    # 4. DuckDB (buffer/fallback if Postgres fails or for all writes)
    if duckdb:
        try:
            con = duckdb.connect(duckdb_path, read_only=False)
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    tenant_id VARCHAR,
                    user_id VARCHAR,
                    session_id VARCHAR,
                    query VARCHAR,
                    result VARCHAR,
                    timestamp BIGINT,
                    synced BOOLEAN DEFAULT TRUE
                )
                """
            )
            con.execute(
                "INSERT INTO memory (tenant_id, user_id, session_id, query, result, timestamp, synced) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [tenant_id, user_id, session_id, query, json.dumps(result), entry["timestamp"], postgres_ok],
            )
            ok = True
            logger.info(f"[MemoryManager] DuckDB stored memory for user {user_id}")
            if postgres_ok:
                flush_duckdb_to_postgres(postgres, duckdb_path)
        except Exception as ex:
            logger.warning(f"[MemoryManager] DuckDB store failed: {ex}")

    # 5. ElasticSearch (optional, document index)
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
__all__ = [
    "recall_context",
    "update_memory",
    "flush_duckdb_to_postgres",
    "get_metrics",
    "_METRICS",
]
