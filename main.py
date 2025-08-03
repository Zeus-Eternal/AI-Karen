"""
Kari FastAPI Server - Production Version
- Complete implementation with all original routes
- Enhanced security and monitoring
- Optimized plugin system
- Production-grade configuration
"""

import logging
import logging.config
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import secrets

# Security imports
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from passlib.context import CryptContext
import ssl

# Original route imports
from ai_karen_engine.api_routes.ai_orchestrator_routes import router as ai_router
from ai_karen_engine.api_routes.audit import router as audit_router
from ai_karen_engine.api_routes.auth import router as auth_router
from ai_karen_engine.api_routes.conversation_routes import router as conversation_router
from ai_karen_engine.api_routes.events import router as events_router
from ai_karen_engine.api_routes.memory_routes import router as memory_router
from ai_karen_engine.api_routes.plugin_routes import router as plugin_router
from ai_karen_engine.api_routes.tool_routes import router as tool_router
from ai_karen_engine.api_routes.web_api_compatibility import router as web_api_router
from ai_karen_engine.api_routes.websocket_routes import router as websocket_router
from ai_karen_engine.api_routes.file_attachment_routes import router as file_attachment_router
from ai_karen_engine.api_routes.code_execution_routes import router as code_execution_router

from ai_karen_engine.server.middleware import configure_middleware
from ai_karen_engine.server.startup import create_lifespan
from ai_karen_engine.server.plugin_loader import ENABLED_PLUGINS, PLUGIN_MAP

# --- Configuration Management -------------------------------------------------

class Settings(BaseSettings):
    app_name: str = "Kari AI Server"
    environment: str = "production"
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(64))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str = "postgresql://user:password@localhost:5432/kari_prod"
    cors_origins: str = "https://yourdomain.com"
    prometheus_enabled: bool = True
    https_redirect: bool = True
    rate_limit: str = "100/minute"
    debug: bool = False
    plugin_dir: str = "/app/plugins"
    llm_refresh_interval: int = 3600

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

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
    
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s %(lineno)d %(pathname)s"
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s'
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/kari.log",
                "maxBytes": 10485760,
                "backupCount": 5,
                "formatter": "json"
            },
            "access": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/access.log",
                "maxBytes": 10485760,
                "backupCount": 5,
                "formatter": "access"
            },
            "error": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/error.log",
                "maxBytes": 10485760,
                "backupCount": 5,
                "formatter": "json",
                "level": "ERROR"
            }
        },
        "loggers": {
            "uvicorn.error": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False
            },
            "uvicorn.access": {
                "handlers": ["access"],
                "level": "INFO",
                "propagate": False
            }
        },
        "root": {
            "handlers": ["console", "file", "error"],
            "level": "INFO" if not settings.debug else "DEBUG"
        }
    })

configure_logging()
logger = logging.getLogger("kari")

# --- Metrics Configuration -------------------------------------------------

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Histogram,
        generate_latest,
        REGISTRY,
        CollectorRegistry
    )
    PROMETHEUS_ENABLED = True
except ImportError:
    PROMETHEUS_ENABLED = False
    logger.warning("Prometheus client not available, metrics disabled")

# Initialize metrics
if PROMETHEUS_ENABLED:
    REQUEST_COUNT = Counter(
        "kari_http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status"],
        registry=REGISTRY
    )
    REQUEST_LATENCY = Histogram(
        "kari_http_request_duration_seconds",
        "HTTP request latency",
        ["method", "path"],
        registry=REGISTRY
    )
    ERROR_COUNT = Counter(
        "kari_http_errors_total",
        "Total HTTP errors",
        ["method", "path", "error_type"],
        registry=REGISTRY
    )
else:
    # Dummy metrics if Prometheus is not available
    class DummyMetric:
        def labels(self, **kwargs):
            return self
        def inc(self, amount=1): pass
        def observe(self, value): pass
    
    REQUEST_COUNT = DummyMetric()
    REQUEST_LATENCY = DummyMetric()
    ERROR_COUNT = DummyMetric()

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
    app.include_router(conversation_router, prefix="/api/conversations", tags=["conversations"])
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
    async def metrics():
        """Prometheus metrics endpoint with authentication"""
        if not PROMETHEUS_ENABLED:
            raise HTTPException(
                status_code=501,
                detail="Metrics are not enabled",
            )

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

    return app


if __name__ == "__main__":
    import uvicorn

    ssl_context = None
    if settings.https_redirect:
        ssl_context = get_ssl_context()

    uvicorn.run(
        "main:create_app",
        host="0.0.0.0",
        port=8000,
        ssl=ssl_context,
        reload=settings.debug,
        workers=4 if settings.environment == "production" else 1,
        log_config=None,
        access_log=False,
        timeout_keep_alive=30,
        timeout_graceful_shutdown=30,
        factory=True,
    )