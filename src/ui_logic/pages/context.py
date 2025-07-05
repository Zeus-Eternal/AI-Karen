"""Session context explorer page stub."""

from ui.config.feature_flags import get_flag
from ui.hooks.auth import get_current_user
from ui.hooks.rbac import check_rbac

REQUIRED_ROLES = ["user", "admin"]
FEATURE_FLAG = "enable_memory_graph"


def render_page(user_ctx: dict | None = None) -> None:
    """Render the Context page if memory graph is enabled.

    Args:
        user_ctx: Optional user context.

    Raises:
        PermissionError: If roles are insufficient.
        RuntimeError: If the memory graph feature is disabled.
        NotImplementedError: Always raised as this is a placeholder.
    """

    user = user_ctx or get_current_user()
    if not check_rbac(user, REQUIRED_ROLES):
        raise PermissionError("Context page access denied")
    if not get_flag(FEATURE_FLAG):
        raise RuntimeError("Memory graph disabled")
    raise NotImplementedError("Context page not implemented")


if __name__ == "__main__":
    try:
        render_page({})
    except NotImplementedError:
        print("Context page stub")

