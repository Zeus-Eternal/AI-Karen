"""
API router for the llama.cpp server.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .auth import make_auth_dependency
from .utils import Stopwatch, RateLimiter

logger = logging.getLogger(__name__)


class ModelLoadRequest(BaseModel):
    model_id: str = Field(..., description="Model identifier to load")


class InferenceRequest(BaseModel):
    prompt: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


def create_router(server, auth_token: Optional[str]) -> APIRouter:
    router = APIRouter()
    auth_dep = make_auth_dependency(auth_token)
    rate_limiter = RateLimiter(limit=server.config.get("server.rate_limit_per_min", 120))

    async def _rate_limit():
        if not rate_limiter.allow():
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    @router.get("/", dependencies=[Depends(auth_dep)])
    async def root():
        return {"message": "llama.cpp server", "version": "1.0.0"}

    @router.get("/health", dependencies=[Depends(auth_dep), Depends(_rate_limit)])
    async def health():
        return await server.health_monitor.snapshot()

    @router.get("/models", dependencies=[Depends(auth_dep), Depends(_rate_limit)])
    async def list_models():
        return await server.model_manager.status()

    @router.post("/models/load", dependencies=[Depends(auth_dep), Depends(_rate_limit)])
    async def load_model(req: ModelLoadRequest):
        timer = Stopwatch()
        ok = await server.model_manager.load_model(req.model_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to load model")
        await server.performance_engine.record_load_ms(timer.ms())
        return {"status": "ok", "model_id": req.model_id}

    @router.post("/models/unload/{model_id}", dependencies=[Depends(auth_dep), Depends(_rate_limit)])
    async def unload_model(model_id: str):
        ok = await server.model_manager.unload_model(model_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to unload model")
        return {"status": "ok", "model_id": model_id}

    @router.post("/inference", dependencies=[Depends(auth_dep), Depends(_rate_limit)])
    async def inference(req: InferenceRequest):
        optimized_prompt = await server.karen_optimization.optimize_prompt(req.prompt)
        optimized_params = await server.karen_optimization.optimize_params(req.parameters)
        result = await server.model_manager.inference(optimized_prompt, optimized_params)
        await server.performance_engine.record_inference_ms(result["duration_ms"])
        return {
            "response": result["response"],
            "model_id": result["model_id"],
            "parameters": optimized_params,
            "timing": {"inference_time_ms": result["duration_ms"]},
        }

    @router.get("/performance", dependencies=[Depends(auth_dep), Depends(_rate_limit)])
    async def performance():
        return await server.performance_engine.snapshot()

    @router.get("/karen", dependencies=[Depends(auth_dep)])
    async def karen():
        return await server.karen_optimization.snapshot()

    return router
