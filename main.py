from fastapi import FastAPI
from pydantic import BaseModel

from core.cortex.dispatch import CortexDispatcher
from core.soft_reasoning_engine import SoftReasoningEngine
from core.embedding_manager import _METRICS as METRICS

app = FastAPI()

dispatcher = CortexDispatcher()
engine = SoftReasoningEngine()


class ChatRequest(BaseModel):
    text: str
    role: str = "user"


class StoreRequest(BaseModel):
    text: str


class SearchRequest(BaseModel):
    text: str
    top_k: int = 3


@app.get("/ping")
def ping():
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: ChatRequest):
    return await dispatcher.dispatch(req.text, role=req.role)
    return await dispatcher.dispatch(req.text)


@app.post("/store")
async def store(req: StoreRequest):
    engine.ingest(req.text)
    return {"status": "stored"}


@app.post("/search")
async def search(req: SearchRequest):
    top_k = getattr(req, "top_k", 3)
    return engine.query(req.text, top_k=top_k)


@app.get("/metrics")
def metrics():
    return METRICS
