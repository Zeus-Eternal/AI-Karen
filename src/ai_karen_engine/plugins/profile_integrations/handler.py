"""Profile-level Integrations plugin."""
from __future__ import annotations

from typing import Dict

# In-memory store mapping user_id -> {service: token}
_PROFILE_INTEGRATIONS: Dict[str, Dict[str, str]] = {}


async def run(params: Dict) -> Dict:
    """Manage integration tokens for a user profile.

    Supported actions:
    - ``list``: Return all integrations for ``user_id``.
    - ``set``: Set ``token`` for ``service``.
    - ``delete``: Remove ``service`` entry.
    """
    user_id = params.get("user_id")
    if not user_id:
        return {"error": "user_id required"}
    action = params.get("action", "list")
    store = _PROFILE_INTEGRATIONS.setdefault(user_id, {})

    if action == "list":
        return {"integrations": store}
    if action == "set":
        service = params.get("service")
        token = params.get("token")
        if not service or token is None:
            return {"error": "service and token required"}
        store[service] = token
        return {"status": "saved", "service": service}
    if action == "delete":
        service = params.get("service")
        if not service:
            return {"error": "service required"}
        store.pop(service, None)
        return {"status": "deleted", "service": service}
    return {"error": f"unknown action {action}"}
