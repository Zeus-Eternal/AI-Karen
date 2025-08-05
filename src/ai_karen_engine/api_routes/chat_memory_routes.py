"""
Production Chat Memory API Routes
RESTful endpoints for chat memory management with proper authentication
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ai_karen_engine.chat.production_memory import production_chat_memory
from ai_karen_engine.core.dependencies import get_current_user_context
from ai_karen_engine.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["chat-memory"])


# Alias core dependency for convenience
get_current_user = get_current_user_context


# Request/Response Models
class StoreTurnRequest(BaseModel):
    chat_id: str
    prompt: str
    response: str
    metadata: Optional[Dict[str, Any]] = None


class ChatReferenceResponse(BaseModel):
    chat_id: str
    user_id: str
    query: Optional[str] = None
    summary: Optional[str] = None
    turns: List[Dict[str, Any]] = Field(default_factory=list)
    semantic_results: List[Dict[str, Any]] = Field(default_factory=list)
    recent_context: Optional[Dict[str, Any]] = None
    timestamp: str


class SemanticSearchRequest(BaseModel):
    query: str
    chat_id: Optional[str] = None
    limit: int = 5
    similarity_threshold: float = 0.7


class MemorySettingsRequest(BaseModel):
    short_term_days: Optional[int] = None
    long_term_days: Optional[int] = None
    tail_turns: Optional[int] = None
    summarize_threshold_tokens: Optional[int] = None


class MemoryStatsResponse(BaseModel):
    user_id: str
    total_chats: int
    total_turns: int
    redis_keys: int
    vector_entries: int
    last_cleanup: Optional[str] = None


# Chat Memory Routes


@router.post("/store-turn")
async def store_chat_turn(
    request: StoreTurnRequest, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Store a chat turn in memory system"""

    try:
        success = await production_chat_memory.store_turn(
            chat_id=request.chat_id,
            user_id=current_user["user_id"],
            prompt=request.prompt,
            response=request.response,
            metadata=request.metadata,
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to store chat turn")

        return {"status": "success", "message": "Chat turn stored successfully"}

    except Exception as e:
        logger.error(f"Error storing chat turn: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{chat_id}/reference", response_model=ChatReferenceResponse)
async def get_chat_reference(
    chat_id: str,
    query: Optional[str] = Query(None, description="Search query for semantic recall"),
    limit: int = Query(5, ge=1, le=50, description="Maximum number of results"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get chat reference for context injection"""

    try:
        reference_data = await production_chat_memory.get_chat_reference(
            chat_id=chat_id, user_id=current_user["user_id"], query=query, limit=limit
        )

        return ChatReferenceResponse(**reference_data)

    except Exception as e:
        logger.error(f"Error getting chat reference: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{chat_id}/context")
async def get_chat_context(
    chat_id: str,
    include_summary: bool = Query(True, description="Include conversation summary"),
    max_turns: Optional[int] = Query(
        None, ge=1, le=100, description="Maximum turns to return"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get chat context from hot storage"""

    try:
        context = await production_chat_memory.get_chat_context(
            chat_id=chat_id,
            user_id=current_user["user_id"],
            include_summary=include_summary,
            max_turns=max_turns,
        )

        return context

    except Exception as e:
        logger.error(f"Error getting chat context: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/semantic-search")
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Search chat history using semantic similarity"""

    try:
        results = await production_chat_memory.semantic_search(
            user_id=current_user["user_id"],
            query=request.query,
            chat_id=request.chat_id,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold,
        )

        return {
            "query": request.query,
            "results": results,
            "total_results": len(results),
            "chat_id": request.chat_id,
        }

    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{chat_id}/memory-settings")
async def update_memory_settings(
    chat_id: str,
    request: MemorySettingsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Update memory settings for a specific chat"""

    try:
        # Convert request to dict, excluding None values
        settings_update = {k: v for k, v in request.dict().items() if v is not None}

        if not settings_update:
            raise HTTPException(status_code=400, detail="No settings provided")

        success = await production_chat_memory.update_user_memory_settings(
            user_id=current_user["user_id"],
            chat_id=chat_id,
            settings_update=settings_update,
        )

        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to update memory settings"
            )

        return {
            "status": "success",
            "message": "Memory settings updated successfully",
            "updated_settings": settings_update,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating memory settings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{chat_id}/memory-settings")
async def get_memory_settings(
    chat_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get memory settings for a specific chat"""

    try:
        # Get chat config from memory service
        chat_config = await production_chat_memory._get_chat_config(
            user_id=current_user["user_id"], chat_id=chat_id
        )

        return {
            "chat_id": chat_id,
            "user_id": current_user["user_id"],
            "settings": {
                "short_term_days": chat_config.short_term_days,
                "long_term_days": chat_config.long_term_days,
                "tail_turns": chat_config.tail_turns,
                "summarize_threshold_tokens": chat_config.summarize_threshold_tokens,
            },
            "stats": {
                "total_turns": chat_config.total_turns,
                "last_summarized_at": chat_config.last_summarized_at.isoformat()
                if chat_config.last_summarized_at
                else None,
                "created_at": chat_config.created_at.isoformat(),
                "updated_at": chat_config.updated_at.isoformat(),
            },
        }

    except Exception as e:
        logger.error(f"Error getting memory settings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/cleanup-memory")
async def cleanup_user_memory(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Clean up expired memory for the current user"""

    try:
        cleanup_stats = await production_chat_memory.cleanup_expired_memory(
            user_id=current_user["user_id"]
        )

        return {
            "status": "success",
            "message": "Memory cleanup completed",
            "stats": cleanup_stats,
        }

    except Exception as e:
        logger.error(f"Error cleaning up memory: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/memory-stats", response_model=MemoryStatsResponse)
async def get_memory_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get memory usage statistics for the current user"""

    try:
        # This would need to be implemented in the memory service
        # For now, return basic stats
        stats = {
            "user_id": current_user["user_id"],
            "total_chats": 0,  # Would query from database
            "total_turns": 0,  # Would query from database
            "redis_keys": 0,  # Would query from Redis
            "vector_entries": 0,  # Would query from vector DB
            "last_cleanup": None,
        }

        return MemoryStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check endpoint
@router.get("/health")
async def memory_health_check():
    """Health check for chat memory system"""

    try:
        # Test Redis connection
        redis_status = production_chat_memory.redis_client.ping()

        return {
            "status": "healthy",
            "redis_connected": redis_status,
            "timestamp": production_chat_memory.redis_client.time()[0],
        }

    except Exception as e:
        logger.error(f"Memory health check failed: {e}")
        return {"status": "unhealthy", "error": str(e), "redis_connected": False}
