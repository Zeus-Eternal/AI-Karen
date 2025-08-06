import pytest

from ai_karen_engine.security.auth_service import AuthService
from ai_karen_engine.security.config import AuthConfig
from ai_karen_engine.security.security_enhancer import RateLimiter


@pytest.mark.asyncio
async def test_logging_with_metrics_hook():
    metrics: list[tuple[str, dict]] = []
    config = AuthConfig()
    config.features.enable_audit_logging = True
    service = AuthService(config=config, metrics_hook=lambda e, d: metrics.append((e, d)))

    assert service.security_enhancer is not None
    logger = service.security_enhancer.audit_logger

    await service.create_user("user@example.com", "password")
    user = await service.authenticate_user("user@example.com", "password")
    assert user is not None
    assert await service.authenticate_user("user@example.com", "wrong") is None

    events = [e.event for e in logger.events]
    assert "login_success" in events
    assert "login_failure" in events
    logged = [name for name, _ in metrics]
    assert "login_success" in logged and "login_failure" in logged


@pytest.mark.asyncio
async def test_rate_limit_blocks_excessive_attempts():
    metrics: list[tuple[str, dict]] = []
    config = AuthConfig()
    config.features.enable_audit_logging = True
    config.features.enable_rate_limiter = True
    service = AuthService(config=config, metrics_hook=lambda e, d: metrics.append((e, d)))

    # make rate limiter very small for the test
    assert service.security_enhancer is not None
    service.security_enhancer.rate_limiter = RateLimiter(2, 60)
    logger = service.security_enhancer.audit_logger

    await service.create_user("rate@example.com", "password")
    assert await service.authenticate_user("rate@example.com", "wrong") is None
    assert await service.authenticate_user("rate@example.com", "wrong") is None
    # third attempt should be blocked by rate limiter
    assert await service.authenticate_user("rate@example.com", "wrong") is None

    events = [e.event for e in logger.events]
    assert events.count("login_failure") >= 2
    assert "rate_limit_exceeded" in events
    logged = [name for name, _ in metrics]
    assert "rate_limit_exceeded" in logged
