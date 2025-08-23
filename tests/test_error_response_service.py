"""
Unit tests for the Error Response Service
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from ai_karen_engine.services.error_response_service import (
    ErrorResponseService,
    ErrorClassificationRule,
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
    IntelligentErrorResponse,
    format_error_for_user,
    format_error_for_api
)


class TestErrorClassificationRule:
    """Test error classification rules"""
    
    def test_rule_creation(self):
        """Test creating a classification rule"""
        rule = ErrorClassificationRule(
            name="test_rule",
            patterns=[r"test.*error"],
            category=ErrorCategory.SYSTEM_ERROR,
            severity=ErrorSeverity.MEDIUM,
            title_template="Test Error",
            summary_template="A test error occurred",
            next_steps=["Step 1", "Step 2"]
        )
        
        assert rule.name == "test_rule"
        assert rule.category == ErrorCategory.SYSTEM_ERROR
        assert rule.severity == ErrorSeverity.MEDIUM
        assert len(rule.patterns) == 1
        assert len(rule.next_steps) == 2
    
    def test_rule_matching(self):
        """Test rule pattern matching"""
        rule = ErrorClassificationRule(
            name="api_key_rule",
            patterns=[r"api.*key.*missing", r"OPENAI_API_KEY.*not.*set"],
            category=ErrorCategory.API_KEY_MISSING,
            severity=ErrorSeverity.HIGH,
            title_template="API Key Missing",
            summary_template="API key not found",
            next_steps=["Add API key"]
        )
        
        # Test positive matches
        assert rule.matches("API key missing from configuration")
        assert rule.matches("OPENAI_API_KEY not set in environment")
        assert rule.matches("The api key is missing")
        
        # Test negative matches
        assert not rule.matches("Database connection failed")
        assert not rule.matches("Rate limit exceeded")
    
    def test_rule_formatting(self):
        """Test rule response formatting with context"""
        rule = ErrorClassificationRule(
            name="provider_error",
            patterns=[r"provider.*error"],
            category=ErrorCategory.PROVIDER_DOWN,
            severity=ErrorSeverity.HIGH,
            title_template="Provider Error: {provider}",
            summary_template="The {provider} service is unavailable",
            next_steps=["Try {provider} again", "Contact admin"],
            retry_after=300
        )
        
        context = ErrorContext(
            error_message="Provider error occurred",
            provider_name="OpenAI"
        )
        
        response = rule.format_response(context)
        
        assert response["title"] == "Provider Error: OpenAI"
        assert response["summary"] == "The OpenAI service is unavailable"
        assert response["next_steps"] == ["Try OpenAI again", "Contact admin"]
        assert response["retry_after"] == 300


class TestErrorResponseService:
    """Test the main error response service"""
    
    @pytest.fixture
    def service(self):
        """Create an error response service instance"""
        return ErrorResponseService()
    
    def test_service_initialization(self, service):
        """Test service initialization"""
        assert len(service.classification_rules) > 0
        assert service._cache_ttl == 300
        assert isinstance(service._provider_health_cache, dict)
    
    def test_openai_api_key_missing_classification(self, service):
        """Test classification of OpenAI API key missing error"""
        response = service.analyze_error(
            error_message="OPENAI_API_KEY not set in environment",
            provider_name="OpenAI"
        )
        
        assert response.category == ErrorCategory.API_KEY_MISSING
        assert response.severity == ErrorSeverity.HIGH
        assert "OpenAI API Key Missing" in response.title
        assert "Add OPENAI_API_KEY to your .env file" in response.next_steps
        assert response.help_url is not None
    
    def test_anthropic_api_key_missing_classification(self, service):
        """Test classification of Anthropic API key missing error"""
        response = service.analyze_error(
            error_message="Anthropic API key not found",
            provider_name="Anthropic"
        )
        
        assert response.category == ErrorCategory.API_KEY_MISSING
        assert response.severity == ErrorSeverity.HIGH
        assert "Anthropic API Key Missing" in response.title
        assert "Add ANTHROPIC_API_KEY to your .env file" in response.next_steps
    
    def test_session_expired_classification(self, service):
        """Test classification of session expired error"""
        response = service.analyze_error(
            error_message="Token has expired",
            status_code=401
        )
        
        assert response.category == ErrorCategory.AUTHENTICATION
        assert response.severity == ErrorSeverity.MEDIUM
        assert "Session Expired" in response.title
        assert "Click the login button to sign in again" in response.next_steps
    
    def test_rate_limit_classification(self, service):
        """Test classification of rate limit error"""
        response = service.analyze_error(
            error_message="Rate limit exceeded for requests",
            status_code=429,
            provider_name="OpenAI"
        )
        
        assert response.category == ErrorCategory.RATE_LIMIT
        assert response.severity == ErrorSeverity.MEDIUM
        assert "Rate Limit Exceeded" in response.title
        assert response.retry_after == 300
        assert "Wait a few minutes before trying again" in response.next_steps
    
    def test_database_connection_error_classification(self, service):
        """Test classification of database connection error"""
        response = service.analyze_error(
            error_message="Database connection failed: Connection refused"
        )
        
        assert response.category == ErrorCategory.DATABASE_ERROR
        assert response.severity == ErrorSeverity.CRITICAL
        assert "Database Connection Failed" in response.title
        assert response.contact_admin is True
        assert "Contact admin immediately" in response.next_steps
    
    def test_missing_table_error_classification(self, service):
        """Test classification of missing database table error"""
        response = service.analyze_error(
            error_message='relation "users" does not exist'
        )
        
        assert response.category == ErrorCategory.DATABASE_ERROR
        assert response.severity == ErrorSeverity.CRITICAL
        assert "Database Not Initialized" in response.title
        assert response.contact_admin is True
        assert "Contact admin to run database migrations" in response.next_steps
    
    def test_provider_unavailable_classification(self, service):
        """Test classification of provider unavailable error"""
        response = service.analyze_error(
            error_message="Service unavailable: 503 error",
            status_code=503,
            provider_name="OpenAI"
        )
        
        assert response.category == ErrorCategory.PROVIDER_DOWN
        assert response.severity == ErrorSeverity.HIGH
        assert "Service Temporarily Unavailable" in response.title
        assert response.retry_after == 180
        assert "Try again in a few minutes" in response.next_steps
    
    def test_network_timeout_classification(self, service):
        """Test classification of network timeout error"""
        response = service.analyze_error(
            error_message="Request timeout after 30 seconds",
            status_code=504
        )
        
        assert response.category == ErrorCategory.NETWORK_ERROR
        assert response.severity == ErrorSeverity.MEDIUM
        assert "Request Timeout" in response.title
        assert response.retry_after == 60
        assert "Check your internet connection" in response.next_steps
    
    def test_validation_error_classification(self, service):
        """Test classification of validation error"""
        response = service.analyze_error(
            error_message="Validation failed: required field missing",
            status_code=400
        )
        
        assert response.category == ErrorCategory.VALIDATION_ERROR
        assert response.severity == ErrorSeverity.LOW
        assert "Invalid Input" in response.title
        assert "Check that all required fields are filled" in response.next_steps
    
    def test_invalid_api_key_classification(self, service):
        """Test classification of invalid API key error"""
        response = service.analyze_error(
            error_message="Invalid API key provided",
            status_code=401,
            provider_name="OpenAI"
        )
        
        assert response.category == ErrorCategory.API_KEY_INVALID
        assert response.severity == ErrorSeverity.HIGH
        assert "Invalid API Key" in response.title
        assert "Verify your OpenAI API key is correct" in response.next_steps
    
    def test_unclassified_error_fallback(self, service):
        """Test fallback response for unclassified errors"""
        response = service.analyze_error(
            error_message="Some completely unknown error occurred"
        )
        
        assert response.category == ErrorCategory.UNKNOWN
        assert response.severity == ErrorSeverity.MEDIUM
        assert "Unexpected Error" in response.title
        assert response.contact_admin is True
        assert response.technical_details is not None
        assert "Try refreshing the page" in response.next_steps
    
    def test_error_with_additional_context(self, service):
        """Test error analysis with additional context"""
        additional_context = {
            "user_id": "user123",
            "request_id": "req456"
        }
        
        response = service.analyze_error(
            error_message="Token has expired",
            additional_context=additional_context
        )
        
        assert response.category == ErrorCategory.AUTHENTICATION
        # Context should be stored but not affect classification
        assert isinstance(response, IntelligentErrorResponse)
    
    def test_add_classification_rule(self, service):
        """Test adding a new classification rule"""
        initial_count = len(service.classification_rules)
        
        new_rule = ErrorClassificationRule(
            name="custom_rule",
            patterns=[r"custom.*error"],
            category=ErrorCategory.SYSTEM_ERROR,
            severity=ErrorSeverity.LOW,
            title_template="Custom Error",
            summary_template="A custom error occurred",
            next_steps=["Custom step"]
        )
        
        service.add_classification_rule(new_rule)
        
        assert len(service.classification_rules) == initial_count + 1
        
        # Test that the new rule works
        response = service.analyze_error("Custom error occurred")
        assert response.category == ErrorCategory.SYSTEM_ERROR
        assert "Custom Error" in response.title
    
    def test_remove_classification_rule(self, service):
        """Test removing a classification rule"""
        # Add a rule first
        test_rule = ErrorClassificationRule(
            name="removable_rule",
            patterns=[r"removable.*error"],
            category=ErrorCategory.SYSTEM_ERROR,
            severity=ErrorSeverity.LOW,
            title_template="Removable Error",
            summary_template="A removable error",
            next_steps=["Remove step"]
        )
        
        service.add_classification_rule(test_rule)
        initial_count = len(service.classification_rules)
        
        # Remove the rule
        removed = service.remove_classification_rule("removable_rule")
        
        assert removed is True
        assert len(service.classification_rules) == initial_count - 1
        
        # Try to remove non-existent rule
        removed = service.remove_classification_rule("non_existent_rule")
        assert removed is False
    
    def test_get_error_statistics(self, service):
        """Test getting error statistics"""
        stats = service.get_error_statistics()
        
        assert "total_rules" in stats
        assert "categories" in stats
        assert "cache_size" in stats
        assert stats["total_rules"] > 0
        assert len(stats["categories"]) == len(ErrorCategory)


class TestErrorContext:
    """Test error context data structure"""
    
    def test_error_context_creation(self):
        """Test creating error context"""
        context = ErrorContext(
            error_message="Test error",
            error_type="TestException",
            status_code=500,
            provider_name="TestProvider"
        )
        
        assert context.error_message == "Test error"
        assert context.error_type == "TestException"
        assert context.status_code == 500
        assert context.provider_name == "TestProvider"
    
    def test_error_context_with_timestamp(self):
        """Test error context with timestamp"""
        timestamp = datetime.utcnow()
        context = ErrorContext(
            error_message="Test error",
            timestamp=timestamp
        )
        
        assert context.timestamp == timestamp


class TestResponseFormatting:
    """Test response formatting utilities"""
    
    def test_format_error_for_user(self):
        """Test formatting error response for user consumption"""
        response = IntelligentErrorResponse(
            title="Test Error",
            summary="A test error occurred",
            category=ErrorCategory.SYSTEM_ERROR,
            severity=ErrorSeverity.MEDIUM,
            next_steps=["Step 1", "Step 2"],
            contact_admin=True,
            retry_after=300,
            help_url="https://example.com/help"
        )
        
        formatted = format_error_for_user(response)
        
        assert formatted["title"] == "Test Error"
        assert formatted["message"] == "A test error occurred"
        assert formatted["severity"] == "medium"
        assert formatted["next_steps"] == ["Step 1", "Step 2"]
        assert formatted["contact_admin"] is True
        assert formatted["retry_after"] == 300
        assert formatted["help_url"] == "https://example.com/help"
    
    def test_format_error_for_api(self):
        """Test formatting error response for API consumption"""
        response = IntelligentErrorResponse(
            title="API Error",
            summary="An API error occurred",
            category=ErrorCategory.API_KEY_MISSING,
            severity=ErrorSeverity.HIGH,
            next_steps=["Add API key"],
            provider_health={"status": "unhealthy"},
            technical_details="Technical info"
        )
        
        formatted = format_error_for_api(response)
        
        assert formatted["error"] == "API Error"
        assert formatted["message"] == "An API error occurred"
        assert formatted["category"] == "api_key_missing"
        assert formatted["severity"] == "high"
        assert formatted["next_steps"] == ["Add API key"]
        assert formatted["provider_health"] == {"status": "unhealthy"}
        assert formatted["technical_details"] == "Technical info"


class TestIntelligentErrorResponse:
    """Test the intelligent error response model"""
    
    def test_response_model_creation(self):
        """Test creating an intelligent error response"""
        response = IntelligentErrorResponse(
            title="Test Title",
            summary="Test summary",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            next_steps=["Step 1", "Step 2"]
        )
        
        assert response.title == "Test Title"
        assert response.summary == "Test summary"
        assert response.category == ErrorCategory.AUTHENTICATION
        assert response.severity == ErrorSeverity.HIGH
        assert response.next_steps == ["Step 1", "Step 2"]
        assert response.contact_admin is False  # Default value
        assert response.retry_after is None  # Default value
    
    def test_response_model_with_optional_fields(self):
        """Test creating response with optional fields"""
        response = IntelligentErrorResponse(
            title="Test Title",
            summary="Test summary",
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            next_steps=["Wait"],
            contact_admin=True,
            retry_after=600,
            help_url="https://help.example.com",
            technical_details="Debug info"
        )
        
        assert response.contact_admin is True
        assert response.retry_after == 600
        assert response.help_url == "https://help.example.com"
        assert response.technical_details == "Debug info"


if __name__ == "__main__":
    pytest.main([__file__])