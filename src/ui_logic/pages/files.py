"""File management and upload page stub."""

from ui.config.feature_flags import get_flag
from ui.hooks.auth import get_current_user
from ui.hooks.rbac import check_rbac

REQUIRED_ROLES = ["user", "admin"]
FEATURE_FLAG = "enable_multimodal"


def render_page(user_ctx: dict | None = None) -> None:
    """Render the Files page for multimodal uploads.

    Args:
        user_ctx: Optional user context dictionary.

    Raises:
        PermissionError: If the user lacks permissions.
        RuntimeError: If file uploads are disabled.
        NotImplementedError: Always raised because logic is not yet implemented.
    """

    user = user_ctx or get_current_user()
    if not check_rbac(user, REQUIRED_ROLES):
        raise PermissionError("File manager access denied")
    if not get_flag(FEATURE_FLAG):
        raise RuntimeError("Multimodal uploads disabled")
    raise NotImplementedError("Files page not implemented")

