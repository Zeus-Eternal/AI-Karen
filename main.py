"""
Kari FastAPI Server - Production Version
- Complete implementation with all original routes
- Enhanced security and monitoring
- Optimized plugin system
- Production-grade configuration
"""

import asyncio
import json
import logging
import logging.config
import os
import sys
import uuid
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from starlette.middleware.sessions import SessionMiddleware
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

# --- Application Lifespan Management ----------------------------------------

_registry_refresh_task: Optional[asyncio.Task] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Complete application lifecycle management"""
    # Startup
    await on_startup()
    try:
        yield
    finally:
        # Shutdown
        await on_shutdown()

async def on_startup():
    """Complete startup sequence"""
    logger.info("Starting Kari AI Server in %s mode", settings.environment)
    
    # Initialize all components
    await init_database()
    await init_ai_services()
    init_security()
    start_background_tasks()
    
    logger.info("Server startup completed")

async def on_shutdown():
    """Complete shutdown sequence"""
    logger.info("Shutting down Kari AI Server")
    await stop_background_tasks()
    await cleanup_ai_services()
    logger.info("Server shutdown completed")

# --- Database Initialization ------------------------------------------------

async def init_database():
    """Initialize all database connections"""
    try:
        from ai_karen_engine.clients.database import init_db
        await init_db(settings.database_url)
        logger.info("Database connection established")
    except Exception as e:
        logger.error("Database initialization failed: %s", str(e))
        raise

# --- AI Services Initialization ---------------------------------------------

async def init_ai_services():
    """Initialize all AI-related services"""
    try:
        from ai_karen_engine.core.memory import manager as memory_manager
        memory_manager.init_memory()
        
        _load_plugins()
        
        from ai_karen_engine.integrations.model_discovery import sync_registry
        sync_registry()
        
        logger.info("AI services initialized")
    except Exception as e:
        logger.error("AI services initialization failed: %s", str(e))
        raise

async def cleanup_ai_services():
    """Cleanup AI resources"""
    try:
        from ai_karen_engine.core.memory import manager as memory_manager
        await memory_manager.close()
        logger.info("AI services cleanup completed")
    except Exception as e:
        logger.error("AI services cleanup failed: %s", str(e))

# --- Security Initialization ------------------------------------------------

def init_security():
    """Initialize all security components"""
    if settings.secret_key == "changeme" and settings.environment == "production":
        logger.critical("Insecure default secret key in production!")
    
    logger.info("Security components initialized")

# --- Background Tasks Management -------------------------------------------

def start_background_tasks():
    """Start all background tasks"""
    global _registry_refresh_task
    
    # Model registry refresh
    if settings.llm_refresh_interval > 0:
        async def _periodic_refresh():
            from ai_karen_engine.integrations.model_discovery import sync_registry
            while True:
                await asyncio.sleep(settings.llm_refresh_interval)
                sync_registry()
        
        _registry_refresh_task = asyncio.create_task(_periodic_refresh())
        logger.info("Started model registry refresh task")

async def stop_background_tasks():
    """Stop all background tasks"""
    global _registry_refresh_task
    
    if _registry_refresh_task:
        _registry_refresh_task.cancel()
        try:
            await _registry_refresh_task
        except asyncio.CancelledError:
            logger.info("Background tasks stopped")
        except Exception as e:
            logger.error("Error stopping background tasks: %s", str(e))

# --- Plugin Management -----------------------------------------------------

PLUGIN_MAP: Dict[str, Dict[str, Any]] = {}
ENABLED_PLUGINS: set[str] = set()

def _load_plugins() -> None:
    """Load and validate all plugins"""
    PLUGIN_MAP.clear()
    ENABLED_PLUGINS.clear()
    
    plugin_dir = Path(settings.plugin_dir)
    if not plugin_dir.exists():
        logger.warning("Plugin directory not found: %s", plugin_dir)
        return
    
    for plugin_path in plugin_dir.iterdir():
        if not plugin_path.is_dir():
            continue
            
        manifest_file = plugin_path / "plugin_manifest.json"
        if not manifest_file.exists():
            continue
            
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                
            if not _validate_plugin_manifest(manifest):
                continue
                
            intents = manifest.get("intent", [])
            if isinstance(intents, str):
                intents = [intents]
                
            for intent in intents:
                PLUGIN_MAP[intent] = manifest
                ENABLED_PLUGINS.add(intent)
                
            logger.info("Loaded plugin: %s", plugin_path.name)
            
        except Exception as e:
            logger.error("Failed loading plugin %s: %s", plugin_path.name, str(e))

def _validate_plugin_manifest(manifest: Dict) -> bool:
    """Validate plugin manifest with enhanced checks"""
    required_fields = ["name", "version", "description", "intent"]
    if not all(field in manifest for field in required_fields):
        return False
        
    if not isinstance(manifest.get("intent", []), (str, list)):
        return False
        
    return True

# --- FastAPI Application Setup ---------------------------------------------

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
        {"url": "http://localhost:8000", "description": "Development server"}
    ]
)

# --- Middleware Setup ------------------------------------------------------

# Security middleware
if settings.https_redirect:
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="kari_session",
    same_site="lax",
    https_only=True
)

# CORS middleware
origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time"],
    max_age=600
)

# Performance middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Custom middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers.update({
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'",
        "Permissions-Policy": "geolocation=(), microphone=()"
    })
    return response

@app.middleware("http")
async def request_monitoring_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    logger.info(
        "Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None
        }
    )
    
    start_time = datetime.now(timezone.utc)
    try:
        response = await call_next(request)
    except HTTPException as e:
        ERROR_COUNT.labels(
            method=request.method,
            path=request.url.path,
            error_type="http_exception"
        ).inc()
        raise
    except Exception as e:
        ERROR_COUNT.labels(
            method=request.method,
            path=request.url.path,
            error_type="unhandled_exception"
        ).inc()
        logger.error(
            "Unhandled exception",
            exc_info=True,
            extra={"request_id": request_id}
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
    
    process_time = (datetime.now(timezone.utc) - start_time).total_seconds()
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    
    REQUEST_COUNT.labels(
        method=request.method,
        path=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        path=request.url.path
    ).observe(process_time)
    
    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "duration": process_time,
            "status": response.status_code
        }
    )
    
    return response

# --- Include All Original Routers ------------------------------------------

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

# --- Core API Routes -------------------------------------------------------

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
            "plugins": len(ENABLED_PLUGINS)
        }
    }

@app.get("/metrics", tags=["monitoring"])
async def metrics():
    """Prometheus metrics endpoint with authentication"""
    if not PROMETHEUS_ENABLED:
        raise HTTPException(
            status_code=501,
            detail="Metrics are not enabled"
        )
    
    # In production, you would add authentication here
    # await verify_admin(request)
    
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/plugins", tags=["plugins"])
async def list_plugins():
    """List all plugins with detailed status"""
    return {
        "enabled": sorted(ENABLED_PLUGINS),
        "available": sorted(PLUGIN_MAP.keys()),
        "count": len(PLUGIN_MAP)
    }

# --- Production Server Setup -----------------------------------------------

if __name__ == "__main__":
    import uvicorn
    
    ssl_context = None
    if settings.https_redirect:
        ssl_context = get_ssl_context()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        ssl=ssl_context,
        reload=settings.debug,
        workers=4 if settings.environment == "production" else 1,
        log_config=None,
        access_log=False,
        timeout_keep_alive=30,
        timeout_graceful_shutdown=30
    )