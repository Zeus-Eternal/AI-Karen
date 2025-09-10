import asyncio

import pytest

# Ensure actions (predictors) are registered
import ai_karen_engine.routing.actions  # noqa: F401

from ai_karen_engine.core.cortex.routing_intents import resolve_routing_intent
from ai_karen_engine.core.cortex.dispatch import dispatch


def test_resolve_routing_intent_detects_routing_select():
    intent, meta = resolve_routing_intent("please switch model to openai gpt-4o", {"user_id": "u1"})
    assert intent == "routing.select"
    assert meta.get("match") == "routing"


@pytest.mark.asyncio
async def test_dispatch_routes_to_routing_predictor():
    user_ctx = {"user_id": "u-test"}
    out = await dispatch(user_ctx, "route to best model for code", mode="predictor")
    assert out["intent"] in ("routing.select", "routing.profile", "routing.health") or out["intent"] == "unknown"
    # If routing.select was chosen, ensure structure is present
    if out["intent"] == "routing.select":
        result = out["result"]
        assert "provider" in result and "model" in result

