"""
FastAPI routes for production chat system with security and authentication.
"""

import logging
import time
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime

from .models import ChatConversation, ChatMessage, ChatProviderConfiguration
from .schemas import (
    CreateConversationRequest, UpdateConversationRequest, SendMessageRequest,
    ConversationResponse, MessageResponse, ProviderResponse,
    ConfigureProviderRequest, ConversationListResponse, MessageListResponse,
    ProviderListResponse, ErrorResponse, SuccessResponse, ConversationMetadata
)
from .services import ChatService, create_secure_chat_service, SecureChatService
from .providers.base import AIRequest
from .middleware import get_current_chat_user, require_chat_permission, require_chat_admin
from .security import (
    validate_file_upload, sanitize_filename, get_content_validator,
    SecurityLevel, ThreatLevel
)
from .monitoring import (
    record_chat_metric, start_chat_session, update_chat_session,
    end_chat_session, MetricType, log_security_event
)
from server.database_config import database_lifespan
from server.config import Settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/chat", tags=["chat"])


# Production-ready database session dependency

async def get_db_session():
    """Dependency to get database session instance."""
    # Use database lifespan context manager for proper session management
    settings = Settings()
    
    # Get database session from lifespan context
    async with database_lifespan(settings) as db_config:
        if db_config and db_config._database_manager:
            async with db_config._database_manager.get_session() as db_session:
                yield db_session
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available"
            )

async def get_chat_service():
    """Dependency to get secure chat service instance."""
    from .services import create_secure_chat_service
    settings = Settings()
    
    # Get database session
    async with database_lifespan(settings) as db_config:
        if db_config and db_config._database_manager:
            async with db_config._database_manager.get_session() as db_session:
                service = create_secure_chat_service(db_session)
                await service.initialize_providers()
                yield service
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available"
            )


async def get_current_user(
    request: Request,
    user_context: Dict[str, Any] = Depends(get_current_chat_user)
) -> Dict[str, Any]:
    """Get current authenticated user with enhanced context."""
    return user_context


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    http_request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    chat_service: SecureChatService = Depends(get_chat_service)
):
    """Create a new conversation with security validation."""
    try:
        user_id = current_user["user_id"]
        client_ip = getattr(http_request.state, 'client_ip', 'unknown')
        
        # Log security event
        await log_security_event(
            "conversation_creation_attempt",
            {
                "user_id": user_id,
                "title": request.title,
                "provider_id": request.metadata.provider_id if request.metadata else None
            },
            user_id=user_id,
            ip_address=client_ip,
            threat_level=ThreatLevel.LOW
        )
        
        # Create conversation with security validation
        conversation = await chat_service.create_conversation_secure(user_id, request)
        
        # Record metrics
        await record_chat_metric(MetricType.ACTIVE_USERS, 1, "count")
        
        return conversation
        
    except ValueError as e:
        # Handle validation errors
        await log_security_event(
            "conversation_creation_failed",
            {
                "user_id": current_user["user_id"],
                "error": str(e)
            },
            user_id=current_user["user_id"],
            ip_address=getattr(http_request.state, 'client_ip', 'unknown'),
            threat_level=ThreatLevel.MEDIUM
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation"
        )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """List user conversations with security validation."""
    try:
        user_id = current_user["user_id"]
        
        # Validate pagination parameters
        if limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit cannot exceed 100"
            )
        
        conversations = await chat_service.list_conversations(user_id, limit, offset)
        
        # Get total count for pagination
        total = len(conversations)
        
        return ConversationListResponse(
            conversations=conversations,
            total=total,
            page=(offset // limit) + 1,
            per_page=limit,
            has_next=offset + limit < total,
            has_prev=offset > 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations"
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get conversation details with authorization check."""
    try:
        user_id = current_user["user_id"]
        
        # Validate conversation ID format
        import re
        if not re.match(r'^[a-f0-9-]{36}$', conversation_id):
            await log_security_event(
                "invalid_conversation_id",
                {
                    "conversation_id": conversation_id,
                    "user_id": user_id
                },
                user_id=user_id,
                threat_level=ThreatLevel.MEDIUM
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation ID format"
            )
        
        conversation = await chat_service.get_conversation(conversation_id, user_id)
        
        if not conversation:
            await log_security_event(
                "unauthorized_conversation_access",
                {
                    "conversation_id": conversation_id,
                    "user_id": user_id
                },
                user_id=user_id,
                threat_level=ThreatLevel.HIGH
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return conversation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation"
        )


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: UpdateConversationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    chat_service: SecureChatService = Depends(get_chat_service)
):
    """Update conversation with security validation."""
    try:
        user_id = current_user["user_id"]
        
        # Validate conversation ID format
        import re
        if not re.match(r'^[a-f0-9-]{36}$', conversation_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation ID format"
            )
        
        # Get existing conversation
        result = await chat_service.db_session.execute(
            select(ChatConversation).where(
                ChatConversation.id == conversation_id
            )
        )
        existing_conversation = result.scalar_one_or_none()
        
        if not existing_conversation or existing_conversation.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Update conversation fields using SQLAlchemy update
        update_values = {}
        if request.title:
            update_values["title"] = request.title
        
        if request.metadata:
            # Merge metadata
            current_metadata = existing_conversation.metadata or {}
            new_metadata = request.metadata.dict() if hasattr(request.metadata, 'dict') else request.metadata
            if isinstance(current_metadata, dict) and isinstance(new_metadata, dict):
                merged_metadata = {**current_metadata, **new_metadata}
            else:
                merged_metadata = new_metadata or {}
            update_values["metadata"] = merged_metadata
        
        if update_values:
            await chat_service.db_session.execute(
                update(ChatConversation)
                .where(ChatConversation.id == conversation_id)
                .values(**update_values)
            )
            await chat_service.db_session.commit()
        
        # Log audit event
        await chat_service.audit_user_action(
            user_id, "conversation_updated", conversation_id, 
            {"title": request.title, "metadata": request.metadata}
        )
        
        # Get updated conversation for response
        updated_result = await chat_service.db_session.execute(
            select(ChatConversation).where(
                ChatConversation.id == conversation_id
            )
        )
        updated_conversation = updated_result.scalar_one()
        
        # Create response with proper field access
        metadata = request.metadata if request.metadata else ConversationMetadata()
        return ConversationResponse(
            id=str(updated_conversation.id),
            user_id=str(updated_conversation.user_id),
            title=getattr(updated_conversation, 'title', ''),
            created_at=getattr(updated_conversation, 'created_at', datetime.utcnow()),
            updated_at=getattr(updated_conversation, 'updated_at', datetime.utcnow()),
            provider_id=str(getattr(updated_conversation, 'provider_id', '')),
            model_used=getattr(updated_conversation, 'model', ''),
            message_count=0,  # Would need to be calculated
            metadata=metadata,
            is_archived=getattr(updated_conversation, 'is_archived', False),
            messages=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    chat_service: SecureChatService = Depends(get_chat_service)
):
    """Delete conversation with authorization check."""
    try:
        user_id = current_user["user_id"]
        
        # Validate conversation ID format
        import re
        if not re.match(r'^[a-f0-9-]{36}$', conversation_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation ID format"
            )
        
        # Get existing conversation
        result = await chat_service.db_session.execute(
            select(ChatConversation).where(
                ChatConversation.id == conversation_id
            )
        )
        existing_conversation = result.scalar_one_or_none()
        
        if not existing_conversation or existing_conversation.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Delete conversation
        await chat_service.db_session.delete(existing_conversation)
        await chat_service.db_session.commit()
        
        # Log audit event
        await chat_service.audit_user_action(
            user_id, "conversation_deleted", conversation_id
        )
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    http_request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    chat_service: SecureChatService = Depends(get_chat_service)
):
    """Send message to conversation with security validation."""
    try:
        user_id = current_user["user_id"]
        client_ip = getattr(http_request.state, 'client_ip', 'unknown')
        
        # Validate conversation ID format
        import re
        if not re.match(r'^[a-f0-9-]{36}$', conversation_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation ID format"
            )
        
        # Send message with security validation
        message = await chat_service.send_message_secure(conversation_id, user_id, request)
        
        # Record metrics
        await record_chat_metric(MetricType.MESSAGE_VOLUME, 1, "count")
        
        return message
        
    except ValueError as e:
        # Handle validation errors
        await log_security_event(
            "message_send_failed",
            {
                "conversation_id": conversation_id,
                "user_id": current_user["user_id"],
                "error": str(e)
            },
            user_id=current_user["user_id"],
            ip_address=getattr(http_request.state, 'client_ip', 'unknown'),
            threat_level=ThreatLevel.MEDIUM
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to send message to conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )


@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
async def get_messages(
    conversation_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get conversation messages with authorization check."""
    try:
        user_id = current_user["user_id"]
        
        # Validate conversation ID format
        import re
        if not re.match(r'^[a-f0-9-]{36}$', conversation_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation ID format"
            )
        
        # Validate pagination parameters
        if limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit cannot exceed 1000"
            )
        
        messages = await chat_service.get_messages(conversation_id, user_id, limit, offset)
        
        # Get total count for pagination
        total = len(messages)
        
        return MessageListResponse(
            messages=messages,
            total=total,
            page=(offset // limit) + 1,
            per_page=limit,
            has_next=offset + limit < total,
            has_prev=offset > 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get messages for conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get messages"
        )


@router.post("/upload")
async def upload_file(
    http_request: Request,
    file: UploadFile = File(...),
    conversation_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    chat_service: SecureChatService = Depends(get_chat_service)
):
    """Upload file with security validation."""
    try:
        user_id = current_user["user_id"]
        client_ip = getattr(http_request.state, 'client_ip', 'unknown')
        
        # Validate file size (max 10MB)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 10MB limit"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Sanitize filename
        safe_filename = sanitize_filename(file.filename or "unknown")
        
        # Validate file for security threats
        validation_result = await chat_service.validate_file_upload_secure(
            file_content, safe_filename
        )
        
        if not validation_result.is_valid:
            await log_security_event(
                "malicious_file_upload",
                {
                    "filename": safe_filename,
                    "threats": validation_result.threats_detected,
                    "user_id": user_id
                },
                user_id=user_id,
                ip_address=client_ip,
                threat_level=ThreatLevel.HIGH
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File validation failed: {', '.join(validation_result.threats_detected)}"
            )
        
        # Process file upload (implementation depends on storage system)
        # This would typically save to cloud storage or local filesystem
        
        return {
            "message": "File uploaded successfully",
            "filename": safe_filename,
            "size": len(file_content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )


@router.get("/security/summary")
async def get_security_summary(
    hours: int = Query(24, ge=1, le=168),  # Max 7 days
    current_user: Dict[str, Any] = Depends(get_current_user),
    chat_service: SecureChatService = Depends(get_chat_service)
):
    """Get security summary for current user."""
    try:
        user_id = current_user["user_id"]
        
        # Validate time range
        if hours > 168:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time range cannot exceed 168 hours (7 days)"
            )
        
        summary = await chat_service.get_security_summary(user_id, hours)
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get security summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security summary"
        )


@router.get("/health")
async def health_check(
    chat_service: ChatService = Depends(get_chat_service)
):
    """Health check for chat services."""
    try:
        providers = await chat_service.list_providers()
        
        # Check if any providers are available
        available_count = sum(1 for p in providers if p.get("is_available", False))
        
        return {
            "status": "healthy" if available_count > 0 else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "providers": {
                "total": len(providers),
                "available": available_count,
                "unavailable": len(providers) - available_count
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


# Admin endpoints
@router.get("/admin/security-events")
async def get_security_events(
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(require_chat_admin),
    chat_service: SecureChatService = Depends(get_chat_service)
):
    """Get security events (admin only)."""
    try:
        from .monitoring import get_chat_monitoring_service
        monitoring_service = get_chat_monitoring_service()
        
        events = monitoring_service.security_monitor.get_events(limit, event_type)
        
        return {
            "events": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "threat_level": event.threat_level.value,
                    "user_id": event.user_id,
                    "ip_address": event.ip_address,
                    "details": event.details,
                    "resolved": event.resolved
                }
                for event in events
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get security events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security events"
        )


@router.get("/admin/alerts")
async def get_security_alerts(
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = None,
    severity_filter: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(require_chat_admin),
    chat_service: SecureChatService = Depends(get_chat_service)
):
    """Get security alerts (admin only)."""
    try:
        from .monitoring import get_chat_monitoring_service, AlertStatus, ThreatLevel
        monitoring_service = get_chat_monitoring_service()
        
        # Convert string parameters to enums
        alert_status = None
        if status_filter:
            try:
                alert_status = AlertStatus(status_filter.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid alert status: {status_filter}"
                )
        
        alert_severity = None
        if severity_filter:
            try:
                alert_severity = ThreatLevel(severity_filter.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid alert severity: {severity_filter}"
                )
        
        alerts = monitoring_service.get_alerts(limit, alert_status, alert_severity)
        
        return {
            "alerts": [
                {
                    "id": alert.id,
                    "timestamp": alert.timestamp.isoformat(),
                    "alert_type": alert.alert_type,
                    "severity": alert.severity.value,
                    "status": alert.status.value,
                    "title": alert.title,
                    "description": alert.description,
                    "source_ip": alert.source_ip,
                    "user_id": alert.user_id,
                    "metadata": alert.metadata,
                    "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                    "resolved_by": alert.resolved_by
                }
                for alert in alerts
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get security alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security alerts"
        )
