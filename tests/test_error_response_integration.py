"""
Integration tests for Error Response Service with Provider Health Monitor
"""

import pytest
from datetime import datetime

from ai_karen_engine.services.error_response_service import (
    ErrorResponseService,
    ErrorCategory,
    ErrorSeverity
)
from ai_karen_engine.services.provider_health_monitor import (
    ProviderHealthMonitor,
    HealthStatus,
    get_health_monitor
)


class TestErrorResponseProviderHealthIntegration:
    """Test integration between error response service and provider health monitor"""
    
    @pytest.fixture
    def error_service(self):
        """Create error response service"""
        return ErrorResponseService()
    
    @pytest.fixture
    def health_monitor(self):
        """Get global health monitor and clear cache"""
        monitor = get_health_monitor()
        monitor.clear_cache()  # Start with clean cache
        return monitor
    
    def test_error_response_with_healthy_provider(self, error_service, health_monitor):
        """Test error response when provider is healthy"""
        # Set up healthy provider
        health_monitor.update_provider_health("OpenAI", True, response_time=0.5)
        
        # Analyze an API key error
        response = error_service.analyze_error(
            error_message="OPENAI_API_KEY not set",
            provider_name="OpenAI"
        )
        
        assert response.category == ErrorCategory.API_KEY_MISSING
        assert response.provider_health is not None
        assert response.provider_health["status"] == "healthy"
        assert response.provider_health["success_rate"] == 1.0
        assert response.provider_health["response_time"] == 0.5
    
    def test_error_response_with_degraded_provider(self, error_service, health_monitor):
        """Test error response when provider is degraded"""
        # Set up degraded provider (multiple failures)
        for _ in range(3):
            health_monitor.update_provider_health("OpenAI", False, error_message="Rate limited")
        
        # Analyze a rate limit error
        response = error_service.analyze_error(
            error_message="Rate limit exceeded",
            provider_name="OpenAI"
        )
        
        assert response.category == ErrorCategory.RATE_LIMIT
        assert response.provider_health is not None
        assert response.provider_health["status"] == "degraded"
        assert response.provider_health["error_message"] == "Rate limited"
        
        # Should suggest alternative provider
        next_steps_text = " ".join(response.next_steps)
        assert "different provider" in next_steps_text.lower() or "alternative provider" in next_steps_text.lower()
    
    def test_error_response_with_unhealthy_provider(self, error_service, health_monitor):
        """Test error response when provider is unhealthy"""
        # Set up unhealthy provider (many failures)
        for _ in range(6):
            health_monitor.update_provider_health("OpenAI", False, error_message="Service down")
        
        # Set up healthy alternative
        health_monitor.update_provider_health("Anthropic", True, response_time=0.3)
        
        # Analyze a provider error
        response = error_service.analyze_error(
            error_message="Service unavailable",
            provider_name="OpenAI"
        )
        
        assert response.category == ErrorCategory.PROVIDER_DOWN
        assert response.provider_health is not None
        assert response.provider_health["status"] == "unhealthy"
        
        # Should suggest specific alternative
        next_steps_text = " ".join(response.next_steps)
        assert "anthropic" in next_steps_text.lower()
    
    def test_error_response_without_provider_health(self, error_service, health_monitor):
        """Test error response when no provider health data is available"""
        response = error_service.analyze_error(
            error_message="Unknown error occurred",
            provider_name="UnknownProvider"
        )
        
        assert response.category == ErrorCategory.UNKNOWN
        assert response.provider_health is not None
        assert response.provider_health["status"] == "unknown"
    
    def test_error_response_no_provider_specified(self, error_service, health_monitor):
        """Test error response when no provider is specified"""
        response = error_service.analyze_error(
            error_message="Database connection failed"
        )
        
        assert response.category == ErrorCategory.DATABASE_ERROR
        assert response.provider_health is None  # No provider specified
    
    def test_provider_health_context_in_response(self, error_service, health_monitor):
        """Test that provider health context is properly included"""
        # Set up provider with specific health data
        health_monitor.update_provider_health(
            "OpenAI", 
            False, 
            response_time=2.5, 
            error_message="Timeout after 30s"
        )
        
        response = error_service.analyze_error(
            error_message="Request timeout",
            provider_name="OpenAI"
        )
        
        assert response.provider_health is not None
        assert response.provider_health["name"] == "OpenAI"
        assert response.provider_health["response_time"] == 2.5
        assert response.provider_health["error_message"] == "Timeout after 30s"
        assert "last_check" in response.provider_health
    
    def test_multiple_providers_health_comparison(self, error_service, health_monitor):
        """Test error response considers multiple provider health states"""
        # Set up multiple providers with different health states
        health_monitor.update_provider_health("OpenAI", False)  # Degraded
        health_monitor.update_provider_health("Anthropic", True, response_time=0.3)  # Healthy
        health_monitor.update_provider_health("Google", True, response_time=0.8)  # Healthy but slower
        
        # Make OpenAI degraded
        for _ in range(2):
            health_monitor.update_provider_health("OpenAI", False)
        
        response = error_service.analyze_error(
            error_message="API key invalid",
            provider_name="OpenAI"
        )
        
        assert response.category == ErrorCategory.API_KEY_INVALID
        
        # Should suggest the best alternative (Anthropic due to better response time)
        next_steps_text = " ".join(response.next_steps)
        assert "anthropic" in next_steps_text.lower()
    
    def test_provider_health_cache_integration(self, error_service, health_monitor):
        """Test that error service uses cached provider health data"""
        # Update provider health
        health_monitor.update_provider_health("OpenAI", True, response_time=0.4)
        
        # Get health through error service (should use cache)
        response = error_service.analyze_error(
            error_message="OPENAI_API_KEY missing",
            provider_name="OpenAI"
        )
        
        # Verify cached data is used
        assert response.provider_health["response_time"] == 0.4
        assert response.provider_health["status"] == "healthy"
    
    def test_error_classification_with_provider_context(self, error_service, health_monitor):
        """Test that error classification considers provider context"""
        # Set up provider that's known to be down
        for _ in range(6):
            health_monitor.update_provider_health("OpenAI", False, error_message="503 Service Unavailable")
        
        # Analyze what could be either a provider or network error
        response = error_service.analyze_error(
            error_message="Connection refused",
            provider_name="OpenAI"
        )
        
        # Should classify as provider down, not generic network error
        assert response.category == ErrorCategory.PROVIDER_DOWN
        assert response.provider_health["status"] == "unhealthy"
    
    def test_success_rate_in_error_response(self, error_service, health_monitor):
        """Test that success rate is included in error responses"""
        # Create mixed success/failure pattern
        results = [True, True, False, True, False, True, True, False, True, True]
        for success in results:
            health_monitor.update_provider_health("OpenAI", success)
        
        response = error_service.analyze_error(
            error_message="Rate limit exceeded",
            provider_name="OpenAI"
        )
        
        expected_rate = sum(results) / len(results)  # 7/10 = 0.7
        assert abs(response.provider_health["success_rate"] - expected_rate) < 0.01
    
    def test_global_health_monitor_integration(self, error_service):
        """Test that error service uses global health monitor instance"""
        # Use global health monitor
        global_monitor = get_health_monitor()
        global_monitor.clear_cache()
        global_monitor.update_provider_health("TestProvider", True, response_time=0.6)
        
        # Error service should use the same global instance
        response = error_service.analyze_error(
            error_message="Test error",
            provider_name="TestProvider"
        )
        
        # Should have the health data from global monitor
        assert response.provider_health is not None
        assert response.provider_health["response_time"] == 0.6


if __name__ == "__main__":
    pytest.main([__file__])