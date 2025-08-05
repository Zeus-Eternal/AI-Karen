"""FastAPI routes exposing the AG-UI memory interface."""

from fastapi import APIRouter, Depends

from ai_karen_engine.core.dependencies import get_memory_service
from ai_karen_engine.models.ag_ui_types import AGUIMemoryQuery, AGUIMemoryQueryResponse
from ai_karen_engine.services.ag_ui_memory_interface import (
    transform_ag_ui_query,
    transform_web_ui_entries,
)
from ai_karen_engine.services.memory_service import WebUIMemoryService

router = APIRouter(tags=["ag-ui-memory"])


@router.post("/query", response_model=AGUIMemoryQueryResponse)
async def query_ag_ui_memory(
    request: AGUIMemoryQuery,
    memory_service: WebUIMemoryService = Depends(get_memory_service),
) -> AGUIMemoryQueryResponse:
    """Query the memory system using AG-UI request format."""
    web_query = await transform_ag_ui_query(request)
    memories = await memory_service.query_memories("default", web_query)
    entries = transform_web_ui_entries(memories)
    return AGUIMemoryQueryResponse(memories=entries)
