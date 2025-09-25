"""
Basic integration test for error response endpoint
Tests the endpoint functionality with minimal dependencies
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Mock the dependencies to avoid heavy imports
@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mock heavy dependencies"""
    with patch('ai_karen_engine.core.dependencies.get_current_user_context') as mock_user_context, \
         patch('ai_karen_engine.services.error_response_service.ErrorResponseService') as mock_service_class, \
         patch('ai_karen_engine.services.provider_health_monitor.get_health_monitor') as mock_health_monitor:
        
        # Mock user context
        mock_user_context.return_value = {"user_id": "test_user", "tenant_id": "test_tenant"}
        
        # Mock error response service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Mock health monitor
        mock_monitor = MagicMock()
        mock_health_monitor.return_value = mock_monitor
        
        yield {
            'user_context': mock_user_context,
            'service': mock_service,
            'monitor': mock_monitor
        }


@pytest.fixture
def app():
    """Create FastAPI app with error response routes"""
    app = FastAPI()
    
    # Import and include the router after mocking dependencies
    from ai_karen_engine.api_routes.error_response_routes import router
    app.include_router(router, prefix="/api")
    
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


def test_analyze_error_endpoint_basic(client, mock_dependencies):
    """Test basic error analysis endpoint functionality"""
    from ai_karen_engine.services.error_response_service import (
        IntelligentErrorResponse,
        ErrorCategory,
        ErrorSeverity
    )
    
    # Configure mock service response
    mock_response = IntelligentErrorResponse(
        title="Test Error Response",
        summary="This is a test error analysis",
        category=ErrorCategory.API_KEY_MISSING,
        severity=ErrorSeverity.HIGH,
        next_steps=["Add API key", "Restart service"],
        contact_admin=False,
        retry_after=None,
        help_url="https://example.com/help",
        technical_details="Test technical details"
    )
    
    mock_dependencies['service'].analyze_error.return_value = mock_response
    
    # Make request
    request_data = {
        "error_message": "OpenAI API key not found",
        "error_type": "AuthenticationError",
        "status_code": 401,
        "provider_name": "openai"
    }
    
    response = client.post("/api/error-response/analyze", json=request_data)
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    assert data["title"] == "Test Error Response"
    assert data["summary"] == "This is a test error analysis"
    assert data["category"] == "api_key_missing"
    assert data["severity"] == "high"
    assert data["next_steps"] == ["Add API key", "Restart service"]
    assert data["contact_admin"] is False
    assert data["help_url"] == "https://example.com/help"
    assert data["technical_details"] == "Test technical details"
    assert "response_time_ms" in data
    
    # Verify service was called
    mock_dependencies['service'].analyze_error.assert_called_once()


def test_analyze_error_validation(client):
    """Test request validation"""
    # Test missing required field
    response = client.post("/api/error-response/analyze", json={})
    assert response.status_code == 422
    
    # Test invalid data types
    response = client.post("/api/error-response/analyze", json={
        "error_message": "Test error",
        "status_code": "invalid"  # Should be int
    })
    assert response.status_code == 422


def test_analyze_error_service_failure(client, mock_dependencies):
    """Test error analysis when service fails"""
    # Configure service to raise exception
    mock_dependencies['service'].analyze_error.side_effect = Exception("Service error")
    
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


def test_provider_health_endpoint(client, mock_dependencies):
    """Test provider health endpoint"""
    from ai_karen_engine.services.provider_health_monitor import ProviderHealthInfo, HealthStatus
    from datetime import datetime
    
    # Configure mock health data
    health_info = ProviderHealthInfo(
        name="openai",
        status=HealthStatus.HEALTHY,
        last_check=datetime.utcnow(),
        response_time=1200.0,
        success_rate=0.95,
        consecutive_failures=0
    )
    
    mock_dependencies['monitor'].get_all_provider_health.return_value = {
        "openai": health_info,
        "anthropic": health_info
    }
    
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


def test_cache_stats_endpoint(client, mock_dependencies):
    """Test cache statistics endpoint"""
    # Configure mock cache stats
    mock_dependencies['monitor'].get_cache_stats.return_value = {
        "total_providers": 2,
        "healthy_count": 2,
        "degraded_count": 0,
        "unhealthy_count": 0,
        "unknown_count": 0,
        "average_response_time": 1200.0
    }
    
    response = client.get("/api/error-response/cache/stats")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "response_cache" in data
    assert "provider_health_cache" in data
    assert "last_updated" in data
    
    # Check response cache stats
    response_cache = data["response_cache"]
    assert "total_entries" in response_cache
    assert "valid_entries" in response_cache
    assert "cache_ttl_seconds" in response_cache
    
    # Check provider health cache stats
    health_cache = data["provider_health_cache"]
    assert health_cache["total_providers"] == 2
    assert health_cache["healthy_count"] == 2


def test_clear_cache_endpoint(client, mock_dependencies):
    """Test cache clear endpoint"""
    response = client.post("/api/error-response/cache/clear")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "message" in data
    assert "statistics" in data
    
    # Check statistics
    stats = data["statistics"]
    assert "entries_cleared" in stats
    assert "cleared_at" in stats


def test_caching_behavior(client, mock_dependencies):
    """Test response caching behavior"""
    from ai_karen_engine.services.error_response_service import (
        IntelligentErrorResponse,
        ErrorCategory,
        ErrorSeverity
    )
    
    # Configure cacheable response
    mock_response = IntelligentErrorResponse(
        title="API Key Missing",
        summary="OpenAI API key not configured",
        category=ErrorCategory.API_KEY_MISSING,  # Cacheable category
        severity=ErrorSeverity.HIGH,
        next_steps=["Add API key"],
        contact_admin=False
    )
    
    mock_dependencies['service'].analyze_error.return_value = mock_response
    
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
    assert mock_dependencies['service'].analyze_error.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])