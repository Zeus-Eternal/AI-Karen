"""Presence detection and activity UI stub."""

from ui_logic.config.feature_flags import get_flag
from ui_logic.hooks.auth import get_current_user
from ui_logic.hooks.rbac import check_rbac
from ai_karen_engine.event_bus import get_event_bus

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
        Returns: List of consumed events.
    """

    user = user_ctx or get_current_user()
    if not check_rbac(user, REQUIRED_ROLES):
        raise PermissionError("Presence page access denied")
    if not get_flag(FEATURE_FLAG):
        raise RuntimeError("Presence feature disabled")
    bus = get_event_bus()
    return [
        {
            "id": e.id,
            "capsule": e.capsule,
            "type": e.event_type,
            "payload": e.payload,
            "risk": e.risk,
        }
        for e in bus.consume(roles=user.get("roles"), tenant_id=user.get("tenant_id"))
    ]


if __name__ == "__main__":
    print(page({"roles": ["admin"]}))
