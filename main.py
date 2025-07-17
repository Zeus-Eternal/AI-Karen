from typing import Any, Dict, List
from pathlib import Path
import sys
import os
import json

from ai_karen_engine.core.cortex.dispatch import dispatch
from ai_karen_engine.core.embedding_manager import _METRICS as METRICS
from ai_karen_engine.core.memory import manager as memory_manager
from ai_karen_engine.core.plugin_registry import _METRICS as PLUGIN_METRICS
from ai_karen_engine.clients.database.elastic_client import _METRICS as DOC_METRICS
from ai_karen_engine.core.soft_reasoning_engine import SoftReasoningEngine
from ai_karen_engine.core.memory.manager import init_memory
from ai_karen_engine.utils.auth import validate_session

if (Path(__file__).resolve().parent / "fastapi").is_dir():
    sys.stderr.write(
        "Error: A local 'fastapi' directory exists. It shadows the installed FastAPI package.\n"
    )
    sys.exit(1)

from fastapi import FastAPI, HTTPException, Request

try:
    from fastapi.responses import JSONResponse, Response
except Exception:
    from fastapi.responses import JSONResponse
    from ai_karen_engine.fastapi_stub import Response

try:
    from prometheus_client import (
        Counter,
        Histogram,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
except Exception:
    class _DummyMetric:
        def __init__(self, *args, **kwargs): pass
        def inc(self, amount: int = 1): pass
        def time(self):
            class _Ctx:
                def __enter__(self): return self
                def __exit__(self, exc_type, exc, tb): pass
            return _Ctx()
    def generate_latest() -> bytes: return b""
    CONTENT_TYPE_LATEST = "text/plain"
    Counter = Histogram = _DummyMetric

from ai_karen_engine.self_refactor import SelfRefactorEngine, SREScheduler
from pydantic import BaseModel
import asyncio
import logging
from ai_karen_engine.integrations.llm_registry import registry as llm_registry
from ai_karen_engine.integrations.model_discovery import sync_registry
from ai_karen_engine.integrations.llm_utils import PROM_REGISTRY
from ai_karen_engine.plugin_router import get_plugin_router
from ai_karen_engine.api_routes.auth import router as auth_router

app = FastAPI()
app.include_router(auth_router)
logger = logging.getLogger("kari")

@app.on_event("startup")
async def _refresh_registry_on_start() -> None:
    init_memory()
    _load_plugins()
    sync_registry()
    interval = int(os.getenv("LLM_REFRESH_INTERVAL", "0"))
    if interval > 0:
        async def _scheduled():
            while True:
                await asyncio.sleep(interval)
                sync_registry()
        asyncio.create_task(_scheduled())

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

_sre_scheduler: SREScheduler | None = None

@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse({"detail": str(exc)}, status_code=500)

engine = SoftReasoningEngine()

PLUGIN_DIR = Path(__file__).resolve().parent / "src" / "ai_karen_engine" / "plugins"
PLUGIN_MAP: Dict[str, Dict[str, Any]] = {}
ENABLED_PLUGINS: set[str] = set()

def _load_plugins() -> None:
    PLUGIN_MAP.clear()
    ENABLED_PLUGINS.clear()
    if not PLUGIN_DIR.is_dir():
        return
    for p in PLUGIN_DIR.iterdir():
        manifest_path = p / "plugin_manifest.json"
        if not manifest_path.exists():
            continue
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            intents = manifest.get("intent")
            if isinstance(intents, str):
                intents = [intents]
            for intent in intents or []:
                PLUGIN_MAP[intent] = manifest
                ENABLED_PLUGINS.add(intent)
        except Exception:
            continue
    get_plugin_router().reload()

if hasattr(app, "middleware"):
    @app.middleware("http")
    async def record_metrics(request: Request, call_next):
        with REQUEST_LATENCY.time():
            response = await call_next(request)
        REQUEST_COUNT.inc()
        return response
else:
    async def record_metrics(request: Request, call_next):
        return await call_next(request)

TENANT_HEADER = "X-Tenant-ID"
PUBLIC_PATHS = {"/ping", "/health", "/ready", "/metrics", "/metrics/prometheus", "/"}

if hasattr(app, "middleware"):
    @app.middleware("http")
    async def require_tenant(request: Request, call_next):
        if request.url.path not in PUBLIC_PATHS:
            tenant = request.headers.get(TENANT_HEADER)
            if not tenant:
                auth = request.headers.get("authorization")
                if auth and auth.lower().startswith("bearer "):
                    token = auth.split(None, 1)[1]
                    ctx = validate_session(token, request.headers.get("user-agent", ""), request.client.host)
                    tenant = ctx.get("tenant_id") if ctx else None
            if not tenant:
                return JSONResponse(status_code=400, content={"detail": "tenant_id required"})
            request.state.tenant_id = tenant
        return await call_next(request)
else:
    async def require_tenant(request: Request, call_next):
        return await call_next(request)

class ChatRequest(BaseModel):
    text: str
    role: str = "user"

class ChatResponse(BaseModel):
    intent: str
    confidence: float
    response: Any

class StoreRequest(BaseModel):
    text: str
    ttl_seconds: float | None = None
    tag: str | None = None

class StoreResponse(BaseModel):
    status: str
    id: int | None

class SearchRequest(BaseModel):
    text: str
    top_k: int = 3
    metadata_filter: Dict[str, Any] | None = None

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

@app.get("/")
def route_map() -> Dict[str, Any]:
    return {"routes": [route.path for route in app.routes]}

@app.get("/ping")
def ping():
    return {"status": "ok"}

@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "healthy", "plugins": sorted(ENABLED_PLUGINS)}

@app.get("/ready")
def ready() -> Dict[str, Any]:
    return {"ready": True}

@app.get("/plugins")
def list_plugins() -> List[str]:
    return sorted(ENABLED_PLUGINS)

@app.get("/plugins/{intent}")
def get_plugin(intent: str):
    manifest = PLUGIN_MAP.get(intent)
    if not manifest:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return manifest

@app.post("/plugins/{intent}/disable")
def disable_plugin(intent: str):
    ENABLED_PLUGINS.discard(intent)
    return {"status": "disabled"}

@app.post("/plugins/{intent}/enable")
def enable_plugin(intent: str):
    if intent in PLUGIN_MAP:
        ENABLED_PLUGINS.add(intent)
        return {"status": "enabled"}
    raise HTTPException(status_code=404, detail="Plugin not found")

@app.post("/plugins/reload")
def reload_plugins():
    _load_plugins()
    return {"reloaded": True}

@app.post("/chat")
async def chat(req: ChatRequest) -> ChatResponse:
    role = getattr(req, "role", "user")
    if role not in {"user", "admin"}:
        raise HTTPException(status_code=403, detail="invalid role")
    try:
        data = await dispatch(req.text, role=role)
    except Exception as exc:
        import traceback
        traceback.print_exc()
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
            engine.ingest,
            req.text,
            metadata=metadata,
            ttl_seconds=req.ttl_seconds,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    status = "stored" if rid is not None else "ignored"
    return StoreResponse(status=status, id=rid)

@app.post("/search")
async def search(req: SearchRequest) -> List[SearchResult]:
    try:
        results = await engine.aquery(
            req.text,
            top_k=getattr(req, "top_k", 3),
            metadata_filter=getattr(req, "metadata_filter", None),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return [SearchResult(**r) for r in results]

@app.get("/metrics")
def metrics() -> MetricsResponse:
    def _norm(d: Dict[str, Any]) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for k, v in d.items():
            if isinstance(v, list):
                out[k] = sum(v) / len(v) if v else 0.0
            else:
                out[k] = float(v)
        return out

    agg = {}
    agg.update(_norm(METRICS))
    agg.update(_norm(memory_manager._METRICS))
    agg.update(_norm(PLUGIN_METRICS))
    agg.update(_norm(DOC_METRICS))
    return MetricsResponse(metrics=agg)

@app.get("/metrics/prometheus")
def metrics_prometheus() -> Response:
    data = generate_latest(PROM_REGISTRY) if PROM_REGISTRY is not None else generate_latest()
    try:
        return Response(data, media_type=CONTENT_TYPE_LATEST)
    except TypeError:
        resp = Response(data)
        resp.media_type = CONTENT_TYPE_LATEST
        return resp

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
def self_refactor_logs(full: bool = False):
    from ai_karen_engine.self_refactor import log_utils
    logs = log_utils.load_logs(full=full)
    return {"logs": logs}

if os.getenv("ENABLE_SELF_REFACTOR"):
    _sre_scheduler = SREScheduler(SelfRefactorEngine(Path(__file__).resolve().parent))
    _sre_scheduler.start()
