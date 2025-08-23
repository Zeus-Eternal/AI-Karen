"""
Intelligent LLM Router API Routes

This module provides API endpoints for the intelligent LLM router system,
including routing decisions, dry-run analysis, health monitoring, and policy management.

Key Features:
- Route requests with explainable decisions
- Dry-run analysis for debugging and optimization
- Health monitoring and status endpoints
- Policy management and configuration
- Routing statistics and analytics
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai_karen_engine.utils.dependency_checks import import_fastapi, import_pydantic

APIRouter, HTTPException, Depends, Request = import_fastapi(
    "APIRouter", "HTTPException", "Depends", "Request"
)
BaseModel, Field = import_pydantic("BaseModel", "Field")

from ai_karen_engine.integrations.llm_router import (
    IntelligentLLMRouter,
    RoutingRequest,
    RouteDecision,
    TaskType,
    PrivacyLevel,
    PerformanceRequirement,
)
from ai_karen_engine.integrations.routing_policies import get_policy_manager
from ai_karen_engine.integrations.registry import get_registry
from ai_karen_engine.core.degraded_mode import get_degraded_mode_manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["intelligent-router"])

# Global router instance
_global_router: Optional[IntelligentLLMRouter] = None


def get_intelligent_router() -> IntelligentLLMRouter:
    """Get the global intelligent router instance."""
    global _global_router
    if _global_router is None:
        _global_router = IntelligentLLMRouter()
    return _global_router


# Request/Response Models

class RoutingRequestModel(BaseModel):
    """API model for routing requests."""
    prompt: str = Field(description="Input prompt to route")
    task_type: str = Field(default="chat", description="Type of task (chat, code, reasoning, etc.)")
    privacy_level: str = Field(default="public", description="Privacy level (public, internal, confidential, restricted)")
    performance_req: str = Field(default="interactive", description="Performance requirement (interactive, batch, background)")
    
    # User preferences
    preferred_provider: Optional[str] = Field(default=None, description="Preferred provider")
    preferred_model: Optional[str] = Field(default=None, description="Preferred model")
    preferred_runtime: Optional[str] = Field(default=None, description="Preferred runtime")
    
    # Context information
    user_id: Optional[str] = Field(default=None, description="User ID")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    context_length: Optional[int] = Field(default=None, description="Context length")
    
    # Additional requirements
    requires_streaming: bool = Field(default=False, description="Requires streaming support")
    requires_function_calling: bool = Field(default=False, description="Requires function calling")
    requires_vision: bool = Field(default=False, description="Requires vision capabilities")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=None, description="Sampling temperature")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RouteDecisionModel(BaseModel):
    """API model for routing decisions."""
    provider: str = Field(description="Selected provider")
    runtime: str = Field(description="Selected runtime")
    model_id: str = Field(description="Selected model ID")
    reason: str = Field(description="Reason for selection")
    confidence: float = Field(description="Confidence score (0-1)")
    fallback_chain: List[str] = Field(description="Fallback chain")
    estimated_cost: Optional[float] = Field(description="Estimated cost")
    estimated_latency: Optional[float] = Field(description="Estimated latency in seconds")
    privacy_compliant: bool = Field(description="Whether selection meets privacy requirements")
    capabilities: List[str] = Field(description="Provider capabilities")


class DryRunAnalysisModel(BaseModel):
    """API model for dry-run analysis results."""
    request_summary: Dict[str, Any] = Field(description="Summary of the request")
    routing_steps: List[Dict[str, Any]] = Field(description="Step-by-step routing analysis")
    available_providers: List[Dict[str, Any]] = Field(description="Available providers")
    available_runtimes: List[Dict[str, Any]] = Field(description="Available runtimes")
    policy_analysis: Dict[str, Any] = Field(description="Policy analysis results")
    final_recommendation: Optional[Dict[str, Any]] = Field(description="Final routing recommendation")
    alternative_options: List[Dict[str, Any]] = Field(description="Alternative routing options")
    error: Optional[str] = Field(default=None, description="Error message if analysis failed")


class HealthStatusModel(BaseModel):
    """API model for health status."""
    summary: Dict[str, Any] = Field(description="Health summary")
    healthy_providers: List[str] = Field(description="List of healthy providers")
    healthy_runtimes: List[str] = Field(description="List of healthy runtimes")
    unhealthy_components: Dict[str, Any] = Field(description="Unhealthy components")
    recent_events: List[Dict[str, Any]] = Field(description="Recent health events")
    recent_failovers: List[Dict[str, Any]] = Field(description="Recent failovers")


class RoutingStatsModel(BaseModel):
    """API model for routing statistics."""
    total_requests: int = Field(description="Total routing requests")
    successful_routes: int = Field(description="Successful routes")
    fallback_routes: int = Field(description="Fallback routes")
    degraded_routes: int = Field(description="Degraded mode routes")
    failed_routes: int = Field(description="Failed routes")
    active_policy: str = Field(description="Active routing policy")
    policy_weights: Dict[str, float] = Field(description="Policy weights")
    health_summary: Optional[Dict[str, Any]] = Field(default=None, description="Health summary")
    recent_health_events: Optional[int] = Field(default=None, description="Recent health events count")
    recent_failovers: Optional[int] = Field(default=None, description="Recent failovers count")


class PolicyInfoModel(BaseModel):
    """API model for policy information."""
    name: str = Field(description="Policy name")
    description: str = Field(description="Policy description")
    weights: Dict[str, float] = Field(description="Policy weights")
    fallback_providers: List[str] = Field(description="Fallback providers")
    fallback_runtimes: List[str] = Field(description="Fallback runtimes")


class DegradedModeStatusModel(BaseModel):
    """API model for degraded mode status."""
    is_active: bool = Field(description="Whether degraded mode is active")
    reason: Optional[str] = Field(description="Reason for degraded mode")
    activated_at: Optional[str] = Field(description="When degraded mode was activated")
    failed_providers: List[str] = Field(description="Failed providers")
    recovery_attempts: int = Field(description="Number of recovery attempts")
    last_recovery_attempt: Optional[str] = Field(description="Last recovery attempt timestamp")
    core_helpers_available: Dict[str, bool] = Field(description="Core helpers availability")


# API Endpoints

@router.post("/route", response_model=RouteDecisionModel)
async def route_request(
    request: RoutingRequestModel,
    intelligent_router: IntelligentLLMRouter = Depends(get_intelligent_router)
) -> RouteDecisionModel:
    """
    Route a request to the optimal provider and runtime.
    
    This endpoint performs intelligent routing based on the request parameters,
    user preferences, privacy requirements, and performance needs.
    """
    try:
        # Convert API model to internal model
        routing_request = RoutingRequest(
            prompt=request.prompt,
            task_type=TaskType(request.task_type),
            privacy_level=PrivacyLevel(request.privacy_level),
            performance_req=PerformanceRequirement(request.performance_req),
            preferred_provider=request.preferred_provider,
            preferred_model=request.preferred_model,
            preferred_runtime=request.preferred_runtime,
            user_id=request.user_id,
            session_id=request.session_id,
            context_length=request.context_length,
            requires_streaming=request.requires_streaming,
            requires_function_calling=request.requires_function_calling,
            requires_vision=request.requires_vision,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            metadata=request.metadata,
        )
        
        # Perform routing
        decision = intelligent_router.route(routing_request)
        
        # Convert to API model
        return RouteDecisionModel(**decision)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Routing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Routing failed: {str(e)}")


@router.post("/dry-run", response_model=DryRunAnalysisModel)
async def dry_run_analysis(
    request: RoutingRequestModel,
    intelligent_router: IntelligentLLMRouter = Depends(get_intelligent_router)
) -> DryRunAnalysisModel:
    """
    Perform dry-run analysis of routing decisions for debugging and optimization.
    
    This endpoint provides detailed analysis of the routing process without
    actually selecting a provider or runtime, useful for debugging and understanding
    routing decisions.
    """
    try:
        # Convert API model to internal model
        routing_request = RoutingRequest(
            prompt=request.prompt,
            task_type=TaskType(request.task_type),
            privacy_level=PrivacyLevel(request.privacy_level),
            performance_req=PerformanceRequirement(request.performance_req),
            preferred_provider=request.preferred_provider,
            preferred_model=request.preferred_model,
            preferred_runtime=request.preferred_runtime,
            user_id=request.user_id,
            session_id=request.session_id,
            context_length=request.context_length,
            requires_streaming=request.requires_streaming,
            requires_function_calling=request.requires_function_calling,
            requires_vision=request.requires_vision,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            metadata=request.metadata,
        )
        
        # Perform dry-run analysis
        analysis = intelligent_router.dry_run(routing_request)
        
        # Convert to API model
        return DryRunAnalysisModel(**analysis)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Dry-run analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Dry-run analysis failed: {str(e)}")


@router.get("/health", response_model=HealthStatusModel)
async def get_health_status(
    intelligent_router: IntelligentLLMRouter = Depends(get_intelligent_router)
) -> HealthStatusModel:
    """
    Get current health status of all providers and runtimes.
    
    This endpoint provides comprehensive health information including
    healthy/unhealthy components, recent events, and failover history.
    """
    try:
        health_status = intelligent_router.get_health_status()
        return HealthStatusModel(**health_status)
        
    except Exception as e:
        logger.error(f"Health status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health status check failed: {str(e)}")


@router.get("/stats", response_model=RoutingStatsModel)
async def get_routing_stats(
    intelligent_router: IntelligentLLMRouter = Depends(get_intelligent_router)
) -> RoutingStatsModel:
    """
    Get comprehensive routing statistics and analytics.
    
    This endpoint provides statistics about routing performance,
    success rates, fallback usage, and policy effectiveness.
    """
    try:
        stats = intelligent_router.get_routing_stats()
        return RoutingStatsModel(**stats)
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.post("/stats/reset")
async def reset_routing_stats(
    intelligent_router: IntelligentLLMRouter = Depends(get_intelligent_router)
) -> Dict[str, str]:
    """
    Reset routing statistics.
    
    This endpoint resets all routing statistics counters to zero.
    """
    try:
        intelligent_router.reset_routing_stats()
        return {"message": "Routing statistics reset successfully"}
        
    except Exception as e:
        logger.error(f"Stats reset failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats reset failed: {str(e)}")


@router.get("/policy", response_model=PolicyInfoModel)
async def get_current_policy(
    intelligent_router: IntelligentLLMRouter = Depends(get_intelligent_router)
) -> PolicyInfoModel:
    """
    Get information about the current routing policy.
    
    This endpoint provides details about the active routing policy
    including weights, fallback chains, and configuration.
    """
    try:
        policy_info = intelligent_router.get_policy_info()
        return PolicyInfoModel(**policy_info)
        
    except Exception as e:
        logger.error(f"Policy info retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Policy info retrieval failed: {str(e)}")


@router.get("/policies")
async def list_available_policies() -> Dict[str, List[str]]:
    """
    List all available routing policies.
    
    This endpoint returns a list of all available routing policies
    that can be used with the intelligent router.
    """
    try:
        policy_manager = get_policy_manager()
        policies = policy_manager.list_policies()
        return {"policies": policies}
        
    except Exception as e:
        logger.error(f"Policy listing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Policy listing failed: {str(e)}")


@router.post("/policy/{policy_name}")
async def set_routing_policy(
    policy_name: str,
    intelligent_router: IntelligentLLMRouter = Depends(get_intelligent_router)
) -> Dict[str, str]:
    """
    Set the active routing policy.
    
    This endpoint changes the active routing policy used by the
    intelligent router for future routing decisions.
    """
    try:
        policy_manager = get_policy_manager()
        policy = policy_manager.get_policy(policy_name)
        
        if not policy:
            raise HTTPException(status_code=404, detail=f"Policy '{policy_name}' not found")
        
        intelligent_router.update_policy(policy)
        return {"message": f"Routing policy updated to '{policy_name}'"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Policy update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Policy update failed: {str(e)}")


@router.get("/degraded-mode", response_model=DegradedModeStatusModel)
async def get_degraded_mode_status() -> DegradedModeStatusModel:
    """
    Get current degraded mode status.
    
    This endpoint provides information about whether degraded mode
    is active, the reason for activation, and core helpers availability.
    """
    try:
        degraded_mode_manager = get_degraded_mode_manager()
        status = degraded_mode_manager.get_status()
        
        return DegradedModeStatusModel(
            is_active=status.is_active,
            reason=status.reason.value if status.reason else None,
            activated_at=status.activated_at.isoformat() if status.activated_at else None,
            failed_providers=status.failed_providers,
            recovery_attempts=status.recovery_attempts,
            last_recovery_attempt=status.last_recovery_attempt.isoformat() if status.last_recovery_attempt else None,
            core_helpers_available=status.core_helpers_available,
        )
        
    except Exception as e:
        logger.error(f"Degraded mode status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Degraded mode status check failed: {str(e)}")


@router.post("/degraded-mode/recover")
async def attempt_degraded_mode_recovery() -> Dict[str, Any]:
    """
    Attempt to recover from degraded mode.
    
    This endpoint triggers a recovery attempt from degraded mode
    by checking if failed providers are now available.
    """
    try:
        degraded_mode_manager = get_degraded_mode_manager()
        
        if not degraded_mode_manager.get_status().is_active:
            return {"message": "Degraded mode is not active", "recovery_needed": False}
        
        recovery_successful = degraded_mode_manager.attempt_recovery()
        
        return {
            "message": "Recovery attempt completed",
            "recovery_successful": recovery_successful,
            "recovery_attempts": degraded_mode_manager.get_status().recovery_attempts,
        }
        
    except Exception as e:
        logger.error(f"Degraded mode recovery failed: {e}")
        raise HTTPException(status_code=500, detail=f"Degraded mode recovery failed: {str(e)}")


@router.get("/providers")
async def list_providers(
    healthy_only: bool = False,
    category: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List all registered providers with their status and capabilities.
    
    Args:
        healthy_only: Only return healthy providers
        category: Filter by provider category (LLM, embedding, etc.)
    """
    try:
        registry = get_registry()
        provider_names = registry.list_providers(category=category, healthy_only=healthy_only)
        
        providers = []
        for name in provider_names:
            spec = registry.get_provider_spec(name)
            health = registry.get_health_status(f"provider:{name}")
            
            providers.append({
                "name": name,
                "description": spec.description if spec else "",
                "category": spec.category if spec else "unknown",
                "requires_api_key": spec.requires_api_key if spec else False,
                "capabilities": list(spec.capabilities) if spec else [],
                "health_status": health.status if health else "unknown",
                "last_health_check": health.last_check if health else None,
            })
        
        return {"providers": providers}
        
    except Exception as e:
        logger.error(f"Provider listing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Provider listing failed: {str(e)}")


@router.get("/runtimes")
async def list_runtimes(
    healthy_only: bool = False
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List all registered runtimes with their status and capabilities.
    
    Args:
        healthy_only: Only return healthy runtimes
    """
    try:
        registry = get_registry()
        runtime_names = registry.list_runtimes(healthy_only=healthy_only)
        
        runtimes = []
        for name in runtime_names:
            spec = registry.get_runtime_spec(name)
            health = registry.get_health_status(f"runtime:{name}")
            
            runtimes.append({
                "name": name,
                "description": spec.description if spec else "",
                "family": spec.family if spec else [],
                "supports": spec.supports if spec else [],
                "requires_gpu": spec.requires_gpu if spec else False,
                "memory_efficient": spec.memory_efficient if spec else False,
                "supports_streaming": spec.supports_streaming if spec else False,
                "supports_batching": spec.supports_batching if spec else False,
                "startup_time": spec.startup_time if spec else "unknown",
                "throughput": spec.throughput if spec else "unknown",
                "priority": spec.priority if spec else 50,
                "health_status": health.status if health else "unknown",
                "last_health_check": health.last_check if health else None,
            })
        
        return {"runtimes": runtimes}
        
    except Exception as e:
        logger.error(f"Runtime listing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Runtime listing failed: {str(e)}")


@router.get("/compatibility/{model_id}")
async def get_model_compatibility(
    model_id: str,
    provider: str,
    family: Optional[str] = None,
    format: Optional[str] = None
) -> Dict[str, List[str]]:
    """
    Get compatible runtimes for a specific model.
    
    Args:
        model_id: Model identifier
        provider: Provider name
        family: Model family (optional)
        format: Model format (optional)
    """
    try:
        from ai_karen_engine.integrations.registry import ModelMetadata
        
        registry = get_registry()
        
        model_meta = ModelMetadata(
            id=model_id,
            name=model_id,
            provider=provider,
            family=family or "",
            format=format or "",
        )
        
        compatible_runtimes = registry.compatible_runtimes(model_meta)
        optimal_runtime = registry.optimal_runtime(model_meta)
        
        return {
            "compatible_runtimes": compatible_runtimes,
            "optimal_runtime": optimal_runtime,
        }
        
    except Exception as e:
        logger.error(f"Compatibility check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Compatibility check failed: {str(e)}")


# Health check endpoint for the router itself
@router.get("/router/health")
async def router_health_check() -> Dict[str, Any]:
    """
    Health check for the intelligent router system.
    
    This endpoint provides a quick health check of the router system
    including registry, policy manager, and degraded mode manager.
    """
    try:
        health_info = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        # Check registry
        try:
            registry = get_registry()
            provider_count = len(registry.list_providers())
            runtime_count = len(registry.list_runtimes())
            health_info["components"]["registry"] = {
                "status": "healthy",
                "providers": provider_count,
                "runtimes": runtime_count,
            }
        except Exception as e:
            health_info["components"]["registry"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_info["status"] = "degraded"
        
        # Check policy manager
        try:
            policy_manager = get_policy_manager()
            policy_count = len(policy_manager.list_policies())
            health_info["components"]["policy_manager"] = {
                "status": "healthy",
                "policies": policy_count,
            }
        except Exception as e:
            health_info["components"]["policy_manager"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_info["status"] = "degraded"
        
        # Check degraded mode manager
        try:
            degraded_mode_manager = get_degraded_mode_manager()
            degraded_status = degraded_mode_manager.get_status()
            health_info["components"]["degraded_mode"] = {
                "status": "healthy",
                "is_active": degraded_status.is_active,
                "core_helpers_available": degraded_status.core_helpers_available,
            }
        except Exception as e:
            health_info["components"]["degraded_mode"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_info["status"] = "degraded"
        
        return health_info
        
    except Exception as e:
        logger.error(f"Router health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }


__all__ = ["router"]