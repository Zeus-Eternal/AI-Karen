"""
Simple tests for enhanced authentication session validation.

Tests the enhanced session validator directly without FastAPI dependencies.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from fastapi import Request, HTTPException

from ai_karen_engine.auth.enhanced_session_validator import (
    EnhancedSessionValidator,
    ValidationResult,
    get_session_validator
)
from ai_karen_engine.auth.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    SessionExpiredError,
)
from ai_karen_engine.auth.models import UserData


@pytest.fixture
def validator():
    """Create enhanced session validator instance."""
    return EnhancedSessionValidator()


@pytest.fixture
def mock_request():
    """Create mock FastAPI request."""
    request = MagicMock(spec=Request)
    request.headers = {"user-agent": "test-agent"}
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    request.url = MagicMock()
    request.url.path = "/api/test"
    request.method = "GET"
    return request


@pytest.fixture
def sample_user_data():
    """Create sample user data."""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "full_name": "Test User",
        "roles": ["user"],
        "tenant_id": "default",
        "preferences": {},
        "two_factor_enabled": False,
        "is_verified": True,
    }


@pytest.fixture
def sample_token_payload():
    """Create sample token payload."""
    return {
        "sub": "test-user-123",
        "email": "test@example.com",
        "full_name": "Test User",
        "roles": ["user"],
        "tenant_id": "default",
        "is_verified": True,
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=15)).timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "jti": "test-jti-123",
        "typ": "access",
    }


class TestEnhancedSessionValidationCore:
    """Test core enhanced session validation functionality."""
    
    @pytest.mark.asyncio
    async def test_validate_request_authentication_success(self, validator, mock_request, sample_user_data):
        """Test successful request authentication."""
        mock_request.headers = {"Authorization": "Bearer valid-token"}
        
        with patch.object(validator, '_validate_access_token_safely') as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=True,
                user_data=sample_user_data,
                validation_source="access_token"
            )
            
            result = await validator.validate_request_authentication(mock_request)
            
            assert result == sample_user_data
    
    @pytest.mark.asyncio
    async def test_validate_request_authentication_missing_header_clear_message(self, validator, mock_request):
        """Test request authentication with missing Authorization header returns clear message."""
        mock_request.headers = {}
        
        with patch.object(validator, '_get_cookie_manager') as mock_get_cookie_manager:
            mock_cookie_manager = MagicMock()
            mock_cookie_manager.get_session_token.return_value = None
            mock_get_cookie_manager.return_value = mock_cookie_manager
            
            with pytest.raises(HTTPException) as exc_info:
                await validator.validate_request_authentication(mock_request)
            
            assert exc_info.value.status_code == 401
            assert "Authentication required" in exc_info.value.detail
            # Ensure we don't get the old generic error message
            assert "Missing or invalid authorization header" not in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_validate_request_authentication_malformed_header_clear_message(self, validator, mock_request):
        """Test request authentication with malformed Authorization header returns clear message."""
        mock_request.headers = {"Authorization": "InvalidFormat token"}
        
        with pytest.raises(HTTPException) as exc_info:
            await validator.validate_request_authentication(mock_request)
        
        assert exc_info.value.status_code == 401
        assert "Invalid authorization header format" in exc_info.value.detail
        assert "Expected 'Bearer <token>'" in exc_info.value.detail
        # Ensure we don't get the old generic error message
        assert "Missing or invalid authorization header" not in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_validate_request_authentication_expired_token_clear_message(self, validator, mock_request):
        """Test request authentication with expired token returns clear message."""
        mock_request.headers = {"Authorization": "Bearer expired-token"}
        
        with patch.object(validator, '_validate_access_token_safely') as mock_validate, \
             patch.object(validator, '_attempt_token_refresh') as mock_refresh:
            
            # Token validation fails with expired token
            mock_validate.return_value = ValidationResult(
                success=False,
                error_type="token_expired",
                should_retry_with_refresh=True
            )
            
            # Refresh also fails
            mock_refresh.return_value = ValidationResult(
                success=False,
                error_type="no_refresh_token"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await validator.validate_request_authentication(mock_request)
            
            assert exc_info.value.status_code == 401
            # The error message should be about the expired token, not the refresh failure
            # because the first validation result is cached
            assert ("access token has expired" in exc_info.value.detail.lower() or 
                    "no refresh token available" in exc_info.value.detail.lower())
            # Ensure we don't get the old generic error message
            assert "Missing or invalid authorization header" not in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_validate_request_authentication_invalid_token_clear_message(self, validator, mock_request):
        """Test request authentication with invalid token returns clear message."""
        mock_request.headers = {"Authorization": "Bearer invalid-token"}
        
        with patch.object(validator, '_validate_access_token_safely') as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=False,
                error_type="invalid_token",
                error_message="Invalid access token: malformed"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await validator.validate_request_authentication(mock_request)
            
            assert exc_info.value.status_code == 401
            assert "Invalid access token" in exc_info.value.detail
            # Ensure we don't get the old generic error message
            assert "Missing or invalid authorization header" not in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_validate_request_authentication_with_session_fallback(self, validator, mock_request, sample_user_data):
        """Test request authentication with session fallback when no Authorization header."""
        mock_request.headers = {}
        
        with patch.object(validator, '_get_cookie_manager') as mock_get_cookie_manager, \
             patch.object(validator, '_validate_session_token_safely') as mock_validate_session:
            
            mock_cookie_manager = MagicMock()
            mock_cookie_manager.get_session_token.return_value = "valid-session-token"
            mock_get_cookie_manager.return_value = mock_cookie_manager
            
            mock_validate_session.return_value = ValidationResult(
                success=True,
                user_data=sample_user_data,
                validation_source="session"
            )
            
            result = await validator.validate_request_authentication(mock_request)
            
            assert result == sample_user_data
    
    @pytest.mark.asyncio
    async def test_validate_request_authentication_with_token_refresh(self, validator, mock_request, sample_user_data):
        """Test request authentication with successful token refresh."""
        mock_request.headers = {"Authorization": "Bearer expired-token"}
        
        with patch.object(validator, '_validate_access_token_safely') as mock_validate_token, \
             patch.object(validator, '_attempt_token_refresh') as mock_refresh:
            
            # First validation fails with expired token
            mock_validate_token.return_value = ValidationResult(
                success=False,
                error_type="token_expired",
                should_retry_with_refresh=True
            )
            
            # Refresh succeeds
            mock_refresh.return_value = ValidationResult(
                success=True,
                user_data=sample_user_data,
                validation_source="refresh"
            )
            
            result = await validator.validate_request_authentication(mock_request)
            
            assert result == sample_user_data
    
    @pytest.mark.asyncio
    async def test_validate_request_authentication_prevents_duplicate_validation(self, validator, mock_request, sample_user_data):
        """Test that validation results are cached to prevent duplicate validation attempts."""
        mock_request.headers = {"Authorization": "Bearer valid-token"}
        
        with patch.object(validator, '_validate_access_token_safely') as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=True,
                user_data=sample_user_data,
                validation_source="access_token"
            )
            
            # First call
            result1 = await validator.validate_request_authentication(mock_request)
            assert result1 == sample_user_data
            assert mock_validate.call_count == 1
            
            # Second call should use cached result
            result2 = await validator.validate_request_authentication(mock_request)
            assert result2 == sample_user_data
            # Should still be 1 due to caching
            assert mock_validate.call_count == 1
    
    @pytest.mark.asyncio
    async def test_validate_optional_authentication_missing_auth_returns_none(self, validator, mock_request):
        """Test optional authentication returns None for missing auth instead of raising exception."""
        mock_request.headers = {}
        
        with patch.object(validator, '_get_cookie_manager') as mock_get_cookie_manager:
            mock_cookie_manager = MagicMock()
            mock_cookie_manager.get_session_token.return_value = None
            mock_get_cookie_manager.return_value = mock_cookie_manager
            
            result = await validator.validate_optional_authentication(mock_request)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_optional_authentication_invalid_token_raises_exception(self, validator, mock_request):
        """Test optional authentication raises exception for invalid token (not missing auth)."""
        mock_request.headers = {"Authorization": "Bearer invalid-token"}
        
        with patch.object(validator, '_validate_access_token_safely') as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=False,
                error_type="invalid_token",
                error_message="Invalid access token"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await validator.validate_optional_authentication(mock_request)
            
            assert exc_info.value.status_code == 401
            assert "Invalid access token" in exc_info.value.detail
    
    def test_clear_error_messages_for_different_scenarios(self, validator):
        """Test that different authentication failure scenarios have clear, distinct error messages."""
        test_cases = [
            ("missing_auth_header", "Authentication required"),
            ("malformed_auth_header", "Invalid authorization header format"),
            ("token_expired", "Access token has expired"),
            ("invalid_token", "Invalid access token"),
            ("session_expired", "Your session has expired"),
            ("session_not_found", "Session not found"),
            ("no_refresh_token", "no refresh token available"),
            ("refresh_token_expired", "Refresh token has expired"),
            ("invalid_refresh_token", "Invalid refresh token"),
            ("validation_error", "Authentication validation failed"),
            ("refresh_error", "Token refresh failed"),
        ]
        
        for error_type, expected_message_part in test_cases:
            result = ValidationResult(success=False, error_type=error_type)
            message, status_code = validator._create_clear_error_message(result)
            
            assert expected_message_part in message
            assert status_code in [401, 500]
            # Ensure we don't get the old generic error message
            assert "Missing or invalid authorization header" not in message
    
    def test_validation_state_management(self, validator, mock_request):
        """Test that validation state is properly managed to prevent memory leaks."""
        # Create multiple validation states
        for i in range(5):
            mock_request.client.host = f"127.0.0.{i}"
            state = validator._get_validation_state(mock_request)
            assert state.request_id
        
        # Check stats
        stats = validator.get_validation_stats()
        assert stats["active_validation_states"] >= 5
        
        # Force cleanup of old states
        validator._last_cleanup = 0  # Force cleanup to run
        validator._cleanup_old_states()
        
        # Stats should reflect cleanup
        new_stats = validator.get_validation_stats()
        assert "active_validation_states" in new_stats
        assert "cached_validation_results" in new_stats


class TestSessionValidatorIntegration:
    """Test session validator integration with auth components."""
    
    @pytest.mark.asyncio
    async def test_token_manager_integration(self, validator, mock_request, sample_token_payload):
        """Test integration with token manager."""
        mock_request.headers = {"Authorization": "Bearer valid-token"}
        
        with patch.object(validator, '_get_token_manager') as mock_get_token_manager:
            mock_token_manager = AsyncMock()
            mock_token_manager.validate_access_token.return_value = sample_token_payload
            mock_get_token_manager.return_value = mock_token_manager
            
            result = await validator.validate_request_authentication(mock_request)
            
            assert result["user_id"] == "test-user-123"
            assert result["email"] == "test@example.com"
            mock_token_manager.validate_access_token.assert_called_once_with("valid-token")
    
    @pytest.mark.asyncio
    async def test_auth_service_integration(self, validator, mock_request):
        """Test integration with auth service for session validation."""
        mock_request.headers = {}
        
        mock_user_data = UserData(
            user_id="test-user-123",
            email="test@example.com",
            full_name="Test User",
            tenant_id="default",
            roles=["user"],
            is_verified=True,
            is_active=True,
            preferences={}
        )
        
        with patch.object(validator, '_get_cookie_manager') as mock_get_cookie_manager, \
             patch.object(validator, '_get_auth_service') as mock_get_auth_service:
            
            mock_cookie_manager = MagicMock()
            mock_cookie_manager.get_session_token.return_value = "valid-session-token"
            mock_get_cookie_manager.return_value = mock_cookie_manager
            
            mock_auth_service = AsyncMock()
            mock_auth_service.validate_session.return_value = mock_user_data
            mock_get_auth_service.return_value = mock_auth_service
            
            result = await validator.validate_request_authentication(mock_request)
            
            assert result["user_id"] == "test-user-123"
            assert result["email"] == "test@example.com"
            mock_auth_service.validate_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cookie_manager_integration(self, validator, mock_request):
        """Test integration with cookie manager for refresh tokens."""
        mock_request.headers = {"Authorization": "Bearer expired-token"}
        
        refresh_payload = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "tenant_id": "default",
            "exp": int((datetime.now(timezone.utc) + timedelta(days=7)).timestamp()),
            "typ": "refresh",
        }
        
        with patch.object(validator, '_validate_access_token_safely') as mock_validate_token, \
             patch.object(validator, '_get_cookie_manager') as mock_get_cookie_manager, \
             patch.object(validator, '_get_token_manager') as mock_get_token_manager:
            
            # Access token validation fails
            mock_validate_token.return_value = ValidationResult(
                success=False,
                error_type="token_expired",
                should_retry_with_refresh=True
            )
            
            # Cookie manager returns refresh token
            mock_cookie_manager = MagicMock()
            mock_cookie_manager.get_refresh_token.return_value = "valid-refresh-token"
            mock_get_cookie_manager.return_value = mock_cookie_manager
            
            # Token manager validates refresh token
            mock_token_manager = AsyncMock()
            mock_token_manager.validate_refresh_token.return_value = refresh_payload
            mock_get_token_manager.return_value = mock_token_manager
            
            result = await validator.validate_request_authentication(mock_request)
            
            assert result["user_id"] == "test-user-123"
            assert result["email"] == "test@example.com"
            mock_cookie_manager.get_refresh_token.assert_called_once()
            mock_token_manager.validate_refresh_token.assert_called_once_with("valid-refresh-token")


class TestGlobalSessionValidator:
    """Test the global session validator instance."""
    
    def test_get_session_validator_singleton(self):
        """Test that get_session_validator returns the same instance."""
        validator1 = get_session_validator()
        validator2 = get_session_validator()
        
        assert validator1 is validator2
        assert isinstance(validator1, EnhancedSessionValidator)
    
    def test_global_validator_functionality(self):
        """Test that global validator has expected functionality."""
        validator = get_session_validator()
        
        # Test basic functionality
        stats = validator.get_validation_stats()
        assert isinstance(stats, dict)
        assert "active_validation_states" in stats
        assert "cached_validation_results" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])