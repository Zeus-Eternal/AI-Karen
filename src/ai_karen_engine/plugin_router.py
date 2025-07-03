"""Compatibility wrapper exposing the core PluginRouter."""
from src.core.plugin_router import (
    PluginRouter as CorePluginRouter,
    AccessDenied,
    PluginRecord,
    PLUGIN_DIR,
    SCHEMA_PATH,
)

__all__ = [
    "CorePluginRouter",
    "AccessDenied",
    "PluginRecord",
    "PLUGIN_DIR",
    "SCHEMA_PATH",
    "PluginRouter",
]

class PluginRouter(CorePluginRouter):
    """Thin subclass for backwards compatibility."""
    pass
  
