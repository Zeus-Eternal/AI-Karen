"""Plugin store client helpers."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from ui_logic.utils.api import api_get
except Exception:  # pragma: no cover
    def api_get(*_args, **_kwargs):
        return []


def fetch_store_plugins(limit: int = 20) -> List[Dict[str, Any]]:
    return list(api_get("/api/plugins/store", params={"limit": limit}) or [])


def search_plugins(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    return list(api_get("/api/plugins/store/search", params={"q": query, "limit": limit}) or [])


__all__ = ["api_get", "fetch_store_plugins", "search_plugins"]
