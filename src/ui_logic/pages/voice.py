"""Voice interface control page stub."""

from ui.config.feature_flags import get_flag
from ui.hooks.auth import get_current_user
from ui.hooks.rbac import check_rbac

REQUIRED_ROLES = ["user", "admin"]
FEATURE_FLAG = "enable_voice_io"


def render_page(user_ctx: dict | None = None) -> None:
    """Render the Voice settings page.

    Args:
        user_ctx: Optional user context dictionary.

    Raises:
        PermissionError: If required roles are missing.
        RuntimeError: If voice IO is disabled.
        NotImplementedError: Always raised as this module is a placeholder.
    """

    user = user_ctx or get_current_user()
    if not check_rbac(user, REQUIRED_ROLES):
        raise PermissionError("Voice page access denied")
    if not get_flag(FEATURE_FLAG):
        raise RuntimeError("Voice I/O disabled")
    raise NotImplementedError("Voice page not implemented")

