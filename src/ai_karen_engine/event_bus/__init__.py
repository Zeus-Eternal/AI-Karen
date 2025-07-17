"""Event bus backed by Redis with in-memory fallback."""

from __future__ import annotations

import collections
import json
import uuid
from dataclasses import dataclass
from typing import Any, Deque, Dict, List, Optional
import json
import os
import logging

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    redis = None

REDIS_URL = os.getenv("REDIS_URL")
ALLOWED_PUBLISH_ROLES = {"admin", "user"}
EVENT_KEY = os.getenv("EVENT_BUS_KEY", "kari:events")
log = logging.getLogger("kari.event_bus")

from ai_karen_engine.config import config_manager

try:  # Optional dependency
    import redis  # type: ignore
except Exception:  # pragma: no cover - optional dep
    redis = None


@dataclass
class Event:
    id: str
    capsule: str
    event_type: str
    payload: Dict[str, Any]
    risk: float
    roles: Optional[List[str]] = None
    tenant_id: Optional[str] = None


class EventBus:
    def __init__(self) -> None:
        self._queue: Deque[Event] = collections.deque()
        self._redis = None
        if redis and REDIS_URL:
            try:
                self._redis = redis.from_url(REDIS_URL)
            except Exception as ex:  # pragma: no cover - connection error
                log.warning("Redis connection failed: %s", ex)
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
        if roles is None or not ALLOWED_PUBLISH_ROLES.intersection(roles):
            raise PermissionError("Event publish denied")
        eid = str(uuid.uuid4())
        event = Event(eid, capsule, event_type, payload, risk, roles, tenant_id)
        if self._redis:
            try:
                self._redis.rpush(EVENT_KEY, json.dumps(event.__dict__))
            except Exception as ex:  # pragma: no cover - redis failure
                log.warning("Redis publish failed: %s", ex)
                self._queue.append(event)
        else:
            self._queue.append(event)
        return eid

    def consume(
        self,
        roles: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> List[Event]:
        events: List[Event] = []
        if self._redis:
            try:
                raw = self._redis.lrange(EVENT_KEY, 0, -1)
                self._redis.delete(EVENT_KEY)
                for b in raw:
                    try:
                        data = json.loads(b.decode())
                        events.append(Event(**data))
                    except Exception as jex:
                        log.warning("Redis decode error: %s", jex)
            except Exception as ex:  # pragma: no cover - redis failure
                log.warning("Redis consume failed: %s", ex)
                self._redis = None
        events.extend(list(self._queue))
        self._queue.clear()
        def _allowed(e: Event) -> bool:
            if tenant_id and e.tenant_id != tenant_id:
                return False
            if roles and not set(roles).intersection(e.roles or []):
                return False
            return True

        return [e for e in events if _allowed(e)]


class RedisEventBus:
    """Redis-backed implementation using a single stream."""

    def __init__(self, redis_client: "redis.Redis | None" = None, stream: str = "kari:events") -> None:
        if redis_client is not None:
            self.redis = redis_client
        else:
            if redis is None:
                raise ImportError("redis package is required for RedisEventBus")
            self.redis = redis.Redis()
        self.stream = stream

    def publish(self, capsule: str, event_type: str, payload: Dict[str, Any], risk: float = 0.0) -> str:
        data = {
            "capsule": capsule,
            "type": event_type,
            "payload": json.dumps(payload),
            "risk": risk,
        }
        eid = self.redis.xadd(self.stream, data)
        return str(eid)

    def consume(self) -> List[Event]:
        entries = self.redis.xrange(self.stream, min="-", max="+")
        events = []
        for eid, data in entries:
            try:
                payload = json.loads(data.get("payload", "{}"))
            except Exception:
                payload = {}
            events.append(
                Event(
                    str(eid),
                    data.get("capsule", ""),
                    data.get("type", ""),
                    payload,
                    float(data.get("risk", 0.0)),
                )
            )
        if entries:
            self.redis.delete(self.stream)
        return events


_global_bus: EventBus | RedisEventBus | None = None


def get_event_bus() -> EventBus:
    """Return a module-level :class:`EventBus` singleton."""
    global _global_bus
    if _global_bus is not None:
        return _global_bus
    backend = config_manager.get_config_value("event_bus", "memory")
    if backend == "redis":
        try:
            _global_bus = RedisEventBus()
        except Exception:
            _global_bus = EventBus()
    else:
        _global_bus = EventBus()
    return _global_bus


__all__ = ["Event", "EventBus", "RedisEventBus", "get_event_bus"]
