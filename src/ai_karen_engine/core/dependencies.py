"""
Dependency Injection for AI Karen Engine Integration.

This module provides dependency injection helpers for FastAPI routes
and other components that need access to integrated services.
"""

import logging
import os
from typing import Any, Dict, Optional, Callable, Union, Literal, TYPE_CHECKING

# Define type alias for the dependency function signature
if TYPE_CHECKING:
    DependencyType = Optional[Callable[..., Any]]
else:
    DependencyType = Any

try:
    from fastapi import Depends, HTTPException, Request  # type: ignore[assignment]
except Exception:  # pragma: no cover
    from ai_karen_engine.fastapi_stub import HTTPException

    def Depends(
        dependency: Optional[Callable[..., Any]] = None,
        *,
        use_cache: bool = True,
        scope: Optional[Literal['function', 'request']] = None
    ) -> Any:  # type: ignore[no-any-return]
        """Dependency injection stub with proper signature matching FastAPI."""
        return dependency if dependency is not None else lambda: None

from ai_karen_engine.core.config_manager import AIKarenConfig, get_config
from ai_karen_engine.core.health_monitor import HealthMonitor, get_health_monitor
from ai_karen_engine.core.service_registry import (
    get_service_registry,
)

logger = logging.getLogger(__name__)


def _get_default_user_context() -> Dict[str, Any]:
    """Return default user context (no authentication required)."""
    return {
        "user_id": "default_user",
        "email": "user@example.com",
        "full_name": "Default User",
        "roles": ["user", "admin"],
        "tenant_id": "default",
        "is_active": True,
    }


# Configuration dependency
async def get_current_config() -> AIKarenConfig:
    """Get current configuration."""
    try:
        return get_config()
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(status_code=500, detail="Configuration unavailable")


# Authentication dependencies (using real authentication)
async def get_current_user_context(request: Request) -> Dict[str, Any]:
    """Get user context using real authentication middleware."""
    try:
        # DEVELOPMENT MODE: Check if we're in development mode
        environment = os.getenv("ENVIRONMENT", "development").lower()
        if environment in ["development", "dev"]:
            logger.debug("🔓 Development mode detected: Using development user context")
            # Return development user context with full permissions
            return {
                "user_id": "dev-user",
                "email": "dev-user@localhost",
                "user_type": "developer",
                "permissions": [
                    "extension:*",
                    "chat:write",
                    "chat:read",
                    "chat:admin",
                    "memory:read",
                    "memory:write",
                    "conversation:create",
                    "message:send",
                    "admin:*"
                ],
                "tenant_id": "dev-tenant",
                "roles": ["admin", "user"],
                "is_active": True,
                "token_id": "dev-token-id"
            }
        
        # PRODUCTION MODE: Use real authentication
        # Import here to avoid circular imports
        from src.auth.auth_middleware import get_auth_middleware, AuthenticationError
        
        # Get auth middleware instance
        auth_middleware = get_auth_middleware()
        
        # Get current user from request (sync call in async context)
        # Use asyncio.to_thread to run sync function in a thread pool
        import asyncio
        user_context = await asyncio.to_thread(auth_middleware.get_current_user, request)
        
        # Ensure we return a dictionary to match type annotation
        if isinstance(user_context, dict):
            return user_context
        else:
            # If get_current_user returns something other than a dict, convert it
            return {"user": user_context}
    except AuthenticationError as e:
        # Re-raise authentication errors to ensure proper HTTP status codes
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        # Log with request context and stacktrace for easier debugging
        try:
            path = getattr(request, "url", None)
            method = getattr(request, "method", "UNKNOWN")
            logger.error(
                f"Authentication error while handling {method} {path}: {e}",
                exc_info=True,
            )
        except Exception:
            logger.error(f"Authentication error (no request context available): {e}", exc_info=True)

        # For unexpected errors, return a generic authentication error
        raise HTTPException(status_code=401, detail="Authentication failed")


async def get_current_user_id(
    user_ctx: Dict[str, Any] = Depends(get_current_user_context)
) -> str:
    """Get current user ID from user context."""
    return user_ctx["user_id"]


async def get_current_tenant_id(
    user_ctx: Dict[str, Any] = Depends(get_current_user_context)
) -> str:
    """Get current tenant ID from user context."""
    return user_ctx["tenant_id"]


# Service dependencies - using Any for return types to avoid conflicts
async def get_ai_orchestrator_service() -> Any:
    """Get AI Orchestrator service instance."""
    registry_error: Optional[Exception] = None

    logger.debug("🔍 Attempting to get AI Orchestrator service from registry...")
    
    try:
        registry = get_service_registry()
        logger.debug(f"✅ Service registry obtained: {type(registry).__name__}")
        logger.debug(f"📋 Available services in registry: {registry.list_services()}")
        
        service = await registry.get_service("ai_orchestrator")
        logger.debug(f"✅ AI Orchestrator service retrieved successfully: {type(service).__name__}")
        return service
    except (ValueError, RuntimeError) as exc:
        # Service registry may not be initialized yet when lazy startup is enabled.
        registry_error = exc
        logger.warning(f"⚠️ Service registry lookup for AI orchestrator failed: {exc}")
        logger.warning(f"⚠️ Error type: {type(exc).__name__}")
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(f"❌ Failed to access AI orchestrator via registry: {exc}", exc_info=True)
        logger.error(f"❌ Error type: {type(exc).__name__}")
        registry_error = exc

    # Fallback to lazy service registry when optimized startup defers instantiation.
    logger.debug("🔄 Attempting lazy loading fallback for AI Orchestrator...")
    try:
        from ai_karen_engine.core.lazy_loading import lazy_registry, setup_lazy_services

        available_lazy_services = lazy_registry.list_services()
        logger.debug(f"📋 Lazy registry services: {available_lazy_services}")
        
        if not available_lazy_services:
            logger.debug("🚀 No lazy services available, setting up lazy services...")
            await setup_lazy_services()
            logger.debug(f"✅ Lazy services setup complete: {lazy_registry.list_services()}")

        service = await lazy_registry.get_service_instance("ai_orchestrator")
        logger.debug(f"✅ AI Orchestrator retrieved from lazy registry: {type(service).__name__}")
        
        if registry_error:
            logger.info(
                "✅ Using lazy-loaded AI orchestrator because registry access failed: %s",
                registry_error,
            )
        return service
    except Exception as lazy_exc:
        logger.error(f"❌ Lazy AI orchestrator initialization failed: {lazy_exc}", exc_info=True)
        logger.error(f"❌ Error type: {type(lazy_exc).__name__}")
        
        # Log additional diagnostic information
        try:
            from ai_karen_engine.core.lazy_loading import lazy_registry
            logger.error(f"❌ Lazy registry services: {lazy_registry.list_services()}")
        except Exception as e:
            logger.error(f"❌ Could not list lazy registry services: {e}")
            
        if registry_error:
            logger.error(f"❌ Registry error prior to lazy fallback: {registry_error}")
        
        logger.error("❌ Raising HTTP 503: AI Orchestrator service unavailable")
        raise HTTPException(
            status_code=503, detail="AI Orchestrator service unavailable"
        )


async def get_memory_service() -> Any:
    """Get Memory service instance."""
    try:
        registry = get_service_registry()
        service = await registry.get_service("memory_service")
        return service
    except Exception as e:
        logger.error(f"Failed to get Memory service: {e}")
        raise HTTPException(status_code=503, detail="Memory service unavailable")


async def get_conversation_service() -> Any:
    """Get Conversation service instance."""
    try:
        registry = get_service_registry()
        service = await registry.get_service("conversation_service")
        return service
    except Exception as e:
        logger.error(f"Failed to get Conversation service: {e}")
        raise HTTPException(status_code=503, detail="Conversation service unavailable")


async def get_plugin_service() -> Any:
    """Get Plugin service instance."""
    try:
        registry = get_service_registry()
        service = await registry.get_service("plugin_service")
        return service
    except Exception as e:
        logger.error(f"Failed to get Plugin service: {e}")
        raise HTTPException(status_code=503, detail="Plugin service unavailable")


async def get_tool_service() -> Any:
    """Get Tool service instance."""
    try:
        registry = get_service_registry()
        service = await registry.get_service("tool_service")
        return service
    except Exception as e:
        logger.error(f"Failed to get Tool service: {e}")
        raise HTTPException(status_code=503, detail="Tool service unavailable")


async def get_analytics_service() -> Any:
    """Get Analytics service instance."""
    try:
        registry = get_service_registry()
        service = await registry.get_service("analytics_service")
        return service
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
async def get_service_registry_instance() -> Any:
    """Get Service Registry instance."""
    try:
        return get_service_registry()
    except Exception as e:
        logger.error(f"Failed to get Service Registry: {e}")
        raise HTTPException(status_code=503, detail="Service Registry unavailable")


# Convenience dependencies for common combinations
async def get_ai_services() -> tuple[Any, Any, Any]:
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


async def get_execution_services() -> tuple[Any, Any]:
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
# These are dependency objects that can be used directly as parameter defaults
AIOrchestrator_Dep = Depends(get_ai_orchestrator_service)  # type: ignore
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
