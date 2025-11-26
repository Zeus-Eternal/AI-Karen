"""
Kari AI Extensions System

The Extensions system provides a higher-level architecture above Kari's plugin system,
enabling developers to build substantial, feature-rich modules that can compose multiple
plugins, provide rich UIs, manage their own data, and be distributed through a marketplace.

Production-ready with:
- Comprehensive factory for centralized initialization
- Resource monitoring and health checks
- Marketplace integration
- Dependency resolution
- Workflow orchestration

LEGACY NOTICE: This module is being migrated to the new two-tier architecture.
New code should import from ai_karen_engine.extension_host instead.
"""

# Import ExtensionManager class from new extension_host
from ai_karen_engine.extension_host import ExtensionManager, get_extension_manager, initialize_extension_manager
from ai_karen_engine.extension_host import (
    ExtensionBase as BaseExtension,
    ExtensionManifest,
    ExtensionContext,
    HookPoint,
    HookContext,
    ExtensionRole,
    Permission,
    ExtensionConfigManager,
    ExtensionHostConfig,
    ExtensionLoader,
    ExtensionRegistry,
    ExtensionRunner,
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

# Legacy imports for backward compatibility
try:
    from ai_karen_engine.extensions.orchestrator import PluginOrchestrator
    from ai_karen_engine.extensions.data_manager import ExtensionDataManager
    from ai_karen_engine.extensions.validator import ExtensionValidator, validate_extension_manifest
    from ai_karen_engine.extensions.dependency_resolver import DependencyResolver
    from ai_karen_engine.extensions.resource_monitor import ResourceMonitor, ExtensionHealthChecker, HealthStatus
    from ai_karen_engine.extensions.marketplace_client import MarketplaceClient
    from ai_karen_engine.extensions.metrics_dashboard import MetricsDashboard
    
    # Import factory for centralized initialization
    from ai_karen_engine.extensions.factory import (
        ExtensionServiceConfig,
        ExtensionServiceFactory,
        get_extension_service_factory,
        get_extension_registry,
        get_marketplace_client,
        initialize_extensions_for_production,
    )
    
    # Legacy compatibility functions (now use factory)
    def initialize_extensions_legacy_system():
        """Legacy function - now uses factory."""
        return initialize_extensions_for_production()
    
    LEGACY_AVAILABLE = True
except ImportError:
    # Legacy components not available
    PluginOrchestrator = None
    ExtensionDataManager = None
    ExtensionValidator = None
    DependencyResolver = None
    ResourceMonitor = None
    ExtensionHealthChecker = None
    HealthStatus = None
    MarketplaceClient = None
    MetricsDashboard = None
    
    def initialize_extensions_legacy_system():
        """Legacy function not available."""
        raise RuntimeError("Legacy extension system components not available. Use initialize_extension_manager() instead.")
    
    LEGACY_AVAILABLE = False

# Define ExtensionRecord and ExtensionStatus for backward compatibility
from ai_karen_engine.extension_host.models import ExtensionRecord, ExtensionStatus

__all__ = [
    # Core classes from new architecture
    "ExtensionManager",
    "BaseExtension",
    "ExtensionManifest",
    "ExtensionContext",
    "HookPoint",
    "HookContext",
    "ExtensionRole",
    "Permission",
    "ExtensionConfigManager",
    "ExtensionHostConfig",
    "ExtensionLoader",
    "ExtensionRegistry",
    "ExtensionRunner",
    
    # Errors from new architecture
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
    
    # Legacy classes (if available)
    "ExtensionRecord",
    "ExtensionStatus",
    "PluginOrchestrator",
    "ExtensionDataManager",
    "ExtensionValidator",
    "validate_extension_manifest",
    "DependencyResolver",
    "ResourceMonitor",
    "ExtensionHealthChecker",
    "HealthStatus",
    "MarketplaceClient",
    "MetricsDashboard",
    
    # Factory (if available)
    "ExtensionServiceConfig",
    "ExtensionServiceFactory",
    "get_extension_service_factory",
    "get_extension_registry",
    "get_marketplace_client",
    "initialize_extensions_for_production",
    
    # Factory convenience functions
    "get_extension_manager",
    "initialize_extension_manager",
    "initialize_extensions_legacy_system",
    
    # Status flag
    "LEGACY_AVAILABLE",
]