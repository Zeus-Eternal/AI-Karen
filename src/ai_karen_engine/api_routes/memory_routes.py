# src/ai_karen_engine/api_routes/memory_routes.py

from uuid import UUID
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from fastapi import APIRouter, HTTPException, Depends, Query, Request, status
from pydantic import BaseModel, Field

from ai_karen_engine.services.memory_service import (
    WebUIMemoryService,
    WebUIMemoryQuery,
    MemoryType,
    UISource,
)
from ai_karen_engine.core.config_manager import AIKarenConfig
from ai_karen_engine.core.dependencies import get_memory_service, get_current_config
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.models.web_api_error_responses import (
    WebAPIErrorCode,
    ValidationErrorDetail,
    create_service_error_response,
    create_validation_error_response,
    create_generic_error_response,
    get_http_status_for_error_code,
)

router = APIRouter(prefix="/api/memory", tags=["memory"])
logger = get_logger(__name__)


# ─── Request / Response Models ────────────────────────────────────────────────

class StoreMemoryRequest(BaseModel):
    content: str = Field(..., description="Memory content")
    ui_source: UISource = Field(..., description="Source UI")
    session_id: Optional[str] = Field(None, description="Session ID")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    memory_type: MemoryType = Field(MemoryType.GENERAL, description="Memory type")
    tags: Optional[List[str]] = Field(None, description="Memory tags")
    importance_score: Optional[int] = Field(None, ge=1, le=10, description="Importance score (1-10)")
    ai_generated: bool = Field(False, description="Whether memory is AI generated")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    ttl_hours: Optional[int] = Field(None, description="Time to live in hours")


class QueryMemoryRequest(BaseModel):
    text: str = Field(..., description="Query text")
    session_id: Optional[str] = Field(None, description="Session ID")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    ui_source: Optional[UISource] = Field(None, description="Filter by UI source")
    memory_types: List[MemoryType] = Field(default_factory=list, description="Filter by memory types")
    tags: List[str] = Field(default_factory=list, description="Filter by tags")
    importance_range: Optional[Tuple[int, int]] = Field(None, description="Importance score range")
    only_user_confirmed: bool = Field(True, description="Only user confirmed memories")
    only_ai_generated: bool = Field(False, description="Only AI generated memories")
    time_range_start: Optional[datetime] = Field(None, description="Start of time range")
    time_range_end: Optional[datetime] = Field(None, description="End of time range")
    top_k: int = Field(10, ge=1, le=100, description="Maximum results from the vector search")
    result_limit: Optional[int] = Field(None, ge=1, description="Override default result cap")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Similarity threshold")
    include_embeddings: bool = Field(False, description="Include embeddings in response")


class BuildContextRequest(BaseModel):
    query: str = Field(..., description="Context query")
    session_id: Optional[str] = Field(None, description="Session ID")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")


class ConfirmMemoryRequest(BaseModel):
    confirmed: bool = Field(..., description="Whether memory is confirmed")


class UpdateImportanceRequest(BaseModel):
    importance_score: int = Field(..., ge=1, le=10, description="New importance score")


class MemoryResponse(BaseModel):
    id: UUID
    content: str
    metadata: Dict[str, Any]
    timestamp: float
    ttl: Optional[str]
    user_id: Optional[str]
    session_id: Optional[str]
    tags: List[str]
    similarity_score: Optional[float]
    ui_source: Optional[str]
    conversation_id: Optional[str]
    memory_type: str
    importance_score: int
    access_count: int
    last_accessed: Optional[str]
    ai_generated: bool
    user_confirmed: bool


class StoreMemoryResponse(BaseModel):
    memory_id: Optional[UUID]
    success: bool
    message: str


class QueryMemoryResponse(BaseModel):
    memories: List[MemoryResponse]
    total_found: int
    query_metadata: Dict[str, Any]


class ContextResponse(BaseModel):
    memories: List[Dict[str, Any]]
    total_memories: int
    memory_types_found: List[str]
    conversation_context: Optional[Dict[str, Any]]
    context_metadata: Dict[str, Any]


class AnalyticsResponse(BaseModel):
    total_memories: int
    memories_by_type: Dict[str, int]
    memories_by_ui_source: Dict[str, int]
    memories_by_importance: Dict[str, int]
    ai_generated_count: int
    user_confirmed_count: int
    average_importance: float
    most_accessed_memories: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    tag_frequency: Dict[str, int]
    web_ui_metrics: Dict[str, Any]


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/store", response_model=StoreMemoryResponse)
async def store_memory(
    req: StoreMemoryRequest,
    memory_service: WebUIMemoryService = Depends(get_memory_service),
):
    try:
        memory_id = await memory_service.store_web_ui_memory(
            tenant_id="default",
            content=req.content,
            user_id="anonymous",
            ui_source=req.ui_source,
            session_id=req.session_id,
            conversation_id=req.conversation_id,
            memory_type=req.memory_type,
            tags=req.tags,
            importance_score=req.importance_score,
            ai_generated=req.ai_generated,
            metadata=req.metadata,
            ttl_hours=req.ttl_hours,
        )
        return StoreMemoryResponse(
            memory_id=memory_id,
            success=bool(memory_id),
            message="Memory stored successfully" if memory_id else "Memory not stored",
        )
    except Exception as e:
        logger.exception("Failed to store memory", error=str(e))
        error = create_service_error_response(
            service_name="memory",
            error=e,
            error_code=WebAPIErrorCode.MEMORY_ERROR,
            user_message="Failed to store memory. Please try again.",
        )
        raise HTTPException(
            status_code=get_http_status_for_error_code(WebAPIErrorCode.MEMORY_ERROR),
            detail=error.dict(),
        )


@router.post("/query", response_model=QueryMemoryResponse)
async def query_memories(
    req: QueryMemoryRequest,
    config: AIKarenConfig = Depends(get_current_config),
    memory_service: WebUIMemoryService = Depends(get_memory_service),
):
    try:
        time_range = (
            (req.time_range_start, req.time_range_end)
            if req.time_range_start and req.time_range_end else None
        )
        limit = req.result_limit or config.memory.get("query_limit", 100)

        query_obj = WebUIMemoryQuery(
            text=req.text,
            user_id="anonymous",
            session_id=req.session_id,
            conversation_id=req.conversation_id,
            ui_source=req.ui_source,
            memory_types=req.memory_types,
            tags=req.tags,
            importance_range=req.importance_range,
            only_user_confirmed=req.only_user_confirmed,
            only_ai_generated=req.only_ai_generated,
            time_range=time_range,
            top_k=min(req.top_k, limit),
            similarity_threshold=req.similarity_threshold,
            include_embeddings=req.include_embeddings,
        )
        results = await memory_service.query_memories("default", query_obj)
        results = results[:limit]

        memories = [
            MemoryResponse(
                id=m.id,
                content=m.content,
                metadata=m.metadata,
                timestamp=m.timestamp,
                ttl=m.ttl.isoformat() if m.ttl else None,
                user_id=m.user_id,
                session_id=m.session_id,
                tags=m.tags,
                similarity_score=m.similarity_score,
                ui_source=m.ui_source.value if m.ui_source else None,
                conversation_id=m.conversation_id,
                memory_type=m.memory_type.value,
                importance_score=m.importance_score,
                access_count=m.access_count,
                last_accessed=m.last_accessed.isoformat() if m.last_accessed else None,
                ai_generated=m.ai_generated,
                user_confirmed=m.user_confirmed,
            )
            for m in results
        ]

        return QueryMemoryResponse(
            memories=memories,
            total_found=len(memories),
            query_metadata={
                "query_text": req.text,
                "filters_applied": {
                    "ui_source": req.ui_source.value if req.ui_source else None,
                    "memory_types": [mt.value for mt in req.memory_types],
                    "tags": req.tags,
                    "importance_range": req.importance_range,
                    "only_user_confirmed": req.only_user_confirmed,
                    "only_ai_generated": req.only_ai_generated,
                },
                "search_params": {
                    "top_k": req.top_k,
                    "result_limit": limit,
                    "similarity_threshold": req.similarity_threshold,
                },
            },
        )
    except Exception as e:
        logger.exception("Failed to query memories", error=str(e))
        error = create_service_error_response(
            service_name="memory",
            error=e,
            error_code=WebAPIErrorCode.MEMORY_ERROR,
            user_message="Failed to query memories. Please try again.",
        )
        raise HTTPException(
            status_code=get_http_status_for_error_code(WebAPIErrorCode.MEMORY_ERROR),
            detail=error.dict(),
        )


@router.post("/context", response_model=ContextResponse)
async def build_context(
    req: BuildContextRequest,
    memory_service: WebUIMemoryService = Depends(get_memory_service),
):
    try:
        ctx = await memory_service.build_conversation_context(
            tenant_id="default",
            query=req.query,
            user_id="anonymous",
            session_id=req.session_id,
            conversation_id=req.conversation_id,
        )
        return ContextResponse(**ctx)
    except Exception as e:
        logger.exception("Failed to build context", error=str(e))
        error = create_service_error_response(
            service_name="memory",
            error=e,
            error_code=WebAPIErrorCode.MEMORY_ERROR,
            user_message="Failed to build conversation context. Please try again.",
        )
        raise HTTPException(
            status_code=get_http_status_for_error_code(WebAPIErrorCode.MEMORY_ERROR),
            detail=error.dict(),
        )


@router.post("/{memory_id}/confirm")
async def confirm_memory(
    memory_id: UUID,
    req: ConfirmMemoryRequest,
    memory_service: WebUIMemoryService = Depends(get_memory_service),
):
    try:
        success = await memory_service.confirm_memory(
            tenant_id="default", memory_id=str(memory_id), confirmed=req.confirmed
        )
        if not success:
            err = create_generic_error_response(
                error_code=WebAPIErrorCode.NOT_FOUND,
                message="Memory not found",
                user_message="The requested memory could not be found.",
                details={"memory_id": memory_id},
            )
            raise HTTPException(
                status_code=get_http_status_for_error_code(WebAPIErrorCode.NOT_FOUND), detail=err.dict()
            )
        return {"success": True, "message": f"Memory {'confirmed' if req.confirmed else 'rejected'} successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to confirm memory", error=str(e))
        error = create_service_error_response(
            service_name="memory",
            error=e,
            error_code=WebAPIErrorCode.MEMORY_ERROR,
            user_message="Failed to confirm memory. Please try again.",
        )
        raise HTTPException(
            status_code=get_http_status_for_error_code(WebAPIErrorCode.MEMORY_ERROR),
            detail=error.dict(),
        )


@router.put("/{memory_id}/importance")
async def update_importance(
    memory_id: UUID,
    req: UpdateImportanceRequest,
    memory_service: WebUIMemoryService = Depends(get_memory_service),
):
    try:
        success = await memory_service.update_memory_importance(
            tenant_id="default", memory_id=str(memory_id), importance_score=req.importance_score
        )
        if not success:
            err = create_generic_error_response(
                error_code=WebAPIErrorCode.NOT_FOUND,
                message="Memory not found",
                user_message="The requested memory could not be found.",
                details={"memory_id": memory_id},
            )
            raise HTTPException(
                status_code=get_http_status_for_error_code(WebAPIErrorCode.NOT_FOUND), detail=err.dict()
            )
        return {"success": True, "message": f"Memory importance updated to {req.importance_score}"}
    except HTTPException:
        raise
    except ValueError as e:
        val_err = [ValidationErrorDetail(field="importance_score", message=str(e), invalid_value=req.importance_score)]
        err = create_validation_error_response(field_errors=val_err, user_message="Invalid importance score value.")
        raise HTTPException(status_code=get_http_status_for_error_code(WebAPIErrorCode.VALIDATION_ERROR), detail=err.dict())
    except Exception as e:
        logger.exception("Failed to update importance", error=str(e))
        error = create_service_error_response(
            service_name="memory",
            error=e,
            error_code=WebAPIErrorCode.MEMORY_ERROR,
            user_message="Failed to update memory importance. Please try again.",
        )
        raise HTTPException(
            status_code=get_http_status_for_error_code(WebAPIErrorCode.MEMORY_ERROR),
            detail=error.dict(),
        )


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: UUID,
    memory_service: WebUIMemoryService = Depends(get_memory_service),
):
    try:
        success = await memory_service.base_manager.delete_memory(tenant_id="default", memory_id=str(memory_id))
        if not success:
            err = create_generic_error_response(
                error_code=WebAPIErrorCode.NOT_FOUND,
                message="Memory not found",
                user_message="The requested memory could not be found.",
                details={"memory_id": memory_id},
            )
            raise HTTPException(
                status_code=get_http_status_for_error_code(WebAPIErrorCode.NOT_FOUND), detail=err.dict()
            )
        return {"success": True, "message": "Memory deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete memory", error=str(e))
        error = create_service_error_response(
            service_name="memory",
            error=e,
            error_code=WebAPIErrorCode.MEMORY_ERROR,
            user_message="Failed to delete memory. Please try again.",
        )
        raise HTTPException(
            status_code=get_http_status_for_error_code(WebAPIErrorCode.MEMORY_ERROR),
            detail=error.dict(),
        )


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    time_range_start: Optional[datetime] = Query(None, description="Start of time range"),
    time_range_end: Optional[datetime] = Query(None, description="End of time range"),
    memory_service: WebUIMemoryService = Depends(get_memory_service),
):
    try:
        time_range = (time_range_start, time_range_end) if time_range_start and time_range_end else None
        analytics = await memory_service.get_memory_analytics(
            tenant_id="default", user_id=user_id or "anonymous", time_range=time_range
        )
        return AnalyticsResponse(**analytics)
    except Exception as e:
        logger.exception("Failed to get analytics", error=str(e))
        error = create_service_error_response(
            service_name="memory",
            error=e,
            error_code=WebAPIErrorCode.MEMORY_ERROR,
            user_message="Failed to get memory analytics. Please try again.",
        )
        raise HTTPException(
            status_code=get_http_status_for_error_code(WebAPIErrorCode.MEMORY_ERROR),
            detail=error.dict(),
        )


@router.get("/stats")
async def get_memory_stats(memory_service: WebUIMemoryService = Depends(get_memory_service)):
    try:
        base_stats = await memory_service.base_manager.get_memory_stats("default")
        web_ui_metrics = memory_service.get_metrics()
        return {"base_stats": base_stats, "web_ui_metrics": web_ui_metrics, "tenant_id": "default"}
    except Exception as e:
        logger.exception("Failed to get stats", error=str(e))
        error = create_service_error_response(
            service_name="memory",
            error=e,
            error_code=WebAPIErrorCode.MEMORY_ERROR,
            user_message="Failed to get memory statistics. Please try again.",
        )
        raise HTTPException(
            status_code=get_http_status_for_error_code(WebAPIErrorCode.MEMORY_ERROR),
            detail=error.dict(),
        )


@router.post("/prune-expired")
async def prune_expired_memories(memory_service: WebUIMemoryService = Depends(get_memory_service)):
    try:
        count = await memory_service.base_manager.prune_expired_memories("default")
        return {"success": True, "pruned_count": count, "message": f"Pruned {count} expired memories"}
    except Exception as e:
        logger.exception("Failed to prune memories", error=str(e))
        error = create_service_error_response(
            service_name="memory",
            error=e,
            error_code=WebAPIErrorCode.MEMORY_ERROR,
            user_message="Failed to prune expired memories. Please try again.",
        )
        raise HTTPException(
            status_code=get_http_status_for_error_code(WebAPIErrorCode.MEMORY_ERROR),
            detail=error.dict(),
        )


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "memory", "timestamp": datetime.utcnow().isoformat()}
