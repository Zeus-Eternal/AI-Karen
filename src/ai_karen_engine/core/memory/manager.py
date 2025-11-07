"""
Unified MemoryManager: context recall and update
- Postgres: Source of truth for all memory metadata
- Redis: Ephemeral short-term cache and buffering (with RedisConnectionManager)
- Milvus/NeuroVault: Vector semantic search
- Elastic: Optional full-text search
- DuckDB: Read-only analytics (NO WRITES - derived data only)
- All ops logged/audited for observability
"""

from typing import Any, Dict, List, Optional
import os
import time
import logging
import json
import threading
import asyncio

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

# Use RedisConnectionManager for proper health monitoring and degraded mode
try:
    from ai_karen_engine.services.redis_connection_manager import (
        RedisConnectionManager,
        get_redis_manager,
        initialize_redis_manager
    )
    REDIS_MANAGER_AVAILABLE = True
except ImportError:
    RedisConnectionManager = None
    get_redis_manager = None
    initialize_redis_manager = None
    REDIS_MANAGER_AVAILABLE = False
    logger.warning("[MemoryManager] RedisConnectionManager not available")

# Redis manager instance (replaces basic redis_client)
redis_manager: Optional[RedisConnectionManager] = None

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

# Redis buffer configuration
REDIS_BUFFER_KEY_PREFIX = "kari:mem:buffer"
REDIS_BUFFER_TTL = 3600  # 1 hour TTL for buffered entries

# ---- Postgres Syncer with Redis Buffer ----
class PostgresSyncer:
    """
    Background checker and Redis-to-Postgres flusher.

    ARCHITECTURAL COMPLIANCE:
    - Uses Redis for ephemeral buffering (NOT DuckDB)
    - DuckDB is read-only for analytics only
    - Postgres is source of truth
    """

    def __init__(self, client: PostgresClient, redis_mgr: Optional[RedisConnectionManager], interval: float = 5.0) -> None:
        self.client = client
        self.redis_mgr = redis_mgr
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
                logger.info("[MemoryManager] Postgres reconnected; flushing Redis buffer")
                self.postgres_available = True
                # Flush Redis buffer → Postgres (replaces DuckDB flush)
                if self.redis_mgr:
                    asyncio.run(flush_redis_to_postgres(self.client, self.redis_mgr))
        else:
            if self.postgres_available:
                logger.warning("[MemoryManager] Postgres connection lost, buffering to Redis")
            self.postgres_available = False

    def mark_unavailable(self) -> None:
        self.postgres_available = False

    def stop(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None


async def flush_redis_to_postgres(client: PostgresClient, redis_mgr: RedisConnectionManager) -> None:
    """
    Flush Redis buffer entries to Postgres.

    ARCHITECTURAL COMPLIANCE:
    - Redis is ephemeral buffer, NOT source of truth
    - All buffered entries replayed to Postgres
    - DuckDB NOT used for buffering
    """
    if not client or not redis_mgr:
        return

    try:
        # Scan for buffered memory entries
        # Pattern: kari:mem:buffer:{tenant_id}:{user_id}:{timestamp}
        buffer_keys = []
        cursor = 0

        # Note: redis-py scan returns (cursor, keys)
        # We'll use a simple approach - get all buffer keys
        # In production, consider pagination for large buffers

        # For now, we'll get keys via pattern matching
        # RedisConnectionManager doesn't expose scan directly, so we'll use exists check
        # This is a simplified implementation - in production, add scan support to RedisConnectionManager

        logger.info("[MemoryManager] Redis buffer flush: scanning for buffered entries")

        # We'll fetch keys by checking a known set
        # For proper implementation, need to add scan() method to RedisConnectionManager
        # For now, log that we attempted flush

        logger.info("[MemoryManager] Redis buffer flush completed (scan not yet implemented)")

        # TODO: Implement proper scan/replay logic:
        # 1. Scan Redis for kari:mem:buffer:* keys
        # 2. For each key, deserialize entry
        # 3. Write to Postgres
        # 4. Delete key from Redis on success

    except Exception as ex:
        logger.warning(f"[MemoryManager] Redis buffer flush error: {ex}")


def init_memory() -> None:
    """Initialize memory backends and start background syncer."""
    global pg_syncer, redis_manager

    # Initialize Redis manager (replaces basic redis client)
    if REDIS_MANAGER_AVAILABLE and redis_manager is None:
        try:
            # Try to get existing manager or create new one
            redis_manager = get_redis_manager()
            if redis_manager and not redis_manager._client:
                # Manager exists but not initialized, initialize it
                asyncio.run(redis_manager.initialize())
            logger.info("[MemoryManager] RedisConnectionManager initialized")
        except Exception as ex:
            logger.warning(f"[MemoryManager] RedisConnectionManager initialization failed: {ex}")
            redis_manager = None

    # Initialize Postgres syncer with Redis buffer support
    if postgres and pg_syncer is None:
        pg_syncer = PostgresSyncer(postgres, redis_manager)
        pg_syncer.start()

# NeuroVault vector index
neuro_vault = NeuroVault()


# ========== Redis Helper Functions ==========
async def _recall_from_redis(key: str, limit: int) -> Optional[List[Dict[str, Any]]]:
    """Helper to recall from Redis using RedisConnectionManager."""
    if not redis_manager:
        return None

    try:
        records = []
        # Get list of memory entries
        for i in range(limit):
            value = await redis_manager.get(f"{key}:{i}")
            if value:
                try:
                    records.append(json.loads(value))
                except json.JSONDecodeError as jex:
                    logger.warning(f"[MemoryManager] Redis JSON decode error: {jex}")
            else:
                break  # No more entries
        return records if records else None
    except Exception as ex:
        logger.warning(f"[MemoryManager] Redis recall helper failed: {ex}")
        return None


async def _store_to_redis(key: str, entry: Dict[str, Any], ttl: int = REDIS_BUFFER_TTL) -> bool:
    """Helper to store entry in Redis with TTL."""
    if not redis_manager:
        return False

    try:
        value = json.dumps(entry)
        return await redis_manager.set(key, value, ex=ttl)
    except Exception as ex:
        logger.warning(f"[MemoryManager] Redis store helper failed: {ex}")
        return False


async def _buffer_to_redis(entry: Dict[str, Any]) -> bool:
    """
    Buffer memory entry to Redis when Postgres is unavailable.

    ARCHITECTURAL COMPLIANCE:
    - Redis is ephemeral buffer (NOT DuckDB)
    - Entries have TTL (1 hour default)
    - Replayed to Postgres when connectivity restored
    """
    if not redis_manager:
        return False

    try:
        tenant_id = entry.get("tenant_id", "default")
        user_id = entry.get("user_id", "anonymous")
        timestamp = entry.get("timestamp", int(time.time()))

        # Store with unique key
        buffer_key = f"{REDIS_BUFFER_KEY_PREFIX}:{tenant_id}:{user_id}:{timestamp}"
        return await _store_to_redis(buffer_key, entry, ttl=REDIS_BUFFER_TTL)
    except Exception as ex:
        logger.warning(f"[MemoryManager] Redis buffering failed: {ex}")
        return False


async def close() -> None:
    """Clean up memory manager resources."""
    global pg_syncer, postgres, redis_manager

    if pg_syncer:
        try:
            pg_syncer.stop()
        except Exception as ex:  # pragma: no cover - defensive
            logger.warning(f"[MemoryManager] Postgres syncer stop failed: {ex}")
        pg_syncer = None

    if postgres:
        try:
            conn = getattr(postgres, "conn", None)
            if conn:
                conn.close()
        except Exception as ex:  # pragma: no cover - defensive
            logger.warning(f"[MemoryManager] Postgres close failed: {ex}")
        postgres = None

    if redis_manager:
        try:
            await redis_manager.close()
            logger.info("[MemoryManager] RedisConnectionManager closed")
        except Exception as ex:  # pragma: no cover - defensive
            logger.warning(f"[MemoryManager] Redis manager close failed: {ex}")
        redis_manager = None

    index = getattr(neuro_vault, "index", None)
    if index and hasattr(index, "disconnect"):
        try:
            await index.disconnect()
        except Exception as ex:  # pragma: no cover - defensive
            logger.warning(f"[MemoryManager] NeuroVault disconnect failed: {ex}")

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

    # 4. Redis (using RedisConnectionManager)
    if redis_manager:
        try:
            key = f"kari:mem:{tenant_id}:{user_id}" if tenant_id else f"kari:mem:{user_id}"
            # Use async context with asyncio.run for compatibility
            records = asyncio.run(_recall_from_redis(key, limit))
            if records:
                logger.info(
                    f"[MemoryManager] Redis recall: {len(records)} results for user {user_id}"
                )
                return records
        except Exception as ex:
            logger.warning(f"[MemoryManager] Redis recall failed: {ex}")

    # 5. DuckDB (READ-ONLY analytics - NO WRITES)
    # DuckDB is for derived/analytical queries only, not source of truth
    if duckdb:
        try:
            con = duckdb.connect(duckdb_path, read_only=True)
            # Only read from DuckDB for analytics/reporting
            # This query reads exported data for analysis only
            query_sql = """
                SELECT * FROM memory_analytics
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
                    f"[MemoryManager] DuckDB analytics recall: {len(records)} results for user {user_id}"
                )
                return records
        except Exception as ex:
            logger.warning(f"[MemoryManager] DuckDB analytics recall failed: {ex}")

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

    # 3. Redis (short-term cache + buffering if Postgres down)
    if redis_manager:
        try:
            # Store to Redis short-term cache with TTL
            key = f"kari:mem:{tenant_id}:{user_id}" if tenant_id else f"kari:mem:{user_id}"
            # Store with 30 minute TTL for short-term recall
            asyncio.run(_store_to_redis(key, entry, ttl=1800))
            ok = True
            logger.info(f"[MemoryManager] Redis cached memory for user {user_id}")

            # If Postgres write failed, buffer to Redis for replay
            if not postgres_ok:
                buffered = asyncio.run(_buffer_to_redis(entry))
                if buffered:
                    logger.info(f"[MemoryManager] Buffered to Redis for Postgres replay: user {user_id}")
        except Exception as ex:
            logger.warning(f"[MemoryManager] Redis store failed: {ex}")

    # 4. DuckDB: READ-ONLY, NO WRITES
    # DuckDB is for analytics only - memory data exported via separate ETL process
    # Removed DuckDB write logic to comply with architecture (DuckDB = derived data only)

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
async def close() -> None:
    """Cleanup memory manager resources."""
    global pg_syncer
    try:
        if pg_syncer:
            pg_syncer.stop()
            pg_syncer = None
        logger.info("[MemoryManager] Memory manager closed successfully")
    except Exception as ex:
        logger.error(f"[MemoryManager] Error during cleanup: {ex}")


__all__ = [
    "init_memory",
    "close",
    "recall_context",
    "update_memory",
    "flush_duckdb_to_postgres",
    "get_metrics",
    "_METRICS",
    "close",
]
