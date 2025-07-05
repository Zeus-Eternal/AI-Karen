"""Enterprise white‑label configuration UI stub."""

from ui.config.feature_flags import get_flag
from ui.hooks.auth import get_current_user
from ui.hooks.rbac import check_rbac

REQUIRED_ROLES = ["enterprise"]
FEATURE_FLAG = "show_branding_controls"


def render_page(user_ctx: dict | None = None) -> None:
    """Render the white‑label page for enterprise tenants.

    Args:
        user_ctx: Optional user context dictionary.

    Raises:
        PermissionError: If RBAC checks fail.
        RuntimeError: If the feature flag is disabled.
        NotImplementedError: Always, placeholder stub.
    """

    user = user_ctx or get_current_user()
    if not check_rbac(user, REQUIRED_ROLES):
        raise PermissionError("Enterprise role required")
    if not get_flag(FEATURE_FLAG):
        raise RuntimeError("Branding controls disabled")
    raise NotImplementedError("White‑label page not implemented")

