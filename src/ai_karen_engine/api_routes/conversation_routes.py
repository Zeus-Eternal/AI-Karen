"""
FastAPI routes for enhanced conversation management with web UI integration.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..services.conversation_service import (
    WebUIConversationService,
    ConversationStatus,
    ConversationPriority,
    UISource
)
from ..database.conversation_manager import MessageRole
# from ..database.client import get_db_client  # Not needed with dependency injection
# Temporarily disable auth imports for web UI integration

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


# Request/Response Models
class CreateConversationRequest(BaseModel):
    """Request model for creating conversation."""
    session_id: str = Field(..., description="Session ID")
    ui_source: UISource = Field(..., description="Source UI")
    title: Optional[str] = Field(None, description="Conversation title")
    initial_message: Optional[str] = Field(None, description="Initial user message")
    user_settings: Optional[Dict[str, Any]] = Field(None, description="User settings")
    ui_context: Optional[Dict[str, Any]] = Field(None, description="UI context data")
    tags: Optional[List[str]] = Field(None, description="Initial tags")
    priority: ConversationPriority = Field(ConversationPriority.NORMAL, description="Conversation priority")


class AddMessageRequest(BaseModel):
    """Request model for adding message."""
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    ui_source: UISource = Field(..., description="Source UI")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Message metadata")
    ai_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI confidence score")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    tokens_used: Optional[int] = Field(None, description="Tokens used")
    model_used: Optional[str] = Field(None, description="Model used for generation")


class BuildContextRequest(BaseModel):
    """Request model for building conversation context."""
    current_message: str = Field(..., description="Current message for context")
    include_memories: bool = Field(True, description="Include memory context")
    include_insights: bool = Field(True, description="Include AI insights")


class UpdateUIContextRequest(BaseModel):
    """Request model for updating UI context."""
    ui_context: Dict[str, Any] = Field(..., description="UI context data")


class UpdateAIInsightsRequest(BaseModel):
    """Request model for updating AI insights."""
    ai_insights: Dict[str, Any] = Field(..., description="AI insights data")


class AddTagsRequest(BaseModel):
    """Request model for adding tags."""
    tags: List[str] = Field(..., description="Tags to add")


class MessageResponse(BaseModel):
    """Response model for messages."""
    id: str
    role: str
    content: str
    timestamp: str
    metadata: Dict[str, Any]
    function_call: Optional[Dict[str, Any]]
    function_response: Optional[Dict[str, Any]]
    ui_source: Optional[str]
    ai_confidence: Optional[float]
    processing_time_ms: Optional[int]
    tokens_used: Optional[int]
    model_used: Optional[str]
    user_feedback: Optional[str]
    edited: bool
    edit_history: List[Dict[str, Any]]


class ConversationResponse(BaseModel):
    """Response model for conversations."""
    id: str
    user_id: str
    title: Optional[str]
    messages: List[MessageResponse]
    metadata: Dict[str, Any]
    is_active: bool
    created_at: str
    updated_at: str
    message_count: int
    last_message_at: Optional[str]
    session_id: Optional[str]
    ui_context: Dict[str, Any]
    ai_insights: Dict[str, Any]
    user_settings: Dict[str, Any]
    summary: Optional[str]
    tags: List[str]
    last_ai_response_id: Optional[str]
    status: str
    priority: str
    context_memories: List[Dict[str, Any]]
    proactive_suggestions: List[str]


class CreateConversationResponse(BaseModel):
    """Response model for creating conversation."""
    conversation: ConversationResponse
    success: bool
    message: str


class AddMessageResponse(BaseModel):
    """Response model for adding message."""
    message: MessageResponse
    success: bool


class ContextResponse(BaseModel):
    """Response model for conversation context."""
    conversation_summary: Dict[str, Any]
    recent_messages: List[Dict[str, Any]]
    relevant_memories: Dict[str, List[Dict[str, Any]]]
    ai_insights: Dict[str, Any]
    user_preferences: Dict[str, Any]
    ai_insights_context: Dict[str, Any]
    conversation_patterns: Dict[str, Any]
    context_metadata: Dict[str, Any]


class ConversationListResponse(BaseModel):
    """Response model for conversation list."""
    conversations: List[ConversationResponse]
    total_count: int
    has_more: bool


class AnalyticsResponse(BaseModel):
    """Response model for conversation analytics."""
    total_conversations: int
    active_conversations: int
    recent_conversations_7d: int
    total_messages: int
    avg_messages_per_conversation: float
    conversations_by_ui_source: Dict[str, int]
    conversations_by_priority: Dict[str, int]
    conversations_with_tags: int
    average_tags_per_conversation: float
    conversations_with_summaries: int
    most_common_tags: Dict[str, int]
    web_ui_metrics: Dict[str, Any]
    metrics: Dict[str, Any]


# Import dependency injection
from ..core.dependencies import get_conversation_service


def _convert_conversation_to_response(conversation) -> ConversationResponse:
    """Convert conversation to response model."""
    conversation_dict = conversation.to_dict()
    
    # Convert messages
    messages = []
    for msg_data in conversation_dict["messages"]:
        messages.append(MessageResponse(
            id=msg_data["id"],
            role=msg_data["role"],
            content=msg_data["content"],
            timestamp=msg_data["timestamp"],
            metadata=msg_data["metadata"],
            function_call=msg_data.get("function_call"),
            function_response=msg_data.get("function_response"),
            ui_source=msg_data.get("ui_source"),
            ai_confidence=msg_data.get("ai_confidence"),
            processing_time_ms=msg_data.get("processing_time_ms"),
            tokens_used=msg_data.get("tokens_used"),
            model_used=msg_data.get("model_used"),
            user_feedback=msg_data.get("user_feedback"),
            edited=msg_data.get("edited", False),
            edit_history=msg_data.get("edit_history", [])
        ))
    
    return ConversationResponse(
        id=conversation_dict["id"],
        user_id=conversation_dict["user_id"],
        title=conversation_dict["title"],
        messages=messages,
        metadata=conversation_dict["metadata"],
        is_active=conversation_dict["is_active"],
        created_at=conversation_dict["created_at"],
        updated_at=conversation_dict["updated_at"],
        message_count=conversation_dict["message_count"],
        last_message_at=conversation_dict["last_message_at"],
        session_id=conversation_dict["session_id"],
        ui_context=conversation_dict["ui_context"],
        ai_insights=conversation_dict["ai_insights"],
        user_settings=conversation_dict["user_settings"],
        summary=conversation_dict["summary"],
        tags=conversation_dict["tags"],
        last_ai_response_id=conversation_dict["last_ai_response_id"],
        status=conversation_dict["status"],
        priority=conversation_dict["priority"],
        context_memories=conversation_dict["context_memories"],
        proactive_suggestions=conversation_dict["proactive_suggestions"]
    )


@router.post("/create", response_model=CreateConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    
    
    conversation_service: WebUIConversationService = Depends(get_conversation_service)
):
    """Create a new conversation with web UI features."""
    try:
        conversation = await conversation_service.create_web_ui_conversation(
            tenant_id="default",
            user_id="anonymous",
            session_id=request.session_id,
            ui_source=request.ui_source,
            title=request.title,
            initial_message=request.initial_message,
            user_settings=request.user_settings,
            ui_context=request.ui_context,
            tags=request.tags,
            priority=request.priority
        )
        
        if not conversation:
            raise HTTPException(status_code=500, detail="Failed to create conversation")
        
        return CreateConversationResponse(
            conversation=_convert_conversation_to_response(conversation),
            success=True,
            message="Conversation created successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    include_context: bool = Query(True, description="Include context data"),
    
    
    conversation_service: WebUIConversationService = Depends(get_conversation_service)
):
    """Get conversation by ID with web UI features."""
    try:
        conversation = await conversation_service.get_web_ui_conversation(
            tenant_id="default",
            conversation_id=conversation_id,
            include_context=include_context
        )
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return _convert_conversation_to_response(conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")


@router.post("/{conversation_id}/messages", response_model=AddMessageResponse)
async def add_message(
    conversation_id: str,
    request: AddMessageRequest,
    
    
    conversation_service: WebUIConversationService = Depends(get_conversation_service)
):
    """Add a message to conversation with web UI features."""
    try:
        message = await conversation_service.add_web_ui_message(
            tenant_id="default",
            conversation_id=conversation_id,
            role=request.role,
            content=request.content,
            ui_source=request.ui_source,
            metadata=request.metadata,
            ai_confidence=request.ai_confidence,
            processing_time_ms=request.processing_time_ms,
            tokens_used=request.tokens_used,
            model_used=request.model_used
        )
        
        if not message:
            raise HTTPException(status_code=500, detail="Failed to add message")
        
        message_dict = message.to_dict()
        message_response = MessageResponse(
            id=message_dict["id"],
            role=message_dict["role"],
            content=message_dict["content"],
            timestamp=message_dict["timestamp"],
            metadata=message_dict["metadata"],
            function_call=message_dict.get("function_call"),
            function_response=message_dict.get("function_response"),
            ui_source=message_dict.get("ui_source"),
            ai_confidence=message_dict.get("ai_confidence"),
            processing_time_ms=message_dict.get("processing_time_ms"),
            tokens_used=message_dict.get("tokens_used"),
            model_used=message_dict.get("model_used"),
            user_feedback=message_dict.get("user_feedback"),
            edited=message_dict.get("edited", False),
            edit_history=message_dict.get("edit_history", [])
        )
        
        return AddMessageResponse(
            message=message_response,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")


@router.post("/{conversation_id}/context", response_model=ContextResponse)
async def build_context(
    conversation_id: str,
    request: BuildContextRequest,
    
    
    conversation_service: WebUIConversationService = Depends(get_conversation_service)
):
    """Build comprehensive conversation context."""
    try:
        context = await conversation_service.build_conversation_context(
            tenant_id="default",
            conversation_id=conversation_id,
            current_message=request.current_message,
            include_memories=request.include_memories,
            include_insights=request.include_insights
        )
        
        return ContextResponse(**context)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build context: {str(e)}")


@router.put("/{conversation_id}/ui-context")
async def update_ui_context(
    conversation_id: str,
    request: UpdateUIContextRequest,
    
    
    conversation_service: WebUIConversationService = Depends(get_conversation_service)
):
    """Update conversation UI context."""
    try:
        success = await conversation_service.update_conversation_ui_context(
            tenant_id="default",
            conversation_id=conversation_id,
            ui_context=request.ui_context
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found or update failed")
        
        return {
            "success": True,
            "message": "UI context updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update UI context: {str(e)}")


@router.put("/{conversation_id}/ai-insights")
async def update_ai_insights(
    conversation_id: str,
    request: UpdateAIInsightsRequest,
    
    
    conversation_service: WebUIConversationService = Depends(get_conversation_service)
):
    """Update conversation AI insights."""
    try:
        success = await conversation_service.update_conversation_ai_insights(
            tenant_id="default",
            conversation_id=conversation_id,
            ai_insights=request.ai_insights
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found or update failed")
        
        return {
            "success": True,
            "message": "AI insights updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update AI insights: {str(e)}")


@router.post("/{conversation_id}/tags")
async def add_tags(
    conversation_id: str,
    request: AddTagsRequest,
    
    
    conversation_service: WebUIConversationService = Depends(get_conversation_service)
):
    """Add tags to conversation."""
    try:
        success = await conversation_service.add_conversation_tags(
            tenant_id="default",
            conversation_id=conversation_id,
            tags=request.tags
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found or update failed")
        
        return {
            "success": True,
            "message": f"Added {len(request.tags)} tags to conversation"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add tags: {str(e)}")


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    active_only: bool = Query(True, description="Only return active conversations"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of conversations"),
    offset: int = Query(0, ge=0, description="Number of conversations to skip"),
    
    
    conversation_service: WebUIConversationService = Depends(get_conversation_service)
):
    """List conversations for current user."""
    try:
        conversations = await conversation_service.base_manager.list_conversations(
            tenant_id="default",
            user_id="anonymous",
            active_only=active_only,
            limit=limit,
            offset=offset
        )
        
        # Convert to web UI conversations
        web_ui_conversations = []
        for conv in conversations:
            # Get web UI data for each conversation
            web_ui_data = await conversation_service._get_web_ui_conversation_data(
                tenant_id, conv.id
            )
            
            web_ui_conv = await conversation_service._convert_to_web_ui_conversation(
                conv,
                web_ui_data.get("session_id"),
                web_ui_data.get("ui_context", {}),
                web_ui_data.get("user_settings", {}),
                web_ui_data.get("tags", []),
                ConversationPriority(web_ui_data.get("priority", "normal")),
                web_ui_data.get("summary"),
                web_ui_data.get("last_ai_response_id")
            )
            
            web_ui_conversations.append(_convert_conversation_to_response(web_ui_conv))
        
        return ConversationListResponse(
            conversations=web_ui_conversations,
            total_count=len(web_ui_conversations),
            has_more=len(web_ui_conversations) == limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")


@router.put("/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    title: Optional[str] = Query(None, description="New title"),
    is_active: Optional[bool] = Query(None, description="Active status"),
    
    
    conversation_service: WebUIConversationService = Depends(get_conversation_service)
):
    """Update conversation properties."""
    try:
        success = await conversation_service.base_manager.update_conversation(
            tenant_id="default",
            conversation_id=conversation_id,
            title=title,
            is_active=is_active
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found or update failed")
        
        return {
            "success": True,
            "message": "Conversation updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update conversation: {str(e)}")


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    
    
    conversation_service: WebUIConversationService = Depends(get_conversation_service)
):
    """Delete a conversation."""
    try:
        success = await conversation_service.base_manager.delete_conversation(
            tenant_id="default",
            conversation_id=conversation_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found or deletion failed")
        
        return {
            "success": True,
            "message": "Conversation deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    time_range_start: Optional[datetime] = Query(None, description="Start of time range"),
    time_range_end: Optional[datetime] = Query(None, description="End of time range"),
    
    
    conversation_service: WebUIConversationService = Depends(get_conversation_service)
):
    """Get conversation analytics for dashboard."""
    try:
        # Build time range tuple if provided
        time_range = None
        if time_range_start and time_range_end:
            time_range = (time_range_start, time_range_end)
        
        # Use current user if no user_id specified
        target_user_id = user_id or "anonymous"
        
        analytics = await conversation_service.get_conversation_analytics(
            tenant_id="default",
            user_id=target_user_id,
            time_range=time_range
        )
        
        return AnalyticsResponse(**analytics)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/stats")
async def get_conversation_stats(
    
    
    conversation_service: WebUIConversationService = Depends(get_conversation_service)
):
    """Get basic conversation statistics."""
    try:
        stats = await conversation_service.base_manager.get_conversation_stats(
            tenant_id, "anonymous"
        )
        web_ui_metrics = conversation_service.get_metrics()
        
        return {
            "base_stats": stats,
            "web_ui_metrics": web_ui_metrics,
            "tenant_id": tenant_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/cleanup-inactive")
async def cleanup_inactive_conversations(
    days_inactive: int = Query(30, ge=1, description="Days of inactivity threshold"),
    
    
    conversation_service: WebUIConversationService = Depends(get_conversation_service)
):
    """Mark old conversations as inactive."""
    try:
        count = await conversation_service.base_manager.cleanup_inactive_conversations(
            tenant_id="default",
            days_inactive=days_inactive
        )
        
        return {
            "success": True,
            "inactive_count": count,
            "message": f"Marked {count} conversations as inactive"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup conversations: {str(e)}")


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for conversation service."""
    return {
        "status": "healthy",
        "service": "conversation",
        "timestamp": datetime.utcnow().isoformat()
    }