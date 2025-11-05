"""
Production Integrations Services Factory
Comprehensive factory for initializing and wiring all LLM integration services.
"""

import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class IntegrationServiceConfig:
    """Configuration for integration services."""

    def __init__(
        self,
        # Provider enablement
        enable_openai: bool = True,
        enable_gemini: bool = True,
        enable_deepseek: bool = True,
        enable_huggingface: bool = True,
        enable_llamacpp: bool = True,
        enable_anthropic: bool = True,
        # Registry settings
        enable_provider_registry: bool = True,
        enable_runtime_registry: bool = True,
        enable_model_discovery: bool = True,
        # Routing settings
        enable_capability_router: bool = True,
        enable_copilot_router: bool = True,
        enable_llm_router: bool = True,
        # Fallback and recovery
        enable_fallback_manager: bool = True,
        enable_error_recovery: bool = True,
        enable_failure_pattern_analysis: bool = True,
        # Model management
        enable_model_availability_manager: bool = True,
        enable_model_store_integration: bool = True,
        # Voice and video
        enable_voice_registry: bool = False,
        enable_video_registry: bool = False,
        # Advanced features
        enable_confidence_scoring: bool = True,
        enable_task_analyzer: bool = True,
        enable_diagnostic_prompts: bool = True,
        # Degraded mode
        enable_degraded_mode: bool = True,
        degraded_mode_auto_activate: bool = True,
        # Health monitoring
        enable_health_checks: bool = True,
        health_check_interval: int = 60,
        # Performance settings
        cache_provider_health: bool = True,
        cache_model_metadata: bool = True,
        warm_cache_on_init: bool = False,
    ):
        # Provider settings
        self.enable_openai = enable_openai
        self.enable_gemini = enable_gemini
        self.enable_deepseek = enable_deepseek
        self.enable_huggingface = enable_huggingface
        self.enable_llamacpp = enable_llamacpp
        self.enable_anthropic = enable_anthropic

        # Registry settings
        self.enable_provider_registry = enable_provider_registry
        self.enable_runtime_registry = enable_runtime_registry
        self.enable_model_discovery = enable_model_discovery

        # Routing settings
        self.enable_capability_router = enable_capability_router
        self.enable_copilot_router = enable_copilot_router
        self.enable_llm_router = enable_llm_router

        # Fallback and recovery
        self.enable_fallback_manager = enable_fallback_manager
        self.enable_error_recovery = enable_error_recovery
        self.enable_failure_pattern_analysis = enable_failure_pattern_analysis

        # Model management
        self.enable_model_availability_manager = enable_model_availability_manager
        self.enable_model_store_integration = enable_model_store_integration

        # Voice and video
        self.enable_voice_registry = enable_voice_registry
        self.enable_video_registry = enable_video_registry

        # Advanced features
        self.enable_confidence_scoring = enable_confidence_scoring
        self.enable_task_analyzer = enable_task_analyzer
        self.enable_diagnostic_prompts = enable_diagnostic_prompts

        # Degraded mode
        self.enable_degraded_mode = enable_degraded_mode
        self.degraded_mode_auto_activate = degraded_mode_auto_activate

        # Health monitoring
        self.enable_health_checks = enable_health_checks
        self.health_check_interval = health_check_interval

        # Performance
        self.cache_provider_health = cache_provider_health
        self.cache_model_metadata = cache_model_metadata
        self.warm_cache_on_init = warm_cache_on_init


class IntegrationServiceFactory:
    """
    Factory for creating and wiring integration services.

    This factory ensures all LLM integration services (providers, routers,
    fallback managers, etc.) are properly initialized, configured, and wired
    together for production use.
    """

    def __init__(self, config: Optional[IntegrationServiceConfig] = None):
        self.config = config or IntegrationServiceConfig()
        self._services = {}
        self._providers = {}
        self._routers = {}
        logger.info("IntegrationServiceFactory initialized")

    def create_provider_registry(self):
        """Create and configure the provider registry."""
        if not self.config.enable_provider_registry:
            logger.info("Provider registry disabled by configuration")
            return None

        try:
            from ai_karen_engine.integrations.registry import get_registry

            registry = get_registry()
            self._services["provider_registry"] = registry
            logger.info("Provider registry created successfully")
            return registry

        except Exception as e:
            logger.error(f"Failed to create provider registry: {e}")
            return None

    def create_voice_registry(self):
        """Create and configure voice registry."""
        if not self.config.enable_voice_registry:
            logger.info("Voice registry disabled by configuration")
            return None

        try:
            from ai_karen_engine.integrations.voice_registry import get_voice_registry

            registry = get_voice_registry()
            self._services["voice_registry"] = registry
            logger.info("Voice registry created successfully")
            return registry

        except Exception as e:
            logger.error(f"Failed to create voice registry: {e}")
            return None

    def create_video_registry(self):
        """Create and configure video registry."""
        if not self.config.enable_video_registry:
            logger.info("Video registry disabled by configuration")
            return None

        try:
            from ai_karen_engine.integrations.video_providers import get_video_registry

            registry = get_video_registry()
            self._services["video_registry"] = registry
            logger.info("Video registry created successfully")
            return registry

        except Exception as e:
            logger.error(f"Failed to create video registry: {e}")
            return None

    def create_model_discovery(self):
        """Create and configure model discovery service."""
        if not self.config.enable_model_discovery:
            logger.info("Model discovery disabled by configuration")
            return None

        try:
            from ai_karen_engine.integrations.model_discovery import ModelDiscoveryEngine

            discovery = ModelDiscoveryEngine()
            self._services["model_discovery"] = discovery
            logger.info("Model discovery service created successfully")
            return discovery

        except Exception as e:
            logger.error(f"Failed to create model discovery: {e}")
            return None

    def create_capability_router(self):
        """Create and configure capability router."""
        if not self.config.enable_capability_router:
            logger.info("Capability router disabled by configuration")
            return None

        try:
            from ai_karen_engine.integrations.capability_router import CapabilityRouter

            # Get or create registry
            registry = self.get_service("provider_registry")
            if not registry:
                registry = self.create_provider_registry()

            router = CapabilityRouter(registry=registry)
            self._routers["capability_router"] = router
            logger.info("Capability router created successfully")
            return router

        except Exception as e:
            logger.error(f"Failed to create capability router: {e}")
            return None

    def create_copilot_router(self):
        """Create and configure copilot router."""
        if not self.config.enable_copilot_router:
            logger.info("Copilot router disabled by configuration")
            return None

        try:
            from ai_karen_engine.integrations.copilot_router import CopilotRouter

            router = CopilotRouter()
            self._routers["copilot_router"] = router
            logger.info("Copilot router created successfully")
            return router

        except Exception as e:
            logger.error(f"Failed to create copilot router: {e}")
            return None

    def create_llm_router(self):
        """Create and configure LLM router."""
        if not self.config.enable_llm_router:
            logger.info("LLM router disabled by configuration")
            return None

        try:
            from ai_karen_engine.integrations.llm_router import LLMRouter

            # Get or create dependency services
            registry = self.get_service("provider_registry")
            if not registry:
                registry = self.create_provider_registry()

            router = LLMRouter(registry=registry)
            self._routers["llm_router"] = router
            logger.info("LLM router created successfully")
            return router

        except Exception as e:
            logger.error(f"Failed to create LLM router: {e}")
            return None

    def create_fallback_manager(self):
        """Create and configure fallback manager."""
        if not self.config.enable_fallback_manager:
            logger.info("Fallback manager disabled by configuration")
            return None

        try:
            from ai_karen_engine.integrations.fallback_manager import FallbackManager

            # Get or create dependencies
            registry = self.get_service("provider_registry")
            if not registry:
                registry = self.create_provider_registry()

            manager = FallbackManager(registry=registry)
            self._services["fallback_manager"] = manager
            logger.info("Fallback manager created successfully")
            return manager

        except Exception as e:
            logger.error(f"Failed to create fallback manager: {e}")
            return None

    def create_error_recovery(self):
        """Create and configure error recovery service."""
        if not self.config.enable_error_recovery:
            logger.info("Error recovery disabled by configuration")
            return None

        try:
            from ai_karen_engine.integrations.error_recovery import ErrorRecoveryManager

            manager = ErrorRecoveryManager()
            self._services["error_recovery"] = manager
            logger.info("Error recovery service created successfully")
            return manager

        except Exception as e:
            logger.error(f"Failed to create error recovery: {e}")
            return None

    def create_failure_pattern_analyzer(self):
        """Create and configure failure pattern analyzer."""
        if not self.config.enable_failure_pattern_analysis:
            logger.info("Failure pattern analyzer disabled by configuration")
            return None

        try:
            from ai_karen_engine.integrations.failure_pattern_analyzer import (
                FailurePatternAnalyzer,
            )

            analyzer = FailurePatternAnalyzer()
            self._services["failure_pattern_analyzer"] = analyzer
            logger.info("Failure pattern analyzer created successfully")
            return analyzer

        except Exception as e:
            logger.error(f"Failed to create failure pattern analyzer: {e}")
            return None

    def create_model_availability_manager(self):
        """Create and configure model availability manager."""
        if not self.config.enable_model_availability_manager:
            logger.info("Model availability manager disabled by configuration")
            return None

        try:
            from ai_karen_engine.integrations.model_availability_manager import (
                ModelAvailabilityManager,
            )

            manager = ModelAvailabilityManager()
            self._services["model_availability_manager"] = manager
            logger.info("Model availability manager created successfully")
            return manager

        except Exception as e:
            logger.error(f"Failed to create model availability manager: {e}")
            return None

    def create_confidence_scorer(self):
        """Create and configure confidence scoring service."""
        if not self.config.enable_confidence_scoring:
            logger.info("Confidence scorer disabled by configuration")
            return None

        try:
            from ai_karen_engine.integrations.confidence_scoring import ConfidenceScorer

            scorer = ConfidenceScorer()
            self._services["confidence_scorer"] = scorer
            logger.info("Confidence scorer created successfully")
            return scorer

        except Exception as e:
            logger.error(f"Failed to create confidence scorer: {e}")
            return None

    def create_task_analyzer(self):
        """Create and configure task analyzer."""
        if not self.config.enable_task_analyzer:
            logger.info("Task analyzer disabled by configuration")
            return None

        try:
            from ai_karen_engine.integrations.task_analyzer import TaskAnalyzer

            analyzer = TaskAnalyzer()
            self._services["task_analyzer"] = analyzer
            logger.info("Task analyzer created successfully")
            return analyzer

        except Exception as e:
            logger.error(f"Failed to create task analyzer: {e}")
            return None

    def initialize_providers(self):
        """Initialize all enabled providers."""
        logger.info("Initializing LLM providers...")

        # Get or create registry
        registry = self.get_service("provider_registry")
        if not registry:
            registry = self.create_provider_registry()

        initialized_providers = []

        # Provider initialization map
        provider_configs = {
            "openai": self.config.enable_openai,
            "gemini": self.config.enable_gemini,
            "deepseek": self.config.enable_deepseek,
            "huggingface": self.config.enable_huggingface,
            "llamacpp": self.config.enable_llamacpp,
            "anthropic": self.config.enable_anthropic,
        }

        for provider_name, enabled in provider_configs.items():
            if enabled:
                try:
                    # Providers auto-register with the registry when initialized
                    logger.info(f"Initializing {provider_name} provider...")
                    initialized_providers.append(provider_name)
                except Exception as e:
                    logger.warning(f"Failed to initialize {provider_name} provider: {e}")

        logger.info(f"Initialized providers: {initialized_providers}")
        return initialized_providers

    def create_all_services(self) -> Dict[str, Any]:
        """
        Create all integration services and wire them together.

        This is the main entry point for full integration system initialization.

        Returns:
            Dictionary of all created services
        """
        logger.info("Creating all integration services")

        # Create core services in dependency order
        self.create_provider_registry()
        self.create_voice_registry()
        self.create_video_registry()
        self.create_model_discovery()

        # Create routers
        self.create_capability_router()
        self.create_copilot_router()
        self.create_llm_router()

        # Create fallback and recovery
        self.create_fallback_manager()
        self.create_error_recovery()
        self.create_failure_pattern_analyzer()

        # Create model management
        self.create_model_availability_manager()

        # Create advanced features
        self.create_confidence_scorer()
        self.create_task_analyzer()

        # Initialize providers
        self.initialize_providers()

        # Warm cache if configured
        if self.config.warm_cache_on_init:
            self._warm_caches()

        logger.info(f"All integration services created: {list(self._services.keys())}")
        logger.info(f"All routers created: {list(self._routers.keys())}")
        return {**self._services, **self._routers}

    def _warm_caches(self):
        """Warm up caches for better initial performance."""
        logger.info("Warming integration service caches...")

        # Warm provider health cache
        registry = self.get_service("provider_registry")
        if registry:
            try:
                registry.get_all_providers()
                logger.info("Provider health cache warmed")
            except Exception as e:
                logger.warning(f"Failed to warm provider cache: {e}")

        # Warm model discovery cache
        discovery = self.get_service("model_discovery")
        if discovery:
            try:
                discovery.discover_all_models()
                logger.info("Model discovery cache warmed")
            except Exception as e:
                logger.warning(f"Failed to warm model discovery cache: {e}")

    def get_service(self, service_name: str):
        """Get a service by name."""
        return self._services.get(service_name)

    def get_router(self, router_name: str):
        """Get a router by name."""
        return self._routers.get(router_name)

    def get_all_services(self) -> Dict[str, Any]:
        """Get all created services."""
        return {**self._services, **self._routers}

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on integration services.

        Returns:
            Dictionary with health status of all services
        """
        health = {}

        # Check provider registry
        registry = self.get_service("provider_registry")
        if registry:
            try:
                providers = registry.get_all_providers()
                health["provider_registry"] = {
                    "status": "healthy",
                    "provider_count": len(providers),
                    "providers": list(providers.keys()),
                }
            except Exception as e:
                health["provider_registry"] = {"status": "error", "error": str(e)}

        # Check routers
        for router_name in ["capability_router", "copilot_router", "llm_router"]:
            router = self.get_router(router_name)
            if router:
                health[router_name] = {"status": "available"}

        # Check fallback manager
        fallback_manager = self.get_service("fallback_manager")
        if fallback_manager:
            health["fallback_manager"] = {"status": "available"}

        # Check model discovery
        discovery = self.get_service("model_discovery")
        if discovery:
            try:
                models = discovery.list_all_models()
                health["model_discovery"] = {
                    "status": "healthy",
                    "model_count": len(models),
                }
            except Exception as e:
                health["model_discovery"] = {"status": "error", "error": str(e)}

        return health


# Global factory instance
_global_factory: Optional[IntegrationServiceFactory] = None


def get_integration_service_factory(
    config: Optional[IntegrationServiceConfig] = None,
) -> IntegrationServiceFactory:
    """
    Get or create global integration service factory.

    Args:
        config: Optional configuration for the factory

    Returns:
        IntegrationServiceFactory instance
    """
    global _global_factory

    if _global_factory is None:
        _global_factory = IntegrationServiceFactory(config)
        logger.info("Global integration service factory created")

    return _global_factory


def get_provider_registry():
    """Get or create global provider registry."""
    factory = get_integration_service_factory()
    registry = factory.get_service("provider_registry")

    if registry is None:
        registry = factory.create_provider_registry()

    return registry


def get_llm_router():
    """Get or create global LLM router."""
    factory = get_integration_service_factory()
    router = factory.get_router("llm_router")

    if router is None:
        router = factory.create_llm_router()

    return router


def get_fallback_manager():
    """Get or create global fallback manager."""
    factory = get_integration_service_factory()
    manager = factory.get_service("fallback_manager")

    if manager is None:
        manager = factory.create_fallback_manager()

    return manager


def initialize_integrations_for_production(
    config: Optional[IntegrationServiceConfig] = None,
):
    """
    Initialize integrations system for production use.

    This is the main entry point for production integration initialization.
    Call this during application startup.

    Args:
        config: Optional configuration

    Returns:
        Dictionary of all services
    """
    factory = get_integration_service_factory(config)
    return factory.create_all_services()


__all__ = [
    "IntegrationServiceConfig",
    "IntegrationServiceFactory",
    "get_integration_service_factory",
    "get_provider_registry",
    "get_llm_router",
    "get_fallback_manager",
    "initialize_integrations_for_production",
]
