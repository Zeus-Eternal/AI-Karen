"""
Unified Extension System Core

This module provides the core components for the unified extension system,
consolidating the best features from both platform/core and runtime systems.
"""

from .extension_registry import ExtensionRegistry
from .extension_loader import ExtensionLoader
from .extension_permissions import ExtensionPermissions, ExtensionPermissionType
from .extension_health_monitor import (
    ExtensionHealthMonitor,
    HealthStatus,
    HealthSeverity,
)
from .extension_lifecycle_manager import (
    ExtensionLifecycleManager,
    ExtensionLifecycleState,
)
from .extension_config import ExtensionConfigManager, ExtensionConfig
from .extension_service import ExtensionService, ExtensionServiceResult
from .execution_substrate import (
    ExtensionExecutionSubstrate,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
)

__all__ = [
    "ExtensionRegistry",
    "ExtensionLoader",
    "ExtensionPermissions",
    "ExtensionPermissionType",
    "ExtensionHealthMonitor",
    "HealthStatus",
    "HealthSeverity",
    "ExtensionLifecycleManager",
    "ExtensionLifecycleState",
    "ExtensionConfigManager",
    "ExtensionConfig",
    "ExtensionService",
    "ExtensionServiceResult",
    "ExtensionExecutionSubstrate",
    "ExecutionRequest",
    "ExecutionResult",
    "ExecutionStatus",
]
