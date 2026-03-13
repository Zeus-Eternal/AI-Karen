"""
Simplified authentication helpers exposed at the services package root.

This module re-exports the helpers from ``services.memory.internal.auth_utils`` so
legacy imports (e.g., ``from services import auth_utils``) continue to work.
"""

from services.memory.internal.auth_utils import (
    COOKIE_NAME,
    clear_auth_cookies,
    get_current_user,
    get_refresh_token,
    get_session_token,
    set_refresh_token_cookie,
    set_session_cookie,
    validate_cookie_security,
)

__all__ = [
    "COOKIE_NAME",
    "get_session_token",
    "get_refresh_token",
    "set_session_cookie",
    "set_refresh_token_cookie",
    "clear_auth_cookies",
    "validate_cookie_security",
    "get_current_user",
]
