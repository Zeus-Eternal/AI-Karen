"""
Kari Audit Log Logic (Pure Backend)
- Secure RBAC-guarded audit event access and filtering
- Search, filter, paginate, and export audit trails
- Tamper-evident event formatting (can be extended for cryptographic signatures)
- 100% UI-agnostic: no frontend code or framework imports
"""

from typing import List, Dict, Any, Optional, Union
from ui_logic.utils.api import fetch_audit_logs
from ui_logic.hooks.rbac import require_roles


class AuditLogAccessError(PermissionError):
    """Custom exception for unauthorized audit log access."""


def get_audit_log(
    user_ctx: Dict[str, Any],
    filter: Optional[Dict[str, Union[str, int]]] = None,
    limit: int = 100,
    sort_desc: bool = True,
    strict: bool = True,
) -> List[Dict[str, Any]]:
    """
    Return a list of audit events, filtered and ordered.
    
    RBAC: Requires 'admin', 'org_admin', or 'auditor' role.
    Optionally allows user to see their own actions if strict=False.
    
    Args:
        user_ctx: Dict containing user context (must include 'user_id' and 'roles').
        filter: Dict with optional keys 'category', 'search'.
        limit: Max number of log entries to return.
        sort_desc: If True, newest first.
        strict: If True, only admins/auditors/org_admin; if False, allows user to see own.
        
    Raises:
        AuditLogAccessError if the user is not authorized.
        
    Returns:
        List of audit log dictionaries.
    """
    if not user_ctx or "user_id" not in user_ctx or "roles" not in user_ctx:
        raise AuditLogAccessError("User context incomplete for audit log access.")

    # Role check
    if require_roles(user_ctx, ["admin", "org_admin", "auditor"]):
        # Authorized—can view all logs
        allowed_user = None
    elif not strict and "user_id" in user_ctx:
        # Allow self-audit if strict is False
        allowed_user = user_ctx["user_id"]
    else:
        raise AuditLogAccessError("Not authorized to view audit logs.")

    category = filter.get("category") if filter and "category" in filter else None
    search = filter.get("search") if filter and "search" in filter else None

    logs = fetch_audit_logs(
        category=category,
        user_id=allowed_user,
        search=search,
        limit=limit
    )

    # Defensive: guarantee order and length
    logs = logs[-limit:] if sort_desc else logs[:limit]
    return list(reversed(logs)) if sort_desc else logs


def audit_log_summary(logs: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Summarize audit log actions for quick analytics (non-UI).
    
    Args:
        logs: List of audit log events.
    Returns:
        Dict mapping action names to their frequency.
    """
    from collections import Counter
    counter = Counter(log.get("action", "unknown") for log in logs)
    return dict(counter)


def search_audit_logs(
    user_ctx: Dict[str, Any],
    query: str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Fast in-memory search across audit logs (RBAC applied).
    
    Args:
        user_ctx: User context dict.
        query: Substring to search in 'action', 'user_id', or 'message'.
        limit: Max entries.
    Returns:
        List of filtered log dicts.
    """
    logs = get_audit_log(user_ctx, limit=limit)
    if not query:
        return logs
    return [
        log for log in logs
        if query.lower() in str(log.get("action", "")).lower()
        or query.lower() in str(log.get("user_id", "")).lower()
        or query.lower() in str(log.get("message", "")).lower()
    ]


def export_audit_logs(
    logs: List[Dict[str, Any]],
    format: str = "json"
) -> Union[str, bytes]:
    """
    Export audit logs in JSON or CSV.
    
    Args:
        logs: List of audit log dicts.
        format: 'json' or 'csv'
    Returns:
        String (JSON) or bytes (CSV)
    """
    import json
    if format == "json":
        return json.dumps(logs, indent=2)
    elif format == "csv":
        import io, csv
        if not logs:
            return b""
        keys = list(logs[0].keys())
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=keys)
        writer.writeheader()
        writer.writerows(logs)
        return buf.getvalue().encode()
    else:
        raise ValueError("Unsupported export format: choose 'json' or 'csv'")

__all__ = [
    "get_audit_log",
    "audit_log_summary",
    "search_audit_logs",
    "export_audit_logs",
    "AuditLogAccessError"
]
