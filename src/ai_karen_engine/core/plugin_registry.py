"""
Unified Plugin Registry for Kari AI
- Auto-discovers and loads plugins from both core and community dirs.
- Tags plugin origin ('core', 'community').
- Exposes: plugin_registry (dict), execute_plugin (callable)
"""

import importlib
import pkgutil

from types import ModuleType

_METRICS: dict[str, int] = {
    "plugins_loaded": 0,
    "plugin_exec_total": 0,
    "plugin_import_errors": 0,
}

try:
    from prometheus_client import Counter
    from ai_karen_engine.integrations.llm_utils import PROM_REGISTRY

    PLUGIN_EXEC_COUNT = Counter(
        "plugin_exec_total",
        "Total plugin execution calls",
        registry=PROM_REGISTRY,
    )
    PLUGIN_LOADED_COUNT = Counter(
        "plugins_loaded",
        "Plugins discovered at startup",
        registry=PROM_REGISTRY,
    )
    PLUGIN_IMPORT_ERROR_COUNT = Counter(
        "plugin_import_errors",
        "Plugin import failures",
        ["plugin"],
        registry=PROM_REGISTRY,
    )
except Exception:  # pragma: no cover - optional dep
    class _Dummy:
        def labels(self, *_, **__):
            return self

        def inc(self, *_args, **_kwargs) -> None:
            pass

    PLUGIN_EXEC_COUNT = PLUGIN_LOADED_COUNT = PLUGIN_IMPORT_ERROR_COUNT = _Dummy()

PLUGIN_REGISTRY: dict[str, dict[str, ModuleType]] = {}


def _discover_plugins(base_pkg: str, type_label: str) -> dict[str, dict[str, ModuleType]]:
    """Discover and import plugins under ``base_pkg``."""
    plugins: dict[str, dict[str, ModuleType]] = {}
    try:
        package = importlib.import_module(base_pkg)
    except ModuleNotFoundError:
        return plugins
    for _, name, ispkg in pkgutil.iter_modules(package.__path__):
        if not ispkg:
            continue
        try:
            mod = importlib.import_module(f"{base_pkg}.{name}.handler")
            plugins[name] = {"handler": mod, "type": type_label}
            _METRICS["plugins_loaded"] += 1
            PLUGIN_LOADED_COUNT.inc()
        except Exception as ex:  # pragma: no cover - safety net
            print(f"Plugin load failed: {name} ({type_label}): {ex}")
            _METRICS["plugin_import_errors"] += 1
            PLUGIN_IMPORT_ERROR_COUNT.labels(plugin=name).inc()
    return plugins

def load_plugins() -> dict[str, dict[str, ModuleType]]:
    """Reload plugin registry from available packages."""
    core_plugins = _discover_plugins("ai_karen_engine.plugins", "core")
    community_plugins = _discover_plugins(
        "ai_karen_engine.community_plugins", "community"
    )

    # Merge and publish
    PLUGIN_REGISTRY.clear()
    PLUGIN_REGISTRY.update(core_plugins)
    PLUGIN_REGISTRY.update(community_plugins)
    return PLUGIN_REGISTRY

def execute_plugin(plugin_entry, user_ctx, query, context=None):
    """
    Executes the main entry point for a plugin.
    """
    handler = plugin_entry["handler"]
    _METRICS["plugin_exec_total"] += 1
    PLUGIN_EXEC_COUNT.inc()
    if hasattr(handler, "run"):
        return handler.run(user_ctx, query, context)
    elif hasattr(handler, "main"):
        return handler.main(user_ctx, query, context)
    else:
        raise RuntimeError(f"No runnable entry for plugin: {handler}")

# Initialize on import (optional, or call load_plugins() on app start)
load_plugins()

plugin_registry = PLUGIN_REGISTRY

__all__ = [
    "plugin_registry",
    "execute_plugin",
    "load_plugins",
    "_METRICS",
    "PLUGIN_IMPORT_ERROR_COUNT",
]
