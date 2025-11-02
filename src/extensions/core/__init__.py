"""
Extension Framework Core Module

This module contains the core framework code for the extension system.
It provides the base classes, managers, and utilities needed to build
and manage extensions.

Key Components:
- BaseExtension: Base class for all extensions
- ExtensionManager: Manages extension lifecycle
- ExtensionRegistry: Registry for tracking loaded extensions
- ExtensionModels: Data models for extensions
- Security: Security framework for extensions
- API Integration: FastAPI integration utilities
- Background Tasks: Background task support
"""

# Import models first (no external dependencies)
from .models import (
    ExtensionManifest,
    ExtensionRecord,
    ExtensionStatus,
    ExtensionContext,
    ExtensionCapabilities,
    ExtensionDependencies,
    ExtensionPermissions,
    ExtensionResources,
    ExtensionRegistryEntry
)

# Import other components with graceful error handling
try:
    from .base import BaseExtension
except ImportError as e:
    BaseExtension = None
    print(f"Warning: Could not import BaseExtension: {e}")

try:
    from .manager import ExtensionManager
except ImportError as e:
    ExtensionManager = None
    print(f"Warning: Could not import ExtensionManager: {e}")

try:
    from .registry import ExtensionRegistry
except ImportError as e:
    ExtensionRegistry = None
    print(f"Warning: Could not import ExtensionRegistry: {e}")

try:
    from .api_integration import ExtensionAPIIntegration
except ImportError as e:
    ExtensionAPIIntegration = None
    print(f"Warning: Could not import ExtensionAPIIntegration: {e}")

try:
    from .background_tasks import BackgroundTaskManager
except ImportError as e:
    BackgroundTaskManager = None
    print(f"Warning: Could not import BackgroundTaskManager: {e}")

try:
    from .security import ExtensionSecurityManager
except ImportError as e:
    ExtensionSecurityManager = None
    print(f"Warning: Could not import ExtensionSecurityManager: {e}")

try:
    from .security_decorators import require_permission, audit_log, security_monitor
except ImportError as e:
    require_permission = audit_log = security_monitor = None
    print(f"Warning: Could not import security decorators: {e}")

__all__ = [
    'BaseExtension',
    'ExtensionManager', 
    'ExtensionRegistry',
    'ExtensionManifest',
    'ExtensionRecord',
    'ExtensionStatus',
    'ExtensionContext',
    'ExtensionCapabilities',
    'ExtensionDependencies',
    'ExtensionPermissions',
    'ExtensionResources',
    'ExtensionRegistryEntry',
    'ExtensionAPIIntegration',
    'BackgroundTaskManager',
    'ExtensionSecurityManager',
    'require_permission',
    'audit_log',
    'security_monitor'
]