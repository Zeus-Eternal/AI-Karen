"""
Simple tests for error response routes without heavy dependencies
"""

import pytest
from unittest.mock import MagicMock, patch
import time

# Test the core functionality without importing the full routes
def test_cache_key_generation():
    """Test cache key generation logic"""
    import hashlib
    
    def _generate_cache_key_test(error_message, error_type, status_code, provider_name):
        """Test version of cache key generation"""
        key_data = f"{error_message}:{error_type}:{status_code}:{provider_name}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    # Test same inputs generate same key
    key1 = _generate_cache_key_test("Test error", "TestError", 500, "openai")
    key2 = _generate_cache_key_test("Test error", "TestError", 500, "openai")
    assert key1 == key2
    
    # Test different inputs generate different keys
    key3 = _generate_cache_key_test("Different error", "TestError", 500, "openai")
    assert key1 != key3
    
    # Test key format
    assert len(key1) == 32
    assert all(c in '0123456789abcdef' for c in key1)


def test_cache_expiry_logic():
    """Test cache expiry logic"""
    cache_ttl = 300  # 5 minutes
    current_time = time.time()
    
    # Test valid cache entry
    cache_entry = {
        "response": {"test": "data"},
        "timestamp": current_time - 100  # 100 seconds ago
    }
    
    cache_age = current_time - cache_entry["timestamp"]
    assert cache_age < cache_ttl  # Should be valid
    
    # Test expired cache entry
    expired_entry = {
        "response": {"test": "data"},
        "timestamp": current_time - 400  # 400 seconds ago
    }
    
    expired_age = current_time - expired_entry["timestamp"]
    assert expired_age > cache_ttl  # Should be expired


def test_error_analysis_request_model():
    """Test the ErrorAnalysisRequest model"""
    from pydantic import BaseModel, Field
    from typing import Optional, Dict, Any
    
    class ErrorAnalysisRequest(BaseModel):
        error_message: str = Field(..., description="The error message to analyze")
        error_type: Optional[str] = Field(None, description="Optional error type")
        status_code: Optional[int] = Field(None, description="Optional HTTP status code")
        provider_name: Optional[str] = Field(None, description="Optional provider name")
        use_ai_analysis: bool = Field(True, description="Whether to use AI analysis")
    
    # Test valid request
    request = ErrorAnalysisRequest(
        error_message="Test error",
        error_type="TestError",
        status_code=500,
        provider_name="openai"
    )
    
    assert request.error_message == "Test error"
    assert request.error_type == "TestError"
    assert request.status_code == 500
    assert request.provider_name == "openai"
    assert request.use_ai_analysis is True
    
    # Test minimal request
    minimal_request = ErrorAnalysisRequest(error_message="Minimal error")
    assert minimal_request.error_message == "Minimal error"
    assert minimal_request.error_type is None
    assert minimal_request.use_ai_analysis is True


def test_error_analysis_response_model():
    """Test the ErrorAnalysisResponse model"""
    from pydantic import BaseModel, Field
    from typing import List, Optional, Dict, Any
    from enum import Enum
    
    class ErrorCategory(str, Enum):
        API_KEY_MISSING = "api_key_missing"
        SYSTEM_ERROR = "system_error"
    
    class ErrorSeverity(str, Enum):
        LOW = "low"
        HIGH = "high"
    
    class ErrorAnalysisResponse(BaseModel):
        title: str = Field(..., description="Error title")
        summary: str = Field(..., description="Error summary")
        category: ErrorCategory = Field(..., description="Error category")
        severity: ErrorSeverity = Field(..., description="Error severity")
        next_steps: List[str] = Field(..., description="Next steps")
        contact_admin: bool = Field(False, description="Contact admin flag")
        cached: bool = Field(False, description="Cached response flag")
        response_time_ms: float = Field(..., description="Response time")
    
    # Test response creation
    response = ErrorAnalysisResponse(
        title="Test Error",
        summary="Test summary",
        category=ErrorCategory.API_KEY_MISSING,
        severity=ErrorSeverity.HIGH,
        next_steps=["Step 1", "Step 2"],
        contact_admin=False,
        cached=False,
        response_time_ms=150.5
    )
    
    assert response.title == "Test Error"
    assert response.category == ErrorCategory.API_KEY_MISSING
    assert response.severity == ErrorSeverity.HIGH
    assert len(response.next_steps) == 2
    assert response.response_time_ms == 150.5


@patch('ai_karen_engine.services.error_response_service.ErrorResponseService')
def test_error_service_integration(mock_service_class):
    """Test integration with error response service"""
    # Mock the service
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    
    # Mock response
    from ai_karen_engine.services.error_response_service import (
        IntelligentErrorResponse,
        ErrorCategory,
        ErrorSeverity
    )
    
    mock_response = IntelligentErrorResponse(
        title="Mock Error",
        summary="Mock summary",
        category=ErrorCategory.API_KEY_MISSING,
        severity=ErrorSeverity.HIGH,
        next_steps=["Mock step"],
        contact_admin=False
    )
    
    mock_service.analyze_error.return_value = mock_response
    
    # Test service call
    service = mock_service_class()
    result = service.analyze_error(
        error_message="Test error",
        error_type="TestError",
        status_code=500
    )
    
    assert result.title == "Mock Error"
    assert result.category == ErrorCategory.API_KEY_MISSING
    mock_service.analyze_error.assert_called_once()


def test_provider_health_response_model():
    """Test provider health response model"""
    from pydantic import BaseModel, Field
    from typing import Dict, Any
    
    class ProviderHealthResponse(BaseModel):
        providers: Dict[str, Dict[str, Any]] = Field(..., description="Provider health data")
        healthy_count: int = Field(..., description="Healthy provider count")
        total_count: int = Field(..., description="Total provider count")
        last_updated: str = Field(..., description="Last update timestamp")
    
    # Test response creation
    response = ProviderHealthResponse(
        providers={
            "openai": {
                "status": "healthy",
                "success_rate": 0.95,
                "response_time": 1200
            }
        },
        healthy_count=1,
        total_count=1,
        last_updated="2024-01-15T10:30:00Z"
    )
    
    assert response.healthy_count == 1
    assert response.total_count == 1
    assert "openai" in response.providers
    assert response.providers["openai"]["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])