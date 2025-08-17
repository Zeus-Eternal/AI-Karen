"""
RedisClient: Handles volatile short-term memory, cache, session, fast flush.
Production: Use redis-py, thread-safe, supports multiple namespaces.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

import redis


class RedisClient:
    def __init__(
        self, url: Optional[str] = None, prefix: str = "kari", pool_size: int = 10
    ) -> None:
        """Initialize the Redis client.

        Parameters
        ----------
        url: optional str
            Redis connection URL. Defaults to ``os.getenv("REDIS_URL")``.
        prefix: str
            Key prefix for all operations.
        """

        self.prefix: str = prefix
        conn_url = url or os.getenv("REDIS_URL")
        self.pool: Optional[redis.ConnectionPool] = None
        self.r: Optional[redis.Redis[Any]] = None
        if conn_url:
            try:
                self.pool = redis.ConnectionPool.from_url(
                    conn_url, max_connections=pool_size
                )
                self.r = redis.Redis(connection_pool=self.pool)
                self.r.ping()
            except Exception as ex:  # pragma: no cover - network may be down
                logging.getLogger(__name__).warning(
                    "[RedisClient] connection failed: %s", ex
                )
                self.r = None
                self.pool = None

    def _k(self, tenant_id: str, user_id: str, kind: str) -> str:
        return f"{self.prefix}:{tenant_id}:{user_id}:{kind}"

    def flush_short_term(self, tenant_id: str, user_id: str) -> None:
        """Flush all short-term cache for user."""
        if not self.r:
            return
        keys = self.r.keys(self._k(tenant_id, user_id, "short_term*"))
        for k in keys:
            self.r.delete(k)

    def flush_long_term(self, tenant_id: str, user_id: str) -> None:
        """Flush all long-term cache for user."""
        if not self.r:
            return
        keys = self.r.keys(self._k(tenant_id, user_id, "long_term*"))
        for k in keys:
            self.r.delete(k)

    def set_short_term(
        self, tenant_id: str, user_id: str, data: Dict[str, Any]
    ) -> None:
        if not self.r:
            return
        self.r.set(self._k(tenant_id, user_id, "short_term"), json.dumps(data))

    def get_short_term(self, tenant_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.r:
            return None
        val = self.r.get(self._k(tenant_id, user_id, "short_term"))
        return json.loads(val) if val else None

    def set_session(
        self, tenant_id: str, user_id: str, sess_data: Dict[str, Any]
    ) -> None:
        if not self.r:
            return
        self.r.set(self._k(tenant_id, user_id, "session"), json.dumps(sess_data))

    def get_session(self, tenant_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.r:
            return None
        val = self.r.get(self._k(tenant_id, user_id, "session"))
        return json.loads(val) if val else None

    # Health
    def health(self) -> bool:
        try:
            if not self.r:
                return False
            self.r.ping()
            return True
        except Exception:
            return False

    def pool_utilization(self) -> float:
        if not self.pool:
            return 0.0
        used = self.pool._created_connections - len(self.pool._available_connections)  # type: ignore[attr-defined]
        max_conn = getattr(self.pool, "max_connections", 0)
        return used / float(max_conn) if max_conn else 0.0
