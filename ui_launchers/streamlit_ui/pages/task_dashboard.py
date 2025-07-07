"""
Kari Task Dashboard – Enterprise Evil Twin Edition

- Centralized admin/user task dashboard for UI and API
- Supports role-based views: user (own), admin (all), plugin/system (external)
- Plug-in friendly: UI injection, observability hooks, and live metrics
- All actions audit-logged (forensics, compliance)
"""

import time
from typing import List, Dict, Any
from ui_logic.hooks.rbac import require_roles
from ui_logic.utils.api import (
    fetch_audit_logs,
    fetch_user_profile,
    api_get,
    api_post,
)
# Add your actual task store/model import as needed, or use API

def get_user_tasks(user_ctx: Dict, include_history: bool = False) -> List[Dict[str, Any]]:
    """
    Return list of current (and optionally past) tasks for this user.
    RBAC: user can see own, admin can see all.
    """
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges for task access.")

    # You may fetch via DB, plugin, or API.
    # Here, we use API (update to use your real source).
    params = {"user_id": user_ctx.get("user_id")}
    if include_history:
        params["include_history"] = True

    # Admin can view all users if 'all_users' param is set
    if require_roles(user_ctx, ["admin"]) and user_ctx.get("view_all", False):
        params.pop("user_id", None)
        params["all_users"] = True

    try:
        tasks = api_get("tasks/list", params=params, token=user_ctx.get("token"), org=user_ctx.get("org_id"))
        return tasks if isinstance(tasks, list) else []
    except Exception:
        # Optionally: log this event
        return []

def submit_task_action(user_ctx: Dict, task_id: str, action: str) -> Dict[str, Any]:
    """
    Allow user/admin to act on a task (pause, cancel, retry, escalate).
    All actions audit-logged.
    """
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges for task actions.")
    payload = {
        "user_id": user_ctx.get("user_id"),
        "action": action,
        "timestamp": int(time.time()),
    }
    try:
        resp = api_post(f"tasks/{task_id}/action", data=payload, token=user_ctx.get("token"), org=user_ctx.get("org_id"))
        # Optionally: fetch_audit_logs(category="task", user_id=user_ctx.get("user_id"))
        return resp
    except Exception as ex:
        return {"error": str(ex)}

def render_task_dashboard(user_ctx: Dict, include_history: bool = False, show_admin: bool = False) -> Dict[str, Any]:
    """
    Render the dashboard payload for UI. Includes:
    - current tasks
    - audit logs (if admin)
    - profile snapshot
    - error (if any)
    """
    try:
        profile = fetch_user_profile(user_ctx.get("user_id"))
        tasks = get_user_tasks(user_ctx, include_history=include_history)
        audit = []
        if show_admin and require_roles(user_ctx, ["admin"]):
            audit = fetch_audit_logs(category="task", user_id=user_ctx.get("user_id"), limit=30)
        return {
            "profile": profile,
            "tasks": tasks,
            "audit": audit,
            "can_admin": require_roles(user_ctx, ["admin"]),
            "error": None,
        }
    except Exception as ex:
        return {
            "profile": None,
            "tasks": [],
            "audit": [],
            "can_admin": False,
            "error": str(ex),
        }

__all__ = [
    "get_user_tasks",
    "submit_task_action",
    "render_task_dashboard",
]
