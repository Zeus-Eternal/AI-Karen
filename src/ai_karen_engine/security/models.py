"""
Enhanced authentication data models for intelligent authentication system.

This module provides comprehensive data models for authentication context,
analysis results, and configuration used by the intelligent authentication system.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pathlib import Path


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
            -90 <= self.latitude <= 90 and
            -180 <= self.longitude <= 180 and
            bool(self.country) and
            bool(self.timezone)
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
        data['timestamp'] = self.timestamp.isoformat()
        if self.time_since_last_login:
            data['time_since_last_login'] = self.time_since_last_login.total_seconds()
        if self.geolocation:
            data['geolocation'] = self.geolocation.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuthContext:
        """Create instance from dictionary."""
        # Handle datetime deserialization
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if data.get('time_since_last_login') is not None:
            data['time_since_last_login'] = timedelta(seconds=data['time_since_last_login'])
        if data.get('geolocation'):
            data['geolocation'] = GeoLocation.from_dict(data['geolocation'])
        return cls(**data)

    def validate(self) -> bool:
        """Validate authentication context data."""
        return (
            bool(self.email) and
            bool(self.password_hash) and
            bool(self.client_ip) and
            bool(self.user_agent) and
            bool(self.request_id) and
            isinstance(self.timestamp, datetime) and
            0.0 <= self.threat_intel_score <= 1.0 and
            self.previous_failed_attempts >= 0
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
            self.token_count >= 0 and
            0.0 <= self.unique_token_ratio <= 1.0 and
            self.entropy_score >= 0.0 and
            bool(self.language) and
            isinstance(self.pattern_types, list)
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
            'email_features': self.email_features.to_dict(),
            'password_features': self.password_features.to_dict(),
            'credential_similarity': self.credential_similarity,
            'language_consistency': self.language_consistency,
            'suspicious_patterns': self.suspicious_patterns,
            'processing_time': self.processing_time,
            'used_fallback': self.used_fallback,
            'model_version': self.model_version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NLPFeatures:
        """Create instance from dictionary."""
        return cls(
            email_features=CredentialFeatures.from_dict(data['email_features']),
            password_features=CredentialFeatures.from_dict(data['password_features']),
            credential_similarity=data['credential_similarity'],
            language_consistency=data['language_consistency'],
            suspicious_patterns=data.get('suspicious_patterns', []),
            processing_time=data.get('processing_time', 0.0),
            used_fallback=data.get('used_fallback', False),
            model_version=data.get('model_version', 'unknown')
        )

    def validate(self) -> bool:
        """Validate NLP features."""
        return (
            self.email_features.validate() and
            self.password_features.validate() and
            0.0 <= self.credential_similarity <= 1.0 and
            self.processing_time >= 0.0 and
            isinstance(self.suspicious_patterns, list)
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
            isinstance(self.embedding_vector, list) and
            len(self.embedding_vector) > 0 and
            all(isinstance(x, (int, float)) for x in self.embedding_vector) and
            0.0 <= self.similarity_to_user_profile <= 1.0 and
            0.0 <= self.similarity_to_attack_patterns <= 1.0 and
            0.0 <= self.outlier_score <= 1.0 and
            self.processing_time >= 0.0
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
            0.0 <= self.time_deviation_score <= 1.0 and
            0.0 <= self.location_deviation_score <= 1.0 and
            0.0 <= self.device_similarity_score <= 1.0 and
            0.0 <= self.login_frequency_anomaly <= 1.0 and
            0.0 <= self.session_duration_anomaly <= 1.0 and
            0.0 <= self.success_rate_last_30_days <= 1.0 and
            isinstance(self.failed_attempts_pattern, dict)
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
    brute_force_indicators: BruteForceIndicators = field(default_factory=BruteForceIndicators)
    credential_stuffing_indicators: CredentialStuffingIndicators = field(default_factory=CredentialStuffingIndicators)
    account_takeover_indicators: AccountTakeoverIndicators = field(default_factory=AccountTakeoverIndicators)

    # Global patterns
    similar_attacks_detected: int = 0
    attack_campaign_correlation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'ip_reputation_score': self.ip_reputation_score,
            'known_attack_patterns': self.known_attack_patterns,
            'threat_actor_indicators': self.threat_actor_indicators,
            'brute_force_indicators': self.brute_force_indicators.to_dict(),
            'credential_stuffing_indicators': self.credential_stuffing_indicators.to_dict(),
            'account_takeover_indicators': self.account_takeover_indicators.to_dict(),
            'similar_attacks_detected': self.similar_attacks_detected,
            'attack_campaign_correlation': self.attack_campaign_correlation
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ThreatAnalysis:
        """Create instance from dictionary."""
        return cls(
            ip_reputation_score=data['ip_reputation_score'],
            known_attack_patterns=data.get('known_attack_patterns', []),
            threat_actor_indicators=data.get('threat_actor_indicators', []),
            brute_force_indicators=BruteForceIndicators.from_dict(data.get('brute_force_indicators', {})),
            credential_stuffing_indicators=CredentialStuffingIndicators.from_dict(data.get('credential_stuffing_indicators', {})),
            account_takeover_indicators=AccountTakeoverIndicators.from_dict(data.get('account_takeover_indicators', {})),
            similar_attacks_detected=data.get('similar_attacks_detected', 0),
            attack_campaign_correlation=data.get('attack_campaign_correlation')
        )

    def validate(self) -> bool:
        """Validate threat analysis."""
        return (
            0.0 <= self.ip_reputation_score <= 1.0 and
            isinstance(self.known_attack_patterns, list) and
            isinstance(self.threat_actor_indicators, list) and
            self.similar_attacks_detected >= 0
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
        return (
            bool(self.action_type) and
            self.priority > 0 and
            bool(self.description)
        )


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
            'risk_score': self.risk_score,
            'risk_level': self.risk_level.value,
            'should_block': self.should_block,
            'requires_2fa': self.requires_2fa,
            'nlp_features': self.nlp_features.to_dict(),
            'embedding_analysis': self.embedding_analysis.to_dict(),
            'behavioral_analysis': self.behavioral_analysis.to_dict(),
            'threat_analysis': self.threat_analysis.to_dict(),
            'processing_time': self.processing_time,
            'model_versions': self.model_versions,
            'confidence_score': self.confidence_score,
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'recommended_actions': [action.to_dict() for action in self.recommended_actions],
            'user_feedback_required': self.user_feedback_required
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuthAnalysisResult:
        """Create instance from dictionary."""
        return cls(
            risk_score=data['risk_score'],
            risk_level=RiskLevel(data['risk_level']),
            should_block=data['should_block'],
            requires_2fa=data['requires_2fa'],
            nlp_features=NLPFeatures.from_dict(data['nlp_features']),
            embedding_analysis=EmbeddingAnalysis.from_dict(data['embedding_analysis']),
            behavioral_analysis=BehavioralAnalysis.from_dict(data['behavioral_analysis']),
            threat_analysis=ThreatAnalysis.from_dict(data['threat_analysis']),
            processing_time=data['processing_time'],
            model_versions=data.get('model_versions', {}),
            confidence_score=data.get('confidence_score', 0.0),
            analysis_timestamp=datetime.fromisoformat(data.get('analysis_timestamp', datetime.now().isoformat())),
            recommended_actions=[SecurityAction.from_dict(action) for action in data.get('recommended_actions', [])],
            user_feedback_required=data.get('user_feedback_required', False)
        )

    def validate(self) -> bool:
        """Validate analysis result."""
        return (
            0.0 <= self.risk_score <= 1.0 and
            isinstance(self.risk_level, RiskLevel) and
            self.nlp_features.validate() and
            self.embedding_analysis.validate() and
            self.behavioral_analysis.validate() and
            self.threat_analysis.validate() and
            self.processing_time >= 0.0 and
            0.0 <= self.confidence_score <= 1.0 and
            isinstance(self.analysis_timestamp, datetime) and
            all(action.validate() for action in self.recommended_actions)
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
            0.0 <= self.low_risk_threshold <= 1.0 and
            0.0 <= self.medium_risk_threshold <= 1.0 and
            0.0 <= self.high_risk_threshold <= 1.0 and
            0.0 <= self.critical_risk_threshold <= 1.0 and
            self.low_risk_threshold <= self.medium_risk_threshold <= 
            self.high_risk_threshold <= self.critical_risk_threshold
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
            self.max_processing_timeout > 0.0 and
            0.0 <= self.fallback_risk_score <= 1.0
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
            'enable_nlp_analysis': self.enable_nlp_analysis,
            'enable_embedding_analysis': self.enable_embedding_analysis,
            'enable_behavioral_analysis': self.enable_behavioral_analysis,
            'enable_threat_intelligence': self.enable_threat_intelligence,
            'risk_thresholds': self.risk_thresholds.to_dict(),
            'max_processing_time': self.max_processing_time,
            'cache_size': self.cache_size,
            'cache_ttl': self.cache_ttl,
            'batch_size': self.batch_size,
            'fallback_config': self.fallback_config.to_dict(),
            'feature_flags': self.feature_flags.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> IntelligentAuthConfig:
        """Create instance from dictionary."""
        return cls(
            enable_nlp_analysis=data.get('enable_nlp_analysis', True),
            enable_embedding_analysis=data.get('enable_embedding_analysis', True),
            enable_behavioral_analysis=data.get('enable_behavioral_analysis', True),
            enable_threat_intelligence=data.get('enable_threat_intelligence', True),
            risk_thresholds=RiskThresholds.from_dict(data.get('risk_thresholds', {})),
            max_processing_time=data.get('max_processing_time', 5.0),
            cache_size=data.get('cache_size', 10000),
            cache_ttl=data.get('cache_ttl', 3600),
            batch_size=data.get('batch_size', 32),
            fallback_config=FallbackConfig.from_dict(data.get('fallback_config', {})),
            feature_flags=FeatureFlags.from_dict(data.get('feature_flags', {}))
        )

    @classmethod
    def from_env(cls) -> IntelligentAuthConfig:
        """Create configuration from environment variables."""
        import os
        
        return cls(
            enable_nlp_analysis=os.getenv('INTELLIGENT_AUTH_ENABLE_NLP', 'true').lower() == 'true',
            enable_embedding_analysis=os.getenv('INTELLIGENT_AUTH_ENABLE_EMBEDDING', 'true').lower() == 'true',
            enable_behavioral_analysis=os.getenv('INTELLIGENT_AUTH_ENABLE_BEHAVIORAL', 'true').lower() == 'true',
            enable_threat_intelligence=os.getenv('INTELLIGENT_AUTH_ENABLE_THREAT_INTEL', 'true').lower() == 'true',
            max_processing_time=float(os.getenv('INTELLIGENT_AUTH_MAX_PROCESSING_TIME', '5.0')),
            cache_size=int(os.getenv('INTELLIGENT_AUTH_CACHE_SIZE', '10000')),
            cache_ttl=int(os.getenv('INTELLIGENT_AUTH_CACHE_TTL', '3600')),
            batch_size=int(os.getenv('INTELLIGENT_AUTH_BATCH_SIZE', '32'))
        )

    def validate(self) -> bool:
        """Validate configuration."""
        return (
            self.max_processing_time > 0.0 and
            self.cache_size > 0 and
            self.cache_ttl > 0 and
            self.batch_size > 0 and
            self.risk_thresholds.validate() and
            self.fallback_config.validate()
        )

    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save configuration to JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> IntelligentAuthConfig:
        """Load configuration from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)