import pytest
from unittest.mock import MagicMock

from ai_karen_engine.security.auth_service import AuthService
from ai_karen_engine.security.config import AuthConfig
from ai_karen_engine.security.observability import AuthObservabilityService, AuthEventType


@pytest.mark.asyncio
async def test_auth_service_observability_integration():
    config = AuthConfig()
    config.features.enable_audit_logging = False

    observability = MagicMock(spec=AuthObservabilityService)
    service = AuthService(config=config, observability_service=observability)

    await service.create_user("obs@example.com", "password")

    user = await service.authenticate_user("obs@example.com", "password")
    assert user is not None
    assert (
        observability.record_auth_event.call_args_list[-1].kwargs["event_type"]
        == AuthEventType.LOGIN_SUCCESS
    )

    observability.record_auth_event.reset_mock()
    assert await service.authenticate_user("obs@example.com", "wrong") is None
    assert (
        observability.record_auth_event.call_args_list[-1].kwargs["event_type"]
        == AuthEventType.LOGIN_FAILURE
    )
