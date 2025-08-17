"""Redis-backed service registry for MCP."""

from __future__ import annotations
from typing import Iterable, Optional
import json

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover - optional dep
    redis = None



class ServiceRegistry:
    """Register and lookup MCP services in Redis."""

    def __init__(self, redis_client: Optional[redis.Redis] = None, prefix: str = "mcp"):
        if redis_client is not None:
            self.redis = redis_client
        else:
            if redis is None:
                raise ImportError("redis package is required for ServiceRegistry")
            self.redis = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
        self.prefix = prefix

    def _k(self, name: str) -> str:
        return f"{self.prefix}:svc:{name}"

    def register(self, name: str, endpoint: str, kind: str, roles: Optional[Iterable[str]] = None) -> None:
        data = {"endpoint": endpoint, "kind": kind, "roles": list(roles or [])}
        self.redis.set(self._k(name), json.dumps(data))

    def deregister(self, name: str) -> None:
        self.redis.delete(self._k(name))

    def lookup(self, name: str) -> Optional[dict]:
        val = self.redis.get(self._k(name))
        return json.loads(val) if val else None

    def list(self) -> dict:
        services = {}
        for key in self.redis.keys(f"{self.prefix}:svc:*"):
            val = self.redis.get(key)
            if val:
                services[key.split(":")[-1]] = json.loads(val)
        return services

