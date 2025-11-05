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
"""

# Import ExtensionManager class directly
from ai_karen_engine.extensions.manager import ExtensionManager
from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.extensions.models import ExtensionManifest, ExtensionRecord, ExtensionStatus
from ai_karen_engine.extensions.registry import ExtensionRegistry
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
    get_extension_manager,
    get_extension_registry,
    get_marketplace_client,
    initialize_extensions_for_production,
)

# Legacy compatibility functions (now use factory)
def initialize_extension_manager():
    """Legacy function - now uses factory."""
    return initialize_extensions_for_production()

__all__ = [
    # Core classes
    "ExtensionManager",
    "BaseExtension",
    "ExtensionManifest",
    "ExtensionRecord",
    "ExtensionStatus",
    "ExtensionRegistry",
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
    # Factory
    "ExtensionServiceConfig",
    "ExtensionServiceFactory",
    "get_extension_service_factory",
    # Factory convenience functions
    "get_extension_manager",
    "get_extension_registry",
    "get_marketplace_client",
    "initialize_extension_manager",
    "initialize_extensions_for_production",
]