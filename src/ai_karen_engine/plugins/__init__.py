"""
Plugin system for Kari AI.

This module provides the core plugin system functionality including
plugin discovery, routing, execution, and management.
"""

from ai_karen_engine.plugins.manager import PluginManager, get_plugin_manager
from ai_karen_engine.plugins.router import PluginRouter, PluginRecord, AccessDenied, get_plugin_router
from ai_karen_engine.plugins.sandbox_system import run_in_sandbox

__all__ = [
    "PluginManager",
    "PluginRouter",
    "PluginRecord", 
    "AccessDenied",
    "get_plugin_manager",
    "get_plugin_router",
    "run_in_sandbox",
]