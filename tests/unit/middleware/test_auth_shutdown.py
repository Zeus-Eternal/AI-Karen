from unittest.mock import AsyncMock

import pytest

from ai_karen_engine.auth.config import AuthConfig, FeatureToggles
from ai_karen_engine.auth.intelligence import IntelligenceEngine
from ai_karen_engine.auth.security import SecurityEnhancer
from ai_karen_engine.auth.service import AuthService


@pytest.mark.asyncio
async def test_intelligence_engine_shutdown():
    config = AuthConfig()
    engine = IntelligenceEngine(config)
    await engine.initialize()
    await engine.shutdown()


@pytest.mark.asyncio
async def test_security_enhancer_shutdown():
    config = AuthConfig()
    enhancer = SecurityEnhancer(config)
    await enhancer.initialize()
    await enhancer.shutdown()


@pytest.mark.asyncio
async def test_auth_service_shutdown_calls_components():
    config = AuthConfig(features=FeatureToggles(enable_intelligent_auth=True))
    service = AuthService(config)
    assert service.intelligence_layer is not None
    assert service.security_layer is not None
    service.intelligence_layer.shutdown = AsyncMock()
    service.security_layer.shutdown = AsyncMock()
    await service.shutdown()
    service.intelligence_layer.shutdown.assert_awaited_once()
    service.security_layer.shutdown.assert_awaited_once()
