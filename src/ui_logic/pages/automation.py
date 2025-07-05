"""Automation dashboard stub with role and feature gating."""

from ui.config.feature_flags import get_flag
from ui.hooks.auth import get_current_user
from ui.hooks.rbac import check_rbac

REQUIRED_ROLES = ["user", "admin"]
FEATURE_FLAG = "enable_workflows"


def render_page(user_ctx: dict | None = None) -> None:
    """Render the automation page.

    Args:
        user_ctx: Optional user context dictionary.

    Raises:
        PermissionError: If RBAC checks fail.
        RuntimeError: If the feature is disabled.
        NotImplementedError: Always, placeholder stub.
    """

    user = user_ctx or get_current_user()
    if not check_rbac(user, REQUIRED_ROLES):
        raise PermissionError("Access denied for Automation page")
    if not get_flag(FEATURE_FLAG):
        raise RuntimeError("Automation feature disabled")
    raise NotImplementedError("Automation page not implemented")

