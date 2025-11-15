"""
Consolidated plugin router implementation shared by ai_karen_engine
and extension-level modules.

This module keeps the legacy import path `src.extensions.plugins.core.router`
working by re-exporting the existing router implementation that lives
inside `ai_karen_engine.plugin_router`.
"""

from ai_karen_engine.plugin_router import (
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
