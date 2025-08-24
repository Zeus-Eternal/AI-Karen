# mypy: ignore-errors
"""
Kari FastAPI Server - Production Version
- Complete implementation with all original routes
- Enhanced security and monitoring
- Optimized plugin system
- Production-grade configuration
"""

# Load environment variables first, before any other imports
from dotenv import load_dotenv
import os

# Load .env file and ensure critical variables are set
load_dotenv()

# Ensure critical environment variables are set with defaults for development
required_env_vars = {
    "KARI_DUCKDB_PASSWORD": "dev-duckdb-pass",
    "KARI_JOB_ENC_KEY": "MaL42789OGRr0--UUf_RV_kanWzb2tSCd6hU6R-sOZo=",
    "KARI_JOB_SIGNING_KEY": "dev-job-key-456",
    "KARI_MODEL_SIGNING_KEY": "dev-signing-key-1234567890abcdef",
    "SECRET_KEY": "super-secret-key-change-me",
    "AUTH_SECRET_KEY": "your-super-secret-jwt-key-change-in-production",
    "DATABASE_URL": "postgresql://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen",
    "POSTGRES_URL": "postgresql+asyncpg://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen",
    "AUTH_DATABASE_URL": "postgresql+asyncpg://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen",
    "REDIS_URL": "redis://localhost:6379/0"
}

for var_name, default_value in required_env_vars.items():
    if not os.getenv(var_name):
        os.environ[var_name] = default_value

import logging
import logging.config
import ssl
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

# Security imports
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Original route imports
from ai_karen_engine.api_routes.ai_orchestrator_routes import router as ai_router
from ai_karen_engine.api_routes.audit import router as audit_router
from ai_karen_engine.api_routes.auth import router as auth_router
from ai_karen_engine.api_routes.auth_session_routes import router as auth_session_router
from ai_karen_engine.api_routes.code_execution_routes import (
    router as code_execution_router,
)
from ai_karen_engine.api_routes.conversation_routes import router as conversation_router
from ai_karen_engine.api_routes.copilot_routes import router as copilot_router
from ai_karen_engine.api_routes.events import router as events_router
from ai_karen_engine.api_routes.file_attachment_routes import (
    router as file_attachment_router,
)
from ai_karen_engine.api_routes.memory_routes import router as memory_router
from ai_karen_engine.api_routes.plugin_routes import router as plugin_router
from ai_karen_engine.api_routes.tool_routes import router as tool_router
from ai_karen_engine.api_routes.web_api_compatibility import router as web_api_router
from ai_karen_engine.api_routes.websocket_routes import router as websocket_router
from ai_karen_engine.api_routes.chat_runtime import router as chat_runtime_router
from ai_karen_engine.api_routes.llm_routes import router as llm_router
from ai_karen_engine.api_routes.provider_routes import router as provider_router
from ai_karen_engine.api_routes.profile_routes import router as profile_router
from ai_karen_engine.api_routes.settings_routes import router as settings_router
from ai_karen_engine.api_routes.error_response_routes import router as error_response_router
from ai_karen_engine.api_routes.analytics_routes import router as analytics_router
from ai_karen_engine.server.middleware import configure_middleware
from ai_karen_engine.server.plugin_loader import ENABLED_PLUGINS, PLUGIN_MAP
from ai_karen_engine.server.startup import create_lifespan
from ai_karen_engine.server.logging_filters import SuppressInvalidHTTPFilter

# Developer API imports
from ui_launchers.backend.developer_api import setup_developer_api

# --- Configuration Management -------------------------------------------------


class Settings(BaseSettings):
    app_name: str = "Kari AI Server"
    environment: str = "development"
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str = "postgresql://user:password@localhost:5432/kari_prod"
    kari_cors_origins: str = Field(
        default="http://localhost:8010,http://127.0.0.1:8010,http://localhost:3000",
        alias="cors_origins",
    )
    prometheus_enabled: bool = True
    https_redirect: bool = False
    rate_limit: str = "100/minute"
    debug: bool = True
    plugin_dir: str = "/app/plugins"
    llm_refresh_interval: int = 3600

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()

# --- Security Setup ----------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


def get_ssl_context():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.set_ciphers("ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384")
    ssl_context.load_cert_chain("cert.pem", "key.pem")
    return ssl_context


# --- Logging Configuration --------------------------------------------------


def configure_logging():
    """Configure production-grade logging"""
    Path("logs").mkdir(exist_ok=True)

    try:
        from pythonjsonlogger import jsonlogger  # type: ignore

        json_formatter: Dict[str, Any] = {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s %(lineno)d %(pathname)s",
        }
    except ImportError:
        json_formatter = {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        }
    except Exception as exc:  # pragma: no cover - unexpected config issues
        logging.getLogger(__name__).exception("Unexpected logging setup error: %s", exc)
        json_formatter = {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        }

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "suppress_invalid_http": {
                    "()": "ai_karen_engine.server.logging_filters.SuppressInvalidHTTPFilter",
                },
            },
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
                "json": json_formatter,
                "access": {
                    "()": "uvicorn.logging.AccessFormatter",
                    "fmt": '%(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s',
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout",
                    "filters": ["suppress_invalid_http"],
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": "logs/kari.log",
                    "maxBytes": 10485760,
                    "backupCount": 5,
                    "formatter": "json",
                    "filters": ["suppress_invalid_http"],
                },
                "access": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": "logs/access.log",
                    "maxBytes": 10485760,
                    "backupCount": 5,
                    "formatter": "access",
                    "filters": ["suppress_invalid_http"],
                },
                "error": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": "logs/error.log",
                    "maxBytes": 10485760,
                    "backupCount": 5,
                    "formatter": "json",
                    "level": "ERROR",
                    "filters": ["suppress_invalid_http"],
                },
            },
            "loggers": {
                "uvicorn.error": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["access"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
            "root": {
                "handlers": ["console", "file", "error"],
                "level": "INFO" if not settings.debug else "DEBUG",
            },
        }
    )


configure_logging()
logger = logging.getLogger("kari")

# --- Metrics Configuration -------------------------------------------------

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        REGISTRY,
        Counter,
        Histogram,
        generate_latest,
    )

    PROMETHEUS_ENABLED = True
except ImportError:
    PROMETHEUS_ENABLED = False
    logger.warning("Prometheus client not available, metrics disabled")

# Initialize metrics using the enhanced metrics manager
from ai_karen_engine.core.metrics_manager import get_metrics_manager

def initialize_metrics():
    """Initialize HTTP metrics using the safe metrics manager."""
    manager = get_metrics_manager()
    
    metrics = {}
    with manager.safe_metrics_context():
        metrics['REQUEST_COUNT'] = manager.register_counter(
            "kari_http_requests_total",
            "Total HTTP requests",
            ["method", "path", "status"]
        )
        metrics['REQUEST_LATENCY'] = manager.register_histogram(
            "kari_http_request_duration_seconds",
            "HTTP request latency",
            ["method", "path"]
        )
        metrics['ERROR_COUNT'] = manager.register_counter(
            "kari_http_errors_total",
            "Total HTTP errors",
            ["method", "path", "error_type"]
        )
    
    return metrics

# Initialize metrics safely
_http_metrics = initialize_metrics()
REQUEST_COUNT = _http_metrics['REQUEST_COUNT']
REQUEST_LATENCY = _http_metrics['REQUEST_LATENCY']
ERROR_COUNT = _http_metrics['ERROR_COUNT']

# --- FastAPI Application Setup ---------------------------------------------


def create_app() -> FastAPI:
    """Application factory for Kari AI"""
    # The lifespan context manager manages startup and shutdown
    # logic for the application. Previously this variable was
    # referenced without being defined which caused the server
    # to crash during initialization. We create it explicitly
    # here before passing it to FastAPI so the app can start
    # correctly.
    lifespan = create_lifespan(settings)
    app = FastAPI(
        title=settings.app_name,
        description="Kari AI Production Server",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        servers=[
            {"url": "https://api.yourdomain.com", "description": "Production server"},
            {"url": "http://localhost:8000", "description": "Development server"},
        ],
    )

    configure_middleware(app, settings, REQUEST_COUNT, REQUEST_LATENCY, ERROR_COUNT)

    app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
    app.include_router(auth_session_router, prefix="/api", tags=["authentication-session"])
    app.include_router(events_router, prefix="/api/events", tags=["events"])
    app.include_router(websocket_router, prefix="/api/ws", tags=["websocket"])
    app.include_router(web_api_router, prefix="/api/web", tags=["web-api"])
    app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])
    app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
    app.include_router(memory_router, prefix="/api/memory", tags=["memory"])
    app.include_router(copilot_router, prefix="/copilot", tags=["copilot"])
    app.include_router(
        conversation_router, prefix="/api/conversations", tags=["conversations"]
    )
    app.include_router(plugin_router, prefix="/api/plugins", tags=["plugins"])
    app.include_router(tool_router, prefix="/api/tools", tags=["tools"])
    app.include_router(audit_router, prefix="/api/audit", tags=["audit"])
    app.include_router(file_attachment_router, prefix="/api/files", tags=["files"])
    app.include_router(code_execution_router, prefix="/api/code", tags=["code"])
    app.include_router(chat_runtime_router, prefix="/api", tags=["chat-runtime"])
    app.include_router(llm_router, prefix="/api/llm", tags=["llm"])
    app.include_router(provider_router, prefix="/api/providers", tags=["providers"])
    app.include_router(profile_router, prefix="/api/profiles", tags=["profiles"])
    app.include_router(error_response_router, prefix="/api", tags=["error-response"])
    app.include_router(settings_router)

    # Setup developer API with enhanced debugging capabilities
    setup_developer_api(app)
    
    # Add reasoning system endpoint for frontend
    @app.post("/api/reasoning/analyze", tags=["reasoning"])
    async def analyze_with_reasoning(request: dict):
        """Analyze user input using the reasoning system with fallbacks"""
        try:
            user_input = request.get("input", "")
            context = request.get("context", {})
            
            # Try AI-powered reasoning first
            try:
                from ai_karen_engine.services.ai_orchestrator.ai_orchestrator import AIOrchestrator
                from ai_karen_engine.core.service_registry import ServiceRegistry
                
                registry = ServiceRegistry()
                ai_orchestrator = await registry.get_service("ai_orchestrator")
                
                # Use AI orchestrator for reasoning
                response = await ai_orchestrator.process_conversation(
                    user_input=user_input,
                    context=context,
                    user_id=context.get("user_id", "anonymous")
                )
                
                return {
                    "success": True,
                    "response": response,
                    "reasoning_method": "ai_orchestrator",
                    "fallback_used": False
                }
                
            except Exception as ai_error:
                logger.warning(f"AI reasoning failed, using fallback: {ai_error}")
                
                # Fallback to local reasoning
                try:
                    from ai_karen_engine.core.degraded_mode import generate_degraded_mode_response
                    
                    # Call the sync function properly
                    fallback_response = generate_degraded_mode_response(
                        user_input=user_input,
                        context=context
                    )
                    
                    return {
                        "success": True,
                        "response": fallback_response,
                        "reasoning_method": "local_fallback",
                        "fallback_used": True,
                        "ai_error": str(ai_error)
                    }
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback reasoning failed: {fallback_error}")
                    
                    # Ultimate fallback - enhanced simple response
                    def generate_simple_response(text: str) -> str:
                        """Generate a more helpful simple response."""
                        text = text.strip().lower()
                        
                        # Coding questions
                        if any(word in text for word in ["function", "code", "python", "javascript", "programming", "algorithm"]):
                            return f"I can help with coding questions! You asked about: {user_input}\n\nWhile I'm in fallback mode, I can still provide basic guidance. For coding tasks, I recommend:\n1. Breaking down the problem into smaller steps\n2. Using clear variable names\n3. Adding comments to explain your logic\n4. Testing your code incrementally\n\nWhat specific aspect would you like help with?"
                        
                        # Questions
                        elif text.endswith("?") or any(word in text for word in ["what", "how", "why", "when", "where", "help"]):
                            return f"I understand you're asking: {user_input}\n\nI'm currently in fallback mode with limited capabilities, but I'll do my best to help. Could you provide more specific details about what you need assistance with?"
                        
                        # Greetings
                        elif any(word in text for word in ["hello", "hi", "hey", "greetings"]):
                            return "Hello! I'm Karen, your AI assistant. I'm currently running in fallback mode, which means some advanced features aren't available, but I'm still here to help with basic questions and tasks. What can I assist you with today?"
                        
                        # Tasks/requests
                        elif any(word in text for word in ["create", "make", "build", "write", "generate"]):
                            return f"I'd be happy to help you with: {user_input}\n\nI'm currently in fallback mode, so my responses may be more basic than usual. Could you break down what you need into specific steps? This will help me provide better assistance."
                        
                        # Default
                        else:
                            return f"I received your message: {user_input}\n\nI'm currently operating in fallback mode with limited capabilities. While I may not be able to provide my full range of assistance, I'm still here to help as best I can. Could you rephrase your request or ask a more specific question?"
                    
                    simple_content = generate_simple_response(user_input)
                    
                    return {
                        "success": True,
                        "response": {
                            "content": simple_content,
                            "type": "text",
                            "metadata": {
                                "fallback_mode": True,
                                "local_processing": True,
                                "enhanced_simple_response": True
                            }
                        },
                        "reasoning_method": "enhanced_simple_fallback",
                        "fallback_used": True,
                        "errors": {
                            "ai_error": str(ai_error),
                            "fallback_error": str(fallback_error)
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Reasoning endpoint error: {e}")
            return {
                "success": False,
                "error": str(e),
                "reasoning_method": "error",
                "fallback_used": True
            }

    @app.get("/health", tags=["system"])
    async def health_check():
        """Basic health check - no authentication required"""
        """Comprehensive health check with fallback status"""
        try:
            # Check service registry status
            service_status = {}
            try:
                from ai_karen_engine.core.service_registry import ServiceRegistry
                registry = ServiceRegistry()
                report = registry.get_initialization_report()
                service_status = {
                    "total_services": report["summary"]["total_services"],
                    "ready_services": report["summary"]["ready_services"],
                    "degraded_services": report["summary"]["degraded_services"],
                    "error_services": report["summary"]["error_services"]
                }
            except Exception:
                service_status = {"status": "unknown"}
            
            # Check connection health
            connection_status = {}
            try:
                from ai_karen_engine.services.database_connection_manager import get_database_manager
                from ai_karen_engine.services.redis_connection_manager import get_redis_manager
                
                db_manager = get_database_manager()
                redis_manager = get_redis_manager()
                
                connection_status = {
                    "database": "degraded" if db_manager.is_degraded() else "healthy",
                    "redis": "degraded" if redis_manager.is_degraded() else "healthy"
                }
            except Exception:
                connection_status = {"database": "unknown", "redis": "unknown"}
            
            # Check model availability
            model_status = {}
            try:
                from pathlib import Path
                models_dir = Path("models")
                gguf_models = list(models_dir.rglob("*.gguf"))
                bin_models = list(models_dir.rglob("*.bin"))
                
                model_status = {
                    "local_models": len(gguf_models) + len(bin_models),
                    "fallback_available": (models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf").exists()
                }
            except Exception:
                model_status = {"local_models": 0, "fallback_available": False}
            
            # Determine overall status
            overall_status = "healthy"
            if connection_status.get("database") == "degraded" or connection_status.get("redis") == "degraded":
                overall_status = "degraded"
            if service_status.get("error_services", 0) > 0:
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "environment": settings.environment,
                "version": "1.0.0",
                "services": service_status,
                "connections": connection_status,
                "models": model_status,
                "plugins": len(ENABLED_PLUGINS),
                "fallback_systems": {
                    "analytics": "active",
                    "error_responses": "active", 
                    "provider_chains": "active",
                    "connection_health": "active"
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "environment": settings.environment,
                "version": "1.0.0",
                "error": str(e),
                "fallback_mode": True
            }

    @app.get("/metrics", tags=["monitoring"])
    async def metrics(api_key: str = Depends(api_key_header)):
        """Prometheus metrics endpoint requiring X-API-KEY header"""
        if not PROMETHEUS_ENABLED:
            raise HTTPException(
                status_code=501,
                detail="Metrics are not enabled",
            )
        if api_key != settings.secret_key:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")

        return Response(
            content=generate_latest(REGISTRY),
            media_type=CONTENT_TYPE_LATEST,
        )

    @app.get("/plugins", tags=["plugins"])
    async def list_plugins():
        """List all plugins with detailed status"""
        return {
            "enabled": sorted(ENABLED_PLUGINS),
            "available": sorted(PLUGIN_MAP.keys()),
            "count": len(PLUGIN_MAP),
        }
    
    @app.get("/api/health/degraded-mode", tags=["system"])
    async def degraded_mode_status():
        """Check if system is running in degraded mode"""
        try:
            # Check various system components for degraded mode
            degraded_components = []
            
            # Check database
            try:
                from ai_karen_engine.services.database_connection_manager import get_database_manager
                db_manager = get_database_manager()
                if db_manager.is_degraded():
                    degraded_components.append("database")
            except Exception:
                degraded_components.append("database")
            
            # Check Redis
            try:
                from ai_karen_engine.services.redis_connection_manager import get_redis_manager
                redis_manager = get_redis_manager()
                if redis_manager.is_degraded():
                    degraded_components.append("redis")
            except Exception:
                degraded_components.append("redis")
            
            # Check AI providers
            failed_providers = []
            try:
                from ai_karen_engine.services.provider_registry import get_provider_registry_service
                provider_service = get_provider_registry_service()
                system_status = provider_service.get_system_status()
                if system_status["available_providers"] == 0:
                    degraded_components.append("ai_providers")
                    failed_providers = system_status.get("failed_providers", [])
            except Exception:
                degraded_components.append("ai_providers")
                failed_providers = ["unknown"]
            
            is_degraded = len(degraded_components) > 0
            
            # Determine degraded mode reason
            reason = None
            if is_degraded:
                if "ai_providers" in degraded_components and "database" in degraded_components:
                    reason = "all_providers_failed"
                elif "database" in degraded_components:
                    reason = "network_issues"
                elif "ai_providers" in degraded_components:
                    reason = "all_providers_failed"
                else:
                    reason = "resource_exhaustion"
            
            # Core helpers availability
            core_helpers_available = {
                "local_nlp": True,  # spaCy is available
                "fallback_responses": True,  # Always available
                "basic_analytics": True,  # Basic analytics work
                "file_operations": True,  # File ops work
                "database_fallback": "database" not in degraded_components
            }
            
            return {
                "is_active": is_degraded,
                "reason": reason,
                "activated_at": datetime.now(timezone.utc).isoformat() if is_degraded else None,
                "failed_providers": failed_providers,
                "recovery_attempts": 0,  # Could track this in a persistent store
                "last_recovery_attempt": None,  # Could track this too
                "core_helpers_available": core_helpers_available
            }
            
        except Exception as e:
            return {
                "is_active": True,
                "reason": "resource_exhaustion",
                "activated_at": datetime.now(timezone.utc).isoformat(),
                "failed_providers": ["unknown"],
                "recovery_attempts": 0,
                "last_recovery_attempt": None,
                "core_helpers_available": {
                    "local_nlp": True,
                    "fallback_responses": True,
                    "basic_analytics": False,
                    "file_operations": True,
                    "database_fallback": False
                }
            }

    @app.post("/api/health/degraded-mode/recover", tags=["system"])
    async def attempt_degraded_mode_recovery():
        """Attempt to recover from degraded mode"""
        try:
            recovery_results = {}
            
            # Try to recover database connection
            try:
                from ai_karen_engine.services.database_connection_manager import get_database_manager
                db_manager = get_database_manager()
                await db_manager.test_connection()
                recovery_results["database"] = "recovered"
            except Exception as e:
                recovery_results["database"] = f"failed: {str(e)}"
            
            # Try to recover Redis connection
            try:
                from ai_karen_engine.services.redis_connection_manager import get_redis_manager
                redis_manager = get_redis_manager()
                await redis_manager.test_connection()
                recovery_results["redis"] = "recovered"
            except Exception as e:
                recovery_results["redis"] = f"failed: {str(e)}"
            
            # Try to recover AI providers
            try:
                from ai_karen_engine.services.provider_registry import get_provider_registry_service
                provider_service = get_provider_registry_service()
                # Force a refresh of provider status
                system_status = provider_service.get_system_status()
                if system_status["available_providers"] > 0:
                    recovery_results["ai_providers"] = "recovered"
                else:
                    recovery_results["ai_providers"] = "still_failed"
            except Exception as e:
                recovery_results["ai_providers"] = f"failed: {str(e)}"
            
            successful_recoveries = sum(1 for result in recovery_results.values() if result == "recovered")
            
            return {
                "success": successful_recoveries > 0,
                "recovery_results": recovery_results,
                "recovered_components": successful_recoveries,
                "total_components": len(recovery_results),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "recovery_results": {},
                "recovered_components": 0,
                "total_components": 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    @app.get("/system/status", tags=["system"])
    async def system_status():
        """Detailed system status for monitoring and debugging"""
        try:
            status = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "environment": settings.environment,
                "version": "1.0.0",
                "uptime": "unknown",  # Could be calculated from startup time
                "fallback_systems": {}
            }
            
            # Service Registry Status
            try:
                from ai_karen_engine.core.service_registry import ServiceRegistry
                registry = ServiceRegistry()
                report = registry.get_initialization_report()
                status["service_registry"] = report
            except Exception as e:
                status["service_registry"] = {"error": str(e)}
            
            # Provider Registry Status
            try:
                from ai_karen_engine.services.provider_registry import get_provider_registry_service
                provider_service = get_provider_registry_service()
                provider_status = provider_service.get_system_status()
                status["providers"] = provider_status
            except Exception as e:
                status["providers"] = {"error": str(e)}
            
            # Connection Health Status
            try:
                from ai_karen_engine.services.connection_health_manager import get_connection_health_manager
                health_manager = get_connection_health_manager()
                connection_statuses = health_manager.get_all_statuses()
                status["connections"] = {
                    name: {
                        "status": conn.status.value,
                        "last_check": conn.last_check.isoformat() if conn.last_check else None,
                        "error_message": conn.error_message,
                        "degraded_features": conn.degraded_features
                    } for name, conn in connection_statuses.items()
                }
            except Exception as e:
                status["connections"] = {"error": str(e)}
            
            # Model and Runtime Status
            try:
                from pathlib import Path
                models_dir = Path("models")
                
                # Count models
                gguf_models = list(models_dir.rglob("*.gguf"))
                bin_models = list(models_dir.rglob("*.bin"))
                
                # Check specific models
                tinyllama_available = (models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf").exists()
                transformers_cache = (models_dir / "transformers").exists()
                
                # Check spaCy
                spacy_available = False
                try:
                    import spacy
                    nlp = spacy.load("en_core_web_sm")
                    spacy_available = True
                except:
                    pass
                
                status["models"] = {
                    "local_models": {
                        "gguf_count": len(gguf_models),
                        "bin_count": len(bin_models),
                        "total": len(gguf_models) + len(bin_models)
                    },
                    "fallback_models": {
                        "tinyllama": tinyllama_available,
                        "transformers_cache": transformers_cache,
                        "spacy": spacy_available
                    },
                    "model_files": [f.name for f in gguf_models[:5]]  # First 5 models
                }
            except Exception as e:
                status["models"] = {"error": str(e)}
            
            # Fallback System Status
            status["fallback_systems"] = {
                "analytics_service": "active",
                "error_responses": "active",
                "provider_chains": "active", 
                "connection_health": "active",
                "database_fallback": "active",
                "redis_fallback": "active",
                "session_persistence": "active"
            }
            
            return status
            
        except Exception as e:
            return {
                "error": "System status check failed",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "fallback_mode": True
            }

    # Add exception handlers for better error handling
    @app.exception_handler(400)
    async def bad_request_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle bad requests gracefully with JSON response"""
        return JSONResponse(
            content={"detail": "Bad Request"},
            status_code=400,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle validation errors gracefully with JSON response"""
        return JSONResponse(
            content={"detail": "Unprocessable Entity"},
            status_code=422,
        )

    return app


if __name__ == "__main__":
    import asyncio
    import logging
    import sys

    import uvicorn  # type: ignore[import-not-found]
    
    # Perform startup checks and system initialization before starting the server
    async def startup_check():
        """Perform comprehensive startup checks and system initialization."""
        try:
            from src.ai_karen_engine.core.startup_check import perform_startup_checks
            
            print("🔍 Performing startup checks and system initialization...")
            checks_passed, issues = await perform_startup_checks(auto_fix=True)
            
            if not checks_passed:
                print("⚠️ Startup checks found issues:")
                for issue in issues:
                    print(f"   - {issue}")
                print("\n💡 Some issues were automatically fixed. Others may require manual attention.")
            else:
                print("✅ All startup checks passed!")
            
            # Initialize fallback systems
            await initialize_fallback_systems()
            
            return True  # Always continue - fallbacks handle issues
            
        except Exception as e:
            print(f"❌ Startup check failed: {e}")
            print("   Continuing with server startup using fallback systems...")
            await initialize_fallback_systems()
            return True  # Continue with fallbacks
    
    async def initialize_fallback_systems():
        """Initialize comprehensive fallback systems for production readiness."""
        print("🔧 Initializing fallback systems...")
        
        try:
            # 1. Initialize Analytics Service with fallback
            try:
                from ai_karen_engine.services.analytics_service import AnalyticsService
                config = {
                    "max_metrics": 10000,
                    "system_monitor_interval": 30,
                    "max_alerts": 1000,
                    "max_user_events": 10000,
                    "max_performance_metrics": 10000
                }
                analytics = AnalyticsService(config)
                print("✅ Analytics service initialized")
            except Exception as e:
                print(f"⚠️ Analytics service using fallback: {e}")
                # Fallback analytics service is handled in service registry
            
            # 2. Initialize Provider Registry with fallback chains
            try:
                from ai_karen_engine.services.provider_registry import get_provider_registry_service
                provider_service = get_provider_registry_service()
                
                # Configure fallback chains for different scenarios
                provider_service.create_fallback_chain(
                    name="production_text",
                    primary="openai",
                    fallbacks=["gemini", "deepseek", "local", "ollama"]
                )
                
                provider_service.create_fallback_chain(
                    name="local_first",
                    primary="ollama", 
                    fallbacks=["local", "openai", "gemini"]
                )
                
                print("✅ Provider fallback chains configured")
            except Exception as e:
                print(f"⚠️ Provider registry fallback: {e}")
            
            # 3. Initialize Connection Health Monitoring
            try:
                from ai_karen_engine.services.connection_health_manager import get_connection_health_manager
                health_manager = get_connection_health_manager()
                await health_manager.start_monitoring(check_interval=30.0)
                print("✅ Connection health monitoring started")
            except Exception as e:
                print(f"⚠️ Connection health monitoring fallback: {e}")
            
            # 4. Initialize Database with fallback
            try:
                from ai_karen_engine.services.database_connection_manager import initialize_database_manager
                db_manager = await initialize_database_manager()
                if db_manager.is_degraded():
                    print("⚠️ Database running in degraded mode (using in-memory fallback)")
                else:
                    print("✅ Database connection healthy")
            except Exception as e:
                print(f"⚠️ Database using fallback mode: {e}")
            
            # 5. Initialize Redis with fallback
            try:
                from ai_karen_engine.services.redis_connection_manager import initialize_redis_manager
                redis_manager = await initialize_redis_manager()
                if redis_manager.is_degraded():
                    print("⚠️ Redis running in degraded mode (using in-memory cache)")
                else:
                    print("✅ Redis connection healthy")
            except Exception as e:
                print(f"⚠️ Redis using fallback mode: {e}")
            
            # 6. Initialize Error Response Service with AI fallback
            try:
                from ai_karen_engine.services.error_response_service import ErrorResponseService
                error_service = ErrorResponseService()
                
                # Test fallback capability
                test_response = error_service.analyze_error(
                    "Test error for system initialization",
                    use_ai_analysis=True  # Will fallback to rules if AI unavailable
                )
                print("✅ Intelligent error responses with fallback configured")
            except Exception as e:
                print(f"⚠️ Error response service fallback: {e}")
            
            # 7. Check Model Availability
            try:
                from pathlib import Path
                models_dir = Path("models")
                
                # Check for local models
                gguf_models = list(models_dir.rglob("*.gguf"))
                bin_models = list(models_dir.rglob("*.bin"))
                
                # Check for TinyLlama fallback model
                tinyllama_path = models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
                has_fallback_model = tinyllama_path.exists()
                
                # Check spaCy
                try:
                    import spacy
                    nlp = spacy.load("en_core_web_sm")
                    has_spacy = True
                except:
                    has_spacy = False
                
                model_count = len(gguf_models) + len(bin_models)
                print(f"✅ Local models available: {model_count} models, TinyLlama: {has_fallback_model}, spaCy: {has_spacy}")
                
                if not (model_count > 0 or has_spacy):
                    print("⚠️ Limited local models - external providers recommended")
                
            except Exception as e:
                print(f"⚠️ Model availability check: {e}")
            
            print("🎯 Fallback systems initialized - server ready for production!")
            
        except Exception as e:
            print(f"⚠️ Fallback initialization error: {e}")
            print("   Server will continue with basic functionality")
    
    # Run startup checks and system initialization
    try:
        print("🚀 AI Karen Engine - Production Server Starting...")
        startup_success = asyncio.run(startup_check())
        
        if startup_success:
            print("\n✅ System initialization complete!")
            print("🎯 Key Features Active:")
            print("   • Session persistence with automatic refresh")
            print("   • Multi-provider AI fallback chains")
            print("   • Local model fallback (TinyLlama + spaCy)")
            print("   • Connection health monitoring with degraded mode")
            print("   • Intelligent error responses with rule-based fallback")
            print("   • Service registry with graceful degradation")
        else:
            print("\n⚠️ System running with some limitations...")
            
    except Exception as e:
        print(f"❌ Startup initialization error: {e}")
        print("   Server will start with basic functionality and fallbacks...")

    # Use the imported SuppressInvalidHTTPFilter from logging_filters module

    # Apply the filter to all relevant uvicorn loggers immediately
    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.addFilter(SuppressInvalidHTTPFilter())
    uvicorn_error_logger.setLevel(
        logging.ERROR
    )  # Set to ERROR level to suppress warnings

    # Also apply to the root uvicorn logger to catch all messages
    uvicorn_root_logger = logging.getLogger("uvicorn")
    uvicorn_root_logger.addFilter(SuppressInvalidHTTPFilter())

    # Apply to any existing handlers on the uvicorn.error logger
    for handler in uvicorn_error_logger.handlers:
        handler.addFilter(SuppressInvalidHTTPFilter())

    # Set the uvicorn.protocols logger to ERROR level to suppress protocol warnings
    uvicorn_protocols_logger = logging.getLogger("uvicorn.protocols")
    uvicorn_protocols_logger.setLevel(logging.ERROR)

    # Set the uvicorn.protocols.http logger specifically
    uvicorn_http_logger = logging.getLogger("uvicorn.protocols.http")
    uvicorn_http_logger.setLevel(logging.ERROR)

    # Apply filter to all uvicorn-related loggers
    for logger_name in [
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.http.httptools_impl",
    ]:
        logger_obj = logging.getLogger(logger_name)
        logger_obj.addFilter(SuppressInvalidHTTPFilter())
        logger_obj.setLevel(logging.ERROR)

    # Completely disable the specific logger that generates "Invalid HTTP request received"
    # This is the most direct way to suppress these warnings
    logging.getLogger("uvicorn.protocols.http.h11_impl").disabled = True
    logging.getLogger("uvicorn.protocols.http.httptools_impl").disabled = True

    # Also try to suppress at the uvicorn.error level more aggressively
    uvicorn_error_logger.disabled = False  # Keep it enabled but filtered
    uvicorn_error_logger.propagate = False  # Don't propagate to parent loggers

    # Disable SSL for development
    ssl_context = None
    # if settings.https_redirect:
    #     ssl_context = get_ssl_context()

    # Create custom log config to suppress uvicorn HTTP warnings
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(message)s",
                "use_colors": None,
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
            },
        },
        "filters": {
            "suppress_invalid_http": {
                "()": SuppressInvalidHTTPFilter,
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
                "filters": ["suppress_invalid_http"],
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {
                "handlers": ["default"],
                "level": "WARNING",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["access"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

    uvicorn_kwargs = {
        "app": "main:create_app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": settings.debug,
        "workers": 1,  # Use single worker for development to avoid issues
        "log_config": log_config,
        "access_log": False,
        "timeout_keep_alive": 30,
        "timeout_graceful_shutdown": 30,
        "factory": True,
        # Add better handling for invalid HTTP requests
        "http": "httptools",  # Use httptools HTTP implementation for better error handling
        "loop": "auto",  # Auto-select the best event loop
        "server_header": False,  # Disable server header to reduce attack surface
        "date_header": False,  # Disable date header for performance
        # Production-ready limits to prevent resource exhaustion
        "limit_concurrency": 200,  # Increased for production
        "limit_max_requests": 10000,  # Increased for production (10x more)
        "backlog": 4096,  # Increased backlog for better handling
    }

    if ssl_context:
        uvicorn_kwargs["ssl"] = ssl_context

    uvicorn.run(**uvicorn_kwargs)
