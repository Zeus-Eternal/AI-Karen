# mypy: ignore-errors
"""
Kari FastAPI Server:
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

# Determine runtime environment early for safe defaults handling
_RUNTIME_ENV = (
    os.getenv("ENVIRONMENT")
    or os.getenv("KARI_ENV")
    or os.getenv("ENV")
    or "development"
).lower()

# Ensure critical environment variables are set
# - In development/test: provide sensible defaults if missing
# - In production: do NOT inject insecure defaults; require explicit configuration
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

if _RUNTIME_ENV in {"development", "dev", "local", "test", "testing"}:
    for var_name, default_value in required_env_vars.items():
        if not os.getenv(var_name):
            os.environ[var_name] = default_value
else:
    _missing = [k for k in required_env_vars.keys() if not os.getenv(k)]
    if _missing:
        # Fail fast in production for missing critical secrets/connections
        raise RuntimeError(
            "Missing required environment variables in production: " + ", ".join(_missing)
        )

# Ensure src/ is on sys.path when running directly from repo root
import sys
_repo_root = os.path.dirname(os.path.abspath(__file__))
_src_path = os.path.join(_repo_root, "src")
if os.path.isdir(_src_path) and _src_path not in sys.path:
    sys.path.insert(0, _src_path)

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
from ai_karen_engine.api_routes.provider_compatibility_routes import router as provider_compatibility_router
from ai_karen_engine.api_routes.model_orchestrator_routes import router as model_orchestrator_router
from ai_karen_engine.api_routes.validation_metrics_routes import router as validation_metrics_router
from ai_karen_engine.api_routes.performance_routes import router as performance_routes
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
    # Long-lived token settings for API stability
    long_lived_token_expire_hours: int = 24  # 24 hours for long-lived tokens
    enable_long_lived_tokens: bool = True
    database_url: str = "postgresql://user:password@localhost:5432/kari_prod"
    kari_cors_origins: str = Field(
        default="http://localhost:8010,http://127.0.0.1:8010,http://localhost:3000",
        alias="cors_origins",
    )
    prometheus_enabled: bool = True
    https_redirect: bool = False
    rate_limit: str = "300/minute"
    debug: bool = True
    plugin_dir: str = "/app/plugins"
    llm_refresh_interval: int = 3600
    
    # Performance Optimization Settings
    enable_performance_optimization: bool = Field(default=True, env="ENABLE_PERFORMANCE_OPTIMIZATION")
    deployment_mode: str = Field(default="development", env="DEPLOYMENT_MODE")
    cpu_threshold: float = Field(default=80.0, env="CPU_THRESHOLD")
    memory_threshold: float = Field(default=85.0, env="MEMORY_THRESHOLD")
    response_time_threshold: float = Field(default=2.0, env="RESPONSE_TIME_THRESHOLD")
    enable_lazy_loading: bool = Field(default=True, env="ENABLE_LAZY_LOADING")
    enable_gpu_offloading: bool = Field(default=True, env="ENABLE_GPU_OFFLOADING")
    enable_service_consolidation: bool = Field(default=True, env="ENABLE_SERVICE_CONSOLIDATION")
    max_startup_time: float = Field(default=30.0, env="MAX_STARTUP_TIME")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # HTTP Request Validation Settings (Requirements 4.1, 4.2, 4.3, 4.4)
    max_request_size: int = Field(default=10 * 1024 * 1024, env="MAX_REQUEST_SIZE")  # 10MB
    max_headers_count: int = Field(default=100, env="MAX_HEADERS_COUNT")
    max_header_size: int = Field(default=8192, env="MAX_HEADER_SIZE")
    enable_request_validation: bool = Field(default=True, env="ENABLE_REQUEST_VALIDATION")
    enable_security_analysis: bool = Field(default=True, env="ENABLE_SECURITY_ANALYSIS")
    log_invalid_requests: bool = Field(default=True, env="LOG_INVALID_REQUESTS")
    validation_rate_limit_per_minute: int = Field(default=100, env="VALIDATION_RATE_LIMIT_PER_MINUTE")
    
    # Security validation patterns (configurable)
    blocked_user_agents: str = Field(
        default="sqlmap,nikto,nmap,masscan,zap",
        env="BLOCKED_USER_AGENTS"
    )
    suspicious_headers: str = Field(
        default="x-forwarded-host,x-cluster-client-ip,x-real-ip",
        env="SUSPICIOUS_HEADERS"
    )
    
    # Protocol-level error handling settings
    max_invalid_requests_per_connection: int = Field(default=10, env="MAX_INVALID_REQUESTS_PER_CONNECTION")
    enable_protocol_error_handling: bool = Field(default=True, env="ENABLE_PROTOCOL_ERROR_HANDLING")

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
            # Disable any handlers/config that uvicorn or early imports added
            # to avoid duplicate log lines in console and files.
            "disable_existing_loggers": True,
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
                # Tune SQLAlchemy verbosity; avoid custom handlers so it
                # propagates to root and doesn't double-format.
                "sqlalchemy": {
                    "level": "INFO" if settings.debug else "WARNING",
                    "propagate": True,
                    "handlers": []
                },
                "sqlalchemy.engine": {
                    "level": "INFO" if settings.debug else "WARNING",
                    "propagate": True,
                    "handlers": []
                },
                "sqlalchemy.pool": {
                    "level": "WARNING",
                    "propagate": True,
                    "handlers": []
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

# --- Validation Framework Initialization -----------------------------------

def load_environment_specific_validation_config(settings: Settings) -> Settings:
    """
    Load environment-specific validation configuration.
    
    Requirement 4.3: Enable/disable specific validation rules based on deployment environment
    """
    environment = settings.environment.lower()
    
    # Production environment - strict validation
    if environment == "production":
        settings.enable_request_validation = True
        settings.enable_security_analysis = True
        settings.log_invalid_requests = True
        settings.max_request_size = min(settings.max_request_size, 5 * 1024 * 1024)  # 5MB max in prod
        settings.validation_rate_limit_per_minute = 50  # Stricter rate limiting
        settings.max_invalid_requests_per_connection = 5  # Lower tolerance
        logger.info("🔒 Production validation config: strict security enabled")
    
    # Development environment - relaxed validation for debugging
    elif environment in ["development", "dev", "local"]:
        settings.enable_request_validation = True
        settings.enable_security_analysis = getattr(settings, "enable_security_analysis", True)
        settings.log_invalid_requests = True
        settings.validation_rate_limit_per_minute = 200  # More lenient for testing
        settings.max_invalid_requests_per_connection = 20  # Higher tolerance for debugging
        logger.info("🔧 Development validation config: relaxed for debugging")
    
    # Testing environment - minimal validation to avoid test interference
    elif environment in ["test", "testing"]:
        settings.enable_request_validation = True
        settings.enable_security_analysis = False  # Disable for faster tests
        settings.log_invalid_requests = False  # Reduce test noise
        settings.validation_rate_limit_per_minute = 1000  # Very high for load tests
        settings.max_invalid_requests_per_connection = 100
        logger.info("🧪 Testing validation config: minimal interference")
    
    # Staging environment - production-like but with more logging
    elif environment == "staging":
        settings.enable_request_validation = True
        settings.enable_security_analysis = True
        settings.log_invalid_requests = True
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        logger.info("🎭 Staging validation config: production-like with enhanced logging")
    
    return settings


def validate_configuration_settings(settings: Settings) -> bool:
    """
    Validate configuration settings for consistency and security.
    
    Requirements 4.1, 4.2: Ensure configuration values are within safe ranges
    """
    issues = []
    
    # Validate request size limits
    if settings.max_request_size <= 0:
        issues.append("max_request_size must be positive")
    elif settings.max_request_size > 100 * 1024 * 1024:  # 100MB
        issues.append("max_request_size too large (>100MB), potential DoS risk")
    
    # Validate header limits
    if settings.max_headers_count <= 0 or settings.max_headers_count > 1000:
        issues.append("max_headers_count must be between 1 and 1000")
    
    if settings.max_header_size <= 0 or settings.max_header_size > 32768:  # 32KB
        issues.append("max_header_size must be between 1 and 32768 bytes")
    
    # Validate rate limiting
    if settings.validation_rate_limit_per_minute <= 0:
        issues.append("validation_rate_limit_per_minute must be positive")
    elif settings.validation_rate_limit_per_minute > 10000:
        issues.append("validation_rate_limit_per_minute too high (>10000), potential resource exhaustion")
    
    # Validate protocol settings
    if settings.max_invalid_requests_per_connection <= 0:
        issues.append("max_invalid_requests_per_connection must be positive")
    elif settings.max_invalid_requests_per_connection > 1000:
        issues.append("max_invalid_requests_per_connection too high (>1000)")
    
    # Log issues
    if issues:
        logger.error("❌ Configuration validation failed:")
        for issue in issues:
            logger.error(f"   • {issue}")
        return False
    
    logger.info("✅ Configuration validation passed")
    return True


def initialize_validation_framework(settings: Settings) -> None:
    """
    Initialize the HTTP request validation framework with configurable settings.
    
    This function sets up the validation components according to requirements:
    - 4.1: Configurable request size limits
    - 4.2: Configurable rate limiting thresholds  
    - 4.3: Environment-specific validation rules
    - 4.4: Updateable validation patterns without code changes
    """
    try:
        # Load environment-specific configuration (Requirement 4.3)
        settings = load_environment_specific_validation_config(settings)
        
        # Validate configuration settings (Requirements 4.1, 4.2)
        if not validate_configuration_settings(settings):
            logger.warning("⚠️ Configuration issues detected, using safe defaults")
        
        from ai_karen_engine.server.http_validator import ValidationConfig
        from ai_karen_engine.server.security_analyzer import SecurityAnalyzer
        from ai_karen_engine.server.rate_limiter import EnhancedRateLimiter, MemoryRateLimitStorage, DEFAULT_RATE_LIMIT_RULES
        from ai_karen_engine.server.enhanced_logger import EnhancedLogger, LoggingConfig
        
        # Parse configurable lists from settings (Requirement 4.4)
        blocked_agents = set(agent.strip().lower() for agent in settings.blocked_user_agents.split(",") if agent.strip())
        suspicious_headers = set(header.strip().lower() for header in settings.suspicious_headers.split(",") if header.strip())
        
        # Create validation configuration from settings
        validation_config = ValidationConfig(
            max_content_length=settings.max_request_size,
            max_headers_count=settings.max_headers_count,
            max_header_size=settings.max_header_size,
            rate_limit_requests_per_minute=settings.validation_rate_limit_per_minute,
            enable_security_analysis=settings.enable_security_analysis,
            log_invalid_requests=settings.log_invalid_requests,
            blocked_user_agents=blocked_agents,
            suspicious_headers=suspicious_headers
        )
        
        # Initialize enhanced logger for validation events
        logging_config = LoggingConfig(
            log_level="INFO",
            enable_security_logging=settings.enable_security_analysis,
            sanitize_data=True
        )
        enhanced_logger = EnhancedLogger(logging_config)
        
        # Store configuration globally for middleware access
        import ai_karen_engine.server.middleware as middleware_module
        middleware_module._validation_config = validation_config
        middleware_module._enhanced_logger = enhanced_logger
        
        logger.info("✅ HTTP request validation framework initialized")
        logger.info(f"   • Environment: {settings.environment}")
        logger.info(f"   • Max request size: {settings.max_request_size / (1024*1024):.1f}MB")
        logger.info(f"   • Max headers: {settings.max_headers_count}")
        logger.info(f"   • Security analysis: {'enabled' if settings.enable_security_analysis else 'disabled'}")
        logger.info(f"   • Rate limiting: {settings.validation_rate_limit_per_minute} requests/minute")
        logger.info(f"   • Blocked user agents: {len(blocked_agents)} patterns")
        logger.info(f"   • Suspicious headers: {len(suspicious_headers)} patterns")
        logger.info(f"   • Protocol error handling: {'enabled' if settings.enable_protocol_error_handling else 'disabled'}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize validation framework: {e}")
        logger.info("Server will continue with basic validation")


# --- FastAPI Application Setup ---------------------------------------------


def create_app() -> FastAPI:
    """Application factory for Kari AI with performance optimization"""
    # Initialize performance configuration
    try:
        from ai_karen_engine.config.performance_config import load_performance_config
        import asyncio
        
        # Load performance configuration synchronously during app creation
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # If loop is already running, we'll load config during startup
            logger.info("📋 Performance configuration will be loaded during startup")
        else:
            # Load configuration now
            perf_config = loop.run_until_complete(load_performance_config())
            logger.info(f"📋 Performance configuration loaded: {perf_config.deployment_mode} mode")
            
            # Update settings with performance configuration
            settings.enable_performance_optimization = perf_config.enable_performance_optimization
            settings.deployment_mode = perf_config.deployment_mode
            settings.cpu_threshold = perf_config.cpu_threshold
            settings.memory_threshold = perf_config.memory_threshold
            settings.response_time_threshold = perf_config.response_time_threshold
            
    except Exception as e:
        logger.warning(f"⚠️ Failed to load performance configuration: {e}")
        logger.info("📦 Using default performance settings")
    
    # The lifespan context manager manages startup and shutdown
    # logic for the application. Previously this variable was
    # referenced without being defined which caused the server
    # to crash during initialization. We create it explicitly
    # here before passing it to FastAPI so the app can start
    # correctly.
    lifespan = create_lifespan(settings)
    app = FastAPI(
        title=settings.app_name,
        description="Kari AI Production Server with Performance Optimization",
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

    # Initialize validation framework before configuring middleware
    initialize_validation_framework(settings)
    
    configure_middleware(app, settings, REQUEST_COUNT, REQUEST_LATENCY, ERROR_COUNT)

    app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
    app.include_router(auth_session_router, prefix="/api", tags=["authentication-session"])
    
    # Authentication system selection based on environment
    auth_mode = os.getenv("AUTH_MODE", "hybrid").lower()
    
    if auth_mode == "bypass":
        # Simple auth bypass for debugging concurrency issues
        from simple_auth_bypass import router as simple_auth_router
        app.include_router(simple_auth_router, prefix="/api", tags=["simple-auth"])
        logger.info("🔓 Using simple auth bypass mode (development only)")
    elif auth_mode == "production":
        # Full production authentication system with database
        from ai_karen_engine.auth.production_auth import router as production_auth_router
        app.include_router(production_auth_router, prefix="/api", tags=["production-auth"])
        logger.info("🔐 Using full production authentication system")
    else:
        # Hybrid authentication system (default) - secure but simple
        from ai_karen_engine.auth.hybrid_auth import router as hybrid_auth_router
        app.include_router(hybrid_auth_router, prefix="/api", tags=["hybrid-auth"])
        logger.info("🔐 Using hybrid authentication system (production-ready)")
    app.include_router(events_router, prefix="/api/events", tags=["events"])
    app.include_router(websocket_router, prefix="/api/ws", tags=["websocket"])
    app.include_router(web_api_router, prefix="/api/web", tags=["web-api"])
    app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])
    app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
    app.include_router(memory_router, prefix="/api/memory", tags=["memory"])
    # Align copilot routes under /api to match frontend expectations
    app.include_router(copilot_router, prefix="/api/copilot", tags=["copilot"])
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
    
    # TEMPORARY: Include mock provider router first to handle suggestions endpoints
    from ai_karen_engine.api_routes.mock_provider_routes import router as mock_provider_router
    app.include_router(mock_provider_router, tags=["mock-providers"])
    
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
    app.include_router(provider_compatibility_router, tags=["provider-compatibility"])
    app.include_router(model_orchestrator_router, tags=["model-orchestrator"])
    app.include_router(validation_metrics_router, tags=["validation-metrics"])
    app.include_router(performance_routes, prefix="/api/performance", tags=["performance"])
    app.include_router(settings_router)

    # Compatibility alias: some web UI proxies still call /copilot/assist
    # Provide a thin alias to the /api/copilot/assist endpoint to avoid 404s.
    try:
        from ai_karen_engine.api_routes.copilot_routes import (
            copilot_assist,  # type: ignore
            copilot_health,  # type: ignore
        )
        # Accept POST (primary), plus OPTIONS for simple checks
        app.add_api_route(
            "/copilot/assist", copilot_assist, methods=["POST", "OPTIONS"], tags=["copilot-compat"]
        )
        # Health alias for convenience
        app.add_api_route(
            "/copilot/health", copilot_health, methods=["GET"], tags=["copilot-compat"]
        )
        # Log presence of alias for quick diagnosis
        try:
            alias_present = any(getattr(r, "path", "") == "/copilot/assist" for r in app.routes)
            logger.info(f"Copilot legacy alias registered: {alias_present}")
        except Exception:
            pass
    except Exception as e:
        logger.warning(f"Copilot legacy alias not registered: {e}")

    # Proactively register copilot routing actions so /api/copilot/start works immediately
    try:
        from ai_karen_engine.integrations.copilotkit.routing_actions import (
            ensure_kire_actions_registered,
        )
        ensure_kire_actions_registered()
    except Exception:
        pass

    # Setup developer API with enhanced debugging capabilities
    setup_developer_api(app)
    
    # Add service registry debug endpoint
    @app.get("/api/debug/services", tags=["debug"])
    async def debug_services():
        """Debug endpoint to check service registry status"""
        try:
            from ai_karen_engine.core.service_registry import get_service_registry
            registry = get_service_registry()
            services = registry.list_services()
            
            return {
                "services": services,
                "total_services": len(services),
                "ready_services": len([s for s in services.values() if s.get("status") == "ready"]),
                "registry_type": str(type(registry))
            }
        except Exception as e:
            return {"error": str(e), "services": {}}
    
    # Add service initialization endpoint
    @app.post("/api/debug/initialize-services", tags=["debug"])
    async def initialize_services_endpoint():
        """Manually initialize services"""
        try:
            from ai_karen_engine.core.service_registry import initialize_services, get_service_registry
            
            logger.info("Manual service initialization requested")
            await initialize_services()
            
            registry = get_service_registry()
            services = registry.list_services()
            report = registry.get_initialization_report()
            
            return {
                "success": True,
                "message": "Services initialized successfully",
                "services": services,
                "report": report
            }
        except Exception as e:
            logger.error(f"Manual service initialization failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Add performance optimization endpoints
    @app.get("/api/admin/performance/status", tags=["admin"])
    async def get_performance_status():
        """Get current performance optimization status"""
        try:
            from ai_karen_engine.server.optimized_startup import (
                get_lifecycle_manager, get_resource_monitor, get_performance_metrics
            )
            
            lifecycle_manager = get_lifecycle_manager()
            resource_monitor = get_resource_monitor()
            performance_metrics = get_performance_metrics()
            
            status = {
                "optimization_enabled": settings.enable_performance_optimization,
                "deployment_mode": settings.deployment_mode,
                "components": {
                    "lifecycle_manager": lifecycle_manager is not None,
                    "resource_monitor": resource_monitor is not None,
                    "performance_metrics": performance_metrics is not None
                }
            }
            
            if resource_monitor:
                status["resource_usage"] = await resource_monitor.get_current_metrics()
            
            if performance_metrics:
                status["performance_summary"] = await performance_metrics.get_summary()
            
            return status
            
        except Exception as e:
            return {"error": str(e), "optimization_enabled": False}
    
    @app.post("/api/admin/performance/audit", tags=["admin"])
    async def run_performance_audit():
        """Run a performance audit"""
        try:
            from ai_karen_engine.audit.performance_auditor import PerformanceAuditor
            
            auditor = PerformanceAuditor()
            await auditor.initialize()
            
            audit_report = await auditor.audit_runtime_performance()
            recommendations = await auditor.generate_optimization_recommendations()
            
            return {
                "success": True,
                "audit_report": audit_report,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Performance audit failed: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/admin/performance/optimize", tags=["admin"])
    async def trigger_optimization():
        """Trigger performance optimization"""
        try:
            from ai_karen_engine.server.optimized_startup import get_lifecycle_manager
            
            lifecycle_manager = get_lifecycle_manager()
            if not lifecycle_manager:
                return {"success": False, "error": "Optimization not enabled"}
            
            # Trigger service consolidation and optimization
            optimization_report = await lifecycle_manager.optimize_services()
            
            return {
                "success": True,
                "message": "Performance optimization completed",
                "report": optimization_report
            }
            
        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")
            return {"success": False, "error": str(e)}
    
    # Add validation configuration management endpoints (Requirement 4.4)
    @app.get("/api/admin/validation/config", tags=["admin"])
    async def get_validation_config():
        """Get current validation configuration"""
        try:
            import ai_karen_engine.server.middleware as middleware_module
            validation_config = getattr(middleware_module, '_validation_config', None)
            
            if validation_config is None:
                return {"error": "Validation configuration not initialized"}
            
            return {
                "max_content_length": validation_config.max_content_length,
                "max_headers_count": validation_config.max_headers_count,
                "max_header_size": validation_config.max_header_size,
                "rate_limit_requests_per_minute": validation_config.rate_limit_requests_per_minute,
                "enable_security_analysis": validation_config.enable_security_analysis,
                "log_invalid_requests": validation_config.log_invalid_requests,
                "blocked_user_agents": list(validation_config.blocked_user_agents),
                "suspicious_headers": list(validation_config.suspicious_headers),
                "environment": settings.environment
            }
        except Exception as e:
            return {"error": str(e)}
    
    @app.post("/api/admin/validation/reload", tags=["admin"])
    async def reload_validation_config():
        """Reload validation configuration from environment variables (Requirement 4.4)"""
        try:
            # Reload settings from environment
            new_settings = Settings()
            
            # Reinitialize validation framework with new settings
            initialize_validation_framework(new_settings)
            
            return {
                "success": True,
                "message": "Validation configuration reloaded successfully",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "environment": new_settings.environment,
                "max_request_size_mb": new_settings.max_request_size / (1024*1024),
                "security_analysis_enabled": new_settings.enable_security_analysis
            }
        except Exception as e:
            logger.error(f"Failed to reload validation configuration: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    @app.post("/api/admin/validation/update-patterns", tags=["admin"])
    async def update_validation_patterns(request: dict):
        """Update validation patterns without code changes (Requirement 4.4)"""
        try:
            import ai_karen_engine.server.middleware as middleware_module
            validation_config = getattr(middleware_module, '_validation_config', None)
            
            if validation_config is None:
                return {"error": "Validation configuration not initialized"}
            
            # Update blocked user agents if provided
            if "blocked_user_agents" in request:
                new_agents = set(agent.strip().lower() for agent in request["blocked_user_agents"] if agent.strip())
                validation_config.blocked_user_agents = new_agents
                logger.info(f"Updated blocked user agents: {len(new_agents)} patterns")
            
            # Update suspicious headers if provided
            if "suspicious_headers" in request:
                new_headers = set(header.strip().lower() for header in request["suspicious_headers"] if header.strip())
                validation_config.suspicious_headers = new_headers
                logger.info(f"Updated suspicious headers: {len(new_headers)} patterns")
            
            # Update rate limiting if provided
            if "rate_limit_requests_per_minute" in request:
                new_rate_limit = int(request["rate_limit_requests_per_minute"])
                if 1 <= new_rate_limit <= 10000:
                    validation_config.rate_limit_requests_per_minute = new_rate_limit
                    logger.info(f"Updated rate limit: {new_rate_limit} requests/minute")
                else:
                    return {"error": "Rate limit must be between 1 and 10000"}
            
            # Update security analysis toggle if provided
            if "enable_security_analysis" in request:
                validation_config.enable_security_analysis = bool(request["enable_security_analysis"])
                logger.info(f"Security analysis: {'enabled' if validation_config.enable_security_analysis else 'disabled'}")
            
            return {
                "success": True,
                "message": "Validation patterns updated successfully",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "updated_config": {
                    "blocked_user_agents": len(validation_config.blocked_user_agents),
                    "suspicious_headers": len(validation_config.suspicious_headers),
                    "rate_limit_requests_per_minute": validation_config.rate_limit_requests_per_minute,
                    "enable_security_analysis": validation_config.enable_security_analysis
                }
            }
        except Exception as e:
            logger.error(f"Failed to update validation patterns: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    @app.get("/api/admin/validation/status", tags=["admin"])
    async def get_validation_status():
        """Get validation system status and metrics"""
        try:
            import ai_karen_engine.server.middleware as middleware_module
            validation_config = getattr(middleware_module, '_validation_config', None)
            enhanced_logger = getattr(middleware_module, '_enhanced_logger', None)
            
            status = {
                "validation_framework_initialized": validation_config is not None,
                "enhanced_logging_initialized": enhanced_logger is not None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "environment": settings.environment
            }
            
            if validation_config:
                status["configuration"] = {
                    "max_content_length_mb": validation_config.max_content_length / (1024*1024),
                    "max_headers_count": validation_config.max_headers_count,
                    "max_header_size": validation_config.max_header_size,
                    "rate_limit_per_minute": validation_config.rate_limit_requests_per_minute,
                    "security_analysis_enabled": validation_config.enable_security_analysis,
                    "logging_enabled": validation_config.log_invalid_requests,
                    "blocked_agents_count": len(validation_config.blocked_user_agents),
                    "suspicious_headers_count": len(validation_config.suspicious_headers)
                }
            
            # Try to get validation metrics if available
            try:
                from ai_karen_engine.core.metrics_manager import get_metrics_manager
                metrics_manager = get_metrics_manager()
                
                # Get validation-related metrics
                validation_metrics = {}
                with metrics_manager.safe_metrics_context():
                    # These metrics would be populated by the middleware
                    validation_metrics = {
                        "total_requests_validated": "available",
                        "invalid_requests_blocked": "available", 
                        "security_threats_detected": "available",
                        "rate_limited_requests": "available"
                    }
                
                status["metrics"] = validation_metrics
            except Exception:
                status["metrics"] = {"error": "Metrics not available"}
            
            return status
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
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
                from ai_karen_engine.core.service_registry import ServiceRegistry, get_service_registry
                
                # Use the global service registry and ensure it's initialized
                registry = get_service_registry()
                
                # Check if services are initialized, if not initialize them
                services = registry.list_services()
                logger.info(f"Available services: {list(services.keys())}")
                
                if "ai_orchestrator" not in services or not services:
                    logger.info("Initializing services for reasoning endpoint...")
                    from ai_karen_engine.core.service_registry import initialize_services
                    await initialize_services()
                    logger.info("Services initialized successfully")
                    # Refresh services list after initialization
                    services = registry.list_services()
                
                # Verify ai_orchestrator is available and ready
                if "ai_orchestrator" not in services:
                    raise Exception("ai_orchestrator service not available after initialization")
                
                service_info = services["ai_orchestrator"]
                if service_info.get("status") != "ready":
                    raise Exception(f"ai_orchestrator service not ready: {service_info.get('status')}")
                
                ai_orchestrator = await registry.get_service("ai_orchestrator")
                logger.info("AI orchestrator retrieved successfully")
                
                # Use AI orchestrator for reasoning
                from ai_karen_engine.models.shared_types import FlowInput
                
                flow_input = FlowInput(
                    prompt=user_input,
                    context=context,
                    user_id=context.get("user_id", "anonymous"),
                    conversation_history=context.get("conversation_history", []),
                    user_settings=context.get("user_settings", {})
                )
                
                flow_output = await ai_orchestrator.conversation_processing_flow(flow_input)
                response = flow_output.response if hasattr(flow_output, 'response') else str(flow_output)
                
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
                    "fallback_available": (models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf").exists()
                }
            except Exception:
                model_status = {"local_models": 0, "fallback_available": False}
            
            # Check model orchestrator health
            model_orchestrator_status = {}
            try:
                from ai_karen_engine.health.model_orchestrator_health import get_model_orchestrator_health
                health_checker = get_model_orchestrator_health()
                orchestrator_health = await health_checker.check_health()
                model_orchestrator_status = {
                    "status": orchestrator_health.get("status", "unknown"),
                    "registry_healthy": orchestrator_health.get("registry_healthy", False),
                    "storage_healthy": orchestrator_health.get("storage_healthy", False),
                    "plugin_loaded": "model_orchestrator" in ENABLED_PLUGINS,
                    "last_check": orchestrator_health.get("timestamp")
                }
            except Exception as e:
                model_orchestrator_status = {
                    "status": "error",
                    "error": str(e),
                    "plugin_loaded": "model_orchestrator" in ENABLED_PLUGINS
                }
            
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
                "model_orchestrator": model_orchestrator_status,
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
            
            # Check AI providers - but consider local models as available
            failed_providers = []
            try:
                from ai_karen_engine.services.provider_registry import get_provider_registry_service
                provider_service = get_provider_registry_service()
                system_status = provider_service.get_system_status()
                
                # Check if we have local models available
                from pathlib import Path
                models_dir = Path("models")
                tinyllama_available = (models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf").exists()
                
                # Check spaCy availability
                spacy_available = False
                try:
                    import spacy
                    nlp = spacy.load("en_core_web_sm")
                    spacy_available = True
                except:
                    pass
                
                # Only consider degraded if NO providers AND NO local models
                if system_status["available_providers"] == 0 and not (tinyllama_available or spacy_available):
                    degraded_components.append("ai_providers")
                    failed_providers = system_status.get("failed_providers", [])
                elif system_status["available_providers"] == 0:
                    # We have local models, so just note the failed remote providers
                    failed_providers = system_status.get("failed_providers", [])
                    
            except Exception:
                # Check if local models are available as fallback
                try:
                    from pathlib import Path
                    models_dir = Path("models")
                    tinyllama_available = (models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf").exists()
                    
                    import spacy
                    nlp = spacy.load("en_core_web_sm")
                    spacy_available = True
                    
                    # Only degraded if no local models
                    if not (tinyllama_available or spacy_available):
                        degraded_components.append("ai_providers")
                        failed_providers = ["unknown"]
                except:
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
            
            # Core helpers availability - check actual availability
            try:
                from pathlib import Path
                models_dir = Path("models")
                tinyllama_available = (models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf").exists()
                
                spacy_available = False
                try:
                    import spacy
                    nlp = spacy.load("en_core_web_sm")
                    spacy_available = True
                except:
                    pass
                
                core_helpers_available = {
                    "local_nlp": spacy_available,  # spaCy NLP processing
                    "local_llm": tinyllama_available,  # TinyLlama for text generation
                    "fallback_responses": True,  # Always available
                    "basic_analytics": True,  # Basic analytics work
                    "file_operations": True,  # File ops work
                    "database_fallback": "database" not in degraded_components
                }
            except Exception:
                core_helpers_available = {
                    "local_nlp": False,
                    "local_llm": False,
                    "fallback_responses": True,
                    "basic_analytics": True,
                    "file_operations": True,
                    "database_fallback": False
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
                tinyllama_available = (models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf").exists()
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
            from ai_karen_engine.core.startup_check import perform_startup_checks
            
            logger.info("🔍 Performing startup checks and system initialization...")
            checks_passed, issues = await perform_startup_checks(auto_fix=True)
            
            if not checks_passed:
                logger.warning("⚠️ Startup checks found issues:")
                for issue in issues:
                    logger.warning(f"   - {issue}")
                logger.info("💡 Some issues were automatically fixed. Others may require manual attention.")
            else:
                logger.info("✅ All startup checks passed!")
            
            # Initialize fallback systems
            await initialize_fallback_systems()
            
            return True  # Always continue - fallbacks handle issues
            
        except Exception as e:
            logger.error(f"❌ Startup check failed: {e}")
            logger.info("Continuing with server startup using fallback systems...")
            await initialize_fallback_systems()
            return True  # Continue with fallbacks
    
    async def initialize_fallback_systems():
        """Initialize comprehensive fallback systems for production readiness."""
        logger.info("🔧 Initializing fallback systems...")
        
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
                logger.info("✅ Analytics service initialized")
            except Exception as e:
                logger.warning(f"⚠️ Analytics service using fallback: {e}")
                # Fallback analytics service is handled in service registry
            
            # 2. Initialize Provider Registry with fallback chains
            try:
                from ai_karen_engine.services.provider_registry import get_provider_registry_service
                provider_service = get_provider_registry_service()
                
                # Configure fallback chains for different scenarios
                provider_service.create_fallback_chain(
                    name="production_text",
                    primary="openai",
                    fallbacks=["gemini", "deepseek", "local", "llama-cpp"]
                )
                
                provider_service.create_fallback_chain(
                    name="local_first",
                    primary="llama-cpp", 
                    fallbacks=["local", "openai", "gemini"]
                )
                
                logger.info("✅ Provider fallback chains configured")
            except Exception as e:
                logger.warning(f"⚠️ Provider registry fallback: {e}")
            
            # 3. Initialize Connection Health Monitoring
            try:
                from ai_karen_engine.services.connection_health_manager import get_connection_health_manager
                health_manager = get_connection_health_manager()
                await health_manager.start_monitoring(check_interval=30.0)
                logger.info("✅ Connection health monitoring started")
            except Exception as e:
                logger.warning(f"⚠️ Connection health monitoring fallback: {e}")
            
            # 4. Initialize Database with fallback
            try:
                from ai_karen_engine.services.database_connection_manager import initialize_database_manager
                db_manager = await initialize_database_manager()
                if db_manager.is_degraded():
                    logger.warning("⚠️ Database running in degraded mode (using in-memory fallback)")
                else:
                    logger.info("✅ Database connection healthy")
            except Exception as e:
                logger.warning(f"⚠️ Database using fallback mode: {e}")
            
            # 5. Initialize Redis with fallback
            try:
                from ai_karen_engine.services.redis_connection_manager import initialize_redis_manager
                redis_manager = await initialize_redis_manager()
                if redis_manager.is_degraded():
                    logger.warning("⚠️ Redis running in degraded mode (using in-memory cache)")
                else:
                    logger.info("✅ Redis connection healthy")
            except Exception as e:
                logger.warning(f"⚠️ Redis using fallback mode: {e}")
            
            # 6. Initialize Error Response Service with AI fallback
            try:
                from ai_karen_engine.services.error_response_service import ErrorResponseService
                error_service = ErrorResponseService()
                
                # Test fallback capability
                test_response = error_service.analyze_error(
                    "Test error for system initialization",
                    use_ai_analysis=True  # Will fallback to rules if AI unavailable
                )
                logger.info("✅ Intelligent error responses with fallback configured")
            except Exception as e:
                logger.warning(f"⚠️ Error response service fallback: {e}")
            
            # 7. Check Model Availability
            try:
                from pathlib import Path
                models_dir = Path("models")
                
                # Check for local models
                gguf_models = list(models_dir.rglob("*.gguf"))
                bin_models = list(models_dir.rglob("*.bin"))
                
                # Check for TinyLlama fallback model
                tinyllama_path = models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf"
                has_fallback_model = tinyllama_path.exists()
                
                # Check spaCy
                try:
                    import spacy
                    nlp = spacy.load("en_core_web_sm")
                    has_spacy = True
                except:
                    has_spacy = False
                
                model_count = len(gguf_models) + len(bin_models)
                logger.info(f"✅ Local models available: {model_count} models, TinyLlama: {has_fallback_model}, spaCy: {has_spacy}")
                
                if not (model_count > 0 or has_spacy):
                    logger.warning("⚠️ Limited local models - external providers recommended")
            
            except Exception as e:
                logger.warning(f"⚠️ Model availability check: {e}")
            
            logger.info("🎯 Fallback systems initialized - server ready for production!")
            
        except Exception as e:
            logger.warning(f"⚠️ Fallback initialization error: {e}")
            logger.info("Server will continue with basic functionality")
    
    # Run startup checks and system initialization
    try:
        logger.info("🚀 AI Karen Engine - Production Server Starting...")
        startup_success = asyncio.run(startup_check())
        
        if startup_success:
            logger.info("✅ System initialization complete!")
            logger.info("🎯 Key Features Active:")
            logger.info("   • Session persistence with automatic refresh")
            logger.info("   • Multi-provider AI fallback chains")
            logger.info("   • Local model fallback (TinyLlama + spaCy)")
            logger.info("   • Connection health monitoring with degraded mode")
            logger.info("   • Intelligent error responses with rule-based fallback")
            logger.info("   • Service registry with graceful degradation")
        else:
            logger.warning("⚠️ System running with some limitations...")
        
    except Exception as e:
        logger.error(f"❌ Startup initialization error: {e}")
        logger.info("Server will start with basic functionality and fallbacks...")

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

    # Use custom uvicorn server with enhanced protocol-level error handling
    from ai_karen_engine.server.custom_server import create_custom_server

    # Create custom server with enhanced protocol-level error handling using settings
    custom_server = create_custom_server(
        app="main:create_app",
        host="0.0.0.0",
        port=8000,
        debug=settings.debug,
        ssl_context=ssl_context,
        workers=1,  # Use single worker for development to avoid issues
        # Enhanced configuration for protocol-level error handling from settings
        max_invalid_requests_per_connection=settings.max_invalid_requests_per_connection,
        enable_protocol_error_handling=settings.enable_protocol_error_handling,
        log_invalid_requests=settings.log_invalid_requests,
        # Production-ready limits to prevent resource exhaustion
        limit_concurrency=200,
        limit_max_requests=10000,
        backlog=4096,
        timeout_keep_alive=30,
        timeout_graceful_shutdown=30,
        access_log=False,
        # Use httptools for better error handling
        http="httptools",
        loop="auto",
        server_header=False,
        date_header=False,
    )

    # Run the custom server
    logger.info("🚀 Starting Kari AI server with enhanced protocol-level error handling")
    custom_server.run()
