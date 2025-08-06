"""
Unified Authentication Exception Classes

This module provides a comprehensive set of exception classes for the consolidated
authentication system, ensuring consistent error handling across all authentication
operations and components.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List


class AuthError(Exception):
    """
    Base authentication error class.
    
    All authentication-related exceptions inherit from this class to provide
    consistent error handling and categorization.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        """
        Initialize authentication error.
        
        Args:
            message: Technical error message for logging
            error_code: Unique error code for programmatic handling
            details: Additional error details for debugging
            user_message: User-friendly error message (if different from technical message)
        """
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
            "details": self.details
        }
    
    def __str__(self) -> str:
        """String representation of the error."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


# Authentication Errors

class InvalidCredentialsError(AuthError):
    """Raised when user provides invalid credentials."""
    
    def __init__(
        self,
        message: str = "Invalid email or password",
        email: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="INVALID_CREDENTIALS",
            user_message="Invalid email or password",
            **kwargs
        )
        if email:
            self.details["email"] = email


class UserNotFoundError(AuthError):
    """Raised when user account is not found."""
    
    def __init__(
        self,
        message: str = "User account not found",
        email: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="USER_NOT_FOUND",
            user_message="User account not found",
            **kwargs
        )
        if email:
            self.details["email"] = email
        if user_id:
            self.details["user_id"] = user_id


class UserAlreadyExistsError(AuthError):
    """Raised when attempting to create a user that already exists."""
    
    def __init__(
        self,
        message: str = "User account already exists",
        email: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="USER_ALREADY_EXISTS",
            user_message="An account with this email already exists",
            **kwargs
        )
        if email:
            self.details["email"] = email


class AccountLockedError(AuthError):
    """Raised when user account is locked due to security reasons."""
    
    def __init__(
        self,
        message: str = "Account is temporarily locked",
        locked_until: Optional[str] = None,
        reason: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="ACCOUNT_LOCKED",
            user_message="Your account is temporarily locked due to security reasons",
            **kwargs
        )
        if locked_until:
            self.details["locked_until"] = locked_until
        if reason:
            self.details["reason"] = reason


class AccountDisabledError(AuthError):
    """Raised when user account is disabled."""
    
    def __init__(
        self,
        message: str = "User account is disabled",
        reason: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="ACCOUNT_DISABLED",
            user_message="Your account has been disabled",
            **kwargs
        )
        if reason:
            self.details["reason"] = reason


class EmailNotVerifiedError(AuthError):
    """Raised when user email is not verified."""
    
    def __init__(
        self,
        message: str = "Email address not verified",
        email: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="EMAIL_NOT_VERIFIED",
            user_message="Please verify your email address before logging in",
            **kwargs
        )
        if email:
            self.details["email"] = email


# Session Errors

class SessionError(AuthError):
    """Base class for session-related errors."""
    pass


class InvalidSessionError(SessionError):
    """Raised when session token is invalid."""
    
    def __init__(
        self,
        message: str = "Invalid session token",
        session_token: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="INVALID_SESSION",
            user_message="Your session is invalid. Please log in again",
            **kwargs
        )
        if session_token:
            # Don't include full token in details for security
            self.details["session_token_prefix"] = session_token[:8] + "..."


class SessionExpiredError(SessionError):
    """Raised when session has expired."""
    
    def __init__(
        self,
        message: str = "Session has expired",
        expired_at: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="SESSION_EXPIRED",
            user_message="Your session has expired. Please log in again",
            **kwargs
        )
        if expired_at:
            self.details["expired_at"] = expired_at


class SessionLimitExceededError(SessionError):
    """Raised when user exceeds maximum number of concurrent sessions."""
    
    def __init__(
        self,
        message: str = "Maximum number of sessions exceeded",
        max_sessions: Optional[int] = None,
        current_sessions: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="SESSION_LIMIT_EXCEEDED",
            user_message="You have too many active sessions. Please log out from other devices",
            **kwargs
        )
        if max_sessions:
            self.details["max_sessions"] = max_sessions
        if current_sessions:
            self.details["current_sessions"] = current_sessions


# Token Errors

class TokenError(AuthError):
    """Base class for token-related errors."""
    pass


class InvalidTokenError(TokenError):
    """Raised when JWT token is invalid."""
    
    def __init__(
        self,
        message: str = "Invalid token",
        token_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="INVALID_TOKEN",
            user_message="Invalid authentication token",
            **kwargs
        )
        if token_type:
            self.details["token_type"] = token_type


class TokenExpiredError(TokenError):
    """Raised when JWT token has expired."""
    
    def __init__(
        self,
        message: str = "Token has expired",
        token_type: Optional[str] = None,
        expired_at: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="TOKEN_EXPIRED",
            user_message="Authentication token has expired",
            **kwargs
        )
        if token_type:
            self.details["token_type"] = token_type
        if expired_at:
            self.details["expired_at"] = expired_at


class TokenMalformedError(TokenError):
    """Raised when JWT token is malformed."""
    
    def __init__(
        self,
        message: str = "Token is malformed",
        **kwargs
    ):
        super().__init__(
            message,
            error_code="TOKEN_MALFORMED",
            user_message="Invalid authentication token format",
            **kwargs
        )


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
        limit_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="RATE_LIMIT_EXCEEDED",
            user_message="Too many requests. Please try again later",
            **kwargs
        )
        if retry_after:
            self.details["retry_after"] = retry_after
        if limit_type:
            self.details["limit_type"] = limit_type


class SecurityBlockError(SecurityError):
    """Raised when request is blocked by security system."""
    
    def __init__(
        self,
        message: str = "Request blocked by security system",
        block_reason: Optional[str] = None,
        risk_score: Optional[float] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="SECURITY_BLOCK",
            user_message="Access denied for security reasons",
            **kwargs
        )
        if block_reason:
            self.details["block_reason"] = block_reason
        if risk_score:
            self.details["risk_score"] = risk_score


class SuspiciousActivityError(SecurityError):
    """Raised when suspicious activity is detected."""
    
    def __init__(
        self,
        message: str = "Suspicious activity detected",
        activity_type: Optional[str] = None,
        confidence: Optional[float] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="SUSPICIOUS_ACTIVITY",
            user_message="Unusual activity detected. Additional verification may be required",
            **kwargs
        )
        if activity_type:
            self.details["activity_type"] = activity_type
        if confidence:
            self.details["confidence"] = confidence


class GeolocationBlockError(SecurityError):
    """Raised when request is blocked due to geolocation restrictions."""
    
    def __init__(
        self,
        message: str = "Access blocked from this location",
        country: Optional[str] = None,
        region: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="GEOLOCATION_BLOCK",
            user_message="Access is not allowed from your current location",
            **kwargs
        )
        if country:
            self.details["country"] = country
        if region:
            self.details["region"] = region


class IPBlockedError(SecurityError):
    """Raised when request comes from a blocked IP address."""
    
    def __init__(
        self,
        message: str = "IP address is blocked",
        ip_address: Optional[str] = None,
        block_reason: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="IP_BLOCKED",
            user_message="Access denied from this IP address",
            **kwargs
        )
        if ip_address:
            self.details["ip_address"] = ip_address
        if block_reason:
            self.details["block_reason"] = block_reason


# Password Errors

class PasswordError(AuthError):
    """Base class for password-related errors."""
    pass


class WeakPasswordError(PasswordError):
    """Raised when password doesn't meet security requirements."""
    
    def __init__(
        self,
        message: str = "Password does not meet security requirements",
        requirements: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="WEAK_PASSWORD",
            user_message="Password does not meet security requirements",
            **kwargs
        )
        if requirements:
            self.details["requirements"] = requirements


class PasswordReuseError(PasswordError):
    """Raised when user tries to reuse a recent password."""
    
    def __init__(
        self,
        message: str = "Password has been used recently",
        **kwargs
    ):
        super().__init__(
            message,
            error_code="PASSWORD_REUSE",
            user_message="You cannot reuse a recent password",
            **kwargs
        )


class InvalidPasswordResetTokenError(PasswordError):
    """Raised when password reset token is invalid or expired."""
    
    def __init__(
        self,
        message: str = "Invalid or expired password reset token",
        **kwargs
    ):
        super().__init__(
            message,
            error_code="INVALID_RESET_TOKEN",
            user_message="Password reset link is invalid or has expired",
            **kwargs
        )


# Two-Factor Authentication Errors

class TwoFactorError(AuthError):
    """Base class for two-factor authentication errors."""
    pass


class TwoFactorRequiredError(TwoFactorError):
    """Raised when two-factor authentication is required."""
    
    def __init__(
        self,
        message: str = "Two-factor authentication required",
        methods: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="TWO_FACTOR_REQUIRED",
            user_message="Two-factor authentication is required",
            **kwargs
        )
        if methods:
            self.details["available_methods"] = methods


class InvalidTwoFactorCodeError(TwoFactorError):
    """Raised when two-factor authentication code is invalid."""
    
    def __init__(
        self,
        message: str = "Invalid two-factor authentication code",
        **kwargs
    ):
        super().__init__(
            message,
            error_code="INVALID_2FA_CODE",
            user_message="Invalid two-factor authentication code",
            **kwargs
        )


class TwoFactorSetupRequiredError(TwoFactorError):
    """Raised when two-factor authentication setup is required."""
    
    def __init__(
        self,
        message: str = "Two-factor authentication setup required",
        **kwargs
    ):
        super().__init__(
            message,
            error_code="2FA_SETUP_REQUIRED",
            user_message="Please set up two-factor authentication",
            **kwargs
        )


# Configuration Errors

class ConfigurationError(AuthError):
    """Raised when there's a configuration error."""
    
    def __init__(
        self,
        message: str = "Authentication service configuration error",
        config_key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="CONFIGURATION_ERROR",
            user_message="Service configuration error",
            **kwargs
        )
        if config_key:
            self.details["config_key"] = config_key


class DatabaseConnectionError(AuthError):
    """Raised when database connection fails."""
    
    def __init__(
        self,
        message: str = "Database connection failed",
        **kwargs
    ):
        super().__init__(
            message,
            error_code="DATABASE_CONNECTION_ERROR",
            user_message="Service temporarily unavailable",
            **kwargs
        )


class RedisConnectionError(AuthError):
    """Raised when Redis connection fails."""
    
    def __init__(
        self,
        message: str = "Redis connection failed",
        **kwargs
    ):
        super().__init__(
            message,
            error_code="REDIS_CONNECTION_ERROR",
            user_message="Service temporarily unavailable",
            **kwargs
        )


# Intelligence Layer Errors

class IntelligenceError(AuthError):
    """Base class for intelligence layer errors."""
    pass


class MLServiceUnavailableError(IntelligenceError):
    """Raised when ML service is unavailable."""
    
    def __init__(
        self,
        message: str = "Machine learning service unavailable",
        service_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="ML_SERVICE_UNAVAILABLE",
            user_message="Authentication service temporarily degraded",
            **kwargs
        )
        if service_name:
            self.details["service_name"] = service_name


class AnalysisTimeoutError(IntelligenceError):
    """Raised when analysis takes too long."""
    
    def __init__(
        self,
        message: str = "Authentication analysis timed out",
        timeout_seconds: Optional[float] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="ANALYSIS_TIMEOUT",
            user_message="Authentication is taking longer than expected",
            **kwargs
        )
        if timeout_seconds:
            self.details["timeout_seconds"] = timeout_seconds


class InsufficientDataError(IntelligenceError):
    """Raised when there's insufficient data for analysis."""
    
    def __init__(
        self,
        message: str = "Insufficient data for analysis",
        data_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="INSUFFICIENT_DATA",
            user_message="Unable to complete security analysis",
            **kwargs
        )
        if data_type:
            self.details["data_type"] = data_type


# Utility Functions

def get_user_friendly_message(error: Exception) -> str:
    """
    Get user-friendly error message from any exception.
    
    Args:
        error: Exception instance
        
    Returns:
        User-friendly error message
    """
    if isinstance(error, AuthError):
        return error.user_message
    
    # Default messages for common exception types
    error_messages = {
        "ConnectionError": "Service temporarily unavailable",
        "TimeoutError": "Request timed out. Please try again",
        "ValueError": "Invalid input provided",
        "KeyError": "Required information missing",
        "PermissionError": "Access denied"
    }
    
    error_type = type(error).__name__
    return error_messages.get(error_type, "An unexpected error occurred")


def categorize_error(error: Exception) -> str:
    """
    Categorize error for logging and monitoring purposes.
    
    Args:
        error: Exception instance
        
    Returns:
        Error category string
    """
    if isinstance(error, (InvalidCredentialsError, UserNotFoundError)):
        return "authentication"
    elif isinstance(error, (SessionError, TokenError)):
        return "session"
    elif isinstance(error, SecurityError):
        return "security"
    elif isinstance(error, PasswordError):
        return "password"
    elif isinstance(error, TwoFactorError):
        return "two_factor"
    elif isinstance(error, (ConfigurationError, DatabaseConnectionError, RedisConnectionError)):
        return "infrastructure"
    elif isinstance(error, IntelligenceError):
        return "intelligence"
    else:
        return "unknown"


def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is retryable.
    
    Args:
        error: Exception instance
        
    Returns:
        True if error is retryable, False otherwise
    """
    # Retryable errors are typically infrastructure-related
    retryable_errors = (
        DatabaseConnectionError,
        RedisConnectionError,
        MLServiceUnavailableError,
        AnalysisTimeoutError
    )
    
    return isinstance(error, retryable_errors)


def should_log_error(error: Exception) -> bool:
    """
    Determine if an error should be logged.
    
    Args:
        error: Exception instance
        
    Returns:
        True if error should be logged, False otherwise
    """
    # Don't log common user errors to avoid log spam
    user_errors = (
        InvalidCredentialsError,
        UserNotFoundError,
        SessionExpiredError,
        InvalidTokenError,
        WeakPasswordError
    )
    
    return not isinstance(error, user_errors)