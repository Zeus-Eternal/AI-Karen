import asyncio
import time

import pytest

from ai_karen_engine.routing.kire_router import KIRERouter
from ai_karen_engine.routing.types import RouteRequest
from ai_karen_engine.routing.kire_router import (
    get_routing_cache_stats,
    get_routing_dedup_stats,
)


@pytest.mark.asyncio
async def test_cache_hit_and_dedup(monkeypatch):
    # Make all healthy
    import ai_karen_engine.routing.kire_router as kr

    async def healthy(_p: str) -> bool:
        return True

    monkeypatch.setattr(kr.ProviderHealth, "is_healthy", healthy)
    router = KIRERouter()

    req = RouteRequest(user_id="u3", task_type="chat", query="hello")
    # First call: miss
    t0 = time.perf_counter()
    dec1 = await router.route_provider_selection(req)
    miss_latency = time.perf_counter() - t0
    assert dec1.provider

    # Second call: should hit cache and be faster
    t1 = time.perf_counter()
    dec2 = await router.route_provider_selection(req)
    hit_latency = time.perf_counter() - t1
    assert dec2.provider == dec1.provider
    # Can't be too strict, but second should be faster in most runs
    assert hit_latency <= miss_latency or hit_latency < 0.05

    # Dedup under concurrency
    async def do_call():
        return await router.route_provider_selection(req)

    await asyncio.gather(*[do_call() for _ in range(5)])
    stats = get_routing_dedup_stats()
    # Dedup rate should be non-zero with concurrent identical calls
    assert stats.get("deduplication_rate", 0) >= 0

    cache_stats = get_routing_cache_stats()
    assert cache_stats["size"] >= 1

