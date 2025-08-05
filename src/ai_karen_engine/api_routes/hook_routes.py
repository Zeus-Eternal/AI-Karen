"""
FastAPI routes for hook management and monitoring.

This module provides endpoints for managing hooks in the unified hook system,
including registration, unregistration, monitoring, and execution statistics.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from fastapi import APIRouter, HTTPException, Depends, Query, Path
    from fastapi.responses import JSONResponse
except ImportError:
    # Stubs for testing
    class APIRouter:
        def __init__(self, **kwargs): 
            self.routes = []
            self.prefix = kwargs.get('prefix', '')
            self.tags = kwargs.get('tags', [])
        def get(self, path: str, **kwargs): return lambda f: f
        def post(self, path: str, **kwargs): return lambda f: f
        def delete(self, path: str, **kwargs): return lambda f: f
        def put(self, path: str, **kwargs): return lambda f: f
    
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str): pass
    
    class JSONResponse:
        def __init__(self, content: Dict, **kwargs): pass
    
    def Depends(func): return func
    def Query(default=None, **kwargs): return default
    def Path(**kwargs): return ""

try:
    from pydantic import BaseModel, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field

from ai_karen_engine.hooks import get_hook_manager, HookTypes, HookContext, HookRegistration
from ai_karen_engine.utils.auth import validate_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hooks", tags=["hooks"])


# Request/Response Models
class RegisterHookRequest(BaseModel):
    """Request model for registering a hook."""
    hook_type: str = Field(..., description="Type of hook to register")
    priority: int = Field(100, description="Hook priority (lower = higher priority)")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Conditions for hook execution")
    source_type: str = Field("api", description="Type of source registering the hook")
    source_name: Optional[str] = Field(None, description="Name of the source")
    enabled: bool = Field(True, description="Whether the hook is enabled")


class HookRegistrationResponse(BaseModel):
    """Response model for hook registration."""
    hook_id: str = Field(..., description="Unique hook ID")
    hook_type: str = Field(..., description="Type of hook")
    priority: int = Field(..., description="Hook priority")
    source_type: str = Field(..., description="Source type")
    source_name: Optional[str] = Field(None, description="Source name")
    enabled: bool = Field(..., description="Whether hook is enabled")
    registered_at: str = Field(..., description="Registration timestamp")


class TriggerHookRequest(BaseModel):
    """Request model for triggering hooks."""
    hook_type: str = Field(..., description="Type of hooks to trigger")
    data: Dict[str, Any] = Field(..., description="Hook execution data")
    user_context: Optional[Dict[str, Any]] = Field(None, description="User context")
    timeout_seconds: float = Field(30.0, description="Execution timeout")


class HookExecutionResponse(BaseModel):
    """Response model for hook execution."""
    hook_type: str = Field(..., description="Type of hooks executed")
    total_hooks: int = Field(..., description="Total hooks triggered")
    successful_hooks: int = Field(..., description="Successfully executed hooks")
    failed_hooks: int = Field(..., description="Failed hooks")
    total_execution_time_ms: float = Field(..., description="Total execution time")
    results: List[Dict[str, Any]] = Field(..., description="Individual hook results")


class HookStatsResponse(BaseModel):
    """Response model for hook statistics."""
    enabled: bool = Field(..., description="Whether hook manager is enabled")
    total_hooks: int = Field(..., description="Total registered hooks")
    hook_types: int = Field(..., description="Number of hook types")
    source_types: List[str] = Field(..., description="Source types")
    execution_stats: Dict[str, int] = Field(..., description="Execution statistics")


class HookListResponse(BaseModel):
    """Response model for listing hooks."""
    hooks: List[HookRegistrationResponse] = Field(..., description="List of hooks")
    total_count: int = Field(..., description="Total number of hooks")
    hook_types: List[str] = Field(..., description="Available hook types")


# Hook Management Endpoints
@router.post("/register", response_model=HookRegistrationResponse)
async def register_hook(
    request: RegisterHookRequest,
    # session: dict = Depends(validate_session)  # Temporarily disabled for web UI integration
):
    """
    Register a new hook with the hook system.
    
    This endpoint allows external systems to register hooks that will be
    triggered at specific points in the chat processing pipeline.
    """
    try:
        hook_manager = get_hook_manager()
        
        # Validate hook type
        if not HookTypes.is_valid_type(request.hook_type):
            logger.warning(f"Registering hook with non-standard type: {request.hook_type}")
        
        # Create a placeholder handler for API-registered hooks
        # In a real implementation, this would be more sophisticated
        async def api_hook_handler(context: HookContext) -> Dict[str, Any]:
            """Placeholder handler for API-registered hooks."""
            return {
                "hook_type": request.hook_type,
                "source_type": request.source_type,
                "source_name": request.source_name,
                "executed_at": datetime.utcnow().isoformat(),
                "data_keys": list(context.data.keys()),
                "message": f"API hook {request.hook_type} executed successfully"
            }
        
        # Register the hook
        hook_id = await hook_manager.register_hook(
            hook_type=request.hook_type,
            handler=api_hook_handler,
            priority=request.priority,
            conditions=request.conditions or {},
            source_type=request.source_type,
            source_name=request.source_name
        )
        
        # Get the registered hook for response
        hook_registration = hook_manager.get_hook_by_id(hook_id)
        if not hook_registration:
            raise HTTPException(status_code=500, detail="Failed to retrieve registered hook")
        
        logger.info(f"Hook registered via API: {hook_id} ({request.hook_type})")
        
        return HookRegistrationResponse(
            hook_id=hook_id,
            hook_type=hook_registration.hook_type,
            priority=hook_registration.priority,
            source_type=hook_registration.source_type,
            source_name=hook_registration.source_name,
            enabled=hook_registration.enabled,
            registered_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to register hook: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to register hook: {str(e)}")


@router.delete("/unregister/{hook_id}")
async def unregister_hook(
    hook_id: str = Path(..., description="Hook ID to unregister"),
    # session: dict = Depends(validate_session)  # Temporarily disabled for web UI integration
):
    """
    Unregister a hook from the hook system.
    """
    try:
        hook_manager = get_hook_manager()
        
        # Check if hook exists
        hook_registration = hook_manager.get_hook_by_id(hook_id)
        if not hook_registration:
            raise HTTPException(status_code=404, detail=f"Hook {hook_id} not found")
        
        # Unregister the hook
        success = await hook_manager.unregister_hook(hook_id)
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to unregister hook {hook_id}")
        
        logger.info(f"Hook unregistered via API: {hook_id}")
        
        return {
            "success": True,
            "message": f"Hook {hook_id} unregistered successfully",
            "hook_id": hook_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unregister hook {hook_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unregister hook: {str(e)}")


@router.post("/trigger", response_model=HookExecutionResponse)
async def trigger_hooks(
    request: TriggerHookRequest,
    # session: dict = Depends(validate_session)  # Temporarily disabled for web UI integration
):
    """
    Manually trigger hooks of a specific type.
    
    This endpoint allows testing and manual execution of hooks.
    """
    try:
        hook_manager = get_hook_manager()
        
        # Create hook context
        context = HookContext(
            hook_type=request.hook_type,
            data=request.data,
            user_context=request.user_context or {}
        )
        
        # Trigger hooks
        summary = await hook_manager.trigger_hooks(context, request.timeout_seconds)
        
        logger.info(f"Hooks triggered via API: {request.hook_type} - {summary.successful_hooks}/{summary.total_hooks} successful")
        
        return HookExecutionResponse(
            hook_type=summary.hook_type,
            total_hooks=summary.total_hooks,
            successful_hooks=summary.successful_hooks,
            failed_hooks=summary.failed_hooks,
            total_execution_time_ms=summary.total_execution_time_ms,
            results=[result.__dict__ for result in summary.results]
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger hooks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger hooks: {str(e)}")


# Hook Information Endpoints
@router.get("/list", response_model=HookListResponse)
async def list_hooks(
    hook_type: Optional[str] = Query(None, description="Filter by hook type"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    source_name: Optional[str] = Query(None, description="Filter by source name"),
    enabled_only: bool = Query(False, description="Show only enabled hooks"),
    # session: dict = Depends(validate_session)  # Temporarily disabled for web UI integration
):
    """
    List all registered hooks with optional filtering.
    """
    try:
        hook_manager = get_hook_manager()
        
        # Get hooks based on filters
        if hook_type:
            hooks = hook_manager.get_hooks_by_type(hook_type)
        elif source_type:
            hooks = hook_manager.get_hooks_by_source(source_type, source_name)
        else:
            hooks = hook_manager.get_all_hooks()
        
        # Filter by enabled status if requested
        if enabled_only:
            hooks = [hook for hook in hooks if hook.enabled]
        
        # Convert to response format
        hook_responses = []
        for hook in hooks:
            hook_responses.append(HookRegistrationResponse(
                hook_id=hook.id,
                hook_type=hook.hook_type,
                priority=hook.priority,
                source_type=hook.source_type,
                source_name=hook.source_name,
                enabled=hook.enabled,
                registered_at=datetime.utcnow().isoformat()  # Placeholder - would be actual registration time
            ))
        
        return HookListResponse(
            hooks=hook_responses,
            total_count=len(hook_responses),
            hook_types=hook_manager.get_hook_types()
        )
        
    except Exception as e:
        logger.error(f"Failed to list hooks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list hooks: {str(e)}")


@router.get("/types")
async def get_hook_types():
    """
    Get all available hook types.
    """
    try:
        standard_types = HookTypes.get_all_types()
        hook_manager = get_hook_manager()
        registered_types = hook_manager.get_hook_types()
        
        # Combine standard and registered types
        all_types = list(set(standard_types + registered_types))
        
        return {
            "standard_types": standard_types,
            "registered_types": registered_types,
            "all_types": sorted(all_types),
            "lifecycle_hooks": HookTypes.get_lifecycle_hooks(),
            "error_hooks": HookTypes.get_error_hooks()
        }
        
    except Exception as e:
        logger.error(f"Failed to get hook types: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get hook types: {str(e)}")


@router.get("/stats", response_model=HookStatsResponse)
async def get_hook_stats():
    """
    Get hook system statistics and status.
    """
    try:
        hook_manager = get_hook_manager()
        summary = hook_manager.get_summary()
        
        return HookStatsResponse(
            enabled=summary["enabled"],
            total_hooks=summary["total_hooks"],
            hook_types=summary["hook_types"],
            source_types=summary["source_types"],
            execution_stats=summary["execution_stats"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get hook stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get hook stats: {str(e)}")


@router.get("/{hook_id}")
async def get_hook_details(
    hook_id: str = Path(..., description="Hook ID"),
    # session: dict = Depends(validate_session)  # Temporarily disabled for web UI integration
):
    """
    Get detailed information about a specific hook.
    """
    try:
        hook_manager = get_hook_manager()
        hook_registration = hook_manager.get_hook_by_id(hook_id)
        
        if not hook_registration:
            raise HTTPException(status_code=404, detail=f"Hook {hook_id} not found")
        
        return {
            "hook_id": hook_registration.id,
            "hook_type": hook_registration.hook_type,
            "priority": hook_registration.priority,
            "conditions": hook_registration.conditions,
            "source_type": hook_registration.source_type,
            "source_name": hook_registration.source_name,
            "enabled": hook_registration.enabled,
            "handler_info": {
                "is_async": asyncio.iscoroutinefunction(hook_registration.handler),
                "handler_name": getattr(hook_registration.handler, '__name__', 'unknown')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get hook details for {hook_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get hook details: {str(e)}")


# Hook Management Operations
@router.put("/{hook_id}/enable")
async def enable_hook(
    hook_id: str = Path(..., description="Hook ID"),
    # session: dict = Depends(validate_session)  # Temporarily disabled for web UI integration
):
    """
    Enable a specific hook.
    """
    try:
        hook_manager = get_hook_manager()
        hook_registration = hook_manager.get_hook_by_id(hook_id)
        
        if not hook_registration:
            raise HTTPException(status_code=404, detail=f"Hook {hook_id} not found")
        
        hook_registration.enabled = True
        logger.info(f"Hook enabled via API: {hook_id}")
        
        return {
            "success": True,
            "message": f"Hook {hook_id} enabled successfully",
            "hook_id": hook_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable hook {hook_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enable hook: {str(e)}")


@router.put("/{hook_id}/disable")
async def disable_hook(
    hook_id: str = Path(..., description="Hook ID"),
    # session: dict = Depends(validate_session)  # Temporarily disabled for web UI integration
):
    """
    Disable a specific hook.
    """
    try:
        hook_manager = get_hook_manager()
        hook_registration = hook_manager.get_hook_by_id(hook_id)
        
        if not hook_registration:
            raise HTTPException(status_code=404, detail=f"Hook {hook_id} not found")
        
        hook_registration.enabled = False
        logger.info(f"Hook disabled via API: {hook_id}")
        
        return {
            "success": True,
            "message": f"Hook {hook_id} disabled successfully",
            "hook_id": hook_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable hook {hook_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disable hook: {str(e)}")


@router.delete("/clear/{source_type}")
async def clear_hooks_by_source(
    source_type: str = Path(..., description="Source type to clear"),
    source_name: Optional[str] = Query(None, description="Specific source name to clear"),
    # session: dict = Depends(validate_session)  # Temporarily disabled for web UI integration
):
    """
    Clear all hooks from a specific source.
    """
    try:
        hook_manager = get_hook_manager()
        cleared_count = await hook_manager.clear_hooks_by_source(source_type, source_name)
        
        logger.info(f"Cleared {cleared_count} hooks from source {source_type}/{source_name}")
        
        return {
            "success": True,
            "message": f"Cleared {cleared_count} hooks from source {source_type}",
            "cleared_count": cleared_count,
            "source_type": source_type,
            "source_name": source_name
        }
        
    except Exception as e:
        logger.error(f"Failed to clear hooks from source {source_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear hooks: {str(e)}")


# System Management Endpoints
@router.post("/system/enable")
async def enable_hook_system(
    # session: dict = Depends(validate_session)  # Temporarily disabled for web UI integration
):
    """
    Enable the entire hook system.
    """
    try:
        hook_manager = get_hook_manager()
        hook_manager.enable()
        
        logger.info("Hook system enabled via API")
        
        return {
            "success": True,
            "message": "Hook system enabled successfully",
            "enabled": True
        }
        
    except Exception as e:
        logger.error(f"Failed to enable hook system: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enable hook system: {str(e)}")


@router.post("/system/disable")
async def disable_hook_system(
    # session: dict = Depends(validate_session)  # Temporarily disabled for web UI integration
):
    """
    Disable the entire hook system.
    """
    try:
        hook_manager = get_hook_manager()
        hook_manager.disable()
        
        logger.info("Hook system disabled via API")
        
        return {
            "success": True,
            "message": "Hook system disabled successfully",
            "enabled": False
        }
        
    except Exception as e:
        logger.error(f"Failed to disable hook system: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disable hook system: {str(e)}")


@router.delete("/system/clear-stats")
async def clear_execution_stats(
    # session: dict = Depends(validate_session)  # Temporarily disabled for web UI integration
):
    """
    Clear hook execution statistics.
    """
    try:
        hook_manager = get_hook_manager()
        hook_manager.clear_execution_stats()
        
        logger.info("Hook execution statistics cleared via API")
        
        return {
            "success": True,
            "message": "Hook execution statistics cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to clear execution stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear execution stats: {str(e)}")


# Health check endpoint
@router.get("/health")
async def hook_system_health():
    """
    Health check for the hook system.
    """
    try:
        hook_manager = get_hook_manager()
        summary = hook_manager.get_summary()
        
        return {
            "status": "healthy" if summary["enabled"] else "disabled",
            "hook_manager": {
                "enabled": summary["enabled"],
                "total_hooks": summary["total_hooks"],
                "hook_types": summary["hook_types"],
                "source_types": summary["source_types"]
            },
            "execution_stats": summary["execution_stats"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Hook system health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }