"""
Integration tests for Error Response Service AI Fallback functionality
Tests the complete flow from AI unavailability to fallback responses
"""

import pytest
from unittest.mock import Mock, patch

from ai_karen_engine.services.error_response_service import (
    ErrorResponseService,
    ErrorCategory,
    ErrorSeverity
)
from ai_karen_engine.services.provider_health_monitor import HealthStatus


class TestErrorResponseAIFallbackIntegration:
    """Integration tests for AI fallback functionality"""
    
    @pytest.fixture
    def service(self):
        """Create an error response service instance"""
        return ErrorResponseService()
    
    def test_complete_ai_fallback_flow(self, service):
        """Test complete flow from AI unavailable to fallback response"""
        # Mock all AI components as unavailable
        with patch.object(service, '_get_llm_router', return_value=None):
            with patch.object(service, '_get_llm_utils', return_value=None):
                with patch('ai_karen_engine.services.error_response_service.get_health_monitor') as mock_health:
                    health_monitor = Mock()
                    health_monitor.get_healthy_providers.return_value = []
                    mock_health.return_value = health_monitor
                    
                    # Test with a known error pattern
                    response = service.analyze_error(
                        error_message="OPENAI_API_KEY not set in environment",
                        use_ai_analysis=True
                    )
                    
                    # Should fall back to rule-based classification
                    assert response.category == ErrorCategory.API_KEY_MISSING
                    assert response.severity == ErrorSeverity.HIGH
                    assert "API" in response.title
                    assert len(response.next_steps) > 0
                    assert any("env" in step.lower() for step in response.next_steps)
    
    def test_ai_available_but_fails_gracefully(self, service):
        """Test graceful handling when AI is available but fails"""
        # Mock AI as available but failing
        mock_router = Mock()
        mock_router.invoke.side_effect = Exception("AI service failed")
        mock_utils = Mock()
        
        with patch.object(service, '_get_llm_router', return_value=mock_router):
            with patch.object(service, '_get_llm_utils', return_value=mock_utils):
                with patch('ai_karen_engine.services.error_response_service.get_health_monitor') as mock_health:
                    health_monitor = Mock()
                    health_monitor.get_healthy_providers.return_value = ['openai']
                    mock_health.return_value = health_monitor
                    
                    response = service.analyze_error(
                        error_message="Database connection failed",
                        use_ai_analysis=True
                    )
                    
                    # Should fall back to rule-based classification
                    assert response.category == ErrorCategory.DATABASE_ERROR
                    assert response.severity == ErrorSeverity.CRITICAL
                    assert response.contact_admin is True
    
    def test_fallback_response_caching(self, service):
        """Test that fallback responses are cached appropriately"""
        with patch.object(service, 'is_ai_available', return_value=False):
            with patch.object(service, '_response_cache') as mock_cache:
                with patch.object(service, '_audit_logger'):
                    mock_cache.get_cached_response.return_value = None
                    
                    # First call should trigger caching
                    response1 = service.analyze_error(
                        error_message="API key invalid",
                        use_ai_analysis=True
                    )
                    
                    # Verify cache was called
                    assert mock_cache.cache_response.called
                    
                    # Verify response quality
                    assert response1.category == ErrorCategory.API_KEY_INVALID
                    assert len(response1.next_steps) > 0
    
    def test_provider_health_integration_with_fallback(self, service):
        """Test provider health integration with fallback responses"""
        with patch.object(service, 'is_ai_available', return_value=False):
            with patch('ai_karen_engine.services.error_response_service.get_health_monitor') as mock_health:
                # Mock unhealthy provider with alternatives
                provider_health = Mock()
                provider_health.name = "OpenAI"
                provider_health.status = HealthStatus.UNHEALTHY
                provider_health.success_rate = 0.0
                provider_health.response_time = 5000
                provider_health.error_message = "Connection failed"
                provider_health.last_check.isoformat.return_value = "2023-01-01T00:00:00"
                
                health_monitor = Mock()
                health_monitor.get_provider_health.return_value = provider_health
                health_monitor.get_alternative_providers.return_value = ['anthropic', 'local']
                mock_health.return_value = health_monitor
                
                response = service.analyze_error(
                    error_message="Service unavailable",
                    provider_name="OpenAI"
                )
                
                # Should include provider health info
                assert response.provider_health is not None
                assert response.provider_health["name"] == "OpenAI"
                assert response.provider_health["status"] == "unhealthy"
                
                # Should suggest alternatives
                assert any("anthropic" in step.lower() for step in response.next_steps)
    
    def test_metrics_reflect_fallback_usage(self, service):
        """Test that metrics properly reflect fallback usage"""
        with patch.object(service, 'is_ai_available', return_value=False):
            metrics = service.get_ai_analysis_metrics()
            
            assert 'ai_available' in metrics
            assert 'fallback_categories_supported' in metrics
            assert metrics['ai_available'] is False
            assert metrics['fallback_categories_supported'] > 0
    
    def test_different_cache_ttls_for_categories(self, service):
        """Test that different error categories get appropriate cache TTLs"""
        test_cases = [
            (ErrorCategory.API_KEY_MISSING, 3600),    # 1 hour
            (ErrorCategory.AUTHENTICATION, 300),       # 5 minutes
            (ErrorCategory.RATE_LIMIT, 900),          # 15 minutes
            (ErrorCategory.DATABASE_ERROR, 180),       # 3 minutes
            (ErrorCategory.NETWORK_ERROR, 60)          # 1 minute
        ]
        
        for category, expected_ttl in test_cases:
            ttl = service._get_cache_ttl_for_category(category)
            assert ttl == expected_ttl, f"Wrong TTL for {category}: expected {expected_ttl}, got {ttl}"
    
    def test_fallback_quality_standards(self, service):
        """Test that all fallback responses meet quality standards"""
        test_errors = [
            ("API key not found", ErrorCategory.API_KEY_MISSING),
            ("Token expired", ErrorCategory.AUTHENTICATION),
            ("Rate limit exceeded", ErrorCategory.RATE_LIMIT),
            ("Database connection failed", ErrorCategory.DATABASE_ERROR),
            ("Service unavailable", ErrorCategory.PROVIDER_DOWN),
            ("Connection timeout", ErrorCategory.NETWORK_ERROR),
            ("Validation failed", ErrorCategory.VALIDATION_ERROR)
        ]
        
        with patch.object(service, 'is_ai_available', return_value=False):
            for error_message, expected_category in test_errors:
                response = service.analyze_error(error_message, use_ai_analysis=True)
                
                # Verify category classification
                assert response.category == expected_category
                
                # Verify quality standards
                assert service.validate_response_quality(response), f"Quality check failed for: {error_message}"
                
                # Verify actionable steps
                action_words = ['add', 'check', 'verify', 'try', 'contact', 'update', 'restart', 'wait', 'use', 'click']
                has_actionable = any(
                    any(word in step.lower() for word in action_words)
                    for step in response.next_steps
                )
                assert has_actionable, f"No actionable steps for: {error_message}"


if __name__ == "__main__":
    pytest.main([__file__])