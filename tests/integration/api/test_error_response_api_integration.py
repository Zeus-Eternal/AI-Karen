"""
Integration tests for the Intelligent Error Response API endpoint

Tests the complete error response API functionality including:
- Error analysis endpoint
- Provider health endpoint  
- Rate limiting
- Caching behavior
- AI integration
- Middleware integration
"""

import asyncio
import json
import pytest
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI

# Import the real FastAPI TestClient, not the stub
try:
    from fastapi.testclient import TestClient as RealTestClient
    REAL_FASTAPI_AVAILABLE = True
except ImportError:
    REAL_FASTAPI_AVAILABLE = False
    RealTestClient = None

from httpx import AsyncClient

from ai_karen_engine.api_routes.error_response_routes import (
    router as error_response_router,
    get_error_response_service,
    _response_cache,
    _get_cached_response,
    _cache_response,
    _generate_cache_key,
    ErrorAnalysisRequest,
    ErrorAnalysisResponse
)
from ai_karen_engine.services.error_response_service import (
    ErrorResponseService,
    IntelligentErrorResponse,
    ErrorCategory,
    ErrorSeverity
)
from ai_karen_engine.services.provider_health_monitor import (
    ProviderHealthMonitor,
    ProviderHealthInfo,
    HealthStatus
)


# Test fixtures
@pytest.fixture
def app():
    """Create FastAPI app with error response routes"""
    app = FastAPI()
    app.include_router(error_response_router, prefix="/api")
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    if not REAL_FASTAPI_AVAILABLE:
        pytest.skip("Real FastAPI TestClient not available")
    return RealTestClient(app)


@pytest.fixture
async def async_client(app):
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_error_service():
    """Mock error response service"""
    service = MagicMock(spec=ErrorResponseService)
    
    # Mock analyze_error method
    service.analyze_error.return_value = IntelligentErrorResponse(
        title="Test Error",
        summary="This is a test error response",
        category=ErrorCategory.API_KEY_MISSING,
        severity=ErrorSeverity.HIGH,
        next_steps=["Step 1", "Step 2"],
        contact_admin=False,
        retry_after=None,
        help_url="https://example.com/help",
        technical_details="Test technical details"
    )
    
    return service


@pytest.fixture
def mock_health_monitor():
    """Mock provider health monitor"""
    monitor = MagicMock(spec=ProviderHealthMonitor)
    
    # Mock health data
    health_info = ProviderHealthInfo(
        name="openai",
        status=HealthStatus.HEALTHY,
        last_check=datetime.utcnow(),
        response_time=1200.0,
        success_rate=0.95,
        consecutive_failures=0
    )
    
    monitor.get_all_provider_health.return_value = {
        "openai": health_info,
        "anthropic": health_info
    }
    
    monitor.get_cache_stats.return_value = {
        "total_providers": 2,
        "healthy_count": 2,
        "degraded_count": 0,
        "unhealthy_count": 0,
        "unknown_count": 0,
        "average_response_time": 1200.0
    }
    
    return monitor


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear response cache before each test"""
    global _response_cache
    _response_cache.clear()
    yield
    _response_cache.clear()


class TestErrorAnalysisEndpoint:
    """Test the error analysis endpoint"""
    
    @patch('ai_karen_engine.api_routes.error_response_routes.get_error_response_service')
    def test_analyze_error_basic(self, mock_get_service, client, mock_error_service):
        """Test basic error analysis"""
        mock_get_service.return_value = mock_error_service
        
        request_data = {
            "error_message": "OpenAI API key not found",
            "error_type": "AuthenticationError",
            "status_code": 401,
            "provider_name": "openai"
        }
        
        response = client.post("/api/error-response/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == "Test Error"
        assert data["summary"] == "This is a test error response"
        assert data["category"] == "api_key_missing"
        assert data["severity"] == "high"
        assert data["next_steps"] == ["Step 1", "Step 2"]
        assert data["contact_admin"] is False
        assert data["cached"] is False
        assert "response_time_ms" in data
        
        # Verify service was called correctly
        mock_error_service.analyze_error.assert_called_once()
        call_args = mock_error_service.analyze_error.call_args
        assert call_args[1]["error_message"] == "OpenAI API key not found"
        assert call_args[1]["error_type"] == "AuthenticationError"
        assert call_args[1]["status_code"] == 401
        assert call_args[1]["provider_name"] == "openai"
    
    @patch('ai_karen_engine.api_routes.error_response_routes.get_error_response_service')
    def test_analyze_error_with_user_context(self, mock_get_service, client, mock_error_service):
        """Test error analysis with user context"""
        mock_get_service.return_value = mock_error_service
        
        request_data = {
            "error_message": "Rate limit exceeded",
            "provider_name": "openai",
            "user_context": {
                "user_id": "test_user",
                "session_id": "test_session"
            }
        }
        
        with patch('ai_karen_engine.api_routes.error_response_routes.get_current_user_context') as mock_user_context:
            mock_user_context.return_value = {"user_id": "test_user", "tenant_id": "test_tenant"}
            
            response = client.post("/api/error-response/analyze", json=request_data)
        
        assert response.status_code == 200
        
        # Verify additional context was passed
        call_args = mock_error_service.analyze_error.call_args
        additional_context = call_args[1]["additional_context"]
        assert additional_context["user_id"] == "test_user"
        assert additional_context["tenant_id"] == "test_tenant"
        assert additional_context["user_id"] == "test_user"  # From user_context
        assert additional_context["session_id"] == "test_session"  # From user_context
    
    @patch('ai_karen_engine.api_routes.error_response_routes.get_error_response_service')
    def test_analyze_error_caching(self, mock_get_service, client, mock_error_service):
        """Test response caching functionality"""
        mock_get_service.return_value = mock_error_service
        
        # Configure service to return cacheable error
        mock_error_service.analyze_error.return_value = IntelligentErrorResponse(
            title="API Key Missing",
            summary="OpenAI API key not configured",
            category=ErrorCategory.API_KEY_MISSING,  # Cacheable category
            severity=ErrorSeverity.HIGH,
            next_steps=["Add API key"],
            contact_admin=False
        )
        
        request_data = {
            "error_message": "OpenAI API key not found",
            "error_type": "AuthenticationError"
        }
        
        # First request - should call service
        response1 = client.post("/api/error-response/analyze", json=request_data)
        assert response1.status_code == 200
        assert response1.json()["cached"] is False
        
        # Second request - should use cache
        response2 = client.post("/api/error-response/analyze", json=request_data)
        assert response2.status_code == 200
        assert response2.json()["cached"] is True
        
        # Service should only be called once
        assert mock_error_service.analyze_error.call_count == 1
    
    @patch('ai_karen_engine.api_routes.error_response_routes.get_error_response_service')
    def test_analyze_error_service_failure(self, mock_get_service, client):
        """Test error analysis when service fails"""
        mock_service = MagicMock()
        mock_service.analyze_error.side_effect = Exception("Service error")
        mock_get_service.return_value = mock_service
        
        request_data = {
            "error_message": "Test error",
            "error_type": "TestError"
        }
        
        response = client.post("/api/error-response/analyze", json=request_data)
        
        # Should return fallback response, not error
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == "Analysis Error"
        assert data["summary"] == "Unable to analyze the error at this time."
        assert data["category"] == "system_error"
        assert data["contact_admin"] is True
        assert "Service error" in data["technical_details"]
    
    def test_analyze_error_validation(self, client):
        """Test request validation"""
        # Missing required field
        response = client.post("/api/error-response/analyze", json={})
        assert response.status_code == 422
        
        # Invalid status code
        response = client.post("/api/error-response/analyze", json={
            "error_message": "Test error",
            "status_code": "invalid"
        })
        assert response.status_code == 422
    
    @patch('ai_karen_engine.api_routes.error_response_routes.get_error_response_service')
    def test_analyze_error_ai_analysis_disabled(self, mock_get_service, client, mock_error_service):
        """Test error analysis with AI analysis disabled"""
        mock_get_service.return_value = mock_error_service
        
        request_data = {
            "error_message": "Test error",
            "use_ai_analysis": False
        }
        
        response = client.post("/api/error-response/analyze", json=request_data)
        assert response.status_code == 200
        
        # Verify AI analysis was disabled
        call_args = mock_error_service.analyze_error.call_args
        assert call_args[1]["use_ai_analysis"] is False


class TestProviderHealthEndpoint:
    """Test the provider health endpoint"""
    
    @patch('ai_karen_engine.api_routes.error_response_routes.get_health_monitor')
    def test_get_provider_health(self, mock_get_monitor, client, mock_health_monitor):
        """Test getting provider health status"""
        mock_get_monitor.return_value = mock_health_monitor
        
        response = client.get("/api/error-response/provider-health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "providers" in data
        assert "healthy_count" in data
        assert "total_count" in data
        assert "last_updated" in data
        
        assert data["healthy_count"] == 2
        assert data["total_count"] == 2
        assert "openai" in data["providers"]
        assert "anthropic" in data["providers"]
        
        # Check provider details
        openai_health = data["providers"]["openai"]
        assert openai_health["status"] == "healthy"
        assert openai_health["success_rate"] == 0.95
        assert openai_health["response_time"] == 1200.0
    
    @patch('ai_karen_engine.api_routes.error_response_routes.get_health_monitor')
    def test_get_provider_health_failure(self, mock_get_monitor, client):
        """Test provider health endpoint when monitor fails"""
        mock_monitor = MagicMock()
        mock_monitor.get_all_provider_health.side_effect = Exception("Monitor error")
        mock_get_monitor.return_value = mock_monitor
        
        response = client.get("/api/error-response/provider-health")
        
        assert response.status_code == 500
        assert "Failed to retrieve provider health status" in response.json()["detail"]


class TestCacheManagement:
    """Test cache management endpoints"""
    
    def test_clear_cache(self, client):
        """Test clearing response cache"""
        # Add some data to cache first
        _response_cache["test_key"] = {
            "response": {"test": "data"},
            "timestamp": time.time()
        }
        
        with patch('ai_karen_engine.api_routes.error_response_routes.get_current_user_context') as mock_user_context:
            mock_user_context.return_value = {"user_id": "test_user"}
            
            response = client.post("/api/error-response/cache/clear")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "statistics" in data
        assert data["statistics"]["entries_cleared"] == 1
        
        # Verify cache is cleared
        assert len(_response_cache) == 0
    
    def test_get_cache_stats(self, client):
        """Test getting cache statistics"""
        # Add some data to cache
        _response_cache["test_key"] = {
            "response": {"test": "data"},
            "timestamp": time.time()
        }
        
        with patch('ai_karen_engine.api_routes.error_response_routes.get_health_monitor') as mock_get_monitor:
            mock_monitor = MagicMock()
            mock_monitor.get_cache_stats.return_value = {
                "total_providers": 2,
                "healthy_count": 2
            }
            mock_get_monitor.return_value = mock_monitor
            
            response = client.get("/api/error-response/cache/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response_cache" in data
        assert "provider_health_cache" in data
        assert data["response_cache"]["total_entries"] == 1
        assert data["response_cache"]["valid_entries"] == 1


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    @patch('ai_karen_engine.api_routes.error_response_routes.get_error_response_service')
    def test_rate_limiting_analyze_endpoint(self, mock_get_service, client, mock_error_service):
        """Test rate limiting on analyze endpoint"""
        mock_get_service.return_value = mock_error_service
        
        request_data = {
            "error_message": "Test error"
        }
        
        # Make requests up to the limit
        # Note: In real tests, you'd need to configure slowapi properly
        # This is a basic structure test
        
        responses = []
        for i in range(5):  # Make several requests
            response = client.post("/api/error-response/analyze", json=request_data)
            responses.append(response)
        
        # All should succeed (rate limit is 30/minute)
        for response in responses:
            assert response.status_code == 200
    
    def test_rate_limiting_cache_clear(self, client):
        """Test rate limiting on cache clear endpoint"""
        with patch('ai_karen_engine.api_routes.error_response_routes.get_current_user_context') as mock_user_context:
            mock_user_context.return_value = {"user_id": "test_user"}
            
            # Make several requests
            responses = []
            for i in range(3):
                response = client.post("/api/error-response/cache/clear")
                responses.append(response)
            
            # All should succeed (rate limit is 10/minute)
            for response in responses:
                assert response.status_code == 200


class TestCacheUtilities:
    """Test cache utility functions"""
    
    def test_generate_cache_key(self):
        """Test cache key generation"""
        request1 = ErrorAnalysisRequest(
            error_message="Test error",
            error_type="TestError",
            status_code=500,
            provider_name="openai"
        )
        
        request2 = ErrorAnalysisRequest(
            error_message="Test error",
            error_type="TestError",
            status_code=500,
            provider_name="openai"
        )
        
        request3 = ErrorAnalysisRequest(
            error_message="Different error",
            error_type="TestError",
            status_code=500,
            provider_name="openai"
        )
        
        key1 = _generate_cache_key(request1)
        key2 = _generate_cache_key(request2)
        key3 = _generate_cache_key(request3)
        
        # Same requests should generate same key
        assert key1 == key2
        
        # Different requests should generate different keys
        assert key1 != key3
        
        # Keys should be valid MD5 hashes
        assert len(key1) == 32
        assert all(c in '0123456789abcdef' for c in key1)
    
    def test_cache_response_and_retrieval(self):
        """Test caching and retrieving responses"""
        cache_key = "test_key"
        response_data = {
            "title": "Test Response",
            "summary": "Test summary",
            "category": "test_category"
        }
        
        # Cache response
        _cache_response(cache_key, response_data)
        
        # Retrieve cached response
        cached = _get_cached_response(cache_key)
        
        assert cached is not None
        assert cached["title"] == "Test Response"
        assert cached["cached"] is True
    
    def test_cache_expiry(self):
        """Test cache expiry functionality"""
        cache_key = "test_key"
        response_data = {"test": "data"}
        
        # Cache response with old timestamp
        _response_cache[cache_key] = {
            "response": response_data,
            "timestamp": time.time() - 400  # 400 seconds ago (expired)
        }
        
        # Should return None for expired cache
        cached = _get_cached_response(cache_key)
        assert cached is None
        
        # Cache entry should be removed
        assert cache_key not in _response_cache


class TestIntegrationScenarios:
    """Test complete integration scenarios"""
    
    @patch('ai_karen_engine.api_routes.error_response_routes.get_error_response_service')
    @patch('ai_karen_engine.api_routes.error_response_routes.get_health_monitor')
    def test_complete_error_analysis_flow(self, mock_get_monitor, mock_get_service, client):
        """Test complete error analysis flow with provider health"""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.analyze_error.return_value = IntelligentErrorResponse(
            title="OpenAI API Key Missing",
            summary="The OpenAI API key is not configured",
            category=ErrorCategory.API_KEY_MISSING,
            severity=ErrorSeverity.HIGH,
            next_steps=["Add OPENAI_API_KEY to .env", "Restart application"],
            provider_health={
                "name": "openai",
                "status": "unknown",
                "success_rate": 0.0
            },
            contact_admin=False,
            help_url="https://platform.openai.com/docs"
        )
        mock_get_service.return_value = mock_service
        
        mock_monitor = MagicMock()
        mock_monitor.get_all_provider_health.return_value = {
            "openai": ProviderHealthInfo(
                name="openai",
                status=HealthStatus.UNKNOWN,
                last_check=datetime.utcnow(),
                success_rate=0.0
            )
        }
        mock_get_monitor.return_value = mock_monitor
        
        # Test error analysis
        error_request = {
            "error_message": "OpenAI API key not found",
            "error_type": "AuthenticationError",
            "status_code": 401,
            "provider_name": "openai",
            "request_path": "/api/chat"
        }
        
        response = client.post("/api/error-response/analyze", json=error_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == "OpenAI API Key Missing"
        assert data["category"] == "api_key_missing"
        assert data["severity"] == "high"
        assert len(data["next_steps"]) == 2
        assert data["provider_health"]["name"] == "openai"
        assert data["help_url"] == "https://platform.openai.com/docs"
        
        # Test provider health
        health_response = client.get("/api/error-response/provider-health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert "openai" in health_data["providers"]
    
    @patch('ai_karen_engine.api_routes.error_response_routes.get_error_response_service')
    def test_ai_enhanced_error_analysis(self, mock_get_service, client):
        """Test AI-enhanced error analysis"""
        # Mock service with AI enhancement
        mock_service = MagicMock()
        mock_service.analyze_error.return_value = IntelligentErrorResponse(
            title="Complex Database Error",
            summary="Database connection failed with detailed AI analysis",
            category=ErrorCategory.DATABASE_ERROR,
            severity=ErrorSeverity.CRITICAL,
            next_steps=[
                "Check database connection string",
                "Verify database server is running",
                "Check network connectivity",
                "Contact admin if issue persists"
            ],
            contact_admin=True,
            technical_details="AI-enhanced analysis: Connection timeout after 30s, likely network issue"
        )
        mock_get_service.return_value = mock_service
        
        request_data = {
            "error_message": "psycopg2.OperationalError: could not connect to server",
            "error_type": "DatabaseError",
            "status_code": 500,
            "use_ai_analysis": True
        }
        
        response = client.post("/api/error-response/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == "Complex Database Error"
        assert data["category"] == "database_error"
        assert data["severity"] == "critical"
        assert data["contact_admin"] is True
        assert len(data["next_steps"]) == 4
        assert "AI-enhanced analysis" in data["technical_details"]
        
        # Verify AI analysis was enabled
        call_args = mock_service.analyze_error.call_args
        assert call_args[1]["use_ai_analysis"] is True


@pytest.mark.asyncio
class TestAsyncIntegration:
    """Test async integration scenarios"""
    
    @patch('ai_karen_engine.api_routes.error_response_routes.get_error_response_service')
    async def test_concurrent_error_analysis(self, mock_get_service, async_client):
        """Test concurrent error analysis requests"""
        mock_service = MagicMock()
        mock_service.analyze_error.return_value = IntelligentErrorResponse(
            title="Concurrent Test",
            summary="Test concurrent analysis",
            category=ErrorCategory.SYSTEM_ERROR,
            severity=ErrorSeverity.MEDIUM,
            next_steps=["Test step"]
        )
        mock_get_service.return_value = mock_service
        
        # Make concurrent requests
        tasks = []
        for i in range(5):
            request_data = {
                "error_message": f"Test error {i}",
                "error_type": "TestError"
            }
            task = async_client.post("/api/error-response/analyze", json=request_data)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Concurrent Test"
        
        # Service should be called for each request
        assert mock_service.analyze_error.call_count == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])