import pytest
from prometheus_client import CollectorRegistry

from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.auth.models import AuthEvent, AuthEventType
from ai_karen_engine.auth.security import AuditLogger
from ai_karen_engine.auth.monitoring import init_auth_metrics


@pytest.mark.asyncio
async def test_audit_logger_emits_prometheus_metrics():
    registry = CollectorRegistry()
    init_auth_metrics(registry, force=True)
    logger = AuditLogger(AuthConfig())

    # Record a successful and failed login event
    await logger.log_auth_event(
        AuthEvent(event_type=AuthEventType.LOGIN_SUCCESS, processing_time_ms=50)
    )
    await logger.log_auth_event(
        AuthEvent(event_type=AuthEventType.LOGIN_FAILED, processing_time_ms=100)
    )

    # Validate metrics were incremented
    success_total = registry.get_sample_value("kari_auth_success_total")
    failure_total = registry.get_sample_value("kari_auth_failure_total")
    processing_count = registry.get_sample_value(
        "kari_auth_processing_seconds_count"
    )

    assert success_total == 1.0
    assert failure_total == 1.0
    assert processing_count == 2.0

