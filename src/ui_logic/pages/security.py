"""Security settings and audit page stub."""

from ui.config.feature_flags import get_flag
from ui.hooks.auth import get_current_user
from ui.hooks.rbac import check_rbac

REQUIRED_ROLES = ["admin"]
FEATURE_FLAG = "enable_enterprise"


def render_page(user_ctx: dict | None = None) -> None:
    """Render the security page if user has access.

    Args:
        user_ctx: Optional user context dictionary.

    Raises:
        PermissionError: If RBAC enforcement fails.
        RuntimeError: If the enterprise feature is disabled.
        NotImplementedError: Always, as this is a stub.
    """

    user = user_ctx or get_current_user()
    if not check_rbac(user, REQUIRED_ROLES):
        raise PermissionError("Admin role required")
    if not get_flag(FEATURE_FLAG):
        raise RuntimeError("Enterprise security features disabled")
    raise NotImplementedError("Security page not implemented")

