"""
Integration tests for Error Response Service with AI Orchestrator
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from ai_karen_engine.services.error_response_service import (
    ErrorResponseService,
    ErrorContext,
    ErrorCategory,
    ErrorSeverity
)


class TestErrorResponseAIOrchestorIntegration:
    """Test integration between Error Response Service and AI Orchestrator"""
    
    @pytest.fixture
    def service(self):
        """Create an error response service instance"""
        return ErrorResponseService()
    
    @pytest.fixture
    def mock_ai_orchestrator(self):
        """Mock AI orchestrator with async methods"""
        mock_orchestrator = Mock()
        mock_orchestrator._initialized = True
        
        # Mock async methods
        mock_orchestrator.process_flow = AsyncMock()
        mock_orchestrator.conversation_processing_flow = AsyncMock()
        mock_orchestrator._enhance_response_with_llm = AsyncMock()
        
        return mock_orchestrator
    
    @pytest.fixture
    def mock_flow_input(self):
        """Mock flow input for AI orchestrator"""
        from ai_karen_engine.models.shared_types import FlowInput
        return FlowInput(
            prompt="Test error analysis",
            user_id="test_user",
            session_id="test_session"
        )
    
    @pytest.fixture
    def mock_flow_output(self):
        """Mock flow output from AI orchestrator"""
        from ai_karen_engine.models.shared_types import FlowOutput, AiData
        return FlowOutput(
            response="AI-generated error analysis and guidance",
            requires_plugin=False,
            ai_data=AiData(
                confidence=0.85,
                reasoning="Error analysis completed successfully"
            )
        )
    
    @pytest.mark.asyncio
    async def test_ai_orchestrator_initialization(self, service):
        """Test AI orchestrator lazy initialization"""
        # Mock the AI orchestrator class
        with patch('ai_karen_engine.services.ai_orchestrator.ai_orchestrator.AIOrchestrator') as mock_orchestrator_class:
            with patch('ai_karen_engine.core.services.base.ServiceConfig') as mock_config_class:
                mock_orchestrator = Mock()
                mock_orchestrator._initialized = True
                mock_orchestrator_class.return_value = mock_orchestrator
                
                # First call should initialize
                orchestrator = service._get_ai_orchestrator()
                assert orchestrator is not None
                assert orchestrator._initialized is True
                
                # Second call should return cached instance
                orchestrator2 = service._get_ai_orchestrator()
                assert orchestrator2 is orchestrator
                
                # Should only initialize once
                mock_orchestrator_class.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ai_orchestrator_error_analysis_flow(self, service, mock_ai_orchestrator, mock_flow_output):
        """Test using AI orchestrator for error analysis flow"""
        service._ai_orchestrator = mock_ai_orchestrator
        
        # Mock the flow execution
        mock_ai_orchestrator.conversation_processing_flow.return_value = mock_flow_output
        
        # Create error context
        context = ErrorContext(
            error_message="Complex system error requiring AI analysis",
            error_type="SystemError",
            status_code=500,
            additional_data={"complexity": "high"}
        )
        
        # This would be called by the enhanced AI analysis method
        # For now, we'll test the orchestrator integration directly
        orchestrator = service._get_ai_orchestrator()
        assert orchestrator is not None
    
    def test_ai_orchestrator_fallback_on_failure(self, service):
        """Test fallback when AI orchestrator fails to initialize"""
        # Mock failed initialization
        with patch('ai_karen_engine.services.ai_orchestrator.ai_orchestrator.AIOrchestrator') as mock_orchestrator_class:
            mock_orchestrator_class.side_effect = Exception("Failed to initialize AI orchestrator")
            
            orchestrator = service._get_ai_orchestrator()
            assert orchestrator is None
            
            # Service should still work without AI orchestrator
            response = service.analyze_error(
                error_message="Test error",
                use_ai_analysis=True
            )
            assert response is not None
    
    def test_prompt_template_integration(self, service):
        """Test integration with AI orchestrator prompt templates"""
        # Test that error analysis prompts are properly formatted
        context = ErrorContext(
            error_message="Authentication failed",
            error_type="AuthError",
            status_code=401,
            provider_name="OAuth"
        )
        
        analysis_context = service._build_error_analysis_context(context)
        prompt = service._build_error_analysis_prompt(context, analysis_context)
        
        # Verify prompt contains key elements for AI orchestrator
        assert "Authentication failed" in prompt
        assert "AuthError" in prompt
        assert "OAuth" in prompt
        assert "JSON format" in prompt
        assert "actionable" in prompt.lower()
        
        # Verify prompt follows AI orchestrator prompt template structure
        assert "Error Details:" in prompt
        assert "Guidelines:" in prompt
        assert "next_steps" in prompt
    
    def test_context_enrichment_for_ai_orchestrator(self, service):
        """Test context enrichment for AI orchestrator processing"""
        context = ErrorContext(
            error_message="Provider timeout error",
            provider_name="OpenAI",
            status_code=504,
            additional_data={
                "request_id": "req_123",
                "user_context": "premium_user"
            }
        )
        
        # Mock provider health
        with patch.object(service, '_get_provider_health') as mock_health:
            mock_health_info = Mock()
            mock_health_info.name = "OpenAI"
            mock_health_info.status.value = "degraded"
            mock_health_info.success_rate = 75.0
            mock_health_info.response_time = 8000
            mock_health_info.error_message = "High latency detected"
            mock_health.return_value = mock_health_info
            
            # Mock alternative providers
            with patch('ai_karen_engine.services.error_response_service.get_health_monitor') as mock_monitor:
                mock_monitor_instance = Mock()
                mock_monitor_instance.get_alternative_providers.return_value = ["Anthropic", "Gemini"]
                mock_monitor.return_value = mock_monitor_instance
                
                analysis_context = service._build_error_analysis_context(context)
                
                # Verify enriched context for AI orchestrator
                assert analysis_context["provider_health"]["name"] == "OpenAI"
                assert analysis_context["provider_health"]["status"] == "degraded"
                assert analysis_context["provider_health"]["success_rate"] == 75.0
                assert analysis_context["alternative_providers"] == ["Anthropic", "Gemini"]
                assert analysis_context["request_id"] == "req_123"
                assert analysis_context["user_context"] == "premium_user"
    
    def test_ai_orchestrator_response_validation(self, service):
        """Test validation of AI orchestrator responses"""
        # Test valid AI orchestrator-style response
        valid_ai_response = """{
            "title": "Provider Timeout - Service Degraded",
            "summary": "The OpenAI service is experiencing high latency and timeouts. This is affecting response times across the system.",
            "category": "provider_down",
            "severity": "high",
            "next_steps": [
                "Try using Anthropic as an alternative provider",
                "Wait 2-3 minutes for OpenAI service to recover",
                "Check OpenAI status page for updates",
                "Contact admin if timeouts persist beyond 10 minutes"
            ],
            "contact_admin": false,
            "retry_after": 180,
            "technical_details": "Provider health shows 75% success rate with 8000ms average response time"
        }"""
        
        context = ErrorContext(
            error_message="Provider timeout",
            provider_name="OpenAI"
        )
        
        parsed_response = service._parse_ai_error_response(valid_ai_response, context)
        
        assert parsed_response is not None
        assert parsed_response.title == "Provider Timeout - Service Degraded"
        assert parsed_response.category == ErrorCategory.PROVIDER_DOWN
        assert parsed_response.severity == ErrorSeverity.HIGH
        assert len(parsed_response.next_steps) == 4
        assert parsed_response.retry_after == 180
        
        # Validate response quality
        assert service.validate_response_quality(parsed_response) is True
    
    def test_ai_orchestrator_enhancement_integration(self, service):
        """Test AI orchestrator enhancement of rule-based responses"""
        from ai_karen_engine.services.error_response_service import IntelligentErrorResponse
        
        # Create base rule-based response
        base_response = IntelligentErrorResponse(
            title="Rate Limit Exceeded",
            summary="You've exceeded the rate limit for OpenAI.",
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            next_steps=[
                "Wait a few minutes before trying again",
                "Consider upgrading your OpenAI plan"
            ]
        )
        
        # Mock AI orchestrator enhancement
        ai_enhancement = """{
            "title": "OpenAI Rate Limit - Upgrade Recommended",
            "summary": "You've hit OpenAI's rate limit. Based on your usage pattern, upgrading to a higher tier would prevent future interruptions.",
            "next_steps": [
                "Wait 5 minutes for rate limit to reset",
                "Upgrade to OpenAI Pro for 5x higher limits",
                "Consider using Anthropic Claude as backup",
                "Implement request queuing to smooth traffic spikes"
            ],
            "additional_insights": "Your current usage suggests you need at least Tier 2 limits"
        }"""
        
        context = ErrorContext(
            error_message="Rate limit exceeded",
            provider_name="OpenAI"
        )
        
        enhanced_response = service._merge_ai_enhancement(base_response, ai_enhancement, context)
        
        assert enhanced_response is not None
        assert "Upgrade Recommended" in enhanced_response.title
        assert "usage pattern" in enhanced_response.summary
        assert len(enhanced_response.next_steps) == 4
        assert any("request queuing" in step for step in enhanced_response.next_steps)
        assert "AI Insights:" in enhanced_response.technical_details
        assert "Tier 2 limits" in enhanced_response.technical_details
    
    def test_ai_orchestrator_error_categorization(self, service):
        """Test AI orchestrator's ability to categorize complex errors"""
        # Test complex error that might be hard to classify with rules
        complex_error_response = """{
            "title": "Multi-Service Authentication Chain Failure",
            "summary": "Authentication failed due to a cascade of service dependencies. OAuth provider is healthy, but token validation service is experiencing issues.",
            "category": "authentication",
            "severity": "high",
            "next_steps": [
                "Check token validation service status",
                "Verify OAuth provider configuration",
                "Try logging in again in 2-3 minutes",
                "Contact admin if authentication continues to fail"
            ],
            "contact_admin": false,
            "retry_after": 120,
            "technical_details": "OAuth token received but validation service returned 503"
        }"""
        
        context = ErrorContext(
            error_message="Authentication chain failure: OAuth token validation failed with service unavailable",
            error_type="AuthenticationChainError",
            status_code=503
        )
        
        parsed_response = service._parse_ai_error_response(complex_error_response, context)
        
        assert parsed_response is not None
        assert parsed_response.category == ErrorCategory.AUTHENTICATION
        assert "Multi-Service" in parsed_response.title
        assert "cascade of service dependencies" in parsed_response.summary
        assert parsed_response.retry_after == 120
        
        # This type of complex analysis would be difficult with rule-based classification
        assert "token validation service" in parsed_response.summary
    
    def test_ai_orchestrator_provider_health_integration(self, service):
        """Test AI orchestrator integration with provider health monitoring"""
        context = ErrorContext(
            error_message="Service temporarily unavailable",
            provider_name="OpenAI",
            status_code=503
        )
        
        # Mock provider health with detailed status
        with patch.object(service, '_get_provider_health') as mock_health:
            mock_health_info = Mock()
            mock_health_info.name = "OpenAI"
            mock_health_info.status.value = "unhealthy"
            mock_health_info.success_rate = 15.0
            mock_health_info.response_time = 15000
            mock_health_info.error_message = "Multiple service endpoints failing"
            mock_health_info.last_check = Mock()
            mock_health_info.last_check.isoformat.return_value = "2024-01-01T12:00:00Z"
            mock_health.return_value = mock_health_info
            
            analysis_context = service._build_error_analysis_context(context)
            
            # Verify provider health is properly integrated
            provider_health = analysis_context["provider_health"]
            assert provider_health["name"] == "OpenAI"
            assert provider_health["status"] == "unhealthy"
            assert provider_health["success_rate"] == 15.0
            assert provider_health["response_time"] == 15000
            assert provider_health["error_message"] == "Multiple service endpoints failing"
            assert provider_health["last_check"] == "2024-01-01T12:00:00Z"
    
    def test_ai_orchestrator_metrics_collection(self, service):
        """Test metrics collection for AI orchestrator integration"""
        metrics = service.get_ai_analysis_metrics()
        
        # Verify AI orchestrator metrics are included
        assert "ai_orchestrator_available" in metrics
        assert isinstance(metrics["ai_orchestrator_available"], bool)
        
        # Test with mocked AI orchestrator
        with patch.object(service, '_get_ai_orchestrator') as mock_get_orchestrator:
            mock_orchestrator = Mock()
            mock_orchestrator._initialized = True
            mock_get_orchestrator.return_value = mock_orchestrator
            
            metrics = service.get_ai_analysis_metrics()
            assert metrics["ai_orchestrator_available"] is True
        
        # Test with failed AI orchestrator
        with patch.object(service, '_get_ai_orchestrator', return_value=None):
            metrics = service.get_ai_analysis_metrics()
            assert metrics["ai_orchestrator_available"] is False


if __name__ == "__main__":
    pytest.main([__file__])