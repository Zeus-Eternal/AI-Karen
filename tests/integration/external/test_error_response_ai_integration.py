"""
Tests for AI integration in Error Response Service
"""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from ai_karen_engine.services.error_response_service import (
    ErrorResponseService,
    ErrorContext,
    ErrorCategory,
    ErrorSeverity,
    IntelligentErrorResponse
)


class TestErrorResponseAIIntegration:
    """Test AI integration features of the error response service"""
    
    @pytest.fixture
    def service(self):
        """Create an error response service instance"""
        return ErrorResponseService()
    
    @pytest.fixture
    def mock_llm_router(self):
        """Mock LLM router"""
        mock_router = Mock()
        mock_router.invoke = Mock()
        return mock_router
    
    @pytest.fixture
    def mock_llm_utils(self):
        """Mock LLM utils"""
        return Mock()
    
    @pytest.fixture
    def mock_ai_orchestrator(self):
        """Mock AI orchestrator"""
        mock_orchestrator = Mock()
        mock_orchestrator._initialized = True
        return mock_orchestrator
    
    def test_lazy_initialization_of_ai_components(self, service):
        """Test that AI components are lazily initialized"""
        # Initially should be None
        assert service._ai_orchestrator is None
        assert service._llm_router is None
        assert service._llm_utils is None
        
        # Should attempt to initialize when accessed
        with patch('ai_karen_engine.services.ai_orchestrator.ai_orchestrator.AIOrchestrator') as mock_orchestrator_class:
            with patch('ai_karen_engine.core.services.base.ServiceConfig') as mock_config_class:
                mock_orchestrator = Mock()
                mock_orchestrator._initialized = True
                mock_orchestrator_class.return_value = mock_orchestrator
                
                orchestrator = service._get_ai_orchestrator()
                assert orchestrator is not None
                mock_orchestrator_class.assert_called_once()
    
    def test_ai_error_analysis_with_valid_response(self, service, mock_llm_router, mock_llm_utils):
        """Test AI error analysis with valid LLM response"""
        # Mock the LLM components
        service._llm_router = mock_llm_router
        service._llm_utils = mock_llm_utils
        
        # Mock AI response
        ai_response = json.dumps({
            "title": "AI-Generated Error Title",
            "summary": "AI-generated explanation of the error",
            "category": "system_error",
            "severity": "medium",
            "next_steps": [
                "Try restarting the service",
                "Check system logs for details",
                "Contact admin if issue persists"
            ],
            "contact_admin": False,
            "technical_details": "AI-generated technical context"
        })
        
        mock_llm_router.invoke.return_value = ai_response
        
        # Test AI analysis
        context = ErrorContext(
            error_message="Unknown system error occurred",
            error_type="SystemError"
        )
        
        response = service._generate_ai_error_response(context)
        
        assert response is not None
        assert response.title == "AI-Generated Error Title"
        assert response.summary == "AI-generated explanation of the error"
        assert response.category == ErrorCategory.SYSTEM_ERROR
        assert response.severity == ErrorSeverity.MEDIUM
        assert len(response.next_steps) == 3
        assert "Try restarting the service" in response.next_steps
        
        # Verify LLM was called with correct parameters
        mock_llm_router.invoke.assert_called_once()
        call_args = mock_llm_router.invoke.call_args
        assert call_args[0][0] == mock_llm_utils  # llm_utils
        assert "Unknown system error occurred" in call_args[0][1]  # prompt
        assert call_args[1]["task_intent"] == "analysis"
        assert call_args[1]["preferred_provider"] == "openai"
    
    def test_ai_error_analysis_with_invalid_json(self, service, mock_llm_router, mock_llm_utils):
        """Test AI error analysis with invalid JSON response"""
        service._llm_router = mock_llm_router
        service._llm_utils = mock_llm_utils
        
        # Mock invalid AI response
        mock_llm_router.invoke.return_value = "This is not valid JSON"
        
        context = ErrorContext(
            error_message="Test error",
            error_type="TestError"
        )
        
        response = service._generate_ai_error_response(context)
        
        assert response is None
    
    def test_ai_error_analysis_with_missing_fields(self, service, mock_llm_router, mock_llm_utils):
        """Test AI error analysis with missing required fields"""
        service._llm_router = mock_llm_router
        service._llm_utils = mock_llm_utils
        
        # Mock AI response missing required fields
        ai_response = json.dumps({
            "title": "Incomplete Response",
            "summary": "Missing required fields"
            # Missing category, severity, next_steps
        })
        
        mock_llm_router.invoke.return_value = ai_response
        
        context = ErrorContext(
            error_message="Test error",
            error_type="TestError"
        )
        
        response = service._generate_ai_error_response(context)
        
        assert response is None
    
    def test_ai_error_analysis_with_invalid_category(self, service, mock_llm_router, mock_llm_utils):
        """Test AI error analysis with invalid category value"""
        service._llm_router = mock_llm_router
        service._llm_utils = mock_llm_utils
        
        # Mock AI response with invalid category
        ai_response = json.dumps({
            "title": "Test Error",
            "summary": "Test summary",
            "category": "invalid_category",
            "severity": "medium",
            "next_steps": ["Step 1"]
        })
        
        mock_llm_router.invoke.return_value = ai_response
        
        context = ErrorContext(
            error_message="Test error",
            error_type="TestError"
        )
        
        response = service._generate_ai_error_response(context)
        
        assert response is None
    
    def test_ai_response_enhancement(self, service, mock_llm_router, mock_llm_utils):
        """Test AI enhancement of rule-based responses"""
        service._llm_router = mock_llm_router
        service._llm_utils = mock_llm_utils
        
        # Create base response
        base_response = IntelligentErrorResponse(
            title="Base Error Title",
            summary="Base error summary",
            category=ErrorCategory.API_KEY_MISSING,
            severity=ErrorSeverity.HIGH,
            next_steps=["Add API key", "Restart service"]
        )
        
        # Mock AI enhancement response
        ai_enhancement = json.dumps({
            "title": "Enhanced Error Title",
            "summary": "Enhanced error summary with more context",
            "next_steps": [
                "Add OPENAI_API_KEY to your .env file",
                "Get your API key from https://platform.openai.com/api-keys",
                "Restart the application after adding the key"
            ],
            "additional_insights": "This error commonly occurs during initial setup"
        })
        
        mock_llm_router.invoke.return_value = ai_enhancement
        
        context = ErrorContext(
            error_message="API key missing",
            provider_name="OpenAI"
        )
        
        enhanced_response = service._enhance_response_with_ai(base_response, context)
        
        assert enhanced_response is not None
        assert enhanced_response.title == "Enhanced Error Title"
        assert enhanced_response.summary == "Enhanced error summary with more context"
        assert len(enhanced_response.next_steps) == 3
        assert "Add OPENAI_API_KEY to your .env file" in enhanced_response.next_steps
        assert "AI Insights:" in enhanced_response.technical_details
    
    def test_analyze_error_with_ai_enabled(self, service, mock_llm_router, mock_llm_utils):
        """Test error analysis with AI enhancement enabled"""
        service._llm_router = mock_llm_router
        service._llm_utils = mock_llm_utils
        
        # Mock AI enhancement for a classified error
        ai_enhancement = json.dumps({
            "title": "Enhanced OpenAI API Key Missing",
            "summary": "Enhanced summary with provider status",
            "next_steps": [
                "Add OPENAI_API_KEY to your .env file",
                "Get your API key from https://platform.openai.com/api-keys",
                "Verify your account has sufficient credits"
            ],
            "additional_insights": "Check your OpenAI account status"
        })
        
        mock_llm_router.invoke.return_value = ai_enhancement
        
        # Test with a classifiable error
        response = service.analyze_error(
            error_message="OPENAI_API_KEY not set in environment",
            provider_name="OpenAI",
            use_ai_analysis=True
        )
        
        assert response is not None
        assert "Enhanced" in response.title
        assert len(response.next_steps) >= 2
        
        # Verify AI enhancement was called
        mock_llm_router.invoke.assert_called_once()
    
    def test_analyze_error_with_ai_disabled(self, service):
        """Test error analysis with AI disabled"""
        # Test with AI disabled
        response = service.analyze_error(
            error_message="OPENAI_API_KEY not set in environment",
            provider_name="OpenAI",
            use_ai_analysis=False
        )
        
        assert response is not None
        assert response.category == ErrorCategory.API_KEY_MISSING
        # Should be the standard rule-based response
        assert "OpenAI API Key Missing" in response.title
    
    def test_analyze_unclassified_error_with_ai(self, service, mock_llm_router, mock_llm_utils):
        """Test analysis of unclassified error with AI"""
        service._llm_router = mock_llm_router
        service._llm_utils = mock_llm_utils
        
        # Mock AI response for unclassified error
        ai_response = json.dumps({
            "title": "AI-Analyzed Custom Error",
            "summary": "AI analysis of the custom error",
            "category": "system_error",
            "severity": "medium",
            "next_steps": [
                "Check application logs",
                "Verify system configuration",
                "Contact support if needed"
            ],
            "contact_admin": False
        })
        
        mock_llm_router.invoke.return_value = ai_response
        
        # Test with unclassifiable error
        response = service.analyze_error(
            error_message="Custom application error XYZ123",
            use_ai_analysis=True
        )
        
        assert response is not None
        assert response.title == "AI-Analyzed Custom Error"
        assert response.category == ErrorCategory.SYSTEM_ERROR
        assert len(response.next_steps) == 3
    
    def test_build_error_analysis_context(self, service):
        """Test building context for AI error analysis"""
        context = ErrorContext(
            error_message="Test error",
            provider_name="OpenAI",
            status_code=500,
            timestamp=datetime.utcnow(),
            additional_data={"user_id": "test123"}
        )
        
        with patch.object(service, '_get_provider_health') as mock_health:
            mock_health_info = Mock()
            mock_health_info.name = "OpenAI"
            mock_health_info.status.value = "healthy"
            mock_health_info.success_rate = 95.5
            mock_health_info.response_time = 150
            mock_health_info.error_message = None
            mock_health.return_value = mock_health_info
            
            analysis_context = service._build_error_analysis_context(context)
            
            assert analysis_context["timestamp"] is not None
            assert analysis_context["provider_health"]["name"] == "OpenAI"
            assert analysis_context["provider_health"]["status"] == "healthy"
            assert analysis_context["provider_health"]["success_rate"] == 95.5
            assert analysis_context["user_id"] == "test123"
    
    def test_build_error_analysis_prompt(self, service):
        """Test building AI analysis prompt"""
        context = ErrorContext(
            error_message="Database connection failed",
            error_type="ConnectionError",
            status_code=500,
            provider_name="PostgreSQL"
        )
        
        analysis_context = {
            "provider_health": {
                "name": "PostgreSQL",
                "status": "unhealthy",
                "success_rate": 0,
                "response_time": 5000
            },
            "alternative_providers": ["MySQL", "SQLite"]
        }
        
        prompt = service._build_error_analysis_prompt(context, analysis_context)
        
        assert "Database connection failed" in prompt
        assert "ConnectionError" in prompt
        assert "PostgreSQL" in prompt
        assert "unhealthy" in prompt
        assert "MySQL, SQLite" in prompt
        assert "JSON format" in prompt
        assert "next_steps" in prompt
    
    def test_response_quality_validation(self, service):
        """Test response quality validation"""
        # Valid response
        valid_response = IntelligentErrorResponse(
            title="Valid Error Title",
            summary="This is a comprehensive error summary with enough detail",
            category=ErrorCategory.API_KEY_MISSING,
            severity=ErrorSeverity.HIGH,
            next_steps=[
                "Add your API key to the configuration",
                "Verify the key is correct",
                "Restart the application"
            ]
        )
        
        assert service.validate_response_quality(valid_response) is True
        
        # Invalid response - too short title
        invalid_response = IntelligentErrorResponse(
            title="Bad",
            summary="This is a comprehensive error summary with enough detail",
            category=ErrorCategory.API_KEY_MISSING,
            severity=ErrorSeverity.HIGH,
            next_steps=["Add API key"]
        )
        
        assert service.validate_response_quality(invalid_response) is False
        
        # Invalid response - no actionable steps
        invalid_response2 = IntelligentErrorResponse(
            title="Valid Error Title",
            summary="This is a comprehensive error summary with enough detail",
            category=ErrorCategory.API_KEY_MISSING,
            severity=ErrorSeverity.HIGH,
            next_steps=["Something went wrong", "Error occurred"]
        )
        
        assert service.validate_response_quality(invalid_response2) is False
        
        # Invalid response - critical severity without contact_admin for database error
        invalid_response3 = IntelligentErrorResponse(
            title="Database Error",
            summary="Database connection failed completely",
            category=ErrorCategory.DATABASE_ERROR,
            severity=ErrorSeverity.CRITICAL,
            next_steps=["Check database"],
            contact_admin=False
        )
        
        assert service.validate_response_quality(invalid_response3) is False
    
    def test_ai_analysis_metrics(self, service):
        """Test AI analysis metrics collection"""
        metrics = service.get_ai_analysis_metrics()
        
        assert "ai_analysis_enabled" in metrics
        assert "ai_orchestrator_available" in metrics
        assert "llm_utils_available" in metrics
        assert "total_classification_rules" in metrics
        assert isinstance(metrics["total_classification_rules"], int)
    
    def test_ai_components_failure_handling(self, service):
        """Test graceful handling of AI component failures"""
        # Mock failed initialization
        with patch.object(service, '_get_llm_router', return_value=None):
            with patch.object(service, '_get_llm_utils', return_value=None):
                context = ErrorContext(
                    error_message="Test error",
                    error_type="TestError"
                )
                
                # Should return None gracefully
                response = service._generate_ai_error_response(context)
                assert response is None
                
                # Should still work with rule-based classification
                response = service.analyze_error(
                    error_message="OPENAI_API_KEY not set",
                    use_ai_analysis=True
                )
                assert response is not None
                assert response.category == ErrorCategory.API_KEY_MISSING
    
    def test_llm_router_exception_handling(self, service, mock_llm_router, mock_llm_utils):
        """Test handling of LLM router exceptions"""
        service._llm_router = mock_llm_router
        service._llm_utils = mock_llm_utils
        
        # Mock LLM router to raise exception
        mock_llm_router.invoke.side_effect = Exception("LLM service unavailable")
        
        context = ErrorContext(
            error_message="Test error",
            error_type="TestError"
        )
        
        # Should handle exception gracefully
        response = service._generate_ai_error_response(context)
        assert response is None
    
    def test_json_parsing_with_code_blocks(self, service, mock_llm_router, mock_llm_utils):
        """Test parsing AI responses wrapped in code blocks"""
        service._llm_router = mock_llm_router
        service._llm_utils = mock_llm_utils
        
        # Mock AI response wrapped in code blocks
        ai_response = """```json
{
    "title": "Code Block Response",
    "summary": "Response wrapped in code blocks",
    "category": "system_error",
    "severity": "medium",
    "next_steps": ["Step 1", "Step 2"]
}
```"""
        
        mock_llm_router.invoke.return_value = ai_response
        
        context = ErrorContext(
            error_message="Test error",
            error_type="TestError"
        )
        
        response = service._generate_ai_error_response(context)
        
        assert response is not None
        assert response.title == "Code Block Response"
        assert response.summary == "Response wrapped in code blocks"


if __name__ == "__main__":
    pytest.main([__file__])