"""Presence detection and activity UI stub."""

from src.ui_logic.config.feature_flags import get_flag
from src.ui_logic.hooks.auth import get_current_user
from src.ui_logic.hooks.rbac import check_rbac

REQUIRED_ROLES = ["admin", "user"]
FEATURE_FLAG = "enable_presence"


def page(user_ctx: dict, **kwargs) -> None:
    """Render the presence page if permitted.

    Args:
        user_ctx: The calling user context.
        **kwargs: Additional parameters (unused).

    Raises:
        PermissionError: If access is denied by RBAC.
        RuntimeError: If the presence feature is disabled.
        NotImplementedError: Always raised as this is a placeholder.
    """

    user = user_ctx or get_current_user()
    if not check_rbac(user, REQUIRED_ROLES):
        raise PermissionError("Presence page access denied")
    if not get_flag(FEATURE_FLAG):
        raise RuntimeError("Presence feature disabled")
    raise NotImplementedError("Coming soon!")


if __name__ == "__main__":
    try:
        page({})
    except NotImplementedError:
        print("Presence page stub")
