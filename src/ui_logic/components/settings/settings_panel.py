"""
Kari Settings Panel Logic (Framework-Agnostic)
- All settings logic: retrieval, update, validation
- RBAC/feature flag checks (never renders UI directly)
- To be used by any UI skin (Streamlit, Gradio, CLI, etc)
"""

from ui_logic.hooks.rbac import require_roles
from ui_logic.config.ui_config import get_settings, update_settings, get_feature_flags

def fetch_settings(user_ctx):
    """Retrieve all settings for the given user context."""
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Not authorized to access settings panel.")
    return get_settings(user_ctx)

def save_settings(user_ctx, settings_dict):
    """Save/update user or system settings."""
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Not authorized to modify settings.")
    return update_settings(user_ctx, settings_dict)

def available_feature_flags(user_ctx):
    """Return enabled feature flags for the user context."""
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Not authorized for feature flags.")
    return get_feature_flags(user_ctx)
