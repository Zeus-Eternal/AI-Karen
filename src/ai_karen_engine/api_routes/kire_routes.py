"""
KIRE routing diagnostics routes.

Surfaces cache and dedup stats for live debugging. Admin-only.
"""
from __future__ import annotations

from typing import Any, Dict

from ai_karen_engine.utils.dependency_checks import import_fastapi
from ai_karen_engine.core.dependencies import get_current_user_context
from ai_karen_engine.routing.kire_router import (
    get_routing_cache_stats,
    get_routing_dedup_stats,
)

APIRouter, Depends, HTTPException = import_fastapi("APIRouter", "Depends", "HTTPException")

router = APIRouter(prefix="/kire", tags=["kire"])


def _require_admin(user_ctx: Dict[str, Any]) -> None:
    if user_ctx.get("is_admin") or "admin" in set(user_ctx.get("roles", [])):
        return
    raise HTTPException(status_code=403, detail="Admin permissions required")


@router.get("/debug/cache-stats", response_model=Dict[str, Any])
async def kire_cache_stats(current_user: Dict[str, Any] = Depends(get_current_user_context)) -> Dict[str, Any]:
    """Return routing cache and dedup stats (admin-only)."""
    _require_admin(current_user)
    return {
        "routing_cache": get_routing_cache_stats(),
        "request_deduplicator": get_routing_dedup_stats(),
    }

