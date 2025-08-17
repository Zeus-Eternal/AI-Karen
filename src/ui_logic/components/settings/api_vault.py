"""
Kari API Vault Logic (Framework-Agnostic)
- Credential storage/retrieval
- RBAC logic only (no UI)
"""

from ui_logic.hooks.rbac import require_roles
from ui_logic.config.ui_config import get_api_keys, save_api_key, delete_api_key

def list_api_keys(user_ctx):
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Not authorized to access the API vault.")
    return get_api_keys(user_ctx)

def add_api_key(user_ctx, api_name, api_value):
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Not authorized to add API keys.")
    return save_api_key(user_ctx, api_name, api_value)

def remove_api_key(user_ctx, api_name):
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Not authorized to delete API keys.")
    return delete_api_key(user_ctx, api_name)
