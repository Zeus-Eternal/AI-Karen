"""
Integration adapter for KIRE routing with the existing LLMRegistry.

Provides a thin wrapper to reuse the KIRERouter housed under `ai_karen_engine.routing`.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from ai_karen_engine.routing.kire_router import KIRERouter as _KIRERouter
from ai_karen_engine.routing.types import RouteRequest, RouteDecision


class KIRERouter:
    """Adapter that mirrors KIRERouter under integrations namespace."""

    def __init__(self, llm_registry=None) -> None:
        self._router = _KIRERouter(llm_registry=llm_registry)

    async def route(self, *, user_id: str, task_type: str, query: str = "", khrp_step: Optional[str] = None, context: Optional[Dict[str, Any]] = None, requirements: Optional[Dict[str, Any]] = None) -> RouteDecision:
        req = RouteRequest(
            user_id=user_id,
            task_type=task_type,
            query=query,
            khrp_step=khrp_step,
            context=context or {},
            requirements=requirements or {},
        )
        return await self._router.route_provider_selection(req)


__all__ = ["KIRERouter", "RouteRequest", "RouteDecision"]

