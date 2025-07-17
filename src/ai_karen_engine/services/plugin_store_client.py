from typing import Any, Dict, List, Optional

from ui_logic.utils.api import api_get


def fetch_store_plugins(
    limit: int = 50,
    token: Optional[str] = None,
    org: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return plugin metadata from the store API or an empty list on error."""
    try:
        params = {"limit": limit}
        return api_get("plugins/store", params=params, token=token, org=org)
    except Exception:
        return []


def search_plugins(
    query: str,
    limit: int = 50,
    token: Optional[str] = None,
    org: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search public plugin marketplace."""
    try:
        params = {"q": query, "limit": limit}
        return api_get("plugins/search", params=params, token=token, org=org)
    except Exception:
        return []


__all__ = ["fetch_store_plugins", "search_plugins"]
