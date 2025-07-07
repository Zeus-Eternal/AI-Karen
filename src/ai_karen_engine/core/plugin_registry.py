"""
Unified Plugin Registry for Kari AI
- Auto-discovers and loads plugins from both core and community dirs.
- Tags plugin origin ('core', 'community').
- Exposes: plugin_registry (dict), execute_plugin (callable)
"""

import importlib
import pkgutil

from types import ModuleType

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
        except Exception as ex:  # pragma: no cover - safety net
            print(f"Plugin load failed: {name} ({type_label}): {ex}")
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
    if hasattr(handler, "run"):
        return handler.run(user_ctx, query, context)
    elif hasattr(handler, "main"):
        return handler.main(user_ctx, query, context)
    else:
        raise RuntimeError(f"No runnable entry for plugin: {handler}")

# Initialize on import (optional, or call load_plugins() on app start)
load_plugins()

plugin_registry = PLUGIN_REGISTRY

__all__ = ["plugin_registry", "execute_plugin", "load_plugins"]
