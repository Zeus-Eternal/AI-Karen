"""
Unified Plugin Framework

This module provides a consolidated plugin system that merges the functionality
from the previous src/plugins and src/marketplace plugin frameworks.

The plugin system is designed for simple, focused functions that can be
executed in a sandboxed environment with proper security controls.
"""

from .core.manager import PluginManager, get_plugin_manager, create_plugin_manager
from .core.router import PluginRouter, get_plugin_router, AccessDenied, PluginRecord
from .core.sandbox import run_in_sandbox
from .core.memory_manager import MemoryManager

__all__ = [
    # Core plugin management
    "PluginManager",
    "get_plugin_manager", 
    "create_plugin_manager",
    
    # Plugin routing and discovery
    "PluginRouter",
    "get_plugin_router",
    "PluginRecord",
    "AccessDenied",
    
    # Sandbox execution
    "run_in_sandbox",
    
    # Memory management
    "MemoryManager",
]