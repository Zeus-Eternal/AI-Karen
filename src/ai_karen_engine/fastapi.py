"""
src/ai_karen_engine/fastapi.py

Kari AI — Evil Twin Production FastAPI/ASGI API Core

Features:
- Universal FastAPI export, drop-in for any ASGI/uvicorn/gunicorn server
- Modular plugin/route discovery (auto-loads /plugins/ and /api_routes/)
- Built-in Prometheus metrics endpoint and healthz/livez probes
- Full audit and structured logging (per request ID, user, path, error, latency)
- RBAC & auth placeholder, ready for JWT/OAuth2/SSO
- Per-env CORS, rate limit, admin UI injection
- Exception handler with security/traceback control
- Ready for headless (CLI, test, mobile) or API-first (web, node, Tauri) operation

"""

import os
import logging
import uuid
from datetime import datetime

from ai_karen_engine.core.memory.manager import init_memory
from ai_karen_engine.utils.auth import validate_session
from ai_karen_engine.extensions import initialize_extension_manager
from ai_karen_engine.plugins.router import get_plugin_router

try:
    from fastapi import FastAPI, APIRouter, Request, Response, status
    from fastapi.responses import JSONResponse, RedirectResponse, PlainTextResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.gzip import GZipMiddleware
except ImportError:
    from ai_karen_engine.fastapi_stub import FastAPI, JSONResponse
    APIRouter = object
    Request = object
    Response = object
    CORSMiddleware = object
    GZipMiddleware = object
    RedirectResponse = object
    PlainTextResponse = object
    status = type('status', (), {'HTTP_500_INTERNAL_SERVER_ERROR': 500})

# -- Structured Logging, Per-Request Trace/Audit --
logger = logging.getLogger("kari_fastapi")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)

# -- Universal FastAPI Instance (for ASGI) --
app = FastAPI(
    title="Kari AI: Modular Orchestrator",
    description="Kari AI: Production-grade modular LLM, memory, plugin and API core.",
    version=os.getenv("KARI_VERSION", "1.0.0"),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    root_path=os.getenv("KARI_API_ROOT", ""),
)

@app.on_event("startup")
async def _init_memory() -> None:
    init_memory()

@app.on_event("startup")
async def _init_ai_karen_integration() -> None:
    """Initialize AI Karen engine integration services."""
    try:
        # Initialize configuration management
        from ai_karen_engine.core.config_manager import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.load_config()
        logger.info(f"Configuration loaded for environment: {config.environment}")
        
        # Initialize service registry and core services
        from ai_karen_engine.core.service_registry import initialize_services
        await initialize_services()
        logger.info("AI Karen integration services initialized")
        
        # Set up health monitoring
        from ai_karen_engine.core.health_monitor import setup_default_health_checks, get_health_monitor
        await setup_default_health_checks()
        health_monitor = get_health_monitor()
        health_monitor.start_monitoring()
        logger.info("Health monitoring started")
        
    except Exception as e:
        logger.error(f"Failed to initialize AI Karen integration: {e}")
        # Don't fail startup completely, but log the error
        raise

@app.on_event("startup")
async def _init_extensions() -> None:
    """Initialize the extension system."""
    from pathlib import Path
    
    # Initialize extension manager
    extension_root = Path("extensions")
    plugin_router = get_plugin_router()
    
    extension_manager = initialize_extension_manager(
        extension_root=extension_root,
        plugin_router=plugin_router,
        db_session=None,  # TODO: Pass actual DB session
        app_instance=app
    )
    
    # Load all available extensions
    try:
        loaded_extensions = await extension_manager.load_all_extensions()
        logger.info(f"Loaded {len(loaded_extensions)} extensions")
        
        # Mount extension API routes
        for name, record in loaded_extensions.items():
            if record.instance and hasattr(record.instance, 'get_api_router'):
                router = record.instance.get_api_router()
                if router:
                    app.include_router(router, tags=[f"extension-{name}"])
                    logger.info(f"Mounted API routes for extension: {name}")
                    
    except Exception as e:
        logger.error(f"Failed to load extensions: {e}")
        # Don't fail startup if extensions fail to load


@app.on_event("startup")
async def _bootstrap_memory_defaults() -> None:
    """Ensure memory tables exist and default models are loaded."""
    try:
        from ai_karen_engine.core.service_registry import get_service_registry
        from ai_karen_engine.core import default_models

        registry = get_service_registry()
        memory_service = await registry.get_service("memory_service")
        base_manager = memory_service.base_manager
        db_client = base_manager.db_client
        db_client.ensure_memory_table("default")

        # Load default models
        await default_models.load_default_models()
        logger.info("Default models initialized")
    except Exception as exc:
        logger.error(f"Failed to bootstrap memory defaults: {exc}")
        raise RuntimeError("Memory bootstrap failed") from exc

# -- Prometheus Metrics (optional) --
try:
    from prometheus_client import make_asgi_app
    app.mount("/metrics", make_asgi_app())
    logger.info("Prometheus metrics endpoint mounted at /metrics")
except ImportError:
    logger.info("Prometheus metrics not installed; skipping /metrics mount")

# -- Enhanced CORS Config for Web UI Integration --
allowed_origins = os.getenv("KARI_CORS_ORIGINS", "*")

# Parse multiple origins if provided as comma-separated string
if allowed_origins != "*":
    origins_list = [origin.strip() for origin in allowed_origins.split(",")]
else:
    origins_list = ["*"]

# Add common web UI development origins if in development mode
if os.getenv("KARI_ENV", "local").lower() in ["local", "development", "dev"]:
    dev_origins = [
        "http://localhost:3000",  # Next.js default
        "http://localhost:3001",  # Alternative port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:8080",  # Vue/other frameworks
        "http://127.0.0.1:8080",
    ]
    if origins_list == ["*"]:
        origins_list = dev_origins
    else:
        origins_list.extend(dev_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Web-UI-Compatible",
        "X-Kari-Trace-Id",
        "User-Agent",
        "Cache-Control",
        "Pragma",
    ],
    expose_headers=[
        "X-Kari-Trace-Id",
        "X-Web-UI-Compatible", 
        "X-Response-Time-Ms",
        "Content-Length",
        "Content-Type",
    ],
    max_age=86400,  # 24 hours for preflight cache
)

logger.info(f"CORS configured for origins: {origins_list}")
# -- GZip for payloads (auto, if available) --
try:
    app.add_middleware(GZipMiddleware, minimum_size=512)
except Exception:
    pass

# --- Plugin/Router Auto-Discovery (production-ready) ---
def auto_discover_routers(app):
    """
    Scans 'api_routes' and 'plugins' for FastAPI routers and mounts them.
    Prioritizes web API compatibility routes for proper precedence.
    """
    import importlib
    import pkgutil

    # First, explicitly mount web API compatibility router for proper precedence
    try:
        from ai_karen_engine.api_routes.web_api_compatibility import router as web_api_router
        app.include_router(web_api_router)
        logger.info("Mounted web API compatibility router with priority")
    except ImportError as e:
        logger.warning(f"Web API compatibility router not found: {e}")
    except Exception as e:
        logger.error(f"Failed to mount web API compatibility router: {e}")

    # Internal app routes (api_routes/*.py) - skip web_api_compatibility as it's already mounted
    try:
        from ai_karen_engine import api_routes
        package = api_routes
        prefix = ""  # Routes already have their own prefixes
    except ImportError:
        package = None

    if package:
        for loader, name, is_pkg in pkgutil.iter_modules(package.__path__):
            # Skip web_api_compatibility as it's already mounted with priority
            if name == "web_api_compatibility":
                continue
                
            try:
                mod = importlib.import_module(f"ai_karen_engine.api_routes.{name}")
                router = getattr(mod, "router", None)
                if isinstance(router, APIRouter) and hasattr(router, "routes"):
                    app.include_router(router)
                    logger.info(f"Mounted router: {name}")
            except Exception as e:
                logger.error(f"Failed to mount router {name}: {e}")

    # Plugins (plugins/*.py)
    plugin_dir = os.path.join(os.path.dirname(__file__), "..", "plugins")
    if os.path.isdir(plugin_dir):
        for fname in os.listdir(plugin_dir):
            if fname.endswith(".py") and not fname.startswith("_"):
                mod_name = fname[:-3]
                try:
                    spec = importlib.util.spec_from_file_location(
                        f"plugins.{mod_name}", os.path.join(plugin_dir, fname)
                    )
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    router = getattr(mod, "router", None)
                    if isinstance(router, APIRouter) and hasattr(router, "routes"):
                        app.include_router(router, prefix=f"/plugins/{mod_name}")
                        logger.info(f"Mounted plugin: /plugins/{mod_name}")
                except Exception as e:
                    logger.error(f"Failed to mount plugin {mod_name}: {e}")

auto_discover_routers(app)

# -- Trace ID + Logging Per Request --
@app.middleware("http")
async def add_trace_and_audit(request: Request, call_next):
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id
    logger.info(f"[{trace_id}] {request.method} {request.url.path} from {request.client.host}")
    try:
        response = await call_next(request)
        logger.info(f"[{trace_id}] {request.method} {request.url.path} status={response.status_code}")
        response.headers["X-Kari-Trace-Id"] = trace_id
        return response
    except Exception as e:
        logger.error(f"[{trace_id}] Exception: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal Server Error", "trace_id": trace_id, "detail": str(e)},
        )

# -- Web UI API Request/Response Logging Middleware --
@app.middleware("http")
async def web_ui_api_logging(request: Request, call_next):
    """Enhanced logging middleware for web UI API endpoints."""
    
    # Check if this is a web UI API request
    is_web_ui_api = (
        request.url.path.startswith("/api/chat/") or
        request.url.path.startswith("/api/memory/") or
        request.url.path.startswith("/api/plugins/") or
        request.url.path.startswith("/api/analytics/") or
        request.url.path.startswith("/api/health")
    )
    
    if not is_web_ui_api:
        return await call_next(request)
    
    trace_id = getattr(request.state, 'trace_id', str(uuid.uuid4()))
    start_time = datetime.utcnow()
    
    # Log request details for web UI endpoints
    user_agent = request.headers.get("user-agent", "unknown")
    content_type = request.headers.get("content-type", "unknown")
    
    logger.info(
        f"[{trace_id}] WEB_UI_API {request.method} {request.url.path} "
        f"from {request.client.host} UA: {user_agent[:50]} CT: {content_type}"
    )
    
    # Log request body for POST/PUT requests (with size limit for security)
    if request.method in ["POST", "PUT", "PATCH"] and os.getenv("KARI_LOG_REQUEST_BODY", "false").lower() == "true":
        try:
            body = await request.body()
            if len(body) < 1000:  # Only log small request bodies
                logger.debug(f"[{trace_id}] Request body: {body.decode('utf-8', errors='ignore')}")
            else:
                logger.debug(f"[{trace_id}] Request body size: {len(body)} bytes (too large to log)")
        except Exception as e:
            logger.debug(f"[{trace_id}] Could not read request body: {e}")
    
    try:
        response = await call_next(request)
        
        # Calculate response time
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Log response details
        logger.info(
            f"[{trace_id}] WEB_UI_API {request.method} {request.url.path} "
            f"status={response.status_code} time={response_time_ms:.2f}ms"
        )
        
        # Add web UI specific headers
        response.headers["X-Web-UI-Compatible"] = "true"
        response.headers["X-Response-Time-Ms"] = str(int(response_time_ms))
        
        # Log error responses for debugging
        if response.status_code >= 400:
            logger.warning(
                f"[{trace_id}] WEB_UI_API Error {response.status_code} for {request.method} {request.url.path} "
                f"time={response_time_ms:.2f}ms"
            )
        
        return response
        
    except Exception as e:
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        logger.error(
            f"[{trace_id}] WEB_UI_API Exception in {request.method} {request.url.path} "
            f"time={response_time_ms:.2f}ms: {e}", 
            exc_info=True
        )
        
        # Return structured error response for web UI
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred while processing your request",
                "type": "INTERNAL_SERVER_ERROR",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "details": {"error_type": type(e).__name__} if os.getenv("KARI_DEBUG", "false").lower() == "true" else None
            },
        )

# -- OAuth2 Bearer Token Validation --
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Validate Bearer JWT tokens and attach user context."""

    public_paths = {
        "/health",
        "/livez",
        "/readyz",
        "/",
        "/docs",
        "/openapi.json",
        "/api/auth/login",
        "/api/auth/token",
        "/api/llm/providers",
        "/api/llm/profiles",
        "/api/llm/settings",
        "/api/llm/health-check",
        "/api/llm/available",
        "/api/llm/auto-select",
    }

    if request.url.path in public_paths:
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    token = auth_header.split(None, 1)[1]
    ctx = validate_session(token, request.headers.get("user-agent", ""), request.client.host)
    if not ctx:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    request.state.user = ctx.get("sub")
    request.state.roles = list(ctx.get("roles", []))
    request.state.tenant = ctx.get("tenant")

    return await call_next(request)

# -- Uptime/health probes for orchestration/infra --
@app.get("/health", response_class=JSONResponse)
async def health(request: Request):
    try:
        # Get comprehensive health status from health monitor
        from ai_karen_engine.core.health_monitor import get_health_monitor
        health_monitor = get_health_monitor()
        health_summary = health_monitor.get_health_summary()
        
        return {
            "status": health_summary["overall_status"],
            "version": app.version,
            "env": os.getenv("KARI_ENV", "local"),
            "trace_id": getattr(request.state, "trace_id", None),
            "services": {
                "total": health_summary["total_services"],
                "healthy": health_summary["healthy_services"],
                "degraded": health_summary["degraded_services"],
                "unhealthy": health_summary["unhealthy_services"]
            },
            "last_check": health_summary["last_check"],
            "average_uptime": health_summary["average_uptime"]
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unknown",
            "version": app.version,
            "env": os.getenv("KARI_ENV", "local"),
            "trace_id": getattr(request.state, "trace_id", None),
            "error": str(e)
        }

@app.get("/livez", response_class=PlainTextResponse)
async def livez():
    return "ok"

@app.get("/readyz", response_class=PlainTextResponse)
async def readyz():
    return "ready"

# -- Service Discovery and Health Monitoring Endpoints --
@app.get("/api/services", response_class=JSONResponse)
async def list_services():
    """List all registered services and their status."""
    try:
        from ai_karen_engine.core.service_registry import get_service_registry
        registry = get_service_registry()
        return {
            "services": registry.list_services(),
            "metrics": registry.get_metrics()
        }
    except Exception as e:
        logger.error(f"Service discovery error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Service discovery failed", "detail": str(e)}
        )

@app.get("/api/services/{service_name}/health", response_class=JSONResponse)
async def get_service_health(service_name: str):
    """Get detailed health information for a specific service."""
    try:
        from ai_karen_engine.core.health_monitor import get_health_monitor
        health_monitor = get_health_monitor()
        service_health = health_monitor.get_service_health(service_name)
        
        if not service_health:
            return JSONResponse(
                status_code=404,
                content={"error": "Service not found", "service": service_name}
            )
        
        return {
            "service_name": service_health.service_name,
            "status": service_health.status.value,
            "last_check": service_health.last_check.isoformat(),
            "uptime": service_health.uptime,
            "error_count": service_health.error_count,
            "success_count": service_health.success_count,
            "recent_checks": [
                {
                    "status": check.status.value,
                    "message": check.message,
                    "timestamp": check.timestamp.isoformat(),
                    "response_time": check.response_time,
                    "error": check.error
                }
                for check in service_health.checks[-10:]  # Last 10 checks
            ]
        }
    except Exception as e:
        logger.error(f"Service health check error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Health check failed", "detail": str(e)}
        )

@app.get("/api/health/summary", response_class=JSONResponse)
async def get_health_summary():
    """Get comprehensive health summary for all services."""
    try:
        from ai_karen_engine.core.health_monitor import get_health_monitor
        health_monitor = get_health_monitor()
        return health_monitor.get_health_summary()
    except Exception as e:
        logger.error(f"Health summary error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Health summary failed", "detail": str(e)}
        )

@app.post("/api/health/check", response_class=JSONResponse)
async def trigger_health_check():
    """Trigger immediate health check for all services."""
    try:
        from ai_karen_engine.core.health_monitor import get_health_monitor
        health_monitor = get_health_monitor()
        results = await health_monitor.check_all_services()
        
        return {
            "message": "Health check completed",
            "results": {
                name: {
                    "status": result.status.value,
                    "message": result.message,
                    "response_time": result.response_time,
                    "timestamp": result.timestamp.isoformat()
                }
                for name, result in results.items()
            }
        }
    except Exception as e:
        logger.error(f"Health check trigger error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Health check failed", "detail": str(e)}
        )

@app.get("/api/config", response_class=JSONResponse)
async def get_configuration():
    """Get current system configuration (sanitized)."""
    try:
        from ai_karen_engine.core.config_manager import get_config
        config = get_config()
        
        # Return sanitized configuration (remove sensitive data)
        return {
            "environment": config.environment.value,
            "debug": config.debug,
            "database": {
                "host": config.database.host,
                "port": config.database.port,
                "database": config.database.database,
                "pool_size": config.database.pool_size
            },
            "redis": {
                "host": config.redis.host,
                "port": config.redis.port,
                "database": config.redis.database
            },
            "vector_db": {
                "provider": config.vector_db.provider,
                "host": config.vector_db.host,
                "port": config.vector_db.port
            },
            "llm": {
                "provider": config.llm.provider,
                "model": config.llm.model,
                "temperature": config.llm.temperature,
                "max_tokens": config.llm.max_tokens
            },
            "web_ui": {
                "enable_web_ui_features": config.web_ui.enable_web_ui_features,
                "session_timeout": config.web_ui.session_timeout,
                "ui_sources": config.web_ui.ui_sources
            },
            "monitoring": {
                "enable_metrics": config.monitoring.enable_metrics,
                "enable_logging": config.monitoring.enable_logging,
                "log_level": config.monitoring.log_level
            }
        }
    except Exception as e:
        logger.error(f"Configuration retrieval error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Configuration retrieval failed", "detail": str(e)}
        )

# -- Human/Index --
@app.get("/", response_class=JSONResponse)
async def index():
    return {
        "service": "Kari AI",
        "message": "Welcome to the Kari AI Modular API.",
        "docs": "/docs",
        "metrics": "/metrics",
        "health": "/health",
        "version": app.version,
    }

# -- Admin UI (optional, mount if present) --
admin_ui_dir = os.getenv("KARI_ADMIN_UI", None)
if admin_ui_dir and os.path.isdir(admin_ui_dir):
    from fastapi.staticfiles import StaticFiles
    app.mount("/admin", StaticFiles(directory=admin_ui_dir), name="admin-ui")
    logger.info("Admin UI mounted at /admin")

# -- Exception handler: log+trace --
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, 'trace_id', str(uuid.uuid4()))
    logger.error(f"[{trace_id}] Unhandled Exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "trace_id": trace_id,
            "detail": str(exc),
        },
    )

# --- ASGI requires `app` at module level for discovery
__all__ = ["app"]

