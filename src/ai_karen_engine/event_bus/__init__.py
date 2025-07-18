"""Simple in-memory event bus simulating Redis Streams."""

from __future__ import annotations

import collections
import uuid
from dataclasses import dataclass
from typing import Any, Deque, Dict, List, Optional


@dataclass
class Event:
    id: str
    capsule: str
    event_type: str
    payload: Dict[str, Any]
    risk: float
    tenant_id: Optional[str]
    roles: List[str]


class EventBus:
    def __init__(self) -> None:
        self._queue: Deque[Event] = collections.deque()

    def publish(
        self,
        capsule: str,
        event_type: str,
        payload: Dict[str, Any],
        risk: float = 0.0,
        *,
        roles: List[str],
        tenant_id: Optional[str] = None,
    ) -> str:
        if not roles:
            raise PermissionError("Missing roles for event publish")
        eid = str(uuid.uuid4())
        self._queue.append(Event(eid, capsule, event_type, payload, risk, tenant_id, list(roles)))
        return eid
    def consume(self, roles: List[str], tenant_id: Optional[str] = None) -> List[Event]:
        events: List[Event] = []
        remaining: Deque[Event] = collections.deque()
        for e in self._queue:
            if tenant_id is not None and e.tenant_id != tenant_id:
                remaining.append(e)
                continue
            if set(roles).intersection(e.roles):
                events.append(e)
            else:
                remaining.append(e)
        self._queue = remaining
        return events


_global_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Return a module-level :class:`EventBus` singleton."""
    global _global_bus
    if _global_bus is None:
        _global_bus = EventBus()
    return _global_bus


__all__ = ["Event", "EventBus", "get_event_bus"]
