"""
Extension Host - Runtime, loader, runner, and registry for KARI's extension system.

This package contains the core machinery that loads, validates, registers, executes, and audits extensions.
It contains zero business logic and zero extension content - only the core runtime components.
"""

# Import base classes and interfaces
from .base import (
    ExtensionBase,
    ExtensionContext,
    ExtensionManifest,
    HookPoint,
    HookContext,
    ExtensionRole,
    Permission
)
from .config import ExtensionConfigManager, ExtensionHostConfig
from .errors import (
    ExtensionError,
    ExtensionLoadError,
    ExtensionValidationError,
    ExtensionExecutionError,
    ExtensionTimeoutError,
    ExtensionPermissionError,
    ExtensionRBACError,
    ExtensionManifestError,
    ExtensionHookError,
    ExtensionDependencyError,
    ExtensionConfigurationError,
    ExtensionSystemError,
    ExtensionRegistryError,
    ExtensionDiscoveryError,
    ExtensionNotFoundError
)
from .loader import ExtensionLoader
from .registry import ExtensionRegistry
from .runner import ExtensionRunner

# Import ExtensionManager and helper functions directly
from .manager import ExtensionManager, get_extension_manager, initialize_extension_manager

__all__ = [
    # Base classes and interfaces
    "ExtensionBase",
    "ExtensionContext",
    "ExtensionManifest",
    "HookPoint",
    "HookContext",
    "ExtensionRole",
    "Permission",
    
    # Configuration
    "ExtensionConfigManager",
    "ExtensionHostConfig",
    
    # Errors
    "ExtensionError",
    "ExtensionLoadError",
    "ExtensionValidationError",
    "ExtensionExecutionError",
    "ExtensionTimeoutError",
    "ExtensionPermissionError",
    "ExtensionRBACError",
    "ExtensionManifestError",
    "ExtensionHookError",
    "ExtensionDependencyError",
    "ExtensionConfigurationError",
    "ExtensionSystemError",
    "ExtensionRegistryError",
    "ExtensionDiscoveryError",
    "ExtensionNotFoundError",
    
    # Core components
    "ExtensionLoader",
    "ExtensionRegistry",
    "ExtensionRunner",
    "ExtensionManager",
    "get_extension_manager",
    "initialize_extension_manager",
]
