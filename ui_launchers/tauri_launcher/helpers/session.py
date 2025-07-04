"""User context provider for the Tauri launcher (demo)."""
from typing import Dict, Any

def get_user_context() -> Dict[str, Any]:
    """Return demo user context. Replace with real auth integration."""
    return {
        "user_id": "zeus",
        "name": "God Zeus",
        "roles": ["admin", "developer", "user"],
        "session_token": "dev-token",
    }

__all__ = ["get_user_context"]
