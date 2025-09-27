import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from ai_karen_engine.routing import actions as routing_actions
from ai_karen_engine.routing.types import RouteDecision


def test_routing_select_requires_rbac_guard():
    routing_actions._rate_limit_counters.clear()
    with pytest.raises(PermissionError):
        asyncio.run(routing_actions.routing_select_handler({}, "hello", context={}))


def test_routing_select_rate_limit():
    routing_actions._rate_limit_counters.clear()

    with patch.object(routing_actions, "_RATE_LIMIT_MAX_CALLS", 2, create=True), patch.object(
        routing_actions, "_RATE_LIMIT_WINDOW_SECONDS", 3600, create=True
    ), patch.object(
        routing_actions._router,
        "route_provider_selection",
        AsyncMock(
            return_value=RouteDecision(
                provider="openai",
                model="gpt-4o-mini",
                reasoning="mock",
                confidence=0.9,
                fallback_chain=["openai"],
                metadata={},
            )
        ),
    ):
        user_ctx = {"user_id": "test-user", "roles": ["routing"]}
        query = "Help me"
        context = {"requirements": {}}

        asyncio.run(routing_actions.routing_select_handler(user_ctx, query, context=context))
        asyncio.run(routing_actions.routing_select_handler(user_ctx, query, context=context))
        with pytest.raises(PermissionError):
            asyncio.run(routing_actions.routing_select_handler(user_ctx, query, context=context))

    routing_actions._rate_limit_counters.clear()
