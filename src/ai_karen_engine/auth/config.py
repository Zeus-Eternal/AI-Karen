"""
Unified Authentication Configuration System

This module provides comprehensive configuration management for the consolidated
authentication service, supporting different authentication modes and deployment
scenarios through a single, well-structured configuration system.
"""

from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from .models import AuthMode, SessionStorageType


@dataclass
class DatabaseConfig:
    """Database configuration for authentication storage."""
    url: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False
    
    def __post_init__(self):
        """Set default database URL from environment if not provided."""
        if not self.url:
            self.url = os.environ.get(
                'POSTGRES_URL',
                'postgresql://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen'
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "url": self.url,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "echo": self.echo
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DatabaseConfig:
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class RedisConfig:
    """Redis configuration for session storage and caching."""
    url: str = ""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    
    def __post_init__(self):
        """Set default Redis URL from environment if not provided."""
        if not self.url:
            self.url = os.environ.get('REDIS_URL', f'redis://{self.host}:{self.port}/{self.db}')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "url": self.url,
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "password": self.password,
            "ssl": self.ssl,
            "max_connections": self.max_connections,
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.socket_connect_timeout
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RedisConfig:
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class TokenConfig:
    """JWT token configuration."""
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    password_reset_token_expire_hours: int = 1
    
    def __post_init__(self):
        """Set default secret key from environment if not provided."""
        if not self.secret_key:
            self.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
            if self.secret_key == 'your-secret-key-change-in-production':
                import warnings
                warnings.warn(
                    "Using default secret key! Set SECRET_KEY environment variable in production.",
                    UserWarning
                )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "secret_key": self.secret_key,
            "algorithm": self.algorithm,
            "access_token_expire_minutes": self.access_token_expire_minutes,
            "refresh_token_expire_days": self.refresh_token_expire_days,
            "password_reset_token_expire_hours": self.password_reset_token_expire_hours
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TokenConfig:
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class SessionConfig:
    """Session management configuration."""
    storage_type: SessionStorageType = SessionStorageType.DATABASE
    expire_hours: int = 24
    max_sessions_per_user: int = 5
    cleanup_interval_minutes: int = 60
    extend_on_activity: bool = True
    secure_cookies: bool = True
    same_site: str = "lax"  # "strict", "lax", or "none"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "storage_type": self.storage_type.value,
            "expire_hours": self.expire_hours,
            "max_sessions_per_user": self.max_sessions_per_user,
            "cleanup_interval_minutes": self.cleanup_interval_minutes,
            "extend_on_activity": self.extend_on_activity,
            "secure_cookies": self.secure_cookies,
            "same_site": self.same_site
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SessionConfig:
        """Create instance from dictionary."""
        storage_type = SessionStorageType(data.get("storage_type", "database"))
        return cls(
            storage_type=storage_type,
            expire_hours=data.get("expire_hours", 24),
            max_sessions_per_user=data.get("max_sessions_per_user", 5),
            cleanup_interval_minutes=data.get("cleanup_interval_minutes", 60),
            extend_on_activity=data.get("extend_on_activity", True),
            secure_cookies=data.get("secure_cookies", True),
            same_site=data.get("same_site", "lax")
        )


@dataclass
class SecurityConfig:
    """Security enhancement configuration."""
    enable_rate_limiting: bool = True
    enable_audit_logging: bool = True
    enable_session_validation: bool = True
    enable_ip_whitelist: bool = False
    enable_geolocation_blocking: bool = False
    
    # Rate limiting settings
    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 15
    rate_limit_window_minutes: int = 15
    
    # Password policy
    min_password_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    password_history_count: int = 5
    
    # Session security
    require_https: bool = True
    validate_user_agent: bool = True
    validate_ip_address: bool = False
    max_session_idle_minutes: int = 30
    
    # Allowed/blocked lists
    ip_whitelist: List[str] = field(default_factory=list)
    ip_blacklist: List[str] = field(default_factory=list)
    blocked_countries: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enable_rate_limiting": self.enable_rate_limiting,
            "enable_audit_logging": self.enable_audit_logging,
            "enable_session_validation": self.enable_session_validation,
            "enable_ip_whitelist": self.enable_ip_whitelist,
            "enable_geolocation_blocking": self.enable_geolocation_blocking,
            "max_failed_attempts": self.max_failed_attempts,
            "lockout_duration_minutes": self.lockout_duration_minutes,
            "rate_limit_window_minutes": self.rate_limit_window_minutes,
            "min_password_length": self.min_password_length,
            "require_uppercase": self.require_uppercase,
            "require_lowercase": self.require_lowercase,
            "require_numbers": self.require_numbers,
            "require_special_chars": self.require_special_chars,
            "password_history_count": self.password_history_count,
            "require_https": self.require_https,
            "validate_user_agent": self.validate_user_agent,
            "validate_ip_address": self.validate_ip_address,
            "max_session_idle_minutes": self.max_session_idle_minutes,
            "ip_whitelist": self.ip_whitelist,
            "ip_blacklist": self.ip_blacklist,
            "blocked_countries": self.blocked_countries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SecurityConfig:
        """Create instance from dictionary."""
        return cls(
            enable_rate_limiting=data.get("enable_rate_limiting", True),
            enable_audit_logging=data.get("enable_audit_logging", True),
            enable_session_validation=data.get("enable_session_validation", True),
            enable_ip_whitelist=data.get("enable_ip_whitelist", False),
            enable_geolocation_blocking=data.get("enable_geolocation_blocking", False),
            max_failed_attempts=data.get("max_failed_attempts", 5),
            lockout_duration_minutes=data.get("lockout_duration_minutes", 15),
            rate_limit_window_minutes=data.get("rate_limit_window_minutes", 15),
            min_password_length=data.get("min_password_length", 8),
            require_uppercase=data.get("require_uppercase", True),
            require_lowercase=data.get("require_lowercase", True),
            require_numbers=data.get("require_numbers", True),
            require_special_chars=data.get("require_special_chars", True),
            password_history_count=data.get("password_history_count", 5),
            require_https=data.get("require_https", True),
            validate_user_agent=data.get("validate_user_agent", True),
            validate_ip_address=data.get("validate_ip_address", False),
            max_session_idle_minutes=data.get("max_session_idle_minutes", 30),
            ip_whitelist=data.get("ip_whitelist", []),
            ip_blacklist=data.get("ip_blacklist", []),
            blocked_countries=data.get("blocked_countries", [])
        )


@dataclass
class IntelligenceConfig:
    """Intelligence layer configuration for ML-based authentication."""
    enable_behavioral_analysis: bool = False
    enable_anomaly_detection: bool = False
    enable_risk_scoring: bool = False
    enable_threat_intelligence: bool = False
    
    # Risk thresholds
    low_risk_threshold: float = 0.3
    medium_risk_threshold: float = 0.6
    high_risk_threshold: float = 0.8
    critical_risk_threshold: float = 0.95
    
    # Processing limits
    max_processing_time_seconds: float = 5.0
    enable_async_processing: bool = True
    fallback_on_timeout: bool = True
    fallback_risk_score: float = 0.0
    
    # ML model settings
    model_cache_size: int = 1000
    model_cache_ttl_minutes: int = 60
    batch_processing_size: int = 32
    
    # Feature flags
    enable_geolocation_analysis: bool = True
    enable_device_fingerprinting: bool = True
    enable_user_profiling: bool = True
    enable_attack_pattern_detection: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enable_behavioral_analysis": self.enable_behavioral_analysis,
            "enable_anomaly_detection": self.enable_anomaly_detection,
            "enable_risk_scoring": self.enable_risk_scoring,
            "enable_threat_intelligence": self.enable_threat_intelligence,
            "low_risk_threshold": self.low_risk_threshold,
            "medium_risk_threshold": self.medium_risk_threshold,
            "high_risk_threshold": self.high_risk_threshold,
            "critical_risk_threshold": self.critical_risk_threshold,
            "max_processing_time_seconds": self.max_processing_time_seconds,
            "enable_async_processing": self.enable_async_processing,
            "fallback_on_timeout": self.fallback_on_timeout,
            "fallback_risk_score": self.fallback_risk_score,
            "model_cache_size": self.model_cache_size,
            "model_cache_ttl_minutes": self.model_cache_ttl_minutes,
            "batch_processing_size": self.batch_processing_size,
            "enable_geolocation_analysis": self.enable_geolocation_analysis,
            "enable_device_fingerprinting": self.enable_device_fingerprinting,
            "enable_user_profiling": self.enable_user_profiling,
            "enable_attack_pattern_detection": self.enable_attack_pattern_detection
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> IntelligenceConfig:
        """Create instance from dictionary."""
        return cls(
            enable_behavioral_analysis=data.get("enable_behavioral_analysis", False),
            enable_anomaly_detection=data.get("enable_anomaly_detection", False),
            enable_risk_scoring=data.get("enable_risk_scoring", False),
            enable_threat_intelligence=data.get("enable_threat_intelligence", False),
            low_risk_threshold=data.get("low_risk_threshold", 0.3),
            medium_risk_threshold=data.get("medium_risk_threshold", 0.6),
            high_risk_threshold=data.get("high_risk_threshold", 0.8),
            critical_risk_threshold=data.get("critical_risk_threshold", 0.95),
            max_processing_time_seconds=data.get("max_processing_time_seconds", 5.0),
            enable_async_processing=data.get("enable_async_processing", True),
            fallback_on_timeout=data.get("fallback_on_timeout", True),
            fallback_risk_score=data.get("fallback_risk_score", 0.0),
            model_cache_size=data.get("model_cache_size", 1000),
            model_cache_ttl_minutes=data.get("model_cache_ttl_minutes", 60),
            batch_processing_size=data.get("batch_processing_size", 32),
            enable_geolocation_analysis=data.get("enable_geolocation_analysis", True),
            enable_device_fingerprinting=data.get("enable_device_fingerprinting", True),
            enable_user_profiling=data.get("enable_user_profiling", True),
            enable_attack_pattern_detection=data.get("enable_attack_pattern_detection", True)
        )


@dataclass
class LoggingConfig:
    """Logging and monitoring configuration."""
    enable_structured_logging: bool = True
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "text"
    
    # Event logging
    log_successful_logins: bool = True
    log_failed_logins: bool = True
    log_session_events: bool = True
    log_security_events: bool = True
    log_admin_actions: bool = True
    
    # Performance logging
    log_slow_operations: bool = True
    slow_operation_threshold_ms: float = 1000.0
    
    # Sensitive data handling
    mask_passwords: bool = True
    mask_tokens: bool = True
    mask_personal_info: bool = True
    
    # Log retention
    max_log_age_days: int = 90
    max_log_size_mb: int = 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enable_structured_logging": self.enable_structured_logging,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "log_successful_logins": self.log_successful_logins,
            "log_failed_logins": self.log_failed_logins,
            "log_session_events": self.log_session_events,
            "log_security_events": self.log_security_events,
            "log_admin_actions": self.log_admin_actions,
            "log_slow_operations": self.log_slow_operations,
            "slow_operation_threshold_ms": self.slow_operation_threshold_ms,
            "mask_passwords": self.mask_passwords,
            "mask_tokens": self.mask_tokens,
            "mask_personal_info": self.mask_personal_info,
            "max_log_age_days": self.max_log_age_days,
            "max_log_size_mb": self.max_log_size_mb
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LoggingConfig:
        """Create instance from dictionary."""
        return cls(
            enable_structured_logging=data.get("enable_structured_logging", True),
            log_level=data.get("log_level", "INFO"),
            log_format=data.get("log_format", "json"),
            log_successful_logins=data.get("log_successful_logins", True),
            log_failed_logins=data.get("log_failed_logins", True),
            log_session_events=data.get("log_session_events", True),
            log_security_events=data.get("log_security_events", True),
            log_admin_actions=data.get("log_admin_actions", True),
            log_slow_operations=data.get("log_slow_operations", True),
            slow_operation_threshold_ms=data.get("slow_operation_threshold_ms", 1000.0),
            mask_passwords=data.get("mask_passwords", True),
            mask_tokens=data.get("mask_tokens", True),
            mask_personal_info=data.get("mask_personal_info", True),
            max_log_age_days=data.get("max_log_age_days", 90),
            max_log_size_mb=data.get("max_log_size_mb", 100)
        )


@dataclass
class AuthConfig:
    """
    Comprehensive authentication configuration for the unified auth service.
    
    This configuration system supports different authentication modes and
    deployment scenarios through a single, well-structured configuration.
    """
    # Core settings
    auth_mode: AuthMode = AuthMode.ENHANCED
    service_name: str = "unified-auth-service"
    service_version: str = "1.0.0"
    debug: bool = False
    
    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    tokens: TokenConfig = field(default_factory=TokenConfig)
    sessions: SessionConfig = field(default_factory=SessionConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    intelligence: IntelligenceConfig = field(default_factory=IntelligenceConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Feature flags based on auth mode
    enable_security_features: bool = True
    enable_intelligent_auth: bool = False
    enable_production_features: bool = False
    
    def __post_init__(self):
        """Configure features based on auth mode."""
        if self.auth_mode == AuthMode.BASIC:
            self.enable_security_features = False
            self.enable_intelligent_auth = False
            self.enable_production_features = False
        elif self.auth_mode == AuthMode.ENHANCED:
            self.enable_security_features = True
            self.enable_intelligent_auth = False
            self.enable_production_features = False
        elif self.auth_mode == AuthMode.INTELLIGENT:
            self.enable_security_features = True
            self.enable_intelligent_auth = True
            self.enable_production_features = False
        elif self.auth_mode == AuthMode.PRODUCTION:
            self.enable_security_features = True
            self.enable_intelligent_auth = True
            self.enable_production_features = True
            
            # Enable production-specific settings
            self.security.require_https = True
            self.sessions.secure_cookies = True
            self.logging.log_level = "WARNING"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "auth_mode": self.auth_mode.value,
            "service_name": self.service_name,
            "service_version": self.service_version,
            "debug": self.debug,
            "database": self.database.to_dict(),
            "redis": self.redis.to_dict(),
            "tokens": self.tokens.to_dict(),
            "sessions": self.sessions.to_dict(),
            "security": self.security.to_dict(),
            "intelligence": self.intelligence.to_dict(),
            "logging": self.logging.to_dict(),
            "enable_security_features": self.enable_security_features,
            "enable_intelligent_auth": self.enable_intelligent_auth,
            "enable_production_features": self.enable_production_features
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuthConfig:
        """Create instance from dictionary."""
        auth_mode = AuthMode(data.get("auth_mode", "enhanced"))
        
        return cls(
            auth_mode=auth_mode,
            service_name=data.get("service_name", "unified-auth-service"),
            service_version=data.get("service_version", "1.0.0"),
            debug=data.get("debug", False),
            database=DatabaseConfig.from_dict(data.get("database", {})),
            redis=RedisConfig.from_dict(data.get("redis", {})),
            tokens=TokenConfig.from_dict(data.get("tokens", {})),
            sessions=SessionConfig.from_dict(data.get("sessions", {})),
            security=SecurityConfig.from_dict(data.get("security", {})),
            intelligence=IntelligenceConfig.from_dict(data.get("intelligence", {})),
            logging=LoggingConfig.from_dict(data.get("logging", {})),
            enable_security_features=data.get("enable_security_features", True),
            enable_intelligent_auth=data.get("enable_intelligent_auth", False),
            enable_production_features=data.get("enable_production_features", False)
        )
    
    @classmethod
    def from_env(cls) -> AuthConfig:
        """Create configuration from environment variables."""
        auth_mode_str = os.environ.get('AUTH_MODE', 'enhanced').lower()
        auth_mode = AuthMode.ENHANCED
        
        if auth_mode_str == 'basic':
            auth_mode = AuthMode.BASIC
        elif auth_mode_str == 'intelligent':
            auth_mode = AuthMode.INTELLIGENT
        elif auth_mode_str == 'production':
            auth_mode = AuthMode.PRODUCTION
        
        config = cls(
            auth_mode=auth_mode,
            service_name=os.environ.get('AUTH_SERVICE_NAME', 'unified-auth-service'),
            service_version=os.environ.get('AUTH_SERVICE_VERSION', '1.0.0'),
            debug=os.environ.get('AUTH_DEBUG', 'false').lower() == 'true'
        )
        
        # Override specific settings from environment
        if 'AUTH_ENABLE_SECURITY' in os.environ:
            config.enable_security_features = os.environ['AUTH_ENABLE_SECURITY'].lower() == 'true'
        
        if 'AUTH_ENABLE_INTELLIGENCE' in os.environ:
            config.enable_intelligent_auth = os.environ['AUTH_ENABLE_INTELLIGENCE'].lower() == 'true'
        
        if 'AUTH_ENABLE_PRODUCTION' in os.environ:
            config.enable_production_features = os.environ['AUTH_ENABLE_PRODUCTION'].lower() == 'true'
        
        return config
    
    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> AuthConfig:
        """Load configuration from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save configuration to JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Validate database URL
        if not self.database.url:
            errors.append("Database URL is required")
        
        # Validate secret key
        if not self.tokens.secret_key or self.tokens.secret_key == 'your-secret-key-change-in-production':
            if self.auth_mode in [AuthMode.PRODUCTION, AuthMode.INTELLIGENT]:
                errors.append("Secure secret key is required for production/intelligent mode")
        
        # Validate Redis configuration if using Redis session storage
        if self.sessions.storage_type == SessionStorageType.REDIS:
            if not self.redis.url and not self.redis.host:
                errors.append("Redis configuration is required when using Redis session storage")
        
        # Validate risk thresholds
        thresholds = [
            self.intelligence.low_risk_threshold,
            self.intelligence.medium_risk_threshold,
            self.intelligence.high_risk_threshold,
            self.intelligence.critical_risk_threshold
        ]
        
        if not all(0.0 <= t <= 1.0 for t in thresholds):
            errors.append("Risk thresholds must be between 0.0 and 1.0")
        
        if not all(thresholds[i] <= thresholds[i+1] for i in range(len(thresholds)-1)):
            errors.append("Risk thresholds must be in ascending order")
        
        # Validate token expiration times
        if self.tokens.access_token_expire_minutes <= 0:
            errors.append("Access token expiration must be positive")
        
        if self.tokens.refresh_token_expire_days <= 0:
            errors.append("Refresh token expiration must be positive")
        
        # Validate session configuration
        if self.sessions.expire_hours <= 0:
            errors.append("Session expiration must be positive")
        
        if self.sessions.max_sessions_per_user <= 0:
            errors.append("Max sessions per user must be positive")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0
    
    def get_mode_description(self) -> str:
        """Get description of current authentication mode."""
        descriptions = {
            AuthMode.BASIC: "Basic username/password authentication",
            AuthMode.ENHANCED: "Enhanced authentication with security features",
            AuthMode.INTELLIGENT: "Intelligent authentication with ML-based analysis",
            AuthMode.PRODUCTION: "Full production authentication with all features"
        }
        return descriptions.get(self.auth_mode, "Unknown mode")


# Predefined configurations for common scenarios

def get_development_config() -> AuthConfig:
    """Get configuration optimized for development."""
    config = AuthConfig(
        auth_mode=AuthMode.ENHANCED,
        debug=True
    )
    config.security.require_https = False
    config.sessions.secure_cookies = False
    config.logging.log_level = "DEBUG"
    return config


def get_testing_config() -> AuthConfig:
    """Get configuration optimized for testing."""
    config = AuthConfig(
        auth_mode=AuthMode.BASIC,
        debug=True
    )
    config.database.url = "sqlite:///test_auth.db"
    config.sessions.storage_type = SessionStorageType.MEMORY
    config.security.enable_rate_limiting = False
    config.logging.log_level = "WARNING"
    return config


def get_production_config() -> AuthConfig:
    """Get configuration optimized for production."""
    config = AuthConfig(
        auth_mode=AuthMode.PRODUCTION,
        debug=False
    )
    config.security.require_https = True
    config.sessions.secure_cookies = True
    config.sessions.storage_type = SessionStorageType.REDIS
    config.logging.log_level = "WARNING"
    config.intelligence.enable_behavioral_analysis = True
    config.intelligence.enable_anomaly_detection = True
    config.intelligence.enable_risk_scoring = True
    return config