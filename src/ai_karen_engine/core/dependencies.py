"""
Dependency Injection for AI Karen Engine Integration.

This module provides dependency injection helpers for FastAPI routes
and other components that need access to the integrated services.
"""

import logging
import time
from typing import Any, Dict, Optional

try:
    from fastapi import Depends, HTTPException, Request
except Exception:  # pragma: no cover
    from ai_karen_engine.fastapi_stub import HTTPException

    def Depends(func):
        return func


from ai_karen_engine.core.config_manager import AIKarenConfig, get_config
from ai_karen_engine.core.health_monitor import HealthMonitor, get_health_monitor
from ai_karen_engine.core.service_registry import (
    AIOrchestrator,
    AnalyticsService,
    PluginService,
    ToolService,
    WebUIConversationService,
    WebUIMemoryService,
    get_service_registry,
)
from ai_karen_engine.auth.service import get_auth_service

logger = logging.getLogger(__name__)


# Configuration dependency
async def get_current_config() -> AIKarenConfig:
    """Get current configuration."""
    try:
        return get_config()
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(status_code=500, detail="Configuration unavailable")


# Authentication dependencies
async def get_current_user_context(request: Request) -> Dict[str, Any]:
    """Get authenticated user context from session token or JWT access token."""
    from ai_karen_engine.services.correlation_service import auth_event, Phase, get_request_id
    
    # Get correlation ID for this request
    correlation_id = getattr(request.state, "correlation_id", get_request_id())
    
    # Log authentication start
    auth_event(
        "session_validated",
        Phase.START,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        request_id=correlation_id,
        details={"stage": "start"},
        risk_score=0.0,
        security_flags=[],
        blocked_by_security=False,
        service_version="consolidated-auth-v1",
    )
    
    user_data = None
    auth_method = None
    processing_start = time.time()
    
    try:
        # First try to get session token from cookie
        session_token = request.cookies.get("kari_session")
        if session_token:
            auth_method = "session_cookie"
            # Use session-based authentication
            service = await get_auth_service()
            user_data = await service.validate_session(
                session_token=session_token,
                ip_address=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent", ""),
            )
            if user_data:
                # Log successful authentication
                processing_time_ms = (time.time() - processing_start) * 1000
                auth_event(
                    "session_validated",
                    Phase.FINISH,
                    success=True,
                    user_id=user_data.get("user_id"),
                    email=user_data.get("email"),
                    auth_method=auth_method,
                    request_id=correlation_id,
                    processing_time_ms=processing_time_ms,
                    details={"stage": "finish", "method": auth_method},
                )
                return user_data
        
        # Try JWT access token from Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            auth_method = "jwt_bearer"
            access_token = auth_header.split(" ")[1]
            try:
                service = await get_auth_service()
                # Use the token manager to validate JWT access token
                token_payload = await service.core_auth.token_manager.validate_access_token(access_token)
                
                # Convert JWT payload to user data format
                user_data = {
                    "user_id": token_payload.get("sub"),
                    "email": token_payload.get("email"),
                    "full_name": token_payload.get("full_name"),
                    "roles": token_payload.get("roles", []),
                    "tenant_id": token_payload.get("tenant_id"),
                    "preferences": token_payload.get("preferences", {}),
                    "two_factor_enabled": token_payload.get("two_factor_enabled", False),
                    "is_verified": token_payload.get("is_verified", False),
                    "is_active": token_payload.get("is_active", True),
                }
                
                # Log successful authentication
                processing_time_ms = (time.time() - processing_start) * 1000
                auth_event(
                    "session_validated",
                    Phase.FINISH,
                    success=True,
                    user_id=user_data.get("user_id"),
                    email=user_data.get("email"),
                    auth_method=auth_method,
                    request_id=correlation_id,
                    processing_time_ms=processing_time_ms,
                    details={"stage": "finish", "method": auth_method},
                )
                return user_data
            except Exception as e:
                # JWT validation failed, log and continue to raise auth error
                processing_time_ms = (time.time() - processing_start) * 1000
                auth_event(
                    "session_validated",
                    Phase.FINISH,
                    success=False,
                    auth_method=auth_method,
                    request_id=correlation_id,
                    processing_time_ms=processing_time_ms,
                    details={"stage": "finish", "method": auth_method, "error": str(e)},
                    error=str(e),
                )
        
        # No valid authentication found
        processing_time_ms = (time.time() - processing_start) * 1000
        auth_event(
            "session_validated",
            Phase.FINISH,
            success=False,
            auth_method=auth_method or "none",
            request_id=correlation_id,
            processing_time_ms=processing_time_ms,
            details={"stage": "finish", "method": auth_method or "none", "error": "No valid authentication"},
            error="No valid authentication found",
        )
        
    except Exception as e:
        # Log authentication failure
        processing_time_ms = (time.time() - processing_start) * 1000
        auth_event(
            "session_validated",
            Phase.FINISH,
            success=False,
            auth_method=auth_method or "unknown",
            request_id=correlation_id,
            processing_time_ms=processing_time_ms,
            details={"stage": "finish", "method": auth_method or "unknown", "error": str(e)},
            error=str(e),
        )
        raise HTTPException(status_code=401, detail="Authentication required")
    
    raise HTTPException(status_code=401, detail="Authentication required")


async def get_current_user_id(
    user_ctx: Dict[str, Any] = Depends(get_current_user_context)
) -> str:
    return user_ctx["user_id"]


async def get_current_tenant_id(
    user_ctx: Dict[str, Any] = Depends(get_current_user_context)
) -> str:
    return user_ctx["tenant_id"]


# Service dependencies
async def get_ai_orchestrator_service() -> AIOrchestrator:
    """Get AI Orchestrator service instance."""
    try:
        registry = get_service_registry()
        return await registry.get_service("ai_orchestrator")
    except Exception as e:
        logger.error(f"Failed to get AI Orchestrator service: {e}")
        raise HTTPException(
            status_code=503, detail="AI Orchestrator service unavailable"
        )


async def get_memory_service() -> WebUIMemoryService:
    """Get Memory service instance."""
    try:
        registry = get_service_registry()
        return await registry.get_service("memory_service")
    except Exception as e:
        logger.error(f"Failed to get Memory service: {e}")
        raise HTTPException(status_code=503, detail="Memory service unavailable")


async def get_conversation_service() -> WebUIConversationService:
    """Get Conversation service instance."""
    try:
        registry = get_service_registry()
        return await registry.get_service("conversation_service")
    except Exception as e:
        logger.error(f"Failed to get Conversation service: {e}")
        raise HTTPException(status_code=503, detail="Conversation service unavailable")


async def get_plugin_service() -> PluginService:
    """Get Plugin service instance."""
    try:
        registry = get_service_registry()
        return await registry.get_service("plugin_service")
    except Exception as e:
        logger.error(f"Failed to get Plugin service: {e}")
        raise HTTPException(status_code=503, detail="Plugin service unavailable")


async def get_tool_service() -> ToolService:
    """Get Tool service instance."""
    try:
        registry = get_service_registry()
        return await registry.get_service("tool_service")
    except Exception as e:
        logger.error(f"Failed to get Tool service: {e}")
        raise HTTPException(status_code=503, detail="Tool service unavailable")


async def get_analytics_service() -> AnalyticsService:
    """Get Analytics service instance."""
    try:
        registry = get_service_registry()
        return await registry.get_service("analytics_service")
    except Exception as e:
        logger.error(f"Failed to get Analytics service: {e}")
        raise HTTPException(status_code=503, detail="Analytics service unavailable")


# Health monitoring dependency
async def get_health_monitor_service() -> HealthMonitor:
    """Get Health Monitor service instance."""
    try:
        return get_health_monitor()
    except Exception as e:
        logger.error(f"Failed to get Health Monitor: {e}")
        raise HTTPException(status_code=503, detail="Health Monitor unavailable")


# Service registry dependency
async def get_service_registry_instance():
    """Get Service Registry instance."""
    try:
        return get_service_registry()
    except Exception as e:
        logger.error(f"Failed to get Service Registry: {e}")
        raise HTTPException(status_code=503, detail="Service Registry unavailable")


# Convenience dependencies for common combinations
async def get_ai_services() -> tuple[
    AIOrchestrator, WebUIMemoryService, WebUIConversationService
]:
    """Get core AI services (orchestrator, memory, conversation)."""
    try:
        registry = get_service_registry()
        orchestrator = await registry.get_service("ai_orchestrator")
        memory = await registry.get_service("memory_service")
        conversation = await registry.get_service("conversation_service")
        return orchestrator, memory, conversation
    except Exception as e:
        logger.error(f"Failed to get AI services: {e}")
        raise HTTPException(status_code=503, detail="AI services unavailable")


async def get_execution_services() -> tuple[PluginService, ToolService]:
    """Get execution services (plugin, tool)."""
    try:
        registry = get_service_registry()
        plugin = await registry.get_service("plugin_service")
        tool = await registry.get_service("tool_service")
        return plugin, tool
    except Exception as e:
        logger.error(f"Failed to get execution services: {e}")
        raise HTTPException(status_code=503, detail="Execution services unavailable")


# FastAPI dependency aliases for easier use in routes
AIOrchestrator_Dep = Depends(get_ai_orchestrator_service)
MemoryService_Dep = Depends(get_memory_service)
ConversationService_Dep = Depends(get_conversation_service)
PluginService_Dep = Depends(get_plugin_service)
ToolService_Dep = Depends(get_tool_service)
AnalyticsService_Dep = Depends(get_analytics_service)
Config_Dep = Depends(get_current_config)
HealthMonitor_Dep = Depends(get_health_monitor_service)
ServiceRegistry_Dep = Depends(get_service_registry_instance)
UserContext_Dep = Depends(get_current_user_context)
UserId_Dep = Depends(get_current_user_id)
TenantId_Dep = Depends(get_current_tenant_id)
