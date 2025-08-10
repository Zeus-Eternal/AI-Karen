import pytest
from datetime import datetime, timezone

from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.auth.intelligence import (
    AnomalyDetector,
    BehavioralPattern,
    LoginAttempt,
)


@pytest.mark.asyncio
async def test_detect_anomalies_normal_behavior():
    """AnomalyDetector should flag unusual attributes."""
    detector = AnomalyDetector(AuthConfig())

    attempt = LoginAttempt(
        user_id="user1",
        email="user@example.com",
        ip_address="1.2.3.4",
        user_agent="agent",
        timestamp=datetime(2024, 1, 1, 3, tzinfo=timezone.utc),
        device_fingerprint="device-999",
        geolocation={"latitude": 34.0522, "longitude": -118.2437},
    )
    pattern = BehavioralPattern(
        user_id="user1",
        typical_login_hours=[9, 10, 11],
        typical_locations=[{"latitude": 40.7128, "longitude": -74.0060}],
        typical_devices=["device-123"],
        login_frequency={"tuesday": 5},
    )

    result = await detector.detect_anomalies(attempt, pattern)
    assert result.is_anomaly is True
    assert {
        "unusual_time",
        "unusual_location",
        "unusual_device",
        "unusual_frequency",
    }.issubset(set(result.anomaly_types))
    assert result.anomaly_score > 0
    assert result.confidence > 0


@pytest.mark.asyncio
async def test_detect_anomalies_without_pattern():
    """No behavioral pattern should yield no anomalies."""
    detector = AnomalyDetector(AuthConfig())
    attempt = LoginAttempt(
        user_id="user1",
        email="user@example.com",
        ip_address="1.2.3.4",
        user_agent="agent",
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )

    result = await detector.detect_anomalies(attempt, None)
    assert result.is_anomaly is False
    assert result.anomaly_score == 0.0


@pytest.mark.asyncio
async def test_detect_anomalies_error_handling(monkeypatch):
    """Failures in detection methods should be handled gracefully."""
    detector = AnomalyDetector(AuthConfig())
    attempt = LoginAttempt(
        user_id="user1",
        email="user@example.com",
        ip_address="1.2.3.4",
        user_agent="agent",
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )

    def boom(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(detector, "_detect_time_anomaly", boom)

    result = await detector.detect_anomalies(attempt, None)
    assert result.is_anomaly is False
    assert result.anomaly_score == 0.0
    assert "error" in result.details
