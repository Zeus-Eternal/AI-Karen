from unittest.mock import AsyncMock

import pytest  # type: ignore[import-not-found]

from ai_karen_engine.security.anomaly_detector import (  # type: ignore[import-not-found]
    AnomalyDetector,
)
from ai_karen_engine.security.intelligent_auth_base import (  # type: ignore[import-not-found]
    ServiceStatus,
)
from ai_karen_engine.security.models import (  # type: ignore[import-not-found]
    IntelligentAuthConfig,
)
from ai_karen_engine.security.threat_intelligence import (  # type: ignore[import-not-found]
    ReputationLevel,
    ThreatIntelligenceEngine,
)


@pytest.mark.asyncio  # type: ignore[misc]
async def test_anomaly_detector_health_check_success() -> None:
    detector = AnomalyDetector(IntelligentAuthConfig())
    detector._perform_health_check = AsyncMock(return_value=True)
    status = await detector.health_check()
    assert status.status == ServiceStatus.HEALTHY


@pytest.mark.asyncio  # type: ignore[misc]
async def test_anomaly_detector_health_check_failure() -> None:
    detector = AnomalyDetector(IntelligentAuthConfig())
    detector._perform_health_check = AsyncMock(return_value=False)
    status = await detector.health_check()
    assert status.status == ServiceStatus.DEGRADED


@pytest.mark.asyncio  # type: ignore[misc]
async def test_anomaly_detector_health_check_exception() -> None:
    detector = AnomalyDetector(IntelligentAuthConfig())
    detector._perform_health_check = AsyncMock(side_effect=RuntimeError("boom"))
    status = await detector.health_check()
    assert status.status == ServiceStatus.UNHEALTHY
    assert "boom" in status.error_message


@pytest.mark.asyncio  # type: ignore[misc]
async def test_threat_intelligence_engine_basic_health_check() -> None:
    engine = ThreatIntelligenceEngine({})
    stats = engine.get_threat_statistics()
    assert stats["total_indicators"] > 0

    result = await engine.analyze_ip_reputation("10.0.0.1")
    assert result.reputation_level != ReputationLevel.CLEAN
