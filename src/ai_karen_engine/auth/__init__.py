"""
Unified Authentication System

This package provides a consolidated authentication system that replaces the
scattered authentication services throughout the codebase with a single,
well-designed service that handles all authentication scenarios cleanly.

The system is organized into layers:
- Core authentication layer (basic user auth, session management)
- Security enhancement layer (rate limiting, audit logging, session validation)
- Intelligence layer (behavioral analysis, anomaly detection, risk scoring)
- Storage layer (database operations, session storage, configuration management)

Key Components:
- models: Unified data models (UserData, SessionData, AuthEvent)
- config: Comprehensive configuration system (AuthConfig)
- exceptions: Unified exception classes for error handling
"""

from .models import (
    # Core data models
    UserData,
    SessionData,
    AuthEvent,
    
    # Enums
    AuthEventType,
    SessionStorageType,
    AuthMode,
    
    # Additional models
    PasswordResetToken,
    RateLimitInfo,
    SecurityResult,
    IntelligenceResult
)

from .config import (
    # Main configuration
    AuthConfig,
    
    # Component configurations
    DatabaseConfig,
    RedisConfig,
    TokenConfig,
    SessionConfig,
    SecurityConfig,
    IntelligenceConfig,
    LoggingConfig,
    
    # Predefined configurations
    get_development_config,
    get_testing_config,
    get_production_config
)

from .exceptions import (
    # Base exceptions
    AuthError,
    
    # Authentication errors
    InvalidCredentialsError,
    UserNotFoundError,
    UserAlreadyExistsError,
    AccountLockedError,
    AccountDisabledError,
    EmailNotVerifiedError,
    
    # Session errors
    SessionError,
    InvalidSessionError,
    SessionExpiredError,
    SessionLimitExceededError,
    
    # Token errors
    TokenError,
    InvalidTokenError,
    TokenExpiredError,
    TokenMalformedError,
    
    # Security errors
    SecurityError,
    RateLimitExceededError,
    SecurityBlockError,
    SuspiciousActivityError,
    GeolocationBlockError,
    IPBlockedError,
    
    # Password errors
    PasswordError,
    WeakPasswordError,
    PasswordReuseError,
    InvalidPasswordResetTokenError,
    
    # Two-factor authentication errors
    TwoFactorError,
    TwoFactorRequiredError,
    InvalidTwoFactorCodeError,
    TwoFactorSetupRequiredError,
    
    # Configuration errors
    ConfigurationError,
    DatabaseConnectionError,
    RedisConnectionError,
    
    # Intelligence layer errors
    IntelligenceError,
    MLServiceUnavailableError,
    AnalysisTimeoutError,
    InsufficientDataError,
    
    # Utility functions
    get_user_friendly_message,
    categorize_error,
    is_retryable_error,
    should_log_error
)

__version__ = "1.0.0"
__author__ = "AI Karen Engine Team"
__description__ = "Unified Authentication System for AI Karen Engine"

# Package metadata
__all__ = [
    # Models
    "UserData",
    "SessionData", 
    "AuthEvent",
    "AuthEventType",
    "SessionStorageType",
    "AuthMode",
    "PasswordResetToken",
    "RateLimitInfo",
    "SecurityResult",
    "IntelligenceResult",
    
    # Configuration
    "AuthConfig",
    "DatabaseConfig",
    "RedisConfig",
    "TokenConfig",
    "SessionConfig",
    "SecurityConfig",
    "IntelligenceConfig",
    "LoggingConfig",
    "get_development_config",
    "get_testing_config",
    "get_production_config",
    
    # Exceptions
    "AuthError",
    "InvalidCredentialsError",
    "UserNotFoundError",
    "UserAlreadyExistsError",
    "AccountLockedError",
    "AccountDisabledError",
    "EmailNotVerifiedError",
    "SessionError",
    "InvalidSessionError",
    "SessionExpiredError",
    "SessionLimitExceededError",
    "TokenError",
    "InvalidTokenError",
    "TokenExpiredError",
    "TokenMalformedError",
    "SecurityError",
    "RateLimitExceededError",
    "SecurityBlockError",
    "SuspiciousActivityError",
    "GeolocationBlockError",
    "IPBlockedError",
    "PasswordError",
    "WeakPasswordError",
    "PasswordReuseError",
    "InvalidPasswordResetTokenError",
    "TwoFactorError",
    "TwoFactorRequiredError",
    "InvalidTwoFactorCodeError",
    "TwoFactorSetupRequiredError",
    "ConfigurationError",
    "DatabaseConnectionError",
    "RedisConnectionError",
    "IntelligenceError",
    "MLServiceUnavailableError",
    "AnalysisTimeoutError",
    "InsufficientDataError",
    "get_user_friendly_message",
    "categorize_error",
    "is_retryable_error",
    "should_log_error"
]