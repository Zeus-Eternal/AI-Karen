"""Task Manager UI page stub with RBAC and feature gating."""

from ui.config.feature_flags import get_flag
from ui.hooks.auth import get_current_user
from ui.hooks.rbac import check_rbac

REQUIRED_ROLES = ["user", "dev"]
FEATURE_FLAG = "enable_workflows"


def render_page(user_ctx: dict | None = None) -> None:
    """Render the Task Manager page if allowed.

    Args:
        user_ctx: Optional user context dictionary.

    Raises:
        PermissionError: If the current user lacks required roles.
        RuntimeError: If the feature flag is disabled.
        NotImplementedError: Always, this is a placeholder.
    """

    user = user_ctx or get_current_user()
    if not check_rbac(user, REQUIRED_ROLES):
        raise PermissionError("Access denied for Task Manager page")
    if not get_flag(FEATURE_FLAG):
        raise RuntimeError("Task Manager feature is disabled")
    raise NotImplementedError("Task Manager page not implemented")

