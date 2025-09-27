"""Shared helpers for Kari Streamlit pages.

These utilities centralise feature-flag and RBAC checks so that the
individual page modules can focus on rendering rich UI experiences instead of
repeating the same boilerplate validation logic.  Keeping the access checks in
one place also makes it easier to harden the behaviour should the policy
change in the future (for example, introducing auditing hooks or telemetry
events).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Mapping, Optional, Sequence

from ui_logic.config.feature_flags import get_flag
from ui_logic.hooks.auth import get_current_user
from ui_logic.hooks.rbac import check_rbac


class FeatureDisabledError(RuntimeError):
    """Raised when a page is accessed while its feature flag is disabled."""


def _normalise_roles(required_roles: Optional[Sequence[str]]) -> Sequence[str]:
    if not required_roles:
        return ()
    # Guard against developers accidentally passing a set/tuple with mixed
    # casing.  Normalisation keeps comparisons consistent with the stored
    # values inside the user context.
    return tuple(sorted({role.strip() for role in required_roles if role}))


def require_page_access(
    user_ctx: Optional[Mapping[str, object]] = None,
    *,
    required_roles: Optional[Sequence[str]] = None,
    feature_flag: Optional[str] = None,
    feature_name: Optional[str] = None,
    rbac_message: Optional[str] = None,
):
    """Validate access for a UI page and return the resolved user context.

    Args:
        user_ctx: Optional user context override supplied by the caller.
        required_roles: Roles that must be present for the page to render.
        feature_flag: Optional feature flag that gates this page.
        feature_name: Human readable name for error messaging.
        rbac_message: Custom error message when RBAC validation fails.

    Returns:
        The resolved user context dictionary.  The object is intentionally
        mutable so Streamlit components can stash additional state if needed.

    Raises:
        PermissionError: When the caller lacks the required roles.
        FeatureDisabledError: When the configured feature flag is turned off.
    """

    user = dict(user_ctx or get_current_user())
    roles = _normalise_roles(required_roles)
    if roles and not check_rbac(user, list(roles)):
        raise PermissionError(rbac_message or "Access denied for this page")

    if feature_flag and not get_flag(feature_flag):
        flag_label = feature_name or feature_flag.replace("_", " ").title()
        raise FeatureDisabledError(f"{flag_label} is currently disabled")

    return user


def format_timedelta(value: float | int | timedelta | None) -> str:
    """Render a timestamp or duration in a human friendly way."""

    if value is None:
        return "—"
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
    elif isinstance(value, (float, int)):
        total_seconds = int(value)
    else:
        return str(value)

    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


def coerce_datetime(value: Optional[float | int | str | datetime]) -> Optional[datetime]:
    """Convert common timestamp representations into :class:`datetime`."""

    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (float, int)):
        return datetime.fromtimestamp(value)
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


__all__ = [
    "FeatureDisabledError",
    "require_page_access",
    "format_timedelta",
    "coerce_datetime",
]
