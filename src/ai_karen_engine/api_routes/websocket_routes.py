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
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Dict, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import StreamingResponse

from ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator, ChatRequest
from ai_karen_engine.chat.stream_processor import StreamProcessor
from ai_karen_engine.chat.websocket_gateway import WebSocketGateway
# REMOVED: Complex auth service - replaced with simple auth
from ai_karen_engine.utils.dependency_checks import import_pydantic

try:
    from sse_starlette.sse import EventSourceResponse
except ImportError:  # pragma: no cover - optional dependency
    # Fallback for EventSourceResponse if sse_starlette is not available
    class EventSourceResponse:  # type: ignore
        def __init__(self, content):
            self.content = content


BaseModel, Field = import_pydantic("BaseModel", "Field")

logger = logging.getLogger(__name__)

# Global instances (will be initialized by dependency injection)
websocket_gateway: Optional[WebSocketGateway] = None
stream_processor: Optional[StreamProcessor] = None
chat_orchestrator: Optional[ChatOrchestrator] = None

router = APIRouter(tags=["websocket"])

# Model operation event types
MODEL_OPERATION_EVENTS = {
    "JOB_STARTED": "job_started",
    "JOB_PROGRESS": "job_progress", 
    "JOB_COMPLETED": "job_completed",
    "JOB_FAILED": "job_failed",
    "JOB_CANCELLED": "job_cancelled",
    "MODEL_DOWNLOADED": "model_downloaded",
    "MODEL_REMOVED": "model_removed",
    "MIGRATION_STARTED": "migration_started",
    "MIGRATION_COMPLETED": "migration_completed",
    "GC_STARTED": "gc_started",
    "GC_COMPLETED": "gc_completed"
}


# Request/Response Models
class StreamChatRequest(BaseModel):
    """Request model for streaming chat via HTTP/SSE."""

    message: str = Field(..., description="User message")
    conversation_id: str = Field(..., description="Conversation ID")
    user_id: str = Field(..., description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    stream_type: str = Field("sse", description="Stream type: sse or http")
    include_context: bool = Field(True, description="Include memory context")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


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
@lru_cache
def get_chat_orchestrator() -> ChatOrchestrator:
    """Create or return the chat orchestrator instance."""
    from ai_karen_engine.chat.memory_processor import MemoryProcessor
    from ai_karen_engine.services.nlp_service_manager import nlp_service_manager
    from ai_karen_engine.database.memory_manager import MemoryManager
    from ai_karen_engine.database.client import MultiTenantPostgresClient
    from ai_karen_engine.core.milvus_client import MilvusClient
    from ai_karen_engine.core import default_models

    try:
        # Initialize required components for memory manager
        db_client = MultiTenantPostgresClient()
        milvus_client = MilvusClient()
        
        # Load embedding manager (async operation handled gracefully)
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, we can't await here
                # Use a fallback or initialize without embedding manager
                embedding_manager = None
            else:
                loop.run_until_complete(default_models.load_default_models())
                embedding_manager = default_models.get_embedding_manager()
        except Exception as e:
            logger.warning(f"Failed to load embedding manager: {e}")
            embedding_manager = None
        
        # Create memory manager instance
        memory_manager = MemoryManager(
            db_client=db_client,
            milvus_client=milvus_client,
            embedding_manager=embedding_manager
        )
    except Exception as e:
        logger.warning(f"Failed to create memory manager: {e}")
        memory_manager = None

    memory_processor = MemoryProcessor(
        spacy_service=nlp_service_manager.spacy_service,
        distilbert_service=nlp_service_manager.distilbert_service,
        memory_manager=memory_manager,
    )

    return ChatOrchestrator(memory_processor=memory_processor)


@lru_cache
def get_websocket_gateway() -> WebSocketGateway:
    """Get WebSocket gateway instance."""
    return WebSocketGateway(get_chat_orchestrator())


@lru_cache
def get_stream_processor() -> StreamProcessor:
    """Get stream processor instance."""
    return StreamProcessor(get_chat_orchestrator())


async def get_current_user_websocket(websocket: WebSocket) -> Dict[str, Any]:
    """Authenticate WebSocket connections using configured session cookie or JWT.

    Prefers the configured auth session cookie name; falls back to legacy
    'kari_session' for backward compatibility. Also accepts Bearer access tokens
    via the Authorization header.
    """
    # Resolve configured session cookie name
    try:
        from ai_karen_engine.auth.cookie_manager import get_cookie_manager
        cm = get_cookie_manager()
        configured_cookie = getattr(cm.config, 'session_cookie', 'auth_session')
    except Exception:
        configured_cookie = 'auth_session'

    # Check configured session cookie first, then legacy name
    session_token = (
        websocket.cookies.get(configured_cookie)
        or websocket.cookies.get("kari_session")
    )
    # Use production auth service for JWT validation
    auth_header = websocket.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header.split(" ", 1)[1]
        try:
            from src.auth.auth_service import get_auth_service, user_account_to_dict

            service = await get_auth_service()
            user = await service.validate_token(access_token)
            if user:
                return user_account_to_dict(user)
        except Exception:
            logger.exception("Failed to validate websocket token")

    raise HTTPException(status_code=401, detail="Authentication required")


# WebSocket endpoint
@router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    gateway: WebSocketGateway = Depends(get_websocket_gateway),
    current_user: Dict[str, Any] = Depends(get_current_user_websocket),
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
        logger.info(
            "WebSocket chat session completed",
            extra={"connection_id": connection_id, "user": current_user.get("user_id")},
        )

    except WebSocketDisconnect as e:
        logger.info(f"WebSocket disconnected: {connection_id} (code: {e.code})")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        if connection_id:
            logger.debug(f"WebSocket connection cleanup: {connection_id}")


@router.websocket("/models/events")
async def websocket_model_events_endpoint(
    websocket: WebSocket,
    gateway: WebSocketGateway = Depends(get_websocket_gateway),
    current_user: Dict[str, Any] = Depends(get_current_user_websocket),
):
    """
    WebSocket endpoint for real-time model operation events.
    
    Features:
    - Real-time job progress updates
    - Model download/installation notifications
    - Migration and garbage collection status
    - Error notifications and recovery suggestions
    
    Requirements: 3.8, 9.3, 9.6
    """
    connection_id = None
    
    try:
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        
        # Register connection for model events
        user_id = current_user.get("user_id", "anonymous")
        
        # Subscribe to model orchestrator events via event bus
        from ai_karen_engine.event_bus import get_event_bus
        event_bus = get_event_bus()
        
        # Create event handler for this connection
        async def handle_model_event(event_data):
            """Handle model orchestrator events and forward to WebSocket."""
            try:
                message = {
                    "type": "model_event",
                    "event": event_data.get("event_type"),
                    "data": event_data.get("payload", {}),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                await websocket.send_text(json.dumps(message))
                logger.debug(f"Sent model event to {connection_id}: {event_data.get('event_type')}")
                
            except Exception as e:
                logger.error(f"Failed to send model event to {connection_id}: {e}")
        
        # Subscribe to model orchestrator events
        event_bus.subscribe("model_orchestrator", handle_model_event)
        
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "connection_id": connection_id,
            "user_id": user_id,
            "subscribed_events": ["model_orchestrator"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))
        
        logger.info(f"Model events WebSocket connected: {connection_id} for user {user_id}")
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }))
                    
                elif message_type == "subscribe_job":
                    # Subscribe to specific job updates
                    job_id = message.get("job_id")
                    if job_id:
                        # In a real implementation, this would register for specific job updates
                        await websocket.send_text(json.dumps({
                            "type": "job_subscription_confirmed",
                            "job_id": job_id,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }))
                        logger.debug(f"Subscribed to job {job_id} for connection {connection_id}")
                
                elif message_type == "unsubscribe_job":
                    # Unsubscribe from specific job updates
                    job_id = message.get("job_id")
                    if job_id:
                        await websocket.send_text(json.dumps({
                            "type": "job_unsubscription_confirmed", 
                            "job_id": job_id,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }))
                        logger.debug(f"Unsubscribed from job {job_id} for connection {connection_id}")
                
                else:
                    logger.warning(f"Unknown message type from {connection_id}: {message_type}")
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from {connection_id}: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }))
            except Exception as e:
                logger.error(f"Error handling message from {connection_id}: {e}")
                break
                
    except WebSocketDisconnect as e:
        logger.info(f"Model events WebSocket disconnected: {connection_id} (code: {e.code})")
    except Exception as e:
        logger.error(f"Model events WebSocket error: {e}", exc_info=True)
    finally:
        if connection_id:
            # Unsubscribe from events
            try:
                event_bus = get_event_bus()
                # In a real implementation, we'd properly unsubscribe the handler
                logger.debug(f"Model events WebSocket connection cleanup: {connection_id}")
            except Exception as e:
                logger.error(f"Error during WebSocket cleanup: {e}")


# Server-Sent Events endpoint
@router.post("/stream/sse", response_model=None)
async def stream_chat_sse(
    request: StreamChatRequest,
    http_request: Request,
    processor: StreamProcessor = Depends(get_stream_processor),
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
            metadata=request.metadata,
        )

        # Create SSE stream
        return await processor.create_sse_stream(chat_request, http_request)

    except Exception as e:
        logger.error(f"Error creating SSE stream: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create stream: {str(e)}"
        )


@router.get("/models/events/sse")
async def model_events_sse(
    http_request: Request,
    job_id: Optional[str] = Query(None, description="Specific job ID to track"),
    current_user: Dict[str, Any] = Depends(get_current_user_websocket),
) -> EventSourceResponse:
    """
    Server-Sent Events endpoint for model operation events.
    
    This provides a fallback for clients that cannot use WebSocket connections.
    
    Requirements: 3.8, 9.3, 9.6
    """
    try:
        user_id = current_user.get("user_id", "anonymous")
        
        async def event_generator():
            """Generate SSE events for model operations."""
            try:
                # Import here to avoid circular imports
                from ai_karen_engine.event_bus import get_event_bus
                
                # Send initial connection event
                yield {
                    "event": "connected",
                    "data": json.dumps({
                        "type": "connection_established",
                        "user_id": user_id,
                        "job_id": job_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                }
                
                # Set up event subscription
                event_bus = get_event_bus()
                received_events = []
                
                # Create event handler
                async def handle_event(event_data):
                    """Handle model orchestrator events."""
                    try:
                        # Filter by job_id if specified
                        if job_id and event_data.get("payload", {}).get("job_id") != job_id:
                            return
                            
                        event_message = {
                            "type": "model_event",
                            "event": event_data.get("event_type"),
                            "data": event_data.get("payload", {}),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        
                        received_events.append(event_message)
                        
                    except Exception as e:
                        logger.error(f"Error handling SSE event: {e}")
                
                # Subscribe to events
                event_bus.subscribe("model_orchestrator", handle_event)
                
                # Keep connection alive and send events
                last_heartbeat = datetime.now()
                
                while True:
                    try:
                        # Check for client disconnect
                        if await http_request.is_disconnected():
                            break
                        
                        # Send any received events
                        while received_events:
                            event = received_events.pop(0)
                            yield {
                                "event": "model_event",
                                "data": json.dumps(event)
                            }
                        
                        # Send heartbeat every 30 seconds
                        now = datetime.now()
                        if (now - last_heartbeat).total_seconds() > 30:
                            yield {
                                "event": "heartbeat",
                                "data": json.dumps({
                                    "type": "heartbeat",
                                    "timestamp": now.isoformat()
                                })
                            }
                            last_heartbeat = now
                        
                        # Small delay to prevent busy waiting
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        logger.error(f"Error in SSE event loop: {e}")
                        break
                        
            except Exception as e:
                logger.error(f"Error in SSE event generator: {e}")
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "type": "error",
                        "message": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                }
        
        return EventSourceResponse(event_generator())
        
    except Exception as e:
        logger.error(f"Error creating model events SSE stream: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create event stream: {str(e)}"
        )


# HTTP streaming endpoint
@router.post("/stream/http")
async def stream_chat_http(
    request: StreamChatRequest,
    http_request: Request,
    processor: StreamProcessor = Depends(get_stream_processor),
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
            metadata=request.metadata,
        )

        # Create HTTP stream
        return await processor.create_http_stream(chat_request, http_request)

    except Exception as e:
        logger.error(f"Error creating HTTP stream: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create stream: {str(e)}"
        )


# Stream management endpoints
@router.get("/stream/{session_id}/status", response_model=StreamStatusResponse)
async def get_stream_status(
    session_id: str, processor: StreamProcessor = Depends(get_stream_processor)
):
    """Get status information for a streaming session."""
    status = await processor.get_stream_status(session_id)

    if not status:
        raise HTTPException(status_code=404, detail="Stream session not found")

    return StreamStatusResponse(**status)


@router.post("/stream/{session_id}/pause")
async def pause_stream(
    session_id: str, processor: StreamProcessor = Depends(get_stream_processor)
):
    """Pause a streaming session."""
    success = await processor.pause_stream(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="Stream session not found")

    return {"success": True, "message": f"Stream {session_id} paused"}


@router.post("/stream/{session_id}/resume")
async def resume_stream(
    session_id: str, processor: StreamProcessor = Depends(get_stream_processor)
):
    """Resume a paused streaming session."""
    success = await processor.resume_stream(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="Stream session not found")

    return {"success": True, "message": f"Stream {session_id} resumed"}


@router.post("/stream/{session_id}/cancel")
async def cancel_stream(
    session_id: str, processor: StreamProcessor = Depends(get_stream_processor)
):
    """Cancel a streaming session."""
    success = await processor.cancel_stream(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="Stream session not found")

    return {"success": True, "message": f"Stream {session_id} cancelled"}


@router.post("/stream/{session_id}/recover")
async def recover_stream(
    session_id: str,
    from_sequence: Optional[int] = Query(
        None, description="Sequence number to resume from"
    ),
    processor: StreamProcessor = Depends(get_stream_processor),
):
    """Recover an interrupted streaming session."""
    success = await processor.recover_stream(session_id, from_sequence)

    if not success:
        raise HTTPException(
            status_code=404, detail="Stream session not found or recovery failed"
        )

    return {"success": True, "message": f"Stream {session_id} recovery initiated"}


# Statistics and monitoring endpoints
@router.get("/stats", response_model=WebSocketStatsResponse)
async def get_websocket_stats(
    gateway: WebSocketGateway = Depends(get_websocket_gateway),
):
    """Get WebSocket connection statistics."""
    stats = gateway.get_connection_stats()
    return WebSocketStatsResponse(**stats)


@router.get("/stream/metrics", response_model=StreamMetricsResponse)
async def get_stream_metrics(
    processor: StreamProcessor = Depends(get_stream_processor),
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
        active_sessions=active_sessions,
    )


@router.get("/stream/active")
async def list_active_streams(
    processor: StreamProcessor = Depends(get_stream_processor),
):
    """List all active streaming sessions."""
    active_streams = await processor.list_active_streams()
    return {"active_streams": active_streams, "total_count": len(active_streams)}


# User presence endpoints
@router.get("/presence/{user_id}")
async def get_user_presence(
    user_id: str, gateway: WebSocketGateway = Depends(get_websocket_gateway)
):
    """Get presence information for a user."""
    presence = gateway.presence_manager.get_presence(user_id)
    return {"user_id": user_id, "presence": presence}


@router.get("/presence/online")
async def get_online_users(gateway: WebSocketGateway = Depends(get_websocket_gateway)):
    """Get list of online users."""
    online_users = gateway.presence_manager.get_online_users()
    return {"online_users": online_users, "count": len(online_users)}


# Typing indicators endpoints
@router.get("/typing/{conversation_id}")
async def get_typing_users(
    conversation_id: str, gateway: WebSocketGateway = Depends(get_websocket_gateway)
):
    """Get users currently typing in a conversation."""
    typing_users = gateway.typing_manager.get_typing_users(conversation_id)
    return {
        "conversation_id": conversation_id,
        "typing_users": typing_users,
        "count": len(typing_users),
    }


# Message queue endpoints
@router.get("/queue/{user_id}")
async def get_queued_messages(
    user_id: str, gateway: WebSocketGateway = Depends(get_websocket_gateway)
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
                "delivery_attempts": msg.delivery_attempts,
            }
            for msg in queued_messages
        ],
        "count": len(queued_messages),
    }


@router.delete("/queue/{user_id}")
async def clear_queued_messages(
    user_id: str, gateway: WebSocketGateway = Depends(get_websocket_gateway)
):
    """Clear all queued messages for a user."""
    await gateway.message_queue.clear_queued_messages(user_id)

    return {"success": True, "message": f"Cleared queued messages for user {user_id}"}


# Connection management endpoints
@router.get("/connections/{user_id}")
async def get_user_connections(
    user_id: str, gateway: WebSocketGateway = Depends(get_websocket_gateway)
):
    """Get all active connections for a user."""
    connections = gateway.get_user_connections(user_id)

    return {"user_id": user_id, "connections": connections, "count": len(connections)}


@router.get("/connections/conversation/{conversation_id}")
async def get_conversation_connections(
    conversation_id: str, gateway: WebSocketGateway = Depends(get_websocket_gateway)
):
    """Get all active connections for a conversation."""
    connections = gateway.get_conversation_connections(conversation_id)

    return {
        "conversation_id": conversation_id,
        "connections": connections,
        "count": len(connections),
    }


# Health check endpoint
@router.get("/health")
async def websocket_health_check(
    gateway: WebSocketGateway = Depends(get_websocket_gateway),
    processor: StreamProcessor = Depends(get_stream_processor),
):
    """Health check for WebSocket services."""
    try:
        gateway_stats = gateway.get_connection_stats()
        stream_metrics = processor.get_performance_metrics()

        return {
            "status": "healthy",
            "websocket_gateway": {
                "status": "running",
                "connections": gateway_stats["total_connections"],
                "authenticated_users": gateway_stats["unique_users"],
            },
            "stream_processor": {
                "status": "running",
                "active_streams": processor.get_active_session_count(),
                "success_rate": stream_metrics["success_rate"],
            },
            "timestamp": datetime.now(timezone.utc),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc),
        }
