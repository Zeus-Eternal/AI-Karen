"""
Production Database Models for Authentication
SQLAlchemy models for users, sessions, and authentication data
"""

import uuid
from datetime import datetime
from typing import Optional, Any, Dict, List

from sqlalchemy import (
    Column, String, DateTime, Boolean, Integer, Text, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """Production user model with proper security"""
    __tablename__ = "users"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile fields
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Role and permissions
    roles = Column(Text, nullable=False, default="user")  # JSON array of roles
    tenant_id = Column(String(36), nullable=False, default="default")

    # Preferences
    preferences = Column(Text, nullable=True)  # JSON preferences

    # 2FA settings
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(String(32), nullable=True)
    backup_codes = Column(Text, nullable=True)  # JSON array of backup codes

    # Security tracking
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)  # IPv6 compatible

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    chat_memories = relationship("ChatMemory", back_populates="user", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_user_email_active", "email", "is_active"),
        Index("idx_user_tenant", "tenant_id"),
        Index("idx_user_created", "created_at"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class UserSession(Base):
    """Production session management"""
    __tablename__ = "user_sessions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Session data
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=True, index=True)

    # Session metadata
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    device_fingerprint = Column(String(255), nullable=True)

    # Session state
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, default=func.now(), nullable=False)

    # Security flags
    is_suspicious = Column(Boolean, default=False, nullable=False)
    risk_score = Column(Integer, default=0, nullable=False)  # 0-100 risk score

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")

    # Indexes
    __table_args__ = (
        Index("idx_session_token_active", "session_token", "is_active"),
        Index("idx_session_user_active", "user_id", "is_active"),
        Index("idx_session_expires", "expires_at"),
        Index("idx_session_activity", "last_activity_at"),
    )

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"


class ChatMemory(Base):
    """Chat memory metadata for user isolation"""
    __tablename__ = "chat_memories"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Chat identification
    chat_id = Column(String(36), nullable=False, index=True)

    # Memory settings (user-configurable)
    short_term_days = Column(Integer, default=1, nullable=False)
    long_term_days = Column(Integer, default=30, nullable=False)
    tail_turns = Column(Integer, default=3, nullable=False)
    summarize_threshold_tokens = Column(Integer, default=3000, nullable=False)

    # Memory state
    total_turns = Column(Integer, default=0, nullable=False)
    last_summarized_at = Column(DateTime, nullable=True)
    current_token_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="chat_memories")

    # Indexes
    __table_args__ = (
        Index("idx_chat_user_chat", "user_id", "chat_id"),
        Index("idx_chat_updated", "updated_at"),
    )

    def __repr__(self):
        return f"<ChatMemory(id={self.id}, user_id={self.user_id}, chat_id={self.chat_id})>"


class PasswordResetToken(Base):
    """Password reset tokens"""
    __tablename__ = "password_reset_tokens"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Token data
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)

    # Security tracking
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    used_at = Column(DateTime, nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_reset_token_expires", "token", "expires_at", "is_used"),
        Index("idx_reset_user", "user_id"),
    )

    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id})>"


class EmailVerificationToken(Base):
    """Email verification tokens"""
    __tablename__ = "email_verification_tokens"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Token data
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    used_at = Column(DateTime, nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_verify_token_expires", "token", "expires_at", "is_used"),
        Index("idx_verify_user", "user_id"),
    )

    def __repr__(self):
        return f"<EmailVerificationToken(id={self.id}, user_id={self.user_id})>"
