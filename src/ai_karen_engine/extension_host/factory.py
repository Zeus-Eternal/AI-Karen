"""
Production Extensions Services Factory
Comprehensive factory for initializing and wiring the extensions system.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ExtensionServiceConfig:
    """Configuration for extension services."""

    def __init__(
        self,
        # Extension root directory
        extension_root: Optional[Path] = None,
        # Feature flags
        enable_marketplace: bool = True,
        enable_resource_monitoring: bool = True,
        enable_health_checks: bool = True,
        enable_dependency_resolution: bool = True,
        enable_workflow_engine: bool = True,
        enable_metrics_dashboard: bool = False,
        # Security settings
        require_signature_verification: bool = False,
        allow_unsigned_extensions: bool = True,
        sandbox_extensions: bool = False,
        # Resource limits
        max_memory_per_extension_mb: int = 512,
        max_cpu_percent_per_extension: int = 25,
        max_extensions: int = 100,
        # Auto-load settings
        auto_discover_on_init: bool = True,
        auto_load_extensions: bool = False,
    ):
        # Points to src/extensions/ (parent.parent of this file)
        self.extension_root = extension_root or (Path(__file__).parent.parent.parent / "extensions")

        self.enable_marketplace = enable_marketplace
        self.enable_resource_monitoring = enable_resource_monitoring
        self.enable_health_checks = enable_health_checks
        self.enable_dependency_resolution = enable_dependency_resolution
        self.enable_workflow_engine = enable_workflow_engine
        self.enable_metrics_dashboard = enable_metrics_dashboard

        self.require_signature_verification = require_signature_verification
        self.allow_unsigned_extensions = allow_unsigned_extensions
        self.sandbox_extensions = sandbox_extensions

        self.max_memory_per_extension_mb = max_memory_per_extension_mb
        self.max_cpu_percent_per_extension = max_cpu_percent_per_extension
        self.max_extensions = max_extensions

        self.auto_discover_on_init = auto_discover_on_init
        self.auto_load_extensions = auto_load_extensions


class ExtensionServiceFactory:
    """
    Factory for creating and wiring extension services.

    This factory ensures all extension services (manager, registry, marketplace, etc.)
    are properly initialized, configured, and wired together for production use.
    """

    def __init__(self, config: Optional[ExtensionServiceConfig] = None):
        self.config = config or ExtensionServiceConfig()
        self._services = {}
        logger.info("ExtensionServiceFactory initialized")

    def create_extension_registry(self):
        """Create and configure extension registry."""
        try:
            from ai_karen_engine.extensions.registry import ExtensionRegistry

            # Get plugin and service registries if available
            plugin_registry = None
            service_registry = None

            try:
                from ai_karen_engine.plugins.router import PluginRouter
                plugin_registry = PluginRouter()
            except Exception as e:
                logger.warning(f"Plugin registry not available: {e}")

            try:
                from ai_karen_engine.core.service_registry import get_service_registry
                service_registry = get_service_registry()
            except Exception as e:
                logger.warning(f"Service registry not available: {e}")

            registry = ExtensionRegistry(
                plugin_registry=plugin_registry,
                service_registry=service_registry
            )

            self._services["extension_registry"] = registry
            logger.info("Extension registry created successfully")
            return registry

        except Exception as e:
            logger.error(f"Failed to create extension registry: {e}")
            return None

    def create_extension_validator(self):
        """Create and configure extension validator."""
        try:
            from ai_karen_engine.extensions.validator import ExtensionValidator

            validator = ExtensionValidator(
                require_signature=self.config.require_signature_verification,
                allow_unsigned=self.config.allow_unsigned_extensions
            )

            self._services["extension_validator"] = validator
            logger.info("Extension validator created successfully")
            return validator

        except Exception as e:
            logger.error(f"Failed to create extension validator: {e}")
            return None

    def create_dependency_resolver(self):
        """Create and configure dependency resolver."""
        if not self.config.enable_dependency_resolution:
            logger.info("Dependency resolver disabled by configuration")
            return None

        try:
            from ai_karen_engine.extensions.dependency_resolver import DependencyResolver

            resolver = DependencyResolver()

            self._services["dependency_resolver"] = resolver
            logger.info("Dependency resolver created successfully")
            return resolver

        except Exception as e:
            logger.error(f"Failed to create dependency resolver: {e}")
            return None

    def create_resource_monitor(self):
        """Create and configure resource monitor."""
        if not self.config.enable_resource_monitoring:
            logger.info("Resource monitor disabled by configuration")
            return None

        try:
            from ai_karen_engine.extensions.resource_monitor import ResourceMonitor

            monitor = ResourceMonitor(
                max_memory_mb=self.config.max_memory_per_extension_mb,
                max_cpu_percent=self.config.max_cpu_percent_per_extension
            )

            self._services["resource_monitor"] = monitor
            logger.info("Resource monitor created successfully")
            return monitor

        except Exception as e:
            logger.error(f"Failed to create resource monitor: {e}")
            return None

    def create_health_checker(self):
        """Create and configure health checker."""
        if not self.config.enable_health_checks:
            logger.info("Health checker disabled by configuration")
            return None

        try:
            from ai_karen_engine.extensions.resource_monitor import ExtensionHealthChecker

            # Get or create resource monitor
            resource_monitor = self.get_service("resource_monitor")
            if not resource_monitor:
                resource_monitor = self.create_resource_monitor()

            if not resource_monitor:
                logger.warning("Cannot create health checker without resource monitor")
                return None

            health_checker = ExtensionHealthChecker(resource_monitor)

            self._services["health_checker"] = health_checker
            logger.info("Health checker created successfully")
            return health_checker

        except Exception as e:
            logger.error(f"Failed to create health checker: {e}")
            return None

    def create_marketplace_client(self):
        """Create and configure marketplace client."""
        if not self.config.enable_marketplace:
            logger.info("Marketplace client disabled by configuration")
            return None

        try:
            from ai_karen_engine.extensions.marketplace_client import MarketplaceClient

            client = MarketplaceClient()

            self._services["marketplace_client"] = client
            logger.info("Marketplace client created successfully")
            return client

        except Exception as e:
            logger.error(f"Failed to create marketplace client: {e}")
            return None

    def create_workflow_engine(self):
        """Create and configure workflow engine."""
        if not self.config.enable_workflow_engine:
            logger.info("Workflow engine disabled by configuration")
            return None

        try:
            from ai_karen_engine.extensions.workflow_engine import WorkflowEngine

            engine = WorkflowEngine()

            self._services["workflow_engine"] = engine
            logger.info("Workflow engine created successfully")
            return engine

        except Exception as e:
            logger.error(f"Failed to create workflow engine: {e}")
            return None

    def create_plugin_orchestrator(self):
        """Create and configure plugin orchestrator."""
        try:
            from ai_karen_engine.extensions.orchestrator import PluginOrchestrator
            from ai_karen_engine.plugins.router import PluginRouter

            # Get or create plugin router
            try:
                plugin_router = PluginRouter()
            except Exception as e:
                logger.error(f"Failed to create plugin router: {e}")
                return None

            orchestrator = PluginOrchestrator(plugin_router=plugin_router)

            self._services["plugin_orchestrator"] = orchestrator
            logger.info("Plugin orchestrator created successfully")
            return orchestrator

        except Exception as e:
            logger.error(f"Failed to create plugin orchestrator: {e}")
            return None

    def create_metrics_dashboard(self):
        """Create and configure metrics dashboard."""
        if not self.config.enable_metrics_dashboard:
            logger.info("Metrics dashboard disabled by configuration")
            return None

        try:
            from ai_karen_engine.extensions.metrics_dashboard import MetricsDashboard

            dashboard = MetricsDashboard()

            self._services["metrics_dashboard"] = dashboard
            logger.info("Metrics dashboard created successfully")
            return dashboard

        except Exception as e:
            logger.error(f"Failed to create metrics dashboard: {e}")
            return None

    def create_extension_data_manager(self):
        """Create and configure extension data manager."""
        try:
            from ai_karen_engine.extensions.data_manager import ExtensionDataManager

            manager = ExtensionDataManager()

            self._services["extension_data_manager"] = manager
            logger.info("Extension data manager created successfully")
            return manager

        except Exception as e:
            logger.error(f"Failed to create extension data manager: {e}")
            return None

    def create_extension_manager(self):
        """
        Create and configure the main extension manager with all services wired.

        Returns:
            Fully configured ExtensionManager instance
        """
        logger.info("Creating extension manager with all services")

        try:
            from ai_karen_engine.extension_host.manager import ExtensionManager
            from ai_karen_engine.plugins.router import PluginRouter

            # Ensure extension root exists
            self.config.extension_root.mkdir(parents=True, exist_ok=True)

            # Get or create all dependent services
            registry = self.get_service("extension_registry") or self.create_extension_registry()
            validator = self.get_service("extension_validator") or self.create_extension_validator()
            dependency_resolver = self.get_service("dependency_resolver") or self.create_dependency_resolver()
            resource_monitor = self.get_service("resource_monitor") or self.create_resource_monitor()
            health_checker = self.get_service("health_checker") or self.create_health_checker()
            marketplace_client = self.get_service("marketplace_client") or self.create_marketplace_client()
            workflow_engine = self.get_service("workflow_engine") or self.create_workflow_engine()
            plugin_orchestrator = self.get_service("plugin_orchestrator") or self.create_plugin_orchestrator()
            data_manager = self.get_service("extension_data_manager") or self.create_extension_data_manager()

            # Get plugin router
            try:
                plugin_router = PluginRouter()
            except Exception as e:
                logger.error(f"Failed to create plugin router: {e}")
                return None

            # Create extension manager
            manager = ExtensionManager(
                extension_root=self.config.extension_root,
                plugin_router=plugin_router,
                marketplace_client=marketplace_client
            )

            # Wire in the services we created
            manager.registry = registry
            manager.validator = validator
            if dependency_resolver:
                manager.dependency_resolver = dependency_resolver
            if resource_monitor:
                manager.resource_monitor = resource_monitor
            if health_checker:
                manager.health_checker = health_checker

            self._services["extension_manager"] = manager

            # Auto-discover and load if configured
            if self.config.auto_discover_on_init:
                logger.info("Auto-discovering extensions...")
                try:
                    import asyncio
                    asyncio.create_task(manager.discover_extensions())
                except Exception as e:
                    logger.error(f"Failed to auto-discover extensions: {e}")

            logger.info("Extension manager created successfully with all services wired")
            return manager

        except Exception as e:
            logger.error(f"Failed to create extension manager: {e}")
            return None

    def create_all_services(self) -> Dict[str, Any]:
        """
        Create all extension services and wire them together.

        This is the main entry point for full extension system initialization.

        Returns:
            Dictionary of all created services
        """
        logger.info("Creating all extension services")

        # Create services in dependency order
        self.create_extension_registry()
        self.create_extension_validator()
        self.create_dependency_resolver()
        self.create_resource_monitor()
        self.create_health_checker()
        self.create_marketplace_client()
        self.create_workflow_engine()
        self.create_plugin_orchestrator()
        self.create_extension_data_manager()
        self.create_metrics_dashboard()

        # Finally, create the main extension manager
        self.create_extension_manager()

        logger.info(f"All extension services created: {list(self._services.keys())}")
        return self._services

    def get_service(self, service_name: str):
        """Get a service by name."""
        return self._services.get(service_name)

    def get_all_services(self) -> Dict[str, Any]:
        """Get all created services."""
        return self._services.copy()

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on extension services.

        Returns:
            Dictionary with health status of all services
        """
        health = {}

        # Check extension manager
        manager = self.get_service("extension_manager")
        if manager:
            try:
                health["extension_manager"] = {
                    "healthy": True,
                    "extension_count": manager.registry.get_extension_count() if manager.registry else 0
                }
            except Exception as e:
                health["extension_manager"] = {"healthy": False, "error": str(e)}

        # Check health checker
        health_checker = self.get_service("health_checker")
        if health_checker:
            health["health_checker"] = {"exists": True}

        # Check marketplace
        marketplace = self.get_service("marketplace_client")
        if marketplace:
            health["marketplace"] = {"exists": True}

        return health


# Global factory instance
_global_factory: Optional[ExtensionServiceFactory] = None


def get_extension_service_factory(config: Optional[ExtensionServiceConfig] = None) -> ExtensionServiceFactory:
    """
    Get or create global extension service factory.

    Args:
        config: Optional configuration for the factory

    Returns:
        ExtensionServiceFactory instance
    """
    global _global_factory

    if _global_factory is None:
        _global_factory = ExtensionServiceFactory(config)
        logger.info("Global extension service factory created")

    return _global_factory


def get_extension_manager():
    """Get or create global extension manager."""
    factory = get_extension_service_factory()
    manager = factory.get_service("extension_manager")

    if manager is None:
        manager = factory.create_extension_manager()

    return manager


def get_extension_registry():
    """Get or create global extension registry."""
    factory = get_extension_service_factory()
    registry = factory.get_service("extension_registry")

    if registry is None:
        registry = factory.create_extension_registry()

    return registry


def get_marketplace_client():
    """Get or create global marketplace client."""
    factory = get_extension_service_factory()
    client = factory.get_service("marketplace_client")

    if client is None:
        client = factory.create_marketplace_client()

    return client


def initialize_extensions_for_production(config: Optional[ExtensionServiceConfig] = None):
    """
    Initialize extensions system for production use.

    This is the main entry point for production extension initialization.
    Call this during application startup.

    Args:
        config: Optional configuration

    Returns:
        ExtensionManager instance
    """
    factory = get_extension_service_factory(config)
    factory.create_all_services()
    return factory.get_service("extension_manager")


__all__ = [
    "ExtensionServiceConfig",
    "ExtensionServiceFactory",
    "get_extension_service_factory",
    "get_extension_manager",
    "get_extension_registry",
    "get_marketplace_client",
    "initialize_extensions_for_production",
]
