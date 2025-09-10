# mypy: ignore-errors
"""
Router configuration for Kari FastAPI Server.
Handles all include_router() wiring without changing route definitions.
"""

import os
import logging
from fastapi import FastAPI
from .config import Settings

logger = logging.getLogger("kari")

# Original route imports
from ai_karen_engine.api_routes.ai_orchestrator_routes import router as ai_router
from ai_karen_engine.api_routes.audit import router as audit_router
from ai_karen_engine.api_routes.auth import router as auth_router
from ai_karen_engine.api_routes.auth_session_routes import router as auth_session_router
from ai_karen_engine.api_routes.code_execution_routes import router as code_execution_router
from ai_karen_engine.api_routes.conversation_routes import router as conversation_router
from ai_karen_engine.api_routes.copilot_routes import router as copilot_router
from ai_karen_engine.api_routes.events import router as events_router
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
from ai_karen_engine.api_routes.enhanced_huggingface_routes import router as enhanced_huggingface_router
from ai_karen_engine.api_routes.response_core_routes import router as response_core_router
from ai_karen_engine.api_routes.scheduler_routes import router as scheduler_router
from ai_karen_engine.api_routes.public_routes import router as public_router
from ai_karen_engine.api_routes.model_library_routes import router as model_library_router
from ai_karen_engine.api_routes.model_library_routes import public_router as model_library_public_router
from ai_karen_engine.api_routes.provider_compatibility_routes import router as provider_compatibility_router
from ai_karen_engine.api_routes.model_orchestrator_routes import router as model_orchestrator_router
from ai_karen_engine.api_routes.validation_metrics_routes import router as validation_metrics_router
from ai_karen_engine.api_routes.performance_routes import router as performance_routes


def wire_routers(app: FastAPI, settings: Settings) -> None:
    """Wire all routers to the FastAPI app in the exact same order as original"""
    
    # Core authentication routers
    app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
    app.include_router(auth_session_router, prefix="/api", tags=["authentication-session"])
    
    # Modern Authentication system selection with 2024 best practices
    effective_env = (os.getenv("ENVIRONMENT") or os.getenv("KARI_ENV") or settings.environment).lower()
    auth_mode = os.getenv("AUTH_MODE", "modern").lower()

    if auth_mode == "modern":
        # Use the new modern authentication system (recommended)
        from ai_karen_engine.auth.modern_auth_routes import router as modern_auth_router
        from ai_karen_engine.auth.modern_auth_middleware import ModernAuthMiddleware, ModernSecurityConfig
        
        # Add modern auth middleware
        modern_config = ModernSecurityConfig()
        app.add_middleware(ModernAuthMiddleware, config=modern_config)
        
        app.include_router(modern_auth_router, prefix="/api", tags=["modern-auth"])
        logger.info("🚀 Using modern authentication system (2024 best practices)")
        
    elif auth_mode == "hybrid":
        # Fallback to hybrid auth for compatibility
        from ai_karen_engine.auth.hybrid_auth import router as hybrid_auth_router
        app.include_router(hybrid_auth_router, prefix="/api", tags=["hybrid-auth"])
        logger.info("🔐 Using hybrid authentication system (legacy compatibility)")
        
    elif effective_env == "production":
        # Production fallback
        from ai_karen_engine.auth.production_auth import router as production_auth_router
        app.include_router(production_auth_router, prefix="/api", tags=["production-auth"])
        logger.info("🔐 Environment=production: using production authentication system")
        
    else:
        # Development fallback
        from ai_karen_engine.auth.hybrid_auth import router as hybrid_auth_router
        app.include_router(hybrid_auth_router, prefix="/api", tags=["hybrid-auth"])
        logger.info("🔧 Using hybrid authentication system (development fallback)")
    
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
    app.include_router(audit_router, prefix="/api/audit", tags=["audit"])
    app.include_router(file_attachment_router, prefix="/api/files", tags=["files"])
    app.include_router(code_execution_router, prefix="/api/code", tags=["code"])
    app.include_router(chat_runtime_router, prefix="/api", tags=["chat-runtime"])
    app.include_router(llm_router, prefix="/api/llm", tags=["llm"])
    
    # Include mock provider routes only when explicitly enabled (never in production)
    _enable_mocks = os.getenv("ENABLE_MOCK_PROVIDERS", "false").lower() in ("1", "true", "yes")
    if effective_env != "production" and _enable_mocks:
        from ai_karen_engine.api_routes.mock_provider_routes import router as mock_provider_router
        app.include_router(mock_provider_router, tags=["mock-providers"])
        logger.info("🧪 Mock provider routes enabled (development/testing)")
    
    # Provider and model routers
    app.include_router(provider_router, prefix="/api/providers", tags=["providers"])
    app.include_router(provider_public_router, prefix="/api/public/providers", tags=["public-providers"])
    app.include_router(profile_router, prefix="/api/profiles", tags=["profiles"])
    app.include_router(error_response_router, prefix="/api", tags=["error-response"])
    app.include_router(health_router, prefix="/api/health", tags=["health"])
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
    app.include_router(performance_routes, prefix="/api/performance", tags=["performance"])
    app.include_router(settings_router)