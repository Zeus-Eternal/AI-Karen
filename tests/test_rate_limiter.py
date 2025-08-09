import pytest

from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.auth.exceptions import RateLimitExceededError
from ai_karen_engine.auth.security import RateLimiter
from ai_karen_engine.auth.rate_limit_store import RedisRateLimitStore

try:
    import fakeredis.aioredis as fakeredis
except Exception:  # pragma: no cover
    fakeredis = None


@pytest.mark.asyncio
async def test_rate_limiter_memory_backend():
    config = AuthConfig()
    config.security.rate_limit_max_requests = 2
    config.security.rate_limit_window_minutes = 1
    limiter = RateLimiter(config)
    ip = "127.0.0.1"
    await limiter.check_rate_limit(ip)
    await limiter.record_attempt(ip)
    await limiter.check_rate_limit(ip)
    await limiter.record_attempt(ip)
    with pytest.raises(RateLimitExceededError):
        await limiter.check_rate_limit(ip)


@pytest.mark.asyncio
async def test_rate_limiter_redis_backend():
    if fakeredis is None:
        pytest.skip("fakeredis not available")
    config = AuthConfig()
    config.security.rate_limit_max_requests = 2
    config.security.rate_limit_window_minutes = 1
    config.security.rate_limit_storage = "redis"
    fake_client = fakeredis.FakeRedis(decode_responses=True)
    store = RedisRateLimitStore(fake_client)
    limiter = RateLimiter(config, store=store)
    ip = "192.168.1.1"
    await limiter.check_rate_limit(ip)
    await limiter.record_attempt(ip)
    await limiter.check_rate_limit(ip)
    await limiter.record_attempt(ip)
    with pytest.raises(RateLimitExceededError):
        await limiter.check_rate_limit(ip)
    await fake_client.close()
