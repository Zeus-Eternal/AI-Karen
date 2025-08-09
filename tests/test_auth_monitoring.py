import pytest
from prometheus_client import CollectorRegistry

from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.auth.monitoring import (
    AuthMonitor,
    init_auth_metrics,
    metrics_hook,
)
from ai_karen_engine.auth.models import AuthEvent, AuthEventType


@pytest.mark.asyncio
async def test_auth_monitor_records_metrics():
    config = AuthConfig()
    monitor = AuthMonitor(config)
    event = AuthEvent(
        event_type=AuthEventType.LOGIN_SUCCESS,
        user_id="user1",
        email="user@example.com",
        tenant_id="tenant1",
        ip_address="127.0.0.1",
        user_agent="pytest",
        success=True,
        processing_time_ms=50,
    )
    await monitor.record_auth_event(event)
    base_tags = {
        "event_type": "login_success",
        "success": "true",
        "tenant_id": "tenant1",
    }
    assert monitor.metrics.get_counter("auth.events.total", base_tags) == 1
    assert monitor.metrics.get_counter("auth.events.success", base_tags) == 1
    assert len(monitor._recent_events) == 1
    await monitor.shutdown()


@pytest.mark.asyncio
async def test_auth_monitor_triggers_security_alert():
    config = AuthConfig()
    monitor = AuthMonitor(config)
    event = AuthEvent(
        event_type=AuthEventType.LOGIN_SUCCESS,
        user_id="user1",
        email="user@example.com",
        ip_address="127.0.0.1",
        user_agent="pytest",
        success=True,
        risk_score=0.95,
    )
    await monitor.record_auth_event(event)
    assert len(monitor.alerts.get_alert_history()) == 1
    await monitor.shutdown()


def test_metrics_hook_records_prometheus_metrics():
    registry = CollectorRegistry()
    init_auth_metrics(registry=registry, force=True)
    metrics_hook("login_success", {"processing_time": 0.1})
    metrics_hook("login_failure", {"processing_time": 0.2})
    assert registry.get_sample_value("kari_auth_success_total") == 1.0
    assert registry.get_sample_value("kari_auth_failure_total") == 1.0
