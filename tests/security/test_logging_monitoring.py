import logging
import re

import pytest
from prometheus_client import CollectorRegistry

from ai_karen_engine.security.auth_metrics import (
    init_auth_metrics,
    metrics_hook,
)
from ai_karen_engine.security.auth_service import AuthService
from ai_karen_engine.security.config import AuthConfig


@pytest.mark.asyncio
async def test_audit_logging_and_metrics(caplog):
    registry = CollectorRegistry()
    init_auth_metrics(registry=registry, force=True)

    config = AuthConfig()
    config.features.enable_audit_logging = True
    service = AuthService(config=config, metrics_hook=metrics_hook)

    with caplog.at_level(logging.INFO):
        await service.create_user("log@example.com", "password")
        user = await service.authenticate_user("log@example.com", "password")
        assert user is not None
        assert await service.authenticate_user("log@example.com", "wrong") is None

    messages = [r.getMessage() for r in caplog.records]
    assert any(re.match(r"AUTH EVENT login_success", m) for m in messages)
    assert any(re.match(r"AUTH EVENT login_failure", m) for m in messages)

    assert registry.get_sample_value("kari_auth_success_total") == 1
    failure_total = registry.get_sample_value("kari_auth_failure_total")
    assert failure_total and failure_total >= 1
    duration_sum = registry.get_sample_value("kari_auth_processing_seconds_sum")
    assert duration_sum and duration_sum > 0
