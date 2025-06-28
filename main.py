from typing import Any, Dict, List
from pathlib import Path
import sys

from core.cortex.dispatch import CortexDispatcher
from core.embedding_manager import _METRICS as METRICS
from core.soft_reasoning_engine import SoftReasoningEngine
if (Path(__file__).resolve().parent / "fastapi").is_dir():
    sys.stderr.write(
        "Error: A local 'fastapi' directory exists. It shadows the installed FastAPI package.\n"
    )
    sys.exit(1)
    
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import logging
from src.integrations.llm_registry import registry as llm_registry

app = FastAPI()

logger = logging.getLogger("kari")


@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse({"detail": str(exc)}, status_code=500)

dispatcher = CortexDispatcher()
engine = SoftReasoningEngine()


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
        raise HTTPException(status_code=500, detail=str(exc))
    if data.get("error"):
        raise HTTPException(status_code=403, detail=data["error"])
    if data.get("response") == "No plugin for intent":
        raise HTTPException(status_code=404, detail="unknown intent")
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
    from src.self_refactor import log_utils

    logs = log_utils.load_logs(full=full)
    return {"logs": logs}
