"""Third‑party integrations management stub."""

from src.ui_logic.config.feature_flags import get_flag
from src.ui_logic.hooks.auth import get_current_user
from src.ui_logic.hooks.rbac import check_rbac

REQUIRED_ROLES = ["admin", "dev"]
FEATURE_FLAG = "enable_plugins"


def render_page(user_ctx: dict | None = None) -> None:
    """Render the integrations page for plugin/LLM setup.

    Args:
        user_ctx: Optional user context dictionary.

    Raises:
        PermissionError: If RBAC enforcement fails.
        RuntimeError: If integrations are disabled.
        NotImplementedError: Always raised as this is a stub.
    """

    user = user_ctx or get_current_user()
    if not check_rbac(user, REQUIRED_ROLES):
        raise PermissionError("Insufficient privileges for integrations page")
    if not get_flag(FEATURE_FLAG):
        raise RuntimeError("Integrations feature disabled")
    raise NotImplementedError("Integrations page not implemented")

