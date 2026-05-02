from __future__ import annotations

from typing import Any

_EVENTS: list[dict[str, Any]] = []


def emit_expression_event(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "correlation_id": payload.get("correlation_id"),
        "request_id": payload.get("request_id"),
        "engine_id": payload.get("engine_id"),
        "engine_type": payload.get("engine_type"),
        "provider": payload.get("provider"),
        "model": payload.get("model"),
        "capabilities": payload.get("capabilities", []),
        "response_mode": payload.get("response_mode"),
        "latency_ms": payload.get("latency_ms", 0.0),
        "fallback_level": payload.get("fallback_level", 0),
        "degraded": payload.get("degraded", False),
        "degradation_reason": payload.get("degradation_reason"),
        "privacy_policy": payload.get("privacy_policy", "default"),
        "policy_rejections": payload.get("policy_rejections", []),
        **payload,
    }
    event = {"event": name, "payload": payload}
    _EVENTS.append(event)
    return event


def get_expression_events(limit: int = 100) -> list[dict[str, Any]]:
    return _EVENTS[-limit:]
