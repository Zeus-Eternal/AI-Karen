"""Logic for listing active user sessions."""

from typing import List, Dict


def get_active_sessions() -> List[Dict[str, str]]:
    """Return a placeholder list of active sessions."""
    # This would query the session store/service in a real system
    return [
        {"user": "demo", "status": "active"},
    ]
