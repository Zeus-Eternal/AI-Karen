"""
RedisClient: Handles volatile short-term memory, cache, session, fast flush.
Production: Use redis-py, thread-safe, supports multiple namespaces.
"""

import os
import logging
import redis
import json

from typing import Optional


class RedisClient:
    def __init__(self, url: Optional[str] = None, prefix: str = "kari"):
        """Initialize the Redis client.

        Parameters
        ----------
        url: optional str
            Redis connection URL. Defaults to ``os.getenv("REDIS_URL")``.
        prefix: str
            Key prefix for all operations.
        """

        self.prefix = prefix
        conn_url = url or os.getenv("REDIS_URL")
        self.r = None
        if conn_url:
            try:
                self.r = redis.Redis.from_url(conn_url)
                self.r.ping()
            except Exception as ex:  # pragma: no cover - network may be down
                logging.getLogger(__name__).warning(
                    "[RedisClient] connection failed: %s", ex
                )
                self.r = None

    def _k(self, tenant_id, user_id, kind):
        return f"{self.prefix}:{tenant_id}:{user_id}:{kind}"

    def flush_short_term(self, tenant_id, user_id):
        """Flush all short-term cache for user."""
        keys = self.r.keys(self._k(tenant_id, user_id, "short_term*"))
        for k in keys:
            self.r.delete(k)

    def flush_long_term(self, tenant_id, user_id):
        """Flush all long-term cache for user."""
        keys = self.r.keys(self._k(tenant_id, user_id, "long_term*"))
        for k in keys:
            self.r.delete(k)

    def set_short_term(self, tenant_id, user_id, data):
        self.r.set(self._k(tenant_id, user_id, "short_term"), json.dumps(data))

    def get_short_term(self, tenant_id, user_id):
        val = self.r.get(self._k(tenant_id, user_id, "short_term"))
        return json.loads(val) if val else None

    def set_session(self, tenant_id, user_id, sess_data):
        self.r.set(self._k(tenant_id, user_id, "session"), json.dumps(sess_data))

    def get_session(self, tenant_id, user_id):
        val = self.r.get(self._k(tenant_id, user_id, "session"))
        return json.loads(val) if val else None

    # Health
    def health(self):
        try:
            self.r.ping()
            return True
        except Exception:
            return False
