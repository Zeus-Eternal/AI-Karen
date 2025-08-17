"""
Kari UI RBAC Hooks - Zero Trust, Audit, and API Compatibility
- check_rbac (legacy alias) + user_has_role (canonical)
- Fully auditable, supports * wildcard, plugin, org
"""

import uuid
import time
from typing import List, Dict, Any, Optional

RBAC_LOG_PATH = "/secure/logs/kari/rbac_audit.log"

def rbac_audit(event: Dict[str, Any]):
    """Log RBAC checks for full forensic trace."""
    event["timestamp"] = int(time.time())
    event["correlation_id"] = str(uuid.uuid4())
    try:
        with open(RBAC_LOG_PATH, "a") as f:
            f.write(str(event) + "\n")
    except Exception:
        pass

def user_has_role(user_ctx: Optional[Dict[str, Any]], required_roles: List[str]) -> bool:
    """
    True if user_ctx['roles'] overlaps required_roles or wildcard '*'.
    Full audit. Used for RBAC gates.
    """
    user = user_ctx or {}
    user_roles = set(user.get("roles", []))
    required_roles_set = set(required_roles)
    allowed = "*" in required_roles_set or bool(
        user_roles.intersection(required_roles_set)
    )
    rbac_audit({
        "user": user.get("name", "unknown"),
        "user_roles": list(user_roles),
        "required_roles": list(required_roles_set),
        "allowed": allowed,
    })
    return allowed

# === Alias for legacy API, keep your downstream happy ===
check_rbac = user_has_role

def require_roles(user_ctx: Optional[Dict[str, Any]], required_roles: List[str]) -> bool:
    """
    Raises PermissionError if user does not have any required_roles.
    Returns True if allowed.
    """
    if not user_has_role(user_ctx, required_roles):
        raise PermissionError(f"RBAC: Access denied. Required: {required_roles}")
    return True

def require_role(required_roles: List[str]):
    """
    Decorator: Only run if user has required roles.
    Example:
        @require_role(["admin"])
        def admin_panel(ctx): ...
    """
    def decorator(fn):
        def wrapped(*args, **kwargs):
            user_ctx = kwargs.get("user_ctx") or (args[0] if args else None)
            if not user_has_role(user_ctx, required_roles):
                raise PermissionError(f"RBAC: Access denied for roles {required_roles}")
            return fn(*args, **kwargs)
        return wrapped
    return decorator

__all__ = [
    "user_has_role",
    "check_rbac",
    "require_role",
    "require_roles",
]
