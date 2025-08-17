"""In-browser code lab page stub for experimentation."""

from ui_logic.config.feature_flags import get_flag
from ui_logic.hooks.auth import get_current_user
from ui_logic.hooks.rbac import check_rbac

REQUIRED_ROLES = ["dev", "admin"]
FEATURE_FLAG = "show_experimental"


def render_page(user_ctx: dict | None = None) -> None:
    """Render the Code Lab page when experimental mode is enabled.

    Args:
        user_ctx: Optional user context dictionary.

    Raises:
        PermissionError: If RBAC checks fail.
        RuntimeError: If experimental features are disabled.
        NotImplementedError: Always raised as this page is a stub.
    """

    user = user_ctx or get_current_user()
    if not check_rbac(user, REQUIRED_ROLES):
        raise PermissionError("Code Lab access denied")
    if not get_flag(FEATURE_FLAG):
        raise RuntimeError("Code Lab feature disabled")
    raise NotImplementedError("Code Lab page not implemented")

