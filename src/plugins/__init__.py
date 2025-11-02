"""
AI Karen Plugin System - Core Infrastructure

This module provides the foundation for the lightweight plugin system,
enabling developers to build simple, focused functions that extend
system capabilities.

The plugin system is organized as follows:
- core/: Plugin framework code (managers, routers, sandbox, memory management)
- implementations/: Plugin implementations organized by category
- docs/: Comprehensive documentation for plugin development

This module maintains backward compatibility by re-exporting framework components.
"""

# Current imports (will be reorganized in task 3)
from ai_karen_engine.plugins.manager import PluginManager, get_plugin_manager
from ai_karen_engine.plugins.router import PluginRouter, PluginRecord, AccessDenied, get_plugin_router
from ai_karen_engine.plugins.sandbox_system import run_in_sandbox

# Import specific plugin implementations (will be moved to implementations/ in task 4)
from .search import SearchPlugin
from .searxng import SearxNGPlugin, SearxNGManager
from .yelp import YelpPlugin

# Future imports from core/ (will be activated in task 3)
# from .core import (
#     PluginManager,
#     PluginRouter,
#     PluginRecord,
#     AccessDenied,
#     MemoryManager,
#     PluginSandbox,
#     get_plugin_manager,
#     get_plugin_router,
#     run_in_sandbox
# )

__all__ = [
    # Plugin implementations (will be moved to implementations/)
    'SearchPlugin',
    'SearxNGPlugin', 
    'SearxNGManager',
    'YelpPlugin',
    # Framework components
    "PluginManager",
    "PluginRouter",
    "PluginRecord", 
    "AccessDenied",
    "get_plugin_manager",
    "get_plugin_router",
    "run_in_sandbox",
]