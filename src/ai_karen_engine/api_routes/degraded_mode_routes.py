"""API routes for degraded mode management."""

import logging
from typing import Any, Dict

from ai_karen_engine.core.degraded_mode import get_degraded_mode_manager, DegradedModeReason
from ai_karen_engine.services.metrics_service import get_metrics_service

try:
    from fastapi import APIRouter, HTTPException, Depends
    from fastapi.responses import JSONResponse
except ImportError:
    from ai_karen_engine.fastapi_stub import APIRouter, HTTPException, Depends
    from ai_karen_engine.fastapi_stub.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["degraded-mode"])


@router.get("/degraded-mode")
async def get_degraded_mode_status() -> Dict[str, Any]:
    """Get current degraded mode status."""
    try:
        manager = get_degraded_mode_manager()
        status = manager.get_status()
        
        return {
            "is_active": status.is_active,
            "reason": status.reason.value if status.reason else None,
            "activated_at": status.activated_at.isoformat() if status.activated_at else None,
            "failed_providers": status.failed_providers,
            "recovery_attempts": status.recovery_attempts,
            "last_recovery_attempt": status.last_recovery_attempt.isoformat() if status.last_recovery_attempt else None,
            "core_helpers_available": status.core_helpers_available
        }
    except Exception as e:
        logger.error(f"Failed to get degraded mode status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get degraded mode status")


@router.get("/degraded-mode/health")
async def get_degraded_mode_health() -> Dict[str, Any]:
    """Get detailed health information for core helpers."""
    try:
        manager = get_degraded_mode_manager()
        health_summary = manager.get_health_summary()
        
        return health_summary
    except Exception as e:
        logger.error(f"Failed to get degraded mode health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get degraded mode health")


@router.post("/degraded-mode/recover")
async def attempt_recovery() -> Dict[str, Any]:
    """Attempt to recover from degraded mode."""
    try:
        manager = get_degraded_mode_manager()
        
        if not manager.get_status().is_active:
            return {
                "success": True,
                "message": "System is not in degraded mode",
                "recovered": False
            }
        
        # Attempt recovery
        recovered = manager.attempt_recovery()
        
        # Record metrics
        metrics_service = get_metrics_service()
        metrics_service.record_copilot_request(
            "degraded_mode_recovery_requested",
            correlation_id=f"recovery_{int(time.time())}"
        )
        
        return {
            "success": True,
            "message": "Recovery attempt initiated" if not recovered else "Recovery successful",
            "recovered": recovered,
            "recovery_attempts": manager.get_status().recovery_attempts
        }
        
    except Exception as e:
        logger.error(f"Failed to attempt recovery: {e}")
        raise HTTPException(status_code=500, detail="Failed to attempt recovery")


@router.post("/degraded-mode/activate")
async def activate_degraded_mode(
    reason: str = "manual_activation",
    failed_providers: list = None
) -> Dict[str, Any]:
    """Manually activate degraded mode (for testing/admin purposes)."""
    try:
        manager = get_degraded_mode_manager()
        
        # Validate reason
        try:
            degraded_reason = DegradedModeReason(reason)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid reason: {reason}")
        
        manager.activate_degraded_mode(degraded_reason, failed_providers or [])
        
        return {
            "success": True,
            "message": f"Degraded mode activated with reason: {reason}",
            "status": manager.get_status().__dict__
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate degraded mode: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate degraded mode")


@router.post("/degraded-mode/deactivate")
async def deactivate_degraded_mode() -> Dict[str, Any]:
    """Manually deactivate degraded mode."""
    try:
        manager = get_degraded_mode_manager()
        
        if not manager.get_status().is_active:
            return {
                "success": True,
                "message": "Degraded mode was not active",
                "was_active": False
            }
        
        manager.deactivate_degraded_mode()
        
        return {
            "success": True,
            "message": "Degraded mode deactivated",
            "was_active": True
        }
        
    except Exception as e:
        logger.error(f"Failed to deactivate degraded mode: {e}")
        raise HTTPException(status_code=500, detail="Failed to deactivate degraded mode")


@router.get("/degraded-mode/metrics")
async def get_degraded_mode_metrics() -> Dict[str, Any]:
    """Get metrics related to degraded mode operations."""
    try:
        metrics_service = get_metrics_service()
        
        # Get basic metrics summary
        stats = metrics_service.get_stats_summary()
        
        # Add degraded mode specific information
        manager = get_degraded_mode_manager()
        status = manager.get_status()
        
        degraded_metrics = {
            "current_status": {
                "is_active": status.is_active,
                "reason": status.reason.value if status.reason else None,
                "recovery_attempts": status.recovery_attempts
            },
            "core_helpers_health": status.core_helpers_available,
            "system_metrics": stats
        }
        
        return degraded_metrics
        
    except Exception as e:
        logger.error(f"Failed to get degraded mode metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get degraded mode metrics")


# Add time import that was missing
import time