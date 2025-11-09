"""
Production Services Factory
Comprehensive factory for initializing and wiring all application services.
"""

import logging
from typing import Optional, Dict, Any, List
from functools import lru_cache

logger = logging.getLogger(__name__)


class ServicesConfig:
    """Configuration for all application services."""

    def __init__(
        self,
        # AI Services
        enable_ai_orchestrator: bool = True,
        enable_model_library: bool = True,
        enable_model_orchestrator: bool = True,
        enable_intelligent_router: bool = True,
        # Memory Services
        enable_memory_service: bool = True,
        enable_enhanced_memory: bool = True,
        enable_integrated_memory: bool = True,
        # NLP Services
        enable_nlp_manager: bool = True,
        enable_spacy: bool = True,
        enable_distilbert: bool = True,
        # Knowledge Services
        enable_knowledge_graph: bool = True,
        enable_knowledge_connectors: bool = True,
        # Analytics Services
        enable_analytics: bool = True,
        enable_analytics_dashboard: bool = True,
        enable_metrics: bool = True,
        # Plugin & Tool Services
        enable_plugin_service: bool = True,
        enable_tool_service: bool = True,
        # Database Services
        enable_database_health: bool = True,
        enable_database_optimization: bool = True,
        enable_database_query_cache: bool = True,
        # Auth & Security Services
        enable_production_auth: bool = True,
        enable_auth_utils: bool = True,
        enable_tenant_isolation: bool = True,
        # Cache Services
        enable_production_cache: bool = True,
        enable_smart_cache: bool = True,
        enable_integrated_cache: bool = True,
        # Monitoring Services
        enable_production_monitoring: bool = True,
        enable_performance_monitor: bool = True,
        enable_health_checker: bool = True,
        enable_slo_monitoring: bool = True,
        # Error & Recovery Services
        enable_error_recovery: bool = True,
        enable_error_aggregation: bool = True,
        enable_graceful_degradation: bool = True,
        enable_fallback_provider: bool = True,
        # Optimization Services
        enable_e2e_optimization: bool = True,
        enable_llm_optimization: bool = True,
        enable_content_optimization: bool = True,
        # Provider Services
        enable_provider_registry: bool = True,
        enable_provider_health_monitor: bool = True,
        enable_provider_compatibility: bool = True,
        # Conversation Services
        enable_conversation_service: bool = True,
        enable_conversation_tracker: bool = True,
        enable_context_processor: bool = True,
        # User Services
        enable_user_service: bool = True,
        enable_persona_service: bool = True,
        enable_profile_manager: bool = True,
        # Streaming & Response Services
        enable_progressive_streamer: bool = True,
        enable_intelligent_response_controller: bool = True,
        enable_response_strategy_engine: bool = True,
        # System Services
        enable_settings_manager: bool = True,
        enable_secret_manager: bool = True,
        enable_webhook_service: bool = True,
        enable_usage_service: bool = True,
        # Advanced Services
        enable_ab_testing: bool = True,
        enable_copilot_capabilities: bool = True,
        enable_cognitive_services: bool = True,
        # Graceful Degradation
        fallback_to_minimal: bool = True,
        allow_partial_initialization: bool = True,
        # Performance
        lazy_initialization: bool = True,
        preload_critical_services: bool = False,
        # Monitoring
        enable_service_health_checks: bool = True,
        health_check_interval: int = 60,
    ):
        # AI Services
        self.enable_ai_orchestrator = enable_ai_orchestrator
        self.enable_model_library = enable_model_library
        self.enable_model_orchestrator = enable_model_orchestrator
        self.enable_intelligent_router = enable_intelligent_router

        # Memory Services
        self.enable_memory_service = enable_memory_service
        self.enable_enhanced_memory = enable_enhanced_memory
        self.enable_integrated_memory = enable_integrated_memory

        # NLP Services
        self.enable_nlp_manager = enable_nlp_manager
        self.enable_spacy = enable_spacy
        self.enable_distilbert = enable_distilbert

        # Knowledge Services
        self.enable_knowledge_graph = enable_knowledge_graph
        self.enable_knowledge_connectors = enable_knowledge_connectors

        # Analytics Services
        self.enable_analytics = enable_analytics
        self.enable_analytics_dashboard = enable_analytics_dashboard
        self.enable_metrics = enable_metrics

        # Plugin & Tool Services
        self.enable_plugin_service = enable_plugin_service
        self.enable_tool_service = enable_tool_service

        # Database Services
        self.enable_database_health = enable_database_health
        self.enable_database_optimization = enable_database_optimization
        self.enable_database_query_cache = enable_database_query_cache

        # Auth & Security Services
        self.enable_production_auth = enable_production_auth
        self.enable_auth_utils = enable_auth_utils
        self.enable_tenant_isolation = enable_tenant_isolation

        # Cache Services
        self.enable_production_cache = enable_production_cache
        self.enable_smart_cache = enable_smart_cache
        self.enable_integrated_cache = enable_integrated_cache

        # Monitoring Services
        self.enable_production_monitoring = enable_production_monitoring
        self.enable_performance_monitor = enable_performance_monitor
        self.enable_health_checker = enable_health_checker
        self.enable_slo_monitoring = enable_slo_monitoring

        # Error & Recovery Services
        self.enable_error_recovery = enable_error_recovery
        self.enable_error_aggregation = enable_error_aggregation
        self.enable_graceful_degradation = enable_graceful_degradation
        self.enable_fallback_provider = enable_fallback_provider

        # Optimization Services
        self.enable_e2e_optimization = enable_e2e_optimization
        self.enable_llm_optimization = enable_llm_optimization
        self.enable_content_optimization = enable_content_optimization

        # Provider Services
        self.enable_provider_registry = enable_provider_registry
        self.enable_provider_health_monitor = enable_provider_health_monitor
        self.enable_provider_compatibility = enable_provider_compatibility

        # Conversation Services
        self.enable_conversation_service = enable_conversation_service
        self.enable_conversation_tracker = enable_conversation_tracker
        self.enable_context_processor = enable_context_processor

        # User Services
        self.enable_user_service = enable_user_service
        self.enable_persona_service = enable_persona_service
        self.enable_profile_manager = enable_profile_manager

        # Streaming & Response Services
        self.enable_progressive_streamer = enable_progressive_streamer
        self.enable_intelligent_response_controller = (
            enable_intelligent_response_controller
        )
        self.enable_response_strategy_engine = enable_response_strategy_engine

        # System Services
        self.enable_settings_manager = enable_settings_manager
        self.enable_secret_manager = enable_secret_manager
        self.enable_webhook_service = enable_webhook_service
        self.enable_usage_service = enable_usage_service

        # Advanced Services
        self.enable_ab_testing = enable_ab_testing
        self.enable_copilot_capabilities = enable_copilot_capabilities
        self.enable_cognitive_services = enable_cognitive_services

        # Options
        self.fallback_to_minimal = fallback_to_minimal
        self.allow_partial_initialization = allow_partial_initialization
        self.lazy_initialization = lazy_initialization
        self.preload_critical_services = preload_critical_services
        self.enable_service_health_checks = enable_service_health_checks
        self.health_check_interval = health_check_interval


class ServicesFactory:
    """
    Factory for creating and wiring all application services.

    This factory ensures all services are properly initialized, configured,
    and wired together with proper dependency management for production use.
    """

    def __init__(self, config: Optional[ServicesConfig] = None):
        self.config = config or ServicesConfig()
        self._services: Dict[str, Any] = {}
        self._initialization_errors: Dict[str, Exception] = {}
        logger.info("ServicesFactory initialized")

    # ==================== AI SERVICES ====================

    def create_ai_orchestrator(self):
        """Create and configure AI Orchestrator."""
        if not self.config.enable_ai_orchestrator:
            return None

        try:
            from ai_karen_engine.services.ai_orchestrator import AIOrchestrator

            orchestrator = AIOrchestrator()
            self._services["ai_orchestrator"] = orchestrator
            logger.info("AI Orchestrator created successfully")
            return orchestrator
        except Exception as e:
            logger.error(f"Failed to create AI Orchestrator: {e}")
            self._initialization_errors["ai_orchestrator"] = e
            return None

    def create_model_library_service(self):
        """Create and configure Model Library Service."""
        if not self.config.enable_model_library:
            return None

        try:
            from ai_karen_engine.services.model_library_service import (
                ModelLibraryService,
            )

            service = ModelLibraryService()
            self._services["model_library"] = service
            logger.info("Model Library Service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create Model Library Service: {e}")
            self._initialization_errors["model_library"] = e
            return None

    def create_model_orchestrator_service(self):
        """Create and configure Model Orchestrator Service."""
        if not self.config.enable_model_orchestrator:
            return None

        try:
            from ai_karen_engine.services.model_orchestrator_service import (
                ModelOrchestratorService,
            )

            service = ModelOrchestratorService()
            self._services["model_orchestrator"] = service
            logger.info("Model Orchestrator Service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create Model Orchestrator Service: {e}")
            self._initialization_errors["model_orchestrator"] = e
            return None

    def create_intelligent_model_router(self):
        """Create and configure Intelligent Model Router."""
        if not self.config.enable_intelligent_router:
            return None

        try:
            from ai_karen_engine.services.intelligent_model_router import (
                IntelligentModelRouter,
            )

            router = IntelligentModelRouter()
            self._services["intelligent_router"] = router
            logger.info("Intelligent Model Router created successfully")
            return router
        except Exception as e:
            logger.error(f"Failed to create Intelligent Model Router: {e}")
            self._initialization_errors["intelligent_router"] = e
            return None

    # ==================== MEMORY SERVICES ====================

    def create_memory_service(self):
        """Create and configure Memory Service."""
        if not self.config.enable_memory_service:
            return None

        try:
            from ai_karen_engine.services.memory_service import WebUIMemoryService

            service = WebUIMemoryService()
            self._services["memory_service"] = service
            logger.info("Memory Service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create Memory Service: {e}")
            self._initialization_errors["memory_service"] = e
            return None

    def create_enhanced_memory_service(self):
        """Create and configure Enhanced Memory Service."""
        if not self.config.enable_enhanced_memory:
            return None

        try:
            from ai_karen_engine.services.enhanced_memory_service import (
                EnhancedMemoryService,
            )

            service = EnhancedMemoryService()
            self._services["enhanced_memory"] = service
            logger.info("Enhanced Memory Service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create Enhanced Memory Service: {e}")
            self._initialization_errors["enhanced_memory"] = e
            return None

    def create_integrated_memory_service(self):
        """Create and configure Integrated Memory Service."""
        if not self.config.enable_integrated_memory:
            return None

        try:
            from ai_karen_engine.services.integrated_memory_service import (
                IntegratedMemoryService,
            )

            service = IntegratedMemoryService()
            self._services["integrated_memory"] = service
            logger.info("Integrated Memory Service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create Integrated Memory Service: {e}")
            self._initialization_errors["integrated_memory"] = e
            return None

    # ==================== NLP SERVICES ====================

    def create_nlp_service_manager(self):
        """Create and configure NLP Service Manager."""
        if not self.config.enable_nlp_manager:
            return None

        try:
            from ai_karen_engine.services.nlp_service_manager import (
                get_nlp_service_manager,
            )

            manager = get_nlp_service_manager()
            self._services["nlp_manager"] = manager
            logger.info("NLP Service Manager created successfully")
            return manager
        except Exception as e:
            logger.error(f"Failed to create NLP Service Manager: {e}")
            self._initialization_errors["nlp_manager"] = e
            return None

    # ==================== KNOWLEDGE SERVICES ====================

    def create_knowledge_graph_client(self):
        """Create and configure Knowledge Graph Client."""
        if not self.config.enable_knowledge_graph:
            return None

        try:
            from ai_karen_engine.services.knowledge_graph_client import (
                KnowledgeGraphClient,
            )

            client = KnowledgeGraphClient()
            self._services["knowledge_graph"] = client
            logger.info("Knowledge Graph Client created successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to create Knowledge Graph Client: {e}")
            self._initialization_errors["knowledge_graph"] = e
            return None

    # ==================== ANALYTICS SERVICES ====================

    def create_analytics_service(self):
        """Create and configure Analytics Service."""
        if not self.config.enable_analytics:
            return None

        try:
            from ai_karen_engine.services.analytics_service import (
                get_analytics_service,
            )

            service = get_analytics_service()
            self._services["analytics"] = service
            logger.info("Analytics Service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create Analytics Service: {e}")
            self._initialization_errors["analytics"] = e
            return None

    def create_analytics_dashboard(self):
        """Create and configure Analytics Dashboard."""
        if not self.config.enable_analytics_dashboard:
            return None

        try:
            from ai_karen_engine.services.analytics_dashboard import (
                get_analytics_dashboard,
            )

            dashboard = get_analytics_dashboard()
            self._services["analytics_dashboard"] = dashboard
            logger.info("Analytics Dashboard created successfully")
            return dashboard
        except Exception as e:
            logger.error(f"Failed to create Analytics Dashboard: {e}")
            self._initialization_errors["analytics_dashboard"] = e
            return None

    def create_metrics_service(self):
        """Create and configure Metrics Service."""
        if not self.config.enable_metrics:
            return None

        try:
            from ai_karen_engine.services.metrics_service import MetricsService

            service = MetricsService()
            self._services["metrics"] = service
            logger.info("Metrics Service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create Metrics Service: {e}")
            self._initialization_errors["metrics"] = e
            return None

    # ==================== PLUGIN & TOOL SERVICES ====================

    def create_plugin_service(self):
        """Create and configure Plugin Service."""
        if not self.config.enable_plugin_service:
            return None

        try:
            from ai_karen_engine.services.plugin_service import get_plugin_service

            service = get_plugin_service()
            self._services["plugin_service"] = service
            logger.info("Plugin Service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create Plugin Service: {e}")
            self._initialization_errors["plugin_service"] = e
            return None

    def create_tool_service(self):
        """Create and configure Tool Service."""
        if not self.config.enable_tool_service:
            return None

        try:
            from ai_karen_engine.services.tool_service import get_tool_service

            service = get_tool_service()
            self._services["tool_service"] = service
            logger.info("Tool Service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create Tool Service: {e}")
            self._initialization_errors["tool_service"] = e
            return None

    # ==================== DATABASE SERVICES ====================

    def create_database_health_monitor(self):
        """Create and configure Database Health Monitor."""
        if not self.config.enable_database_health:
            return None

        try:
            from ai_karen_engine.services.database_health_monitor import (
                DatabaseHealthMonitor,
            )

            monitor = DatabaseHealthMonitor()
            self._services["database_health"] = monitor
            logger.info("Database Health Monitor created successfully")
            return monitor
        except Exception as e:
            logger.error(f"Failed to create Database Health Monitor: {e}")
            self._initialization_errors["database_health"] = e
            return None

    def create_database_optimization_service(self):
        """Create and configure Database Optimization Service."""
        if not self.config.enable_database_optimization:
            return None

        try:
            from ai_karen_engine.services.database_optimization_service import (
                DatabaseOptimizationService,
            )

            service = DatabaseOptimizationService()
            self._services["database_optimization"] = service
            logger.info("Database Optimization Service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create Database Optimization Service: {e}")
            self._initialization_errors["database_optimization"] = e
            return None

    def create_database_query_cache_service(self):
        """Create and configure Database Query Cache Service."""
        if not self.config.enable_database_query_cache:
            return None

        try:
            from ai_karen_engine.services.database_query_cache_service import (
                DatabaseQueryCacheService,
            )

            service = DatabaseQueryCacheService()
            self._services["database_query_cache"] = service
            logger.info("Database Query Cache Service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create Database Query Cache Service: {e}")
            self._initialization_errors["database_query_cache"] = e
            return None

    # ==================== AUTH & SECURITY SERVICES ====================

    def create_production_auth_service(self):
        """Create and configure Production Auth Service."""
        if not self.config.enable_production_auth:
            return None

        try:
            from ai_karen_engine.services.production_auth_service import (
                ProductionAuthService,
            )

            service = ProductionAuthService()
            self._services["production_auth"] = service
            logger.info("Production Auth Service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create Production Auth Service: {e}")
            self._initialization_errors["production_auth"] = e
            return None

    # ==================== CACHE SERVICES ====================

    def create_production_cache_service(self):
        """Create and configure Production Cache Service."""
        if not self.config.enable_production_cache:
            return None

        try:
            from ai_karen_engine.services.production_cache_service import (
                ProductionCacheService,
            )

            service = ProductionCacheService()
            self._services["production_cache"] = service
            logger.info("Production Cache Service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create Production Cache Service: {e}")
            self._initialization_errors["production_cache"] = e
            return None

    def create_smart_cache_manager(self):
        """Create and configure Smart Cache Manager."""
        if not self.config.enable_smart_cache:
            return None

        try:
            from ai_karen_engine.services.smart_cache_manager import SmartCacheManager

            manager = SmartCacheManager()
            self._services["smart_cache"] = manager
            logger.info("Smart Cache Manager created successfully")
            return manager
        except Exception as e:
            logger.error(f"Failed to create Smart Cache Manager: {e}")
            self._initialization_errors["smart_cache"] = e
            return None

    def create_integrated_cache_system(self):
        """Create and configure Integrated Cache System."""
        if not self.config.enable_integrated_cache:
            return None

        try:
            from ai_karen_engine.services.integrated_cache_system import (
                IntegratedCacheSystem,
            )

            system = IntegratedCacheSystem()
            self._services["integrated_cache"] = system
            logger.info("Integrated Cache System created successfully")
            return system
        except Exception as e:
            logger.error(f"Failed to create Integrated Cache System: {e}")
            self._initialization_errors["integrated_cache"] = e
            return None

    # ==================== MONITORING SERVICES ====================

    def create_production_monitoring_service(self):
        """Create and configure Production Monitoring Service."""
        if not self.config.enable_production_monitoring:
            return None

        try:
            from ai_karen_engine.services.production_monitoring_service import (
                ProductionMonitoringService,
            )

            service = ProductionMonitoringService()
            self._services["production_monitoring"] = service
            logger.info("Production Monitoring Service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create Production Monitoring Service: {e}")
            self._initialization_errors["production_monitoring"] = e
            return None

    def create_performance_monitor(self):
        """Create and configure Performance Monitor."""
        if not self.config.enable_performance_monitor:
            return None

        try:
            from ai_karen_engine.services.performance_monitor import PerformanceMonitor

            monitor = PerformanceMonitor()
            self._services["performance_monitor"] = monitor
            logger.info("Performance Monitor created successfully")
            return monitor
        except Exception as e:
            logger.error(f"Failed to create Performance Monitor: {e}")
            self._initialization_errors["performance_monitor"] = e
            return None

    def create_health_checker(self):
        """Create and configure Health Checker."""
        if not self.config.enable_health_checker:
            return None

        try:
            from ai_karen_engine.services.health_checker import HealthChecker

            checker = HealthChecker()
            self._services["health_checker"] = checker
            logger.info("Health Checker created successfully")
            return checker
        except Exception as e:
            logger.error(f"Failed to create Health Checker: {e}")
            self._initialization_errors["health_checker"] = e
            return None

    # ==================== ERROR & RECOVERY SERVICES ====================

    def create_error_recovery_system(self):
        """Create and configure Error Recovery System."""
        if not self.config.enable_error_recovery:
            return None

        try:
            from ai_karen_engine.services.error_recovery_system import (
                ErrorRecoverySystem,
            )

            system = ErrorRecoverySystem()
            self._services["error_recovery"] = system
            logger.info("Error Recovery System created successfully")
            return system
        except Exception as e:
            logger.error(f"Failed to create Error Recovery System: {e}")
            self._initialization_errors["error_recovery"] = e
            return None

    def create_graceful_degradation_coordinator(self):
        """Create and configure Graceful Degradation Coordinator."""
        if not self.config.enable_graceful_degradation:
            return None

        try:
            from ai_karen_engine.services.graceful_degradation_coordinator import (
                GracefulDegradationCoordinator,
            )

            coordinator = GracefulDegradationCoordinator()
            self._services["graceful_degradation"] = coordinator
            logger.info("Graceful Degradation Coordinator created successfully")
            return coordinator
        except Exception as e:
            logger.error(f"Failed to create Graceful Degradation Coordinator: {e}")
            self._initialization_errors["graceful_degradation"] = e
            return None

    def create_fallback_provider(self):
        """Create and configure Fallback Provider."""
        if not self.config.enable_fallback_provider:
            return None

        try:
            from ai_karen_engine.services.fallback_provider import FallbackProvider

            provider = FallbackProvider()
            self._services["fallback_provider"] = provider
            logger.info("Fallback Provider created successfully")
            return provider
        except Exception as e:
            logger.error(f"Failed to create Fallback Provider: {e}")
            self._initialization_errors["fallback_provider"] = e
            return None

    # ==================== PROVIDER SERVICES ====================

    def create_provider_registry(self):
        """Create and configure Provider Registry."""
        if not self.config.enable_provider_registry:
            return None

        try:
            from ai_karen_engine.services.provider_registry import ProviderRegistry

            registry = ProviderRegistry()
            self._services["provider_registry"] = registry
            logger.info("Provider Registry created successfully")
            return registry
        except Exception as e:
            logger.error(f"Failed to create Provider Registry: {e}")
            self._initialization_errors["provider_registry"] = e
            return None

    def create_provider_health_monitor(self):
        """Create and configure Provider Health Monitor."""
        if not self.config.enable_provider_health_monitor:
            return None

        try:
            from ai_karen_engine.services.provider_health_monitor import (
                ProviderHealthMonitor,
            )

            monitor = ProviderHealthMonitor()
            self._services["provider_health_monitor"] = monitor
            logger.info("Provider Health Monitor created successfully")
            return monitor
        except Exception as e:
            logger.error(f"Failed to create Provider Health Monitor: {e}")
            self._initialization_errors["provider_health_monitor"] = e
            return None

    # ==================== CONVERSATION SERVICES ====================

    def create_conversation_service(self):
        """Create and configure Conversation Service."""
        if not self.config.enable_conversation_service:
            return None

        try:
            from ai_karen_engine.services.conversation_service import (
                ConversationService,
            )

            service = ConversationService()
            self._services["conversation_service"] = service
            logger.info("Conversation Service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create Conversation Service: {e}")
            self._initialization_errors["conversation_service"] = e
            return None

    def create_context_processor(self):
        """Create and configure Context Processor."""
        if not self.config.enable_context_processor:
            return None

        try:
            from ai_karen_engine.services.context_processor import ContextProcessor

            processor = ContextProcessor()
            self._services["context_processor"] = processor
            logger.info("Context Processor created successfully")
            return processor
        except Exception as e:
            logger.error(f"Failed to create Context Processor: {e}")
            self._initialization_errors["context_processor"] = e
            return None

    # ==================== USER SERVICES ====================

    def create_user_service(self):
        """Create and configure User Service."""
        if not self.config.enable_user_service:
            return None

        try:
            from ai_karen_engine.services.user_service import UserService

            service = UserService()
            self._services["user_service"] = service
            logger.info("User Service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create User Service: {e}")
            self._initialization_errors["user_service"] = e
            return None

    def create_persona_service(self):
        """Create and configure Persona Service."""
        if not self.config.enable_persona_service:
            return None

        try:
            from ai_karen_engine.services.persona_service import PersonaService

            service = PersonaService()
            self._services["persona_service"] = service
            logger.info("Persona Service created successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to create Persona Service: {e}")
            self._initialization_errors["persona_service"] = e
            return None

    # ==================== SYSTEM SERVICES ====================

    def create_settings_manager(self):
        """Create and configure Settings Manager."""
        if not self.config.enable_settings_manager:
            return None

        try:
            from ai_karen_engine.services.settings_manager import SettingsManager

            manager = SettingsManager()
            self._services["settings_manager"] = manager
            logger.info("Settings Manager created successfully")
            return manager
        except Exception as e:
            logger.error(f"Failed to create Settings Manager: {e}")
            self._initialization_errors["settings_manager"] = e
            return None

    def create_secret_manager(self):
        """Create and configure Secret Manager."""
        if not self.config.enable_secret_manager:
            return None

        try:
            from ai_karen_engine.services.secret_manager import SecretManager

            manager = SecretManager()
            self._services["secret_manager"] = manager
            logger.info("Secret Manager created successfully")
            return manager
        except Exception as e:
            logger.error(f"Failed to create Secret Manager: {e}")
            self._initialization_errors["secret_manager"] = e
            return None

    # ==================== ORCHESTRATION ====================

    def create_all_services(self) -> Dict[str, Any]:
        """
        Create all enabled services in proper dependency order.

        This is the main entry point for full system initialization.

        Returns:
            Dictionary of all successfully created services
        """
        logger.info("Creating all services in dependency order")

        # Phase 1: Foundation Services (no dependencies)
        logger.info("Phase 1: Foundation services")
        self.create_settings_manager()
        self.create_secret_manager()
        self.create_health_checker()
        self.create_metrics_service()

        # Phase 2: Infrastructure Services (database, cache, monitoring)
        logger.info("Phase 2: Infrastructure services")
        self.create_database_health_monitor()
        self.create_database_optimization_service()
        self.create_database_query_cache_service()
        self.create_production_cache_service()
        self.create_smart_cache_manager()
        self.create_integrated_cache_system()
        self.create_production_monitoring_service()
        self.create_performance_monitor()

        # Phase 3: Auth & Security Services
        logger.info("Phase 3: Auth & security services")
        self.create_production_auth_service()

        # Phase 4: Core Services (NLP, knowledge, analytics)
        logger.info("Phase 4: Core services")
        self.create_nlp_service_manager()
        self.create_knowledge_graph_client()
        self.create_analytics_service()
        self.create_analytics_dashboard()

        # Phase 5: Provider & Model Services
        logger.info("Phase 5: Provider & model services")
        self.create_provider_registry()
        self.create_provider_health_monitor()
        self.create_model_library_service()
        self.create_model_orchestrator_service()
        self.create_intelligent_model_router()

        # Phase 6: Memory Services
        logger.info("Phase 6: Memory services")
        self.create_memory_service()
        self.create_enhanced_memory_service()
        self.create_integrated_memory_service()

        # Phase 7: Plugin & Tool Services
        logger.info("Phase 7: Plugin & tool services")
        self.create_plugin_service()
        self.create_tool_service()

        # Phase 8: Error & Recovery Services
        logger.info("Phase 8: Error & recovery services")
        self.create_error_recovery_system()
        self.create_graceful_degradation_coordinator()
        self.create_fallback_provider()

        # Phase 9: Conversation & Context Services
        logger.info("Phase 9: Conversation & context services")
        self.create_conversation_service()
        self.create_context_processor()

        # Phase 10: User Services
        logger.info("Phase 10: User services")
        self.create_user_service()
        self.create_persona_service()

        # Phase 11: AI Orchestrator (depends on most other services)
        logger.info("Phase 11: AI orchestrator")
        self.create_ai_orchestrator()

        services_count = len(self._services)
        errors_count = len(self._initialization_errors)

        logger.info(
            f"Services initialization complete: {services_count} services created, "
            f"{errors_count} errors"
        )

        if self._initialization_errors:
            logger.warning(f"Failed services: {list(self._initialization_errors.keys())}")

        return self._services

    def get_service(self, service_name: str):
        """Get a service by name."""
        return self._services.get(service_name)

    def get_all_services(self) -> Dict[str, Any]:
        """Get all created services."""
        return self._services.copy()

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all services.

        Returns:
            Dictionary with health status of all services
        """
        if not self.config.enable_service_health_checks:
            return {"health_checks_disabled": True}

        health = {
            "services_count": len(self._services),
            "errors_count": len(self._initialization_errors),
            "services": {},
            "errors": {},
        }

        # Check each service
        for service_name, service in self._services.items():
            try:
                # Try to call health_check method if available
                if hasattr(service, "health_check"):
                    service_health = service.health_check()
                    health["services"][service_name] = {
                        "healthy": True,
                        "details": service_health,
                    }
                else:
                    health["services"][service_name] = {"healthy": True, "exists": True}
            except Exception as e:
                health["services"][service_name] = {
                    "healthy": False,
                    "error": str(e),
                }

        # Record initialization errors
        for service_name, error in self._initialization_errors.items():
            health["errors"][service_name] = str(error)

        return health

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics from all services.

        Returns:
            Dictionary with metrics from all services
        """
        metrics = {
            "services_count": len(self._services),
            "errors_count": len(self._initialization_errors),
            "services": {},
        }

        # Collect metrics from each service
        for service_name, service in self._services.items():
            try:
                if hasattr(service, "get_metrics"):
                    service_metrics = service.get_metrics()
                    metrics["services"][service_name] = service_metrics
            except Exception as e:
                logger.warning(
                    f"Failed to get metrics from {service_name}: {e}"
                )

        return metrics


# Global factory instance
_global_factory: Optional[ServicesFactory] = None


def get_services_factory(config: Optional[ServicesConfig] = None) -> ServicesFactory:
    """
    Get or create global services factory.

    Args:
        config: Optional configuration for the factory

    Returns:
        ServicesFactory instance
    """
    global _global_factory

    if _global_factory is None:
        _global_factory = ServicesFactory(config)
        logger.info("Global services factory created")

    return _global_factory


def initialize_services_for_production():
    """
    Initialize all services for production use.

    This is the main entry point for production service initialization.
    Call this during application startup.
    """
    factory = get_services_factory()
    factory.create_all_services()
    logger.info("All services initialized for production")
    return factory.health_check()


__all__ = [
    "ServicesConfig",
    "ServicesFactory",
    "get_services_factory",
    "initialize_services_for_production",
]
