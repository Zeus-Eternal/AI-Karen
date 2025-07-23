"""
FastAPI routes for enhanced memory management with web UI integration.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..services.memory_service import (
    WebUIMemoryService,
    WebUIMemoryQuery,
    MemoryType,
    UISource,
)
from ..core.config_manager import AIKarenConfig
from ..core.dependencies import get_memory_service, get_current_config
# from ..database.client import get_db_client  # Not needed with dependency injection
# Temporarily disable auth imports for web UI integration

router = APIRouter(prefix="/api/memory", tags=["memory"])


# Request/Response Models
class StoreMemoryRequest(BaseModel):
    """Request model for storing memory."""
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
    """Request model for querying memories."""
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
    """Request model for building conversation context."""
    query: str = Field(..., description="Context query")
    session_id: Optional[str] = Field(None, description="Session ID")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")


class ConfirmMemoryRequest(BaseModel):
    """Request model for confirming memory."""
    confirmed: bool = Field(..., description="Whether memory is confirmed")


class UpdateImportanceRequest(BaseModel):
    """Request model for updating memory importance."""
    importance_score: int = Field(..., ge=1, le=10, description="New importance score")


class MemoryResponse(BaseModel):
    """Response model for memory entries."""
    id: str
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
    """Response model for storing memory."""
    memory_id: Optional[str]
    success: bool
    message: str


class QueryMemoryResponse(BaseModel):
    """Response model for querying memories."""
    memories: List[MemoryResponse]
    total_found: int
    query_metadata: Dict[str, Any]


class ContextResponse(BaseModel):
    """Response model for conversation context."""
    memories: List[Dict[str, Any]]
    total_memories: int
    memory_types_found: List[str]
    conversation_context: Optional[Dict[str, Any]]
    context_metadata: Dict[str, Any]


class AnalyticsResponse(BaseModel):
    """Response model for memory analytics."""
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





@router.post("/store", response_model=StoreMemoryResponse)
async def store_memory(
    request: StoreMemoryRequest,
    
    
    memory_service: WebUIMemoryService = Depends(get_memory_service)
):
    """Store a new memory entry."""
    try:
        memory_id = await memory_service.store_web_ui_memory(
            tenant_id="default",
            content=request.content,
            user_id="anonymous",
            ui_source=request.ui_source,
            session_id=request.session_id,
            conversation_id=request.conversation_id,
            memory_type=request.memory_type,
            tags=request.tags,
            importance_score=request.importance_score,
            ai_generated=request.ai_generated,
            metadata=request.metadata,
            ttl_hours=request.ttl_hours
        )
        
        return StoreMemoryResponse(
            memory_id=memory_id,
            success=memory_id is not None,
            message="Memory stored successfully" if memory_id else "Memory not stored (not surprising enough)"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store memory: {str(e)}")


@router.post("/query", response_model=QueryMemoryResponse)
async def query_memories(
    request: QueryMemoryRequest,
    config: AIKarenConfig = Depends(get_current_config),
    memory_service: WebUIMemoryService = Depends(get_memory_service)
):
    """Query memories with advanced filtering."""
    try:
        # Build time range tuple if provided
        time_range = None
        if request.time_range_start and request.time_range_end:
            time_range = (request.time_range_start, request.time_range_end)
        
        # Determine the maximum number of results
        limit = request.result_limit or config.memory.get("query_limit", 100)

        # Create query object
        query = WebUIMemoryQuery(
            text=request.text,
            user_id="anonymous",
            session_id=request.session_id,
            conversation_id=request.conversation_id,
            ui_source=request.ui_source,
            memory_types=request.memory_types,
            tags=request.tags,
            importance_range=request.importance_range,
            only_user_confirmed=request.only_user_confirmed,
            only_ai_generated=request.only_ai_generated,
            time_range=time_range,
            top_k=min(request.top_k, limit),
            similarity_threshold=request.similarity_threshold,
            include_embeddings=request.include_embeddings
        )

        memories = await memory_service.query_memories("default", query)

        # Enforce final limit on returned results
        memories = memories[:limit]
        
        # Convert to response format
        memory_responses = []
        for memory in memories:
            memory_responses.append(MemoryResponse(
                id=memory.id,
                content=memory.content,
                metadata=memory.metadata,
                timestamp=memory.timestamp,
                ttl=memory.ttl.isoformat() if memory.ttl else None,
                user_id=memory.user_id,
                session_id=memory.session_id,
                tags=memory.tags,
                similarity_score=memory.similarity_score,
                ui_source=memory.ui_source.value if memory.ui_source else None,
                conversation_id=memory.conversation_id,
                memory_type=memory.memory_type.value,
                importance_score=memory.importance_score,
                access_count=memory.access_count,
                last_accessed=memory.last_accessed.isoformat() if memory.last_accessed else None,
                ai_generated=memory.ai_generated,
                user_confirmed=memory.user_confirmed
            ))
        
        return QueryMemoryResponse(
            memories=memory_responses,
            total_found=len(memory_responses),
            query_metadata={
                "query_text": request.text,
                "filters_applied": {
                    "ui_source": request.ui_source.value if request.ui_source else None,
                    "memory_types": [mt.value for mt in request.memory_types],
                    "tags": request.tags,
                    "importance_range": request.importance_range,
                    "only_user_confirmed": request.only_user_confirmed,
                    "only_ai_generated": request.only_ai_generated
                },
                "search_params": {
                    "top_k": request.top_k,
                    "result_limit": limit,
                    "similarity_threshold": request.similarity_threshold
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query memories: {str(e)}")


@router.post("/context", response_model=ContextResponse)
async def build_context(
    request: BuildContextRequest,
    
    
    memory_service: WebUIMemoryService = Depends(get_memory_service)
):
    """Build conversation context from relevant memories."""
    try:
        context = await memory_service.build_conversation_context(
            tenant_id="default",
            query=request.query,
            user_id="anonymous",
            session_id=request.session_id,
            conversation_id=request.conversation_id
        )
        
        return ContextResponse(**context)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build context: {str(e)}")


@router.post("/{memory_id}/confirm")
async def confirm_memory(
    memory_id: str,
    request: ConfirmMemoryRequest,
    
    
    memory_service: WebUIMemoryService = Depends(get_memory_service)
):
    """Confirm or reject an AI-generated memory."""
    try:
        success = await memory_service.confirm_memory(
            tenant_id="default",
            memory_id=memory_id,
            confirmed=request.confirmed
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found or update failed")
        
        return {
            "success": True,
            "message": f"Memory {'confirmed' if request.confirmed else 'rejected'} successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to confirm memory: {str(e)}")


@router.put("/{memory_id}/importance")
async def update_importance(
    memory_id: str,
    request: UpdateImportanceRequest,
    
    
    memory_service: WebUIMemoryService = Depends(get_memory_service)
):
    """Update memory importance score."""
    try:
        success = await memory_service.update_memory_importance(
            tenant_id="default",
            memory_id=memory_id,
            importance_score=request.importance_score
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found or update failed")
        
        return {
            "success": True,
            "message": f"Memory importance updated to {request.importance_score}"
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update importance: {str(e)}")


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    
    
    memory_service: WebUIMemoryService = Depends(get_memory_service)
):
    """Delete a memory entry."""
    try:
        success = await memory_service.base_manager.delete_memory(
            tenant_id="default",
            memory_id=memory_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found or deletion failed")
        
        return {
            "success": True,
            "message": "Memory deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {str(e)}")


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    time_range_start: Optional[datetime] = Query(None, description="Start of time range"),
    time_range_end: Optional[datetime] = Query(None, description="End of time range"),
    
    
    memory_service: WebUIMemoryService = Depends(get_memory_service)
):
    """Get memory analytics for dashboard."""
    try:
        # Build time range tuple if provided
        time_range = None
        if time_range_start and time_range_end:
            time_range = (time_range_start, time_range_end)
        
        # Use current user if no user_id specified
        target_user_id = user_id or "anonymous"
        
        analytics = await memory_service.get_memory_analytics(
            tenant_id="default",
            user_id=target_user_id,
            time_range=time_range
        )
        
        return AnalyticsResponse(**analytics)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/stats")
async def get_memory_stats(
    
    
    memory_service: WebUIMemoryService = Depends(get_memory_service)
):
    """Get basic memory statistics."""
    try:
        stats = await memory_service.base_manager.get_memory_stats("default")
        web_ui_metrics = memory_service.get_metrics()
        
        return {
            "base_stats": stats,
            "web_ui_metrics": web_ui_metrics,
            "tenant_id": "default"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/prune-expired")
async def prune_expired_memories(
    
    
    memory_service: WebUIMemoryService = Depends(get_memory_service)
):
    """Prune expired memories for the tenant."""
    try:
        pruned_count = await memory_service.base_manager.prune_expired_memories("default")
        
        return {
            "success": True,
            "pruned_count": pruned_count,
            "message": f"Pruned {pruned_count} expired memories"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to prune memories: {str(e)}")


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for memory service."""
    return {
        "status": "healthy",
        "service": "memory",
        "timestamp": datetime.utcnow().isoformat()
    }