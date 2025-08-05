from __future__ import annotations

import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from ai_karen_engine.services.memory_service import WebUIMemoryService
from ai_karen_engine.core.dependencies import get_memory_service
from ai_karen_engine.utils.bootstrap import bootstrap_memory_system

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])

@router.post("/bootstrap_memory")
async def bootstrap_memory(
    request: Request,
    memory_service: WebUIMemoryService = Depends(get_memory_service),
):
    """Force initialization of memory tables and default models."""
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    try:
        success = await bootstrap_memory_system(memory_service, tenant_id="default")
        return JSONResponse({"success": success})
    except Exception as exc:
        logger.error(f"[{trace_id}] bootstrap failed: {exc}")
        raise HTTPException(status_code=500, detail="bootstrap failed") from exc
