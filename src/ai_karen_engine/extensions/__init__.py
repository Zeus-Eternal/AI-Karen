"""
Extensions Services Domain

This domain contains all services related to extension management, execution, and orchestration.
The extension system is now organized into:
- platform: Extension platform framework (host, registry, integration, API routes)
- plugins: User/community plugin packages
- system_extensions: Built-in system extension packages
- runtime: Engine-facing runtime behavior (loader, executor, auth, permissions, etc.)
"""

from .runtime.extension_registry import ExtensionRegistry
from .runtime.extension_loader import ExtensionLoader
from .runtime.extension_executor import ExtensionExecutor
from .runtime.extension_monitor import ExtensionMonitor
from .runtime.extension_config import ExtensionConfig
from .runtime.extension_auth import ExtensionAuth
from .runtime.extension_permissions import ExtensionPermissions
from .runtime.extension_rbac import ExtensionRBAC
from .runtime.extension_marketplace import ExtensionMarketplace
from .runtime.extension_api import ExtensionApi
from .runtime.extension_health_monitor import ExtensionHealthMonitor
from .runtime.extension_error_recovery import ExtensionErrorRecovery
from .runtime.extension_tenant_access import ExtensionTenantAccess
from .runtime.extension_environment_config import ExtensionEnvironmentConfig
from .runtime.extension_config_validator import ExtensionConfigValidator
from .runtime.extension_config_hot_reload import ExtensionConfigHotReload
from .runtime.extension_config_integration import ExtensionConfigIntegration
from .runtime.extension_alerting_system import ExtensionAlertingSystem

__all__ = [
    "ExtensionRegistry",
    "ExtensionLoader",
    "ExtensionExecutor",
    "ExtensionMonitor",
    "ExtensionConfig",
    "ExtensionAuth",
    "ExtensionPermissions",
    "ExtensionRBAC",
    "ExtensionMarketplace",
    "ExtensionApi",
    "ExtensionHealthMonitor",
    "ExtensionErrorRecovery",
    "ExtensionTenantAccess",
    "ExtensionEnvironmentConfig",
    "ExtensionConfigValidator",
    "ExtensionConfigHotReload",
    "ExtensionConfigIntegration",
    "ExtensionAlertingSystem",
]
