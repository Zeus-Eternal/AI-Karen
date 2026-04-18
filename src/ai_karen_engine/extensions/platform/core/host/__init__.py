"""Unified extension host exports with lazy runtime imports."""

from __future__ import annotations

from importlib import import_module

from ai_karen_engine.extensions.platform.core.host.base import (
    ExtensionBase,
    ExtensionContext,
    ExtensionManifest,
    HookContext,
    HookPoint,
)
from ai_karen_engine.extensions.platform.core.host.config import ExtensionConfigManager, ExtensionHostConfig
from ai_karen_engine.extensions.platform.core.host.loader import ExtensionLoader
from ai_karen_engine.extensions.platform.core.host.models import (
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
