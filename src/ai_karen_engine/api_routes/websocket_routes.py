"""
WebSocket API Routes for Real-Time Chat Communication

This module provides WebSocket endpoints for real-time chat functionality,
including connection management, streaming responses, and fallback to
Server-Sent Events when WebSocket is not available.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse

try:
    from sse_starlette.sse import EventSourceResponse
except ImportError:
    # Fallback for EventSourceResponse if sse_starlette is not available
    class EventSourceResponse:
        def __init__(self, content): 
            self.content = content

try:
    from pydantic import BaseModel, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field

from ai_karen_engine.chat.websocket_gateway import WebSocketGateway, WebSocketMessage, MessageType
from ai_karen_engine.chat.stream_processor import StreamProcessor
from ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator, ChatRequest
from ai_karen_engine.utils.auth import validate_session
from ai_karen_engine.hooks import get_hook_manager, HookTypes, HookContext

logger = logging.getLogger(__name__)

# Global instances (will be initialized by dependency injection)
websocket_gateway: Optional[WebSocketGateway] = None
stream_processor: Optional[StreamProcessor] = None
chat_orchestrator: Optional[ChatOrchestrator] = None

router = APIRouter(prefix="/api/ws", tags=["websocket"])


# Request/Response Models
class StreamChatRequest(BaseModel):
    """Request model for streaming chat via HTTP/SSE."""
    message: str = Field(..., description="User message")
    conversation_id: str = Field(..., description="Conversation ID")
    user_id: str = Field(..., description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    stream_type: str = Field("sse", description="Stream type: sse or http")
    include_context: bool = Field(True, description="Include memory context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class StreamStatusResponse(BaseModel):
    """Response model for stream status."""
    session_id: str
    status: str
    stream_type: str
    started_at: str
    chunks_sent: int
    bytes_sent: int
    processing_time: float
    user_id: Optional[str]
    conversation_id: Optional[str]


class WebSocketStatsResponse(BaseModel):
    """Response model for WebSocket statistics."""
    total_connections: int
    authenticated_connections: int
    unique_users: int
    active_conversations: int
    typing_users: int
    online_users: int
    queue_stats: Dict[str, Any]


class StreamMetricsResponse(BaseModel):
    """Response model for streaming metrics."""
    total_streams: int
    successful_streams: int
    failed_streams: int
    success_rate: float
    avg_stream_duration: float
    avg_processing_time: float
    active_sessions: int


# Dependency injection functions
def get_websocket_gateway() -> WebSocketGateway:
    """Get WebSocket gateway instance."""
    global websocket_gateway
    if websocket_gateway is None:
        # Initialize with default chat orchestrator
        from ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator
        from ai_karen_engine.chat.memory_processor import MemoryProcessor
        from ai_karen_engine.services.nlp_service_manager import nlp_service_manager
        
        # Create memory processor
        memory_processor = MemoryProcessor(
            spacy_service=nlp_service_manager.spacy_service,
            distilbert_service=nlp_service_manager.distilbert_service,
            memory_manager=None  # Will be injected later
        )
        
        # Create chat orchestrator
        chat_orch = ChatOrchestrator(memory_processor=memory_processor)
        
        # Create WebSocket gateway
        websocket_gateway = WebSocketGateway(chat_orch)
    
    return websocket_gateway


def get_stream_processor() -> StreamProcessor:
    """Get stream processor instance."""
    global stream_processor
    if stream_processor is None:
        # Initialize with default chat orchestrator
        from ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator
        from ai_karen_engine.chat.memory_processor import MemoryProcessor
        from ai_karen_engine.services.nlp_service_manager import nlp_service_manager
        
        # Create memory processor
        memory_processor = MemoryProcessor(
            spacy_service=nlp_service_manager.spacy_service,
            distilbert_service=nlp_service_manager.distilbert_service,
            memory_manager=None  # Will be injected later
        )
        
        # Create chat orchestrator
        chat_orch = ChatOrchestrator(memory_processor=memory_processor)
        
        # Create stream processor
        stream_processor = StreamProcessor(chat_orch)
    
    return stream_processor


# WebSocket endpoint
@router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    gateway: WebSocketGateway = Depends(get_websocket_gateway)
):
    """
    WebSocket endpoint for real-time chat communication.
    
    Features:
    - Real-time bidirectional communication
    - Authentication and session management
    - Typing indicators and presence
    - Message queuing for offline scenarios
    - Connection recovery and reconnection logic
    """
    connection_id = None
    
    try:
        # Handle WebSocket connection
        connection_id = await gateway.handle_websocket_connection(websocket)
        logger.info(f"WebSocket chat session completed: {connection_id}")
        
    except WebSocketDisconnect as e:
        logger.info(f"WebSocket disconnected: {connection_id} (code: {e.code})")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        if connection_id:
            logger.debug(f"WebSocket connection cleanup: {connection_id}")


# Server-Sent Events endpoint
@router.post("/stream/sse")
async def stream_chat_sse(
    request: StreamChatRequest,
    http_request: Request,
    processor: StreamProcessor = Depends(get_stream_processor)
) -> EventSourceResponse:
    """
    Server-Sent Events endpoint for streaming chat responses.
    
    This provides a fallback for clients that cannot use WebSocket connections.
    """
    try:
        # Create chat request
        chat_request = ChatRequest(
            message=request.message,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            session_id=request.session_id,
            stream=True,
            include_context=request.include_context,
            metadata=request.metadata
        )
        
        # Create SSE stream
        return await processor.create_sse_stream(chat_request, http_request)
        
    except Exception as e:
        logger.error(f"Error creating SSE stream: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create stream: {str(e)}")


# HTTP streaming endpoint
@router.post("/stream/http")
async def stream_chat_http(
    request: StreamChatRequest,
    http_request: Request,
    processor: StreamProcessor = Depends(get_stream_processor)
) -> StreamingResponse:
    """
    HTTP streaming endpoint for streaming chat responses.
    
    Returns NDJSON (newline-delimited JSON) stream.
    """
    try:
        # Create chat request
        chat_request = ChatRequest(
            message=request.message,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            session_id=request.session_id,
            stream=True,
            include_context=request.include_context,
            metadata=request.metadata
        )
        
        # Create HTTP stream
        return await processor.create_http_stream(chat_request, http_request)
        
    except Exception as e:
        logger.error(f"Error creating HTTP stream: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create stream: {str(e)}")


# Stream management endpoints
@router.get("/stream/{session_id}/status", response_model=StreamStatusResponse)
async def get_stream_status(
    session_id: str,
    processor: StreamProcessor = Depends(get_stream_processor)
):
    """Get status information for a streaming session."""
    status = await processor.get_stream_status(session_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Stream session not found")
    
    return StreamStatusResponse(**status)


@router.post("/stream/{session_id}/pause")
async def pause_stream(
    session_id: str,
    processor: StreamProcessor = Depends(get_stream_processor)
):
    """Pause a streaming session."""
    success = await processor.pause_stream(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Stream session not found")
    
    return {"success": True, "message": f"Stream {session_id} paused"}


@router.post("/stream/{session_id}/resume")
async def resume_stream(
    session_id: str,
    processor: StreamProcessor = Depends(get_stream_processor)
):
    """Resume a paused streaming session."""
    success = await processor.resume_stream(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Stream session not found")
    
    return {"success": True, "message": f"Stream {session_id} resumed"}


@router.post("/stream/{session_id}/cancel")
async def cancel_stream(
    session_id: str,
    processor: StreamProcessor = Depends(get_stream_processor)
):
    """Cancel a streaming session."""
    success = await processor.cancel_stream(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Stream session not found")
    
    return {"success": True, "message": f"Stream {session_id} cancelled"}


@router.post("/stream/{session_id}/recover")
async def recover_stream(
    session_id: str,
    from_sequence: Optional[int] = Query(None, description="Sequence number to resume from"),
    processor: StreamProcessor = Depends(get_stream_processor)
):
    """Recover an interrupted streaming session."""
    success = await processor.recover_stream(session_id, from_sequence)
    
    if not success:
        raise HTTPException(status_code=404, detail="Stream session not found or recovery failed")
    
    return {"success": True, "message": f"Stream {session_id} recovery initiated"}


# Statistics and monitoring endpoints
@router.get("/stats", response_model=WebSocketStatsResponse)
async def get_websocket_stats(
    gateway: WebSocketGateway = Depends(get_websocket_gateway)
):
    """Get WebSocket connection statistics."""
    stats = gateway.get_connection_stats()
    return WebSocketStatsResponse(**stats)


@router.get("/stream/metrics", response_model=StreamMetricsResponse)
async def get_stream_metrics(
    processor: StreamProcessor = Depends(get_stream_processor)
):
    """Get streaming performance metrics."""
    metrics = processor.get_performance_metrics()
    active_sessions = processor.get_active_session_count()
    
    return StreamMetricsResponse(
        total_streams=metrics["total_streams"],
        successful_streams=metrics["successful_streams"],
        failed_streams=metrics["failed_streams"],
        success_rate=metrics["success_rate"],
        avg_stream_duration=metrics["avg_stream_duration"],
        avg_processing_time=metrics["avg_processing_time"],
        active_sessions=active_sessions
    )


@router.get("/stream/active")
async def list_active_streams(
    processor: StreamProcessor = Depends(get_stream_processor)
):
    """List all active streaming sessions."""
    active_streams = await processor.list_active_streams()
    return {
        "active_streams": active_streams,
        "total_count": len(active_streams)
    }


# User presence endpoints
@router.get("/presence/{user_id}")
async def get_user_presence(
    user_id: str,
    gateway: WebSocketGateway = Depends(get_websocket_gateway)
):
    """Get presence information for a user."""
    presence = gateway.presence_manager.get_presence(user_id)
    return {
        "user_id": user_id,
        "presence": presence
    }


@router.get("/presence/online")
async def get_online_users(
    gateway: WebSocketGateway = Depends(get_websocket_gateway)
):
    """Get list of online users."""
    online_users = gateway.presence_manager.get_online_users()
    return {
        "online_users": online_users,
        "count": len(online_users)
    }


# Typing indicators endpoints
@router.get("/typing/{conversation_id}")
async def get_typing_users(
    conversation_id: str,
    gateway: WebSocketGateway = Depends(get_websocket_gateway)
):
    """Get users currently typing in a conversation."""
    typing_users = gateway.typing_manager.get_typing_users(conversation_id)
    return {
        "conversation_id": conversation_id,
        "typing_users": typing_users,
        "count": len(typing_users)
    }


# Message queue endpoints
@router.get("/queue/{user_id}")
async def get_queued_messages(
    user_id: str,
    gateway: WebSocketGateway = Depends(get_websocket_gateway)
):
    """Get queued messages for a user."""
    queued_messages = await gateway.message_queue.get_queued_messages(user_id)
    
    return {
        "user_id": user_id,
        "queued_messages": [
            {
                "message_id": msg.message.message_id,
                "type": msg.message.type.value,
                "content": msg.message.data,
                "queued_at": msg.queued_at.isoformat(),
                "expires_at": msg.expires_at.isoformat() if msg.expires_at else None,
                "delivery_attempts": msg.delivery_attempts
            }
            for msg in queued_messages
        ],
        "count": len(queued_messages)
    }


@router.delete("/queue/{user_id}")
async def clear_queued_messages(
    user_id: str,
    gateway: WebSocketGateway = Depends(get_websocket_gateway)
):
    """Clear all queued messages for a user."""
    await gateway.message_queue.clear_queued_messages(user_id)
    
    return {
        "success": True,
        "message": f"Cleared queued messages for user {user_id}"
    }


# Connection management endpoints
@router.get("/connections/{user_id}")
async def get_user_connections(
    user_id: str,
    gateway: WebSocketGateway = Depends(get_websocket_gateway)
):
    """Get all active connections for a user."""
    connections = gateway.get_user_connections(user_id)
    
    return {
        "user_id": user_id,
        "connections": connections,
        "count": len(connections)
    }


@router.get("/connections/conversation/{conversation_id}")
async def get_conversation_connections(
    conversation_id: str,
    gateway: WebSocketGateway = Depends(get_websocket_gateway)
):
    """Get all active connections for a conversation."""
    connections = gateway.get_conversation_connections(conversation_id)
    
    return {
        "conversation_id": conversation_id,
        "connections": connections,
        "count": len(connections)
    }


# Health check endpoint
@router.get("/health")
async def websocket_health_check():
    """Health check for WebSocket services."""
    try:
        gateway = get_websocket_gateway()
        processor = get_stream_processor()
        
        gateway_stats = gateway.get_connection_stats()
        stream_metrics = processor.get_performance_metrics()
        
        return {
            "status": "healthy",
            "websocket_gateway": {
                "status": "running",
                "connections": gateway_stats["total_connections"],
                "authenticated_users": gateway_stats["unique_users"]
            },
            "stream_processor": {
                "status": "running",
                "active_streams": processor.get_active_session_count(),
                "success_rate": stream_metrics["success_rate"]
            },
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }


# Initialize services on module import
def initialize_websocket_services():
    """Initialize WebSocket services."""
    global websocket_gateway, stream_processor
    
    try:
        # Get instances to trigger initialization
        get_websocket_gateway()
        get_stream_processor()
        
        logger.info("WebSocket services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize WebSocket services: {e}")


# Initialize on import
initialize_websocket_services()