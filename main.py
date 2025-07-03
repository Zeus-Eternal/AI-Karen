from typing import Any, Dict, List
from pathlib import Path
import sys
import os
from ai_karen_engine.core.cortex.dispatch import CortexDispatcher
from ai_karen_engine.core.embedding_manager import _METRICS as METRICS
from ai_karen_engine.core.soft_reasoning_engine import SoftReasoningEngine

if (Path(__file__).resolve().parent / "fastapi").is_dir():
    sys.stderr.write(
        "Error: A local 'fastapi' directory exists. It shadows the installed FastAPI package.\n"
    )
    sys.exit(1)
from fastapi import FastAPI, HTTPException, Request

try:
    from fastapi.responses import JSONResponse, Response
except Exception:  # fastapi_stub compatibility
    from fastapi.responses import JSONResponse
    from ai_karen_engine.fastapi_stub import Response
try:
    from prometheus_client import (
        Counter,
        Histogram,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
except Exception:  # pragma: no cover - fallback when package is missing

    class _DummyMetric:
        def __init__(self, *args, **kwargs):
            pass

        def inc(self, amount: int = 1) -> None:
            pass

        def time(self):
            class _Ctx:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    pass

            return _Ctx()

    def generate_latest() -> bytes:
        return b""

    CONTENT_TYPE_LATEST = "text/plain"
    Counter = Histogram = _DummyMetric
from ai_karen_engine.self_refactor import SelfRefactorEngine, SREScheduler
from pydantic import BaseModel
import asyncio
import logging
from ai_karen_engine.integrations.llm_registry import registry as llm_registry
from ai_karen_engine.integrations.model_discovery import sync_registry

app = FastAPI()

logger = logging.getLogger("kari")


@app.on_event("startup")
async def _refresh_registry_on_start() -> None:
    """Refresh the model registry on startup and optionally on a schedule."""
    sync_registry()
    interval = int(os.getenv("LLM_REFRESH_INTERVAL", "0"))
    if interval > 0:
        async def _scheduled():
            while True:
                await asyncio.sleep(interval)
                sync_registry()

        asyncio.create_task(_scheduled())

REQUEST_COUNT = Counter("kari_http_requests_total", "Total HTTP requests")
REQUEST_LATENCY = Histogram("kari_http_request_seconds", "Latency of HTTP requests")
LNM_ERROR_COUNT = Counter("lnm_runtime_errors_total", "Total LNM pipeline failures")


_sre_scheduler: SREScheduler | None = None


@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse({"detail": str(exc)}, status_code=500)


dispatcher = CortexDispatcher()
engine = SoftReasoningEngine()


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
    """Return all available route paths."""
    return {"routes": [route.path for route in app.routes]}


@app.get("/ping")
def ping():
    return {"status": "ok"}


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "plugins": len(dispatcher.router.intent_map),
    }


@app.get("/ready")
def ready() -> Dict[str, Any]:
    return {"ready": True}


@app.post("/chat")
async def chat(req: ChatRequest) -> ChatResponse:
    role = getattr(req, "role", "user")
    try:
        data = await dispatcher.dispatch(req.text, role=role)
    except Exception as exc:  # pragma: no cover - safety net
        import traceback

        traceback.print_exc()
        LNM_ERROR_COUNT.inc()
        return JSONResponse(status_code=500, content={"error": str(exc)})
    if data.get("error"):
        raise HTTPException(status_code=403, detail=data["error"])
    # Unknown intents return a normal response instead of 404
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
    except Exception as exc:  # pragma: no cover - safety net
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
    except Exception as exc:  # pragma: no cover - safety net
        raise HTTPException(status_code=500, detail=str(exc))
    return [SearchResult(**r) for r in results]


@app.get("/metrics")
def metrics() -> MetricsResponse:
    agg = {k: sum(v) / len(v) if v else 0 for k, v in METRICS.items()}
    return MetricsResponse(metrics=agg)


@app.get("/metrics/prometheus")
def metrics_prometheus() -> Response:
    data = generate_latest()
    try:
        return Response(data, media_type=CONTENT_TYPE_LATEST)
    except TypeError:
        resp = Response(data)
        resp.media_type = CONTENT_TYPE_LATEST
        return resp


@app.get("/plugins")
def list_plugins() -> List[str]:
    return dispatcher.router.list_intents()


@app.post("/plugins/reload")
def reload_plugins():
    dispatcher.router.reload()
    return {"status": "reloaded", "count": len(dispatcher.router.intent_map)}


@app.get("/plugins/{intent}")
def plugin_manifest(intent: str):
    plugin = dispatcher.router.get_plugin(intent)
    if not plugin:
        raise HTTPException(status_code=404, detail="not found")
    return plugin.manifest


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
    """Return SelfRefactor logs. Sanitized unless ADVANCED_MODE allows full."""
    from ai_karen_engine.self_refactor import log_utils

    logs = log_utils.load_logs(full=full)
    return {"logs": logs}


if os.getenv("ENABLE_SELF_REFACTOR"):
    _sre_scheduler = SREScheduler(SelfRefactorEngine(Path(__file__).resolve().parent))
    _sre_scheduler.start()
