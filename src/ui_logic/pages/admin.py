"""
Kari Admin Page Logic (Backend/Core)
- Entry point for all admin panels (audit, diagnostics, RBAC, org)
- Orchestrates role checks and panel access
- 100% UI-agnostic: no frontend or Streamlit imports
"""

from typing import Dict, Any, Optional

from src.ui_logic.components.admin.audit_log import (
    get_audit_log,
    audit_log_summary,
    search_audit_logs,
    export_audit_logs,
    AuditLogAccessError,
)
from src.ui_logic.components.admin.diagnostics import (
    get_system_diagnostics,
    run_diagnostics_check,
)
from src.ui_logic.components.admin.rbac_panel import (
    get_user_roles,
    set_user_roles,
    get_role_policies,
    set_role_policies,
)
from src.ui_logic.components.admin.org_admin import (
    get_org_users,
    create_org_user,
    update_user,
    delete_org_user,
    get_org_settings,
    set_org_settings,
)
# If you have more, import them here!

def admin_page(user_ctx: Dict[str, Any], action: Optional[str] = None, **kwargs) -> Any:
    """
    Entry point for admin logic.
    Dispatches to the correct admin function based on `action`.
    RBAC: Only admin/org_admin/auditor/devops permitted.
    Args:
        user_ctx: User context dict.
        action: Operation name ('audit_log', 'diagnostics', 'rbac', 'org', etc.).
        kwargs: Additional args for the action.
    Returns:
        Response from the requested admin action.
    Raises:
        PermissionError, AuditLogAccessError, etc.
    """
    if not user_ctx or "roles" not in user_ctx:
        raise PermissionError("Missing user context or roles for admin panel.")

    allowed_roles = {"admin", "org_admin", "auditor", "devops"}
    user_roles = set(user_ctx.get("roles", []))
    if not user_roles.intersection(allowed_roles):
        raise PermissionError("User does not have admin privileges.")

    # --- Dispatch map (easy to extend) ---
    dispatch = {
        "audit_log": lambda: get_audit_log(user_ctx, **kwargs),
        "audit_summary": lambda: audit_log_summary(get_audit_log(user_ctx, **kwargs)),
        "audit_search": lambda: search_audit_logs(user_ctx, kwargs.get("query", ""), kwargs.get("limit", 100)),
        "audit_export": lambda: export_audit_logs(
            kwargs.get("logs") or get_audit_log(user_ctx, limit=kwargs.get("limit", 100)),
            format=kwargs.get("format", "json")
        ),
        "diagnostics": lambda: get_system_diagnostics(),
        "diagnostics_check": lambda: run_diagnostics_check(**kwargs),
        "rbac_get_user_roles": lambda: get_user_roles(kwargs["user_id"]),
        "rbac_set_user_roles": lambda: set_user_roles(kwargs["user_id"], kwargs["roles"]),
        "rbac_get_role_policies": lambda: get_role_policies(kwargs["role"]),
        "rbac_set_role_policies": lambda: set_role_policies(kwargs["role"], kwargs["policies"]),
        "org_get_users": lambda: get_org_users(kwargs["org_id"]),
        "org_create_user": lambda: create_org_user(kwargs["org_id"], kwargs["user_data"]),
        "org_update_user": lambda: update_user(kwargs["org_id"], kwargs["user_id"], kwargs["data"]),
        "org_delete_user": lambda: delete_org_user(kwargs["org_id"], kwargs["user_id"]),
        "org_get_settings": lambda: get_org_settings(kwargs["org_id"]),
        "org_set_settings": lambda: set_org_settings(kwargs["org_id"], kwargs["data"]),
        # Add more here as needed!
    }

    if not action:
        raise ValueError("Action must be specified for admin_page()")

    if action not in dispatch:
        raise ValueError(f"Unknown admin action: {action}")

    return dispatch[action]()

__all__ = ["admin_page"]
