"""
Kari Theme Switcher Logic (Framework-Agnostic)
- Logic for listing/setting themes
- Never renders UI (import in UI skin only)
"""

from ui.config.branding import get_available_themes, set_theme_for_user
from ui.hooks.rbac import require_roles

def fetch_available_themes(user_ctx):
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Not authorized to view themes.")
    return get_available_themes()

def set_user_theme(user_ctx, theme_name):
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Not authorized to change theme.")
    return set_theme_for_user(user_ctx, theme_name)
