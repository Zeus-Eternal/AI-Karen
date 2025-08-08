"""Authentication related SQLAlchemy models."""

import uuid
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class AuthUser(Base):
    """Application user account"""

    __tablename__ = "auth_users"

    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    password_hash = Column(String(255))
    tenant_id = Column(String)
    roles = Column(JSONB, nullable=False, default=list)
    preferences = Column(JSONB, default=dict)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(String(32))
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime)

    sessions = relationship("AuthSession", back_populates="user", cascade="all, delete-orphan")
    chat_memories = relationship("ChatMemory", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_auth_user_email_active", "email", "is_active"),
        Index("idx_auth_user_tenant", "tenant_id"),
        Index("idx_auth_user_created", "created_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"<AuthUser(user_id={self.user_id}, email={self.email})>"


class AuthSession(Base):
    """Session tokens tied to a user"""

    __tablename__ = "auth_sessions"

    session_token = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("auth_users.user_id", ondelete="CASCADE"), nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    expires_in = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_accessed = Column(DateTime, default=func.now(), nullable=False)
    ip_address = Column(String)
    user_agent = Column(Text)
    device_fingerprint = Column(String)
    geolocation = Column(JSONB)
    risk_score = Column(Numeric(5, 2), default=0)
    security_flags = Column(JSONB, default=list)
    is_active = Column(Boolean, default=True, nullable=False)
    invalidated_at = Column(DateTime)
    invalidation_reason = Column(Text)

    user = relationship("AuthUser", back_populates="sessions")

    __table_args__ = (
        Index("idx_auth_sessions_user_active", "user_id", "is_active"),
        Index("idx_auth_sessions_last_accessed", "last_accessed"),
    )

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"<AuthSession(session_token={self.session_token}, user_id={self.user_id})>"


class AuthProvider(Base):
    """Authentication provider configuration"""

    __tablename__ = "auth_providers"

    provider_id = Column(String, primary_key=True)
    tenant_id = Column(String)
    type = Column(String, nullable=False)
    config = Column(JSONB, nullable=False)
    metadata = Column(JSONB, default=dict)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    identities = relationship("UserIdentity", back_populates="provider", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AuthProvider(provider_id={self.provider_id})>"


class UserIdentity(Base):
    """Links a user to an external auth provider identity"""

    __tablename__ = "user_identities"

    identity_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("auth_users.user_id", ondelete="CASCADE"), nullable=False)
    provider_id = Column(String, ForeignKey("auth_providers.provider_id"), nullable=False)
    provider_user = Column(String, nullable=False)
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=func.now())

    user = relationship("AuthUser")
    provider = relationship("AuthProvider", back_populates="identities")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UserIdentity(identity_id={self.identity_id}, user_id={self.user_id})>"


class ChatMemory(Base):
    """Chat memory metadata for user isolation"""

    __tablename__ = "chat_memories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("auth_users.user_id", ondelete="CASCADE"), nullable=False)
    chat_id = Column(String(36), nullable=False, index=True)
    short_term_days = Column(Integer, default=1, nullable=False)
    long_term_days = Column(Integer, default=30, nullable=False)
    tail_turns = Column(Integer, default=3, nullable=False)
    summarize_threshold_tokens = Column(Integer, default=3000, nullable=False)
    total_turns = Column(Integer, default=0, nullable=False)
    last_summarized_at = Column(DateTime)
    current_token_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("AuthUser", back_populates="chat_memories")

    __table_args__ = (
        Index("idx_chat_user_chat", "user_id", "chat_id"),
        Index("idx_chat_updated", "updated_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ChatMemory(id={self.id}, user_id={self.user_id}, chat_id={self.chat_id})>"


class PasswordResetToken(Base):
    """Password reset tokens"""

    __tablename__ = "password_reset_tokens"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("auth_users.user_id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    used_at = Column(DateTime)

    __table_args__ = (
        Index("idx_reset_token_expires", "token", "expires_at", "is_used"),
        Index("idx_reset_user", "user_id"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id})>"


class EmailVerificationToken(Base):
    """Email verification tokens"""

    __tablename__ = "email_verification_tokens"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("auth_users.user_id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    used_at = Column(DateTime)

    __table_args__ = (
        Index("idx_verify_token_expires", "token", "expires_at", "is_used"),
        Index("idx_verify_user", "user_id"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<EmailVerificationToken(id={self.id}, user_id={self.user_id})>"
