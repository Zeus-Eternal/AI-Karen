"""
FastAPI dependency providers for all application services.

Provides singleton instances of all services for dependency injection throughout the application.
All dependencies use @lru_cache() for consistent global singleton instances.
"""

from functools import lru_cache
from typing import Optional

from src.services.factory import get_services_factory


# ==================== FACTORY DEPENDENCY ====================

@lru_cache()
def get_services_factory_dependency():
    """
    FastAPI dependency for services factory.

    Returns:
        ServicesFactory instance

    Usage:
        @app.get("/services/status")
        def get_status(factory = Depends(get_services_factory_dependency)):
            return factory.health_check()
    """
    return get_services_factory()


# ==================== AI SERVICES DEPENDENCIES ====================

@lru_cache()
def get_ai_orchestrator_dependency():
    """
    FastAPI dependency for AI Orchestrator.

    Usage:
        @app.post("/ai/orchestrate")
        def orchestrate(
            request: dict,
            orchestrator = Depends(get_ai_orchestrator_dependency)
        ):
            return orchestrator.process(request)
    """
    factory = get_services_factory()
    service = factory.get_service("ai_orchestrator")
    if service is None:
        service = factory.create_ai_orchestrator()
    return service


@lru_cache()
def get_model_library_dependency():
    """
    FastAPI dependency for Model Library Service.

    Usage:
        @app.get("/models/list")
        def list_models(library = Depends(get_model_library_dependency)):
            return library.list_models()
    """
    factory = get_services_factory()
    service = factory.get_service("model_library")
    if service is None:
        service = factory.create_model_library_service()
    return service


@lru_cache()
def get_model_orchestrator_dependency():
    """
    FastAPI dependency for Model Orchestrator Service.

    Usage:
        @app.post("/models/orchestrate")
        def orchestrate_model(
            request: dict,
            orchestrator = Depends(get_model_orchestrator_dependency)
        ):
            return orchestrator.orchestrate(request)
    """
    factory = get_services_factory()
    service = factory.get_service("model_orchestrator")
    if service is None:
        service = factory.create_model_orchestrator_service()
    return service


@lru_cache()
def get_intelligent_router_dependency():
    """
    FastAPI dependency for Intelligent Model Router.

    Usage:
        @app.post("/route")
        def route_request(
            request: dict,
            router = Depends(get_intelligent_router_dependency)
        ):
            return router.route(request)
    """
    factory = get_services_factory()
    service = factory.get_service("intelligent_router")
    if service is None:
        service = factory.create_intelligent_model_router()
    return service


# ==================== MEMORY SERVICES DEPENDENCIES ====================

@lru_cache()
def get_memory_service_dependency():
    """
    FastAPI dependency for Memory Service.

    Usage:
        @app.post("/memory/store")
        def store_memory(
            data: dict,
            memory = Depends(get_memory_service_dependency)
        ):
            return memory.store(data)
    """
    factory = get_services_factory()
    service = factory.get_service("memory_service")
    if service is None:
        service = factory.create_memory_service()
    return service


@lru_cache()
def get_enhanced_memory_dependency():
    """
    FastAPI dependency for Enhanced Memory Service.

    Usage:
        @app.post("/memory/enhanced/search")
        def search_memory(
            query: str,
            memory = Depends(get_enhanced_memory_dependency)
        ):
            return memory.search(query)
    """
    factory = get_services_factory()
    service = factory.get_service("enhanced_memory")
    if service is None:
        service = factory.create_enhanced_memory_service()
    return service


@lru_cache()
def get_integrated_memory_dependency():
    """
    FastAPI dependency for Integrated Memory Service.

    Usage:
        @app.get("/memory/integrated/stats")
        def get_memory_stats(memory = Depends(get_integrated_memory_dependency)):
            return memory.get_stats()
    """
    factory = get_services_factory()
    service = factory.get_service("integrated_memory")
    if service is None:
        service = factory.create_integrated_memory_service()
    return service


# ==================== NLP SERVICES DEPENDENCIES ====================

@lru_cache()
def get_nlp_manager_dependency():
    """
    FastAPI dependency for NLP Service Manager.

    Usage:
        @app.post("/nlp/parse")
        def parse_text(
            text: str,
            nlp = Depends(get_nlp_manager_dependency)
        ):
            return nlp.parse(text)
    """
    factory = get_services_factory()
    service = factory.get_service("nlp_manager")
    if service is None:
        service = factory.create_nlp_service_manager()
    return service


# ==================== KNOWLEDGE SERVICES DEPENDENCIES ====================

@lru_cache()
def get_knowledge_graph_dependency():
    """
    FastAPI dependency for Knowledge Graph Client.

    Usage:
        @app.post("/kg/query")
        def query_kg(
            query: str,
            kg = Depends(get_knowledge_graph_dependency)
        ):
            return kg.execute_cypher(query)
    """
    factory = get_services_factory()
    service = factory.get_service("knowledge_graph")
    if service is None:
        service = factory.create_knowledge_graph_client()
    return service


# ==================== ANALYTICS SERVICES DEPENDENCIES ====================

@lru_cache()
def get_analytics_service_dependency():
    """
    FastAPI dependency for Analytics Service.

    Usage:
        @app.get("/analytics/stats")
        def get_analytics(analytics = Depends(get_analytics_service_dependency)):
            return analytics.get_stats()
    """
    factory = get_services_factory()
    service = factory.get_service("analytics")
    if service is None:
        service = factory.create_analytics_service()
    return service


@lru_cache()
def get_analytics_dashboard_dependency():
    """
    FastAPI dependency for Analytics Dashboard.

    Usage:
        @app.get("/analytics/dashboard")
        def get_dashboard(dashboard = Depends(get_analytics_dashboard_dependency)):
            return dashboard.get_data()
    """
    factory = get_services_factory()
    service = factory.get_service("analytics_dashboard")
    if service is None:
        service = factory.create_analytics_dashboard()
    return service


@lru_cache()
def get_metrics_service_dependency():
    """
    FastAPI dependency for Metrics Service.

    Usage:
        @app.get("/metrics")
        def get_metrics(metrics = Depends(get_metrics_service_dependency)):
            return metrics.get_all()
    """
    factory = get_services_factory()
    service = factory.get_service("metrics")
    if service is None:
        service = factory.create_metrics_service()
    return service


# ==================== PLUGIN & TOOL SERVICES DEPENDENCIES ====================

@lru_cache()
def get_plugin_service_dependency():
    """
    FastAPI dependency for Plugin Service.

    Usage:
        @app.post("/plugins/execute")
        def execute_plugin(
            plugin_id: str,
            params: dict,
            plugins = Depends(get_plugin_service_dependency)
        ):
            return plugins.execute(plugin_id, params)
    """
    factory = get_services_factory()
    service = factory.get_service("plugin_service")
    if service is None:
        service = factory.create_plugin_service()
    return service


@lru_cache()
def get_tool_service_dependency():
    """
    FastAPI dependency for Tool Service.

    Usage:
        @app.post("/tools/execute")
        def execute_tool(
            tool_id: str,
            params: dict,
            tools = Depends(get_tool_service_dependency)
        ):
            return tools.execute(tool_id, params)
    """
    factory = get_services_factory()
    service = factory.get_service("tool_service")
    if service is None:
        service = factory.create_tool_service()
    return service


# ==================== DATABASE SERVICES DEPENDENCIES ====================

@lru_cache()
def get_database_health_dependency():
    """
    FastAPI dependency for Database Health Monitor.

    Usage:
        @app.get("/health/database")
        def get_db_health(monitor = Depends(get_database_health_dependency)):
            return monitor.check_health()
    """
    factory = get_services_factory()
    service = factory.get_service("database_health")
    if service is None:
        service = factory.create_database_health_monitor()
    return service


@lru_cache()
def get_database_optimization_dependency():
    """
    FastAPI dependency for Database Optimization Service.

    Usage:
        @app.post("/database/optimize")
        def optimize_db(optimizer = Depends(get_database_optimization_dependency)):
            return optimizer.optimize()
    """
    factory = get_services_factory()
    service = factory.get_service("database_optimization")
    if service is None:
        service = factory.create_database_optimization_service()
    return service


@lru_cache()
def get_database_query_cache_dependency():
    """
    FastAPI dependency for Database Query Cache Service.

    Usage:
        @app.get("/database/cache/stats")
        def get_cache_stats(cache = Depends(get_database_query_cache_dependency)):
            return cache.get_stats()
    """
    factory = get_services_factory()
    service = factory.get_service("database_query_cache")
    if service is None:
        service = factory.create_database_query_cache_service()
    return service


# ==================== AUTH & SECURITY SERVICES DEPENDENCIES ====================

@lru_cache()
def get_auth_service_dependency():
    """
    FastAPI dependency for Production Auth Service.

    Usage:
        @app.post("/auth/login")
        def login(
            credentials: dict,
            auth = Depends(get_auth_service_dependency)
        ):
            return auth.authenticate(credentials)
    """
    factory = get_services_factory()
    service = factory.get_service("production_auth")
    if service is None:
        service = factory.create_production_auth_service()
    return service


# ==================== CACHE SERVICES DEPENDENCIES ====================

@lru_cache()
def get_production_cache_dependency():
    """
    FastAPI dependency for Production Cache Service.

    Usage:
        @app.get("/cache/stats")
        def get_cache_stats(cache = Depends(get_production_cache_dependency)):
            return cache.get_stats()
    """
    factory = get_services_factory()
    service = factory.get_service("production_cache")
    if service is None:
        service = factory.create_production_cache_service()
    return service


@lru_cache()
def get_smart_cache_dependency():
    """
    FastAPI dependency for Smart Cache Manager.

    Usage:
        @app.get("/cache/smart/stats")
        def get_smart_cache_stats(cache = Depends(get_smart_cache_dependency)):
            return cache.get_stats()
    """
    factory = get_services_factory()
    service = factory.get_service("smart_cache")
    if service is None:
        service = factory.create_smart_cache_manager()
    return service


@lru_cache()
def get_integrated_cache_dependency():
    """
    FastAPI dependency for Integrated Cache System.

    Usage:
        @app.post("/cache/invalidate")
        def invalidate_cache(
            pattern: str,
            cache = Depends(get_integrated_cache_dependency)
        ):
            return cache.invalidate(pattern)
    """
    factory = get_services_factory()
    service = factory.get_service("integrated_cache")
    if service is None:
        service = factory.create_integrated_cache_system()
    return service


# ==================== MONITORING SERVICES DEPENDENCIES ====================

@lru_cache()
def get_production_monitoring_dependency():
    """
    FastAPI dependency for Production Monitoring Service.

    Usage:
        @app.get("/monitoring/status")
        def get_monitoring_status(
            monitor = Depends(get_production_monitoring_dependency)
        ):
            return monitor.get_status()
    """
    factory = get_services_factory()
    service = factory.get_service("production_monitoring")
    if service is None:
        service = factory.create_production_monitoring_service()
    return service


@lru_cache()
def get_performance_monitor_dependency():
    """
    FastAPI dependency for Performance Monitor.

    Usage:
        @app.get("/monitoring/performance")
        def get_performance(monitor = Depends(get_performance_monitor_dependency)):
            return monitor.get_metrics()
    """
    factory = get_services_factory()
    service = factory.get_service("performance_monitor")
    if service is None:
        service = factory.create_performance_monitor()
    return service


@lru_cache()
def get_health_checker_dependency():
    """
    FastAPI dependency for Health Checker.

    Usage:
        @app.get("/health")
        def health_check(checker = Depends(get_health_checker_dependency)):
            return checker.check_all()
    """
    factory = get_services_factory()
    service = factory.get_service("health_checker")
    if service is None:
        service = factory.create_health_checker()
    return service


# ==================== ERROR & RECOVERY SERVICES DEPENDENCIES ====================

@lru_cache()
def get_error_recovery_dependency():
    """
    FastAPI dependency for Error Recovery System.

    Usage:
        @app.post("/errors/recover")
        def recover_from_error(
            error: dict,
            recovery = Depends(get_error_recovery_dependency)
        ):
            return recovery.recover(error)
    """
    factory = get_services_factory()
    service = factory.get_service("error_recovery")
    if service is None:
        service = factory.create_error_recovery_system()
    return service


@lru_cache()
def get_graceful_degradation_dependency():
    """
    FastAPI dependency for Graceful Degradation Coordinator.

    Usage:
        @app.get("/degradation/status")
        def get_degradation_status(
            coordinator = Depends(get_graceful_degradation_dependency)
        ):
            return coordinator.get_status()
    """
    factory = get_services_factory()
    service = factory.get_service("graceful_degradation")
    if service is None:
        service = factory.create_graceful_degradation_coordinator()
    return service


@lru_cache()
def get_fallback_provider_dependency():
    """
    FastAPI dependency for Fallback Provider.

    Usage:
        @app.post("/fallback/execute")
        def execute_with_fallback(
            request: dict,
            fallback = Depends(get_fallback_provider_dependency)
        ):
            return fallback.execute(request)
    """
    factory = get_services_factory()
    service = factory.get_service("fallback_provider")
    if service is None:
        service = factory.create_fallback_provider()
    return service


# ==================== PROVIDER SERVICES DEPENDENCIES ====================

@lru_cache()
def get_provider_registry_dependency():
    """
    FastAPI dependency for Provider Registry.

    Usage:
        @app.get("/providers/list")
        def list_providers(registry = Depends(get_provider_registry_dependency)):
            return registry.list_all()
    """
    factory = get_services_factory()
    service = factory.get_service("provider_registry")
    if service is None:
        service = factory.create_provider_registry()
    return service


@lru_cache()
def get_provider_health_monitor_dependency():
    """
    FastAPI dependency for Provider Health Monitor.

    Usage:
        @app.get("/providers/health")
        def get_provider_health(
            monitor = Depends(get_provider_health_monitor_dependency)
        ):
            return monitor.check_all()
    """
    factory = get_services_factory()
    service = factory.get_service("provider_health_monitor")
    if service is None:
        service = factory.create_provider_health_monitor()
    return service


# ==================== CONVERSATION SERVICES DEPENDENCIES ====================

@lru_cache()
def get_conversation_service_dependency():
    """
    FastAPI dependency for Conversation Service.

    Usage:
        @app.post("/conversation/create")
        def create_conversation(
            data: dict,
            service = Depends(get_conversation_service_dependency)
        ):
            return service.create(data)
    """
    factory = get_services_factory()
    service = factory.get_service("conversation_service")
    if service is None:
        service = factory.create_conversation_service()
    return service


@lru_cache()
def get_context_processor_dependency():
    """
    FastAPI dependency for Context Processor.

    Usage:
        @app.post("/context/process")
        def process_context(
            context: dict,
            processor = Depends(get_context_processor_dependency)
        ):
            return processor.process(context)
    """
    factory = get_services_factory()
    service = factory.get_service("context_processor")
    if service is None:
        service = factory.create_context_processor()
    return service


# ==================== USER SERVICES DEPENDENCIES ====================

@lru_cache()
def get_user_service_dependency():
    """
    FastAPI dependency for User Service.

    Usage:
        @app.get("/users/{user_id}")
        def get_user(
            user_id: str,
            service = Depends(get_user_service_dependency)
        ):
            return service.get_user(user_id)
    """
    factory = get_services_factory()
    service = factory.get_service("user_service")
    if service is None:
        service = factory.create_user_service()
    return service


@lru_cache()
def get_persona_service_dependency():
    """
    FastAPI dependency for Persona Service.

    Usage:
        @app.get("/personas/list")
        def list_personas(service = Depends(get_persona_service_dependency)):
            return service.list_all()
    """
    factory = get_services_factory()
    service = factory.get_service("persona_service")
    if service is None:
        service = factory.create_persona_service()
    return service


# ==================== SYSTEM SERVICES DEPENDENCIES ====================

@lru_cache()
def get_settings_manager_dependency():
    """
    FastAPI dependency for Settings Manager.

    Usage:
        @app.get("/settings")
        def get_settings(manager = Depends(get_settings_manager_dependency)):
            return manager.get_all()
    """
    factory = get_services_factory()
    service = factory.get_service("settings_manager")
    if service is None:
        service = factory.create_settings_manager()
    return service


@lru_cache()
def get_secret_manager_dependency():
    """
    FastAPI dependency for Secret Manager.

    Usage:
        @app.get("/secrets/{key}")
        def get_secret(
            key: str,
            manager = Depends(get_secret_manager_dependency)
        ):
            return manager.get_secret(key)
    """
    factory = get_services_factory()
    service = factory.get_service("secret_manager")
    if service is None:
        service = factory.create_secret_manager()
    return service


# ==================== HEALTH & METRICS ====================

def get_services_health_check():
    """
    FastAPI dependency for services health check.

    Returns:
        Dictionary of all services health statuses

    Usage:
        @app.get("/health/services")
        def services_health(health: dict = Depends(get_services_health_check)):
            return health
    """
    factory = get_services_factory()
    return factory.health_check()


def get_services_metrics():
    """
    FastAPI dependency for services metrics.

    Returns:
        Dictionary of metrics from all services

    Usage:
        @app.get("/metrics/services")
        def services_metrics(metrics: dict = Depends(get_services_metrics)):
            return metrics
    """
    factory = get_services_factory()
    return factory.get_metrics()


# ==================== COMPOSITE DEPENDENCIES ====================

def get_core_services():
    """
    Get all core services in a single dependency.

    Returns:
        Dictionary with commonly used services

    Usage:
        @app.post("/process")
        def process_request(
            request: dict,
            services: dict = Depends(get_core_services)
        ):
            ai = services['ai_orchestrator']
            memory = services['memory']
            analytics = services['analytics']
            # ... use services
    """
    factory = get_services_factory()
    return {
        "ai_orchestrator": factory.get_service("ai_orchestrator") or factory.create_ai_orchestrator(),
        "memory": factory.get_service("memory_service") or factory.create_memory_service(),
        "nlp": factory.get_service("nlp_manager") or factory.create_nlp_service_manager(),
        "analytics": factory.get_service("analytics") or factory.create_analytics_service(),
        "cache": factory.get_service("production_cache") or factory.create_production_cache_service(),
        "auth": factory.get_service("production_auth") or factory.create_production_auth_service(),
    }


__all__ = [
    # Factory
    "get_services_factory_dependency",
    # AI Services
    "get_ai_orchestrator_dependency",
    "get_model_library_dependency",
    "get_model_orchestrator_dependency",
    "get_intelligent_router_dependency",
    # Memory Services
    "get_memory_service_dependency",
    "get_enhanced_memory_dependency",
    "get_integrated_memory_dependency",
    # NLP Services
    "get_nlp_manager_dependency",
    # Knowledge Services
    "get_knowledge_graph_dependency",
    # Analytics Services
    "get_analytics_service_dependency",
    "get_analytics_dashboard_dependency",
    "get_metrics_service_dependency",
    # Plugin & Tool Services
    "get_plugin_service_dependency",
    "get_tool_service_dependency",
    # Database Services
    "get_database_health_dependency",
    "get_database_optimization_dependency",
    "get_database_query_cache_dependency",
    # Auth & Security Services
    "get_auth_service_dependency",
    # Cache Services
    "get_production_cache_dependency",
    "get_smart_cache_dependency",
    "get_integrated_cache_dependency",
    # Monitoring Services
    "get_production_monitoring_dependency",
    "get_performance_monitor_dependency",
    "get_health_checker_dependency",
    # Error & Recovery Services
    "get_error_recovery_dependency",
    "get_graceful_degradation_dependency",
    "get_fallback_provider_dependency",
    # Provider Services
    "get_provider_registry_dependency",
    "get_provider_health_monitor_dependency",
    # Conversation Services
    "get_conversation_service_dependency",
    "get_context_processor_dependency",
    # User Services
    "get_user_service_dependency",
    "get_persona_service_dependency",
    # System Services
    "get_settings_manager_dependency",
    "get_secret_manager_dependency",
    # Health & Metrics
    "get_services_health_check",
    "get_services_metrics",
    # Composite
    "get_core_services",
]
