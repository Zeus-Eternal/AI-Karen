"""
Router configuration for Kari FastAPI Server.
Handles all include_router() wiring without changing route definitions.
"""

import os
import logging
from typing import Optional, Any
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.responses import JSONResponse, Response as FastAPIResponse

from .config import Settings


def _ensure_asgi_response(response: FastAPIResponse) -> FastAPIResponse:
    """Ensure downstream responses remain ASGI-callable objects."""
    if callable(response):
        return response

    logger.error(
        "⚠️ Downstream handler returned non-callable response type %s; wrapping in JSONResponse",
        type(response),
    )
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


def _http_exception_response(exc: HTTPException) -> FastAPIResponse:
    """Convert HTTPException into a proper ASGI response while preserving headers."""
    content = {"detail": exc.detail} if exc.detail else {}
    response = JSONResponse(status_code=exc.status_code, content=content)
    if exc.headers:
        for header, value in exc.headers.items():
            response.headers[header] = value
    return response

logger = logging.getLogger("kari")

# Original route imports
from ai_karen_engine.api_routes.ai_orchestrator_routes import router as ai_router
from ai_karen_engine.api_routes.audit import router as audit_router
# DEPRECATED: Complex auth system - replaced with simple auth
# from ai_karen_engine.api_routes.auth import router as auth_router
# from ai_karen_engine.api_routes.auth_session_routes import router as auth_session_router

# NEW: Simple auth system
try:
    from ai_karen_engine.api_routes.auth_routes import router as auth_router
    from src.auth.auth_middleware import AuthenticationError
    from src.auth.auth_middleware import get_auth_middleware
    logger.info("✅ Auth router imported successfully")
except ImportError as e:
    # Fallback - disable auth routes if auth not available
    auth_router = None
    logger.warning(f"🚫 Auth system not available - auth routes disabled: {e}")
from ai_karen_engine.api_routes.code_execution_routes import router as code_execution_router
from ai_karen_engine.api_routes.conversation_routes import router as conversation_router
from ai_karen_engine.api_routes.copilot_routes import router as copilot_router
from ai_karen_engine.api_routes.events import router as events_router
from ai_karen_engine.api_routes.extensions import router as extensions_router
from ai_karen_engine.api_routes.file_attachment_routes import router as file_attachment_router
from ai_karen_engine.api_routes.memory_routes import router as memory_router
from ai_karen_engine.api_routes.plugin_routes import router as plugin_router
from ai_karen_engine.api_routes.plugin_routes import public_router as plugin_public_router
from ai_karen_engine.api_routes.tool_routes import router as tool_router
from ai_karen_engine.api_routes.web_api_compatibility import router as web_api_router
from ai_karen_engine.api_routes.websocket_routes import router as websocket_router
from ai_karen_engine.api_routes.chat_runtime import router as chat_runtime_router
from ai_karen_engine.api_routes.llm_routes import router as llm_router
from ai_karen_engine.api_routes.provider_routes import router as provider_router
from ai_karen_engine.api_routes.provider_routes import public_router as provider_public_router
from ai_karen_engine.api_routes.profile_routes import router as profile_router
from ai_karen_engine.api_routes.settings_routes import router as settings_router
from ai_karen_engine.api_routes.error_response_routes import router as error_response_router
from ai_karen_engine.api_routes.analytics_routes import router as analytics_router
from ai_karen_engine.api_routes.health import router as health_router
from ai_karen_engine.api_routes.model_management_routes import router as model_management_router
from ai_karen_engine.api_routes.huggingface_routes import router as enhanced_huggingface_router
from ai_karen_engine.api_routes.response_core_routes import router as response_core_router
from ai_karen_engine.api_routes.scheduler_routes import router as scheduler_router
from ai_karen_engine.api_routes.public_routes import router as public_router
from ai_karen_engine.api_routes.model_library_routes import router as model_library_router
from ai_karen_engine.api_routes.model_library_routes import public_router as model_library_public_router
from ai_karen_engine.api_routes.provider_compatibility_routes import router as provider_compatibility_router
from ai_karen_engine.api_routes.model_orchestrator_routes import router as model_orchestrator_router
from ai_karen_engine.api_routes.validation_metrics_routes import router as validation_metrics_router
from ai_karen_engine.api_routes.performance_routes import router as performance_routes
from ai_karen_engine.api_routes.model_organization_routes import router as model_organization_router
from ai_karen_engine.api_routes.user_preferences_routes import router as user_preferences_router
from ai_karen_engine.api_routes.user_data_routes import router as user_data_router

# Multi-modal and AI enhancement routes
multimodal_router: Optional[Any] = None
ai_enhancement_router: Optional[Any] = None
MULTIMODAL_AVAILABLE = False

try:
    from ai_karen_engine.api_routes.multimodal_routes import router as multimodal_router
    from ai_karen_engine.api_routes.ai_routes import router as ai_enhancement_router
    MULTIMODAL_AVAILABLE = True
    logger.info("✅ Multi-modal and AI enhancement routers imported successfully")
except ImportError as e:
    MULTIMODAL_AVAILABLE = False
    logger.warning(f"🚫 Multi-modal routes not available: {e}")

# Extension monitoring system
try:
    from .extension_monitoring_api import monitoring_router
    EXTENSION_MONITORING_AVAILABLE = True
    logger.info("✅ Extension monitoring router imported successfully")
except ImportError as e:
    monitoring_router = None
    EXTENSION_MONITORING_AVAILABLE = False
    logger.warning(f"🚫 Extension monitoring not available: {e}")


def wire_routers(app: FastAPI, settings: Settings) -> None:
    """Wire all routers to the FastAPI app with simplified auth system"""
    
    logger.info("🔧 Starting router wiring...")
    
    # NEW: Simple authentication system
    logger.info(f"🔍 Auth router status: {auth_router is not None}")
    if auth_router:
        app.include_router(auth_router, prefix="/api", tags=["authentication"])
        logger.info("🔐 Auth router loaded successfully")
    else:
        logger.warning("🚫 Auth router not available")
    
    # Environment check for auth mode
    effective_env = (os.getenv("ENVIRONMENT") or os.getenv("KARI_ENV") or settings.environment).lower()
    auth_mode = os.getenv("AUTH_MODE", "production").lower()
    
    logger.info(f"🔐 Using auth system - AUTH_MODE={auth_mode}")
    
    # Add auth middleware globally (if available)
    try:
        from src.auth.auth_middleware import get_auth_middleware
        auth_middleware = get_auth_middleware()

        # Use FastAPI middleware for global auth
        @app.middleware("http")
        async def auth_middleware_handler(request, call_next):
            # Check for development bypass headers first
            skip_auth_header = request.headers.get("X-Skip-Auth")
            dev_mode_header = request.headers.get("X-Development-Mode")
            
            if skip_auth_header == "dev" and dev_mode_header == "true":
                # Development mode - set mock user context directly
                mock_user_id = request.headers.get("X-Mock-User-ID", "dev-user")
                request.state.user = {
                    'user_id': mock_user_id,
                    'email': f"{mock_user_id}@localhost",
                    'user_type': 'developer',
                    'permissions': ['extension:*', 'chat:write', 'memory:read', 'memory:write'],
                    'token_id': 'dev-token-id'
                }
                logger.info(f"🔓 Development mode bypass for user: {mock_user_id}")
            else:
                # Skip auth for public endpoints
                if auth_middleware.is_public_endpoint(request.url.path):
                    response = await call_next(request)
                    return _ensure_asgi_response(response)

                # For protected endpoints, authenticate and add user to request state
                try:
                    user_data = auth_middleware.get_current_user(request)
                    request.state.user = user_data
                except HTTPException as exc:
                    logger.warning(
                        "🚫 Authentication failed for %s %s: %s",
                        request.method,
                        request.url.path,
                        exc.detail,
                    )
                    return _http_exception_response(exc)
                except AuthenticationError as exc:
                    # Handle specific authentication errors
                    logger.warning(
                        "🚫 Authentication error for %s %s: %s",
                        request.method,
                        request.url.path,
                        exc.message,
                    )
                    return _http_exception_response(HTTPException(
                        status_code=exc.status_code,
                        detail=exc.message
                    ))
                except Exception as exc:
                    # Log unexpected authentication errors with full context
                    logger.exception(
                        "⚠️ Unexpected error during authentication for %s %s: %s",
                        request.method,
                        request.url.path,
                        str(exc),
                    )
                    # Return a generic authentication error without exposing internal details
                    return _http_exception_response(HTTPException(
                        status_code=500,
                        detail="Authentication service temporarily unavailable"
                    ))

            response = await call_next(request)
            return _ensure_asgi_response(response)

        logger.info("🔐 Auth middleware loaded successfully")
    except ImportError:
        logger.warning("🚫 Auth middleware not available")
    
    # Core API routers
    app.include_router(events_router, prefix="/api/events", tags=["events"])
    app.include_router(websocket_router, prefix="/api/ws", tags=["websocket"])
    app.include_router(web_api_router, prefix="/api/web", tags=["web-api"])
    app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])
    app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
    app.include_router(memory_router, prefix="/api/memory", tags=["memory"])
    
    # Align copilot routes under /api to match frontend expectations
    app.include_router(copilot_router, prefix="/api/copilot", tags=["copilot"])
    app.include_router(conversation_router, prefix="/api/conversations", tags=["conversations"])
    app.include_router(plugin_router, prefix="/api/plugins", tags=["plugins"])
    app.include_router(plugin_public_router, tags=["plugins-public"])
    app.include_router(tool_router, prefix="/api/tools", tags=["tools"])
    # Audit router enabled
    app.include_router(audit_router, prefix="/api/audit", tags=["audit"])
    # Extensions router
    app.include_router(extensions_router, prefix="/api/extensions", tags=["extensions"])
    app.include_router(file_attachment_router, prefix="/api/files", tags=["files"])
    app.include_router(code_execution_router, prefix="/api/code", tags=["code"])
    app.include_router(chat_runtime_router, prefix="/api", tags=["chat-runtime"])
    app.include_router(llm_router, prefix="/api/llm", tags=["llm"])
    
    # Mock provider routes removed for production
    logger.info("🚫 Mock provider routes disabled for production")
    
    # Provider and model routers
    app.include_router(provider_router, prefix="/api/providers", tags=["providers"])
    app.include_router(provider_public_router, prefix="/api/public/providers", tags=["public-providers"])
    app.include_router(profile_router, prefix="/api/profiles", tags=["profiles"])
    app.include_router(error_response_router, prefix="/api", tags=["error-response"])
    # Health router already defines a "/health" prefix, so mount it at the API root
    # to expose endpoints like "/api/health" and "/api/health/degraded-mode".
    app.include_router(health_router, prefix="/api", tags=["health"])
    app.include_router(model_management_router, tags=["model-management"])
    app.include_router(enhanced_huggingface_router, prefix="/api", tags=["enhanced-huggingface"])
    app.include_router(response_core_router, tags=["response-core"])
    app.include_router(scheduler_router, tags=["scheduler"])
    app.include_router(public_router, tags=["public"])
    app.include_router(model_library_router, tags=["model-library"])
    app.include_router(model_library_public_router, tags=["model-library-public"])
    app.include_router(provider_compatibility_router, tags=["provider-compatibility"])
    app.include_router(model_orchestrator_router, tags=["model-orchestrator"])
    app.include_router(validation_metrics_router, tags=["validation-metrics"])
    app.include_router(performance_routes, tags=["performance"])
    app.include_router(model_organization_router, tags=["model-organization"])
    app.include_router(user_preferences_router, tags=["user-preferences"])
    app.include_router(user_data_router, prefix="/api", tags=["user-data"])
    app.include_router(settings_router)
    
    # Multi-modal and AI enhancement routes
    if MULTIMODAL_AVAILABLE:
        if multimodal_router:
            app.include_router(multimodal_router, tags=["multimodal"])
            logger.info("🎨 Multi-modal router loaded successfully")
        if ai_enhancement_router:
            app.include_router(ai_enhancement_router, tags=["ai-enhancement"])
            logger.info("🧠 AI enhancement router loaded successfully")
    else:
        logger.warning("🚫 Multi-modal and AI enhancement routes not available")
    
    # Extension monitoring system
    if EXTENSION_MONITORING_AVAILABLE and monitoring_router:
        app.include_router(monitoring_router, tags=["extension-monitoring"])
        logger.info("📊 Extension monitoring router loaded successfully")
    else:
        logger.warning("🚫 Extension monitoring router not available")
