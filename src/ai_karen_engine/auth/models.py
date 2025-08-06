"""
Unified Authentication Data Models

This module provides consistent data models for all authentication components
in the consolidated authentication system. These models replace the scattered
data structures used across different auth services.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pathlib import Path


# Enums for type safety and consistency

class AuthEventType(Enum):
    """Types of authentication events for logging and monitoring."""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    SESSION_CREATED = "session_created"
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


class SessionStorageType(Enum):
    """Types of session storage backends."""
    DATABASE = "database"
    REDIS = "redis"
    MEMORY = "memory"


class AuthMode(Enum):
    """Authentication modes for different deployment scenarios."""
    BASIC = "basic"              # Simple username/password
    ENHANCED = "enhanced"        # With security features (rate limiting, audit logging)
    INTELLIGENT = "intelligent"  # With ML-based behavioral analysis
    PRODUCTION = "production"    # Full production features


# Core Data Models

@dataclass
class UserData:
    """
    Unified user data model used across all authentication components.
    
    This replaces the various UserData classes scattered across different
    auth services with a single, comprehensive model.
    """
    user_id: str
    email: str
    full_name: Optional[str] = None
    roles: List[str] = field(default_factory=lambda: ["user"])
    tenant_id: str = "default"
    preferences: Dict[str, Any] = field(default_factory=dict)
    is_verified: bool = True
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Additional fields for enhanced functionality
    last_login_at: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None
    
    def __post_init__(self):
        """Set default timestamps if not provided."""
        now = datetime.utcnow()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now
    
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
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "failed_login_attempts": self.failed_login_attempts,
            "locked_until": self.locked_until.isoformat() if self.locked_until else None,
            "two_factor_enabled": self.two_factor_enabled,
            "two_factor_secret": self.two_factor_secret
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UserData:
        """Create instance from dictionary."""
        # Handle datetime deserialization
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        
        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])
        
        last_login_at = None
        if data.get("last_login_at"):
            last_login_at = datetime.fromisoformat(data["last_login_at"])
        
        locked_until = None
        if data.get("locked_until"):
            locked_until = datetime.fromisoformat(data["locked_until"])
        
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
            two_factor_secret=data.get("two_factor_secret")
        )
    
    def is_locked(self) -> bool:
        """Check if user account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
    
    def add_role(self, role: str) -> None:
        """Add a role to the user."""
        if role not in self.roles:
            self.roles.append(role)
            self.updated_at = datetime.utcnow()
    
    def remove_role(self, role: str) -> None:
        """Remove a role from the user."""
        if role in self.roles:
            self.roles.remove(role)
            self.updated_at = datetime.utcnow()


@dataclass
class SessionData:
    """
    Unified session data model used across all authentication components.
    
    This replaces the various SessionData classes with a single, comprehensive model
    that supports different token types and security features.
    """
    session_token: str
    access_token: str
    refresh_token: str
    user_data: UserData
    expires_in: int  # Seconds until access token expires
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    
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
            "invalidated_at": self.invalidated_at.isoformat() if self.invalidated_at else None,
            "invalidation_reason": self.invalidation_reason
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SessionData:
        """Create instance from dictionary."""
        created_at = datetime.fromisoformat(data["created_at"])
        last_accessed = datetime.fromisoformat(data["last_accessed"])
        
        invalidated_at = None
        if data.get("invalidated_at"):
            invalidated_at = datetime.fromisoformat(data["invalidated_at"])
        
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
            invalidation_reason=data.get("invalidation_reason")
        )
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        if not self.is_active:
            return True
        
        # Check if access token has expired
        expires_at = self.created_at + timedelta(seconds=self.expires_in)
        return datetime.utcnow() > expires_at
    
    def update_last_accessed(self) -> None:
        """Update the last accessed timestamp."""
        self.last_accessed = datetime.utcnow()
    
    def invalidate(self, reason: str = "manual") -> None:
        """Invalidate the session."""
        self.is_active = False
        self.invalidated_at = datetime.utcnow()
        self.invalidation_reason = reason
    
    def add_security_flag(self, flag: str) -> None:
        """Add a security flag to the session."""
        if flag not in self.security_flags:
            self.security_flags.append(flag)


@dataclass
class AuthEvent:
    """
    Unified authentication event model for logging and monitoring.
    
    This provides comprehensive event tracking across all authentication
    operations for security monitoring and audit purposes.
    """
    event_type: AuthEventType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
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
    service_version: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
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
            "service_version": self.service_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuthEvent:
        """Create instance from dictionary."""
        return cls(
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
            service_version=data.get("service_version", "unknown")
        )
    
    def add_detail(self, key: str, value: Any) -> None:
        """Add a detail to the event."""
        self.details[key] = value
    
    def add_security_flag(self, flag: str) -> None:
        """Add a security flag to the event."""
        if flag not in self.security_flags:
            self.security_flags.append(flag)
    
    def set_error(self, message: str) -> None:
        """Mark event as failed with error message."""
        self.success = False
        self.error_message = message
    
    def set_processing_time(self, start_time: datetime) -> None:
        """Set processing time based on start time."""
        self.processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000


# Additional Models for Enhanced Functionality

@dataclass
class PasswordResetToken:
    """Model for password reset tokens."""
    token: str
    user_id: str
    email: str
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)
    used_at: Optional[datetime] = None
    ip_address: str = "unknown"
    user_agent: str = ""
    
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_used(self) -> bool:
        """Check if token has been used."""
        return self.used_at is not None
    
    def mark_used(self) -> None:
        """Mark token as used."""
        self.used_at = datetime.utcnow()


@dataclass
class RateLimitInfo:
    """Model for rate limiting information."""
    identifier: str  # IP address, user ID, etc.
    attempts: int
    window_start: datetime
    window_duration: timedelta
    max_attempts: int
    locked_until: Optional[datetime] = None
    
    def is_locked(self) -> bool:
        """Check if identifier is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def is_window_expired(self) -> bool:
        """Check if current window has expired."""
        return datetime.utcnow() > (self.window_start + self.window_duration)
    
    def reset_window(self) -> None:
        """Reset the rate limit window."""
        self.attempts = 0
        self.window_start = datetime.utcnow()
        self.locked_until = None
    
    def add_attempt(self) -> bool:
        """Add an attempt and return if limit is exceeded."""
        if self.is_window_expired():
            self.reset_window()
        
        self.attempts += 1
        
        if self.attempts > self.max_attempts:
            # Lock for the remaining window duration
            remaining_time = (self.window_start + self.window_duration) - datetime.utcnow()
            self.locked_until = datetime.utcnow() + remaining_time
            return True
        
        return False


@dataclass
class SecurityResult:
    """Result from security enhancement checks."""
    allowed: bool
    risk_score: float
    flags: List[str] = field(default_factory=list)
    reason: Optional[str] = None
    recommended_action: Optional[str] = None
    requires_2fa: bool = False
    
    def add_flag(self, flag: str) -> None:
        """Add a security flag."""
        if flag not in self.flags:
            self.flags.append(flag)
    
    def block(self, reason: str) -> None:
        """Block the request with a reason."""
        self.allowed = False
        self.reason = reason
    
    def require_2fa(self, reason: str) -> None:
        """Require 2FA with a reason."""
        self.requires_2fa = True
        self.recommended_action = f"2FA required: {reason}"


@dataclass
class IntelligenceResult:
    """Result from intelligence layer analysis."""
    risk_score: float
    confidence: float
    anomaly_detected: bool
    behavioral_flags: List[str] = field(default_factory=list)
    threat_indicators: List[str] = field(default_factory=list)
    recommended_action: Optional[str] = None
    processing_time_ms: float = 0.0
    
    def add_behavioral_flag(self, flag: str) -> None:
        """Add a behavioral analysis flag."""
        if flag not in self.behavioral_flags:
            self.behavioral_flags.append(flag)
    
    def add_threat_indicator(self, indicator: str) -> None:
        """Add a threat indicator."""
        if indicator not in self.threat_indicators:
            self.threat_indicators.append(indicator)