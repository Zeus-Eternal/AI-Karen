"""
Simple Integration Tests for Middleware

Tests the basic functionality of the middleware integration without
relying on complex mocking or FastAPI stub behavior.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta

from ai_karen_engine.middleware.session_persistence import SessionPersistenceMiddleware
from ai_karen_engine.middleware.intelligent_error_handler import IntelligentErrorHandlerMiddleware
from ai_karen_engine.auth.exceptions import TokenExpiredError, InvalidTokenError


class TestSessionPersistenceMiddleware:
    """Test session persistence middleware core functionality."""
    
    def test_should_skip_auth_public_paths(self):
        """Test that public paths are correctly identified."""
        middleware = SessionPersistenceMiddleware(None)
        
        # Mock request objects
        class MockRequest:
            def __init__(self, path):
                self.url = Mock()
                self.url.path = path
        
        # Test public paths
        assert middleware._should_skip_auth(MockRequest("/api/auth/login"))
        assert middleware._should_skip_auth(MockRequest("/api/health"))
        assert middleware._should_skip_auth(MockRequest("/docs"))
        assert middleware._should_skip_auth(MockRequest("/openapi.json"))
        
        # Test protected paths
        assert not middleware._should_skip_auth(MockRequest("/api/test/protected"))
        assert not middleware._should_skip_auth(MockRequest("/api/users"))
    
    def test_should_skip_session_persistence(self):
        """Test that auth routes skip session persistence."""
        middleware = SessionPersistenceMiddleware(None)
        
        class MockRequest:
            def __init__(self, path):
                self.url = Mock()
                self.url.path = path
        
        # Test auth routes that should skip session persistence
        assert middleware._should_skip_session_persistence(MockRequest("/api/auth/login"))
        assert middleware._should_skip_session_persistence(MockRequest("/api/auth/register"))
        assert middleware._should_skip_session_persistence(MockRequest("/api/auth/refresh"))
        
        # Test routes that should use session persistence
        assert not middleware._should_skip_session_persistence(MockRequest("/api/test/protected"))
        assert not middleware._should_skip_session_persistence(MockRequest("/api/users"))
    
    def test_extract_request_metadata(self):
        """Test request metadata extraction."""
        middleware = SessionPersistenceMiddleware(None)
        
        class MockRequest:
            def __init__(self, path="/test", method="GET", headers=None, client_host="127.0.0.1"):
                self.url = Mock()
                self.url.path = path
                self.method = method
                self.headers = headers or {}
                self.client = Mock()
                self.client.host = client_host
        
        # Test basic metadata extraction
        request = MockRequest(
            path="/api/test",
            method="POST",
            headers={"user-agent": "test-client/1.0"},
            client_host="192.168.1.100"
        )
        
        import asyncio
        metadata = asyncio.run(middleware._extract_request_metadata(request))
        
        assert metadata["ip_address"] == "192.168.1.100"
        assert metadata["user_agent"] == "test-client/1.0"
        assert metadata["path"] == "/api/test"
        assert metadata["method"] == "POST"
    
    def test_extract_request_metadata_with_forwarded_for(self):
        """Test request metadata extraction with X-Forwarded-For header."""
        middleware = SessionPersistenceMiddleware(None)
        
        class MockRequest:
            def __init__(self):
                self.url = Mock()
                self.url.path = "/test"
                self.method = "GET"
                self.headers = {
                    "x-forwarded-for": "203.0.113.1, 192.168.1.100",
                    "user-agent": "test-client/1.0"
                }
                self.client = Mock()
                self.client.host = "10.0.0.1"
        
        request = MockRequest()
        
        import asyncio
        metadata = asyncio.run(middleware._extract_request_metadata(request))
        
        # Should use first IP from X-Forwarded-For
        assert metadata["ip_address"] == "203.0.113.1"
        assert metadata["user_agent"] == "test-client/1.0"


class TestIntelligentErrorHandlerMiddleware:
    """Test intelligent error handler middleware core functionality."""
    
    def test_should_use_simple_error(self):
        """Test that certain paths use simple error responses."""
        middleware = IntelligentErrorHandlerMiddleware(None)
        
        class MockRequest:
            def __init__(self, path):
                self.url = Mock()
                self.url.path = path
        
        # Test paths that should use simple errors
        assert middleware._should_use_simple_error(MockRequest("/api/health"))
        assert middleware._should_use_simple_error(MockRequest("/docs"))
        assert middleware._should_use_simple_error(MockRequest("/openapi.json"))
        
        # Test paths that should use intelligent errors
        assert not middleware._should_use_simple_error(MockRequest("/api/test/protected"))
        assert not middleware._should_use_simple_error(MockRequest("/api/users"))
    
    def test_extract_provider_from_error(self):
        """Test provider detection from error messages."""
        middleware = IntelligentErrorHandlerMiddleware(None)
        
        # Test OpenAI detection
        assert middleware._extract_provider_from_error("OpenAI API key not found", "") == "openai"
        assert middleware._extract_provider_from_error("GPT model unavailable", "") == "openai"
        assert middleware._extract_provider_from_error("ChatGPT error", "") == "openai"
        
        # Test Anthropic detection
        assert middleware._extract_provider_from_error("Anthropic API error", "") == "anthropic"
        assert middleware._extract_provider_from_error("Claude model error", "") == "anthropic"
        
        # Test HuggingFace detection
        assert middleware._extract_provider_from_error("HuggingFace transformers error", "") == "huggingface"
        
        # Test no provider detected
        assert middleware._extract_provider_from_error("Generic database error", "") is None
        assert middleware._extract_provider_from_error("Network timeout", "") is None
    
    def test_extract_request_metadata(self):
        """Test request metadata extraction."""
        middleware = IntelligentErrorHandlerMiddleware(None)
        
        class MockRequest:
            def __init__(self):
                self.url = Mock()
                self.url.path = "/api/test"
                self.method = "POST"
                self.headers = {"user-agent": "test-client/1.0"}
                self.client = Mock()
                self.client.host = "192.168.1.100"
        
        request = MockRequest()
        
        import asyncio
        metadata = asyncio.run(middleware._extract_request_metadata(request))
        
        assert metadata["ip_address"] == "192.168.1.100"
        assert metadata["user_agent"] == "test-client/1.0"
        assert metadata["path"] == "/api/test"
        assert metadata["method"] == "POST"
        assert "timestamp" in metadata


class TestMiddlewareConfiguration:
    """Test middleware configuration and initialization."""
    
    def test_session_persistence_middleware_init(self):
        """Test session persistence middleware initialization."""
        # Test with intelligent errors enabled
        middleware = SessionPersistenceMiddleware(None, enable_intelligent_errors=True)
        assert middleware.enable_intelligent_errors is True
        
        # Test with intelligent errors disabled
        middleware = SessionPersistenceMiddleware(None, enable_intelligent_errors=False)
        assert middleware.enable_intelligent_errors is False
    
    def test_error_handler_middleware_init(self):
        """Test error handler middleware initialization."""
        # Test with intelligent responses enabled
        middleware = IntelligentErrorHandlerMiddleware(
            None, 
            enable_intelligent_responses=True, 
            debug_mode=False
        )
        assert middleware.enable_intelligent_responses is True
        assert middleware.debug_mode is False
        
        # Test with debug mode enabled
        middleware = IntelligentErrorHandlerMiddleware(
            None, 
            enable_intelligent_responses=True, 
            debug_mode=True
        )
        assert middleware.debug_mode is True
    
    @patch("ai_karen_engine.middleware.session_persistence.ErrorResponseService")
    def test_error_service_lazy_initialization(self, mock_service_class):
        """Test that error service is lazily initialized."""
        mock_instance = Mock()
        mock_service_class.return_value = mock_instance
        
        middleware = SessionPersistenceMiddleware(None, enable_intelligent_errors=True)
        
        # Error service should not be initialized yet
        assert middleware._error_response_service is None
        
        # First call should initialize the service
        service = middleware._get_error_response_service()
        assert service is mock_instance
        assert middleware._error_response_service is mock_instance
        
        # Second call should return the same instance
        service2 = middleware._get_error_response_service()
        assert service2 is mock_instance
        
        # Service class should only be called once
        mock_service_class.assert_called_once()
    
    @patch("ai_karen_engine.middleware.session_persistence.ErrorResponseService")
    def test_error_service_initialization_failure(self, mock_service_class):
        """Test handling of error service initialization failure."""
        mock_service_class.side_effect = Exception("Service init failed")
        
        middleware = SessionPersistenceMiddleware(None, enable_intelligent_errors=True)
        
        # Should handle initialization failure gracefully
        service = middleware._get_error_response_service()
        assert service is None
        assert middleware._error_response_service is None
    
    def test_error_service_disabled(self):
        """Test behavior when error service is disabled."""
        middleware = SessionPersistenceMiddleware(None, enable_intelligent_errors=False)
        
        # Should return None when disabled
        service = middleware._get_error_response_service()
        assert service is None


class TestTokenValidation:
    """Test token validation functionality."""
    
    @patch("ai_karen_engine.middleware.session_persistence.EnhancedTokenManager")
    @patch("ai_karen_engine.middleware.session_persistence.AuthConfig")
    def test_validate_access_token_success(self, mock_auth_config, mock_token_manager_class):
        """Test successful access token validation."""
        mock_token_manager = Mock()
        mock_token_manager_class.return_value = mock_token_manager
        
        # Mock successful token validation (async method)
        async def mock_validate(token):
            return {
                "sub": "user123",
                "email": "test@example.com",
                "roles": ["user"],
                "tenant_id": "default",
                "is_verified": True
            }
        
        mock_token_manager.validate_access_token = mock_validate
        
        middleware = SessionPersistenceMiddleware(None)
        
        import asyncio
        result = asyncio.run(middleware._validate_access_token("valid_token"))
        
        assert result is not None
        assert result["user_id"] == "user123"
        assert result["email"] == "test@example.com"
        assert result["roles"] == ["user"]
        assert result["tenant_id"] == "default"
        assert result["is_verified"] is True
    
    @patch("ai_karen_engine.middleware.session_persistence.EnhancedTokenManager")
    @patch("ai_karen_engine.middleware.session_persistence.AuthConfig")
    def test_validate_access_token_expired(self, mock_auth_config, mock_token_manager_class):
        """Test expired access token validation."""
        mock_token_manager = Mock()
        mock_token_manager_class.return_value = mock_token_manager
        
        # Mock expired token (async method)
        async def mock_validate_expired(token):
            raise TokenExpiredError("Token expired")
        
        mock_token_manager.validate_access_token = mock_validate_expired
        
        middleware = SessionPersistenceMiddleware(None)
        
        import asyncio
        result = asyncio.run(middleware._validate_access_token("expired_token"))
        
        assert result is None
    
    @patch("ai_karen_engine.middleware.session_persistence.EnhancedTokenManager")
    @patch("ai_karen_engine.middleware.session_persistence.AuthConfig")
    def test_validate_access_token_invalid(self, mock_auth_config, mock_token_manager_class):
        """Test invalid access token validation."""
        mock_token_manager = Mock()
        mock_token_manager_class.return_value = mock_token_manager
        
        # Mock invalid token (async method)
        async def mock_validate_invalid(token):
            raise InvalidTokenError("Invalid token")
        
        mock_token_manager.validate_access_token = mock_validate_invalid
        
        middleware = SessionPersistenceMiddleware(None)
        
        import asyncio
        with pytest.raises(Exception):  # Should raise HTTPException
            asyncio.run(middleware._validate_access_token("invalid_token"))


if __name__ == "__main__":
    pytest.main([__file__])