"""PluginManager with metrics and memory hooks."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .router import PluginRouter
from ai_karen_engine.core.memory.manager import update_memory
from ai_karen_engine.integrations.llm_utils import embed_text

try:
    from prometheus_client import Counter, REGISTRY
    METRICS_ENABLED = True
except Exception:  # pragma: no cover - optional dependency
    METRICS_ENABLED = False

    class _DummyMetric:
        def labels(self, **kwargs):
            return self

        def inc(self, n: int = 1) -> None:
            pass

    Counter = _DummyMetric  # type: ignore

if METRICS_ENABLED:
    if "plugin_calls_total" not in REGISTRY._names_to_collectors:
        PLUGIN_CALLS = Counter(
            "plugin_calls_total",
            "Total plugin calls",
            ["plugin"],
        )
    else:  # pragma: no cover - reuse collector under reload
        PLUGIN_CALLS = REGISTRY._names_to_collectors["plugin_calls_total"]

    if "plugin_failure_rate" not in REGISTRY._names_to_collectors:
        PLUGIN_FAILURES = Counter(
            "plugin_failure_rate",
            "Plugin failures",
            ["plugin"],
        )
    else:  # pragma: no cover - reuse collector
        PLUGIN_FAILURES = REGISTRY._names_to_collectors["plugin_failure_rate"]

    if "memory_writes_total" not in REGISTRY._names_to_collectors:
        MEMORY_WRITES = Counter(
            "memory_writes_total",
            "Memory writes from plugins",
        )
    else:  # pragma: no cover - reuse collector
        MEMORY_WRITES = REGISTRY._names_to_collectors["memory_writes_total"]
else:  # pragma: no cover - metrics disabled
    PLUGIN_CALLS = Counter()
    PLUGIN_FAILURES = Counter()
    MEMORY_WRITES = Counter()

logger = logging.getLogger("kari.plugin_manager")


class PluginManager:
    """Manage plugin execution with metrics and memory persistence."""

    def __init__(self, router: Optional[PluginRouter] = None) -> None:
        self.router = router or PluginRouter()

    async def run_plugin(
        self,
        name: str,
        params: Dict[str, Any],
        user_ctx: Dict[str, Any],
    ) -> Any:
        """Execute a plugin and record metrics/memory."""
        PLUGIN_CALLS.labels(plugin=name).inc()
        logger.info("Running plugin %s with params=%s", name, params)
        try:
            result, out, err = await self.router.dispatch(
                name, params, roles=user_ctx.get("roles")
            )
            logger.info("Plugin %s result: %s", name, result)
            if out:
                logger.debug("%s stdout: %s", name, out.strip())
            if err:
                logger.debug("%s stderr: %s", name, err.strip())
        except Exception as ex:  # pragma: no cover - runtime safeguard
            PLUGIN_FAILURES.labels(plugin=name).inc()
            logger.exception("Plugin %s failed: %s", name, ex)
            raise

        summary = str(result)[:200]
        embed_input = f"{name} {summary} {user_ctx}"
        try:
            embed_text(embed_input)
        except Exception:  # pragma: no cover - embedding optional
            logger.debug("Embedding failed for plugin %s", name)

        try:
            update_memory(
                user_ctx,
                name,
                {"params": params, "result": result},
                tenant_id=user_ctx.get("tenant_id"),
            )
            MEMORY_WRITES.inc()
        except Exception:  # pragma: no cover - safety
            logger.warning("Memory update failed for plugin %s", name)

        return result, out, err


_plugin_manager: Optional[PluginManager] = None


def create_plugin_manager(router: Optional[PluginRouter] = None) -> PluginManager:
    """Return a new :class:`PluginManager` instance."""
    return PluginManager(router=router)


def get_plugin_manager() -> PluginManager:
    """Return cached PluginManager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


__all__ = [
    "PluginManager",
    "get_plugin_manager",
    "create_plugin_manager",
    "PLUGIN_CALLS",
    "PLUGIN_FAILURES",
    "MEMORY_WRITES",
]