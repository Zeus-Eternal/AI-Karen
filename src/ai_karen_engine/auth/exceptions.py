"""Authentication exception hierarchy for Kari AI."""


class AuthError(Exception):
    """Base class for authentication related errors."""


class UserNotFoundError(AuthError):
    """Raised when a requested user record does not exist."""


class UserAlreadyExistsError(AuthError):
    """Raised when attempting to create a user that already exists."""


class RateLimitExceededError(AuthError):
    """Raised when an authentication rate limit has been exceeded."""


class SecurityError(AuthError):
    """Raised when a security policy prevents the requested action."""


__all__ = [
    "AuthError",
    "UserNotFoundError",
    "UserAlreadyExistsError",
    "RateLimitExceededError",
    "SecurityError",
]
