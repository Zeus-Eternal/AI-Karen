"""Persona library and editor stub."""

from ui.config.feature_flags import get_flag
from ui.hooks.auth import get_current_user
from ui.hooks.rbac import check_rbac

REQUIRED_ROLES = ["user", "admin"]
FEATURE_FLAG = "enable_premium"


def render_page(user_ctx: dict | None = None) -> None:
    """Render the Personas page if premium is enabled.

    Args:
        user_ctx: Optional user context dictionary.

    Raises:
        PermissionError: If user lacks required roles.
        RuntimeError: If premium features are disabled.
        NotImplementedError: Always, because logic is pending.
    """

    user = user_ctx or get_current_user()
    if not check_rbac(user, REQUIRED_ROLES):
        raise PermissionError("Personas page access denied")
    if not get_flag(FEATURE_FLAG):
        raise RuntimeError("Persona features disabled")
    raise NotImplementedError("Personas page not implemented")

