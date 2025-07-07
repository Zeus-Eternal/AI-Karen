"""Experimental labs UI stub gated by feature flags."""

from src.ui_logic.config.feature_flags import get_flag
from src.ui_logic.hooks.auth import get_current_user
from src.ui_logic.hooks.rbac import check_rbac

REQUIRED_ROLES = ["dev", "admin"]
FEATURE_FLAG = "show_experimental"


def render_page(user_ctx: dict | None = None) -> None:
    """Render the Labs page when experimental mode is enabled.

    Args:
        user_ctx: Optional user context.

    Raises:
        PermissionError: If RBAC check fails.
        RuntimeError: If the experimental flag is not enabled.
        NotImplementedError: Always raised as this is a placeholder.
    """

    user = user_ctx or get_current_user()
    if not check_rbac(user, REQUIRED_ROLES):
        raise PermissionError("Labs access denied")
    if not get_flag(FEATURE_FLAG):
        raise RuntimeError("Labs feature is disabled")
    raise NotImplementedError("Labs page not implemented")

