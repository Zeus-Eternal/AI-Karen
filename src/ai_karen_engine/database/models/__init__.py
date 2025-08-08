# mypy: ignore-errors
"""SQLAlchemy models for multi-tenant AI-Karen platform."""

import json
import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import (
    JSON,
    UUID,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    desc,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import expression

from ai_karen_engine.automation_manager.encryption_utils import (
    decrypt_data,
    encrypt_data,
)

Base = declarative_base()


class Tenant(Base):
    """Tenant model for multi-tenant isolation."""

    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    subscription_tier = Column(String(50), nullable=False, default="basic")
    settings = Column(JSON, default={})
    is_active = Column(Boolean, default=True, server_default=expression.true())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship(
        "AuthUser", back_populates="tenant", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_tenant_slug", "slug"),
        Index("idx_tenant_active", "is_active"),
    )

    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', slug='{self.slug}')>"


class AuthUser(Base):
    """User model with tenant association."""

    __tablename__ = "auth_users"

    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String)
    email = Column(String(255), nullable=False)
    roles = Column(ARRAY(String), default=[])
    preferences = Column(JSON, default={})
    is_active = Column(Boolean, default=True, server_default=expression.true())
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship(
        "Tenant",
        back_populates="users",
        primaryjoin="AuthUser.tenant_id==cast(Tenant.id, String)",
    )

    __table_args__ = (
        Index("idx_auth_user_tenant", "tenant_id"),
        Index("idx_auth_user_email", "email"),
        Index("idx_auth_user_active", "is_active"),
    )

    def __repr__(self):
        return f"<AuthUser(user_id={self.user_id}, email='{self.email}', tenant_id={self.tenant_id})>"


class TenantConversation(Base):
    """Base model for tenant-specific conversations."""

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(255))
    conversation_metadata = Column(JSON, default={})
    is_active = Column(Boolean, default=True, server_default=expression.true())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Web UI integration fields
    session_id = Column(String(255), index=True)  # Session tracking for web UI
    ui_context = Column(JSON, default={})  # Web UI specific context data
    ai_insights = Column(JSON, default={})  # AI-generated insights and metadata
    user_settings = Column(
        JSON, default={}
    )  # User settings snapshot for this conversation
    summary = Column(Text)  # Conversation summary
    tags = Column(ARRAY(String), default=[])  # Conversation tags for organization
    last_ai_response_id = Column(String(255))  # Track last AI response for continuity

    __table_args__ = (
        Index("idx_conversation_user", "user_id"),
        Index("idx_conversation_created", "created_at"),
        Index("idx_conversation_active", "is_active"),
        Index("idx_conversation_session", "session_id"),
        Index("idx_conversation_tags", "tags"),
        Index("idx_conversation_user_session", "user_id", "session_id"),
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


class TenantMemoryItem(Base):
    """Base model for tenant-specific memory items."""

    __tablename__ = "memory_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scope = Column(String(255), nullable=False)
    kind = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(ARRAY(Float), nullable=True)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_memory_items_scope_kind", "scope", "kind"),)

    def __repr__(self):
        return f"<TenantMemoryItem(id={self.id}, scope='{self.scope}', kind='{self.kind}')>"


# Backwards compatibility alias
TenantMemoryEntry = TenantMemoryItem


class TenantMessage(Base):
    """Individual message within a conversation."""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, default={})
    function_call = Column(JSON)
    function_response = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_message_conversation_time", "conversation_id", "created_at"),
    )

    def __repr__(self):
        return f"<TenantMessage(id={self.id}, conversation_id={self.conversation_id}, role='{self.role}')>"


class TenantMessageTool(Base):
    """Tool execution associated with a message."""

    __tablename__ = "message_tools"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_name = Column(String(255), nullable=False)
    arguments = Column(JSON, default={})
    result = Column(JSON)
    latency_ms = Column(Integer)
    status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_message_tool_message", "message_id"),)

    def __repr__(self):
        return f"<TenantMessageTool(id={self.id}, message_id={self.message_id}, tool='{self.tool_name}')>"

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

    __tablename__ = "plugin_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    plugin_name = Column(String(255), nullable=False)
    execution_data = Column(JSON, default={})
    result = Column(JSON)
    status = Column(
        String(50), default="pending"
    )  # pending, running, completed, failed
    error_message = Column(Text)
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    __table_args__ = (
        Index("idx_plugin_user", "user_id"),
        Index("idx_plugin_name", "plugin_name"),
        Index("idx_plugin_status", "status"),
        Index("idx_plugin_created", "created_at"),
    )

    def __repr__(self):
        return f"<TenantPluginExecution(id={self.id}, plugin_name='{self.plugin_name}', status='{self.status}')>"


class AuditLog(Base):
    """Audit logging records for tenant and user activity."""

    __tablename__ = "audit_log"

    event_id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(String)
    user_id = Column(String)
    actor_type = Column(String)
    action = Column(String, nullable=False)
    resource_type = Column(String)
    resource_id = Column(String)
    ip_address = Column(String)
    user_agent = Column(Text)
    details = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_audit_tenant_time", "tenant_id", desc("created_at")),)

    def __repr__(self):
        return f"<AuditLog(event_id={self.event_id}, action='{self.action}', tenant_id={self.tenant_id})>"


class Extension(Base):
    """Registered extension metadata."""

    __tablename__ = "extensions"

    name = Column(String, primary_key=True)
    version = Column(String, nullable=False)
    category = Column(String)
    capabilities = Column(JSONB)
    directory = Column(String)
    status = Column(String, nullable=False)
    error_msg = Column(Text)
    loaded_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow)

    usage = relationship("ExtensionUsage", back_populates="extension")

    def __repr__(self):
        return f"<Extension(name={self.name}, status='{self.status}')>"


class ExtensionUsage(Base):
    """Sampled resource usage metrics for extensions."""

    __tablename__ = "extension_usage"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, ForeignKey("extensions.name", ondelete="CASCADE"))
    memory_mb = Column(Float)
    cpu_percent = Column(Float)
    disk_mb = Column(Float)
    network_sent = Column(BigInteger)
    network_recv = Column(BigInteger)
    uptime_seconds = Column(BigInteger)
    sampled_at = Column(DateTime, default=datetime.utcnow)

    extension = relationship("Extension", back_populates="usage")

    __table_args__ = (Index("idx_ext_usage_name_time", "name", desc("sampled_at")),)

    def __repr__(self):
        return f"<ExtensionUsage(name={self.name}, sampled_at={self.sampled_at})>"


class Hook(Base):
    """Registered hook metadata."""

    __tablename__ = "hooks"

    hook_id = Column(String, primary_key=True)
    hook_type = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    source_name = Column(String)
    priority = Column(Integer, default=50)
    enabled = Column(Boolean, default=True)
    conditions = Column(JSON, default={})
    registered_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_hooks_type", "hook_type"),
        Index("idx_hooks_enabled", "enabled"),
    )

    def __repr__(self):
        return f"<Hook(hook_id={self.hook_id}, hook_type='{self.hook_type}')>"


class HookExecutionStat(Base):
    """Aggregated hook execution metrics."""

    __tablename__ = "hook_exec_stats"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    hook_type = Column(String)
    source_name = Column(String)
    executions = Column(BigInteger, default=0)
    successes = Column(BigInteger, default=0)
    errors = Column(BigInteger, default=0)
    timeouts = Column(BigInteger, default=0)
    avg_duration_ms = Column(Integer, default=0)
    window_start = Column(DateTime)
    window_end = Column(DateTime)

    __table_args__ = (
        Index("idx_hook_exec_stats_type_window", "hook_type", "window_start"),
    )

    def __repr__(self):
        return f"<HookExecutionStat(id={self.id}, hook_type='{self.hook_type}')>"


class LLMProvider(Base):
    """Registered LLM provider with encrypted configuration."""

    __tablename__ = "llm_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    provider_type = Column(String(50), nullable=False)
    _config = Column("encrypted_config", LargeBinary, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requests = relationship("LLMRequest", back_populates="provider")

    @property
    def config(self) -> Dict[str, Any]:
        data = decrypt_data(self._config)
        return json.loads(data) if data else {}

    @config.setter
    def config(self, value: Dict[str, Any]) -> None:
        self._config = encrypt_data(json.dumps(value))

    def __repr__(self) -> str:
        return f"<LLMProvider(name={self.name}, type={self.provider_type})>"


class LLMRequest(Base):
    """LLM invocation metrics for cost tracking."""

    __tablename__ = "llm_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("llm_providers.id"))
    provider_name = Column(String(100), nullable=False)
    model = Column(String(100))
    tenant_id = Column(String, index=True)
    user_id = Column(String, index=True)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    cost = Column(Numeric(10, 4))
    latency_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    provider = relationship("LLMProvider", back_populates="requests")

    __table_args__ = (
        Index("idx_llm_requests_provider_time", "provider_name", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<LLMRequest(provider={self.provider_name}, model={self.model}, cost={self.cost})>"
