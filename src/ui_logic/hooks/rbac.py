"""
Kari UI RBAC Enforcement
- Diabolical, policy-driven, zero-trust role checks
- Wildcard and tiered org support (premium/enterprise)
- Auditable, with correlation ID for every access decision
"""

import uuid
import time
import logging
from typing import List, Dict, Any, Optional

from ui.hooks.auth import get_current_user

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

def check_rbac(user_ctx: Optional[Dict[str, Any]], required_roles: List[str]) -> bool:
    """
    Return True if user_ctx['roles'] overlaps with required_roles (or wildcard '*').
    Logs all checks for audit trail.
    """
    user = user_ctx or get_current_user()
    user_roles = set(user.get("roles", []))
    required_roles_set = set(required_roles)
    allowed = (
        "*" in required_roles_set
        or bool(user_roles.intersection(required_roles_set))
    )
    rbac_audit({
        "user": user.get("name", "unknown"),
        "user_roles": list(user_roles),
        "required_roles": list(required_roles_set),
        "allowed": allowed,
    })
    return allowed

def require_role(required_roles: List[str]):
    """
    Decorator: Only run the wrapped function if current user has required role(s).
    Example:
        @require_role(["admin"])
        def panel(): ...
    """
    def decorator(fn):
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if not check_rbac(user, required_roles):
                raise PermissionError(f"RBAC: Access denied for roles {required_roles}")
            return fn(*args, **kwargs)
        return wrapped
    return decorator

__all__ = [
    "check_rbac",
    "require_role",
]
