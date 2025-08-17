"""Avatar upload utility."""

from typing import Dict

from ui_logic.hooks.rbac import require_roles
from ui_logic.utils.api import save_file


def upload_avatar(user_ctx: Dict, file_bytes: bytes, filename: str) -> str:
    """Save user avatar and return file identifier."""
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Not authorized to upload avatar.")
    return save_file(user_ctx["user_id"], file_bytes, filename, "image/png", None)


__all__ = ["upload_avatar"]
