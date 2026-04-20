"""
Unified Extension System

This module provides a unified extension system that consolidates the best features
from both platform/core and runtime systems, eliminating duplication and providing
a single source of truth for extension management.
"""

from .core import (
    ExtensionRegistry,
    ExtensionLoader,
    ExtensionPermissions,
    ExtensionPermissionType,
    ExtensionHealthMonitor,
    HealthStatus,
    HealthSeverity,
    ExtensionLifecycleManager,
    ExtensionLifecycleState,
    ExtensionConfig,
    ExtensionConfigManager,
    ExtensionService,
    ExtensionServiceResult,
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
    "ExtensionConfig",
    "ExtensionConfigManager",
    "ExtensionService",
    "ExtensionServiceResult",
    "ExtensionExecutionSubstrate",
    "ExecutionRequest",
    "ExecutionResult",
    "ExecutionStatus",
]
