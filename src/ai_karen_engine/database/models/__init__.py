"""SQLAlchemy models for multi-tenant AI-Karen platform."""

from sqlalchemy import Column, String, UUID, DateTime, Text, JSON, ForeignKey, Index, Boolean, Integer
from sqlalchemy.sql import expression
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class Tenant(Base):
    """Tenant model for multi-tenant isolation."""
    __tablename__ = 'tenants'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    subscription_tier = Column(String(50), nullable=False, default='basic')
    settings = Column(JSON, default={})
    is_active = Column(Boolean, default=True, server_default=expression.true())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_tenant_slug', 'slug'),
        Index('idx_tenant_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', slug='{self.slug}')>"


class User(Base):
    """User model with tenant association."""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    email = Column(String(255), nullable=False)
    roles = Column(ARRAY(String), default=[])
    preferences = Column(JSON, default={})
    is_active = Column(Boolean, default=True, server_default=expression.true())
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    
    __table_args__ = (
        Index('idx_user_tenant', 'tenant_id'),
        Index('idx_user_email', 'email'),
        Index('idx_user_tenant_email', 'tenant_id', 'email', unique=True),
        Index('idx_user_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', tenant_id={self.tenant_id})>"


class TenantConversation(Base):
    """Base model for tenant-specific conversations."""
    __tablename__ = 'conversations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(255))
    messages = Column(JSON, default=[])
    conversation_metadata = Column(JSON, default={})
    is_active = Column(Boolean, default=True, server_default=expression.true())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Web UI integration fields
    session_id = Column(String(255), index=True)  # Session tracking for web UI
    ui_context = Column(JSON, default={})  # Web UI specific context data
    ai_insights = Column(JSON, default={})  # AI-generated insights and metadata
    user_settings = Column(JSON, default={})  # User settings snapshot for this conversation
    summary = Column(Text)  # Conversation summary
    tags = Column(ARRAY(String), default=[])  # Conversation tags for organization
    last_ai_response_id = Column(String(255))  # Track last AI response for continuity
    
    __table_args__ = (
        Index('idx_conversation_user', 'user_id'),
        Index('idx_conversation_created', 'created_at'),
        Index('idx_conversation_active', 'is_active'),
        Index('idx_conversation_session', 'session_id'),
        Index('idx_conversation_tags', 'tags'),
        Index('idx_conversation_user_session', 'user_id', 'session_id'),
    )
    
    def __repr__(self):
        return f"<TenantConversation(id={self.id}, user_id={self.user_id}, title='{self.title}')>"
    
    def add_tag(self, tag: str):
        """Add a tag to the conversation."""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """Remove a tag from the conversation."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
    
    def update_ui_context(self, context_data: dict):
        """Update UI context with new data."""
        if self.ui_context is None:
            self.ui_context = {}
        self.ui_context.update(context_data)
    
    def update_ai_insights(self, insights_data: dict):
        """Update AI insights with new data."""
        if self.ai_insights is None:
            self.ai_insights = {}
        self.ai_insights.update(insights_data)


class TenantMemoryEntry(Base):
    """Base model for tenant-specific memory entries."""
    __tablename__ = 'memory_entries'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vector_id = Column(String(255), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    session_id = Column(String(255))
    content = Column(Text, nullable=False)
    query = Column(Text)
    result = Column(JSON)
    embedding_id = Column(String(255))
    memory_metadata = Column(JSON, default={})
    ttl = Column(DateTime)
    timestamp = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Web UI integration fields
    ui_source = Column(String(50))  # Source UI (web, streamlit, desktop)
    conversation_id = Column(UUID(as_uuid=True))  # Link to conversation
    memory_type = Column(String(50), default='general')  # Type of memory (fact, preference, context)
    tags = Column(ARRAY(String), default=[])  # Memory tags for categorization
    importance_score = Column(Integer, default=5)  # Importance score (1-10)
    access_count = Column(Integer, default=0)  # How many times this memory was accessed
    last_accessed = Column(DateTime)  # When this memory was last accessed
    ai_generated = Column(Boolean, default=False)  # Whether this memory was AI-generated
    user_confirmed = Column(Boolean, default=True)  # Whether user confirmed this memory
    
    __table_args__ = (
        Index('idx_memory_vector', 'vector_id'),
        Index('idx_memory_user', 'user_id'),
        Index('idx_memory_session', 'session_id'),
        Index('idx_memory_created', 'created_at'),
        Index('idx_memory_ttl', 'ttl'),
        Index('idx_memory_ui_source', 'ui_source'),
        Index('idx_memory_conversation', 'conversation_id'),
        Index('idx_memory_type', 'memory_type'),
        Index('idx_memory_tags', 'tags'),
        Index('idx_memory_importance', 'importance_score'),
        Index('idx_memory_user_conversation', 'user_id', 'conversation_id'),
        Index('idx_memory_user_type', 'user_id', 'memory_type'),
    )
    
    def __repr__(self):
        return f"<TenantMemoryEntry(id={self.id}, vector_id='{self.vector_id}', user_id={self.user_id})>"
    
    def add_tag(self, tag: str):
        """Add a tag to the memory entry."""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """Remove a tag from the memory entry."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
    
    def increment_access_count(self):
        """Increment the access count and update last accessed time."""
        self.access_count = (self.access_count or 0) + 1
        self.last_accessed = datetime.utcnow()
    
    def set_importance(self, score: int):
        """Set the importance score (1-10)."""
        if 1 <= score <= 10:
            self.importance_score = score
        else:
            raise ValueError("Importance score must be between 1 and 10")
    
    def update_metadata(self, metadata_data: dict):
        """Update memory metadata with new data."""
        if self.memory_metadata is None:
            self.memory_metadata = {}
        self.memory_metadata.update(metadata_data)


class TenantPluginExecution(Base):
    """Base model for tenant-specific plugin executions."""
    __tablename__ = 'plugin_executions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    plugin_name = Column(String(255), nullable=False)
    execution_data = Column(JSON, default={})
    result = Column(JSON)
    status = Column(String(50), default='pending')  # pending, running, completed, failed
    error_message = Column(Text)
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_plugin_user', 'user_id'),
        Index('idx_plugin_name', 'plugin_name'),
        Index('idx_plugin_status', 'status'),
        Index('idx_plugin_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<TenantPluginExecution(id={self.id}, plugin_name='{self.plugin_name}', status='{self.status}')>"


class TenantAuditLog(Base):
    """Base model for tenant-specific audit logging."""
    __tablename__ = 'audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True))
    action = Column(String(255), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    details = Column(JSON, default={})
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    correlation_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_created', 'created_at'),
        Index('idx_audit_correlation', 'correlation_id'),
    )
    
    def __repr__(self):
        return f"<TenantAuditLog(id={self.id}, action='{self.action}', user_id={self.user_id})>"