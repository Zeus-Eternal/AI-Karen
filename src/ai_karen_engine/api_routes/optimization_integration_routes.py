"""
API Routes for Optimization Integration

Provides REST API endpoints for managing and monitoring the integrated
optimization system while preserving existing functionality.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from ai_karen_engine.services.optimization_integration_orchestrator import (
    get_optimization_integration_orchestrator,
    initialize_optimization_integration,
    integrate_reasoning_system
)
from ai_karen_engine.services.optimization_configuration_manager import (
    get_optimization_config_manager,
    get_optimization_config
)

logger = logging.getLogger("kari.optimization_integration_routes")

# Create router
router = APIRouter(prefix="/api/optimization", tags=["optimization_integration"])

# Pydantic models for API
class IntegrationStatusResponse(BaseModel):
    initialized: bool
    initialization_error: Optional[str] = None
    component_status: Dict[str, Dict[str, Any]]
    integrated_components: List[str]
    configuration_summary: Dict[str, Any]
    model_management_status: Dict[str, Any]
    cache_system_metrics: Dict[str, Any]
    performance_monitoring_status: Dict[str, Any]
    reasoning_preservation_stats: Dict[str, Any]

class HealthCheckResponse(BaseModel):
    overall_health: str
    timestamp: str
    components: Dict[str, Dict[str, Any]]

class ConfigurationUpdateRequest(BaseModel):
    updates: Dict[str, Any]
    validate: bool = True

class ConfigurationResponse(BaseModel):
    optimization_enabled: bool
    optimization_level: str
    config_version: str
    last_updated: str
    components: Dict[str, bool]
    reasoning_preservation: Dict[str, bool]
    validation_status: bool
    auto_save_enabled: bool

class ModelIntegrationResponse(BaseModel):
    total_models: int
    discovered_models: int
    verified_models: int
    routing_enabled_models: int
    profile_mappings: Dict[str, int]
    last_refresh: float
    integration_health: Dict[str, float]

class PerformanceDashboardResponse(BaseModel):
    timestamp: str
    metrics_count: int
    aggregated_stats: Dict[str, Dict[str, float]]
    active_alerts: List[Dict[str, Any]]
    component_health: Dict[str, float]
    trends: Dict[str, str]

# Dependency to get orchestrator
async def get_orchestrator():
    """Dependency to get the optimization integration orchestrator."""
    return get_optimization_integration_orchestrator()

# Dependency to get config manager
async def get_config_manager():
    """Dependency to get the optimization configuration manager."""
    return get_optimization_config_manager()

@router.get("/status", response_model=IntegrationStatusResponse)
async def get_integration_status(orchestrator = Depends(get_orchestrator)):
    """Get comprehensive integration status."""
    try:
        status = orchestrator.get_integration_status()
        return IntegrationStatusResponse(**status)
    except Exception as e:
        logger.error(f"Failed to get integration status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/initialize")
async def initialize_integration(
    background_tasks: BackgroundTasks,
    orchestrator = Depends(get_orchestrator)
):
    """Initialize the optimization integration system."""
    try:
        if orchestrator._initialized:
            return {"message": "Integration already initialized", "status": "success"}
        
        # Initialize in background
        background_tasks.add_task(orchestrator.initialize_integration)
        
        return {
            "message": "Integration initialization started",
            "status": "initializing"
        }
    except Exception as e:
        logger.error(f"Failed to initialize integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=HealthCheckResponse)
async def health_check(orchestrator = Depends(get_orchestrator)):
    """Perform comprehensive health check of integrated system."""
    try:
        health_status = await orchestrator.health_check()
        return HealthCheckResponse(**health_status)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config", response_model=ConfigurationResponse)
async def get_configuration(config_manager = Depends(get_config_manager)):
    """Get current optimization configuration."""
    try:
        config_summary = config_manager.get_configuration_summary()
        return ConfigurationResponse(**config_summary)
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config")
async def update_configuration(
    request: ConfigurationUpdateRequest,
    config_manager = Depends(get_config_manager)
):
    """Update optimization configuration."""
    try:
        success = config_manager.update_configuration(
            request.updates,
            validate=request.validate
        )
        
        if success:
            return {
                "message": "Configuration updated successfully",
                "status": "success"
            }
        else:
            return {
                "message": "Configuration update failed validation",
                "status": "validation_failed"
            }
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config/reset")
async def reset_configuration(
    component: Optional[str] = None,
    config_manager = Depends(get_config_manager)
):
    """Reset configuration to defaults."""
    try:
        success = config_manager.reset_to_defaults(component)
        
        if success:
            return {
                "message": f"Configuration {'component ' + component if component else ''} reset to defaults",
                "status": "success"
            }
        else:
            return {
                "message": "Configuration reset failed",
                "status": "failed"
            }
    except Exception as e:
        logger.error(f"Failed to reset configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/validate")
async def validate_configuration(config_manager = Depends(get_config_manager)):
    """Validate current configuration."""
    try:
        validation_errors = config_manager.validate_configuration()
        
        return {
            "valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/integration", response_model=ModelIntegrationResponse)
async def get_model_integration_status(orchestrator = Depends(get_orchestrator)):
    """Get model integration status."""
    try:
        status = orchestrator.model_manager.get_integration_status()
        return ModelIntegrationResponse(**status)
    except Exception as e:
        logger.error(f"Failed to get model integration status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/refresh")
async def refresh_model_discovery(
    background_tasks: BackgroundTasks,
    orchestrator = Depends(get_orchestrator)
):
    """Refresh model discovery and integration."""
    try:
        # Refresh in background
        background_tasks.add_task(orchestrator.model_manager.refresh_model_discovery)
        
        return {
            "message": "Model discovery refresh started",
            "status": "refreshing"
        }
    except Exception as e:
        logger.error(f"Failed to refresh model discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/integrated")
async def get_integrated_models(orchestrator = Depends(get_orchestrator)):
    """Get all integrated models with their status."""
    try:
        # Get active profile
        profile_manager = orchestrator.model_manager.profile_manager
        active_profile = profile_manager.get_active_profile()
        
        if not active_profile:
            return {
                "models": [],
                "integration_status": {},
                "error": "No active profile found"
            }
        
        # Get models for active profile
        models = await orchestrator.model_manager.get_models_for_profile(active_profile.name)
        
        # Get integration status
        integration_status = {
            model["model_info"].id: {
                "model_id": model["integration_status"].model_id,
                "discovered": model["integration_status"].discovered,
                "profile_compatible": model["integration_status"].profile_compatible,
                "connection_verified": model["integration_status"].connection_verified,
                "routing_enabled": model["integration_status"].routing_enabled,
                "last_updated": model["integration_status"].last_updated,
                "error_message": model["integration_status"].error_message
            }
            for model in models if model["integration_status"]
        }
        
        # Format models for frontend
        formatted_models = []
        for model in models:
            model_info = model["model_info"]
            formatted_models.append({
                "id": model_info.id,
                "name": model_info.name,
                "display_name": model_info.display_name,
                "type": model_info.type.value,
                "path": model_info.path,
                "size": model_info.size,
                "modalities": [
                    {
                        "type": mod.type.value,
                        "input_supported": mod.input_supported,
                        "output_supported": mod.output_supported,
                        "formats": mod.formats
                    }
                    for mod in model_info.modalities
                ],
                "capabilities": [cap.value for cap in model_info.capabilities],
                "requirements": {
                    "memory_mb": model_info.requirements.memory_mb if model_info.requirements else 0,
                    "gpu_required": model_info.requirements.gpu_required if model_info.requirements else False,
                    "min_context_length": model_info.requirements.min_context_length if model_info.requirements else 0
                },
                "status": model_info.status.value,
                "metadata": {
                    "description": model_info.metadata.description if model_info.metadata else "",
                    "version": model_info.metadata.version if model_info.metadata else "",
                    "author": model_info.metadata.author if model_info.metadata else "",
                    "context_length": model_info.metadata.context_length if model_info.metadata else 0,
                    "parameter_count": model_info.metadata.parameter_count if model_info.metadata else None,
                    "quantization": model_info.metadata.quantization if model_info.metadata else None,
                    "use_cases": model_info.metadata.use_cases if model_info.metadata else [],
                    "language_support": model_info.metadata.language_support if model_info.metadata else []
                },
                "tags": model_info.tags,
                "category": {
                    "primary": model_info.category.primary,
                    "secondary": model_info.category.secondary,
                    "specialization": model_info.category.specialization
                }
            })
        
        return {
            "models": formatted_models,
            "integration_status": integration_status,
            "active_profile": active_profile.name
        }
        
    except Exception as e:
        logger.error(f"Failed to get integrated models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/integrated/{model_id}/routing")
async def toggle_model_routing(
    model_id: str,
    enable: bool,
    orchestrator = Depends(get_orchestrator)
):
    """Enable or disable routing for a specific model."""
    try:
        if enable:
            success = await orchestrator.model_manager.enable_model_routing(model_id)
        else:
            success = await orchestrator.model_manager.disable_model_routing(model_id)
        
        return {
            "message": f"Model routing {'enabled' if enable else 'disabled'} for {model_id}",
            "status": "success" if success else "failed",
            "model_id": model_id,
            "routing_enabled": enable if success else not enable
        }
    except Exception as e:
        logger.error(f"Failed to toggle model routing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/metrics")
async def get_cache_metrics(orchestrator = Depends(get_orchestrator)):
    """Get cache system metrics."""
    try:
        metrics = orchestrator.cache_system.get_integration_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get cache metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/optimize")
async def optimize_cache_performance(
    background_tasks: BackgroundTasks,
    orchestrator = Depends(get_orchestrator)
):
    """Optimize cache performance."""
    try:
        # Optimize in background
        background_tasks.add_task(orchestrator.cache_system.optimize_cache_performance)
        
        return {
            "message": "Cache optimization started",
            "status": "optimizing"
        }
    except Exception as e:
        logger.error(f"Failed to optimize cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/dashboard", response_model=PerformanceDashboardResponse)
async def get_performance_dashboard(orchestrator = Depends(get_orchestrator)):
    """Get performance dashboard data."""
    try:
        dashboard_data = orchestrator.performance_monitor.get_performance_dashboard_data()
        return PerformanceDashboardResponse(**dashboard_data)
    except Exception as e:
        logger.error(f"Failed to get performance dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/performance/alerts/{alert_id}/resolve")
async def resolve_performance_alert(
    alert_id: str,
    orchestrator = Depends(get_orchestrator)
):
    """Resolve a performance alert."""
    try:
        await orchestrator.performance_monitor.resolve_alert(alert_id)
        
        return {
            "message": f"Alert {alert_id} resolved",
            "status": "success",
            "alert_id": alert_id
        }
    except Exception as e:
        logger.error(f"Failed to resolve alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reasoning/preservation")
async def get_reasoning_preservation_stats(orchestrator = Depends(get_orchestrator)):
    """Get reasoning preservation statistics."""
    try:
        stats = orchestrator.reasoning_preservation_layer.get_reasoning_statistics()
        return stats
    except Exception as e:
        logger.error(f"Failed to get reasoning preservation stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/shutdown")
async def shutdown_integration(
    background_tasks: BackgroundTasks,
    orchestrator = Depends(get_orchestrator)
):
    """Shutdown the optimization integration system."""
    try:
        # Shutdown in background
        background_tasks.add_task(orchestrator.shutdown)
        
        return {
            "message": "Integration shutdown initiated",
            "status": "shutting_down"
        }
    except Exception as e:
        logger.error(f"Failed to shutdown integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Export router
__all__ = ["router"]