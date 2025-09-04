"""
DecisionLogger emits structured routing events for observability (OSIRIS-compatible).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from collections import deque
from datetime import datetime
from typing import Any, Dict, Optional

from ai_karen_engine.routing.types import RouteDecision
from ai_karen_engine.event_bus import EventBus
from ai_karen_engine.core.logging.logger import get_logger


@dataclass
class RoutingEvent:
    timestamp: datetime
    request_id: str
    user_id: str
    task_type: str
    khrp_step: Optional[str]
    decision: RouteDecision
    execution_time_ms: float
    success: bool
    error: Optional[str] = None


class DecisionLogger:
    def __init__(self) -> None:
        # Use CopilotKit logging pattern
        self._log = get_logger("kari.kire").logger
        try:
            self._bus = EventBus()
        except Exception:
            self._bus = None
        # In-memory history for audit/debug
        self._history = deque(maxlen=500)

    def log_decision(
        self,
        request_id: str,
        user_id: str,
        task_type: str,
        khrp_step: Optional[str],
        decision: RouteDecision,
        execution_time_ms: float,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        payload: Dict[str, Any] = {
            "engine": "kire",
            "action": "routing.select",
            "event": "routing.done" if success else "routing.error",
            "correlation_id": request_id,
            "user_id": user_id,
            "task_type": task_type,
            "khrp_step": khrp_step,
            "provider": decision.provider,
            "model": decision.model,
            "reason": decision.reasoning,
            "confidence": decision.confidence,
            "fallback_chain": decision.fallback_chain,
            "metadata": decision.metadata,
            "exec_ms": execution_time_ms,
        }
        if error:
            payload["error"] = error
        level = logging.INFO if success else logging.ERROR
        # Copy correlation_id onto top-level extra for structured logging
        extra = {"context": payload, "correlation_id": payload.get("correlation_id")}
        self._log.log(level, "osiris.event", extra=extra)
        # Also publish to event bus if available
        try:
            if self._bus:
                roles = ["admin", "user"]
                self._bus.publish("osiris", payload["event"], payload, roles=roles)
        except Exception:
            pass
        # Store in history for audit
        try:
            self._history.append(payload)
        except Exception:
            pass

    def log_start(self, request_id: str, user_id: str, action: str, meta: Dict[str, Any]) -> None:
        payload = {
            "engine": "kire",
            "action": action,
            "event": "routing.start",
            "correlation_id": request_id,
            "user_id": user_id,
            **meta,
        }
        self._log.info("osiris.event", extra={"context": payload, "correlation_id": request_id})
        try:
            if self._bus:
                roles = ["admin", "user"]
                self._bus.publish("osiris", payload["event"], payload, roles=roles)
        except Exception:
            pass
        try:
            self._history.append(payload)
        except Exception:
            pass

    # -------- Audit utilities --------
    def get_history(self, limit: int = 100, user_id: Optional[str] = None) -> list[dict]:
        items = list(self._history)[-limit:]
        if user_id:
            items = [e for e in items if e.get("user_id") == user_id]
        return items

    def generate_audit_report(self, limit: int = 200) -> Dict[str, Any]:
        items = list(self._history)[-limit:]
        total = len(items)
        by_provider: Dict[str, int] = {}
        errors = 0
        for e in items:
            prov = e.get("provider") or (e.get("metadata") or {}).get("provider")
            if prov:
                by_provider[prov] = by_provider.get(prov, 0) + 1
            if e.get("event") == "routing.error":
                errors += 1
        return {
            "total_events": total,
            "error_events": errors,
            "by_provider": by_provider,
        }
