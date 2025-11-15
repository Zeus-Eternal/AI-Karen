"""
Core plugin utilities exposed to extensions.
"""

from .router import (
    PluginRouter,
    get_plugin_router,
    AccessDenied,
    PluginRecord,
    PLUGIN_IMPORT_ERRORS,
)

__all__ = [
    "PluginRouter",
    "get_plugin_router",
    "AccessDenied",
    "PluginRecord",
    "PLUGIN_IMPORT_ERRORS",
]
