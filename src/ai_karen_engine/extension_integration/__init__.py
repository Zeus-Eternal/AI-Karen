"""
Extensions Integration - Comprehensive extension lifecycle management for CoPilot system.

This package provides a complete extension integration system with:
- Extension discovery and registration mechanisms
- Extension loading and unloading with dependency resolution
- Extension sandboxing and security isolation
- Extension configuration management and validation
- Extension communication and inter-extension messaging
- Extension health monitoring and error recovery
- Extension versioning and update management
- Extension permissions and access control
- Extension metrics collection and performance monitoring
- Database models for persistence
- API routes for management
- Integration layer for coordination
"""

from .lifecycle_manager import ExtensionLifecycleManager
from .discovery_service import ExtensionDiscoveryService
from .sandbox_manager import ExtensionSandboxManager
from .communication_manager import ExtensionCommunicationManager
from .version_manager import ExtensionVersionManager
from .permissions_manager import ExtensionPermissionsManager
from .metrics_collector import ExtensionMetricsCollector
from .models import (
    ExtensionModel, ExtensionVersionModel, ExtensionMetricModel,
    ExtensionEventModel, ExtensionConfigModel, ExtensionState, ExtensionType,
    create_extension_tables, drop_extension_tables
)
from .api import router as extension_api_router
from .integration import (
    ExtensionIntegrationManager, get_integration_manager, set_integration_manager,
    get_lifecycle_manager, get_discovery_service, get_sandbox_manager,
    get_communication_manager, get_version_manager, get_permissions_manager,
    get_metrics_collector
)

__all__ = [
    # Core components
    "ExtensionLifecycleManager",
    "ExtensionDiscoveryService",
    "ExtensionSandboxManager",
    "ExtensionCommunicationManager",
    "ExtensionVersionManager",
    "ExtensionPermissionsManager",
    "ExtensionMetricsCollector",
    
    # Database models
    "ExtensionModel",
    "ExtensionVersionModel",
    "ExtensionMetricModel",
    "ExtensionEventModel",
    "ExtensionConfigModel",
    "ExtensionState",
    "ExtensionType",
    "create_extension_tables",
    "drop_extension_tables",
    
    # API
    "extension_api_router",
    
    # Integration
    "ExtensionIntegrationManager",
    "get_integration_manager",
    "set_integration_manager",
    "get_lifecycle_manager",
    "get_discovery_service",
    "get_sandbox_manager",
    "get_communication_manager",
    "get_version_manager",
    "get_permissions_manager",
    "get_metrics_collector",
]