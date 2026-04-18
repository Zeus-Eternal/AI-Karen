"""
Data models for AI-Karen chat system.
Integrates production SQLAlchemy models with canonical Pydantic models.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    UUID,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    JSON,
    JSONB,
    ForeignKey,
    Column,
    Index,
    func,
    LargeBinary,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import expression

try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, ConfigDict, Field

from .conversation_models import ChatMessage, Conversation, MessageRole, MessageType

Base = declarative_base()


# SQLAlchemy Models (for production database compatibility)
class ChatConversation(Base):
    """Chat conversation model for the production chat system."""

    __tablename__ = "chat_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("auth_users.user_id"), nullable=False
    )
    title = Column(String(255))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    provider_id = Column(String(50))
    model_used = Column(String(100))
    message_count = Column(Integer, default=0)
    metadata = Column(JSONB, default=dict)
    is_archived = Column(Boolean, default=False)

    # Security fields
    is_encrypted = Column(Boolean, default=False)
    security_level = Column(String(20), default="medium")
    conversation_status = Column(String(20), default="active")

    # Relationships
    messages = relationship(
        "ChatMessage", back_populates="conversation", cascade="all, delete-orphan"
    )
    attachments = relationship(
        "MessageAttachment", back_populates="message", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_user_conversations", "user_id"),
        Index("idx_conversations_status", "conversation_status"),
        Index("idx_conversations_created", "created_at"),
    )


class ChatMessage(Base):
    """Chat message model for the production chat system."""

    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True), ForeignKey("chat_conversations.id"), nullable=False
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("auth_users.user_id"), nullable=False
    )
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default="text")  # text, image, file, code
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    metadata = Column(JSONB, default=dict)
    is_processed = Column(Boolean, default=False)
    token_count = Column(Integer, default=0)

    # Security fields
    is_encrypted = Column(Boolean, default=False)
    security_level = Column(String(20), default="medium")

    # Relationships
    conversation = relationship("ChatConversation", back_populates="messages")
    attachments = relationship("MessageAttachment", back_populates="message")

    # Indexes
    __table_args__ = (
        Index("idx_messages_conversation", "conversation_id"),
        Index("idx_messages_user", "user_id"),
        Index("idx_messages_created", "created_at"),
        Index("idx_messages_role", "role"),
    )


class MessageAttachment(Base):
    """Message attachment model for the production chat system."""

    __tablename__ = "message_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(
        UUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=False
    )
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    file_path = Column(String(500))
    storage_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    metadata = Column(JSONB, default=dict)

    # Security fields
    is_scanned = Column(Boolean, default=False)
    scan_result = Column(String(50), default="pending")
    security_level = Column(String(20), default="medium")

    # Relationships
    message = relationship("ChatMessage", back_populates="attachments")

    # Indexes
    __table_args__ = (
        Index("idx_attachments_message", "message_id"),
        Index("idx_attachments_created", "created_at"),
    )


class ChatSession(Base):
    """Chat session model for tracking user sessions."""

    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("auth_users.user_id"), nullable=False
    )
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("chat_conversations.id"))
    session_token = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_activity = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True))
    metadata = Column(JSONB, default=dict)
    is_active = Column(Boolean, default=True)

    # Indexes
    __table_args__ = (
        Index("idx_sessions_user", "user_id"),
        Index("idx_sessions_active", "is_active"),
        Index("idx_sessions_expires", "expires_at"),
    )


class ChatProviderConfiguration(Base):
    """LLM provider configuration model."""

    __tablename__ = "chat_provider_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_type = Column(
        String(50), nullable=False
    )  # openai, anthropic, gemini, local
    provider_id = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    config = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    metadata = Column(JSONB, default=dict)

    # Indexes
    __table_args__ = (
        Index("idx_provider_type", "provider_type"),
        Index("idx_provider_active", "is_active"),
    )


# Pydantic Models (for canonical API compatibility)
class EnhancedChatMessage(ChatMessage):
    """Enhanced chat message model with additional fields."""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    # Additional fields for enhanced functionality
    conversation_title: Optional[str] = None
    user_name: Optional[str] = None
    processing_time: Optional[float] = None
    tokens_used: Optional[int] = None
    feedback_score: Optional[float] = None
    tags: List[str] = Field(default_factory=list)

    @classmethod
    def from_sqlalchemy(cls, sql_message: ChatMessage) -> "EnhancedChatMessage":
        """Convert SQLAlchemy model to Pydantic model."""
        return cls(
            id=str(sql_message.id),
            conversation_id=str(sql_message.conversation_id),
            user_id=str(sql_message.user_id),
            role=sql_message.role,
            content=sql_message.content,
            content_type=sql_message.content_type,
            created_at=sql_message.created_at,
            updated_at=sql_message.updated_at,
            metadata=sql_message.metadata or {},
            is_processed=sql_message.is_processed,
            token_count=sql_message.token_count,
            conversation_title=sql_message.conversation.title
            if sql_message.conversation
            else None,
            user_name=f"User_{sql_message.user_id}",  # Would need actual user name from auth
            tags=sql_message.metadata.get("tags", []) if sql_message.metadata else [],
        )


class EnhancedConversation(Conversation):
    """Enhanced conversation model with additional fields."""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    # Additional fields for enhanced functionality
    model_used: Optional[str] = None
    provider_id: Optional[str] = None
    average_response_time: Optional[float] = None
    satisfaction_score: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    last_message_preview: Optional[str] = None

    @classmethod
    def from_sqlalchemy(
        cls, sql_conversation: ChatConversation
    ) -> "EnhancedConversation":
        """Convert SQLAlchemy model to Pydantic model."""
        # Get last message preview
        last_message = None
        if sql_conversation.messages:
            last_message = (
                sql_conversation.messages[-1].content[:100] + "..."
                if len(sql_conversation.messages[-1].content) > 100
                else sql_conversation.messages[-1].content
            )

        return cls(
            id=str(sql_conversation.id),
            user_id=str(sql_conversation.user_id),
            title=sql_conversation.title or "Untitled Conversation",
            description=sql_conversation.description,
            created_at=sql_conversation.created_at,
            updated_at=sql_conversation.updated_at,
            message_count=sql_conversation.message_count,
            metadata=sql_conversation.metadata or {},
            status=sql_conversation.conversation_status,
            model_used=sql_conversation.model_used,
            provider_id=sql_conversation.provider_id,
            average_response_time=sql_conversation.metadata.get(
                "average_response_time"
            ),
            satisfaction_score=sql_conversation.metadata.get("satisfaction_score"),
            tags=sql_conversation.metadata.get("tags", [])
            if sql_conversation.metadata
            else [],
            last_message_preview=last_message,
        )


class ConversationStats(BaseModel):
    """Conversation statistics model."""

    conversation_id: str
    total_messages: int
    user_messages: int
    assistant_messages: int
    total_tokens: int
    average_response_time: float
    satisfaction_score: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ProviderConfig(BaseModel):
    """Provider configuration model."""

    id: str
    provider_type: str
    provider_id: str
    name: str
    description: Optional[str] = None
    config: Dict[str, Any]
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionInfo(BaseModel):
    """Session information model."""

    id: str
    user_id: str
    conversation_id: Optional[str] = None
    session_token: str
    created_at: datetime
    last_activity: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


# Utility functions for model conversion
def convert_sql_to_pydantic(sql_model: Base, pydantic_model: type) -> BaseModel:
    """Convert SQLAlchemy model to Pydantic model."""
    if sql_model is None:
        return None

    # Get the data from SQLAlchemy model
    data = {}
    for column in sql_model.__table__.columns:
        value = getattr(sql_model, column.name)
        # Convert UUID to string for JSON serialization
        if isinstance(value, uuid.UUID):
            value = str(value)
        data[column.name] = value

    return pydantic_model(**data)


def convert_pydantic_to_sql(pydantic_model: BaseModel, sql_class: type) -> Base:
    """Convert Pydantic model to SQLAlchemy model."""
    data = pydantic_model.model_dump()

    # Remove fields that don't exist in SQLAlchemy model
    sql_fields = [column.name for column in sql_class.__table__.columns]
    filtered_data = {k: v for k, v in data.items() if k in sql_fields}

    return sql_class(**filtered_data)


# Factory functions
def create_conversation(user_id: str, title: str, **kwargs) -> ChatConversation:
    """Create a new conversation."""
    return ChatConversation(user_id=uuid.UUID(user_id), title=title, **kwargs)


def create_message(
    conversation_id: str, user_id: str, role: str, content: str, **kwargs
) -> ChatMessage:
    """Create a new message."""
    return ChatMessage(
        conversation_id=uuid.UUID(conversation_id),
        user_id=uuid.UUID(user_id),
        role=role,
        content=content,
        **kwargs,
    )
