"""
FastAPI routes for AI-Karen chat system with security and authentication.
Integrates production FastAPI routes with canonical chat service architecture.
"""

import logging
import time
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Request,
    UploadFile,
    File,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime

from ai_karen_engine.chat.dependencies import (
    get_chat_orchestrator_dependency,
    get_memory_service,
)
from ai_karen_engine.chat.security import (
    validate_file_upload,
    sanitize_filename,
    get_content_validator,
    SecurityLevel,
    ValidationResult,
)
from ai_karen_engine.chat.conversation_models import Conversation, Message

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/conversations", response_model=Dict[str, Any])
async def create_conversation(
    request: Request,
    title: str = Query(..., description="Conversation title"),
    description: Optional[str] = Query(None, description="Conversation description"),
    security_level: SecurityLevel = Query(
        SecurityLevel.MEDIUM, description="Security level for conversation"
    ),
    orchestrator=Depends(get_chat_orchestrator_dependency),
):
    """Create a new conversation."""
    try:
        # Minimal validation - only required fields
        if not title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Title is required"
            )

        # Create conversation through orchestrator
        conversation_data = {
            "title": title,
            "description": description,
            "user_id": request.state.user_id
            if hasattr(request.state, "user_id")
            else None,
            "security_level": security_level.value,
        }

        conversation = await orchestrator.create_conversation(conversation_data)

        return {
            "success": True,
            "conversation": {
                "id": conversation.id,
                "title": conversation.title,
                "description": conversation.description,
                "created_at": conversation.created_at,
                "security_level": conversation.security_level,
            },
        }

    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/conversations", response_model=Dict[str, Any])
async def list_conversations(
    request: Request,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of conversations"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    orchestrator=Depends(get_chat_orchestrator_dependency),
):
    """List user conversations."""
    try:
        # Get user ID from request state
        user_id = request.state.user_id if hasattr(request.state, "user_id") else None

        # List conversations through orchestrator
        conversations = await orchestrator.list_conversations(
            user_id=user_id, limit=limit, offset=offset
        )

        return {
            "success": True,
            "conversations": [
                {
                    "id": conv.id,
                    "title": conv.title,
                    "description": conv.description,
                    "created_at": conv.created_at,
                    "updated_at": conv.updated_at,
                    "message_count": conv.message_count
                    if hasattr(conv, "message_count")
                    else 0,
                }
                for conv in conversations
            ],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(conversations),
            },
        }

    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/conversations/{conversation_id}", response_model=Dict[str, Any])
async def get_conversation(
    conversation_id: str, orchestrator=Depends(get_chat_orchestrator_dependency)
):
    """Get a specific conversation."""
    try:
        conversation = await orchestrator.get_conversation(conversation_id)

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )

        return {
            "success": True,
            "conversation": {
                "id": conversation.id,
                "title": conversation.title,
                "description": conversation.description,
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at,
                "messages": [
                    {
                        "id": msg.id,
                        "content": msg.content,
                        "role": msg.role,
                        "created_at": msg.created_at,
                    }
                    for msg in conversation.messages
                ],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/conversations/{conversation_id}/messages", response_model=Dict[str, Any])
async def send_message(
    request: Request,
    conversation_id: str,
    content: str,
    role: str = Query("user", description="Message role (user or assistant)"),
    security_level: SecurityLevel = Query(
        SecurityLevel.MEDIUM, description="Security level for message"
    ),
    orchestrator=Depends(get_chat_orchestrator_dependency),
):
    """Send a message in a conversation."""
    try:
        # Minimal validation - only required fields
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Content is required"
            )

        # Get user ID from request state
        user_id = request.state.user_id if hasattr(request.state, "user_id") else None

        # Send message through orchestrator
        message_data = {
            "conversation_id": conversation_id,
            "content": content,
            "role": role,
            "user_id": user_id,
            "security_level": security_level.value,
        }

        message = await orchestrator.send_message(message_data)

        return {
            "success": True,
            "message": {
                "id": message.id,
                "content": message.content,
                "role": message.role,
                "created_at": message.created_at,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/conversations/{conversation_id}/messages", response_model=Dict[str, Any])
async def get_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum number of messages"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    orchestrator=Depends(get_chat_orchestrator_dependency),
):
    """Get messages in a conversation."""
    try:
        messages = await orchestrator.get_messages(
            conversation_id=conversation_id, limit=limit, offset=offset
        )

        return {
            "success": True,
            "messages": [
                {
                    "id": msg.id,
                    "content": msg.content,
                    "role": msg.role,
                    "created_at": msg.created_at,
                }
                for msg in messages
            ],
            "pagination": {"limit": limit, "offset": offset, "total": len(messages)},
        }

    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/conversations/{conversation_id}/files", response_model=Dict[str, Any])
async def upload_file(
    request: Request,
    conversation_id: str,
    file: UploadFile = File(...),
    security_level: SecurityLevel = Query(
        SecurityLevel.MEDIUM, description="Security level for file"
    ),
    orchestrator=Depends(get_chat_orchestrator_dependency),
):
    """Upload a file to a conversation."""
    try:
        # Read file and sanitize filename
        file_data = await file.read()
        filename = sanitize_filename(file.filename)

        # Get user ID from request state
        user_id = request.state.user_id if hasattr(request.state, "user_id") else None

        # Upload file through orchestrator
        file_data = {
            "conversation_id": conversation_id,
            "filename": filename,
            "content": file_data,
            "content_type": file.content_type,
            "user_id": user_id,
            "security_level": security_level.value,
        }

        uploaded_file = await orchestrator.upload_file(file_data)

        return {
            "success": True,
            "file": {
                "id": uploaded_file.id,
                "filename": uploaded_file.filename,
                "content_type": uploaded_file.content_type,
                "size": uploaded_file.size,
                "created_at": uploaded_file.created_at,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/conversations/{conversation_id}/stream", response_class=StreamingResponse)
async def stream_conversation(
    request: Request,
    conversation_id: str,
    message: str,
    orchestrator=Depends(get_chat_orchestrator_dependency),
):
    """Stream conversation responses."""
    try:
        # Get user ID from request state
        user_id = request.state.user_id if hasattr(request.state, "user_id") else None

        # Create async generator for streaming
        async def generate_response():
            try:
                async for chunk in orchestrator.stream_response(
                    conversation_id=conversation_id, message=message, user_id=user_id
                ):
                    yield f"data: {chunk}\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f'data: {{"error": "{str(e)}"}}\n\n'

        return StreamingResponse(generate_response(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Failed to start streaming: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete("/conversations/{conversation_id}", response_model=Dict[str, Any])
async def delete_conversation(
    conversation_id: str, orchestrator=Depends(get_chat_orchestrator_dependency)
):
    """Delete a conversation."""
    try:
        success = await orchestrator.delete_conversation(conversation_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )

        return {"success": True, "message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/health", response_model=Dict[str, Any])
async def chat_health_check():
    """Health check for chat system."""
    try:
        memory_service = get_memory_service()

        return {
            "success": True,
            "status": "healthy",
            "services": {"memory": "available" if memory_service else "unavailable"},
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
