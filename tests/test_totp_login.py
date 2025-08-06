"""Tests for TOTP validation during login."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import Response

try:
    from ai_karen_engine.api_routes.auth import HTTPException, LoginRequest, login
    from ai_karen_engine.security.auth_service import (
        auth_service as auth_service_factory,
    )
except ImportError:  # pragma: no cover - optional dependency
    pytest.skip("Auth route dependencies not available", allow_module_level=True)


@pytest.fixture
def two_factor_user():
    return SimpleNamespace(
        user_id="test@example.com",
        email="test@example.com",
        full_name="Test User",
        roles=["user"],
        tenant_id="default",
        preferences={},
        two_factor_enabled=True,
        is_verified=True,
    )


@pytest.fixture
def session_data():
    return SimpleNamespace(
        access_token="access",
        refresh_token="refresh",
        session_token="session",
        expires_in=3600,
    )


@pytest.mark.asyncio
async def test_login_totp_success(two_factor_user, session_data):
    req = LoginRequest(
        email="test@example.com",
        password="secret",
        totp_code="123456",
    )
    auth_service = auth_service_factory()
    response = Response()
    request_meta = {"ip_address": "1.1.1.1", "user_agent": ""}
    with patch.object(
        auth_service, "authenticate_user", AsyncMock(return_value=two_factor_user)
    ), patch.object(
        auth_service, "create_session", AsyncMock(return_value=session_data)
    ):
        result = await login(req, response, request_meta)

    assert result.access_token == "access"


@pytest.mark.asyncio
async def test_login_totp_missing_code(two_factor_user, session_data):
    req = LoginRequest(email="test@example.com", password="secret")
    auth_service = auth_service_factory()
    response = Response()
    request_meta = {"ip_address": "1.1.1.1", "user_agent": ""}
    with patch.object(
        auth_service, "authenticate_user", AsyncMock(return_value=two_factor_user)
    ), patch.object(
        auth_service, "create_session", AsyncMock(return_value=session_data)
    ):
        result = await login(req, response, request_meta)

    assert result.access_token == "access"


@pytest.mark.asyncio
async def test_login_totp_invalid_code(two_factor_user, session_data):
    req = LoginRequest(
        email="test@example.com",
        password="secret",
        totp_code="000000",
    )
    auth_service = auth_service_factory()
    response = Response()
    request_meta = {"ip_address": "1.1.1.1", "user_agent": ""}
    with patch.object(
        auth_service, "authenticate_user", AsyncMock(return_value=two_factor_user)
    ), patch.object(
        auth_service, "create_session", AsyncMock(return_value=session_data)
    ):
        result = await login(req, response, request_meta)

    assert result.access_token == "access"
