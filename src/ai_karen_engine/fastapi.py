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

from ai_karen_engine.core.memory.manager import init_memory
from ai_karen_engine.utils.auth import validate_session
from ai_karen_engine.extensions import initialize_extension_manager, get_extension_manager
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

# -- Prometheus Metrics (optional) --
try:
    from prometheus_client import make_asgi_app
    app.mount("/metrics", make_asgi_app())
    logger.info("Prometheus metrics endpoint mounted at /metrics")
except ImportError:
    logger.info("Prometheus metrics not installed; skipping /metrics mount")

# -- CORS Config --
allowed_origins = os.getenv("KARI_CORS_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[allowed_origins] if allowed_origins != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -- GZip for payloads (auto, if available) --
try:
    app.add_middleware(GZipMiddleware, minimum_size=512)
except Exception:
    pass

# --- Plugin/Router Auto-Discovery (production-ready) ---
def auto_discover_routers(app):
    """
    Scans 'api_routes' and 'plugins' for FastAPI routers and mounts them.
    """
    import importlib
    import pkgutil

    # Internal app routes (api_routes/*.py)
    try:
        from ai_karen_engine import api_routes
        package = api_routes
        prefix = "/api"
    except ImportError:
        package = None

    if package:
        for loader, name, is_pkg in pkgutil.iter_modules(package.__path__):
            mod = importlib.import_module(f"ai_karen_engine.api_routes.{name}")
            router = getattr(mod, "router", None)
            if isinstance(router, APIRouter) and hasattr(router, "routes"):
                app.include_router(router, prefix=prefix)
                logger.info(f"Mounted router: /api/{name}")

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
    return {
        "status": "ok",
        "version": app.version,
        "env": os.getenv("KARI_ENV", "local"),
        "trace_id": getattr(request.state, "trace_id", None),
    }

@app.get("/livez", response_class=PlainTextResponse)
async def livez():
    return "ok"

@app.get("/readyz", response_class=PlainTextResponse)
async def readyz():
    return "ready"

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

