"""
Error Recovery and Graceful Degradation API Routes

This module provides API endpoints for error recovery system monitoring,
configuration, and manual intervention capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from ..services.graceful_degradation_coordinator import (
    graceful_degradation_coordinator,
    DegradationContext,
    SystemHealthStatus,
    DegradationLevel
)
from ..services.error_recovery_system import (
    error_recovery_system,
    ErrorType,
    RecoveryStrategy
)
from ..services.model_availability_handler import (
    model_availability_handler,
    ModelAvailabilityStatus
)
from ..services.timeout_performance_handler import (
    timeout_performance_handler
)
from ..services.memory_exhaustion_handler import (
    memory_exhaustion_handler,
    MemoryPressureLevel
)
from ..services.streaming_interruption_handler import (
    streaming_interruption_handler
)

from ..core.types.shared_types import Modality, ModalityType


# Pydantic models for API requests/responses
class SystemHealthResponse(BaseModel):
    overall_status: str
    degradation_level: int
    available_models: List[str]
    unavailable_models: List[str]
    memory_pressure: str
    active_recoveries: int
    recommendations: List[str]
    timestamp: float


class ErrorRecoveryRequest(BaseModel):
    query: str
    error_message: str
    model_id: Optional[str] = None
    modalities: List[str] = Field(default_factory=list)


class ErrorRecoveryResponse(BaseModel):
    success: bool
    recovered_content: str
    strategy_used: Optional[str] = None
    fallback_model: Optional[str] = None
    degradation_level: int
    recovery_time: float
    warnings: List[str] = Field(default_factory=list)


class ModelAvailabilityResponse(BaseModel):
    model_id: str
    status: str
    response_time: float
    error_message: Optional[str] = None
    load_percentage: float


class MemoryStatusResponse(BaseModel):
    usage_percentage: float
    pressure_level: str
    available_gb: float
    used_gb: float
    total_gb: float


class PerformanceRecommendationResponse(BaseModel):
    recommendations: List[Dict[str, Any]]
    current_metrics: Dict[str, float]


class RecoveryStatisticsResponse(BaseModel):
    error_recovery: Dict[str, Any]
    model_availability: Dict[str, Any]
    memory_exhaustion: Dict[str, Any]
    streaming_interruption: Dict[str, Any]
    overall_stats: Dict[str, Any]


# Create router
router = APIRouter(prefix="/api/error-recovery", tags=["Error Recovery"])
logger = logging.getLogger(__name__)


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health():
    """
    Get comprehensive system health status including degradation level,
    model availability, and performance metrics.
    """
    try:
        health_report = await graceful_degradation_coordinator.assess_system_health()
        
        return SystemHealthResponse(
            overall_status=health_report.overall_status.value,
            degradation_level=health_report.degradation_level.value,
            available_models=health_report.available_models,
            unavailable_models=health_report.unavailable_models,
            memory_pressure=health_report.memory_pressure.value,
            active_recoveries=health_report.active_recoveries,
            recommendations=health_report.recommendations,
            timestamp=health_report.timestamp
        )
        
    except Exception as e:
        logger.error(f"Failed to get system health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recover", response_model=ErrorRecoveryResponse)
async def recover_from_error(request: ErrorRecoveryRequest):
    """
    Manually trigger error recovery for a specific query and error.
    """
    try:
        # Convert modalities from strings
        modalities = []
        for modality_str in request.modalities:
            try:
                modality_type = ModalityType(modality_str.lower())
                modalities.append(Modality(
                    type=modality_type,
                    input_supported=True,
                    output_supported=True
                ))
            except ValueError:
                logger.warning(f"Unknown modality type: {modality_str}")
        
        # Create a mock exception from error message
        mock_error = Exception(request.error_message)
        
        # Perform coordinated recovery
        recovery_response = await graceful_degradation_coordinator.handle_coordinated_recovery(
            query=request.query,
            error=mock_error,
            model_id=request.model_id,
            modalities=modalities
        )
        
        return ErrorRecoveryResponse(
            success=True,
            recovered_content=recovery_response.content,
            strategy_used=None,  # Would be set by actual recovery
            fallback_model=recovery_response.model_used,
            degradation_level=recovery_response.degradation_level.value,
            recovery_time=recovery_response.response_time,
            warnings=recovery_response.warnings
        )
        
    except Exception as e:
        logger.error(f"Error recovery failed: {str(e)}")
        return ErrorRecoveryResponse(
            success=False,
            recovered_content="",
            degradation_level=DegradationLevel.EMERGENCY.value,
            recovery_time=0.0,
            warnings=[f"Recovery failed: {str(e)}"]
        )


@router.get("/models/{model_id}/availability", response_model=ModelAvailabilityResponse)
async def check_model_availability(model_id: str):
    """
    Check the availability status of a specific model.
    """
    try:
        health_check = await model_availability_handler.check_model_availability(model_id)
        
        return ModelAvailabilityResponse(
            model_id=model_id,
            status=health_check.status.value,
            response_time=health_check.response_time,
            error_message=health_check.error_message,
            load_percentage=health_check.load_percentage
        )
        
    except Exception as e:
        logger.error(f"Model availability check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/fallback")
async def get_fallback_models(
    failed_model: str = Query(..., description="The failed model ID"),
    modalities: List[str] = Query(default=[], description="Required modalities")
):
    """
    Get fallback model recommendations for a failed model.
    """
    try:
        from ..services.model_availability_handler import ModalityRequirement
        
        # Convert modalities to requirements
        modality_requirements = []
        for modality_str in modalities:
            try:
                modality_type = ModalityType(modality_str.lower())
                modality_requirements.append(ModalityRequirement(
                    modality_type=modality_type,
                    input_required=True,
                    output_required=True
                ))
            except ValueError:
                logger.warning(f"Unknown modality type: {modality_str}")
        
        # Find fallback candidates
        candidates = await model_availability_handler.find_fallback_models(
            failed_model_id=failed_model,
            modality_requirements=modality_requirements,
            max_candidates=5
        )
        
        return {
            "failed_model": failed_model,
            "fallback_candidates": [
                {
                    "model_id": candidate.model_info.id,
                    "model_name": candidate.model_info.display_name,
                    "compatibility_score": candidate.compatibility_score,
                    "estimated_performance": candidate.estimated_performance,
                    "availability_score": candidate.availability_score,
                    "modality_coverage": {
                        modality.value: coverage 
                        for modality, coverage in candidate.modality_coverage.items()
                    }
                }
                for candidate in candidates
            ]
        }
        
    except Exception as e:
        logger.error(f"Fallback model lookup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/status", response_model=MemoryStatusResponse)
async def get_memory_status():
    """
    Get current memory status and pressure level.
    """
    try:
        memory_status = await memory_exhaustion_handler.monitor_memory_status()
        
        return MemoryStatusResponse(
            usage_percentage=memory_status.usage_percentage,
            pressure_level=memory_status.pressure_level.value,
            available_gb=memory_status.available_memory / (1024**3),
            used_gb=memory_status.used_memory / (1024**3),
            total_gb=memory_status.total_memory / (1024**3)
        )
        
    except Exception as e:
        logger.error(f"Memory status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/recover")
async def trigger_memory_recovery(
    query: str = Body(..., description="Query context for recovery")
):
    """
    Manually trigger memory recovery and optimization.
    """
    try:
        recovery_result = await memory_exhaustion_handler.handle_memory_exhaustion(query)
        
        return {
            "success": recovery_result.success,
            "memory_freed_mb": recovery_result.memory_freed / (1024**2),
            "optimizations_applied": [
                {
                    "strategy": opt.strategy.value,
                    "description": opt.description,
                    "success": opt.success,
                    "memory_saved_mb": opt.actual_savings / (1024**2)
                }
                for opt in recovery_result.optimizations_applied
            ],
            "final_memory_usage": recovery_result.final_memory_status.usage_percentage,
            "recovery_time": recovery_result.recovery_time,
            "fallback_response": recovery_result.fallback_response
        }
        
    except Exception as e:
        logger.error(f"Memory recovery failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/recommendations", response_model=PerformanceRecommendationResponse)
async def get_performance_recommendations(
    model_id: Optional[str] = Query(None, description="Model ID for specific recommendations")
):
    """
    Get performance optimization recommendations.
    """
    try:
        if model_id:
            recommendations = await timeout_performance_handler.get_performance_recommendations(model_id)
            
            # Get recent metrics for the model
            recent_metrics = await timeout_performance_handler._get_recent_performance_metrics(model_id)
            current_metrics = {}
            
            if recent_metrics:
                latest = recent_metrics[-1]
                current_metrics = {
                    "response_time": latest.response_time,
                    "cpu_usage": latest.cpu_usage,
                    "memory_usage": latest.memory_usage
                }
        else:
            recommendations = []
            current_metrics = {}
        
        return PerformanceRecommendationResponse(
            recommendations=recommendations,
            current_metrics=current_metrics
        )
        
    except Exception as e:
        logger.error(f"Performance recommendations failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=RecoveryStatisticsResponse)
async def get_recovery_statistics():
    """
    Get comprehensive recovery and error handling statistics.
    """
    try:
        # Get statistics from all components
        memory_stats = await memory_exhaustion_handler.get_memory_statistics()
        streaming_stats = await streaming_interruption_handler.get_recovery_statistics()
        system_status = await graceful_degradation_coordinator.get_system_status()
        
        return RecoveryStatisticsResponse(
            error_recovery={
                "total_recoveries": 0,  # Would be tracked by error recovery system
                "successful_recoveries": 0,
                "average_recovery_time": 0.0
            },
            model_availability={
                "health_checks_performed": 0,  # Would be tracked
                "models_available": len(system_status["health_report"]["available_models"]),
                "models_unavailable": len(system_status["health_report"]["unavailable_models"]),
                "circuit_breakers_open": 0
            },
            memory_exhaustion=memory_stats,
            streaming_interruption=streaming_stats,
            overall_stats=system_status["degradation_stats"]
        )
        
    except Exception as e:
        logger.error(f"Statistics retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/simulate-error")
async def simulate_error_for_testing(
    error_type: str = Body(..., description="Type of error to simulate"),
    query: str = Body("Test query", description="Test query"),
    model_id: Optional[str] = Body(None, description="Model ID for testing")
):
    """
    Simulate different types of errors for testing recovery mechanisms.
    """
    try:
        # Create appropriate error based on type
        error_map = {
            "timeout": asyncio.TimeoutError("Simulated timeout"),
            "memory": MemoryError("Simulated memory exhaustion"),
            "model_unavailable": Exception("Model not available"),
            "connection": ConnectionError("Simulated connection failure"),
            "streaming": Exception("Streaming interrupted")
        }
        
        if error_type not in error_map:
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown error type. Available: {list(error_map.keys())}"
            )
        
        simulated_error = error_map[error_type]
        
        # Test recovery
        recovery_response = await graceful_degradation_coordinator.handle_coordinated_recovery(
            query=query,
            error=simulated_error,
            model_id=model_id
        )
        
        return {
            "simulated_error_type": error_type,
            "recovery_successful": True,
            "recovered_content": recovery_response.content,
            "degradation_level": recovery_response.degradation_level.value,
            "fallback_applied": recovery_response.fallback_applied,
            "optimizations_applied": recovery_response.optimizations_applied,
            "response_time": recovery_response.response_time,
            "warnings": recovery_response.warnings
        }
        
    except Exception as e:
        logger.error(f"Error simulation failed: {str(e)}")
        return {
            "simulated_error_type": error_type,
            "recovery_successful": False,
            "error_message": str(e)
        }


@router.post("/configuration/update")
async def update_error_recovery_configuration(
    config: Dict[str, Any] = Body(..., description="Configuration updates")
):
    """
    Update error recovery system configuration.
    """
    try:
        updated_settings = {}
        
        # Update timeout settings
        if "timeouts" in config:
            timeout_config = config["timeouts"]
            if "model_loading" in timeout_config:
                timeout_performance_handler.timeout_config.model_loading = timeout_config["model_loading"]
                updated_settings["model_loading_timeout"] = timeout_config["model_loading"]
            
            if "inference" in timeout_config:
                timeout_performance_handler.timeout_config.inference = timeout_config["inference"]
                updated_settings["inference_timeout"] = timeout_config["inference"]
        
        # Update memory thresholds
        if "memory_thresholds" in config:
            memory_config = config["memory_thresholds"]
            for level, threshold in memory_config.items():
                if hasattr(MemoryPressureLevel, level.upper()):
                    pressure_level = MemoryPressureLevel[level.upper()]
                    memory_exhaustion_handler.memory_thresholds[pressure_level] = threshold
                    updated_settings[f"memory_{level}_threshold"] = threshold
        
        # Update performance thresholds
        if "performance_thresholds" in config:
            perf_config = config["performance_thresholds"]
            for metric, threshold in perf_config.items():
                if metric in timeout_performance_handler.performance_thresholds:
                    timeout_performance_handler.performance_thresholds[metric].warning_threshold = threshold.get("warning", 0)
                    timeout_performance_handler.performance_thresholds[metric].critical_threshold = threshold.get("critical", 0)
                    updated_settings[f"{metric}_thresholds"] = threshold
        
        return {
            "success": True,
            "updated_settings": updated_settings,
            "message": "Configuration updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Configuration update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configuration")
async def get_error_recovery_configuration():
    """
    Get current error recovery system configuration.
    """
    try:
        return {
            "timeouts": {
                "model_loading": timeout_performance_handler.timeout_config.model_loading,
                "inference": timeout_performance_handler.timeout_config.inference,
                "streaming_chunk": timeout_performance_handler.timeout_config.streaming_chunk,
                "health_check": timeout_performance_handler.timeout_config.health_check,
                "fallback_switch": timeout_performance_handler.timeout_config.fallback_switch
            },
            "memory_thresholds": {
                level.name.lower(): threshold
                for level, threshold in memory_exhaustion_handler.memory_thresholds.items()
            },
            "performance_thresholds": {
                name: {
                    "warning": threshold.warning_threshold,
                    "critical": threshold.critical_threshold,
                    "unit": threshold.unit
                }
                for name, threshold in timeout_performance_handler.performance_thresholds.items()
            },
            "optimization_settings": timeout_performance_handler.optimization_settings
        }
        
    except Exception as e:
        logger.error(f"Configuration retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))