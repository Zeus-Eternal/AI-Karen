"""Unified extension host exports with lazy runtime imports."""

from __future__ import annotations

from importlib import import_module

from extensions.core.host.base import (
    ExtensionBase,
    ExtensionContext,
    ExtensionManifest,
    HookContext,
    HookPoint,
)
from extensions.core.host.config import ExtensionConfigManager, ExtensionHostConfig
from extensions.core.host.loader import ExtensionLoader
from extensions.core.host.models import (
    ExtensionCapabilities,
    ExtensionPermissions,
    ExtensionRBAC,
    ExtensionRecord,
    ExtensionResources,
    ExtensionStatus,
)

__all__ = [
    "ExtensionBase",
    "ExtensionCapabilities",
    "ExtensionConfigManager",
    "ExtensionContext",
    "ExtensionHostConfig",
    "ExtensionLoader",
    "ExtensionManager",
    "ExtensionManifest",
    "ExtensionPermissions",
    "ExtensionRBAC",
    "ExtensionRecord",
    "ExtensionRegistry",
    "ExtensionResources",
    "ExtensionRunner",
    "ExtensionStatus",
    "HookContext",
    "HookPoint",
    "get_registry",
]


def __getattr__(name: str):
    if name == "ExtensionManager":
        return import_module("extensions.core.host.manager").ExtensionManager
    if name == "ExtensionRunner":
        return import_module("extensions.core.host.runner").ExtensionRunner
    if name in {"ExtensionRegistry", "get_registry"}:
        registry_module = import_module("extensions.core.host.registry")
        return getattr(registry_module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
