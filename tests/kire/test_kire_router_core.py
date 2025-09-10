import asyncio
import time
import types

import pytest

from ai_karen_engine.routing.kire_router import KIRERouter
from ai_karen_engine.routing.types import RouteRequest


@pytest.mark.asyncio
async def test_kire_router_basic_decision(monkeypatch):
    # Force health to true for all providers
    import ai_karen_engine.routing.kire_router as kr

    async def healthy(_provider: str) -> bool:
        return True

    monkeypatch.setattr(kr.ProviderHealth, "is_healthy", healthy)

    router = KIRERouter()
    req = RouteRequest(user_id="u1", task_type="chat", query="hello world")
    dec = await router.route_provider_selection(req)
    assert dec.provider in {"openai", "deepseek", "llamacpp", "gemini", "huggingface"}
    assert dec.model
    assert dec.confidence > 0


@pytest.mark.asyncio
async def test_kire_router_fallback_on_unhealthy(monkeypatch):
    # Make openai unhealthy, deepseek healthy
    import ai_karen_engine.routing.kire_router as kr

    async def is_healthy(p: str) -> bool:
        if p == "openai":
            return False
        return True

    monkeypatch.setattr(kr.ProviderHealth, "is_healthy", is_healthy)

    router = KIRERouter()
    req = RouteRequest(user_id="u2", task_type="reasoning", query="explain why")
    dec = await router.route_provider_selection(req)
    # Should not pick openai when unhealthy; deepseek acceptable
    assert dec.provider != "openai"

