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
        # DEVELOPMENT/BYPASS MODE: Check if we're in development or explicit bypass mode
        environment = os.getenv("ENVIRONMENT", os.getenv("KARI_ENV", "development")).lower()
        auth_bypass = os.getenv("KARI_AUTH_BYPASS", "true").lower() == "true"
        
        if environment in ["development", "dev"] or auth_bypass:
            logger.info("🔓 Auth Bypass Enabled: Using development user context")
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
        from ai_karen_engine.auth.auth_middleware import (
            AuthenticationError,
            get_auth_middleware,
        )
        
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
            
            # CRITICAL FIX: To prevent the UI from receiving 500s or 401s when the 
            # database drops and the user hits the copilot endpoint, we check if 
            # this is a copilot route. If so, return a default context to allow 
            # FallbackProvider to safely execute in degraded mode.
            if path and "/copilot/assist" in str(path):
                logger.warning(
                    f"Authentication failed due to `{e}` while accessing copilot. "
                    "Returning default context to allow degraded fallback execution."
                )
                return _get_default_user_context()
                
            logger.error(f"Authentication error while handling {method} {path}: {e}", exc_info=True)
        except Exception:
            logger.error(f"Authentication error (no request context available): {e}", exc_info=True)

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
    tenant_id = user_ctx.get("tenant_id")
    if not tenant_id:
        # Fallback for development/legacy users
        logger.warning(f"⚠️ Missing tenant_id in context for user {user_ctx.get('user_id')}, using 'dev-tenant'")
        return "dev-tenant"
    return str(tenant_id)


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
    registry_error: Optional[Exception] = None
    try:
        logger.info("🔍 DEBUG: Attempting to get conversation service from registry...")
        registry = get_service_registry()
        logger.info(f"🔍 DEBUG: Service registry obtained: {type(registry).__name__}")
        logger.info(f"🔍 DEBUG: Available services: {registry.list_services()}")
        
        service = await registry.get_service("conversation_service")
        logger.info(f"🔍 DEBUG: Conversation service retrieved successfully: {type(service).__name__}")
        return service
    except Exception as exc:
        registry_error = exc
        logger.error(f"❌ Service registry lookup for conversation service failed: {exc}", exc_info=True)
        logger.error(f"❌ Error type: {type(exc).__name__}")
        logger.error(f"❌ Error details: {str(exc)}")

    try:
        logger.info("🔍 DEBUG: Attempting lazy loading fallback for conversation service...")
        from ai_karen_engine.core.lazy_loading import lazy_registry, setup_lazy_services
        await setup_lazy_services()
        lazy_services = lazy_registry.list_services()
        logger.info(f"🔍 DEBUG: Lazy registry services: {lazy_services}")
        if "conversation_service" not in lazy_services:
            logger.error(f"❌ conversation_service not found in lazy registry. Available: {lazy_services}")
        service = await lazy_registry.get_service_instance("conversation_service")
        logger.info(f"🔍 DEBUG: Conversation service retrieved from lazy registry: {type(service).__name__}")
        return service
    except Exception as lazy_exc:
        logger.error(f"⚠️ Lazy Conversation service initialization failed: {lazy_exc}", exc_info=True)
        logger.error(f"⚠️ Error type: {type(lazy_exc).__name__}")
        logger.error(f"⚠️ Error details: {str(lazy_exc)}")
        
        # FINAL STANDING FALLBACK: Direct instantiation or Factory
        try:
            logger.info("🔄 Final fallback: Attempting to create WebUIConversationService via ChatServiceFactory...")
            from ai_karen_engine.chat.factory import get_chat_service_factory
            from services.memory.conversation_service import WebUIConversationService
            from services.memory.memory_service import WebUIMemoryService
            from typing import cast
            
            factory = get_chat_service_factory()
            logger.info(f"🔍 DEBUG: ChatServiceFactory obtained: {type(factory).__name__}")
            base_manager = factory.create_conversation_manager()
            logger.info(f"🔍 DEBUG: Base conversation manager created: {type(base_manager).__name__}")
            memory_service = factory.create_memory_service() or WebUIMemoryService()
            logger.info(f"🔍 DEBUG: Memory service created: {type(memory_service).__name__}")
            
            if base_manager:
                # The ConversationManager needs to be adapted to work with WebUIConversationService
                # Let's create a simple adapter or use the base_manager directly
                from ai_karen_engine.database.conversation_manager import (
                    ConversationManager,
                    normalize_user_id,
                )
                
                # Create a simple adapter class
                class ConversationManagerAdapter:
                    def __init__(self, enhanced_manager):
                        self.enhanced_manager = enhanced_manager
                    
                    # Delegate the required methods
                    async def create_conversation(self, tenant_id, user_id, title=None, initial_message=None, metadata=None):
                        return await self.enhanced_manager.create_conversation(
                            tenant_id=tenant_id,
                            user_id=normalize_user_id(user_id),
                            title=title,
                            initial_message=initial_message,
                            metadata=metadata or {}
                        )
                    
                    async def get_conversation(self, tenant_id, conversation_id, include_context=False):
                        return await self.enhanced_manager.get_conversation(tenant_id, conversation_id)
                    
                    async def add_message(self, tenant_id, conversation_id, role, content, metadata=None):
                        return await self.enhanced_manager.add_message(
                            tenant_id=tenant_id,
                            conversation_id=conversation_id,
                            role=role,
                            content=content,
                            metadata=metadata or {}
                        )

                    async def list_conversations(self, tenant_id, user_id, active_only=True, limit=50, offset=0):
                        """Delegated list_conversations to the underlying manager."""
                        try:
                            from ai_karen_engine.chat.conversation_models import ConversationFilters, ConversationStatus
                            
                            # Map active_only to ConversationFilters
                            filters = None
                            if active_only:
                                filters = ConversationFilters(status=ConversationStatus.ACTIVE)
                            
                            # Use keyword arguments as supported by the enhanced ConversationManager
                            return await self.enhanced_manager.list_conversations(
                                tenant_id=tenant_id,
                                user_id=normalize_user_id(user_id),
                                filters=filters,
                                limit=limit,
                                offset=offset
                            )
                        except Exception as e:
                            logger.error(f"❌ Adapter list_conversations failed: {e}")
                            return []

                    @property
                    def db_client(self):
                        return self.enhanced_manager.db_client
                
                adapter = ConversationManagerAdapter(base_manager)
                service = WebUIConversationService(
                    base_conversation_manager=cast(ConversationManager, adapter),
                    memory_service=memory_service
                )
                logger.info("✅ Success: WebUIConversationService created via manual factory wiring with adapter.")
                return service
            else:
                logger.error("❌ ChatServiceFactory failed to create base conversation manager.")
        except Exception as factory_exc:
             logger.error(f"❌ WebUIConversationService manual wiring failed: {factory_exc}", exc_info=True)

        if registry_error:
            logger.error(f"❌ Original registry error: {registry_error}", exc_info=True)
        logger.error("❌ Raising HTTP 503: Conversation service unavailable")
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


async def get_chat_orchestrator_service() -> Any:
    """Get Chat Orchestrator service instance as the absolute source of truth."""
    registry_error: Optional[Exception] = None

    logger.info("🔍 DEBUG: Attempting to get Chat Orchestrator service from registry...")
    
    try:
        registry = get_service_registry()
        logger.info(f"🔍 DEBUG: Service registry obtained: {type(registry).__name__}")
        logger.info(f"🔍 DEBUG: Available services in registry: {registry.list_services()}")
        
        service = await registry.get_service("chat_orchestrator")
        logger.info(f"🔍 DEBUG: Chat Orchestrator service retrieved successfully: {type(service).__name__}")
        return service
    except (ValueError, RuntimeError) as exc:
        # Service registry may not be initialized yet when lazy startup is enabled.
        registry_error = exc
        logger.error(f"❌ Service registry lookup for Chat Orchestrator failed: {exc}", exc_info=True)
        logger.error(f"❌ Error type: {type(exc).__name__}")
        logger.error(f"❌ Error details: {str(exc)}")
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(f"❌ Failed to access Chat Orchestrator via registry: {exc}", exc_info=True)
        logger.error(f"❌ Error type: {type(exc).__name__}")
        logger.error(f"❌ Error details: {str(exc)}")
        registry_error = exc

    # Fallback to lazy service registry when optimized startup defers instantiation.
    logger.debug("🔄 Attempting lazy loading fallback for Chat Orchestrator...")
    try:
        from ai_karen_engine.core.lazy_loading import lazy_registry, setup_lazy_services

        available_lazy_services = lazy_registry.list_services()
        logger.debug(f"📋 Lazy registry services: {available_lazy_services}")
        
        if not available_lazy_services:
            logger.debug("🚀 No lazy services available, setting up lazy services...")
            await setup_lazy_services()
            logger.debug(f"✅ Lazy services setup complete: {lazy_registry.list_services()}")

        service = await lazy_registry.get_service_instance("chat_orchestrator")
        logger.debug(f"✅ Chat Orchestrator retrieved from lazy registry: {type(service).__name__}")
        
        if registry_error:
            logger.info(
                "✅ Using lazy-loaded Chat Orchestrator because registry access failed: %s",
                registry_error,
            )
        return service
    except Exception as lazy_exc:
        logger.error(f"❌ Lazy Chat Orchestrator initialization failed: {lazy_exc}", exc_info=True)
        logger.error(f"❌ Error type: {type(lazy_exc).__name__}")
        
        # Log additional diagnostic information
        try:
            from ai_karen_engine.core.lazy_loading import lazy_registry
            logger.error(f"❌ Lazy registry services: {lazy_registry.list_services()}")
        except Exception as e:
            logger.error(f"❌ Could not list lazy registry services: {e}")
            
        # FINAL STANDING FALLBACK: Use the production ChatServiceFactory to force-create the instance
        # This bypasses all registry-level suppression and ensures the service is available.
        try:
            logger.info("🔄 Final fallback: Attempting to create Chat Orchestrator via ChatServiceFactory...")
            from ai_karen_engine.chat.factory import get_chat_orchestrator
            service = get_chat_orchestrator()
            if service:
                logger.info("✅ Success: Chat Orchestrator created via factory fallback.")
                return service
        except Exception as factory_exc:
            logger.error(f"❌ ChatServiceFactory fallback also failed: {factory_exc}")

        logger.error("❌ Raising HTTP 503: Chat Orchestrator service unavailable")
        raise HTTPException(
            status_code=503, detail="Chat Orchestrator service unavailable"
        )


# Chat Orchestrator dependency for FastAPI routes
ChatOrchestrator_Dep = get_chat_orchestrator_service
