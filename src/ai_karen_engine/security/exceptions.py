from __future__ import annotations

"""Custom exceptions for authentication and security modules."""


class AuthError(Exception):
    """Base class for authentication related errors."""


class AuthenticationError(AuthError):
    """Raised when authentication fails."""


class AuthorizationError(AuthError):
    """Raised when a user is not permitted to perform an action."""


class SessionError(AuthError):
    """Raised for problems related to session management."""


class TokenError(AuthError):
    """Raised for JWT and token related issues."""

