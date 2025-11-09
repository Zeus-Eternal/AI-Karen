"""
LlamaCpp In-Process LLM Plugin for Kari AI
- Pure llama-cpp-python (no REST, no HTTP, no server)
- Production-safe, hot-swap, async/streaming, health, all via FastAPI
- Plugin entrypoint: import as 'router' per manifest
"""

import logging
from fastapi import APIRouter, HTTPException, Body, Request
from fastapi.responses import StreamingResponse
from starlette.concurrency import iterate_in_threadpool
from typing import List, Dict, Optional, Any

from ai_karen_engine.plugins.llm_services.llama.llama_client import llamacpp_inprocess_client

router = APIRouter(
    prefix="/llm/llamacpp",
    tags=["LlamaCpp (In-Process LLM)"],
)

log = logging.getLogger("llamacpp_plugin")
log.setLevel(logging.INFO)

# --- List all available models
@router.get("/models", response_model=List[str])
def list_models():
    """Return all available GGUF models in the model directory."""
    try:
        models = llamacpp_inprocess_client.list_models()
        return models
    except Exception as e:
        log.exception("Model listing failed")
        raise HTTPException(status_code=500, detail=str(e))

# --- Switch GGUF model (hot-swap)
@router.post("/switch")
def switch_model(
    model_name: str = Body(..., embed=True),
    ctx_size: Optional[int] = Body(None),
    n_threads: Optional[int] = Body(None)
):
    """
    Hot-swap to a different GGUF model. Optionally adjust context size or threads.
    """
    try:
        llamacpp_inprocess_client.switch_model(model_name, ctx_size, n_threads)
        return {"status": "ok", "active_model": llamacpp_inprocess_client.model_name}
    except Exception as e:
        log.exception("Switch model failed")
        raise HTTPException(status_code=500, detail=str(e))

# --- Health check
@router.get("/health", response_model=Dict[str, Any])
def health():
    """
    Basic health check: can load model and answer to 'ping'.
    """
    try:
        status = llamacpp_inprocess_client.health_check()
        return status
    except Exception as e:
        log.exception("Health check failed")
        raise HTTPException(status_code=500, detail=str(e))

# --- Embedding API
@router.post("/embedding")
def embedding(
    text: Any = Body(..., embed=True)
):
    """
    Get an embedding vector for a given string or list of strings.
    """
    try:
        result = llamacpp_inprocess_client.embedding(text)
        return {"embedding": result}
    except Exception as e:
        log.exception("Embedding failed")
        raise HTTPException(status_code=500, detail=str(e))

# --- Synchronous chat (single response or streaming)
@router.post("/chat")
def chat(
    messages: List[Dict[str, str]] = Body(..., embed=True),
    max_tokens: int = Body(128),
    stream: bool = Body(False)
):
    """
    Synchronous chat endpoint. Set stream=True for token streaming.
    """
    try:
        if stream:
            def generator():
                for chunk in llamacpp_inprocess_client.chat(messages, stream=True, max_tokens=max_tokens):
                    yield chunk
            return StreamingResponse(generator(), media_type="text/plain")
        else:
            response = llamacpp_inprocess_client.chat(messages, stream=False, max_tokens=max_tokens)
            return {"response": response}
    except Exception as e:
        log.exception("Chat failed")
        raise HTTPException(status_code=500, detail=str(e))

# --- Async Chat (for advanced clients or mobile UX)

@router.post("/achat")
async def achat(
    request: Request,
    messages: List[Dict[str, str]] = Body(..., embed=True),
    max_tokens: int = Body(128),
    stream: bool = Body(False)
):
    """
    Async chat endpoint. Supports async token streaming and non-blocking chat.
    """
    try:
        if stream:
            async def streamer():
                async for chunk in llamacpp_inprocess_client.achat(messages, stream=True, max_tokens=max_tokens):
                    yield chunk
            # Some environments may require token streaming to be run in threadpool for thread safety
            return StreamingResponse(iterate_in_threadpool(streamer()), media_type="text/plain")
        else:
            # Non-streaming: run in executor for non-blocking I/O
            response = await llamacpp_inprocess_client.achat(messages, stream=False, max_tokens=max_tokens)
            return {"response": response}
    except Exception as e:
        log.exception("Async chat failed")
        raise HTTPException(status_code=500, detail=str(e))
