"""
Unified authentication system for AI Karen.

This package provides a consolidated authentication service that replaces
the fragmented authentication services throughout the codebase with a
single, well-designed system.

Key Components:
- models: Unified data models (UserData, SessionData, AuthEvent)
- config: Comprehensive configuration system (AuthConfig)
- exceptions: Unified exception hierarchy for error handling

Usage:
    from ai_karen_engine.auth import AuthConfig, UserData, SessionData
    from ai_karen_engine.auth.exceptions import InvalidCredentialsError

    config = AuthConfig.from_env()
    # Use the unified models and configuration
"""

from ai_karen_engine.auth.config import (
    AuthConfig,
    DatabaseConfig,
    FeatureToggles,
    IntelligenceConfig,
    JWTConfig,
    SecurityConfig,
    SessionConfig,
)
from ai_karen_engine.auth.exceptions import (  # Base exceptions; Authentication errors; Session errors; Token errors; Security errors; Authorization errors; Validation errors; Configuration errors; Database errors; Service errors; Utility functions
    AccountDisabledError,
    AccountLockedError,
    AnomalyDetectedError,
    AuthenticationError,
    AuthError,
    AuthorizationError,
    ConfigurationError,
    DatabaseConnectionError,
    DatabaseError,
    DatabaseOperationError,
    EmailNotVerifiedError,
    EmailValidationError,
    ExternalServiceError,
    InsufficientPermissionsError,
    IntelligentAuthBlockError,
    InvalidConfigurationError,
    InvalidCredentialsError,
    InvalidTokenError,
    InvalidTwoFactorCodeError,
    MaxSessionsExceededError,
    MissingConfigurationError,
    PasswordValidationError,
    RateLimitExceededError,
    SecurityError,
    ServiceError,
    ServiceUnavailableError,
    SessionError,
    SessionExpiredError,
    SessionInvalidatedError,
    SessionNotFoundError,
    SuspiciousActivityError,
    TenantAccessDeniedError,
    TokenError,
    TokenExpiredError,
    TokenNotFoundError,
    TwoFactorRequiredError,
    UserAlreadyExistsError,
    UserDataValidationError,
    UserNotFoundError,
    ValidationError,
    get_http_status_code,
    is_user_error,
)
from ai_karen_engine.auth.intelligence import (
    AnomalyDetector,
    AnomalyResult,
    BehavioralAnalyzer,
    BehavioralPattern,
    IntelligenceEngine,
    IntelligenceResult,
    LoginAttempt,
    RiskScorer,
)
from ai_karen_engine.auth.models import AuthEvent, AuthEventType, SessionData, UserData
from ai_karen_engine.auth.monitoring import AuthMonitor, metrics_hook
from ai_karen_engine.auth.security import (
    AuditLogger,
    RateLimiter,
    SecurityEnhancer,
    SessionValidator,
)
from ai_karen_engine.auth.service import (
    AuthService,
    create_auth_service,
    get_auth_service,
    get_intelligent_auth_service,
    get_production_auth_service,
    get_unified_auth_service,
)

__version__ = "1.0.0"
__author__ = "AI Karen Team"
__description__ = "Unified authentication system for AI Karen"

__all__ = [
    # Configuration
    "AuthConfig",
    "DatabaseConfig",
    "JWTConfig",
    "SessionConfig",
    "SecurityConfig",
    "IntelligenceConfig",
    "FeatureToggles",
    # Models
    "UserData",
    "SessionData",
    "AuthEvent",
    "AuthEventType",
    # Security components
    "SecurityEnhancer",
    "RateLimiter",
    "AuditLogger",
    "SessionValidator",
    # Intelligence components
    "IntelligenceEngine",
    "AnomalyDetector",
    "BehavioralAnalyzer",
    "RiskScorer",
    "LoginAttempt",
    "BehavioralPattern",
    "AnomalyResult",
    "IntelligenceResult",
    # Main service interface
    "AuthService",
    "create_auth_service",
    "get_auth_service",
    "get_production_auth_service",
    "get_intelligent_auth_service",
    "get_unified_auth_service",
    # Monitoring
    "AuthMonitor",
    "metrics_hook",
    # Base exceptions
    "AuthError",
    "AuthenticationError",
    "AuthorizationError",
    "ConfigurationError",
    "ValidationError",
    # Authentication errors
    "InvalidCredentialsError",
    "UserNotFoundError",
    "UserAlreadyExistsError",
    "AccountLockedError",
    "AccountDisabledError",
    "EmailNotVerifiedError",
    "TwoFactorRequiredError",
    "InvalidTwoFactorCodeError",
    # Session errors
    "SessionError",
    "SessionExpiredError",
    "SessionNotFoundError",
    "SessionInvalidatedError",
    "MaxSessionsExceededError",
    # Token errors
    "TokenError",
    "InvalidTokenError",
    "TokenExpiredError",
    "TokenNotFoundError",
    # Security errors
    "SecurityError",
    "RateLimitExceededError",
    "SuspiciousActivityError",
    "IntelligentAuthBlockError",
    "AnomalyDetectedError",
    # Authorization errors
    "InsufficientPermissionsError",
    "TenantAccessDeniedError",
    # Validation errors
    "PasswordValidationError",
    "EmailValidationError",
    "UserDataValidationError",
    # Configuration errors
    "InvalidConfigurationError",
    "MissingConfigurationError",
    # Database errors
    "DatabaseError",
    "DatabaseConnectionError",
    "DatabaseOperationError",
    # Service errors
    "ServiceError",
    "ServiceUnavailableError",
    "ExternalServiceError",
    # Utility functions
    "is_user_error",
    "get_http_status_code",
]
