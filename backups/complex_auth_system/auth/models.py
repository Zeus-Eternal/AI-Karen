"""
Unified data models for the consolidated authentication service.

This module provides consistent data models that all authentication components
will use, replacing the fragmented models across different auth services.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class AuthEventType(Enum):
    """Types of authentication events for logging and monitoring."""

    LOGIN_ATTEMPT = "login_attempt"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGIN_BLOCKED = "login_blocked"
    LOGOUT = "logout"
    SESSION_CREATED = "session_created"
    SESSION_VALIDATED = "session_validated"
    SESSION_EXPIRED = "session_expired"
    SESSION_INVALIDATED = "session_invalidated"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    PASSWORD_CHANGED = "password_changed"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DEACTIVATED = "user_deactivated"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SECURITY_BLOCK = "security_block"
    TWO_FACTOR_REQUIRED = "two_factor_required"
    TWO_FACTOR_SUCCESS = "two_factor_success"
    TWO_FACTOR_FAILED = "two_factor_failed"
    ANOMALY_DETECTED = "anomaly_detected"
    THREAT_DETECTED = "threat_detected"
    PROFILE_UPDATED = "profile_updated"


@dataclass
class UserData:
    """
    Unified user data model used across all authentication components.

    This replaces the various user data structures used by different
    authentication services with a single, consistent model.
    """

    user_id: str
    email: str
    full_name: Optional[str] = None
    roles: List[str] = field(default_factory=lambda: ["user"])
    tenant_id: str = "default"
    preferences: Dict[str, Any] = field(default_factory=dict)
    is_verified: bool = True
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Security and session management fields
    last_login_at: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None

    def __post_init__(self) -> None:
        """Ensure timestamps are set if not provided."""
        if not isinstance(self.created_at, datetime):
            self.created_at = datetime.now(timezone.utc)
        if not isinstance(self.updated_at, datetime):
            self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "full_name": self.full_name,
            "roles": self.roles,
            "tenant_id": self.tenant_id,
            "preferences": self.preferences,
            "is_verified": self.is_verified,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_login_at": self.last_login_at.isoformat()
            if self.last_login_at
            else None,
            "failed_login_attempts": self.failed_login_attempts,
            "locked_until": self.locked_until.isoformat()
            if self.locked_until
            else None,
            "two_factor_enabled": self.two_factor_enabled,
            # Never expose the raw two-factor secret when serializing.
            # Keep the key for backward compatibility but mask the value.
            "two_factor_secret": None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserData":
        """Create instance from dictionary."""
        # Handle datetime deserialization
        created_at = (
            datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now(timezone.utc)
        )
        updated_at = (
            datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else datetime.now(timezone.utc)
        )
        last_login_at = (
            datetime.fromisoformat(data["last_login_at"])
            if data.get("last_login_at")
            else None
        )
        locked_until = (
            datetime.fromisoformat(data["locked_until"])
            if data.get("locked_until")
            else None
        )

        return cls(
            user_id=data["user_id"],
            email=data["email"],
            full_name=data.get("full_name"),
            roles=data.get("roles", ["user"]),
            tenant_id=data.get("tenant_id", "default"),
            preferences=data.get("preferences", {}),
            is_verified=data.get("is_verified", True),
            is_active=data.get("is_active", True),
            created_at=created_at,
            updated_at=updated_at,
            last_login_at=last_login_at,
            failed_login_attempts=data.get("failed_login_attempts", 0),
            locked_until=locked_until,
            two_factor_enabled=data.get("two_factor_enabled", False),
            two_factor_secret=data.get("two_factor_secret"),
        )

    def validate(self) -> bool:
        """Validate user data integrity."""
        return (
            bool(self.user_id)
            and bool(self.email)
            and isinstance(self.roles, list)
            and self.failed_login_attempts >= 0
            and isinstance(self.preferences, dict)
        )

    def is_locked(self) -> bool:
        """Check if user account is currently locked."""
        return (
            bool(self.locked_until) and datetime.now(timezone.utc) < self.locked_until
        )

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles

    def add_role(self, role: str) -> None:
        """Add a role to the user."""
        if role not in self.roles:
            self.roles.append(role)
            self.updated_at = datetime.now(timezone.utc)

    def remove_role(self, role: str) -> None:
        """Remove a role from the user."""
        if role in self.roles:
            self.roles.remove(role)
            self.updated_at = datetime.now(timezone.utc)

    def update_last_login(self) -> None:
        """Update the last login timestamp."""
        self.last_login_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def increment_failed_attempts(self) -> None:
        """Increment failed login attempts counter."""
        self.failed_login_attempts += 1
        self.updated_at = datetime.now(timezone.utc)

    def reset_failed_attempts(self) -> None:
        """Reset failed login attempts counter."""
        self.failed_login_attempts = 0
        self.updated_at = datetime.now(timezone.utc)

    def lock_account(self, duration_minutes: int = 15) -> None:
        """Lock the account for a specified duration."""
        self.locked_until = datetime.now(timezone.utc) + timedelta(
            minutes=duration_minutes
        )
        self.updated_at = datetime.now(timezone.utc)

    def unlock_account(self) -> None:
        """Unlock the account."""
        self.locked_until = None
        self.failed_login_attempts = 0
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class SessionData:
    """
    Unified session data model for authentication sessions.

    This consolidates session management across all authentication services
    with comprehensive security and tracking information.
    """

    session_token: str
    access_token: str
    refresh_token: str
    user_data: UserData
    expires_in: int  # Seconds until access token expires
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Security context
    ip_address: str = "unknown"
    user_agent: str = ""
    device_fingerprint: Optional[str] = None
    geolocation: Optional[Dict[str, Any]] = None

    # Risk assessment
    risk_score: float = 0.0
    security_flags: List[str] = field(default_factory=list)

    # Session management
    is_active: bool = True
    invalidated_at: Optional[datetime] = None
    invalidation_reason: Optional[str] = None

    def __post_init__(self) -> None:
        """Ensure timestamps are set if not provided."""
        if not isinstance(self.created_at, datetime):
            self.created_at = datetime.now(timezone.utc)
        if not isinstance(self.last_accessed, datetime):
            self.last_accessed = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_token": self.session_token,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "user_data": self.user_data.to_dict(),
            "expires_in": self.expires_in,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "device_fingerprint": self.device_fingerprint,
            "geolocation": self.geolocation,
            "risk_score": self.risk_score,
            "security_flags": self.security_flags,
            "is_active": self.is_active,
            "invalidated_at": self.invalidated_at.isoformat()
            if self.invalidated_at
            else None,
            "invalidation_reason": self.invalidation_reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """Create instance from dictionary."""
        created_at = datetime.fromisoformat(data["created_at"])
        last_accessed = datetime.fromisoformat(data["last_accessed"])
        invalidated_at = (
            datetime.fromisoformat(data["invalidated_at"])
            if data.get("invalidated_at")
            else None
        )

        return cls(
            session_token=data["session_token"],
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            user_data=UserData.from_dict(data["user_data"]),
            expires_in=data["expires_in"],
            created_at=created_at,
            last_accessed=last_accessed,
            ip_address=data.get("ip_address", "unknown"),
            user_agent=data.get("user_agent", ""),
            device_fingerprint=data.get("device_fingerprint"),
            geolocation=data.get("geolocation"),
            risk_score=data.get("risk_score", 0.0),
            security_flags=data.get("security_flags", []),
            is_active=data.get("is_active", True),
            invalidated_at=invalidated_at,
            invalidation_reason=data.get("invalidation_reason"),
        )

    def validate(self) -> bool:
        """Validate session data integrity."""
        return (
            bool(self.session_token)
            and bool(self.access_token)
            and bool(self.refresh_token)
            and self.expires_in > 0
            and self.user_data.validate()
            and 0.0 <= self.risk_score <= 1.0
        )

    def is_expired(self) -> bool:
        """Check if the session has expired."""
        if not self.is_active:
            return True
        expires_at = self.created_at + timedelta(seconds=self.expires_in)
        return datetime.now(timezone.utc) > expires_at

    def update_last_accessed(self) -> None:
        """Update the last accessed timestamp."""
        self.last_accessed = datetime.now(timezone.utc)

    def invalidate(self, reason: str = "manual") -> None:
        """Invalidate the session."""
        self.is_active = False
        self.invalidated_at = datetime.now(timezone.utc)
        self.invalidation_reason = reason

    def add_security_flag(self, flag: str) -> None:
        """Add a security flag to the session."""
        if flag not in self.security_flags:
            self.security_flags.append(flag)

    def remove_security_flag(self, flag: str) -> None:
        """Remove a security flag from the session."""
        if flag in self.security_flags:
            self.security_flags.remove(flag)

    def update_risk_score(self, score: float) -> None:
        """Update the risk score for the session."""
        self.risk_score = max(0.0, min(1.0, score))  # Clamp between 0 and 1


@dataclass
class AuthEvent:
    """
    Unified authentication event model for logging and monitoring.

    This provides consistent event tracking across all authentication
    operations for security monitoring and audit purposes.
    """

    event_type: AuthEventType
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: str = field(default_factory=lambda: str(uuid4()))

    # User context
    user_id: Optional[str] = None
    email: Optional[str] = None
    tenant_id: Optional[str] = None

    # Request context
    ip_address: str = "unknown"
    user_agent: str = ""
    request_id: Optional[str] = None
    session_token: Optional[str] = None

    # Event details
    success: bool = True
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    # Security context
    risk_score: float = 0.0
    security_flags: List[str] = field(default_factory=list)
    blocked_by_security: bool = False

    # Processing metadata
    processing_time_ms: float = 0.0
    service_version: str = "consolidated-auth-v1"

    def __post_init__(self) -> None:
        """Ensure timestamp is set if not provided."""
        if not isinstance(self.timestamp, datetime):
            self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "email": self.email,
            "tenant_id": self.tenant_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
            "session_token": self.session_token,
            "success": self.success,
            "error_message": self.error_message,
            "details": self.details,
            "risk_score": self.risk_score,
            "security_flags": self.security_flags,
            "blocked_by_security": self.blocked_by_security,
            "processing_time_ms": self.processing_time_ms,
            "service_version": self.service_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthEvent":
        """Create instance from dictionary."""
        return cls(
            event_id=data.get("event_id", str(uuid4())),
            event_type=AuthEventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            user_id=data.get("user_id"),
            email=data.get("email"),
            tenant_id=data.get("tenant_id"),
            ip_address=data.get("ip_address", "unknown"),
            user_agent=data.get("user_agent", ""),
            request_id=data.get("request_id"),
            session_token=data.get("session_token"),
            success=data.get("success", True),
            error_message=data.get("error_message"),
            details=data.get("details", {}),
            risk_score=data.get("risk_score", 0.0),
            security_flags=data.get("security_flags", []),
            blocked_by_security=data.get("blocked_by_security", False),
            processing_time_ms=data.get("processing_time_ms", 0.0),
            service_version=data.get("service_version", "consolidated-auth-v1"),
        )

    def validate(self) -> bool:
        """Validate authentication event data."""
        return (
            isinstance(self.event_type, AuthEventType)
            and isinstance(self.timestamp, datetime)
            and 0.0 <= self.risk_score <= 1.0
            and self.processing_time_ms >= 0.0
            and isinstance(self.details, dict)
            and isinstance(self.security_flags, list)
        )

    def add_detail(self, key: str, value: Any) -> None:
        """Add a detail to the event."""
        self.details[key] = value

    def add_security_flag(self, flag: str) -> None:
        """Add a security flag to the event."""
        if flag not in self.security_flags:
            self.security_flags.append(flag)

    def set_error(self, message: str) -> None:
        """Mark the event as failed with an error message."""
        self.success = False
        self.error_message = message

    def set_processing_time(self, start_time: datetime) -> None:
        """Set the processing time based on start time."""
        self.processing_time_ms = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds() * 1000

    def mark_blocked_by_security(self, reason: str) -> None:
        """Mark the event as blocked by security measures."""
        self.blocked_by_security = True
        self.success = False
        self.add_detail("security_block_reason", reason)
