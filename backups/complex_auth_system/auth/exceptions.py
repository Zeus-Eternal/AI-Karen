"""
Unified exception classes for the consolidated authentication service.

This module provides consistent error handling across all authentication
operations, replacing the fragmented exception handling in different
auth services.
"""

from typing import Any, Dict, List, Optional


class AuthError(Exception):
    """
    Base authentication error class.
    
    All authentication-related exceptions inherit from this base class
    to provide consistent error handling across the consolidated service.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.user_message = user_message or message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "user_message": self.user_message,
            "details": self.details,
        }
    
    def __str__(self) -> str:
        return f"{self.error_code}: {self.message}"


class AuthenticationError(AuthError):
    """Base class for authentication-related errors."""
    pass


class AuthorizationError(AuthError):
    """Base class for authorization-related errors."""
    pass


class ConfigurationError(AuthError):
    """Base class for configuration-related errors."""
    pass


class ValidationError(AuthError):
    """Base class for data validation errors."""
    pass


# Authentication Errors

class InvalidCredentialsError(AuthenticationError):
    """Raised when user credentials are invalid."""
    
    def __init__(
        self,
        message: str = "Invalid email or password",
        email: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Invalid email or password",
            **kwargs
        )
        if email:
            self.details["email"] = email


class UserNotFoundError(AuthenticationError):
    """Raised when a user is not found."""
    
    def __init__(
        self,
        message: str = "User not found",
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="User not found",
            **kwargs
        )
        if user_id:
            self.details["user_id"] = user_id
        if email:
            self.details["email"] = email


class UserAlreadyExistsError(AuthenticationError):
    """Raised when attempting to create a user that already exists."""
    
    def __init__(
        self,
        message: str = "User already exists",
        email: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="An account with this email already exists",
            **kwargs
        )
        if email:
            self.details["email"] = email


class AccountLockedError(AuthenticationError):
    """Raised when a user account is locked due to failed attempts."""
    
    def __init__(
        self,
        message: str = "Account is temporarily locked",
        locked_until: Optional[str] = None,
        failed_attempts: Optional[int] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Account is temporarily locked due to too many failed login attempts",
            **kwargs
        )
        if locked_until:
            self.details["locked_until"] = locked_until
        if failed_attempts is not None:
            self.details["failed_attempts"] = failed_attempts


class AccountDisabledError(AuthenticationError):
    """Raised when a user account is disabled."""
    
    def __init__(
        self,
        message: str = "Account is disabled",
        user_id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="This account has been disabled",
            **kwargs
        )
        if user_id:
            self.details["user_id"] = user_id


class EmailNotVerifiedError(AuthenticationError):
    """Raised when a user's email is not verified."""
    
    def __init__(
        self,
        message: str = "Email address not verified",
        email: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Please verify your email address before logging in",
            **kwargs
        )
        if email:
            self.details["email"] = email


class TwoFactorRequiredError(AuthenticationError):
    """Raised when two-factor authentication is required."""
    
    def __init__(
        self,
        message: str = "Two-factor authentication required",
        user_id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Two-factor authentication is required",
            **kwargs
        )
        if user_id:
            self.details["user_id"] = user_id


class InvalidTwoFactorCodeError(AuthenticationError):
    """Raised when an invalid two-factor authentication code is provided."""
    
    def __init__(
        self,
        message: str = "Invalid two-factor authentication code",
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Invalid two-factor authentication code",
            **kwargs
        )


# Session Errors

class SessionError(AuthError):
    """Base class for session-related errors."""
    pass


class SessionExpiredError(SessionError):
    """Raised when a session has expired."""
    
    def __init__(
        self,
        message: str = "Session has expired",
        session_token: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Your session has expired. Please log in again",
            **kwargs
        )
        if session_token:
            self.details["session_token"] = session_token


class SessionNotFoundError(SessionError):
    """Raised when a session is not found."""
    
    def __init__(
        self,
        message: str = "Session not found",
        session_token: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Invalid session. Please log in again",
            **kwargs
        )
        if session_token:
            self.details["session_token"] = session_token


class SessionInvalidatedError(SessionError):
    """Raised when a session has been invalidated."""
    
    def __init__(
        self,
        message: str = "Session has been invalidated",
        session_token: Optional[str] = None,
        reason: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Your session is no longer valid. Please log in again",
            **kwargs
        )
        if session_token:
            self.details["session_token"] = session_token
        if reason:
            self.details["reason"] = reason


class MaxSessionsExceededError(SessionError):
    """Raised when maximum number of sessions per user is exceeded."""
    
    def __init__(
        self,
        message: str = "Maximum number of sessions exceeded",
        user_id: Optional[str] = None,
        max_sessions: Optional[int] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Maximum number of active sessions exceeded",
            **kwargs
        )
        if user_id:
            self.details["user_id"] = user_id
        if max_sessions is not None:
            self.details["max_sessions"] = max_sessions


# Token Errors

class TokenError(AuthError):
    """Base class for token-related errors."""
    pass


class InvalidTokenError(TokenError):
    """Raised when a token is invalid."""
    
    def __init__(
        self,
        message: str = "Invalid token",
        token_type: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Invalid or malformed token",
            **kwargs
        )
        if token_type:
            self.details["token_type"] = token_type


class TokenExpiredError(TokenError):
    """Raised when a token has expired."""
    
    def __init__(
        self,
        message: str = "Token has expired",
        token_type: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Token has expired",
            **kwargs
        )
        if token_type:
            self.details["token_type"] = token_type


class TokenNotFoundError(TokenError):
    """Raised when a token is not found."""
    
    def __init__(
        self,
        message: str = "Token not found",
        token_type: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Token not found or already used",
            **kwargs
        )
        if token_type:
            self.details["token_type"] = token_type


# Security Errors

class SecurityError(AuthError):
    """Base class for security-related errors."""
    pass


class RateLimitExceededError(SecurityError):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Too many requests. Please try again later",
            **kwargs
        )
        if retry_after is not None:
            self.details["retry_after"] = retry_after
        if limit is not None:
            self.details["limit"] = limit


class SuspiciousActivityError(SecurityError):
    """Raised when suspicious activity is detected."""
    
    def __init__(
        self,
        message: str = "Suspicious activity detected",
        activity_type: Optional[str] = None,
        risk_score: Optional[float] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Suspicious activity detected. Please verify your identity",
            **kwargs
        )
        if activity_type:
            self.details["activity_type"] = activity_type
        if risk_score is not None:
            self.details["risk_score"] = risk_score


class IntelligentAuthBlockError(SecurityError):
    """Raised when intelligent authentication system blocks a request."""
    
    def __init__(
        self,
        message: str = "Request blocked by intelligent authentication",
        block_reason: Optional[str] = None,
        risk_score: Optional[float] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Authentication request blocked for security reasons",
            **kwargs
        )
        if block_reason:
            self.details["block_reason"] = block_reason
        if risk_score is not None:
            self.details["risk_score"] = risk_score


class AnomalyDetectedError(SecurityError):
    """Raised when an anomaly is detected in authentication patterns."""
    
    def __init__(
        self,
        message: str = "Authentication anomaly detected",
        anomaly_type: Optional[str] = None,
        anomaly_types: Optional[List[str]] = None,
        confidence: Optional[float] = None,
        risk_score: Optional[float] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Unusual authentication pattern detected",
            **kwargs
        )
        if anomaly_type:
            self.details["anomaly_type"] = anomaly_type
        if anomaly_types:
            self.details["anomaly_types"] = anomaly_types
        if confidence is not None:
            self.details["confidence"] = confidence
        if risk_score is not None:
            self.details["risk_score"] = risk_score


# Authorization Errors

class InsufficientPermissionsError(AuthorizationError):
    """Raised when user lacks required permissions."""
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permission: Optional[str] = None,
        user_roles: Optional[list] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="You don't have permission to perform this action",
            **kwargs
        )
        if required_permission:
            self.details["required_permission"] = required_permission
        if user_roles:
            self.details["user_roles"] = user_roles


class TenantAccessDeniedError(AuthorizationError):
    """Raised when user tries to access resources from different tenant."""
    
    def __init__(
        self,
        message: str = "Access denied to tenant resources",
        user_tenant: Optional[str] = None,
        requested_tenant: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Access denied to requested resources",
            **kwargs
        )
        if user_tenant:
            self.details["user_tenant"] = user_tenant
        if requested_tenant:
            self.details["requested_tenant"] = requested_tenant


# Validation Errors

class PasswordValidationError(ValidationError):
    """Raised when password doesn't meet requirements."""
    
    def __init__(
        self,
        message: str = "Password doesn't meet requirements",
        requirements: Optional[list] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Password doesn't meet security requirements",
            **kwargs
        )
        if requirements:
            self.details["requirements"] = requirements


class EmailValidationError(ValidationError):
    """Raised when email format is invalid."""
    
    def __init__(
        self,
        message: str = "Invalid email format",
        email: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Please enter a valid email address",
            **kwargs
        )
        if email:
            self.details["email"] = email


class UserDataValidationError(ValidationError):
    """Raised when user data validation fails."""
    
    def __init__(
        self,
        message: str = "User data validation failed",
        field: Optional[str] = None,
        value: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Invalid user data provided",
            **kwargs
        )
        if field:
            self.details["field"] = field
        if value:
            self.details["value"] = value


# Configuration Errors

class InvalidConfigurationError(ConfigurationError):
    """Raised when authentication configuration is invalid."""
    
    def __init__(
        self,
        message: str = "Invalid authentication configuration",
        config_field: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Authentication service configuration error",
            **kwargs
        )
        if config_field:
            self.details["config_field"] = config_field


class MissingConfigurationError(ConfigurationError):
    """Raised when required configuration is missing."""
    
    def __init__(
        self,
        message: str = "Required configuration missing",
        missing_field: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Authentication service configuration error",
            **kwargs
        )
        if missing_field:
            self.details["missing_field"] = missing_field


# Database Errors

class DatabaseError(AuthError):
    """Base class for database-related errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    
    def __init__(
        self,
        message: str = "Database connection failed",
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Service temporarily unavailable",
            **kwargs
        )


class DatabaseOperationError(DatabaseError):
    """Raised when database operation fails."""
    
    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Service temporarily unavailable",
            **kwargs
        )
        if operation:
            self.details["operation"] = operation


class MigrationError(DatabaseError):
    """Raised when database migration fails."""
    
    def __init__(
        self,
        message: str = "Database migration failed",
        migration_step: Optional[str] = None,
        source_database: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Database migration failed",
            **kwargs
        )
        if migration_step:
            self.details["migration_step"] = migration_step
        if source_database:
            self.details["source_database"] = source_database


# Service Errors

class ServiceError(AuthError):
    """Base class for service-related errors."""
    pass


class ServiceUnavailableError(ServiceError):
    """Raised when authentication service is unavailable."""
    
    def __init__(
        self,
        message: str = "Authentication service unavailable",
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Authentication service is temporarily unavailable",
            **kwargs
        )


class ExternalServiceError(ServiceError):
    """Raised when external service dependency fails."""
    
    def __init__(
        self,
        message: str = "External service error",
        service_name: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            message=message,
            user_message="Service temporarily unavailable",
            **kwargs
        )
        if service_name:
            self.details["service_name"] = service_name


# Utility functions for exception handling

def is_user_error(exception: Exception) -> bool:
    """Check if an exception represents a user error (4xx) vs system error (5xx)."""
    user_error_types = (
        InvalidCredentialsError,
        UserNotFoundError,
        UserAlreadyExistsError,
        AccountLockedError,
        AccountDisabledError,
        EmailNotVerifiedError,
        TwoFactorRequiredError,
        InvalidTwoFactorCodeError,
        SessionExpiredError,
        SessionNotFoundError,
        SessionInvalidatedError,
        MaxSessionsExceededError,
        InvalidTokenError,
        TokenExpiredError,
        TokenNotFoundError,
        RateLimitExceededError,
        InsufficientPermissionsError,
        TenantAccessDeniedError,
        PasswordValidationError,
        EmailValidationError,
        UserDataValidationError,
    )
    return isinstance(exception, user_error_types)


def get_http_status_code(exception: Exception) -> int:
    """Get appropriate HTTP status code for an authentication exception."""
    if isinstance(exception, (
        InvalidCredentialsError,
        UserNotFoundError,
        InvalidTokenError,
        TokenExpiredError,
        TokenNotFoundError,
        SessionExpiredError,
        SessionNotFoundError,
        SessionInvalidatedError,
    )):
        return 401  # Unauthorized
    
    elif isinstance(exception, (
        InsufficientPermissionsError,
        TenantAccessDeniedError,
        AccountDisabledError,
    )):
        return 403  # Forbidden
    
    elif isinstance(exception, (
        UserAlreadyExistsError,
        PasswordValidationError,
        EmailValidationError,
        UserDataValidationError,
        InvalidTwoFactorCodeError,
    )):
        return 400  # Bad Request
    
    elif isinstance(exception, (
        AccountLockedError,
        RateLimitExceededError,
        SuspiciousActivityError,
        IntelligentAuthBlockError,
        AnomalyDetectedError,
        MaxSessionsExceededError,
    )):
        return 429  # Too Many Requests
    
    elif isinstance(exception, (
        EmailNotVerifiedError,
        TwoFactorRequiredError,
    )):
        return 422  # Unprocessable Entity
    
    elif isinstance(exception, (
        DatabaseConnectionError,
        DatabaseOperationError,
        ServiceUnavailableError,
        ExternalServiceError,
    )):
        return 503  # Service Unavailable
    
    elif isinstance(exception, (
        InvalidConfigurationError,
        MissingConfigurationError,
    )):
        return 500  # Internal Server Error
    
    else:
        return 500  # Internal Server Error (default)