from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest import MonkeyPatch

from ai_karen_engine.security.auth_service import AuthService
from ai_karen_engine.security.config import AuthConfig, FeatureToggles
from ai_karen_engine.security.intelligence_engine import IntelligenceEngine
from ai_karen_engine.security.models import AuthContext

# mypy: ignore-errors


@pytest.mark.asyncio
async def test_intelligence_engine_calculates_risk_score(
    monkeypatch: MonkeyPatch,
) -> None:
    cred = MagicMock()
    cred_instance = MagicMock()
    cred_instance.analyze_credentials = AsyncMock(return_value=SimpleNamespace())
    cred.return_value = cred_instance
    monkeypatch.setattr(
        "ai_karen_engine.security.intelligence_engine.CredentialAnalyzer", cred
    )

    beh = MagicMock()
    beh_instance = MagicMock()
    beh_instance.generate_behavioral_embedding = AsyncMock(
        return_value=SimpleNamespace()
    )
    beh_instance.analyze_embedding_for_anomalies = AsyncMock(
        return_value=SimpleNamespace()
    )
    beh.return_value = beh_instance
    monkeypatch.setattr(
        "ai_karen_engine.security.intelligence_engine.BehavioralEmbeddingService",
        beh,
    )

    anomaly = MagicMock()
    anomaly_instance = MagicMock()
    anomaly_instance.analyze_authentication_attempt = AsyncMock(
        return_value=SimpleNamespace(overall_risk_score=0.42)
    )
    anomaly.return_value = anomaly_instance
    monkeypatch.setattr(
        "ai_karen_engine.security.intelligence_engine.ComprehensiveAnomalyEngine",
        anomaly,
    )

    adaptive = MagicMock()
    adaptive_instance = MagicMock()
    adaptive_instance.initialize = AsyncMock(return_value=True)
    adaptive.return_value = adaptive_instance
    monkeypatch.setattr(
        "ai_karen_engine.security.intelligence_engine.AdaptiveLearningEngine", adaptive
    )

    engine = IntelligenceEngine()
    engine._initialized = True

    context = AuthContext(
        email="user@example.com",
        password_hash="hash",
        client_ip="0.0.0.0",
        user_agent="agent",
        timestamp=datetime.utcnow(),
        request_id="req",
    )

    score = await engine.calculate_risk_score(context)

    assert score == 0.42
    cred_instance.analyze_credentials.assert_called_once_with(
        "user@example.com", "hash"
    )
    beh_instance.generate_behavioral_embedding.assert_called_once()
    beh_instance.analyze_embedding_for_anomalies.assert_called_once()
    anomaly_instance.analyze_authentication_attempt.assert_called_once()


@pytest.mark.asyncio
async def test_auth_service_blocks_on_high_risk(monkeypatch: MonkeyPatch) -> None:
    config = AuthConfig(features=FeatureToggles(enable_intelligent_checks=True))

    mock_engine = MagicMock()
    mock_engine.calculate_risk_score = AsyncMock(return_value=0.9)
    from ai_karen_engine.security.models import IntelligentAuthConfig

    mock_engine.config = IntelligentAuthConfig()

    monkeypatch.setattr(
        "ai_karen_engine.security.auth_service.IntelligenceEngine", lambda: mock_engine
    )

    auth = AuthService(config=config)

    monkeypatch.setattr(
        auth.core_authenticator,
        "authenticate_user",
        AsyncMock(return_value={"user_id": "1", "email": "user@example.com"}),
    )

    result = await auth.authenticate_user("user@example.com", "password")

    assert result is None
    assert mock_engine.calculate_risk_score.await_count == 1
