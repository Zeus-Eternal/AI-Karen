import asyncio
from unittest.mock import patch

from ai_karen_engine.routing import kire_router
from ai_karen_engine.routing.kire_router import KIRERouter
from ai_karen_engine.routing.types import RouteRequest


def test_cache_key_includes_query_context_signature():
    router = KIRERouter()
    base_request = RouteRequest(
        user_id="user-1",
        task_type="chat",
        query="Summarize the doc",
        requirements={"priority": "high"},
        context={"tenant_id": "t1", "request_metadata": {"correlation_id": "abc"}},
    )
    key_one = router._generate_cache_key(base_request)

    key_two = router._generate_cache_key(
        RouteRequest(
            user_id="user-1",
            task_type="chat",
            query="Summarize the financial document",
            requirements={"priority": "high"},
            context={"tenant_id": "t1", "request_metadata": {"correlation_id": "abc"}},
        )
    )

    different_context = router._generate_cache_key(
        RouteRequest(
            user_id="user-1",
            task_type="chat",
            query="Summarize the doc",
            requirements={"priority": "high"},
            context={"tenant_id": "t2", "request_metadata": {"correlation_id": "abc"}},
        )
    )

    assert key_one != key_two, "Cache key must change when query text changes"
    assert key_one != different_context, "Cache key must change when routing context changes"


async def _run_health_fallback(router: KIRERouter) -> tuple[str, str, str, float]:
    req = RouteRequest(user_id="user-2", task_type="chat", query="hi")
    analysis = router.task_analyzer.analyze(req.query, context=req.context)
    cognition = router.cognitive_reasoner.evaluate(req, analysis, profile=None)
    return await router._refine_by_requirements(
        provider="openai",
        model="gpt-4o",
        req=req,
        chain=["openai", "deepseek"],
        required_caps=["text"],
        inferred_task="chat",
        analysis=analysis,
        cognition=cognition,
    )


def test_provider_health_fallback_degrades():
    router = KIRERouter()

    class ConservativeHealth:
        SOURCE = "fallback"

        @staticmethod
        async def is_healthy(provider: str) -> bool:
            return False

    with patch.object(kire_router, "ProviderHealth", ConservativeHealth):
        provider, model, reason, confidence = asyncio.run(_run_health_fallback(router))

    assert "health unavailable" in reason
    assert confidence <= 0.55
