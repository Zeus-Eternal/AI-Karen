"""System diagnostics and metrics page stub."""

from ui.config.feature_flags import get_flag
from ui.hooks.auth import get_current_user
from ui.hooks.rbac import check_rbac

REQUIRED_ROLES = ["admin"]
FEATURE_FLAG = "enable_admin_panel"


def render_page(user_ctx: dict | None = None) -> None:
    """Render the Diagnostics page if admin panel is enabled.

    Args:
        user_ctx: Optional user context dictionary.

    Raises:
        PermissionError: If RBAC fails.
        RuntimeError: If admin panel is disabled.
        NotImplementedError: Always raised since this is a placeholder.
    """

    user = user_ctx or get_current_user()
    if not check_rbac(user, REQUIRED_ROLES):
        raise PermissionError("Diagnostics page requires admin role")
    if not get_flag(FEATURE_FLAG):
        raise RuntimeError("Admin panel disabled")
    raise NotImplementedError("Diagnostics page not implemented")

