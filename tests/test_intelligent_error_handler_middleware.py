"""
Tests for Intelligent Error Handler Middleware

Tests the intelligent error handler middleware functionality including:
- Global error handling with intelligent responses
- HTTP exception handling
- Unhandled exception handling
- Provider detection from errors
- Debug mode functionality
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from ai_karen_engine.middleware.intelligent_error_handler import IntelligentErrorHandlerMiddleware


@pytest.fixture
def app():
    """Create test FastAPI app with intelligent error handler middleware."""
    app = FastAPI()
    
    # Add middleware
    app.add_middleware(
        IntelligentErrorHandlerMiddleware,
        enable_intelligent_responses=True,
        debug_mode=False
    )
    
    # Add test routes
    @app.get("/api/test/success")
    async def success_route():
        return {"message": "success"}
    
    @app.get("/api/test/http_error")
    async def http_error_route():
        raise HTTPException(status_code=400, detail="Bad request")
    
    @app.get("/api/test/unhandled_error")
    async def unhandled_error_route():
        raise ValueError("Something went wrong")
    
    @app.get("/api/test/openai_error")
    async def openai_error_route():
        raise Exception("OpenAI API key not found")
    
    @app.get("/api/health")
    async def health_route():
        raise HTTPException(status_code=503, detail="Service unavailable")
    
    return app


@pytest.fixture
def debug_app():
    """Create test FastAPI app with debug mode enabled."""
    app = FastAPI()
    
    # Add middleware with debug mode
    app.add_middleware(
        IntelligentErrorHandlerMiddleware,
        enable_intelligent_responses=True,
        debug_mode=True
    )
    
    @app.get("/api/test/error")
    async def error_route():
        raise ValueError("Debug error")
    
    return app


@pytest.fixture
def simple_app():
    """Create test FastAPI app with intelligent responses disabled."""
    app = FastAPI()
    
    # Add middleware with intelligent responses disabled
    app.add_middleware(
        IntelligentErrorHandlerMiddleware,
        enable_intelligent_responses=False,
        debug_mode=False
    )
    
    @app.get("/api/test/error")
    async def error_route():
        raise HTTPException(status_code=400, detail="Simple error")
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_error_service():
    """Mock error response service."""
    with patch("ai_karen_engine.middleware.intelligent_error_handler.ErrorResponseService") as mock:
        instance = Mock()
        mock.return_value = instance
        yield instance


class TestIntelligentErrorHandlerMiddleware:
    """Test intelligent error handler middleware functionality."""
    
    def test_successful_request_passes_through(self, client):
        """Test that successful requests pass through without modification."""
        response = client.get("/api/test/success")
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
    
    def test_http_exception_with_intelligent_response(self, client, mock_error_service):
        """Test HTTP exception handling with intelligent error response."""
        # Mock error service response
        mock_response = Mock()
        mock_response.summary = "The request was malformed or invalid"
        mock_response.title = "Bad Request"
        mock_response.category = "validation_error"
        mock_response.severity = "low"
        mock_response.next_steps = ["Check your input format", "Verify required fields"]
        mock_response.contact_admin = False
        mock_response.retry_after = None
        mock_response.help_url = "https://docs.example.com/api"
        mock_response.provider_health = None
        mock_response.technical_details = None
        mock_error_service.analyze_error.return_value = mock_response
        
        response = client.get("/api/test/http_error")
        assert response.status_code == 400
        
        data = response.json()
        assert data["detail"] == "The request was malformed or invalid"
        assert data["error"]["title"] == "Bad Request"
        assert data["error"]["category"] == "validation_error"
        assert data["error"]["severity"] == "low"
        assert data["error"]["next_steps"] == ["Check your input format", "Verify required fields"]
        assert data["error"]["contact_admin"] is False
        assert data["error"]["help_url"] == "https://docs.example.com/api"
        assert "timestamp" in data["error"]
    
    def test_unhandled_exception_with_intelligent_response(self, client, mock_error_service):
        """Test unhandled exception handling with intelligent error response."""
        # Mock error service response
        mock_response = Mock()
        mock_response.summary = "An unexpected error occurred while processing your request"
        mock_response.title = "Internal Server Error"
        mock_response.category = "system_error"
        mock_response.severity = "high"
        mock_response.next_steps = ["Try again later", "Contact admin if problem persists"]
        mock_response.contact_admin = True
        mock_response.retry_after = 60
        mock_response.help_url = None
        mock_response.provider_health = None
        mock_response.technical_details = "ValueError: Something went wrong"
        mock_error_service.analyze_error.return_value = mock_response
        
        response = client.get("/api/test/unhandled_error")
        assert response.status_code == 500
        
        data = response.json()
        assert data["detail"] == "An unexpected error occurred while processing your request"
        assert data["error"]["title"] == "Internal Server Error"
        assert data["error"]["category"] == "system_error"
        assert data["error"]["severity"] == "high"
        assert data["error"]["contact_admin"] is True
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "60"
    
    def test_provider_detection_from_error_message(self, client, mock_error_service):
        """Test provider detection from error messages."""
        # Mock error service response
        mock_response = Mock()
        mock_response.summary = "OpenAI API key is missing"
        mock_response.title = "API Key Missing"
        mock_response.category = "api_key_missing"
        mock_response.severity = "high"
        mock_response.next_steps = ["Add OPENAI_API_KEY to your .env file"]
        mock_response.contact_admin = False
        mock_response.retry_after = None
        mock_response.help_url = None
        mock_response.provider_health = None
        mock_response.technical_details = None
        mock_error_service.analyze_error.return_value = mock_response
        
        response = client.get("/api/test/openai_error")
        assert response.status_code == 500
        
        # Verify error service was called with provider name
        mock_error_service.analyze_error.assert_called_once()
        call_args = mock_error_service.analyze_error.call_args
        assert call_args[1]["provider_name"] == "openai"
    
    def test_simple_error_paths_use_simple_responses(self, client, mock_error_service):
        """Test that certain paths use simple error responses instead of intelligent ones."""
        response = client.get("/api/health")
        assert response.status_code == 503
        
        # Should get simple error response
        data = response.json()
        assert data == {"detail": "Service unavailable"}
        
        # Error service should not be called for simple error paths
        mock_error_service.analyze_error.assert_not_called()
    
    def test_debug_mode_includes_traceback(self):
        """Test that debug mode includes traceback in error responses."""
        debug_app = FastAPI()
        debug_app.add_middleware(
            IntelligentErrorHandlerMiddleware,
            enable_intelligent_responses=True,
            debug_mode=True
        )
        
        @debug_app.get("/api/test/error")
        async def error_route():
            raise ValueError("Debug error")
        
        client = TestClient(debug_app)
        
        with patch("ai_karen_engine.middleware.intelligent_error_handler.ErrorResponseService") as mock_service:
            mock_response = Mock()
            mock_response.summary = "Debug error occurred"
            mock_response.title = "Debug Error"
            mock_response.category = "system_error"
            mock_response.severity = "high"
            mock_response.next_steps = ["Check logs"]
            mock_response.contact_admin = False
            mock_response.retry_after = None
            mock_response.help_url = None
            mock_response.provider_health = None
            mock_response.technical_details = "ValueError: Debug error"
            mock_service.return_value.analyze_error.return_value = mock_response
            
            response = client.get("/api/test/error")
            assert response.status_code == 500
            
            data = response.json()
            assert "traceback" in data["error"]
            assert "ValueError: Debug error" in data["error"]["traceback"]
    
    def test_intelligent_responses_disabled(self):
        """Test middleware behavior when intelligent responses are disabled."""
        simple_app = FastAPI()
        simple_app.add_middleware(
            IntelligentErrorHandlerMiddleware,
            enable_intelligent_responses=False,
            debug_mode=False
        )
        
        @simple_app.get("/api/test/error")
        async def error_route():
            raise HTTPException(status_code=400, detail="Simple error")
        
        client = TestClient(simple_app)
        response = client.get("/api/test/error")
        
        assert response.status_code == 400
        data = response.json()
        assert data == {"detail": "Simple error"}
    
    def test_error_service_initialization_failure(self, client):
        """Test handling when error service initialization fails."""
        with patch("ai_karen_engine.middleware.intelligent_error_handler.ErrorResponseService") as mock_service:
            # Mock initialization failure
            mock_service.side_effect = Exception("Service init failed")
            
            response = client.get("/api/test/http_error")
            assert response.status_code == 400
            
            # Should fallback to simple error response
            data = response.json()
            assert data == {"detail": "Bad request"}
    
    def test_error_service_analysis_failure(self, client, mock_error_service):
        """Test handling when error service analysis fails."""
        # Mock analysis failure
        mock_error_service.analyze_error.side_effect = Exception("Analysis failed")
        
        response = client.get("/api/test/http_error")
        assert response.status_code == 400
        
        # Should fallback to simple error response
        data = response.json()
        assert data == {"detail": "Bad request"}
    
    def test_provider_health_included_in_response(self, client, mock_error_service):
        """Test that provider health information is included in error responses."""
        # Mock error service response with provider health
        mock_response = Mock()
        mock_response.summary = "OpenAI service is currently unavailable"
        mock_response.title = "Service Unavailable"
        mock_response.category = "provider_down"
        mock_response.severity = "high"
        mock_response.next_steps = ["Try again later", "Use alternative provider"]
        mock_response.contact_admin = False
        mock_response.retry_after = 180
        mock_response.help_url = None
        mock_response.provider_health = {
            "name": "openai",
            "status": "unhealthy",
            "success_rate": 0.0,
            "response_time": 5000,
            "error_message": "Connection timeout"
        }
        mock_response.technical_details = None
        mock_error_service.analyze_error.return_value = mock_response
        
        response = client.get("/api/test/openai_error")
        assert response.status_code == 500
        
        data = response.json()
        assert "provider_health" in data["error"]
        assert data["error"]["provider_health"]["name"] == "openai"
        assert data["error"]["provider_health"]["status"] == "unhealthy"
    
    def test_retry_after_header_set(self, client, mock_error_service):
        """Test that Retry-After header is set when specified in error response."""
        # Mock error service response with retry_after
        mock_response = Mock()
        mock_response.summary = "Rate limit exceeded"
        mock_response.title = "Too Many Requests"
        mock_response.category = "rate_limit"
        mock_response.severity = "medium"
        mock_response.next_steps = ["Wait before retrying"]
        mock_response.contact_admin = False
        mock_response.retry_after = 300
        mock_response.help_url = None
        mock_response.provider_health = None
        mock_response.technical_details = None
        mock_error_service.analyze_error.return_value = mock_response
        
        response = client.get("/api/test/http_error")
        assert response.status_code == 400
        
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "300"
    
    def test_request_metadata_extraction(self, client, mock_error_service):
        """Test that request metadata is properly extracted and passed to error service."""
        mock_response = Mock()
        mock_response.summary = "Error occurred"
        mock_response.title = "Error"
        mock_response.category = "system_error"
        mock_response.severity = "medium"
        mock_response.next_steps = ["Try again"]
        mock_response.contact_admin = False
        mock_response.retry_after = None
        mock_response.help_url = None
        mock_response.provider_health = None
        mock_response.technical_details = None
        mock_error_service.analyze_error.return_value = mock_response
        
        response = client.get(
            "/api/test/http_error",
            headers={"User-Agent": "test-client/1.0"}
        )
        assert response.status_code == 400
        
        # Verify error service was called with request metadata
        mock_error_service.analyze_error.assert_called_once()
        call_args = mock_error_service.analyze_error.call_args
        additional_context = call_args[1]["additional_context"]
        
        assert additional_context["path"] == "/api/test/http_error"
        assert additional_context["method"] == "GET"
        assert additional_context["user_agent"] == "test-client/1.0"
        assert "timestamp" in additional_context


class TestProviderDetection:
    """Test provider detection functionality."""
    
    def test_openai_provider_detection(self):
        """Test detection of OpenAI-related errors."""
        middleware = IntelligentErrorHandlerMiddleware(None)
        
        # Test various OpenAI error patterns
        test_cases = [
            ("OpenAI API key not found", "openai api error"),
            ("GPT model unavailable", "some traceback"),
            ("ChatGPT rate limit exceeded", ""),
        ]
        
        for error_msg, traceback in test_cases:
            provider = middleware._extract_provider_from_error(error_msg, traceback)
            assert provider == "openai"
    
    def test_anthropic_provider_detection(self):
        """Test detection of Anthropic-related errors."""
        middleware = IntelligentErrorHandlerMiddleware(None)
        
        test_cases = [
            ("Anthropic API key invalid", ""),
            ("Claude model error", "anthropic client error"),
        ]
        
        for error_msg, traceback in test_cases:
            provider = middleware._extract_provider_from_error(error_msg, traceback)
            assert provider == "anthropic"
    
    def test_no_provider_detected(self):
        """Test when no provider can be detected from error."""
        middleware = IntelligentErrorHandlerMiddleware(None)
        
        provider = middleware._extract_provider_from_error(
            "Generic database error", 
            "some generic traceback"
        )
        assert provider is None


class TestMiddlewareIntegration:
    """Test middleware integration scenarios."""
    
    def test_middleware_with_other_middleware(self):
        """Test that error handler works correctly with other middleware."""
        app = FastAPI()
        
        # Add error handler first
        app.add_middleware(
            IntelligentErrorHandlerMiddleware,
            enable_intelligent_responses=True,
            debug_mode=False
        )
        
        # Add another middleware that might raise exceptions
        @app.middleware("http")
        async def failing_middleware(request, call_next):
            if request.url.path == "/api/test/middleware_error":
                raise ValueError("Middleware error")
            return await call_next(request)
        
        @app.get("/api/test/success")
        async def success_route():
            return {"message": "success"}
        
        @app.get("/api/test/middleware_error")
        async def middleware_error_route():
            return {"message": "should not reach here"}
        
        client = TestClient(app)
        
        # Test successful request
        response = client.get("/api/test/success")
        assert response.status_code == 200
        
        # Test middleware error handling
        with patch("ai_karen_engine.middleware.intelligent_error_handler.ErrorResponseService") as mock_service:
            mock_response = Mock()
            mock_response.summary = "Middleware error occurred"
            mock_response.title = "Internal Error"
            mock_response.category = "system_error"
            mock_response.severity = "high"
            mock_response.next_steps = ["Contact admin"]
            mock_response.contact_admin = True
            mock_response.retry_after = None
            mock_response.help_url = None
            mock_response.provider_health = None
            mock_response.technical_details = None
            mock_service.return_value.analyze_error.return_value = mock_response
            
            response = client.get("/api/test/middleware_error")
            assert response.status_code == 500
            
            data = response.json()
            assert data["error"]["title"] == "Internal Error"


if __name__ == "__main__":
    pytest.main([__file__])