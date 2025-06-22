from fastapi import FastAPI
from pydantic import BaseModel

from core.cortex.dispatch import CortexDispatcher
from core.soft_reasoning_engine import SoftReasoningEngine
from core.embedding_manager import _METRICS as METRICS

from typing import Any, Dict, List

app = FastAPI()

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



@app.post("/chat")
async def chat(req: ChatRequest) -> ChatResponse:
    role = getattr(req, "role", "user")
    data = await dispatcher.dispatch(req.text, role=role)
    return ChatResponse(**data)

@app.post("/chat")
async def chat(req: ChatRequest):
 
    role = getattr(req, "role", "user")
    data = await dispatcher.dispatch(req.text, role=role)
    return ChatResponse(**data)


@app.post("/store")
async def store(req: StoreRequest) -> StoreResponse:
    metadata = {"tag": req.tag} if req.tag else None
    rid = engine.ingest(
        req.text,
        metadata=metadata,
        ttl_seconds=req.ttl_seconds,
    )
    return StoreResponse(status="stored", id=rid)


@app.post("/search")
async def search(req: SearchRequest) -> List[SearchResult]:
    top_k = getattr(req, "top_k", 3)
    results = engine.query(
        req.text,
        top_k=top_k,
        metadata_filter=getattr(req, "metadata_filter", None),
    )
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
        return {"error": "not found"}
    return plugin.manifest
