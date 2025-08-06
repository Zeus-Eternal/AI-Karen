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

from ai_karen_engine.security.models import (
    AuthEvent,
    AuthEventType,
    SessionData,
    UserData,
)


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