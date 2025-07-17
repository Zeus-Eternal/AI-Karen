"""Event bus backed by Redis with in-memory fallback."""

from __future__ import annotations

import collections
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


_global_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Return a module-level :class:`EventBus` singleton."""
    global _global_bus
    if _global_bus is None:
        _global_bus = EventBus()
    return _global_bus


__all__ = ["Event", "EventBus", "get_event_bus"]
