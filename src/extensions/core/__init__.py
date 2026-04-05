"""Unified extension core exports with a lazy package surface."""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "ExtensionCoreManager",
    "PluginManager",
    "PluginOrchestrator",
    "PluginRouter",
    "PluginStatus",
    "create_plugin_manager",
    "get_extension_core_manager",
    "get_plugin_manager",
    "get_plugin_orchestrator",
    "get_plugin_router",
    "get_registry",
]


def __getattr__(name: str):
    if name == "ExtensionCoreManager":
        return import_module("extensions.core.manager").ExtensionCoreManager
    if name == "get_extension_core_manager":
        return import_module("extensions.core.manager").get_extension_core_manager
    if name in {"PluginStatus", "get_registry"}:
        registry_module = import_module("extensions.core.registry.plugin_registry")
        return getattr(registry_module, name)
    if name in {"PluginRouter", "get_plugin_router"}:
        router_module = import_module("extensions.core.host.router")
        return getattr(router_module, name)
    if name in {"PluginManager", "get_plugin_manager"}:
        manager_module = import_module("extensions.core.integration.manager")
        return getattr(manager_module, name)
    if name in {"PluginOrchestrator", "get_plugin_orchestrator"}:
        orchestrator_module = import_module("extensions.core.integration.orchestrator")
        if name == "get_plugin_orchestrator":
            return orchestrator_module.get_plugin_orchestrator
        return orchestrator_module.PluginOrchestrator
    if name == "create_plugin_manager":
        return lambda: import_module("extensions.core.integration.manager").PluginManager()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
