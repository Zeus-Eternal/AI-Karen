"""
Unit tests for Error Response Service Fallback Mechanisms
Tests the enhanced fallback functionality when AI analysis is unavailable
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from ai_karen_engine.services.error_response_service import (
    ErrorResponseService,
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
    IntelligentErrorResponse
)
from ai_karen_engine.services.provider_health_monitor import HealthStatus


class TestErrorResponseFallbackMechanisms:
    """Test fallback mechanisms when AI analysis is unavailable"""
    
    @pytest.fixture
    def service(self):
        """Create an error response service instance"""
        return ErrorResponseService()
    
    @pytest.fixture
    def mock_health_monitor(self):
        """Mock health monitor"""
        with patch('ai_karen_engine.services.error_response_service.get_health_monitor') as mock:
            health_monitor = Mock()
            health_monitor.get_healthy_providers.return_value = []
            health_monitor.get_alternative_providers.return_value = ['anthropic', 'local']
            health_monitor.get_provider_health.return_value = None
            mock.return_value = health_monitor
            yield health_monitor
    
    def test_is_ai_available_when_no_providers(self, service, mock_health_monitor):
        """Test AI availability check when no providers are healthy"""
        mock_health_monitor.get_healthy_providers.return_value = []
        
        with patch.object(service, '_get_llm_router', return_value=Mock()):
            with patch.object(service, '_get_llm_utils', return_value=Mock()):
                assert service.is_ai_available() is False
    
    def test_is_ai_available_when_llm_router_unavailable(self, service, mock_health_monitor):
        """Test AI availability check when LLM router is unavailable"""
        mock_health_monitor.get_healthy_providers.return_value = ['openai']
        
        with patch.object(service, '_get_llm_router', return_value=None):
            with patch.object(service, '_get_llm_utils', return_value=Mock()):
                assert service.is_ai_available() is False
    
    def test_is_ai_available_when_llm_utils_unavailable(self, service, mock_health_monitor):
        """Test AI availability check when LLM utils is unavailable"""
        mock_health_monitor.get_healthy_providers.return_value = ['openai']
        
        with patch.object(service, '_get_llm_router', return_value=Mock()):
            with patch.object(service, '_get_llm_utils', return_value=None):
                assert service.is_ai_available() is False
    
    def test_is_ai_available_when_all_components_available(self, service, mock_health_monitor):
        """Test AI availability check when all components are available"""
        mock_health_monitor.get_healthy_providers.return_value = ['openai']
        
        with patch.object(service, '_get_llm_router', return_value=Mock()):
            with patch.object(service, '_get_llm_utils', return_value=Mock()):
                assert service.is_ai_available() is True
    
    def test_is_ai_available_handles_exceptions(self, service):
        """Test AI availability check handles exceptions gracefully"""
        with patch.object(service, '_get_llm_router', side_effect=Exception("Test error")):
            assert service.is_ai_available() is False
    
    def test_classify_error_locally_authentication(self, service):
        """Test local error classification for authentication errors"""
        test_cases = [
            ("Token has expired", ErrorCategory.AUTHENTICATION),
            ("Unauthorized access", ErrorCategory.AUTHENTICATION),
            ("Login failed", ErrorCategory.AUTHENTICATION),
            ("Session invalid", ErrorCategory.AUTHENTICATION),
            ("401 error occurred", ErrorCategory.AUTHENTICATION)
        ]
        
        for error_message, expected_category in test_cases:
            category = service.classify_error_locally(error_message)
            assert category == expected_category, f"Failed for: {error_message}"
    
    def test_classify_error_locally_api_key_missing(self, service):
        """Test local error classification for missing API key errors"""
        test_cases = [
            ("API key not found", ErrorCategory.API_KEY_MISSING),
            ("OPENAI_API_KEY not set", ErrorCategory.API_KEY_MISSING),
            ("API key missing from configuration", ErrorCategory.API_KEY_MISSING),
            ("ANTHROPIC_API_KEY not found", ErrorCategory.API_KEY_MISSING)
        ]
        
        for error_message, expected_category in test_cases:
            category = service.classify_error_locally(error_message)
            assert category == expected_category, f"Failed for: {error_message}"
    
    def test_classify_error_locally_api_key_invalid(self, service):
        """Test local error classification for invalid API key errors"""
        test_cases = [
            ("API key invalid", ErrorCategory.API_KEY_INVALID),
            ("Invalid API key provided", ErrorCategory.API_KEY_INVALID),
            ("API key incorrect", ErrorCategory.API_KEY_INVALID)
        ]
        
        for error_message, expected_category in test_cases:
            category = service.classify_error_locally(error_message)
            assert category == expected_category, f"Failed for: {error_message}"
    
    def test_classify_error_locally_rate_limit(self, service):
        """Test local error classification for rate limit errors"""
        test_cases = [
            ("Rate limit exceeded", ErrorCategory.RATE_LIMIT),
            ("Too many requests", ErrorCategory.RATE_LIMIT),
            ("Quota exceeded", ErrorCategory.RATE_LIMIT),
            ("429 error", ErrorCategory.RATE_LIMIT)
        ]
        
        for error_message, expected_category in test_cases:
            category = service.classify_error_locally(error_message)
            assert category == expected_category, f"Failed for: {error_message}"
    
    def test_classify_error_locally_provider_down(self, service):
        """Test local error classification for provider down errors"""
        test_cases = [
            ("Service unavailable", ErrorCategory.PROVIDER_DOWN),
            ("Provider is down", ErrorCategory.PROVIDER_DOWN),
            ("Connection refused", ErrorCategory.PROVIDER_DOWN),
            ("503 service unavailable", ErrorCategory.PROVIDER_DOWN)
        ]
        
        for error_message, expected_category in test_cases:
            category = service.classify_error_locally(error_message)
            assert category == expected_category, f"Failed for: {error_message}"
    
    def test_classify_error_locally_network_error(self, service):
        """Test local error classification for network errors"""
        test_cases = [
            ("Connection timeout", ErrorCategory.NETWORK_ERROR),
            ("Network error occurred", ErrorCategory.NETWORK_ERROR),
            ("Request timeout", ErrorCategory.NETWORK_ERROR),
            ("504 gateway timeout", ErrorCategory.NETWORK_ERROR)
        ]
        
        for error_message, expected_category in test_cases:
            category = service.classify_error_locally(error_message)
            assert category == expected_category, f"Failed for: {error_message}"
    
    def test_classify_error_locally_database_error(self, service):
        """Test local error classification for database errors"""
        test_cases = [
            ("Database connection failed", ErrorCategory.DATABASE_ERROR),
            ("SQL error occurred", ErrorCategory.DATABASE_ERROR),
            ("Table does not exist", ErrorCategory.DATABASE_ERROR),
            ("Relation not found", ErrorCategory.DATABASE_ERROR)
        ]
        
        for error_message, expected_category in test_cases:
            category = service.classify_error_locally(error_message)
            assert category == expected_category, f"Failed for: {error_message}"
    
    def test_classify_error_locally_validation_error(self, service):
        """Test local error classification for validation errors"""
        test_cases = [
            ("Validation failed", ErrorCategory.VALIDATION_ERROR),
            ("Invalid input provided", ErrorCategory.VALIDATION_ERROR),
            ("Required field missing", ErrorCategory.VALIDATION_ERROR),
            ("400 bad request", ErrorCategory.VALIDATION_ERROR)
        ]
        
        for error_message, expected_category in test_cases:
            category = service.classify_error_locally(error_message)
            assert category == expected_category, f"Failed for: {error_message}"
    
    def test_classify_error_locally_unknown(self, service):
        """Test local error classification for unknown errors"""
        category = service.classify_error_locally("Some completely unknown error")
        assert category == ErrorCategory.UNKNOWN
    
    def test_get_fallback_response_authentication(self, service):
        """Test getting fallback response for authentication errors"""
        response = service.get_fallback_response(ErrorCategory.AUTHENTICATION)
        
        assert response["title"] == "Authentication Required"
        assert "log in" in response["summary"].lower()
        assert response["severity"] == ErrorSeverity.MEDIUM
        assert response["contact_admin"] is False
        assert len(response["next_steps"]) > 0
    
    def test_get_fallback_response_api_key_missing(self, service):
        """Test getting fallback response for missing API key errors"""
        response = service.get_fallback_response(ErrorCategory.API_KEY_MISSING)
        
        assert response["title"] == "API Configuration Missing"
        assert "api keys" in response["summary"].lower()
        assert response["severity"] == ErrorSeverity.HIGH
        assert response["contact_admin"] is True
        assert any("env" in step.lower() for step in response["next_steps"])
    
    def test_get_fallback_response_rate_limit(self, service):
        """Test getting fallback response for rate limit errors"""
        response = service.get_fallback_response(ErrorCategory.RATE_LIMIT)
        
        assert response["title"] == "Rate Limit Exceeded"
        assert "too many requests" in response["summary"].lower()
        assert response["severity"] == ErrorSeverity.MEDIUM
        assert response["retry_after"] == 300
        assert any("wait" in step.lower() for step in response["next_steps"])
    
    def test_get_fallback_response_database_error(self, service):
        """Test getting fallback response for database errors"""
        response = service.get_fallback_response(ErrorCategory.DATABASE_ERROR)
        
        assert response["title"] == "Database Error"
        assert "database" in response["summary"].lower()
        assert response["severity"] == ErrorSeverity.CRITICAL
        assert response["contact_admin"] is True
        assert any("admin" in step.lower() for step in response["next_steps"])
    
    def test_analyze_error_with_ai_unavailable(self, service, mock_health_monitor):
        """Test error analysis when AI is unavailable falls back to rules"""
        # Mock AI as unavailable
        with patch.object(service, 'is_ai_available', return_value=False):
            response = service.analyze_error(
                error_message="API key not found in configuration",
                use_ai_analysis=True
            )
        
        assert response.category == ErrorCategory.API_KEY_MISSING
        assert response.severity == ErrorSeverity.HIGH
        assert "API Configuration Missing" in response.title
        assert len(response.next_steps) > 0
    
    def test_analyze_error_fallback_for_unclassified(self, service, mock_health_monitor):
        """Test error analysis fallback for completely unclassified errors"""
        with patch.object(service, 'is_ai_available', return_value=False):
            response = service.analyze_error(
                error_message="Some completely unknown error occurred",
                use_ai_analysis=True
            )
        
        assert response.category == ErrorCategory.UNKNOWN
        assert response.severity == ErrorSeverity.MEDIUM
        assert "Unexpected Error" in response.title
        assert response.contact_admin is True
        assert response.technical_details is not None
    
    def test_analyze_error_with_provider_health_info(self, service, mock_health_monitor):
        """Test error analysis includes provider health information"""
        # Mock provider health
        provider_health = Mock()
        provider_health.name = "OpenAI"
        provider_health.status = HealthStatus.UNHEALTHY
        provider_health.success_rate = 0.0
        provider_health.response_time = 5000
        provider_health.error_message = "Connection failed"
        provider_health.last_check = datetime.utcnow()
        
        mock_health_monitor.get_provider_health.return_value = provider_health
        mock_health_monitor.get_alternative_providers.return_value = ['anthropic', 'local']
        
        with patch.object(service, 'is_ai_available', return_value=False):
            response = service.analyze_error(
                error_message="OpenAI service unavailable",
                provider_name="OpenAI"
            )
        
        assert response.provider_health is not None
        assert response.provider_health["name"] == "OpenAI"
        assert response.provider_health["status"] == "unhealthy"
        assert any("anthropic" in step.lower() for step in response.next_steps)
    
    def test_handle_ai_analysis_failure(self, service):
        """Test handling AI analysis failure"""
        context = ErrorContext(
            error_message="Test error",
            provider_name="OpenAI"
        )
        
        with patch.object(service, '_audit_logger') as mock_audit:
            response = service.handle_ai_analysis_failure(context, Exception("AI failed"))
        
        assert isinstance(response, IntelligentErrorResponse)
        assert response.category == ErrorCategory.UNKNOWN
        mock_audit.log_ai_analysis_failed.assert_called_once()
    
    def test_get_provider_fallback_suggestions(self, service, mock_health_monitor):
        """Test getting provider fallback suggestions"""
        mock_health_monitor.get_alternative_providers.return_value = ['anthropic', 'local', 'huggingface']
        
        suggestions = service.get_provider_fallback_suggestions("openai")
        
        assert len(suggestions) == 3
        assert 'anthropic' in suggestions
        assert 'local' in suggestions
        assert 'huggingface' in suggestions
    
    def test_get_provider_fallback_suggestions_handles_errors(self, service):
        """Test provider fallback suggestions handle errors gracefully"""
        with patch('ai_karen_engine.services.error_response_service.get_health_monitor', side_effect=Exception("Test error")):
            suggestions = service.get_provider_fallback_suggestions("openai")
            assert suggestions == []
    
    def test_get_cache_ttl_for_category(self, service):
        """Test getting appropriate cache TTL for different error categories"""
        test_cases = [
            (ErrorCategory.API_KEY_MISSING, 3600),    # 1 hour
            (ErrorCategory.AUTHENTICATION, 300),       # 5 minutes
            (ErrorCategory.RATE_LIMIT, 900),          # 15 minutes
            (ErrorCategory.DATABASE_ERROR, 180),       # 3 minutes
            (ErrorCategory.NETWORK_ERROR, 60),         # 1 minute
            (ErrorCategory.UNKNOWN, 300)               # Default 5 minutes
        ]
        
        for category, expected_ttl in test_cases:
            ttl = service._get_cache_ttl_for_category(category)
            assert ttl == expected_ttl, f"Failed for category: {category}"
    
    def test_enhanced_caching_prevents_repeated_failures(self, service):
        """Test that enhanced caching prevents repeated analysis failures"""
        error_message = "Database connection failed"
        
        # Mock cache to return None first time, then return cached response
        cached_response = {
            "title": "Database Error",
            "summary": "Database connection failed",
            "category": ErrorCategory.DATABASE_ERROR,
            "severity": ErrorSeverity.CRITICAL,
            "next_steps": ["Contact admin"],
            "contact_admin": True,
            "provider_health": None,
            "retry_after": None,
            "help_url": None,
            "technical_details": None
        }
        
        with patch.object(service, '_response_cache') as mock_cache:
            with patch.object(service, '_audit_logger'):
                # First call - cache miss
                mock_cache.get_cached_response.return_value = None
                response1 = service.analyze_error(error_message, use_ai_analysis=False)
                
                # Second call - cache hit
                mock_cache.get_cached_response.return_value = cached_response
                response2 = service.analyze_error(error_message, use_ai_analysis=False)
        
        # Verify both responses are for database errors
        assert response1.category == ErrorCategory.DATABASE_ERROR
        assert response2.category == ErrorCategory.DATABASE_ERROR
        
        # Verify cache was called
        assert mock_cache.get_cached_response.call_count == 2
        assert mock_cache.cache_response.call_count == 1  # Only cached once
    
    def test_ai_analysis_metrics_include_fallback_info(self, service):
        """Test that AI analysis metrics include fallback information"""
        with patch.object(service, 'is_ai_available', return_value=False):
            metrics = service.get_ai_analysis_metrics()
        
        assert 'ai_available' in metrics
        assert 'fallback_categories_supported' in metrics
        assert metrics['ai_available'] is False
        assert metrics['fallback_categories_supported'] == len(ErrorCategory)
    
    def test_fallback_response_quality_validation(self, service):
        """Test that fallback responses meet quality standards"""
        for category in ErrorCategory:
            if category == ErrorCategory.UNKNOWN:
                continue  # Skip unknown category as it's handled differently
                
            fallback_data = service.get_fallback_response(category)
            
            # Validate response structure
            assert 'title' in fallback_data
            assert 'summary' in fallback_data
            assert 'next_steps' in fallback_data
            assert 'severity' in fallback_data
            
            # Validate content quality
            assert len(fallback_data['title']) > 5
            assert len(fallback_data['summary']) > 10
            assert len(fallback_data['next_steps']) > 0
            assert isinstance(fallback_data['severity'], ErrorSeverity)
            
            # Validate actionable steps
            action_words = ['add', 'check', 'verify', 'try', 'contact', 'update', 'restart', 'wait', 'use']
            has_actionable_step = any(
                any(word in step.lower() for word in action_words)
                for step in fallback_data['next_steps']
            )
            assert has_actionable_step, f"No actionable steps for category: {category}"


if __name__ == "__main__":
    pytest.main([__file__])