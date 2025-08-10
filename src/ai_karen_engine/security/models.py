"""
Enhanced authentication data models for intelligent authentication system.

This module provides comprehensive data models for authentication context,
analysis results, and configuration used by the intelligent authentication system.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class AuthEventType(Enum):
    """Types of authentication events for logging and monitoring."""

    LOGIN_ATTEMPT = "login_attempt"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGIN_FAILURE = "login_failure"
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
    ML_ANALYSIS_COMPLETED = "ml_analysis_completed"
    ML_ANALYSIS_FAILED = "ml_analysis_failed"


@dataclass
class UserData:
    """Unified user data model used across authentication components."""

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

    def __post_init__(self) -> None:
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
            "last_login_at": self.last_login_at.isoformat()
            if self.last_login_at
            else None,
            "failed_login_attempts": self.failed_login_attempts,
            "locked_until": self.locked_until.isoformat()
            if self.locked_until
            else None,
            "two_factor_enabled": self.two_factor_enabled,
            "two_factor_secret": self.two_factor_secret,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserData":
        """Create instance from dictionary."""
        created_at = (
            datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else None
        )
        updated_at = (
            datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else None
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
        """Validate basic user data."""
        return bool(self.user_id) and bool(self.email) and isinstance(self.roles, list)

    def is_locked(self) -> bool:
        return self.locked_until is not None and datetime.utcnow() < self.locked_until

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def add_role(self, role: str) -> None:
        if role not in self.roles:
            self.roles.append(role)
            self.updated_at = datetime.utcnow()

    def remove_role(self, role: str) -> None:
        if role in self.roles:
            self.roles.remove(role)
            self.updated_at = datetime.utcnow()


@dataclass
class SessionData:
    """Unified session data model for authentication sessions."""

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
        """Validate session data."""
        return (
            bool(self.session_token)
            and bool(self.access_token)
            and bool(self.refresh_token)
            and self.expires_in > 0
            and self.user_data.validate()
        )

    def is_expired(self) -> bool:
        if not self.is_active:
            return True
        expires_at = self.created_at + timedelta(seconds=self.expires_in)
        return datetime.utcnow() > expires_at

    def update_last_accessed(self) -> None:
        self.last_accessed = datetime.utcnow()

    def invalidate(self, reason: str = "manual") -> None:
        self.is_active = False
        self.invalidated_at = datetime.utcnow()
        self.invalidation_reason = reason

    def add_security_flag(self, flag: str) -> None:
        if flag not in self.security_flags:
            self.security_flags.append(flag)


@dataclass
class AuthEvent:
    """Unified authentication event model for logging and monitoring."""

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
            "service_version": self.service_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthEvent":
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
            service_version=data.get("service_version", "unknown"),
        )

    def validate(self) -> bool:
        """Validate authentication event."""
        return (
            isinstance(self.event_type, AuthEventType)
            and isinstance(self.timestamp, datetime)
            and 0.0 <= self.risk_score <= 1.0
        )

    def add_detail(self, key: str, value: Any) -> None:
        self.details[key] = value

    def add_security_flag(self, flag: str) -> None:
        if flag not in self.security_flags:
            self.security_flags.append(flag)

    def set_error(self, message: str) -> None:
        self.success = False
        self.error_message = message

    def set_processing_time(self, start_time: datetime) -> None:
        self.processing_time_ms = (
            datetime.utcnow() - start_time
        ).total_seconds() * 1000


class RiskLevel(Enum):
    """Risk level enumeration for authentication attempts."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityActionType(Enum):
    """Types of security actions that can be recommended."""

    BLOCK = "block"
    REQUIRE_2FA = "require_2fa"
    MONITOR = "monitor"
    ALERT = "alert"
    ALLOW = "allow"


@dataclass
class GeoLocation:
    """Geographical location information for authentication context."""

    country: str
    region: str
    city: str
    latitude: float
    longitude: float
    timezone: str
    is_usual_location: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GeoLocation:
        """Create instance from dictionary."""
        return cls(**data)

    def validate(self) -> bool:
        """Validate geolocation data."""
        return (
            -90 <= self.latitude <= 90
            and -180 <= self.longitude <= 180
            and bool(self.country)
            and bool(self.timezone)
        )


@dataclass
class AuthContext:
    """Enhanced authentication context with comprehensive metadata."""

    # Core authentication data
    email: str
    password_hash: str  # For analysis without storing plaintext
    client_ip: str
    user_agent: str
    timestamp: datetime
    request_id: str

    # Enhanced context data
    geolocation: Optional[GeoLocation] = None
    device_fingerprint: Optional[str] = None
    session_id: Optional[str] = None
    referrer: Optional[str] = None

    # Behavioral context
    time_since_last_login: Optional[timedelta] = None
    login_frequency_pattern: Optional[Dict[str, Any]] = None
    typical_login_hours: Optional[List[int]] = None

    # Security context
    is_tor_exit_node: bool = False
    is_vpn: bool = False
    threat_intel_score: float = 0.0
    previous_failed_attempts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Handle datetime serialization
        data["timestamp"] = self.timestamp.isoformat()
        if self.time_since_last_login:
            data["time_since_last_login"] = self.time_since_last_login.total_seconds()
        if self.geolocation:
            data["geolocation"] = self.geolocation.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuthContext:
        """Create instance from dictionary."""
        # Handle datetime deserialization
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if data.get("time_since_last_login") is not None:
            data["time_since_last_login"] = timedelta(
                seconds=data["time_since_last_login"]
            )
        if data.get("geolocation"):
            data["geolocation"] = GeoLocation.from_dict(data["geolocation"])
        return cls(**data)

    def validate(self) -> bool:
        """Validate authentication context data."""
        return (
            bool(self.email)
            and bool(self.password_hash)
            and bool(self.client_ip)
            and bool(self.user_agent)
            and bool(self.request_id)
            and isinstance(self.timestamp, datetime)
            and 0.0 <= self.threat_intel_score <= 1.0
            and self.previous_failed_attempts >= 0
        )


@dataclass
class CredentialFeatures:
    """Features extracted from credential analysis."""

    token_count: int
    unique_token_ratio: float
    entropy_score: float
    language: str
    contains_suspicious_patterns: bool
    pattern_types: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CredentialFeatures:
        """Create instance from dictionary."""
        return cls(**data)

    def validate(self) -> bool:
        """Validate credential features."""
        return (
            self.token_count >= 0
            and 0.0 <= self.unique_token_ratio <= 1.0
            and self.entropy_score >= 0.0
            and bool(self.language)
            and isinstance(self.pattern_types, list)
        )


@dataclass
class NLPFeatures:
    """NLP analysis features for authentication credentials."""

    # Credential analysis
    email_features: CredentialFeatures
    password_features: CredentialFeatures

    # Combined analysis
    credential_similarity: float
    language_consistency: bool
    suspicious_patterns: List[str] = field(default_factory=list)

    # Processing metadata
    processing_time: float = 0.0
    used_fallback: bool = False
    model_version: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "email_features": self.email_features.to_dict(),
            "password_features": self.password_features.to_dict(),
            "credential_similarity": self.credential_similarity,
            "language_consistency": self.language_consistency,
            "suspicious_patterns": self.suspicious_patterns,
            "processing_time": self.processing_time,
            "used_fallback": self.used_fallback,
            "model_version": self.model_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NLPFeatures:
        """Create instance from dictionary."""
        return cls(
            email_features=CredentialFeatures.from_dict(data["email_features"]),
            password_features=CredentialFeatures.from_dict(data["password_features"]),
            credential_similarity=data["credential_similarity"],
            language_consistency=data["language_consistency"],
            suspicious_patterns=data.get("suspicious_patterns", []),
            processing_time=data.get("processing_time", 0.0),
            used_fallback=data.get("used_fallback", False),
            model_version=data.get("model_version", "unknown"),
        )

    def validate(self) -> bool:
        """Validate NLP features."""
        return (
            self.email_features.validate()
            and self.password_features.validate()
            and 0.0 <= self.credential_similarity <= 1.0
            and self.processing_time >= 0.0
            and isinstance(self.suspicious_patterns, list)
        )


@dataclass
class EmbeddingAnalysis:
    """Embedding analysis results for behavioral patterns."""

    embedding_vector: List[float]
    similarity_to_user_profile: float
    similarity_to_attack_patterns: float
    cluster_assignment: Optional[str] = None
    outlier_score: float = 0.0
    processing_time: float = 0.0
    model_version: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EmbeddingAnalysis:
        """Create instance from dictionary."""
        return cls(**data)

    def validate(self) -> bool:
        """Validate embedding analysis."""
        return (
            isinstance(self.embedding_vector, list)
            and len(self.embedding_vector) > 0
            and all(isinstance(x, (int, float)) for x in self.embedding_vector)
            and 0.0 <= self.similarity_to_user_profile <= 1.0
            and 0.0 <= self.similarity_to_attack_patterns <= 1.0
            and 0.0 <= self.outlier_score <= 1.0
            and self.processing_time >= 0.0
        )


@dataclass
class BehavioralAnalysis:
    """Behavioral analysis results for user patterns."""

    # Temporal patterns
    is_usual_time: bool
    time_deviation_score: float

    # Location patterns
    is_usual_location: bool
    location_deviation_score: float

    # Device patterns
    is_known_device: bool
    device_similarity_score: float

    # Frequency patterns
    login_frequency_anomaly: float
    session_duration_anomaly: float

    # Historical context
    success_rate_last_30_days: float
    failed_attempts_pattern: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BehavioralAnalysis:
        """Create instance from dictionary."""
        return cls(**data)

    def validate(self) -> bool:
        """Validate behavioral analysis."""
        return (
            0.0 <= self.time_deviation_score <= 1.0
            and 0.0 <= self.location_deviation_score <= 1.0
            and 0.0 <= self.device_similarity_score <= 1.0
            and 0.0 <= self.login_frequency_anomaly <= 1.0
            and 0.0 <= self.session_duration_anomaly <= 1.0
            and 0.0 <= self.success_rate_last_30_days <= 1.0
            and isinstance(self.failed_attempts_pattern, dict)
        )


@dataclass
class BruteForceIndicators:
    """Indicators for brute force attack detection."""

    rapid_attempts: bool = False
    multiple_ips: bool = False
    password_variations: bool = False
    time_pattern_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BruteForceIndicators:
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class CredentialStuffingIndicators:
    """Indicators for credential stuffing attack detection."""

    multiple_accounts: bool = False
    common_passwords: bool = False
    distributed_sources: bool = False
    success_rate_pattern: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CredentialStuffingIndicators:
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class AccountTakeoverIndicators:
    """Indicators for account takeover detection."""

    location_anomaly: bool = False
    device_change: bool = False
    behavior_change: bool = False
    privilege_escalation: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AccountTakeoverIndicators:
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class ThreatAnalysis:
    """Comprehensive threat analysis results."""

    # Threat intelligence
    ip_reputation_score: float
    known_attack_patterns: List[str] = field(default_factory=list)
    threat_actor_indicators: List[str] = field(default_factory=list)

    # Attack detection
    brute_force_indicators: BruteForceIndicators = field(
        default_factory=BruteForceIndicators
    )
    credential_stuffing_indicators: CredentialStuffingIndicators = field(
        default_factory=CredentialStuffingIndicators
    )
    account_takeover_indicators: AccountTakeoverIndicators = field(
        default_factory=AccountTakeoverIndicators
    )

    # Global patterns
    similar_attacks_detected: int = 0
    attack_campaign_correlation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "ip_reputation_score": self.ip_reputation_score,
            "known_attack_patterns": self.known_attack_patterns,
            "threat_actor_indicators": self.threat_actor_indicators,
            "brute_force_indicators": self.brute_force_indicators.to_dict(),
            "credential_stuffing_indicators": self.credential_stuffing_indicators.to_dict(),
            "account_takeover_indicators": self.account_takeover_indicators.to_dict(),
            "similar_attacks_detected": self.similar_attacks_detected,
            "attack_campaign_correlation": self.attack_campaign_correlation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ThreatAnalysis:
        """Create instance from dictionary."""
        return cls(
            ip_reputation_score=data["ip_reputation_score"],
            known_attack_patterns=data.get("known_attack_patterns", []),
            threat_actor_indicators=data.get("threat_actor_indicators", []),
            brute_force_indicators=BruteForceIndicators.from_dict(
                data.get("brute_force_indicators", {})
            ),
            credential_stuffing_indicators=CredentialStuffingIndicators.from_dict(
                data.get("credential_stuffing_indicators", {})
            ),
            account_takeover_indicators=AccountTakeoverIndicators.from_dict(
                data.get("account_takeover_indicators", {})
            ),
            similar_attacks_detected=data.get("similar_attacks_detected", 0),
            attack_campaign_correlation=data.get("attack_campaign_correlation"),
        )

    def validate(self) -> bool:
        """Validate threat analysis."""
        return (
            0.0 <= self.ip_reputation_score <= 1.0
            and isinstance(self.known_attack_patterns, list)
            and isinstance(self.threat_actor_indicators, list)
            and self.similar_attacks_detected >= 0
        )


@dataclass
class SecurityAction:
    """Security action recommendation."""

    action_type: str
    priority: int
    description: str
    automated: bool
    requires_human_review: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SecurityAction:
        """Create instance from dictionary."""
        return cls(**data)

    def validate(self) -> bool:
        """Validate security action."""
        return bool(self.action_type) and self.priority > 0 and bool(self.description)


@dataclass
class AuthAnalysisResult:
    """Comprehensive authentication analysis result."""

    # Core results
    risk_score: float
    risk_level: RiskLevel
    should_block: bool
    requires_2fa: bool

    # Detailed analysis
    nlp_features: NLPFeatures
    embedding_analysis: EmbeddingAnalysis
    behavioral_analysis: BehavioralAnalysis
    threat_analysis: ThreatAnalysis

    # Processing metadata
    processing_time: float
    model_versions: Dict[str, str] = field(default_factory=dict)
    confidence_score: float = 0.0
    analysis_timestamp: datetime = field(default_factory=datetime.now)

    # Recommendations
    recommended_actions: List[SecurityAction] = field(default_factory=list)
    user_feedback_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "should_block": self.should_block,
            "requires_2fa": self.requires_2fa,
            "nlp_features": self.nlp_features.to_dict(),
            "embedding_analysis": self.embedding_analysis.to_dict(),
            "behavioral_analysis": self.behavioral_analysis.to_dict(),
            "threat_analysis": self.threat_analysis.to_dict(),
            "processing_time": self.processing_time,
            "model_versions": self.model_versions,
            "confidence_score": self.confidence_score,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "recommended_actions": [
                action.to_dict() for action in self.recommended_actions
            ],
            "user_feedback_required": self.user_feedback_required,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuthAnalysisResult:
        """Create instance from dictionary."""
        return cls(
            risk_score=data["risk_score"],
            risk_level=RiskLevel(data["risk_level"]),
            should_block=data["should_block"],
            requires_2fa=data["requires_2fa"],
            nlp_features=NLPFeatures.from_dict(data["nlp_features"]),
            embedding_analysis=EmbeddingAnalysis.from_dict(data["embedding_analysis"]),
            behavioral_analysis=BehavioralAnalysis.from_dict(
                data["behavioral_analysis"]
            ),
            threat_analysis=ThreatAnalysis.from_dict(data["threat_analysis"]),
            processing_time=data["processing_time"],
            model_versions=data.get("model_versions", {}),
            confidence_score=data.get("confidence_score", 0.0),
            analysis_timestamp=datetime.fromisoformat(
                data.get("analysis_timestamp", datetime.now().isoformat())
            ),
            recommended_actions=[
                SecurityAction.from_dict(action)
                for action in data.get("recommended_actions", [])
            ],
            user_feedback_required=data.get("user_feedback_required", False),
        )

    def validate(self) -> bool:
        """Validate analysis result."""
        return (
            0.0 <= self.risk_score <= 1.0
            and isinstance(self.risk_level, RiskLevel)
            and self.nlp_features.validate()
            and self.embedding_analysis.validate()
            and self.behavioral_analysis.validate()
            and self.threat_analysis.validate()
            and self.processing_time >= 0.0
            and 0.0 <= self.confidence_score <= 1.0
            and isinstance(self.analysis_timestamp, datetime)
            and all(action.validate() for action in self.recommended_actions)
        )


# Configuration Models


@dataclass
class RiskThresholds:
    """Risk threshold configuration for authentication decisions."""

    low_risk_threshold: float = 0.3
    medium_risk_threshold: float = 0.6
    high_risk_threshold: float = 0.8
    critical_risk_threshold: float = 0.95

    # Adaptive thresholds
    enable_adaptive_thresholds: bool = True
    user_specific_thresholds: bool = True
    time_based_adjustments: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RiskThresholds:
        """Create instance from dictionary."""
        return cls(**data)

    def validate(self) -> bool:
        """Validate risk thresholds."""
        return (
            0.0 <= self.low_risk_threshold <= 1.0
            and 0.0 <= self.medium_risk_threshold <= 1.0
            and 0.0 <= self.high_risk_threshold <= 1.0
            and 0.0 <= self.critical_risk_threshold <= 1.0
            and self.low_risk_threshold
            <= self.medium_risk_threshold
            <= self.high_risk_threshold
            <= self.critical_risk_threshold
        )


@dataclass
class FeatureFlags:
    """Feature flags for intelligent authentication components."""

    enable_geolocation_analysis: bool = True
    enable_device_fingerprinting: bool = True
    enable_threat_intelligence: bool = True
    enable_behavioral_learning: bool = True
    enable_attack_pattern_detection: bool = True
    enable_real_time_alerts: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FeatureFlags:
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class FallbackConfig:
    """Configuration for fallback behavior when ML services fail."""

    block_on_nlp_failure: bool = False
    block_on_embedding_failure: bool = False
    block_on_anomaly_failure: bool = False
    max_processing_timeout: float = 5.0
    fallback_risk_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FallbackConfig:
        """Create instance from dictionary."""
        return cls(**data)

    def validate(self) -> bool:
        """Validate fallback configuration."""
        return (
            self.max_processing_timeout > 0.0 and 0.0 <= self.fallback_risk_score <= 1.0
        )


@dataclass
class IntelligentAuthConfig:
    """Comprehensive configuration for intelligent authentication system."""

    # ML Service Configuration
    enable_nlp_analysis: bool = True
    enable_embedding_analysis: bool = True
    enable_behavioral_analysis: bool = True
    enable_threat_intelligence: bool = True

    # Risk Thresholds
    risk_thresholds: RiskThresholds = field(default_factory=RiskThresholds)

    # Performance Configuration
    max_processing_time: float = 5.0
    cache_size: int = 10000
    cache_ttl: int = 3600
    batch_size: int = 32

    # Fallback Configuration
    fallback_config: FallbackConfig = field(default_factory=FallbackConfig)

    # Feature Flags
    feature_flags: FeatureFlags = field(default_factory=FeatureFlags)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enable_nlp_analysis": self.enable_nlp_analysis,
            "enable_embedding_analysis": self.enable_embedding_analysis,
            "enable_behavioral_analysis": self.enable_behavioral_analysis,
            "enable_threat_intelligence": self.enable_threat_intelligence,
            "risk_thresholds": self.risk_thresholds.to_dict(),
            "max_processing_time": self.max_processing_time,
            "cache_size": self.cache_size,
            "cache_ttl": self.cache_ttl,
            "batch_size": self.batch_size,
            "fallback_config": self.fallback_config.to_dict(),
            "feature_flags": self.feature_flags.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> IntelligentAuthConfig:
        """Create instance from dictionary."""
        return cls(
            enable_nlp_analysis=data.get("enable_nlp_analysis", True),
            enable_embedding_analysis=data.get("enable_embedding_analysis", True),
            enable_behavioral_analysis=data.get("enable_behavioral_analysis", True),
            enable_threat_intelligence=data.get("enable_threat_intelligence", True),
            risk_thresholds=RiskThresholds.from_dict(data.get("risk_thresholds", {})),
            max_processing_time=data.get("max_processing_time", 5.0),
            cache_size=data.get("cache_size", 10000),
            cache_ttl=data.get("cache_ttl", 3600),
            batch_size=data.get("batch_size", 32),
            fallback_config=FallbackConfig.from_dict(data.get("fallback_config", {})),
            feature_flags=FeatureFlags.from_dict(data.get("feature_flags", {})),
        )

    @classmethod
    def from_env(cls) -> IntelligentAuthConfig:
        """Create configuration from environment variables."""
        import os

        def _get_bool(name: str, default: bool) -> bool:
            return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}

        def _get_float(name: str, default: float) -> float:
            try:
                return float(os.getenv(name, str(default)))
            except ValueError:
                return default

        def _get_int(name: str, default: int) -> int:
            try:
                return int(os.getenv(name, str(default)))
            except ValueError:
                return default

        risk_thresholds = RiskThresholds(
            low_risk_threshold=_get_float("INTELLIGENT_AUTH_RISK_LOW", 0.3),
            medium_risk_threshold=_get_float("INTELLIGENT_AUTH_RISK_MEDIUM", 0.6),
            high_risk_threshold=_get_float("INTELLIGENT_AUTH_RISK_HIGH", 0.8),
            critical_risk_threshold=_get_float("INTELLIGENT_AUTH_RISK_CRITICAL", 0.95),
            enable_adaptive_thresholds=_get_bool(
                "INTELLIGENT_AUTH_RISK_ADAPTIVE", True
            ),
            user_specific_thresholds=_get_bool(
                "INTELLIGENT_AUTH_RISK_USER_SPECIFIC", True
            ),
            time_based_adjustments=_get_bool("INTELLIGENT_AUTH_RISK_TIME_BASED", True),
        )

        fallback_config = FallbackConfig(
            block_on_nlp_failure=_get_bool(
                "INTELLIGENT_AUTH_FALLBACK_BLOCK_NLP", False
            ),
            block_on_embedding_failure=_get_bool(
                "INTELLIGENT_AUTH_FALLBACK_BLOCK_EMBEDDING", False
            ),
            block_on_anomaly_failure=_get_bool(
                "INTELLIGENT_AUTH_FALLBACK_BLOCK_ANOMALY", False
            ),
            max_processing_timeout=_get_float(
                "INTELLIGENT_AUTH_FALLBACK_MAX_TIMEOUT", 5.0
            ),
            fallback_risk_score=_get_float("INTELLIGENT_AUTH_FALLBACK_RISK_SCORE", 0.0),
        )

        feature_flags = FeatureFlags(
            enable_geolocation_analysis=_get_bool(
                "INTELLIGENT_AUTH_FEATURE_GEOLOCATION", True
            ),
            enable_device_fingerprinting=_get_bool(
                "INTELLIGENT_AUTH_FEATURE_DEVICE_FP", True
            ),
            enable_threat_intelligence=_get_bool(
                "INTELLIGENT_AUTH_FEATURE_THREAT_INTEL", True
            ),
            enable_behavioral_learning=_get_bool(
                "INTELLIGENT_AUTH_FEATURE_BEHAVIORAL_LEARNING", True
            ),
            enable_attack_pattern_detection=_get_bool(
                "INTELLIGENT_AUTH_FEATURE_ATTACK_PATTERN", True
            ),
            enable_real_time_alerts=_get_bool(
                "INTELLIGENT_AUTH_FEATURE_REAL_TIME_ALERTS", True
            ),
        )

        config = cls(
            enable_nlp_analysis=_get_bool("INTELLIGENT_AUTH_ENABLE_NLP", True),
            enable_embedding_analysis=_get_bool(
                "INTELLIGENT_AUTH_ENABLE_EMBEDDING", True
            ),
            enable_behavioral_analysis=_get_bool(
                "INTELLIGENT_AUTH_ENABLE_BEHAVIORAL", True
            ),
            enable_threat_intelligence=_get_bool(
                "INTELLIGENT_AUTH_ENABLE_THREAT_INTEL", True
            ),
            risk_thresholds=risk_thresholds,
            max_processing_time=_get_float("INTELLIGENT_AUTH_MAX_PROCESSING_TIME", 5.0),
            cache_size=_get_int("INTELLIGENT_AUTH_CACHE_SIZE", 10000),
            cache_ttl=_get_int("INTELLIGENT_AUTH_CACHE_TTL", 3600),
            batch_size=_get_int("INTELLIGENT_AUTH_BATCH_SIZE", 32),
            fallback_config=fallback_config,
            feature_flags=feature_flags,
        )

        if not risk_thresholds.validate():
            raise ValueError("Invalid risk threshold values in environment variables")
        if not fallback_config.validate():
            raise ValueError(
                "Invalid fallback configuration values in environment variables"
            )
        if not config.validate():
            raise ValueError(
                "Invalid IntelligentAuthConfig values in environment variables"
            )

        return config

    def validate(self) -> bool:
        """Validate configuration."""
        return (
            self.max_processing_time > 0.0
            and self.cache_size > 0
            and self.cache_ttl > 0
            and self.batch_size > 0
            and self.risk_thresholds.validate()
            and self.fallback_config.validate()
        )

    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save configuration to JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> IntelligentAuthConfig:
        """Load configuration from JSON file."""
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)
