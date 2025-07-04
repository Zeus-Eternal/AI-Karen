"""
Kari API Tokens Management Logic (Framework-Agnostic)
- Enterprise-grade API token CRUD
- RBAC-secured, encrypted, and audit-logged
"""

import uuid
import datetime
from typing import List, Dict, Optional
from ui.hooks.rbac import require_roles
from ui.utils.api import get_api_token_store, save_api_token, revoke_api_token, fetch_audit_logs

def list_api_tokens(user_ctx: Dict) -> List[Dict]:
    """Return all API tokens for the user (RBAC: admin/developer only)."""
    if not user_ctx or not require_roles(user_ctx, ["admin", "developer"]):
        raise PermissionError("Insufficient privileges to list API tokens.")
    store = get_api_token_store()
    return store.list_tokens(owner=user_ctx["user_id"])

def create_api_token(user_ctx: Dict, label: str, expires: Optional[datetime.date]=None) -> str:
    """
    Create a new API token, store only hash. Returns the *raw token* (display once).
    """
    if not user_ctx or not require_roles(user_ctx, ["admin", "developer"]):
        raise PermissionError("Insufficient privileges to create API tokens.")

    token_id = str(uuid.uuid4())
    raw_token = str(uuid.uuid4()).replace("-", "") + str(uuid.uuid4()).replace("-", "")
    expires_at = expires.isoformat() if expires else None
    now = datetime.datetime.utcnow().isoformat()
    save_api_token({
        "id": token_id,
        "label": label,
        "owner": user_ctx["user_id"],
        "roles": user_ctx.get("roles", []),
        "created_at": now,
        "expires_at": expires_at,
        "active": True,
        # Store only a secure hash, never plaintext
        "token_hash": hash_token(raw_token),
    })
    return raw_token  # Show only ONCE to the user

def revoke_token(user_ctx: Dict, token_id: str):
    """Revoke (disable) an API token (RBAC: admin/developer only)."""
    if not user_ctx or not require_roles(user_ctx, ["admin", "developer"]):
        raise PermissionError("Insufficient privileges to revoke API tokens.")
    return revoke_api_token(token_id, user_ctx["user_id"])

def get_token_audit_trail(user_ctx: Dict, limit: int = 25) -> List[Dict]:
    """Fetch audit logs related to API token management for this user."""
    if not user_ctx or not require_roles(user_ctx, ["admin", "developer"]):
        raise PermissionError("Insufficient privileges to view API token audit trail.")
    logs = fetch_audit_logs(category="api_token", user_id=user_ctx["user_id"])
    return logs[-limit:][::-1]

def hash_token(token: str) -> str:
    """Secure hash for API tokens (never store plaintext)"""
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()
