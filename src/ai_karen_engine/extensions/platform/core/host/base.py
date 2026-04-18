"""
Base classes and interfaces for the KARI extension system.

This module defines the core abstractions that all extensions must implement.
Import types from unified manifest for consistency.
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

# Import types from unified manifest
from ai_karen_engine.extensions.platform.core.manifest import (
    ExtensionManifest,
    ExtensionContext,
    ExtensionConfigSchema,
    ExtensionPermissions,
    ExtensionRBAC,
    ExtensionRole,
    ExtensionPromptFiles,
    HookPoint,
    Permission,
    HookContext,
)


class ExtensionError(Exception):
    """Base exception for extension-related errors."""

    pass


class ExtensionLoadError(ExtensionError):
    """Exception raised when an extension fails to load."""

    pass


class ExtensionValidationError(ExtensionError):
    """Exception raised when an extension fails validation."""

    pass


class ExtensionExecutionError(ExtensionError):
    """Exception raised when an extension fails during execution."""

    pass


class ExtensionTimeoutError(ExtensionError):
    """Exception raised when an extension execution times out."""

    pass


class ExtensionBase(ABC):
    """Base class that all KARI extensions must inherit from."""

    def __init__(self, manifest: ExtensionManifest, context: ExtensionContext):
        """Initialize the extension with its manifest and context."""
        self.manifest = manifest
        self.context = context
        self.logger = logging.getLogger(f"extension.{manifest.name}")
        self._is_initialized = False
        self._is_shutdown = False
        self.enabled = manifest.rbac.default_enabled

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the extension.

        This method is called when the extension is loaded.
        It should set up any resources needed by the extension.
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Shutdown the extension.

        This method is called when the extension is unloaded.
        It should clean up any resources created by the extension.
        """
        pass

    @abstractmethod
    async def execute_hook(
        self, hook_point: HookPoint, context: HookContext
    ) -> Dict[str, Any]:
        """
        Execute a hook point.

        Args:
            hook_point: The hook point being executed
            context: The hook context containing data and user context

        Returns:
            A dictionary containing the result of the hook execution
        """
        pass

    async def _initialize(self) -> None:
        """Internal initialization method that sets up the extension."""
        try:
            await self.initialize()
            self._is_initialized = True
            self.logger.info(f"Extension {self.manifest.name} initialized successfully")
        except Exception as e:
            self.logger.error(
                f"Failed to initialize extension {self.manifest.name}: {e}"
            )
            raise ExtensionLoadError(f"Failed to initialize extension: {e}") from e

    async def _shutdown(self) -> None:
        """Internal shutdown method that cleans up the extension."""
        try:
            await self.shutdown()
            self._is_shutdown = True
            self.logger.info(f"Extension {self.manifest.name} shut down successfully")
        except Exception as e:
            self.logger.error(f"Failed to shutdown extension {self.manifest.name}: {e}")
            raise ExtensionError(f"Failed to shutdown extension: {e}") from e

    def is_initialized(self) -> bool:
        """Check if the extension has been initialized."""
        return self._is_initialized

    def is_shutdown(self) -> bool:
        """Check if the extension has been shut down."""
        return self._is_shutdown

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the extension."""
        return {
            "name": self.manifest.name,
            "version": self.manifest.version,
            "initialized": self._is_initialized,
            "shutdown": self._is_shutdown,
            "hook_points": [hp.value for hp in self.manifest.hook_points],
        }

    def has_permission(self, permission: Permission) -> bool:
        """Check if the extension has a specific permission."""
        if permission == Permission.MEMORY_READ:
            return self.manifest.permissions.memory_read
        elif permission == Permission.MEMORY_WRITE:
            return self.manifest.permissions.memory_write
        elif permission == Permission.TOOL_ACCESS:
            return len(self.manifest.permissions.tools) > 0
        elif permission == Permission.USER_DATA_READ:
            return self.manifest.permissions.user_data_read
        elif permission == Permission.USER_DATA_WRITE:
            return self.manifest.permissions.user_data_write
        elif permission == Permission.SYSTEM_CONFIG_READ:
            return self.manifest.permissions.system_config_read
        elif permission == Permission.SYSTEM_CONFIG_WRITE:
            return self.manifest.permissions.system_config_write
        return False

    def can_access_tool(self, tool_name: str) -> bool:
        """Check if the extension can access a specific tool."""
        return tool_name in self.manifest.permissions.tools

    def is_role_allowed(self, role: ExtensionRole) -> bool:
        """Check if the extension allows a specific role."""
        return role in self.manifest.rbac.allowed_roles

    def is_enabled_by_default(self) -> bool:
        """Check if the extension is enabled by default."""
        return self.manifest.rbac.default_enabled

    def supports_hook_point(self, hook_point: HookPoint) -> bool:
        """Check if the extension supports a specific hook point."""
        return hook_point in self.manifest.hook_points


# Type aliases
HookHandler = Callable[..., Awaitable[Any]]
MaybeAsyncFn = Union[Callable[..., Any], Callable[..., Awaitable[Any]]]


__all__ = [
    "ExtensionBase",
    "HookPoint",
    "Permission",
    "ExtensionRole",
    "ExtensionContext",
    "ExtensionConfigSchema",
    "ExtensionPermissions",
    "ExtensionRBAC",
    "ExtensionPromptFiles",
    "ExtensionManifest",
    "ExtensionError",
    "ExtensionLoadError",
    "ExtensionValidationError",
    "ExtensionExecutionError",
    "ExtensionTimeoutError",
    "HookContext",
    "HookHandler",
    "MaybeAsyncFn",
]
