"""
Kari Privacy Console Logic (Framework-Agnostic)
- All privacy control logic (export, delete, anonymize)
- NO UI code—logic only
"""

from ui.hooks.rbac import require_roles
from ui.config.ui_config import get_privacy_data, anonymize_user_data, export_user_data, delete_user_data

def fetch_privacy_data(user_ctx):
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Not authorized to access privacy data.")
    return get_privacy_data(user_ctx)

def do_export_user_data(user_ctx):
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Not authorized for export.")
    return export_user_data(user_ctx)

def do_delete_user_data(user_ctx):
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Not authorized for deletion.")
    return delete_user_data(user_ctx)

def do_anonymize_user_data(user_ctx):
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Not authorized for anonymization.")
    return anonymize_user_data(user_ctx)
