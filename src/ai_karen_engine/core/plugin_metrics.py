"""Prometheus metrics for plugin execution and memory writes."""

from typing import Any

try:
    from prometheus_client import Counter

    PLUGIN_CALLS = Counter(
        "plugin_calls_total",
        "Total plugin executions",
        ["plugin", "success"],
    )
    MEMORY_WRITES = Counter(
        "memory_writes_total",
        "Memory writes triggered by plugins",
        ["plugin", "success"],
    )
except Exception:  # pragma: no cover - missing dependency
    class _DummyCounter:
        def labels(self, **_kw: Any) -> "_DummyCounter":
            return self

        def inc(self, *_args: Any, **_kw: Any) -> None:
            pass

    PLUGIN_CALLS = MEMORY_WRITES = _DummyCounter()


def record_plugin_call(plugin: str, success: bool) -> None:
    """Increment plugin call counter."""
    label = "true" if success else "false"
    PLUGIN_CALLS.labels(plugin=plugin, success=label).inc()


def record_memory_write(plugin: str, success: bool) -> None:
    """Increment memory write counter."""
    label = "true" if success else "false"
    MEMORY_WRITES.labels(plugin=plugin, success=label).inc()

__all__ = ["record_plugin_call", "record_memory_write"]
