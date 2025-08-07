import pytest

from ai_karen_engine.security.auth_service import AuthService
from ai_karen_engine.security import auth_manager


@pytest.mark.asyncio
async def test_password_reset_flow():
    service = AuthService()
    await service.create_user("reset@example.com", "oldpass")
    token = await service.request_password_reset("reset@example.com")
    assert token is not None
    assert await service.reset_password(token, "newpass")
    assert await service.authenticate_user("reset@example.com", "newpass")


@pytest.mark.asyncio
async def test_email_verification_flow():
    service = AuthService()
    await service.create_user("verify@example.com", "pass")
    # user should start unverified in the underlying store
    assert auth_manager._USERS["verify@example.com"]["is_verified"] is False
    token = await service.request_email_verification("verify@example.com")
    assert token is not None
    assert await service.verify_email(token)
    assert auth_manager._USERS["verify@example.com"]["is_verified"] is True


@pytest.mark.asyncio
async def test_update_user_profile():
    service = AuthService()
    user = await service.create_user("profile@example.com", "pass")
    assert await service.update_user_profile(
        user.user_id,
        full_name="Test User",
        preferences={"theme": "dark"},
    )
    stored = auth_manager._USERS[user.user_id]
    assert stored.get("full_name") == "Test User"
    assert stored.get("preferences", {}).get("theme") == "dark"
