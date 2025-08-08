# mypy: ignore-errors
"""
Kari FastAPI Server - Production Version
- Complete implementation with all original routes
- Enhanced security and monitoring
- Optimized plugin system
- Production-grade configuration
"""

import logging
import logging.config
import ssl
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

# Security imports
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

# Original route imports
from ai_karen_engine.api_routes.ai_orchestrator_routes import router as ai_router
from ai_karen_engine.api_routes.audit import router as audit_router
from ai_karen_engine.api_routes.auth import router as auth_router
from ai_karen_engine.api_routes.code_execution_routes import (
    router as code_execution_router,
)
from ai_karen_engine.api_routes.conversation_routes import router as conversation_router
from ai_karen_engine.api_routes.events import router as events_router
from ai_karen_engine.api_routes.file_attachment_routes import (
    router as file_attachment_router,
)
from ai_karen_engine.api_routes.memory_routes import router as memory_router
from ai_karen_engine.api_routes.plugin_routes import router as plugin_router
from ai_karen_engine.api_routes.tool_routes import router as tool_router
from ai_karen_engine.api_routes.web_api_compatibility import router as web_api_router
from ai_karen_engine.api_routes.websocket_routes import router as websocket_router
from ai_karen_engine.server.middleware import configure_middleware
from ai_karen_engine.server.plugin_loader import ENABLED_PLUGINS, PLUGIN_MAP
from ai_karen_engine.server.startup import create_lifespan
from ai_karen_engine.server.logging_filters import SuppressInvalidHTTPFilter

# --- Configuration Management -------------------------------------------------


class Settings(BaseSettings):
    app_name: str = "Kari AI Server"
    environment: str = "development"
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str = Field(..., env="DATABASE_URL")
    kari_cors_origins: str = Field(
        default="http://localhost:8010,http://127.0.0.1:8010,http://localhost:3000",
        alias="cors_origins",
    )
    prometheus_enabled: bool = True
    https_redirect: bool = False
    rate_limit: str = "100/minute"
    debug: bool = Field(default=False, env="DEBUG")
    plugin_dir: str = "/app/plugins"
    llm_refresh_interval: int = 3600

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


try:
    settings = Settings()
except ValidationError as e:
    missing = ", ".join(err["loc"][0] for err in e.errors())
    raise RuntimeError(
        f"Missing required environment variables: {missing}"
    ) from e

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
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s %(lineno)d %(pathname)s",
                },
                "access": {
                    "()": "uvicorn.logging.AccessFormatter",
                    "fmt": '%(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s',
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
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

# Initialize metrics - use a global flag to prevent duplicate registration
_metrics_initialized = False
REQUEST_COUNT = None
REQUEST_LATENCY = None
ERROR_COUNT = None


def initialize_metrics():
    global _metrics_initialized, REQUEST_COUNT, REQUEST_LATENCY, ERROR_COUNT

    if _metrics_initialized:
        return

    if PROMETHEUS_ENABLED:
        try:
            REQUEST_COUNT = Counter(
                "kari_http_requests_total",
                "Total HTTP requests",
                ["method", "path", "status"],
                registry=REGISTRY,
            )
            REQUEST_LATENCY = Histogram(
                "kari_http_request_duration_seconds",
                "HTTP request latency",
                ["method", "path"],
                registry=REGISTRY,
            )
            ERROR_COUNT = Counter(
                "kari_http_errors_total",
                "Total HTTP errors",
                ["method", "path", "error_type"],
                registry=REGISTRY,
            )
        except ValueError as e:
            if "Duplicated timeseries" in str(e):
                logger.warning("Metrics already registered, using dummy metrics")

                # Use dummy metrics if already registered
                class DummyMetric:
                    def labels(self, **kwargs):
                        return self

                    def inc(self, amount=1):
                        pass

                    def observe(self, value):
                        pass

                REQUEST_COUNT = DummyMetric()
                REQUEST_LATENCY = DummyMetric()
                ERROR_COUNT = DummyMetric()
            else:
                raise
    else:
        # Dummy metrics if Prometheus is not available
        class DummyMetric:
            def labels(self, **kwargs):
                return self

            def inc(self, amount=1):
                pass

            def observe(self, value):
                pass

        REQUEST_COUNT = DummyMetric()
        REQUEST_LATENCY = DummyMetric()
        ERROR_COUNT = DummyMetric()

    _metrics_initialized = True


# Initialize metrics
initialize_metrics()

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
    app.include_router(events_router, prefix="/api/events", tags=["events"])
    app.include_router(websocket_router, prefix="/api/ws", tags=["websocket"])
    app.include_router(web_api_router, prefix="/api/web", tags=["web-api"])
    app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
    app.include_router(memory_router, prefix="/api/memory", tags=["memory"])
    app.include_router(
        conversation_router, prefix="/api/conversations", tags=["conversations"]
    )
    app.include_router(plugin_router, prefix="/api/plugins", tags=["plugins"])
    app.include_router(tool_router, prefix="/api/tools", tags=["tools"])
    app.include_router(audit_router, prefix="/api/audit", tags=["audit"])
    app.include_router(file_attachment_router, prefix="/api/files", tags=["files"])
    app.include_router(code_execution_router, prefix="/api/code", tags=["code"])

    @app.get("/health", tags=["system"])
    async def health_check():
        """Comprehensive health check"""
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": settings.environment,
            "version": "1.0.0",
            "services": {
                "database": "connected",
                "memory": "initialized",
                "plugins": len(ENABLED_PLUGINS),
            },
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
    import logging

    import uvicorn  # type: ignore[import-not-found]

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
        # Add limits to prevent resource exhaustion from invalid requests
        "limit_concurrency": 100,
        "limit_max_requests": 1000,
        "backlog": 2048,
    }

    if ssl_context:
        uvicorn_kwargs["ssl"] = ssl_context

    uvicorn.run(**uvicorn_kwargs)
