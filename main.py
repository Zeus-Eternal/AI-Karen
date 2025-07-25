"""
Kari FastAPI Server
- Chat, Plugin management, metrics, multi-tenant enforcement
- Prometheus instrumentation with fallback stubs
- Self-refactor scheduler
"""

import os
import sys
import json
import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ai_karen_engine.core.cortex.dispatch import dispatch
from ai_karen_engine.core.embedding_manager import _METRICS as METRICS
from ai_karen_engine.core.memory import manager as memory_manager
from ai_karen_engine.core.plugin_registry import _METRICS as PLUGIN_METRICS
from ai_karen_engine.clients.database.elastic_client import _METRICS as DOC_METRICS
from ai_karen_engine.core.soft_reasoning_engine import SoftReasoningEngine
from ai_karen_engine.core.memory.manager import init_memory
import ai_karen_engine.utils.auth as auth_utils
from ai_karen_engine.self_refactor import SelfRefactorEngine, SREScheduler
from ai_karen_engine.integrations.llm_registry import registry as llm_registry
from ai_karen_engine.integrations.model_discovery import sync_registry
from ai_karen_engine.integrations.llm_utils import PROM_REGISTRY
from ai_karen_engine.plugins.router import get_plugin_router
from ai_karen_engine.api_routes.auth import router as auth_router
from ai_karen_engine.api_routes.events import router as events_router
from ai_karen_engine.api_routes.ai_orchestrator_routes import router as ai_router
from ai_karen_engine.api_routes.memory_routes import router as memory_router
from ai_karen_engine.api_routes.conversation_routes import router as conversation_router
from ai_karen_engine.api_routes.plugin_routes import router as plugin_router
from ai_karen_engine.api_routes.tool_routes import router as tool_router
from ai_karen_engine.api_routes.web_api_compatibility import router as web_api_router

# ─── Prometheus metrics (with graceful fallback) ─────────────────────────────

try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
except ImportError:
    class _DummyMetric:
        def __init__(self, *args, **kwargs): pass
        def inc(self, amount: int = 1): pass
        def time(self):
            class _Ctx:
                def __enter__(self): return self
                def __exit__(self, exc_type, exc, tb): pass
            return _Ctx()
    Counter = Histogram = _DummyMetric
    def generate_latest() -> bytes: return b""
    CONTENT_TYPE_LATEST = "text/plain"

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

allowed_origins = os.getenv("KARI_CORS_ORIGINS", "*")
origins_list = (
    [origin.strip() for origin in allowed_origins.split(",")] if allowed_origins != "*" else ["*"]
)
if os.getenv("KARI_ENV", "local").lower() in ["local", "development", "dev"]:
    dev_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:9002",  # Web UI default port
        "http://127.0.0.1:9002",  # Web UI default port
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
    max_age=86400,
)

logger.info(f"CORS configured for origins: {origins_list}")

# ─── Middleware: Metrics & Multi-Tenant ─────────────────────────────────────
PUBLIC_PATHS = {
    "/",
    "/ping",
    "/health",
    "/ready",
    "/metrics",
    "/metrics/prometheus",
    "/api/ai/generate-starter",
    "/api/chat/process",
    "/api/memory/query",
    "/api/memory/store",
    "/api/plugins",
    "/api/plugins/execute",
    "/api/analytics/system",
    "/api/analytics/usage",
    "/api/health",
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
    if request.url.path not in PUBLIC_PATHS:
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
            return JSONResponse(status_code=400, content={"detail": "tenant_id required"})
        request.state.tenant_id = tenant
    return await call_next(request)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log requests and response details with trace ID."""
    trace_id = str(uuid.uuid4())
    start = datetime.utcnow()
    logger.info(f"[{trace_id}] {request.method} {request.url.path} from {request.client.host}")
    response = await call_next(request)
    duration = (datetime.utcnow() - start).total_seconds() * 1000
    logger.info(
        f"[{trace_id}] {request.method} {request.url.path} status={response.status_code} time={duration:.2f}ms"
    )
    response.headers["X-Kari-Trace-Id"] = trace_id
    response.headers["X-Response-Time-Ms"] = str(int(duration))
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

    if request.method in ["POST", "PUT", "PATCH"] and os.getenv("KARI_LOG_REQUEST_BODY", "false").lower() == "true":
        try:
            body = await request.body()
            if len(body) < 1000:
                logger.debug(f"[{trace_id}] Request body: {body.decode('utf-8', errors='ignore')}")
            else:
                logger.debug(f"[{trace_id}] Request body size: {len(body)} bytes (too large to log)")
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
                "details": {"error_type": type(e).__name__} if os.getenv("KARI_DEBUG", "false").lower() == "true" else None,
            },
        )

app.include_router(auth_router)
app.include_router(events_router)
app.include_router(web_api_router)  # Web API compatibility router first for precedence
app.include_router(ai_router)
app.include_router(memory_router)
app.include_router(conversation_router)
app.include_router(plugin_router)
app.include_router(tool_router)

# ─── Startup: memory, plugins, LLM registry refresh ───────────────────────────

@app.on_event("startup")
async def on_startup() -> None:
    # Initialize legacy components
    init_memory()
    _load_plugins()
    sync_registry()
    
    # Initialize AI Karen integration services
    try:
        from ai_karen_engine.core.config_manager import get_config_manager
        from ai_karen_engine.core.service_registry import initialize_services
        from ai_karen_engine.core.health_monitor import setup_default_health_checks, get_health_monitor
        
        # Load configuration
        config_manager = get_config_manager()
        config = config_manager.load_config()
        logger.info(f"AI Karen configuration loaded for environment: {config.environment}")
        
        # Initialize services
        await initialize_services()
        logger.info("AI Karen integration services initialized")
        
        # Set up health monitoring
        await setup_default_health_checks()
        health_monitor = get_health_monitor()
        health_monitor.start_monitoring()
        logger.info("Health monitoring started")
        
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
            logger.warning(f"Failed loading plugin manifest: {plugin_path}", exc_info=True)
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
    user_ctx = {"user_id": ctx["sub"], "roles": ctx.get("roles", []), "tenant_id": ctx.get("tenant_id")}
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
        rid = await asyncio.to_thread(engine.ingest, req.text, metadata=metadata, ttl_seconds=req.ttl_seconds)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    status = "stored" if rid is not None else "ignored"
    return StoreResponse(status=status, id=rid)

@app.post("/search")
async def search(req: SearchRequest) -> List[SearchResult]:
    try:
        results = await engine.aquery(req.text, top_k=req.top_k, metadata_filter=req.metadata_filter)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return [SearchResult(**r) for r in results]

@app.get("/metrics")
def metrics() -> MetricsResponse:
    def _norm(d):
        return {k: (sum(v)/len(v) if isinstance(v, list) else float(v)) for k, v in d.items()}
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
    models = list(llm_registry.list_models())
    return ModelListResponse(models=models, active=llm_registry.active)

@app.post("/models/select")
def select_model(req: ModelSelectRequest) -> ModelListResponse:
    try:
        llm_registry.set_active(req.model)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    models = list(llm_registry.list_models())
    return ModelListResponse(models=models, active=llm_registry.active)

@app.get("/self_refactor/logs")
def self_refactor_logs(full: bool = False) -> Dict[str, List[str]]:
    from ai_karen_engine.self_refactor import log_utils
    return {"logs": log_utils.load_logs(full=full)}

# ─── Optional Self-Refactor Scheduler ─────────────────────────────────────────

if os.getenv("ENABLE_SELF_REFACTOR"):
    _sre_scheduler = SREScheduler(SelfRefactorEngine(Path(__file__).parent))
    _sre_scheduler.start()
