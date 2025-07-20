"""SQLAlchemy models for multi-tenant AI-Karen platform."""

from sqlalchemy import Column, String, UUID, DateTime, Text, JSON, ForeignKey, Index, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
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
    is_active = Column(Boolean, default=True)
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
    is_active = Column(Boolean, default=True)
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
    metadata = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_conversation_user', 'user_id'),
        Index('idx_conversation_created', 'created_at'),
        Index('idx_conversation_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<TenantConversation(id={self.id}, user_id={self.user_id}, title='{self.title}')>"


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
    metadata = Column(JSON, default={})
    ttl = Column(DateTime)
    timestamp = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_memory_vector', 'vector_id'),
        Index('idx_memory_user', 'user_id'),
        Index('idx_memory_session', 'session_id'),
        Index('idx_memory_created', 'created_at'),
        Index('idx_memory_ttl', 'ttl'),
    )
    
    def __repr__(self):
        return f"<TenantMemoryEntry(id={self.id}, vector_id='{self.vector_id}', user_id={self.user_id})>"


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