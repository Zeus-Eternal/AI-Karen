"""Compatibility model exports for the unified extension host."""

from ai_karen_engine.extensions.platform.core.host.base import (
    ExtensionBase,
    ExtensionConfigSchema,
    ExtensionContext,
    ExtensionManifest,
    ExtensionPermissions as HostExtensionPermissions,
    ExtensionPromptFiles,
    ExtensionRBAC,
    ExtensionRole,
    HookContext,
    HookPoint,
    Permission,
)
from ai_karen_engine.extensions.platform.core.registry.manifest import (
    ExtensionCapabilities,
    ExtensionDependencies,
    ExtensionManifestAPI,
    ExtensionPermissions,
    ExtensionRecord,
    ExtensionResources,
    ExtensionStatus,
    NAME_PATTERN,
)

__all__ = [
    "ExtensionBase",
    "ExtensionCapabilities",
    "ExtensionConfigSchema",
    "ExtensionContext",
    "ExtensionDependencies",
    "ExtensionManifest",
    "ExtensionManifestAPI",
    "ExtensionPermissions",
    "ExtensionPromptFiles",
    "ExtensionRBAC",
    "ExtensionRecord",
    "ExtensionResources",
    "ExtensionRole",
    "ExtensionStatus",
    "HookContext",
    "HookPoint",
    "HostExtensionPermissions",
    "NAME_PATTERN",
    "Permission",
]
