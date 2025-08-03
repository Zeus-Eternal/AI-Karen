"""
Kari FastAPI Server
- Chat, Plugin management, metrics, multi-tenant enforcement
- Prometheus instrumentation with fallback stubs
- Self-refactor scheduler
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

# --- Environment Loading ----------------------------------------------------
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # Fallback if python-dotenv is not installed

    def load_dotenv(path: str, **_kwargs):
        if not Path(path).exists():
            return False
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip() or line.strip().startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    os.environ.setdefault(k, v)
        return True


# Load variables from .envK and .env before importing the engine
if Path(".envK").exists():
    load_dotenv(".envK", override=True)
if Path(".env").exists():
    load_dotenv(".env", override=True)

# Ensure DATABASE_URL is set for database clients
if "DATABASE_URL" not in os.environ and os.getenv("POSTGRES_URL"):
    os.environ["DATABASE_URL"] = os.environ["POSTGRES_URL"]

import ai_karen_engine.utils.auth as auth_utils
from ai_karen_engine.api_routes.ai_orchestrator_routes import router as ai_router
from ai_karen_engine.api_routes.audit import router as audit_router
from ai_karen_engine.api_routes.conversation_routes import router as conversation_router
from ai_karen_engine.api_routes.events import router as events_router
from ai_karen_engine.api_routes.memory_routes import router as memory_router
from ai_karen_engine.api_routes.plugin_routes import router as plugin_router
from ai_karen_engine.api_routes.auth import router as auth_router
from ai_karen_engine.api_routes.tool_routes import router as tool_router
from ai_karen_engine.api_routes.web_api_compatibility import router as web_api_router
from ai_karen_engine.clients.database.elastic_client import _METRICS as DOC_METRICS
from ai_karen_engine.core.cortex.dispatch import dispatch
from ai_karen_engine.core.embedding_manager import _METRICS as METRICS
from ai_karen_engine.core.memory import manager as memory_manager
from ai_karen_engine.core.memory.manager import init_memory
from ai_karen_engine.core.plugin_registry import _METRICS as PLUGIN_METRICS
from ai_karen_engine.core.soft_reasoning_engine import SoftReasoningEngine
from ai_karen_engine.integrations.llm_registry import get_registry
from ai_karen_engine.integrations.llm_utils import PROM_REGISTRY
from ai_karen_engine.integrations.model_discovery import sync_registry
from ai_karen_engine.plugins.router import get_plugin_router
from ai_karen_engine.self_refactor import SelfRefactorEngine, SREScheduler

# ─── Prometheus metrics (with graceful fallback) ─────────────────────────────

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Histogram,
        generate_latest,
    )
except ImportError:

    class _DummyMetric:
        def __init__(self, *args, **kwargs):
            pass

        def inc(self, amount: int = 1):
            pass

        def time(self):
            class _Ctx:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    pass

            return _Ctx()

    Counter = Histogram = _DummyMetric

    def generate_latest() -> bytes:
        return b""

    CONTENT_TYPE_LATEST = "text/plain"


# Initialize Prometheus metrics with collision handling
def _init_metrics():
    """Initialize Prometheus metrics with duplicate handling"""
    global REQUEST_COUNT, REQUEST_LATENCY, LNM_ERROR_COUNT

    try:
        REQUEST_COUNT = Counter(
            "kari_http_requests_total",
            "Total HTTP requests",
            registry=PROM_REGISTRY,
        )
        REQUEST_LATENCY = Histogram(
            "kari_http_request_seconds",
            "Latency of HTTP requests",
            registry=PROM_REGISTRY,
        )
        LNM_ERROR_COUNT = Counter(
            "lnm_runtime_errors_total",
            "Total LNM pipeline failures",
            registry=PROM_REGISTRY,
        )
        print(f"[DEBUG] Metrics initialized successfully: REQUEST_COUNT={REQUEST_COUNT}")
    except ValueError as e:
        if "Duplicated timeseries" in str(e):
            print(f"[DEBUG] Handling duplicate metrics: {e}")
            # Initialize to None first
            REQUEST_COUNT = None
            REQUEST_LATENCY = None
            LNM_ERROR_COUNT = None
            
            # Metrics already registered, get existing ones
            for collector in PROM_REGISTRY._collector_to_names:
                if hasattr(collector, "_name"):
                    if collector._name == "kari_http_requests_total":
                        REQUEST_COUNT = collector
                    elif collector._name == "kari_http_request_seconds":
                        REQUEST_LATENCY = collector
                    elif collector._name == "lnm_runtime_errors_total":
                        LNM_ERROR_COUNT = collector
            
            # Fallback to dummy metrics if not found
            if REQUEST_COUNT is None:
                class _LocalDummyMetric:
                    def inc(self, amount=1):
                        pass
                    def time(self):
                        class _Ctx:
                            def __enter__(self):
                                return self
                            def __exit__(self, exc_type, exc, tb):
                                pass
                        return _Ctx()
                REQUEST_COUNT = _LocalDummyMetric()
            if REQUEST_LATENCY is None:
                REQUEST_LATENCY = _LocalDummyMetric()
            if LNM_ERROR_COUNT is None:
                LNM_ERROR_COUNT = _LocalDummyMetric()
                
            print(f"[DEBUG] Reused existing metrics: REQUEST_COUNT={REQUEST_COUNT}")
        else:
            print(f"[DEBUG] Unexpected ValueError: {e}")
            raise
    except Exception as e:
        print(f"[DEBUG] Error initializing metrics: {e}")
        # Fallback to dummy metrics - create instances without arguments
        class _LocalDummyMetric:
            def inc(self, amount=1):
                pass
            def time(self):
                class _Ctx:
                    def __enter__(self):
                        return self
                    def __exit__(self, exc_type, exc, tb):
                        pass
                return _Ctx()
        
        REQUEST_COUNT = _LocalDummyMetric()
        REQUEST_LATENCY = _LocalDummyMetric()
        LNM_ERROR_COUNT = _LocalDummyMetric()


# Initialize metrics
_init_metrics()

# Logger setup
logger = logging.getLogger("kari")


# ─── FastAPI Setup ───────────────────────────────────────────────────────────

# guard against local “fastapi” folder shadowing the package
if (Path(__file__).resolve().parent / "fastapi").is_dir():
    sys.stderr.write(
        "Error: A local 'fastapi' directory exists. It shadows the installed FastAPI package.\n"
    )
    sys.exit(1)

app = FastAPI()

def _validate_cors_configuration():
    """Validate CORS configuration and log potential issues."""
    environment = os.getenv("KARI_ENV", "local").lower()
    allowed_origins = os.getenv("KARI_CORS_ORIGINS", "")
    
    validation_issues = []
    
    # Check for production security
    if environment in ["production", "prod"]:
        if not allowed_origins or allowed_origins == "*":
            validation_issues.append(
                "Production environment should have explicit CORS origins configured, not '*'"
            )
        elif "*" in allowed_origins:
            validation_issues.append(
                "Production environment should not include '*' in CORS origins"
            )
    
    # Check for common misconfigurations
    if allowed_origins:
        origins = [origin.strip() for origin in allowed_origins.split(",")]
        for origin in origins:
            if origin.endswith("/"):
                validation_issues.append(f"CORS origin should not end with '/': {origin}")
            if not origin.startswith(("http://", "https://")) and origin != "*":
                validation_issues.append(f"CORS origin should include protocol: {origin}")
    
    # Log validation results
    if validation_issues:
        logger.warning("CORS configuration validation issues found:")
        for issue in validation_issues:
            logger.warning(f"  - {issue}")
    else:
        logger.info("CORS configuration validation passed")
    
    return len(validation_issues) == 0


def _get_cors_origins():
    """Get CORS origins based on environment configuration."""
    # Get base origins from environment
    allowed_origins = os.getenv("KARI_CORS_ORIGINS", "")
    origins_list = []
    
    if allowed_origins:
        origins_list = [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]
    
    # Add environment-specific origins
    environment = os.getenv("KARI_ENV", "local").lower()
    
    if environment in ["local", "development", "dev"]:
        # Development origins - use environment variables for external hosts
        external_host = os.getenv("KAREN_EXTERNAL_HOST", "")
        web_ui_port = os.getenv("KAREN_WEB_UI_PORT", "9002")
        backend_port = os.getenv("PORT", "8000")
        
        dev_origins = [
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            f"http://localhost:{web_ui_port}",  # Web UI default port
            f"http://127.0.0.1:{web_ui_port}",  # Web UI default port
        ]
        
        # Add external host origins if configured
        if external_host:
            dev_origins.extend([
                f"http://{external_host}:{web_ui_port}",
                f"http://{external_host}:{backend_port}",
            ])
        
        # Add development origins to the list
        for origin in dev_origins:
            if origin not in origins_list:
                origins_list.append(origin)
    
    # If no origins configured, allow all for development, restrict for production
    if not origins_list:
        if environment in ["local", "development", "dev"]:
            return ["*"]
        else:
            # Production should have explicit origins configured
            logger.warning("No CORS origins configured for production environment")
            return []
    
    return origins_list

origins_list = _get_cors_origins()


# ─── Middleware: Metrics & Multi-Tenant ─────────────────────────────────────
PUBLIC_PATHS = {
    "/",
    "/ping",
    "/health",
    "/ready",
    "/metrics",
    "/metrics/prometheus",
    "/cors/config",  # CORS debugging endpoint
    "/api/ai/generate-starter",
    "/api/chat/process",
    "/api/memory/query",
    "/api/memory/store",
    "/api/plugins",
    "/api/plugins/execute",
    "/api/analytics/system",
    "/api/analytics/usage",
    "/api/health",
    # Conversation endpoints - must be public for web UI integration
    "/api/conversations/create",
    "/api/conversations",
    # Authentication endpoints - must be public for login to work
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/me",
    "/api/auth/logout",
    "/api/auth/request_password_reset",
    "/api/auth/reset_password",
    "/api/auth/setup_2fa",
    "/api/auth/confirm_2fa",
}


@app.middleware("http")
async def record_metrics(request: Request, call_next):
    with REQUEST_LATENCY.time():
        response = await call_next(request)
    REQUEST_COUNT.inc()
    return response


TENANT_HEADER = "X-Tenant-ID"


@app.middleware("http")
async def require_tenant(request: Request, call_next):
    # Check if path is in public paths or matches conversation patterns
    is_public = (
        request.url.path in PUBLIC_PATHS or
        request.url.path.startswith("/api/conversations/")
    )
    
    if not is_public:
        tenant = request.headers.get(TENANT_HEADER)
        if not tenant:
            auth = request.headers.get("authorization", "")
            if auth.lower().startswith("bearer "):
                token = auth.split(maxsplit=1)[1]
                ctx = auth_utils.validate_session(
                    token,
                    request.headers.get("user-agent", ""),
                    request.client.host,
                )
                tenant = ctx.get("tenant_id") if ctx else None
        if not tenant:
            return JSONResponse(
                status_code=400, content={"detail": "tenant_id required"}
            )
        request.state.tenant_id = tenant
    return await call_next(request)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log requests and response details with trace ID."""
    trace_id = str(uuid.uuid4())
    start = datetime.utcnow()
    logger.info(
        f"[{trace_id}] {request.method} {request.url.path} from {request.client.host}"
    )
    response = await call_next(request)
    duration = (datetime.utcnow() - start).total_seconds() * 1000
    logger.info(
        f"[{trace_id}] {request.method} {request.url.path} status={response.status_code} time={duration:.2f}ms"
    )
    response.headers["X-Kari-Trace-Id"] = trace_id
    response.headers["X-Response-Time-Ms"] = str(int(duration))
    return response


@app.middleware("http")
async def cors_debugging_middleware(request: Request, call_next):
    """Log CORS preflight requests and potential CORS issues."""
    
    # Log preflight requests
    if request.method == "OPTIONS":
        origin = request.headers.get("origin", "unknown")
        requested_method = request.headers.get("access-control-request-method", "unknown")
        requested_headers = request.headers.get("access-control-request-headers", "none")
        
        logger.info(
            f"CORS preflight request from origin: {origin}, "
            f"method: {requested_method}, headers: {requested_headers}"
        )
        
        # Check if origin is allowed
        if origin != "unknown" and origins_list != ["*"]:
            if origin not in origins_list:
                logger.warning(
                    f"CORS preflight request from unauthorized origin: {origin}. "
                    f"Allowed origins: {origins_list}"
                )
    
    response = await call_next(request)
    
    # Log CORS-related response headers for debugging
    if request.method == "OPTIONS" or request.headers.get("origin"):
        cors_headers = {
            k: v for k, v in response.headers.items() 
            if k.lower().startswith("access-control-")
        }
        if cors_headers:
            logger.debug(f"CORS response headers: {cors_headers}")
    
    return response


@app.middleware("http")
async def web_ui_api_logging(request: Request, call_next):
    """Enhanced logging middleware for web UI API endpoints."""

    is_web_ui_api = (
        request.url.path.startswith("/api/chat/")
        or request.url.path.startswith("/api/memory/")
        or request.url.path.startswith("/api/plugins/")
        or request.url.path.startswith("/api/analytics/")
        or request.url.path.startswith("/api/health")
    )

    if not is_web_ui_api:
        return await call_next(request)

    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    start_time = datetime.utcnow()

    user_agent = request.headers.get("user-agent", "unknown")
    content_type = request.headers.get("content-type", "unknown")

    logger.info(
        f"[{trace_id}] WEB_UI_API {request.method} {request.url.path} "
        f"from {request.client.host} UA: {user_agent[:50]} CT: {content_type}"
    )

    if (
        request.method in ["POST", "PUT", "PATCH"]
        and os.getenv("KARI_LOG_REQUEST_BODY", "false").lower() == "true"
    ):
        try:
            body = await request.body()
            if len(body) < 1000:
                logger.debug(
                    f"[{trace_id}] Request body: {body.decode('utf-8', errors='ignore')}"
                )
            else:
                logger.debug(
                    f"[{trace_id}] Request body size: {len(body)} bytes (too large to log)"
                )
        except Exception as e:
            logger.debug(f"[{trace_id}] Could not read request body: {e}")

    try:
        response = await call_next(request)
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000

        logger.info(
            f"[{trace_id}] WEB_UI_API {request.method} {request.url.path} "
            f"status={response.status_code} time={response_time_ms:.2f}ms"
        )

        response.headers["X-Web-UI-Compatible"] = "true"
        response.headers["X-Response-Time-Ms"] = str(int(response_time_ms))

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
            exc_info=True,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred while processing your request",
                "type": "INTERNAL_SERVER_ERROR",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat(),
                "details": (
                    {"error_type": type(e).__name__}
                    if os.getenv("KARI_DEBUG", "false").lower() == "true"
                    else None
                ),
            },
        )


# Configure CORS after all custom middleware so that preflight requests are
# processed before tenant or authentication checks.
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
    max_age=86400,
)

logger.info(f"CORS configured for origins: {origins_list}")

app.include_router(auth_router)
app.include_router(events_router)
app.include_router(web_api_router)  # Web API compatibility router first for precedence
app.include_router(ai_router)
app.include_router(memory_router)
app.include_router(conversation_router)
app.include_router(plugin_router)
app.include_router(tool_router)
app.include_router(audit_router)

# ─── Startup: memory, plugins, LLM registry refresh ───────────────────────────


@app.on_event("startup")
async def on_startup() -> None:
    # Validate CORS configuration on startup
    _validate_cors_configuration()
    
    # Initialize legacy components
    init_memory()
    _load_plugins()
    sync_registry()

    # Initialize AI Karen integration services
    try:
        from ai_karen_engine.core.config_manager import get_config_manager
        from ai_karen_engine.core.health_monitor import (
            get_health_monitor,
            setup_default_health_checks,
        )
        from ai_karen_engine.core.service_registry import initialize_services

        # Load configuration
        config_manager = get_config_manager()
        config = config_manager.load_config()
        logger.info(
            f"AI Karen configuration loaded for environment: {config.environment}"
        )

        # Initialize services
        await initialize_services()
        logger.info("AI Karen integration services initialized")

        # Set up health monitoring
        await setup_default_health_checks()
        health_monitor = get_health_monitor()
        health_monitor.start_monitoring()
        logger.info("Health monitoring started")
        logger.info("Greetings, the logs are ready for review")

    except Exception as e:
        logger.error(f"Failed to initialize AI Karen integration: {e}")
        # Continue with legacy startup even if integration fails

    # Legacy LLM refresh interval
    interval = int(os.getenv("LLM_REFRESH_INTERVAL", "0"))
    if interval > 0:

        async def _periodic_refresh():
            while True:
                await asyncio.sleep(interval)
                sync_registry()

        asyncio.create_task(_periodic_refresh())


# ─── Plugin Discovery ────────────────────────────────────────────────────────

PLUGIN_DIR = Path(__file__).resolve().parent / "src" / "ai_karen_engine" / "plugins"
PLUGIN_MAP: Dict[str, Dict[str, Any]] = {}
ENABLED_PLUGINS: set[str] = set()


def _load_plugins() -> None:
    PLUGIN_MAP.clear()
    ENABLED_PLUGINS.clear()
    if not PLUGIN_DIR.is_dir():
        return
    for plugin_path in PLUGIN_DIR.iterdir():
        manifest_file = plugin_path / "plugin_manifest.json"
        if not manifest_file.exists():
            continue
        try:
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            intents = manifest.get("intent", [])
            if isinstance(intents, str):
                intents = [intents]
            for intent in intents:
                PLUGIN_MAP[intent] = manifest
                ENABLED_PLUGINS.add(intent)
        except Exception:
            logger.warning(
                f"Failed loading plugin manifest: {plugin_path}", exc_info=True
            )
    get_plugin_router().reload()


# ─── Exception Handler ───────────────────────────────────────────────────────


@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse({"detail": str(exc)}, status_code=500)


# ─── Shared Engine ──────────────────────────────────────────────────────────

engine = SoftReasoningEngine()
_sre_scheduler: Optional[SREScheduler] = None

# ─── Pydantic Models ─────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    text: str


class ChatResponse(BaseModel):
    intent: str
    confidence: float
    response: Any


class StoreRequest(BaseModel):
    text: str
    ttl_seconds: Optional[float] = None
    tag: Optional[str] = None


class StoreResponse(BaseModel):
    status: str
    id: Optional[int] = None


class SearchRequest(BaseModel):
    text: str
    top_k: int = 3
    metadata_filter: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    id: int
    score: float
    payload: Dict[str, Any]


class MetricsResponse(BaseModel):
    metrics: Dict[str, float]


class ModelListResponse(BaseModel):
    models: List[str]
    active: str


class ModelSelectRequest(BaseModel):
    model: str


# ─── Routes ──────────────────────────────────────────────────────────────────


@app.get("/")
def route_map() -> Dict[str, Any]:
    return {"routes": [route.path for route in app.routes]}


@app.get("/ping")
def ping() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "healthy", "plugins": sorted(ENABLED_PLUGINS)}


@app.get("/ready")
def ready() -> Dict[str, bool]:
    return {"ready": True}


@app.get("/plugins")
def list_plugins() -> List[str]:
    return sorted(ENABLED_PLUGINS)


@app.get("/plugins/{intent}")
def get_plugin(intent: str) -> Dict[str, Any]:
    manifest = PLUGIN_MAP.get(intent)
    if not manifest:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return manifest


@app.post("/plugins/{intent}/disable")
def disable_plugin(intent: str) -> Dict[str, str]:
    ENABLED_PLUGINS.discard(intent)
    return {"status": "disabled"}


@app.post("/plugins/{intent}/enable")
def enable_plugin(intent: str) -> Dict[str, str]:
    if intent in PLUGIN_MAP:
        ENABLED_PLUGINS.add(intent)
        return {"status": "enabled"}
    raise HTTPException(status_code=404, detail="Plugin not found")


@app.post("/plugins/reload")
def reload_plugins() -> Dict[str, bool]:
    _load_plugins()
    return {"reloaded": True}


@app.post("/chat")
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = auth.split(maxsplit=1)[1]
    ctx = auth_utils.validate_session(
        token,
        request.headers.get("user-agent", ""),
        request.client.host,
    )
    if not ctx:
        raise HTTPException(status_code=401, detail="Invalid token")
    role = "admin" if "admin" in ctx.get("roles", []) else "user"
    user_ctx = {
        "user_id": ctx["sub"],
        "roles": ctx.get("roles", []),
        "tenant_id": ctx.get("tenant_id"),
    }
    try:
        data = await dispatch(user_ctx, req.text, role=role)
    except Exception as exc:
        logger.exception("dispatch error")
        LNM_ERROR_COUNT.inc()
        return JSONResponse(status_code=500, content={"error": str(exc)})
    if data.get("error"):
        raise HTTPException(status_code=403, detail=data["error"])
    return ChatResponse(**data)


@app.post("/store")
async def store(req: StoreRequest) -> StoreResponse:
    metadata = {"tag": req.tag} if req.tag else None
    try:
        rid = await asyncio.to_thread(
            engine.ingest, req.text, metadata=metadata, ttl_seconds=req.ttl_seconds
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    status = "stored" if rid is not None else "ignored"
    return StoreResponse(status=status, id=rid)


@app.post("/search")
async def search(req: SearchRequest) -> List[SearchResult]:
    try:
        results = await engine.aquery(
            req.text, top_k=req.top_k, metadata_filter=req.metadata_filter
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return [SearchResult(**r) for r in results]


@app.get("/metrics")
def metrics() -> MetricsResponse:
    def _norm(d):
        return {
            k: (sum(v) / len(v) if isinstance(v, list) else float(v))
            for k, v in d.items()
        }

    agg = {}
    agg.update(_norm(METRICS))
    agg.update(_norm(memory_manager._METRICS))
    agg.update(_norm(PLUGIN_METRICS))
    agg.update(_norm(DOC_METRICS))
    return MetricsResponse(metrics=agg)


@app.get("/metrics/prometheus")
def metrics_prometheus() -> Response:
    data = generate_latest(PROM_REGISTRY) if PROM_REGISTRY else generate_latest()
    try:
        return Response(data, media_type=CONTENT_TYPE_LATEST)
    except TypeError:
        r = Response(data)
        r.media_type = CONTENT_TYPE_LATEST
        return r


@app.get("/models")
def list_models() -> ModelListResponse:
    llm_registry = get_registry()
    models = llm_registry.list_providers()
    active_provider = llm_registry.auto_select_provider() or (
        models[0] if models else "none"
    )
    return ModelListResponse(models=models, active=active_provider)


@app.post("/models/select")
def select_model(req: ModelSelectRequest) -> ModelListResponse:
    llm_registry = get_registry()
    try:
        # For now, just validate the model exists
        if req.model not in llm_registry.list_providers():
            raise KeyError(f"Model {req.model} not found")
        # In a full implementation, you'd set the active model here
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    models = llm_registry.list_providers()
    return ModelListResponse(models=models, active=req.model)


@app.get("/self_refactor/logs")
def self_refactor_logs(full: bool = False) -> Dict[str, List[str]]:
    from ai_karen_engine.self_refactor import log_utils

    return {"logs": log_utils.load_logs(full=full)}


@app.get("/cors/config")
def cors_config() -> Dict[str, Any]:
    """Get current CORS configuration for debugging."""
    environment = os.getenv("KARI_ENV", "local").lower()
    allowed_origins_env = os.getenv("KARI_CORS_ORIGINS", "")
    external_host = os.getenv("KAREN_EXTERNAL_HOST", "")
    web_ui_port = os.getenv("KAREN_WEB_UI_PORT", "9002")
    backend_port = os.getenv("PORT", "8000")
    
    return {
        "environment": environment,
        "configured_origins": allowed_origins_env,
        "active_origins": origins_list,
        "external_host": external_host,
        "web_ui_port": web_ui_port,
        "backend_port": backend_port,
        "validation_passed": _validate_cors_configuration(),
        "cors_middleware_config": {
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "max_age": 86400,
        }
    }


# ─── Optional Self-Refactor Scheduler ─────────────────────────────────────────

if os.getenv("ENABLE_SELF_REFACTOR"):
    _sre_scheduler = SREScheduler(SelfRefactorEngine(Path(__file__).parent))
    _sre_scheduler.start()

# ─── Server Startup ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    # Server configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")

    print(f"🚀 Starting AI Karen Backend Server...")
    print(f"📍 Server will be available at:")
    print(f"   - http://localhost:{port}")
    print(f"   - http://127.0.0.1:{port}")
    print(f"   - http://{host}:{port}")
    print(f"🌐 CORS configured for Web UI on port 9002")
    print(f"⏹️  Press Ctrl+C to stop the server")
    print("-" * 60)

    try:
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True,
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)
