from datetime import datetime, timedelta

import pytest  # type: ignore[import-not-found]

from ai_karen_engine.security.models import (  # type: ignore[import-not-found]
    AuthContext,
    GeoLocation,
    IntelligentAuthConfig,
)


def create_auth_context() -> AuthContext:
    return AuthContext(
        email="user@example.com",
        password_hash="hashed",
        client_ip="127.0.0.1",
        user_agent="pytest",
        timestamp=datetime.utcnow(),
        request_id="req-1",
        geolocation=GeoLocation(
            country="US",
            region="NY",
            city="New York",
            latitude=40.7128,
            longitude=-74.0060,
            timezone="UTC",
        ),
        time_since_last_login=timedelta(hours=1),
        threat_intel_score=0.1,
        previous_failed_attempts=0,
    )


def test_auth_context_serialization_roundtrip() -> None:
    context = create_auth_context()
    data = context.to_dict()
    restored = AuthContext.from_dict(data)
    assert restored == context
    assert restored.validate()


def test_auth_context_invalid_timestamp() -> None:
    context = create_auth_context()
    data = context.to_dict()
    data["timestamp"] = "invalid-timestamp"
    with pytest.raises(ValueError):
        AuthContext.from_dict(data)


def test_auth_context_validation_failure() -> None:
    context = create_auth_context()
    context.threat_intel_score = 1.5
    assert not context.validate()


def test_intelligent_auth_config_serialization_and_validation() -> None:
    config = IntelligentAuthConfig()
    data = config.to_dict()
    restored = IntelligentAuthConfig.from_dict(data)
    assert restored == config
    assert restored.validate()


def test_intelligent_auth_config_validation_failure() -> None:
    config = IntelligentAuthConfig()
    config.max_processing_time = -1
    assert not config.validate()


def test_intelligent_auth_config_from_env_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("INTELLIGENT_AUTH_RISK_LOW", "0.9")
    monkeypatch.setenv("INTELLIGENT_AUTH_RISK_HIGH", "0.1")
    with pytest.raises(ValueError):
        IntelligentAuthConfig.from_env()
