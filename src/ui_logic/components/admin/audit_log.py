"""
Kari Audit Log Logic
- Pulls and filters audit events from secure log store
- Supports RBAC, log slicing, and event search
"""

from typing import List, Dict, Any, Optional
from ui.utils.api import fetch_audit_logs

def get_audit_log(user_ctx: Dict, filter: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
    """
    Returns a list of audit events, most recent first. RBAC enforced.
    """
    category = filter.get("category") if filter else None
    search = filter.get("search") if filter else None
    logs = fetch_audit_logs(category=category, user_id=user_ctx["user_id"], search=search)
    return logs[-limit:][::-1]
