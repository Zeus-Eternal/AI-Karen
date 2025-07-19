"""Base classes and utilities for MCP clients."""

from __future__ import annotations

from typing import Iterable, Optional

from .registry import ServiceRegistry

try:
    from prometheus_client import Counter, Histogram
    METRICS_ENABLED = True
except Exception:  # pragma: no cover - optional dep
    METRICS_ENABLED = False

    class _DummyMetric:
        def labels(self, **_kw):
            return self

        def inc(self, _n: int = 1) -> None:
            pass

        def observe(self, _v: float) -> None:
            pass

    Counter = Histogram = _DummyMetric

MCP_CALLS_TOTAL = Counter(
    "mcp_calls_total",
    "Total MCP calls",
    ["service", "success"],
) if METRICS_ENABLED else Counter()

MCP_AUTH_FAILURES = Counter(
    "mcp_auth_failures",
    "MCP authentication failures",
    ["service"],
) if METRICS_ENABLED else Counter()

MCP_LATENCY = Histogram(
    "mcp_latency_seconds",
    "Latency of MCP calls (seconds)",
    ["service", "success"],
) if METRICS_ENABLED else Histogram()


class AuthorizationError(Exception):
    """Raised when authentication or RBAC checks fail."""


class BaseMCPClient:
    """Common functionality for MCP clients."""

    def __init__(self, registry: "ServiceRegistry", token: str, role: str):
        self.registry = registry
        self.token = token
        self.role = role

    def _record_metric(self, service: str, duration: float, success: bool) -> None:
        label_success = "true" if success else "false"
        MCP_CALLS_TOTAL.labels(service=service, success=label_success).inc()
        MCP_LATENCY.labels(service=service, success=label_success).observe(duration)

    def _auth(self, service: str, token: str, roles: Optional[Iterable[str]]) -> None:
        if token != self.token or (roles and self.role not in roles):
            MCP_AUTH_FAILURES.labels(service=service).inc()
            raise AuthorizationError("Invalid token or insufficient role")


