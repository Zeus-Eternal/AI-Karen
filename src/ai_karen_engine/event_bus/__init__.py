"""
Simple in-memory and Redis-backed event bus with tenant & role filtering.
"""

from __future__ import annotations

import collections
import json
import os
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Deque, Dict, List, Optional, Union

from ai_karen_engine.config.config_manager import config_manager

# Optional Redis dependency
try:
    import redis  # type: ignore
except ImportError:
    redis = None

# Default configuration
REDIS_URL = config_manager.get_config_value("redis", "url", default=os.getenv("REDIS_URL"))
EVENT_LIST_KEY = config_manager.get_config_value("event_bus", "key", default="kari:events")
ALLOWED_PUBLISH_ROLES = set(config_manager.get_config_value("event_bus", "allowed_roles", default=["admin", "user"]))

@dataclass
class Event:
    id: str
    capsule: str
    event_type: str
    payload: Dict[str, Any]
    risk: float
    roles: List[str]
    tenant_id: Optional[str] = None

class EventBus:
    """In-memory FIFO event bus with optional Redis fallback."""

    def __init__(self) -> None:
        self._queue: Deque[Event] = collections.deque()
        self._redis: Optional["redis.Redis"] = None

        if redis and REDIS_URL:
            try:
                self._redis = redis.from_url(REDIS_URL)
            except Exception:
                self._redis = None

    def publish(
        self,
        capsule: str,
        event_type: str,
        payload: Dict[str, Any],
        risk: float = 0.0,
        roles: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> str:
        # enforce allowed roles
        if not roles or not ALLOWED_PUBLISH_ROLES.intersection(roles):
            raise PermissionError("Publish denied: insufficient roles")
        eid = str(uuid.uuid4())
        event = Event(eid, capsule, event_type, payload, risk, roles, tenant_id)

        # try Redis first
        if self._redis:
            try:
                self._redis.rpush(EVENT_LIST_KEY, json.dumps(asdict(event)))
                return eid
            except Exception:
                self._redis = None  # disable Redis on failure

        # fallback to in-memory queue
        self._queue.append(event)
        return eid

    def consume(
        self,
        roles: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> List[Event]:
        results: List[Event] = []

        # drain Redis list if available
        if self._redis:
            try:
                raw = self._redis.lrange(EVENT_LIST_KEY, 0, -1)
                self._redis.delete(EVENT_LIST_KEY)
                for item in raw:
                    text = item.decode() if isinstance(item, (bytes, bytearray)) else item
                    data = json.loads(text)
                    results.append(Event(**data))
            except Exception:
                self._redis = None  # disable Redis on error

        # drain in-memory queue
        results.extend(self._queue)
        self._queue.clear()

        # apply tenant & role filtering
        def allowed(e: Event) -> bool:
            if tenant_id is not None and e.tenant_id != tenant_id:
                return False
            if roles and not set(roles).intersection(e.roles):
                return False
            return True

        return [e for e in results if allowed(e)]

class RedisEventBus(EventBus):
    """Explicit Redis-only event bus (list semantics)."""

    def __init__(
        self,
        redis_client: Optional["redis.Redis"] = None,
        list_key: Optional[str] = None,
    ) -> None:
        super().__init__()
        if redis_client:
            self._redis = redis_client
        elif redis is None:
            raise ImportError("redis package is required for RedisEventBus")
        elif REDIS_URL:
            self._redis = redis.from_url(REDIS_URL)
        else:
            self._redis = redis.Redis()
        self._list_key = list_key or EVENT_LIST_KEY

    def publish(
        self,
        capsule: str,
        event_type: str,
        payload: Dict[str, Any],
        risk: float = 0.0,
        roles: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> str:
        if not roles or not ALLOWED_PUBLISH_ROLES.intersection(roles):
            raise PermissionError("Publish denied: insufficient roles")
        eid = str(uuid.uuid4())
        ev = Event(eid, capsule, event_type, payload, risk, roles or [], tenant_id)
        self._redis.rpush(self._list_key, json.dumps(asdict(ev)))
        return eid

    def consume(
        self,
        roles: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> List[Event]:
        raw = self._redis.lrange(self._list_key, 0, -1)
        if raw:
            self._redis.delete(self._list_key)
        events: List[Event] = []
        for item in raw:
            text = item.decode() if isinstance(item, (bytes, bytearray)) else item
            data = json.loads(text)
            events.append(Event(**data))
        # apply same filtering as base
        return super().consume(roles=roles, tenant_id=tenant_id)

# Singleton accessor
_global_bus: Union[EventBus, RedisEventBus, None] = None

def get_event_bus() -> Union[EventBus, RedisEventBus]:
    """Return a singleton EventBus, preferring Redis if configured."""
    global _global_bus
    if _global_bus is not None:
        return _global_bus

    backend = config_manager.get_config_value("event_bus", "backend", default="memory").lower()
    if backend == "redis" and redis:
        try:
            _global_bus = RedisEventBus()
        except Exception:
            _global_bus = EventBus()
    else:
        _global_bus = EventBus()

    return _global_bus

__all__ = ["Event", "EventBus", "RedisEventBus", "get_event_bus"]
