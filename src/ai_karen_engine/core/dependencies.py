"""
Dependency Injection for AI Karen Engine Integration.

This module provides dependency injection helpers for FastAPI routes
and other components that need access to the integrated services.
"""

import logging
import os
from typing import Any, Dict

try:
    from fastapi import Depends, HTTPException, Request, status
except Exception:  # pragma: no cover
    from ai_karen_engine.fastapi_stub import HTTPException, status

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

logger = logging.getLogger(__name__)


def _get_default_user_context() -> Dict[str, Any]:
    """Return legacy default user context."""
    return {
        "user_id": "default_user",
        "email": "user@example.com",
        "full_name": "Default User",
        "roles": ["user", "admin"],
        "tenant_id": "default",
        "is_active": True,
    }


def _is_dev_auth_enabled() -> bool:
    """Check if development authentication fallback is permitted."""
    dev_mode = os.getenv("AUTH_DEV_MODE", "false").lower() in {"1", "true", "yes"}
    allow_login = os.getenv("AUTH_ALLOW_DEV_LOGIN", "false").lower() in {"1", "true", "yes"}
    return dev_mode or allow_login


def _get_dev_fallback_context() -> Dict[str, Any]:
    """Return a development fallback user context."""
    context = _get_default_user_context()
    context.update(
        {
            "user_id": "dev-user",
            "email": "dev@example.com",
            "full_name": "Development User",
            "roles": ["admin", "user"],
            "is_development_fallback": True,
        }
    )
    return context


# Configuration dependency
async def get_current_config() -> AIKarenConfig:
    """Get current configuration."""
    try:
        return get_config()
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(status_code=500, detail="Configuration unavailable")


# Authentication dependencies (no authentication required)
async def get_current_user_context(request: Request = None) -> Dict[str, Any]:
    """Resolve the current authenticated user context."""
    if request is None:
        raise HTTPException(status_code=500, detail="Request context unavailable")

    # Use cached user if middleware has already run
    cached_user = getattr(request.state, "user", None)
    if cached_user:
        return cached_user

    try:
        from src.auth.auth_middleware import get_auth_middleware
    except Exception as exc:
        logger.error("Failed to import authentication middleware: %s", exc)
        if _is_dev_auth_enabled():
            fallback = _get_dev_fallback_context()
            request.state.user = fallback
            return fallback
        raise HTTPException(status_code=503, detail="Authentication middleware unavailable")

    middleware = get_auth_middleware()

    try:
        user_context = await middleware.authenticate_request(request)
        request.state.user = user_context
        return user_context
    except HTTPException as exc:
        if _is_dev_auth_enabled() and exc.status_code in {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN}:
            fallback = _get_dev_fallback_context()
            request.state.user = fallback
            return fallback
        raise
    except Exception as exc:
        logger.error("Authentication processing error: %s", exc)
        if _is_dev_auth_enabled():
            fallback = _get_dev_fallback_context()
            request.state.user = fallback
            return fallback
        raise HTTPException(status_code=401, detail="Authentication failed")


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
    registry_error: Optional[Exception] = None

    try:
        registry = get_service_registry()
        return await registry.get_service("ai_orchestrator")
    except (ValueError, RuntimeError) as exc:
        # Service registry may not be initialized yet when lazy startup is enabled.
        registry_error = exc
        logger.debug("Service registry lookup for AI orchestrator failed: %s", exc)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to access AI orchestrator via registry: %s", exc)
        registry_error = exc

    # Fallback to lazy service registry when optimized startup defers instantiation.
    try:
        from ai_karen_engine.core.lazy_loading import lazy_registry, setup_lazy_services

        if not lazy_registry.list_services():
            await setup_lazy_services()

        service = await lazy_registry.get_service_instance("ai_orchestrator")
        if registry_error:
            logger.info(
                "Using lazy-loaded AI orchestrator because registry access failed: %s",
                registry_error,
            )
        return service
    except Exception as lazy_exc:
        logger.error("Lazy AI orchestrator initialization failed: %s", lazy_exc)
        if registry_error:
            logger.error("Registry error prior to lazy fallback: %s", registry_error)
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
