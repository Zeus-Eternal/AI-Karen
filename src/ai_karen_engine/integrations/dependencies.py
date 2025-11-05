"""
FastAPI dependency providers for integration services.

Provides singleton instances of all integration services for dependency injection.
"""

from functools import lru_cache
from typing import Optional, Dict, Any

from ai_karen_engine.integrations.factory import (
    get_provider_registry as _get_provider_registry,
    get_llm_router as _get_llm_router,
    get_fallback_manager as _get_fallback_manager,
    get_integration_service_factory,
)


# Provider registry dependencies
@lru_cache()
def get_provider_registry_dependency():
    """
    FastAPI dependency for provider registry.

    Returns:
        ProviderRegistry instance

    Usage:
        @app.get("/providers")
        def list_providers(
            registry = Depends(get_provider_registry_dependency)
        ):
            return registry.get_all_providers()
    """
    return _get_provider_registry()


# Router dependencies
@lru_cache()
def get_llm_router_dependency():
    """
    FastAPI dependency for LLM router.

    Returns:
        LLMRouter instance or None if unavailable

    Usage:
        @app.post("/route")
        def route_request(
            request: RoutingRequest,
            router = Depends(get_llm_router_dependency)
        ):
            if not router:
                raise HTTPException(status_code=503, detail="LLM router unavailable")
            return router.route(request)
    """
    return _get_llm_router()


@lru_cache()
def get_capability_router_dependency():
    """
    FastAPI dependency for capability router.

    Returns:
        CapabilityRouter instance or None if unavailable

    Usage:
        @app.post("/route/capability")
        def route_with_capabilities(
            request: RoutingCapabilityRequest,
            router = Depends(get_capability_router_dependency)
        ):
            if not router:
                raise HTTPException(status_code=503, detail="Capability router unavailable")
            return router.route_with_capabilities(request)
    """
    factory = get_integration_service_factory()
    return factory.get_router("capability_router") or factory.create_capability_router()


@lru_cache()
def get_copilot_router_dependency():
    """
    FastAPI dependency for copilot router.

    Returns:
        CopilotRouter instance or None if unavailable

    Usage:
        @app.post("/copilot/suggest")
        def get_suggestions(
            code: str,
            router = Depends(get_copilot_router_dependency)
        ):
            if not router:
                raise HTTPException(status_code=503, detail="Copilot router unavailable")
            return router.get_suggestions(code)
    """
    factory = get_integration_service_factory()
    return factory.get_router("copilot_router") or factory.create_copilot_router()


# Fallback and recovery dependencies
@lru_cache()
def get_fallback_manager_dependency():
    """
    FastAPI dependency for fallback manager.

    Returns:
        FallbackManager instance or None if unavailable

    Usage:
        @app.post("/generate/with-fallback")
        def generate_with_fallback(
            prompt: str,
            fallback_manager = Depends(get_fallback_manager_dependency)
        ):
            if not fallback_manager:
                raise HTTPException(status_code=503, detail="Fallback manager unavailable")
            return fallback_manager.execute_with_fallback(prompt)
    """
    return _get_fallback_manager()


@lru_cache()
def get_error_recovery_dependency():
    """
    FastAPI dependency for error recovery service.

    Returns:
        ErrorRecoveryManager instance or None if unavailable

    Usage:
        @app.post("/recover")
        def recover_from_error(
            error: ErrorInfo,
            recovery = Depends(get_error_recovery_dependency)
        ):
            if not recovery:
                raise HTTPException(status_code=503, detail="Error recovery unavailable")
            return recovery.recover(error)
    """
    factory = get_integration_service_factory()
    return factory.get_service("error_recovery") or factory.create_error_recovery()


# Model management dependencies
@lru_cache()
def get_model_discovery_dependency():
    """
    FastAPI dependency for model discovery service.

    Returns:
        ModelDiscoveryEngine instance or None if unavailable

    Usage:
        @app.get("/models/discover")
        def discover_models(
            discovery = Depends(get_model_discovery_dependency)
        ):
            if not discovery:
                raise HTTPException(status_code=503, detail="Model discovery unavailable")
            return discovery.discover_all_models()
    """
    factory = get_integration_service_factory()
    return factory.get_service("model_discovery") or factory.create_model_discovery()


@lru_cache()
def get_model_availability_manager_dependency():
    """
    FastAPI dependency for model availability manager.

    Returns:
        ModelAvailabilityManager instance or None if unavailable

    Usage:
        @app.get("/models/{model_id}/availability")
        def check_model_availability(
            model_id: str,
            manager = Depends(get_model_availability_manager_dependency)
        ):
            if not manager:
                raise HTTPException(status_code=503, detail="Model availability manager unavailable")
            return manager.check_availability(model_id)
    """
    factory = get_integration_service_factory()
    return (
        factory.get_service("model_availability_manager")
        or factory.create_model_availability_manager()
    )


# Voice and video dependencies
@lru_cache()
def get_voice_registry_dependency():
    """
    FastAPI dependency for voice registry.

    Returns:
        VoiceRegistry instance or None if unavailable

    Usage:
        @app.get("/voice/providers")
        def list_voice_providers(
            registry = Depends(get_voice_registry_dependency)
        ):
            if not registry:
                raise HTTPException(status_code=503, detail="Voice registry unavailable")
            return registry.get_all_providers()
    """
    factory = get_integration_service_factory()
    return factory.get_service("voice_registry") or factory.create_voice_registry()


@lru_cache()
def get_video_registry_dependency():
    """
    FastAPI dependency for video registry.

    Returns:
        VideoRegistry instance or None if unavailable

    Usage:
        @app.get("/video/providers")
        def list_video_providers(
            registry = Depends(get_video_registry_dependency)
        ):
            if not registry:
                raise HTTPException(status_code=503, detail="Video registry unavailable")
            return registry.get_all_providers()
    """
    factory = get_integration_service_factory()
    return factory.get_service("video_registry") or factory.create_video_registry()


# Advanced feature dependencies
@lru_cache()
def get_confidence_scorer_dependency():
    """
    FastAPI dependency for confidence scorer.

    Returns:
        ConfidenceScorer instance or None if unavailable

    Usage:
        @app.post("/score/confidence")
        def score_confidence(
            response: str,
            scorer = Depends(get_confidence_scorer_dependency)
        ):
            if not scorer:
                raise HTTPException(status_code=503, detail="Confidence scorer unavailable")
            return scorer.score(response)
    """
    factory = get_integration_service_factory()
    return factory.get_service("confidence_scorer") or factory.create_confidence_scorer()


@lru_cache()
def get_task_analyzer_dependency():
    """
    FastAPI dependency for task analyzer.

    Returns:
        TaskAnalyzer instance or None if unavailable

    Usage:
        @app.post("/analyze/task")
        def analyze_task(
            task: str,
            analyzer = Depends(get_task_analyzer_dependency)
        ):
            if not analyzer:
                raise HTTPException(status_code=503, detail="Task analyzer unavailable")
            return analyzer.analyze(task)
    """
    factory = get_integration_service_factory()
    return factory.get_service("task_analyzer") or factory.create_task_analyzer()


@lru_cache()
def get_failure_pattern_analyzer_dependency():
    """
    FastAPI dependency for failure pattern analyzer.

    Returns:
        FailurePatternAnalyzer instance or None if unavailable

    Usage:
        @app.get("/failures/patterns")
        def get_failure_patterns(
            analyzer = Depends(get_failure_pattern_analyzer_dependency)
        ):
            if not analyzer:
                raise HTTPException(status_code=503, detail="Failure pattern analyzer unavailable")
            return analyzer.get_patterns()
    """
    factory = get_integration_service_factory()
    return (
        factory.get_service("failure_pattern_analyzer")
        or factory.create_failure_pattern_analyzer()
    )


# Factory dependency
@lru_cache()
def get_integration_factory_dependency():
    """
    FastAPI dependency for integration service factory.

    Returns:
        IntegrationServiceFactory instance

    Usage:
        @app.get("/integrations/status")
        def get_integration_status(
            factory = Depends(get_integration_factory_dependency)
        ):
            return factory.health_check()
    """
    return get_integration_service_factory()


# Health check dependency
def get_integration_health_check():
    """
    FastAPI dependency for integration service health check.

    Returns:
        Dictionary of integration service health statuses

    Usage:
        @app.get("/health/integrations")
        def integration_health(health: dict = Depends(get_integration_health_check)):
            return health
    """
    factory = get_integration_service_factory()
    return factory.health_check()


# Combined router dependency (returns best available router)
def get_best_available_router():
    """
    FastAPI dependency that returns the best available router.

    Preference order:
    1. LLM Router (most comprehensive)
    2. Capability Router (capability-aware)
    3. Copilot Router (code-focused)

    Returns:
        Best available router instance or None

    Usage:
        @app.post("/route/auto")
        def route_automatically(
            request: dict,
            router = Depends(get_best_available_router)
        ):
            if not router:
                raise HTTPException(status_code=503, detail="No router available")
            return router.route(request)
    """
    factory = get_integration_service_factory()

    # Try routers in preference order
    routers_to_try = [
        ("llm_router", factory.create_llm_router),
        ("capability_router", factory.create_capability_router),
        ("copilot_router", factory.create_copilot_router),
    ]

    for router_name, create_fn in routers_to_try:
        router = factory.get_router(router_name)
        if router:
            return router

        # Try to create if not exists
        try:
            router = create_fn()
            if router:
                return router
        except Exception:
            continue

    return None


__all__ = [
    # Registry dependencies
    "get_provider_registry_dependency",
    "get_voice_registry_dependency",
    "get_video_registry_dependency",
    # Router dependencies
    "get_llm_router_dependency",
    "get_capability_router_dependency",
    "get_copilot_router_dependency",
    # Fallback and recovery
    "get_fallback_manager_dependency",
    "get_error_recovery_dependency",
    "get_failure_pattern_analyzer_dependency",
    # Model management
    "get_model_discovery_dependency",
    "get_model_availability_manager_dependency",
    # Advanced features
    "get_confidence_scorer_dependency",
    "get_task_analyzer_dependency",
    # Factory
    "get_integration_factory_dependency",
    "get_integration_health_check",
    # Utilities
    "get_best_available_router",
]
