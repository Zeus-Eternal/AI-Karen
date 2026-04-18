"""Unified extension integration exports with lazy admin/API imports."""

from __future__ import annotations

from importlib import import_module

ExtensionIntegrationManager = None
_integration_manager = None

__all__ = [
    "ExtensionIntegrationManager",
    "PluginManager",
    "extension_api_router",
    "get_integration_manager",
    "get_plugin_manager",
    "set_integration_manager",
]


def __getattr__(name: str):
    if name == "PluginManager":
        return import_module("extensions.core.integration.manager").PluginManager
    if name == "get_plugin_manager":
        return import_module("extensions.core.integration.manager").get_plugin_manager
    if name == "extension_api_router":
        return import_module("extensions.core.integration.api").router
    if name == "ExtensionIntegrationManager":
        return import_module("extensions.core.integration.manager").PluginManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def set_integration_manager(manager):
    global _integration_manager
    _integration_manager = manager


def get_integration_manager():
    if _integration_manager is not None:
        return _integration_manager
    return import_module("extensions.core.integration.manager").get_plugin_manager()
