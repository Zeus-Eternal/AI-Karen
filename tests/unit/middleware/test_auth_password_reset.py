import pytest
from unittest.mock import AsyncMock, MagicMock

from ai_karen_engine.auth.service import AuthService, AuthConfig
from ai_karen_engine.auth.models import UserData

@pytest.fixture
def auth_service():
    service = AuthService.__new__(AuthService)
    service.config = AuthConfig()
    service.logger = MagicMock()
    service.initialize = AsyncMock()
    service._record_auth_event = AsyncMock()
    service._record_performance_metric = AsyncMock()
    service.core_auth = AsyncMock()
    service.core_auth.token_manager = AsyncMock()
    service.core_auth.db_client = AsyncMock()
    service.security_layer = AsyncMock()
    return service

@pytest.mark.asyncio
async def test_create_password_reset_token_success(auth_service):
    user = UserData(user_id="u1", email="user@example.com")
    auth_service.core_auth.get_user_by_email.return_value = user
    auth_service.core_auth.token_manager.create_password_reset_token_with_storage.return_value = "tok"
    token = await auth_service.create_password_reset_token(
        email=user.email, ip_address="127.0.0.1", user_agent="agent"
    )
    assert token == "tok"
    auth_service.core_auth.get_user_by_email.assert_called_once_with(user.email)
    auth_service.core_auth.token_manager.create_password_reset_token_with_storage.assert_called_once()

@pytest.mark.asyncio
async def test_create_password_reset_token_user_not_found(auth_service):
    auth_service.core_auth.get_user_by_email.return_value = None
    token = await auth_service.create_password_reset_token(
        email="missing@example.com", ip_address="0.0.0.0", user_agent="agent"
    )
    assert token is None

@pytest.mark.asyncio
async def test_verify_password_reset_token_invalid(auth_service):
    auth_service.core_auth.token_manager.verify_password_reset_token_with_storage.return_value = None
    result = await auth_service.verify_password_reset_token(
        token="bad", new_password="NewPass123!", ip_address="0.0.0.0", user_agent="agent"
    )
    assert result is False

@pytest.mark.asyncio
async def test_verify_email_address_success(auth_service):
    user = UserData(user_id="u1", email="user@example.com")
    auth_service.core_auth.token_manager.verify_email_verification_token_with_storage.return_value = user
    result = await auth_service.verify_email_address("tok")
    assert result is True
    auth_service.core_auth.db_client.update_user.assert_called_once_with(user)

@pytest.mark.asyncio
async def test_verify_email_address_invalid_token(auth_service):
    auth_service.core_auth.token_manager.verify_email_verification_token_with_storage.return_value = None
    result = await auth_service.verify_email_address("bad")
    assert result is False
