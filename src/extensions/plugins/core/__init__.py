"""
Plugin Framework Core Components

This package contains the core framework components for the unified plugin system.
"""

from .manager import PluginManager, get_plugin_manager, create_plugin_manager
from .router import PluginRouter, get_plugin_router, AccessDenied, PluginRecord
from .sandbox import run_in_sandbox
from .memory_manager import MemoryManager

__all__ = [
    "PluginManager",
    "get_plugin_manager", 
    "create_plugin_manager",
    "PluginRouter",
    "get_plugin_router",
    "PluginRecord",
    "AccessDenied",
    "run_in_sandbox",
    "MemoryManager",
]