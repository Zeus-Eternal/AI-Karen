"""Tests for TOTP validation during login."""

import pytest
from unittest.mock import AsyncMock, patch

from fastapi import Response
from types import SimpleNamespace

from ai_karen_engine.api_routes.auth import (
    login,
    LoginRequest,
    auth_service,
    HTTPException,
)


@pytest.fixture
def two_factor_user():
    return {
        "user_id": "test@example.com",
        "email": "test@example.com",
        "full_name": "Test User",
        "roles": ["user"],
        "tenant_id": "default",
        "preferences": {},
        "two_factor_enabled": True,
        "is_verified": True,
    }


@pytest.fixture
def session_data():
    return {
        "access_token": "access",
        "refresh_token": "refresh",
        "session_token": "session",
        "expires_in": 3600,
    }


@pytest.mark.asyncio
async def test_login_totp_success(two_factor_user, session_data):
    req = LoginRequest(
        email="test@example.com",
        password="secret",
        totp_code="123456",
    )
    request = SimpleNamespace(headers={}, client=SimpleNamespace(host="1.1.1.1"), state=SimpleNamespace())
    response = Response()
    with patch.object(auth_service, "authenticate_user", AsyncMock(return_value=two_factor_user)), \
         patch.object(auth_service, "create_session", AsyncMock(return_value=session_data)), \
         patch("ai_karen_engine.api_routes.auth.verify_totp", return_value=True):
        result = await login(req, request, response)

    assert result.access_token == "access"


@pytest.mark.asyncio
async def test_login_totp_missing_code(two_factor_user):
    req = LoginRequest(email="test@example.com", password="secret")
    request = SimpleNamespace(headers={}, client=SimpleNamespace(host="1.1.1.1"), state=SimpleNamespace())
    response = Response()
    with patch.object(auth_service, "authenticate_user", AsyncMock(return_value=two_factor_user)):
        with pytest.raises(HTTPException) as exc:
            await login(req, request, response)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Two-factor authentication required"


@pytest.mark.asyncio
async def test_login_totp_invalid_code(two_factor_user):
    req = LoginRequest(
        email="test@example.com",
        password="secret",
        totp_code="000000",
    )
    request = SimpleNamespace(headers={}, client=SimpleNamespace(host="1.1.1.1"), state=SimpleNamespace())
    response = Response()
    with patch.object(auth_service, "authenticate_user", AsyncMock(return_value=two_factor_user)), \
         patch("ai_karen_engine.api_routes.auth.verify_totp", return_value=False):
        with pytest.raises(HTTPException) as exc:
            await login(req, request, response)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid two-factor code"

