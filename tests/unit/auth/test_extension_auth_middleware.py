"""
Unit tests for extension authentication middleware.
Tests the core authentication logic, token validation, and permission checking.
"""

import pytest
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

from server.security import ExtensionAuthManager


class TestExtensionAuthManager:
    """Test cases for ExtensionAuthManager core functionality."""

    @pytest.fixture
    def auth_config(self):
        """Test configuration for authentication manager."""
        return {
            "secret_key": "test-secret-key",
            "algorithm": "HS256",
            "enabled": True,
            "auth_mode": "production",
            "dev_bypass_enabled": False,
            "require_https": False,
            "access_token_expire_minutes": 60,
            "service_token_expire_minutes": 30,
            "api_key": "test-api-key",
            "default_permissions": ["extension:read", "extension:write"]
        }

    @pytest.fixture
    def auth_manager(self, auth_config):
        """Create authentication manager for testing."""
        return ExtensionAuthManager(auth_config)

    @pytest.fixture
    def mock_request(self):
        """Create mock request for testing."""
        request = Mock(spec=Request)
        request.url.path = "/api/extensions/"
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.100"
        return request

    def test_create_access_token(self, auth_manager):
        """Test access token creation."""
        user_id = "test-user"
        tenant_id = "test-tenant"
        roles = ["user"]
        permissions = ["extension:read"]

        token = auth_manager.create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=roles,
            permissions=permissions
        )

        # Verify token can be decoded
        payload = jwt.decode(token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        
        assert payload["user_id"] == user_id
        assert payload["tenant_id"] == tenant_id
        assert payload["roles"] == roles
        assert payload["permissions"] == permissions
        assert payload["token_type"] == "access"
        assert payload["iss"] == "kari-extension-system"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_service_token(self, auth_manager):
        """Test service token creation."""
        service_name = "test-service"
        permissions = ["extension:background_tasks"]

        token = auth_manager.create_service_token(
            service_name=service_name,
            permissions=permissions
        )

        # Verify token can be decoded
        payload = jwt.decode(token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        
        assert payload["service_name"] == service_name
        assert payload["permissions"] == permissions
        assert payload["token_type"] == "service"
        assert payload["iss"] == "kari-extension-system"

    def test_create_background_task_token(self, auth_manager):
        """Test background task token creation."""
        task_name = "test-task"
        user_id = "test-user"
        service_name = "test-service"

        token = auth_manager.create_background_task_token(
            task_name=task_name,
            user_id=user_id,
            service_name=service_name
        )

        # Should create service token for background tasks
        payload = jwt.decode(token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        
        assert payload["service_name"] == service_name
        assert "extension:background_tasks" in payload["permissions"]
        assert "extension:execute" in payload["permissions"]

    @pytest.mark.asyncio
    async def test_authenticate_valid_token(self, auth_manager, mock_request):
        """Test authentication with valid JWT token."""
        # Create valid token
        token = auth_manager.create_access_token(
            user_id="test-user",
            tenant_id="test-tenant",
            roles=["user"],
            permissions=["extension:read"]
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        user_context = await auth_manager.authenticate_extension_request(mock_request, credentials)

        assert user_context["user_id"] == "test-user"
        assert user_context["tenant_id"] == "test-tenant"
        assert user_context["roles"] == ["user"]
        assert user_context["permissions"] == ["extension:read"]

    @pytest.mark.asyncio
    async def test_authenticate_expired_token(self, auth_manager, mock_request):
        """Test authentication with expired token."""
        # Create expired token
        expired_time = datetime.now(timezone.utc) - timedelta(minutes=1)
        token = auth_manager.create_access_token(
            user_id="test-user",
            expires_delta=timedelta(seconds=-60)  # Already expired
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            await auth_manager.authenticate_extension_request(mock_request, credentials)
        
        assert exc_info.value.status_code == 403
        assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_authenticate_invalid_token(self, auth_manager, mock_request):
        """Test authentication with invalid token."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")

        with pytest.raises(HTTPException) as exc_info:
            await auth_manager.authenticate_extension_request(mock_request, credentials)
        
        assert exc_info.value.status_code == 403
        assert "invalid" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_authenticate_no_credentials(self, auth_manager, mock_request):
        """Test authentication without credentials."""
        with pytest.raises(HTTPException) as exc_info:
            await auth_manager.authenticate_extension_request(mock_request, None)
        
        assert exc_info.value.status_code == 403
        assert "authentication required" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_authenticate_with_api_key(self, auth_manager, mock_request):
        """Test authentication with API key."""
        mock_request.headers = {"X-EXTENSION-API-KEY": "test-api-key"}

        user_context = await auth_manager.authenticate_extension_request(mock_request, None)

        assert user_context["user_id"] == "api-key-user"
        assert user_context["tenant_id"] == "system"
        assert user_context["roles"] == ["admin"]
        assert user_context["permissions"] == ["extension:*"]
        assert user_context["token_type"] == "api_key"

    @pytest.mark.asyncio
    async def test_authenticate_invalid_api_key(self, auth_manager, mock_request):
        """Test authentication with invalid API key."""
        mock_request.headers = {"X-EXTENSION-API-KEY": "invalid-key"}

        with pytest.raises(HTTPException) as exc_info:
            await auth_manager.authenticate_extension_request(mock_request, None)
        
        assert exc_info.value.status_code == 403
        assert "invalid api key" in exc_info.value.detail.lower()

    def test_development_mode_detection(self, auth_manager, mock_request):
        """Test development mode detection."""
        # Test with development header
        mock_request.headers = {"X-Development-Mode": "true"}
        assert auth_manager._is_development_mode(mock_request) == False  # dev_bypass_enabled is False

        # Test with development config
        auth_manager.dev_bypass_enabled = True
        assert auth_manager._is_development_mode(mock_request) == True

        # Test with localhost and skip auth header
        mock_request.headers = {"X-Skip-Auth": "dev"}
        mock_request.client.host = "127.0.0.1"
        assert auth_manager._is_development_mode(mock_request) == True

    @pytest.mark.asyncio
    async def test_development_mode_authentication(self, auth_config, mock_request):
        """Test authentication in development mode."""
        auth_config["dev_bypass_enabled"] = True
        auth_config["auth_mode"] = "development"
        auth_manager = ExtensionAuthManager(auth_config)

        user_context = await auth_manager.authenticate_extension_request(mock_request, None)

        assert user_context["user_id"] == "dev-user"
        assert user_context["tenant_id"] == "dev-tenant"
        assert user_context["roles"] == ["admin", "user"]
        assert user_context["token_type"] == "development"

    def test_has_permission_admin_user(self, auth_manager):
        """Test permission checking for admin users."""
        user_context = {
            "user_id": "admin-user",
            "roles": ["admin"],
            "permissions": []
        }

        assert auth_manager.has_permission(user_context, "extension:read") == True
        assert auth_manager.has_permission(user_context, "extension:write") == True
        assert auth_manager.has_permission(user_context, "any:permission") == True

    def test_has_permission_specific_permission(self, auth_manager):
        """Test permission checking for specific permissions."""
        user_context = {
            "user_id": "test-user",
            "roles": ["user"],
            "permissions": ["extension:read", "extension:background_tasks"]
        }

        assert auth_manager.has_permission(user_context, "read") == True
        assert auth_manager.has_permission(user_context, "background_tasks") == True
        assert auth_manager.has_permission(user_context, "write") == False

    def test_has_permission_wildcard(self, auth_manager):
        """Test permission checking with wildcard permissions."""
        user_context = {
            "user_id": "service-user",
            "roles": ["service"],
            "permissions": ["extension:*"]
        }

        assert auth_manager.has_permission(user_context, "read") == True
        assert auth_manager.has_permission(user_context, "write") == True
        assert auth_manager.has_permission(user_context, "admin") == True

    def test_has_permission_extension_specific(self, auth_manager):
        """Test permission checking for extension-specific permissions."""
        user_context = {
            "user_id": "test-user",
            "roles": ["user"],
            "permissions": ["extension:test-ext:read", "extension:test-ext:write"]
        }

        assert auth_manager.has_permission(user_context, "read", "test-ext") == True
        assert auth_manager.has_permission(user_context, "write", "test-ext") == True
        assert auth_manager.has_permission(user_context, "read", "other-ext") == False

    @pytest.mark.asyncio
    async def test_require_permission_dependency(self, auth_manager):
        """Test permission requirement dependency."""
        user_context = {
            "user_id": "test-user",
            "roles": ["user"],
            "permissions": ["extension:read"]
        }

        # Mock the authenticate_extension_request method
        auth_manager.authenticate_extension_request = AsyncMock(return_value=user_context)

        permission_checker = auth_manager.require_permission("read")
        result = await permission_checker()

        assert result == user_context

    @pytest.mark.asyncio
    async def test_require_permission_insufficient(self, auth_manager):
        """Test permission requirement with insufficient permissions."""
        user_context = {
            "user_id": "test-user",
            "roles": ["user"],
            "permissions": ["extension:read"]
        }

        # Mock the authenticate_extension_request method
        auth_manager.authenticate_extension_request = AsyncMock(return_value=user_context)

        permission_checker = auth_manager.require_permission("write")

        with pytest.raises(HTTPException) as exc_info:
            await permission_checker()
        
        assert exc_info.value.status_code == 403
        assert "insufficient permissions" in exc_info.value.detail.lower()

    def test_service_token_authentication(self, auth_manager, mock_request):
        """Test authentication with service token."""
        # Create service token
        token = auth_manager.create_service_token(
            service_name="test-service",
            permissions=["extension:background_tasks"]
        )

        # Decode and verify service token structure
        payload = jwt.decode(token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        
        assert payload["token_type"] == "service"
        assert payload["service_name"] == "test-service"
        assert payload["permissions"] == ["extension:background_tasks"]

    def test_token_expiration_times(self, auth_manager):
        """Test token expiration time configuration."""
        # Test access token expiration
        access_token = auth_manager.create_access_token("test-user")
        access_payload = jwt.decode(access_token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        
        # Should expire in 60 minutes (3600 seconds)
        exp_time = datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc)
        iat_time = datetime.fromtimestamp(access_payload["iat"], tz=timezone.utc)
        duration = exp_time - iat_time
        
        assert abs(duration.total_seconds() - 3600) < 60  # Allow 1 minute tolerance

        # Test service token expiration
        service_token = auth_manager.create_service_token("test-service")
        service_payload = jwt.decode(service_token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        
        # Should expire in 30 minutes (1800 seconds)
        exp_time = datetime.fromtimestamp(service_payload["exp"], tz=timezone.utc)
        iat_time = datetime.fromtimestamp(service_payload["iat"], tz=timezone.utc)
        duration = exp_time - iat_time
        
        assert abs(duration.total_seconds() - 1800) < 60  # Allow 1 minute tolerance

    def test_custom_expiration_times(self, auth_manager):
        """Test custom token expiration times."""
        custom_expiry = timedelta(minutes=15)
        
        token = auth_manager.create_access_token(
            "test-user",
            expires_delta=custom_expiry
        )
        
        payload = jwt.decode(token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat_time = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        duration = exp_time - iat_time
        
        assert abs(duration.total_seconds() - 900) < 60  # 15 minutes = 900 seconds

    @pytest.mark.asyncio
    async def test_authentication_disabled(self, auth_config, mock_request):
        """Test authentication when disabled."""
        auth_config["enabled"] = False
        auth_manager = ExtensionAuthManager(auth_config)

        user_context = await auth_manager.authenticate_extension_request(mock_request, None)

        assert user_context["user_id"] == "dev-user"
        assert user_context["token_type"] == "development"

    def test_create_dev_user_context(self, auth_manager):
        """Test development user context creation."""
        dev_context = auth_manager._create_dev_user_context()

        assert dev_context["user_id"] == "dev-user"
        assert dev_context["tenant_id"] == "dev-tenant"
        assert dev_context["roles"] == ["admin", "user"]
        assert dev_context["token_type"] == "development"
        assert "extension:read" in dev_context["permissions"]
        assert "extension:write" in dev_context["permissions"]


class TestExtensionAuthManagerEdgeCases:
    """Test edge cases and error conditions for ExtensionAuthManager."""

    @pytest.fixture
    def minimal_config(self):
        """Minimal configuration for testing edge cases."""
        return {
            "secret_key": "test-key",
            "enabled": True
        }

    @pytest.fixture
    def auth_manager(self, minimal_config):
        """Create authentication manager with minimal config."""
        return ExtensionAuthManager(minimal_config)

    def test_missing_user_id_in_token(self, auth_manager, mock_request):
        """Test token without user_id."""
        # Create token without user_id
        payload = {
            "tenant_id": "test-tenant",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc)
        }
        token = jwt.encode(payload, auth_manager.secret_key, algorithm=auth_manager.algorithm)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            auth_manager.authenticate_extension_request(mock_request, credentials)
        
        assert exc_info.value.status_code == 403

    def test_malformed_token(self, auth_manager, mock_request):
        """Test malformed JWT token."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not.a.jwt")

        with pytest.raises(HTTPException) as exc_info:
            auth_manager.authenticate_extension_request(mock_request, credentials)
        
        assert exc_info.value.status_code == 403

    def test_token_with_wrong_secret(self, auth_manager, mock_request):
        """Test token signed with wrong secret."""
        payload = {
            "user_id": "test-user",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc)
        }
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            auth_manager.authenticate_extension_request(mock_request, credentials)
        
        assert exc_info.value.status_code == 403

    def test_empty_permissions_list(self, auth_manager):
        """Test user context with empty permissions."""
        user_context = {
            "user_id": "test-user",
            "roles": [],
            "permissions": []
        }

        assert auth_manager.has_permission(user_context, "read") == False
        assert auth_manager.has_permission(user_context, "write") == False

    def test_none_permissions(self, auth_manager):
        """Test user context with None permissions."""
        user_context = {
            "user_id": "test-user",
            "roles": None,
            "permissions": None
        }

        assert auth_manager.has_permission(user_context, "read") == False

    @pytest.fixture
    def mock_request(self):
        """Create mock request for testing."""
        request = Mock(spec=Request)
        request.url.path = "/api/extensions/"
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.100"
        return request