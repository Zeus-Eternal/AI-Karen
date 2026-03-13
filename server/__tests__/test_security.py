"""
Tests for security functionality.

Tests authentication, authorization, JWT tokens, and security configuration.
"""

import pytest
import jwt
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock

from server.security import (
    ExtensionAuthManager,
    pwd_context,
    api_key_header,
    oauth2_scheme,
    get_ssl_context,
    get_extension_auth_manager,
    validate_environment_security
)


class TestExtensionAuthManager:
    """Test extension authentication manager functionality."""
    
    @pytest.fixture
    def auth_manager(self):
        """Create a test auth manager."""
        config = {
            "secret_key": "test-secret-key",
            "algorithm": "HS256",
            "enabled": True,
            "auth_mode": "hybrid",
            "dev_bypass_enabled": True,
            "require_https": False,
            "access_token_expire_minutes": 60,
            "service_token_expire_minutes": 30
        }
        return ExtensionAuthManager(config)
    
    def test_initialization(self, auth_manager):
        """Test auth manager initialization."""
        assert auth_manager.secret_key == "test-secret-key"
        assert auth_manager.algorithm == "HS256"
        assert auth_manager.enabled is True
        assert auth_manager.auth_mode == "hybrid"
        assert auth_manager.dev_bypass_enabled is True
        assert auth_manager.require_https is False
        assert auth_manager.token_manager is None  # Not initialized yet
    
    def test_create_access_token(self, auth_manager):
        """Test JWT access token creation."""
        with patch('server.security.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 1, tzinfo=timezone.utc)
            mock_datetime.utcnow.return_value = datetime(2023, 1, 1, tzinfo=timezone.utc)
            
            token = auth_manager.create_access_token(
                user_id="test-user",
                tenant_id="test-tenant",
                roles=["user"],
                permissions=["extension:read"],
                expires_delta=timedelta(hours=1)
            )
            
            # Decode token to verify contents
            payload = jwt.decode(token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
            
            assert payload["user_id"] == "test-user"
            assert payload["tenant_id"] == "test-tenant"
            assert payload["roles"] == ["user"]
            assert payload["permissions"] == ["extension:read"]
            assert payload["token_type"] == "access"
            assert payload["iss"] == "kari-extension-system"
            assert "exp" in payload
    
    def test_create_service_token(self, auth_manager):
        """Test JWT service token creation."""
        with patch('server.security.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 1, tzinfo=timezone.utc)
            mock_datetime.utcnow.return_value = datetime(2023, 1, 1, tzinfo=timezone.utc)
            
            token = auth_manager.create_service_token(
                service_name="test-service",
                permissions=["extension:background_tasks"],
                expires_delta=timedelta(minutes=30)
            )
            
            # Decode token to verify contents
            payload = jwt.decode(token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
            
            assert payload["service_name"] == "test-service"
            assert payload["permissions"] == ["extension:background_tasks"]
            assert payload["token_type"] == "service"
            assert payload["iss"] == "kari-extension-system"
    
    def test_create_background_task_token(self, auth_manager):
        """Test background task token creation."""
        with patch('server.security.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 1, tzinfo=timezone.utc)
            mock_datetime.utcnow.return_value = datetime(2023, 1, 1, tzinfo=timezone.utc)
            
            token = auth_manager.create_background_task_token(
                task_name="test-task",
                service_name="test-service",
                permissions=["extension:execute"],
                expires_delta=timedelta(minutes=15)
            )
            
            # Decode token to verify contents
            payload = jwt.decode(token, auth_manager.secret_key, algorithms=[auth_manager.algorithm])
            
            assert payload["task_name"] == "test-task"
            assert payload["service_name"] == "test-service"
            assert payload["permissions"] == ["extension:execute", "extension:background_tasks"]
            assert payload["token_type"] == "service"
    
    @pytest.mark.asyncio
    async def test_generate_user_token_pair(self, auth_manager):
        """Test user token pair generation."""
        with patch('server.security.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 1, tzinfo=timezone.utc)
            mock_datetime.utcnow.return_value = datetime(2023, 1, 1, tzinfo=timezone.utc)
            
            # Mock token manager
            mock_token_manager = Mock()
            mock_token_manager.generate_user_tokens = AsyncMock(return_value={
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "token_type": "bearer",
                "expires_in": 3600
            })
            
            with patch.object(auth_manager, 'token_manager', mock_token_manager):
                tokens = await auth_manager.generate_user_token_pair(
                    user_id="test-user",
                    tenant_id="test-tenant",
                    roles=["user"],
                    permissions=["extension:read"]
                )
            
            assert tokens["access_token"] == "test-access-token"
            assert tokens["refresh_token"] == "test-refresh-token"
            assert tokens["token_type"] == "bearer"
            assert tokens["expires_in"] == 3600
    
    @pytest.mark.asyncio
    async def test_refresh_user_token(self, auth_manager):
        """Test user token refresh."""
        mock_token_manager = Mock()
        mock_token_manager.refresh_access_token = AsyncMock(return_value={
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "token_type": "bearer",
            "expires_in": 3600
        })
        
        with patch.object(auth_manager, 'token_manager', mock_token_manager):
            tokens = await auth_manager.refresh_user_token(
                refresh_token="old-refresh-token",
                new_permissions=["extension:write"]
            )
            
            assert tokens["access_token"] == "new-access-token"
            assert tokens["refresh_token"] == "new-refresh-token"
            assert tokens["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_revoke_token(self, auth_manager):
        """Test token revocation."""
        mock_token_manager = Mock()
        mock_token_manager.revoke_token = AsyncMock(return_value=True)
        
        with patch.object(auth_manager, 'token_manager', mock_token_manager):
            result = await auth_manager.revoke_token("test-token")
            
            assert result is True
            mock_token_manager.revoke_token.assert_called_once_with("test-token")
    
    @pytest.mark.asyncio
    async def test_authenticate_extension_request(self, auth_manager):
        """Test extension request authentication."""
        from fastapi import Request, HTTPException
        from fastapi.security import HTTPAuthorizationCredentials
        
        # Create a mock request
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/extensions/test"
        mock_request.headers = {}
        mock_request.client.host = "localhost"
        
        # Test with disabled authentication
        auth_manager.enabled = False
        user_context = await auth_manager.authenticate_extension_request(mock_request)
        assert user_context["user_id"] == "dev-user"
        assert user_context["token_type"] == "development"
        
        # Test with API key
        auth_manager.enabled = True
        mock_request.headers = {"X-EXTENSION-API-KEY": "test-api-key"}
        
        with patch.object(auth_manager, '_authenticate_with_api_key') as mock_auth:
            user_context = await auth_manager.authenticate_extension_request(mock_request)
            mock_auth.assert_called_once_with("test-api-key")
    
    def test_has_permission(self, auth_manager):
        """Test permission checking."""
        user_context = {
            "user_id": "test-user",
            "roles": ["user"],
            "permissions": ["extension:read"]
        }
        
        # Test with matching permission
        assert auth_manager.has_permission(user_context, "extension:read") is True
        
        # Test with non-matching permission
        assert auth_manager.has_permission(user_context, "extension:write") is False
        
        # Test with admin role
        admin_context = {
            "user_id": "admin-user",
            "roles": ["admin"],
            "permissions": []
        }
        assert auth_manager.has_permission(admin_context, "extension:write") is True
    
    def test_development_mode_detection(self, auth_manager):
        """Test development mode detection."""
        from fastapi import Request
        
        # Test with auth mode set to development
        auth_manager.auth_mode = "development"
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        
        assert auth_manager._is_development_mode(mock_request) is True
        
        # Test with development header
        auth_manager.auth_mode = "production"
        mock_request.headers = {"X-Development-Mode": "true"}
        
        assert auth_manager._is_development_mode(mock_request) is True
        
        # Test with localhost
        auth_manager.auth_mode = "production"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"X-Skip-Auth": "dev"}
        
        assert auth_manager._is_development_mode(mock_request) is True


class TestPasswordContext:
    """Test password context and hashing."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "test-password"
        hashed = pwd_context.hash(password)
        
        # Verify hash
        assert pwd_context.verify(password, hashed) is True
        assert pwd_context.verify("wrong-password", hashed) is False
    
    def test_password_salt_generation(self):
        """Test salt generation for password hashing."""
        password = "test-password"
        hashed1 = pwd_context.hash(password)
        hashed2 = pwd_context.hash(password)
        
        # Hashes should be different due to salt
        assert hashed1 != hashed2


class TestJWTTokenHandling:
    """Test JWT token creation and validation."""
    
    @pytest.fixture
    def jwt_config(self):
        """Test JWT configuration."""
        return {
            "secret_key": "test-jwt-secret-key-that-is-long-enough",
            "algorithm": "HS256"
        }
    
    def test_jwt_encoding(self, jwt_config):
        """Test JWT token encoding."""
        payload = {
            "user_id": "test-user",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc)
        }
        
        token = jwt.encode(payload, jwt_config["secret_key"], algorithm=jwt_config["algorithm"])
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_jwt_decoding(self, jwt_config):
        """Test JWT token decoding."""
        payload = {
            "user_id": "test-user",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc)
        }
        
        token = jwt.encode(payload, jwt_config["secret_key"], algorithm=jwt_config["algorithm"])
        decoded = jwt.decode(token, jwt_config["secret_key"], algorithms=[jwt_config["algorithm"]])
        
        assert decoded["user_id"] == payload["user_id"]
        assert "exp" in decoded
        assert "iat" in decoded
    
    def test_jwt_expired_token(self, jwt_config):
        """Test JWT expired token handling."""
        # Create an expired token
        expired_payload = {
            "user_id": "test-user",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired 1 hour ago
            "iat": datetime.now(timezone.utc) - timedelta(hours=2)
        }
        
        expired_token = jwt.encode(expired_payload, jwt_config["secret_key"], algorithm=jwt_config["algorithm"])
        
        # Should raise expired signature error
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(expired_token, jwt_config["secret_key"], algorithms=[jwt_config["algorithm"]])
    
    def test_jwt_invalid_token(self, jwt_config):
        """Test JWT invalid token handling."""
        # Create a token with different secret
        payload = {"user_id": "test-user"}
        token = jwt.encode(payload, "different-secret", algorithm="HS256")
        
        # Should raise invalid signature error
        with pytest.raises(jwt.InvalidTokenError):
            jwt.decode(token, jwt_config["secret_key"], algorithms=[jwt_config["algorithm"]])


class TestEnvironmentSecurityValidation:
    """Test environment security validation."""
    
    def test_validate_environment_security_success(self):
        """Test successful environment security validation."""
        with patch.dict('os.environ', {
            'SECRET_KEY': 'proper-secret-key-that-is-long-enough',
            'DATABASE_URL': 'postgresql://user:pass@localhost:5432/testdb',
            'AUTH_SECRET_KEY': 'another-proper-secret-key-that-is-long-enough',
            'EXTENSION_SECRET_KEY': 'extension-secret-key-that-is-long-enough'
        }):
            result = validate_environment_security()
            
            assert result['overall_status'] == 'secure'
            assert len(result['secrets_validation']) == 4
            assert all(validation['valid'] for validation in result['secrets_validation'].values())
    
    def test_validate_environment_security_missing_secrets(self):
        """Test environment security validation with missing secrets."""
        with patch.dict('os.environ', {
            'SECRET_KEY': '',
            'DATABASE_URL': 'postgresql://user:pass@localhost:5432/testdb',
            'AUTH_SECRET_KEY': 'another-proper-secret-key-that-is-long-enough',
            'EXTENSION_SECRET_KEY': 'extension-secret-key-that-is-long-enough'
        }):
            result = validate_environment_security()
            
            assert result['overall_status'] == 'insecure'
            assert 'SECRET_KEY' in result['secrets_validation']
            assert not result['secrets_validation']['SECRET_KEY']['valid']
    
    def test_validate_environment_security_production_requirements(self):
        """Test production environment security requirements."""
        with patch.dict('os.environ', {
            'SECRET_KEY': 'proper-secret-key-that-is-long-enough',
            'DATABASE_URL': 'postgresql://user:pass@localhost:5432/testdb',
            'AUTH_SECRET_KEY': 'another-proper-secret-key-that-is-long-enough',
            'EXTENSION_SECRET_KEY': 'extension-secret-key-that-is-long-enough',
            'ENVIRONMENT': 'production',
            'DEBUG': 'true'  # Debug should not be enabled in production
        }):
            result = validate_environment_security()
            
            assert result['overall_status'] == 'insecure'
            assert 'DEBUG mode enabled in production environment' in result['errors']
    
    def test_validate_environment_security_ssl_requirements(self):
        """Test SSL requirements for production."""
        with patch.dict('os.environ', {
            'SECRET_KEY': 'proper-secret-key-that-is-long-enough',
            'DATABASE_URL': 'postgresql://user:pass@localhost:5432/testdb',
            'AUTH_SECRET_KEY': 'another-proper-secret-key-that-is-long-enough',
            'EXTENSION_SECRET_KEY': 'extension-secret-key-that-is-long-enough',
            'ENVIRONMENT': 'production',
            # Missing SSL certificate paths
        }):
            result = validate_environment_security()
            
            assert result['overall_status'] == 'degraded'
            assert 'SSL certificates not configured for production' in result['warnings']


class TestGlobalAuthManager:
    """Test global extension authentication manager."""
    
    def test_get_extension_auth_manager(self):
        """Test global auth manager retrieval."""
        # Clear global manager first
        import server.security
        server.security.extension_auth_manager = None
        
        with patch('server.security.Settings') as mock_settings:
            mock_settings.return_value.get_extension_auth_config.return_value = {
                "secret_key": "test-secret-key",
                "algorithm": "HS256",
                "enabled": True
            }
            
            manager = get_extension_auth_manager()
            
            assert manager is not None
            assert manager.secret_key == "test-secret-key"
            assert manager.enabled is True
    
    def test_auth_manager_singleton(self):
        """Test that auth manager is a singleton."""
        import server.security
        
        # Clear global manager
        server.security.extension_auth_manager = None
        
        manager1 = get_extension_auth_manager()
        manager2 = get_extension_auth_manager()
        
        assert manager1 is manager2  # Same instance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])