from src.auth.auth_middleware import require_auth
"""
Dependency Injection for AI Karen Engine Integration.

This module provides dependency injection helpers for FastAPI routes
and other components that need access to the integrated services.
"""

import logging
import os
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
# REMOVED: Complex auth service

logger = logging.getLogger(__name__)


def _env_truthy(name: str) -> bool:
    """Return True when an environment flag is enabled."""

    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _dev_auth_enabled() -> bool:
    """Determine whether development authentication fallbacks are allowed."""

    if _env_truthy("AUTH_DEV_MODE") or _env_truthy("AUTH_ALLOW_DEV_LOGIN"):
        return True

    auth_mode = os.getenv("AUTH_MODE", "").strip().lower()
    return auth_mode in {"development", "bypass"}


def _build_dev_user_context(request: Request) -> Dict[str, Any]:
    """Create a synthetic user context for development mode."""

    anon_id = os.getenv("AUTH_DEV_USER_ID", "dev-user")
    roles = os.getenv("AUTH_DEV_USER_ROLES", "admin,user").split(",")
    roles = [role.strip() for role in roles if role.strip()]
    if not roles:
        roles = ["admin", "user"]

    return {
        "user_id": anon_id,
        "email": f"{anon_id}@example.com",
        "full_name": os.getenv("AUTH_DEV_USER_NAME", "Development User"),
        "roles": roles,
        "tenant_id": "default",
        "token_payload": {
            "sub": anon_id,
            "roles": roles,
            "type": "development",
        },
        "auth_mode": os.getenv("AUTH_MODE", "development"),
        "is_development_fallback": True,
        "request_path": getattr(getattr(request, "url", None), "path", ""),
    }


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
    """Get authenticated user context using simple JWT auth."""

    allow_dev_fallback = _dev_auth_enabled()

    try:
        # Use simple auth middleware to get user
        from src.auth.auth_middleware import get_auth_middleware

        auth_middleware = get_auth_middleware()
        user_data = await auth_middleware.authenticate_request(request)
        if user_data:
            # Ensure tenant_id exists for compatibility
            if "tenant_id" not in user_data:
                user_data["tenant_id"] = "default"
            return user_data

        if allow_dev_fallback:
            logger.info(
                "Authentication skipped: dev fallback user applied for %s",
                getattr(getattr(request, "url", None), "path", "unknown"),
            )
            return _build_dev_user_context(request)

        raise HTTPException(status_code=401, detail="Authentication required")

    except HTTPException as exc:
        if allow_dev_fallback and exc.status_code == 401:
            logger.info(
                "Authentication failed with %s. Using dev fallback user for %s",
                exc.detail,
                getattr(getattr(request, "url", None), "path", "unknown"),
            )
            return _build_dev_user_context(request)
        raise
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        if allow_dev_fallback:
            logger.info(
                "Recovering from auth error with dev fallback user for %s",
                getattr(getattr(request, "url", None), "path", "unknown"),
            )
            return _build_dev_user_context(request)
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
