"""
Extensions Services Domain

This domain contains all services related to extension management, execution, and orchestration.
The extension system is now organized into:
- platform: Extension platform framework (host, registry, integration, API routes)
- plugins: User/community plugin packages
- system_extensions: Built-in system extension packages
- runtime: Engine-facing runtime behavior (loader, executor, auth, permissions, etc.)
"""

from .unified.core.extension_registry import ExtensionRegistry
from .unified.core.extension_loader import ExtensionLoader
from .unified.core.extension_config import ExtensionConfigManager
from .unified.core.extension_permissions import ExtensionPermissions
from .unified.core.extension_health_monitor import ExtensionHealthMonitor
from .unified.core.extension_lifecycle_manager import ExtensionLifecycleManager
from .unified.core.extension_service import ExtensionService
from .unified.core.execution_substrate import ExtensionExecutionSubstrate

__all__ = [
    "ExtensionRegistry",
    "ExtensionLoader",
    "ExtensionConfigManager",
    "ExtensionPermissions",
    "ExtensionHealthMonitor",
    "ExtensionLifecycleManager",
    "ExtensionService",
    "ExtensionExecutionSubstrate",
]
