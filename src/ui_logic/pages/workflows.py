"""Workflow builder and management page stub."""

from ui.config.feature_flags import get_flag
from ui.hooks.auth import get_current_user
from ui.hooks.rbac import check_rbac

REQUIRED_ROLES = ["admin"]
FEATURE_FLAG = "enable_workflows"


def render_page(user_ctx: dict | None = None) -> None:
    """Render the Workflows page if enabled.

    Args:
        user_ctx: Optional user context dictionary.

    Raises:
        PermissionError: If RBAC check fails.
        RuntimeError: If workflow features are disabled.
        NotImplementedError: Always raised as this is a placeholder.
    """

    user = user_ctx or get_current_user()
    if not check_rbac(user, REQUIRED_ROLES):
        raise PermissionError("Workflows page requires admin role")
    if not get_flag(FEATURE_FLAG):
        raise RuntimeError("Workflow feature disabled")
    raise NotImplementedError("Workflows page not implemented")

