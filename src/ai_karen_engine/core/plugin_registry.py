"""
Unified Plugin Registry for Kari AI
- Auto-discovers and loads plugins from both core and community dirs.
- Tags plugin origin ('core', 'community').
- Exposes: plugin_registry (dict), execute_plugin (callable)
"""

import importlib
import os
import sys
from pathlib import Path
from types import ModuleType

PLUGIN_REGISTRY = {}

def _discover_plugins(base_path, type_label):
    plugins = {}
    for item in Path(base_path).iterdir():
        if item.is_dir() and not item.name.startswith('__'):
            handler_path = item / "handler.py"
            if handler_path.exists():
                mod_name = f"{item.parent.name}.{item.name}.handler"
                # Insert base_path into sys.path for dynamic import
                if str(item.parent) not in sys.path:
                    sys.path.insert(0, str(item.parent))
                try:
                    mod = importlib.import_module(f"{item.name}.handler")
                    plugins[item.name] = {"handler": mod, "type": type_label}
                except Exception as ex:
                    print(f"Plugin load failed: {item.name} ({type_label}): {ex}")
    return plugins

def load_plugins():
    # Core plugins
    core_dir = Path(__file__).parent.parent / "plugins"
    core_plugins = _discover_plugins(core_dir, "core")

    # Community plugins (top-level under ai_karen_engine)
    comm_dir = Path(__file__).parent.parent / "community_plugins"
    community_plugins = _discover_plugins(comm_dir, "community")

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
