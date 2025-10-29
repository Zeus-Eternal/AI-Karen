"""
Extension Error Recovery API

Provides API endpoints for monitoring and managing the extension error recovery system.

Requirements addressed:
- 3.1: Extension integration service error handling
- 3.2: Extension API calls with proper authentication
- 3.3: Authentication failures and retry logic
- 9.1: Graceful degradation when authentication fails
- 9.2: Fallback behavior for extension unavailability
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

from .extension_error_recovery_manager import (
    get_extension_error_recovery_manager,
    ExtensionError,
    ErrorCategory,
    ErrorSeverity,
    RecoveryResult,
    create_extension_error,
    create_auth_token_expired_error,
    create_service_unavailable_error,
    create_network_error,
    create_permission_denied_error
)

from .extension_error_recovery_integration import (
    get_extension_error_recovery_integration,
    handle_extension_api_error,
    handle_extension_auth_error,
    handle_extension_service_unavailable,
    handle_extension_network_error
)

logger = logging.getLogger(__name__)

# Create router for error recovery endpoints
router = APIRouter(prefix="/api/extension-error-recovery", tags=["extension-error-recovery"])


@router.get("/status")
async def get_recovery_status() -> Dict[str, Any]:
    """Get the current status of the extension error recovery system"""
    try:
        recovery_manager = get_extension_error_recovery_manager()
        if not recovery_manager:
            return {
                "status": "not_initialized",
                "message": "Extension error recovery manager not initialized",
                "healthy": False
            }
        
        integration = get_extension_error_recovery_integration()
        integration_healthy = integration.is_healthy() if integration else False
        
        stats = recovery_manager.get_recovery_statistics()
        active_recoveries = recovery_manager.get_active_recoveries()
        
        return {
            "status": "active",
            "healthy": integration_healthy and not stats.get("circuit_breaker_open", False),
            "statistics": stats,
            "active_recoveries_count": len(active_recoveries),
            "integration_initialized": integration is not None,
            "integration_healthy": integration_healthy,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting recovery status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recovery status: {str(e)}"
        )


@router.get("/statistics")
async def get_recovery_statistics() -> Dict[str, Any]:
    """Get detailed recovery statistics"""
    try:
        recovery_manager = get_extension_error_recovery_manager()
        if not recovery_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Extension error recovery manager not initialized"
            )
        
        stats = recovery_manager.get_recovery_statistics()
        return {
            "statistics": stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recovery statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recovery statistics: {str(e)}"
        )


@router.get("/active-recoveries")
async def get_active_recoveries() -> Dict[str, Any]:
    """Get information about currently active recovery attempts"""
    try:
        recovery_manager = get_extension_error_recovery_manager()
        if not recovery_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Extension error recovery manager not initialized"
            )
        
        active_recoveries = recovery_manager.get_active_recoveries()
        return {
            "active_recoveries": active_recoveries,
            "count": len(active_recoveries),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active recoveries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active recoveries: {str(e)}"
        )


@router.post("/handle-error")
async def handle_error_endpoint(
    error_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle an extension error through the recovery system"""
    try:
        integration = get_extension_error_recovery_integration()
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Extension error recovery integration not initialized"
            )
        
        # Extract error information
        error_type = error_data.get("type", "unknown")
        endpoint = error_data.get("endpoint", "/api/extensions/")
        operation = error_data.get("operation", "extension_operation")
        message = error_data.get("message", "Unknown error")
        context = error_data.get("context", {})
        
        # Handle different error types
        if error_type == "http":
            status_code = error_data.get("status_code", 500)
            result = await integration.handle_http_error(status_code, endpoint, operation, context)
        elif error_type == "network":
            result = await integration.handle_network_error(endpoint, operation, message, context)
        elif error_type == "service":
            service_name = error_data.get("service_name", "unknown_service")
            result = await integration.handle_service_error(service_name, endpoint, operation, message, context)
        else:
            # Create generic error
            recovery_manager = get_extension_error_recovery_manager()
            if not recovery_manager:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Extension error recovery manager not initialized"
                )
            
            error = create_extension_error(
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.MEDIUM,
                code="GENERIC_ERROR",
                message=message,
                endpoint=endpoint,
                operation=operation,
                context=context
            )
            
            result = await recovery_manager.handle_error(error, context)
        
        return {
            "recovery_result": {
                "success": result.success,
                "strategy": result.strategy,
                "message": result.message,
                "fallback_data": result.fallback_data,
                "retry_after": result.retry_after,
                "requires_user_action": result.requires_user_action,
                "escalated": result.escalated
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling error through recovery system: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle error: {str(e)}"
        )


@router.post("/handle-auth-error")
async def handle_auth_error_endpoint(
    error_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle authentication error through the recovery system"""
    try:
        endpoint = error_data.get("endpoint", "/api/extensions/")
        operation = error_data.get("operation", "authentication")
        context = error_data.get("context", {})
        
        result = await handle_extension_auth_error(endpoint, operation, context)
        
        return {
            "recovery_result": {
                "success": result.success,
                "strategy": result.strategy,
                "message": result.message,
                "fallback_data": result.fallback_data,
                "retry_after": result.retry_after,
                "requires_user_action": result.requires_user_action,
                "escalated": result.escalated
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error handling auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle auth error: {str(e)}"
        )


@router.post("/handle-service-unavailable")
async def handle_service_unavailable_endpoint(
    error_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle service unavailable error through the recovery system"""
    try:
        service_name = error_data.get("service_name", "unknown_service")
        endpoint = error_data.get("endpoint", "/api/extensions/")
        operation = error_data.get("operation", "service_operation")
        context = error_data.get("context", {})
        
        result = await handle_extension_service_unavailable(service_name, endpoint, operation, context)
        
        return {
            "recovery_result": {
                "success": result.success,
                "strategy": result.strategy,
                "message": result.message,
                "fallback_data": result.fallback_data,
                "retry_after": result.retry_after,
                "requires_user_action": result.requires_user_action,
                "escalated": result.escalated
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error handling service unavailable error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle service unavailable error: {str(e)}"
        )


@router.post("/handle-network-error")
async def handle_network_error_endpoint(
    error_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle network error through the recovery system"""
    try:
        endpoint = error_data.get("endpoint", "/api/extensions/")
        operation = error_data.get("operation", "network_operation")
        message = error_data.get("message", "Network error")
        context = error_data.get("context", {})
        
        result = await handle_extension_network_error(endpoint, message, operation, context)
        
        return {
            "recovery_result": {
                "success": result.success,
                "strategy": result.strategy,
                "message": result.message,
                "fallback_data": result.fallback_data,
                "retry_after": result.retry_after,
                "requires_user_action": result.requires_user_action,
                "escalated": result.escalated
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error handling network error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle network error: {str(e)}"
        )


@router.post("/reset-circuit-breaker")
async def reset_circuit_breaker() -> Dict[str, Any]:
    """Reset the circuit breaker (admin function)"""
    try:
        recovery_manager = get_extension_error_recovery_manager()
        if not recovery_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Extension error recovery manager not initialized"
            )
        
        recovery_manager.force_circuit_breaker_reset()
        
        return {
            "message": "Circuit breaker reset successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting circuit breaker: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset circuit breaker: {str(e)}"
        )


@router.post("/clear-history")
async def clear_recovery_history() -> Dict[str, Any]:
    """Clear the recovery history (admin function)"""
    try:
        recovery_manager = get_extension_error_recovery_manager()
        if not recovery_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Extension error recovery manager not initialized"
            )
        
        recovery_manager.clear_recovery_history()
        
        return {
            "message": "Recovery history cleared successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing recovery history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear recovery history: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for the error recovery system"""
    try:
        recovery_manager = get_extension_error_recovery_manager()
        integration = get_extension_error_recovery_integration()
        
        if not recovery_manager:
            return {
                "healthy": False,
                "status": "recovery_manager_not_initialized",
                "message": "Extension error recovery manager not initialized",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        if not integration:
            return {
                "healthy": False,
                "status": "integration_not_initialized", 
                "message": "Extension error recovery integration not initialized",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Get health status from integration
        integration_healthy = integration.is_healthy()
        stats = recovery_manager.get_recovery_statistics()
        
        # Determine overall health
        circuit_breaker_open = stats.get("circuit_breaker_open", False)
        success_rate = stats.get("success_rate_24h", 1.0)
        active_recoveries_count = len(recovery_manager.get_active_recoveries())
        
        healthy = (
            integration_healthy and
            not circuit_breaker_open and
            success_rate >= 0.7 and  # At least 70% success rate
            active_recoveries_count < 10  # Not too many active recoveries
        )
        
        status_message = "healthy" if healthy else "degraded"
        issues = []
        
        if not integration_healthy:
            issues.append("integration_unhealthy")
        if circuit_breaker_open:
            issues.append("circuit_breaker_open")
        if success_rate < 0.7:
            issues.append(f"low_success_rate_{success_rate:.2%}")
        if active_recoveries_count >= 10:
            issues.append(f"too_many_active_recoveries_{active_recoveries_count}")
        
        return {
            "healthy": healthy,
            "status": status_message,
            "message": f"Recovery system is {status_message}" + (f" (issues: {', '.join(issues)})" if issues else ""),
            "details": {
                "integration_healthy": integration_healthy,
                "circuit_breaker_open": circuit_breaker_open,
                "success_rate_24h": success_rate,
                "active_recoveries_count": active_recoveries_count,
                "issues": issues
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in recovery system health check: {e}")
        return {
            "healthy": False,
            "status": "health_check_failed",
            "message": f"Health check failed: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/config")
async def get_recovery_config() -> Dict[str, Any]:
    """Get the current recovery system configuration"""
    try:
        recovery_manager = get_extension_error_recovery_manager()
        if not recovery_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Extension error recovery manager not initialized"
            )
        
        return {
            "config": recovery_manager.config,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recovery config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recovery config: {str(e)}"
        )


# Error handler for the router
@router.exception_handler(Exception)
async def recovery_api_exception_handler(request: Request, exc: Exception):
    """Global exception handler for recovery API endpoints"""
    logger.error(f"Unhandled exception in recovery API: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred in the recovery system",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


# Include the router in your main FastAPI app
def include_recovery_api_routes(app):
    """Include the recovery API routes in the main FastAPI app"""
    app.include_router(router)
    logger.info("Extension error recovery API routes included")


# Example usage in main app:
# from server.extension_error_recovery_api import include_recovery_api_routes
# include_recovery_api_routes(app)