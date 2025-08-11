import pytest

from ai_karen_engine.auth.models import AuthEvent, AuthEventType
from ai_karen_engine.auth.security import AuditLogger


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "event_type,metric_name",
    [
        (AuthEventType.LOGIN_SUCCESS, "kari_auth_success_total"),
        (AuthEventType.LOGIN_FAILED, "kari_auth_failure_total"),
    ],
)
async def test_audit_logger_emits_prometheus_metrics(
    event_type, metric_name, metrics_registry, auth_config
):
    logger = AuditLogger(auth_config)

    await logger.log_auth_event(
        AuthEvent(event_type=event_type, processing_time_ms=50)
    )

    assert metrics_registry.get_sample_value(metric_name) == 1.0
    assert (
        metrics_registry.get_sample_value("kari_auth_processing_seconds_count")
        == 1.0
    )

