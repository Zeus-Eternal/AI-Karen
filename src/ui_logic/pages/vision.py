"""Computer vision and OCR page stub."""

from src.ui_logic.config.feature_flags import get_flag
from src.ui_logic.hooks.auth import get_current_user
from src.ui_logic.hooks.rbac import check_rbac

REQUIRED_ROLES = ["user", "admin"]
FEATURE_FLAG = "enable_multimodal"


def render_page(user_ctx: dict | None = None) -> None:
    """Render the Vision page for image analysis.

    Args:
        user_ctx: Optional user context.

    Raises:
        PermissionError: If RBAC check fails.
        RuntimeError: If vision features are disabled.
        NotImplementedError: Always raised as this module is a stub.
    """

    user = user_ctx or get_current_user()
    if not check_rbac(user, REQUIRED_ROLES):
        raise PermissionError("Vision page access denied")
    if not get_flag(FEATURE_FLAG):
        raise RuntimeError("Vision features disabled")
    raise NotImplementedError("Vision page not implemented")

