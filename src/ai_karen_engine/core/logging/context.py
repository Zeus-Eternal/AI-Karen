from __future__ import annotations

import contextvars
from dataclasses import dataclass, field
from typing import Any

@dataclass(slots=True)
class RuntimeLogContext:
    correlation_id: str | None = None
    request_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    user_id: str | None = None
    tenant_id: str | None = None
    session_id: str | None = None
    conversation_id: str | None = None
    route: str | None = None
    method: str | None = None
    client_ip_hash: str | None = None
    intent: str | None = None
    runtime_stage: str | None = None
    provider: str | None = None
    model: str | None = None
    engine_id: str | None = None
    engine_type: str | None = None
    runtime_engine: str | None = None
    fallback_level: int | None = None
    degraded: bool | None = None
    degradation_reason: str | None = None
    memory_activation_mode: str | None = None
    memory_classes: list[str] | None = None
    tool_name: str | None = None
    plugin_id: str | None = None
    status: str | None = None
    error_type: str | None = None
    error_code: str | None = None
    latency_ms: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary, removing None values."""
        data = {
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "route": self.route,
            "method": self.method,
            "client_ip_hash": self.client_ip_hash,
            "intent": self.intent,
            "runtime_stage": self.runtime_stage,
            "provider": self.provider,
            "model": self.model,
            "engine_id": self.engine_id,
            "engine_type": self.engine_type,
            "runtime_engine": self.runtime_engine,
            "fallback_level": self.fallback_level,
            "degraded": self.degraded,
            "degradation_reason": self.degradation_reason,
            "memory_activation_mode": self.memory_activation_mode,
            "memory_classes": self.memory_classes,
            "tool_name": self.tool_name,
            "plugin_id": self.plugin_id,
            "status": self.status,
            "error_type": self.error_type,
            "error_code": self.error_code,
            "latency_ms": self.latency_ms,
        }
        data.update(self.extra)
        return {k: v for k, v in data.items() if v is not None}

_CONTEXT: contextvars.ContextVar[RuntimeLogContext] = contextvars.ContextVar(
    "runtime_log_context", default=RuntimeLogContext()
)

def get_log_context() -> RuntimeLogContext:
    """Return the current runtime log context."""
    return _CONTEXT.get()

def set_log_context(context: RuntimeLogContext) -> contextvars.Token:
    """Set the current runtime log context."""
    return _CONTEXT.set(context)

def clear_log_context():
    """Reset the runtime log context to empty."""
    _CONTEXT.set(RuntimeLogContext())

def bind_log_context(**kwargs: Any):
    """Update the current context with new values."""
    ctx = get_log_context()
    for key, value in kwargs.items():
        if hasattr(ctx, key):
            setattr(ctx, key, value)
        else:
            ctx.extra[key] = value
