"""
Pydantic schemas for AI-Karen chat system API.
Integrates production schemas with canonical schemas.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Union, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum

from .conversation_models import ChatMessage, Conversation, MessageRole, MessageType


class ProviderType(str, Enum):
    """Provider type enum for LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    LOCAL = "local"


class SecurityLevel(str, Enum):
    """Security level enum for content validation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    STRICT = "strict"


class StreamingStatus(str, Enum):
    """Streaming status enum for messages."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ThreatLevel(str, Enum):
    """Threat level enum for security events."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConversationStatus(str, Enum):
    """Conversation status enum."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    TEMPLATE = "template"


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat(), uuid.UUID: lambda v: str(v)}


class MessageMetadata(BaseSchema):
    """Metadata for chat messages."""

    token_count: Optional[int] = None
    processing_time_ms: Optional[int] = None
    provider_id: Optional[str] = None
    model_used: Optional[str] = None
    security_level: Optional[str] = None
    threats_detected: List[str] = Field(default_factory=list)
    validation_passed: bool = True


class ConversationMetadata(BaseSchema):
    """Metadata for conversations."""

    message_count: int = 0
    total_tokens: int = 0
    average_response_time: Optional[float] = None
    satisfaction_score: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    security_level: Optional[str] = None
    last_activity: Optional[datetime] = None
    model_used: Optional[str] = None
    provider_id: Optional[str] = None


# Request schemas
class CreateConversationRequest(BaseSchema):
    """Request to create a new conversation."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator("title")
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()


class UpdateConversationRequest(BaseSchema):
    """Request to update an existing conversation."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    security_level: Optional[SecurityLevel] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[ConversationStatus] = None

    @validator("title")
    def validate_title(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Title cannot be empty")
            return v.strip()
        return v


class SendMessageRequest(BaseSchema):
    """Request to send a message."""

    content: str = Field(..., min_length=1, max_length=10000)
    role: MessageRole = MessageRole.USER
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    stream: bool = False
    conversation_id: Optional[str] = None

    @validator("content")
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()


class StreamMessageRequest(BaseSchema):
    """Request to stream a message."""

    content: str = Field(..., min_length=1, max_length=10000)
    role: MessageRole = MessageRole.USER
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    conversation_id: Optional[str] = None

    @validator("content")
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()


class UploadFileRequest(BaseSchema):
    """Request to upload a file."""

    filename: str = Field(..., min_length=1, max_length=255)
    content: bytes = Field(..., description="File content as bytes")
    content_type: Optional[str] = None
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    conversation_id: Optional[str] = None


class ConfigureProviderRequest(BaseSchema):
    """Request to configure an LLM provider."""

    provider_type: ProviderType
    provider_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    config: Dict[str, Any] = Field(..., description="Provider configuration")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator("config")
    def validate_config(cls, v):
        if not v or not isinstance(v, dict):
            raise ValueError("Configuration must be a non-empty dictionary")
        return v


# Response schemas
class ConversationResponse(BaseSchema):
    """Response for conversation data."""

    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    status: ConversationStatus
    metadata: ConversationMetadata
    security_level: SecurityLevel
    model_used: Optional[str] = None
    provider_id: Optional[str] = None

    @classmethod
    def from_conversation(cls, conversation: Conversation) -> "ConversationResponse":
        """Create from Conversation model."""
        return cls(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            description=conversation.description,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            status=conversation.status,
            metadata=ConversationMetadata(
                message_count=conversation.message_count,
                tags=conversation.tags or [],
                security_level=conversation.security_level or SecurityLevel.MEDIUM,
                last_activity=conversation.updated_at,
            ),
            security_level=conversation.security_level or SecurityLevel.MEDIUM,
            model_used=conversation.metadata.get("model_used")
            if conversation.metadata
            else None,
            provider_id=conversation.metadata.get("provider_id")
            if conversation.metadata
            else None,
        )


class MessageResponse(BaseSchema):
    """Response for message data."""

    id: str
    conversation_id: str
    user_id: str
    role: MessageRole
    content: str
    content_type: MessageType = MessageType.TEXT
    created_at: datetime
    updated_at: datetime
    metadata: MessageMetadata
    security_level: SecurityLevel

    @classmethod
    def from_message(cls, message: ChatMessage) -> "MessageResponse":
        """Create from ChatMessage model."""
        return cls(
            id=message.id,
            conversation_id=message.conversation_id,
            user_id=message.user_id,
            role=message.role,
            content=message.content,
            content_type=message.content_type,
            created_at=message.created_at,
            updated_at=message.updated_at,
            metadata=MessageMetadata(
                token_count=message.metadata.get("token_count")
                if message.metadata
                else None,
                processing_time_ms=message.metadata.get("processing_time_ms")
                if message.metadata
                else None,
                provider_id=message.metadata.get("provider_id")
                if message.metadata
                else None,
                model_used=message.metadata.get("model_used")
                if message.metadata
                else None,
                security_level=message.security_level or SecurityLevel.MEDIUM,
                threats_detected=message.metadata.get("threats_detected", [])
                if message.metadata
                else [],
                validation_passed=message.metadata.get("validation_passed", True),
            ),
            security_level=message.security_level or SecurityLevel.MEDIUM,
        )


class ProviderResponse(BaseSchema):
    """Response for provider configuration."""

    id: str
    provider_type: ProviderType
    provider_id: str
    name: str
    description: Optional[str] = None
    config: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "ProviderResponse":
        """Create from configuration dictionary."""
        return cls(
            id=config.get("id", str(uuid.uuid4())),
            provider_type=config.get("provider_type", ProviderType.OPENAI),
            provider_id=config.get("provider_id", ""),
            name=config.get("name", ""),
            description=config.get("description"),
            config=config.get("config", {}),
            is_active=config.get("is_active", True),
            created_at=config.get("created_at", datetime.utcnow()),
            updated_at=config.get("updated_at", datetime.utcnow()),
            metadata=config.get("metadata", {}),
        )


# List response schemas
class ConversationListResponse(BaseSchema):
    """Response for list of conversations."""

    conversations: List[ConversationResponse]
    total: int
    limit: int
    offset: int

    @classmethod
    def from_conversations(
        cls, conversations: List[Conversation], total: int, limit: int, offset: int
    ) -> "ConversationListResponse":
        """Create from list of conversations."""
        return cls(
            conversations=[
                ConversationResponse.from_conversation(conv) for conv in conversations
            ],
            total=total,
            limit=limit,
            offset=offset,
        )


class MessageListResponse(BaseSchema):
    """Response for list of messages."""

    messages: List[MessageResponse]
    total: int
    limit: int
    offset: int
    conversation_id: str

    @classmethod
    def from_messages(
        cls,
        messages: List[ChatMessage],
        total: int,
        limit: int,
        offset: int,
        conversation_id: str,
    ) -> "MessageListResponse":
        """Create from list of messages."""
        return cls(
            messages=[MessageResponse.from_message(msg) for msg in messages],
            total=total,
            limit=limit,
            offset=offset,
            conversation_id=conversation_id,
        )


class ProviderListResponse(BaseSchema):
    """Response for list of providers."""

    providers: List[ProviderResponse]
    total: int

    @classmethod
    def from_configs(
        cls, configs: List[Dict[str, Any]], total: int
    ) -> "ProviderListResponse":
        """Create from list of configurations."""
        return cls(
            providers=[ProviderResponse.from_config(config) for config in configs],
            total=total,
        )


# Streaming response schemas
class StreamChunkResponse(BaseSchema):
    """Response for streaming chunks."""

    chunk_id: str
    content: str
    role: Optional[MessageRole] = None
    status: StreamingStatus = StreamingStatus.IN_PROGRESS
    metadata: Optional[MessageMetadata] = None
    timestamp: datetime

    @classmethod
    def from_chunk(
        cls,
        content: str,
        chunk_id: str,
        role: Optional[MessageRole] = None,
        status: StreamingStatus = StreamingStatus.IN_PROGRESS,
    ) -> "StreamChunkResponse":
        """Create from chunk data."""
        return cls(
            chunk_id=chunk_id,
            content=content,
            role=role,
            status=status,
            metadata=MessageMetadata(),
            timestamp=datetime.utcnow(),
        )


class StreamStartResponse(BaseSchema):
    """Response for stream start."""

    stream_id: str
    conversation_id: str
    status: StreamingStatus = StreamingStatus.IN_PROGRESS
    estimated_chunks: Optional[int] = None
    metadata: MessageMetadata

    @classmethod
    def from_stream(
        cls,
        stream_id: str,
        conversation_id: str,
        estimated_chunks: Optional[int] = None,
    ) -> "StreamStartResponse":
        """Create from stream data."""
        return cls(
            stream_id=stream_id,
            conversation_id=conversation_id,
            status=StreamingStatus.IN_PROGRESS,
            estimated_chunks=estimated_chunks,
            metadata=MessageMetadata(),
        )


class StreamEndResponse(BaseSchema):
    """Response for stream end."""

    stream_id: str
    conversation_id: str
    status: StreamingStatus = StreamingStatus.COMPLETED
    total_chunks: int
    total_tokens: Optional[int] = None
    processing_time_ms: Optional[int] = None
    metadata: MessageMetadata

    @classmethod
    def from_completion(
        cls,
        stream_id: str,
        conversation_id: str,
        total_chunks: int,
        total_tokens: Optional[int] = None,
        processing_time_ms: Optional[int] = None,
    ) -> "StreamEndResponse":
        """Create from completion data."""
        return cls(
            stream_id=stream_id,
            conversation_id=conversation_id,
            status=StreamingStatus.COMPLETED,
            total_chunks=total_chunks,
            total_tokens=total_tokens,
            processing_time_ms=processing_time_ms,
            metadata=MessageMetadata(),
        )


# Error response schemas
class ErrorResponse(BaseSchema):
    """Response for errors."""

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    request_id: Optional[str] = None

    @classmethod
    def from_exception(
        cls,
        error: Exception,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> "ErrorResponse":
        """Create from exception."""
        return cls(
            error=error.__class__.__name__,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            request_id=request_id,
        )


class SuccessResponse(BaseSchema):
    """Response for successful operations."""

    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime

    @classmethod
    def from_data(
        cls, message: str, data: Optional[Dict[str, Any]] = None
    ) -> "SuccessResponse":
        """Create from data."""
        return cls(message=message, data=data, timestamp=datetime.utcnow())


# WebSocket message schemas
class WebSocketMessage(BaseSchema):
    """WebSocket message schema."""

    type: str
    data: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None

    @classmethod
    def create(
        cls,
        message_type: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> "WebSocketMessage":
        """Create WebSocket message."""
        return cls(
            type=message_type,
            data=data,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            conversation_id=conversation_id,
        )


# Health check schemas
class HealthCheckResponse(BaseSchema):
    """Response for health checks."""

    status: str
    services: Dict[str, str]
    timestamp: datetime
    version: Optional[str] = None
    uptime: Optional[float] = None

    @classmethod
    def from_status(
        cls,
        status: str,
        services: Dict[str, str],
        version: Optional[str] = None,
        uptime: Optional[float] = None,
    ) -> "HealthCheckResponse":
        """Create from status data."""
        return cls(
            status=status,
            services=services,
            timestamp=datetime.utcnow(),
            version=version,
            uptime=uptime,
        )
