"""
Unit tests for the Enhanced Session Validator.

Tests the improved session validation logic that prevents false
"invalid authorization header" errors and implements proper session
state management.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from fastapi import Request, HTTPException

from ai_karen_engine.auth.enhanced_session_validator import (
    EnhancedSessionValidator,
    ValidationResult,
    ValidationState,
    get_session_validator
)
from ai_karen_engine.auth.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    SessionExpiredError,
    SessionNotFoundError,
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


class TestEnhancedSessionValidator:
    """Test cases for EnhancedSessionValidator."""
    
    def test_initialization(self, validator):
        """Test validator initialization."""
        assert validator._token_manager is None
        assert validator._cookie_manager is None
        assert validator._auth_service is None
        assert validator._validation_states == {}
        assert validator._validation_cache_ttl == 30
    
    def test_generate_request_id(self, validator, mock_request):
        """Test request ID generation."""
        request_id = validator._generate_request_id(mock_request)
        assert isinstance(request_id, str)
        assert len(request_id) == 16  # MD5 hash truncated to 16 chars
        
        # Should generate same ID for same request
        request_id2 = validator._generate_request_id(mock_request)
        # Note: Due to timestamp, IDs will be different, but format should be same
        assert len(request_id2) == 16
    
    def test_get_validation_state(self, validator, mock_request):
        """Test validation state management."""
        state = validator._get_validation_state(mock_request)
        assert isinstance(state, ValidationState)
        assert state.request_id
        assert state.validation_attempts == set()
        assert state.last_validation_time is None
        assert state.cached_result is None
        
        # Should return same state for same request
        state2 = validator._get_validation_state(mock_request)
        assert state.request_id == state2.request_id
    
    def test_cache_validation_result(self, validator, mock_request):
        """Test validation result caching."""
        state = validator._get_validation_state(mock_request)
        result = ValidationResult(success=True, user_data={"user_id": "test"})
        
        validator._cache_validation_result(state, result)
        
        assert state.cached_result == result
        assert state.cache_expires_at is not None
        assert state.last_validation_time is not None
        assert validator._is_cached_result_valid(state)
    
    def test_cached_result_expiry(self, validator, mock_request):
        """Test cached result expiry."""
        state = validator._get_validation_state(mock_request)
        result = ValidationResult(success=True, user_data={"user_id": "test"})
        
        # Set expired cache
        validator._cache_validation_result(state, result)
        state.cache_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        
        assert not validator._is_cached_result_valid(state)
    
    def test_extract_request_metadata(self, validator, mock_request):
        """Test request metadata extraction."""
        metadata = validator._extract_request_metadata(mock_request)
        
        assert metadata["ip_address"] == "127.0.0.1"
        assert metadata["user_agent"] == "test-agent"
        assert metadata["path"] == "/api/test"
        assert "method" in metadata
    
    def test_extract_request_metadata_with_forwarded_for(self, validator, mock_request):
        """Test request metadata extraction with X-Forwarded-For header."""
        mock_request.headers = {
            "user-agent": "test-agent",
            "x-forwarded-for": "192.168.1.1, 10.0.0.1"
        }
        
        metadata = validator._extract_request_metadata(mock_request)
        assert metadata["ip_address"] == "192.168.1.1"
    
    @pytest.mark.asyncio
    async def test_validate_access_token_safely_success(self, validator, sample_token_payload):
        """Test successful access token validation."""
        with patch.object(validator, '_get_token_manager') as mock_get_token_manager:
            mock_token_manager = AsyncMock()
            mock_token_manager.validate_access_token.return_value = sample_token_payload
            mock_get_token_manager.return_value = mock_token_manager
            
            result = await validator._validate_access_token_safely(
                "valid-token", 
                {"ip_address": "127.0.0.1", "path": "/test"}
            )
            
            assert result.success
            assert result.user_data["user_id"] == "test-user-123"
            assert result.user_data["email"] == "test@example.com"
            assert result.validation_source == "access_token"
            assert result.error_type is None
    
    @pytest.mark.asyncio
    async def test_validate_access_token_safely_expired(self, validator):
        """Test access token validation with expired token."""
        with patch.object(validator, '_get_token_manager') as mock_get_token_manager:
            mock_token_manager = AsyncMock()
            mock_token_manager.validate_access_token.side_effect = TokenExpiredError()
            mock_get_token_manager.return_value = mock_token_manager
            
            result = await validator._validate_access_token_safely(
                "expired-token", 
                {"ip_address": "127.0.0.1", "path": "/test"}
            )
            
            assert not result.success
            assert result.error_type == "token_expired"
            assert result.should_retry_with_refresh
            assert "expired" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_validate_access_token_safely_invalid(self, validator):
        """Test access token validation with invalid token."""
        with patch.object(validator, '_get_token_manager') as mock_get_token_manager:
            mock_token_manager = AsyncMock()
            mock_token_manager.validate_access_token.side_effect = InvalidTokenError("Invalid token")
            mock_get_token_manager.return_value = mock_token_manager
            
            result = await validator._validate_access_token_safely(
                "invalid-token", 
                {"ip_address": "127.0.0.1", "path": "/test"}
            )
            
            assert not result.success
            assert result.error_type == "invalid_token"
            assert not result.should_retry_with_refresh
            assert "invalid" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_validate_session_token_safely_success(self, validator):
        """Test successful session token validation."""
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
        
        with patch.object(validator, '_get_auth_service') as mock_get_auth_service:
            mock_auth_service = AsyncMock()
            mock_auth_service.validate_session.return_value = mock_user_data
            mock_get_auth_service.return_value = mock_auth_service
            
            result = await validator._validate_session_token_safely(
                "valid-session-token",
                {"ip_address": "127.0.0.1", "user_agent": "test-agent", "path": "/test"}
            )
            
            assert result.success
            assert result.user_data["user_id"] == "test-user-123"
            assert result.validation_source == "session"
    
    @pytest.mark.asyncio
    async def test_validate_session_token_safely_expired(self, validator):
        """Test session token validation with expired session."""
        with patch.object(validator, '_get_auth_service') as mock_get_auth_service:
            mock_auth_service = AsyncMock()
            mock_auth_service.validate_session.side_effect = SessionExpiredError("Session expired")
            mock_get_auth_service.return_value = mock_auth_service
            
            result = await validator._validate_session_token_safely(
                "expired-session-token",
                {"ip_address": "127.0.0.1", "user_agent": "test-agent", "path": "/test"}
            )
            
            assert not result.success
            assert result.error_type == "session_expired"
    
    @pytest.mark.asyncio
    async def test_attempt_token_refresh_success(self, validator, mock_request):
        """Test successful token refresh."""
        refresh_payload = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "tenant_id": "default",
            "exp": int((datetime.now(timezone.utc) + timedelta(days=7)).timestamp()),
            "typ": "refresh",
        }
        
        with patch.object(validator, '_get_cookie_manager') as mock_get_cookie_manager, \
             patch.object(validator, '_get_token_manager') as mock_get_token_manager:
            
            mock_cookie_manager = MagicMock()
            mock_cookie_manager.get_refresh_token.return_value = "valid-refresh-token"
            mock_get_cookie_manager.return_value = mock_cookie_manager
            
            mock_token_manager = AsyncMock()
            mock_token_manager.validate_refresh_token.return_value = refresh_payload
            mock_get_token_manager.return_value = mock_token_manager
            
            result = await validator._attempt_token_refresh(
                mock_request,
                {"ip_address": "127.0.0.1", "path": "/test"}
            )
            
            assert result.success
            assert result.user_data["user_id"] == "test-user-123"
            assert result.validation_source == "refresh"
    
    @pytest.mark.asyncio
    async def test_attempt_token_refresh_no_token(self, validator, mock_request):
        """Test token refresh with no refresh token."""
        with patch.object(validator, '_get_cookie_manager') as mock_get_cookie_manager:
            mock_cookie_manager = MagicMock()
            mock_cookie_manager.get_refresh_token.return_value = None
            mock_get_cookie_manager.return_value = mock_cookie_manager
            
            result = await validator._attempt_token_refresh(
                mock_request,
                {"ip_address": "127.0.0.1", "path": "/test"}
            )
            
            assert not result.success
            assert result.error_type == "no_refresh_token"
    
    def test_create_clear_error_message(self, validator):
        """Test clear error message creation."""
        test_cases = [
            (ValidationResult(success=False, error_type="missing_auth_header"), 401),
            (ValidationResult(success=False, error_type="token_expired"), 401),
            (ValidationResult(success=False, error_type="invalid_token"), 401),
            (ValidationResult(success=False, error_type="session_expired"), 401),
            (ValidationResult(success=False, error_type="validation_error"), 500),
        ]
        
        for result, expected_status in test_cases:
            message, status_code = validator._create_clear_error_message(result)
            assert isinstance(message, str)
            assert len(message) > 0
            assert status_code == expected_status
    
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
    async def test_validate_request_authentication_missing_header(self, validator, mock_request):
        """Test request authentication with missing Authorization header."""
        mock_request.headers = {}
        
        with patch.object(validator, '_get_cookie_manager') as mock_get_cookie_manager:
            mock_cookie_manager = MagicMock()
            mock_cookie_manager.get_session_token.return_value = None
            mock_get_cookie_manager.return_value = mock_cookie_manager
            
            with pytest.raises(HTTPException) as exc_info:
                await validator.validate_request_authentication(mock_request)
            
            assert exc_info.value.status_code == 401
            assert "Authentication required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_validate_request_authentication_malformed_header(self, validator, mock_request):
        """Test request authentication with malformed Authorization header."""
        mock_request.headers = {"Authorization": "InvalidFormat token"}
        
        with pytest.raises(HTTPException) as exc_info:
            await validator.validate_request_authentication(mock_request)
        
        assert exc_info.value.status_code == 401
        assert "Invalid authorization header format" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_validate_request_authentication_with_session_fallback(self, validator, mock_request, sample_user_data):
        """Test request authentication with session fallback."""
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
    async def test_validate_request_authentication_with_refresh(self, validator, mock_request, sample_user_data):
        """Test request authentication with token refresh."""
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
    async def test_validate_request_authentication_cached_result(self, validator, mock_request, sample_user_data):
        """Test request authentication with cached result."""
        mock_request.headers = {"Authorization": "Bearer valid-token"}
        
        # First call
        with patch.object(validator, '_validate_access_token_safely') as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=True,
                user_data=sample_user_data,
                validation_source="access_token"
            )
            
            result1 = await validator.validate_request_authentication(mock_request)
            assert result1 == sample_user_data
            assert mock_validate.call_count == 1
        
        # Second call should use cached result
        with patch.object(validator, '_validate_access_token_safely') as mock_validate:
            result2 = await validator.validate_request_authentication(mock_request)
            assert result2 == sample_user_data
            assert mock_validate.call_count == 0  # Should not be called due to cache
    
    @pytest.mark.asyncio
    async def test_validate_optional_authentication_success(self, validator, mock_request, sample_user_data):
        """Test optional authentication with valid token."""
        mock_request.headers = {"Authorization": "Bearer valid-token"}
        
        with patch.object(validator, 'validate_request_authentication') as mock_validate:
            mock_validate.return_value = sample_user_data
            
            result = await validator.validate_optional_authentication(mock_request)
            
            assert result == sample_user_data
    
    @pytest.mark.asyncio
    async def test_validate_optional_authentication_missing_auth(self, validator, mock_request):
        """Test optional authentication with missing auth."""
        mock_request.headers = {}
        
        with patch.object(validator, 'validate_request_authentication') as mock_validate:
            from fastapi import HTTPException
            mock_validate.side_effect = HTTPException(
                status_code=401, 
                detail="Authentication required. Please provide a valid access token"
            )
            
            result = await validator.validate_optional_authentication(mock_request)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_optional_authentication_invalid_token(self, validator, mock_request):
        """Test optional authentication with invalid token."""
        mock_request.headers = {"Authorization": "Bearer invalid-token"}
        
        with patch.object(validator, 'validate_request_authentication') as mock_validate:
            from fastapi import HTTPException
            mock_validate.side_effect = HTTPException(
                status_code=401, 
                detail="Invalid access token"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await validator.validate_optional_authentication(mock_request)
            
            assert exc_info.value.status_code == 401
            assert "Invalid access token" in exc_info.value.detail
    
    def test_get_validation_stats(self, validator, mock_request):
        """Test validation statistics."""
        # Create some validation states
        state1 = validator._get_validation_state(mock_request)
        validator._cache_validation_result(
            state1, 
            ValidationResult(success=True, user_data={"user_id": "test"})
        )
        
        stats = validator.get_validation_stats()
        
        assert stats["active_validation_states"] >= 1
        assert stats["cached_validation_results"] >= 1
        assert stats["cache_ttl_seconds"] == 30
        assert "cleanup_interval_seconds" in stats
    
    def test_cleanup_old_states(self, validator, mock_request):
        """Test cleanup of old validation states."""
        # Create a state and mark it as old
        state = validator._get_validation_state(mock_request)
        state.last_validation_time = datetime.now(timezone.utc) - timedelta(minutes=15)
        
        initial_count = len(validator._validation_states)
        
        # Force cleanup
        validator._last_cleanup = 0  # Force cleanup to run
        validator._cleanup_old_states()
        
        # Should have cleaned up the old state
        assert len(validator._validation_states) < initial_count


class TestGlobalSessionValidator:
    """Test the global session validator instance."""
    
    def test_get_session_validator_singleton(self):
        """Test that get_session_validator returns the same instance."""
        validator1 = get_session_validator()
        validator2 = get_session_validator()
        
        assert validator1 is validator2
        assert isinstance(validator1, EnhancedSessionValidator)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])