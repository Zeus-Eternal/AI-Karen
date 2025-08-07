"""Compatibility shims for legacy authentication APIs.

This module provides thin wrappers that map deprecated helper
functions from earlier versions of the codebase to the new
:class:`~ai_karen_engine.security.auth_service.AuthService` factory.
Each shim emits a :class:`DeprecationWarning` when used to help callers
migrate to the modern API ``auth_service()``.
"""

from __future__ import annotations

import warnings

from ai_karen_engine.security.auth_service import AuthService, auth_service


def _deprecated_alias(name: str) -> AuthService:
    """Return the shared :class:`AuthService` instance with a warning.

    Parameters
    ----------
    name:
        The name of the deprecated accessor that was used.  It is
        interpolated into the warning message so users know which symbol
        to replace.
    """

    warnings.warn(
        f"'{name}' is deprecated. Use 'auth_service()' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return auth_service()


def get_production_auth_service() -> AuthService:
    """Deprecated accessor for production environments.

    Historically the project offered separate helpers for different
    environments.  The new unified :func:`auth_service` replaces all of
    them, but this function remains as a thin shim for older imports.
    """

    return _deprecated_alias("get_production_auth_service")


def get_demo_auth_service() -> AuthService:
    """Deprecated accessor for demo environments.

    Returns the same shared service instance as
    :func:`get_production_auth_service` and exists solely for backwards
    compatibility with older code.  A ``DeprecationWarning`` is emitted
    when invoked.
    """

    return _deprecated_alias("get_demo_auth_service")


def get_auth_service() -> AuthService:
    """Generic deprecated accessor.

    This mirrors :func:`auth_service` but is kept to ease the transition
    for any callers still importing the old name.
    """

    return _deprecated_alias("get_auth_service")


__all__ = [
    "get_production_auth_service",
    "get_demo_auth_service",
    "get_auth_service",
]
