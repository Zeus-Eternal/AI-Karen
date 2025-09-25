"""
Tests for Enhanced Error Handling with AG-UI and CopilotKit Fallbacks

This test suite validates the enhanced error handling middleware and
fallback mechanisms for AG-UI components and CopilotKit integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone

# Test the enhanced error middleware
from src.ai_karen_engine.server.enhanced_error_middleware import (
    EnhancedErrorMiddleware,
    EnhancedErrorHandler,
    ErrorRecoveryConfig,
    ErrorType,
    FallbackStrategy,
    CircuitBreakerState
)

# Test the CopilotKit error handler
from src.ai_karen_engine.copilotkit.error_handler import (
    CopilotKitFallbackHandler,
    CopilotKitErrorType
)

# Test the hook error recovery
from src.ai_karen_engine.hooks.error_recovery import (
    HookErrorRecoveryManager,
    HookErrorType,
    RecoveryStrategy,
    CircuitBreakerConfig,
    RetryConfig
)


class TestEnhancedErrorHandler:
    """Test the enhanced error handler with AG-UI and CopilotKit fallbacks."""
    
    @pytest.fixture
    def error_handler(self):
        """Create error handler instance."""
        config = ErrorRecoveryConfig()
        return EnhancedErrorHandler(config)
    
    @pytest.fixture
    def mock_llm_orchestrator(self):
        """Mock LLM orchestrator."""
        mock = AsyncMock()
        mock.enhanced_route.return_value = "Fallback response"
        mock.route_with_copilotkit.return_value = "CopilotKit fallback response"
        return mock
    
    @pytest.fixture
    def mock_hook_manager(self):
        """Mock hook manager."""
        mock = AsyncMock()
        mock.trigger_hooks.return_value = Mock(successful_hooks=1, total_hooks=1)
        return mock
    
    @pytest.mark.asyncio
    async def test_handle_ag_ui_grid_error(self, error_handler):
        """Test AG-UI grid error handling."""
        error = Exception("Grid rendering failed")
        context = {
            "data": [{"id": 1, "name": "test"}],
            "columns": [{"field": "id"}, {"field": "name"}]
        }
        
        result = await error_handler.handle_ag_ui_error(error, "grid", context)
        
        assert result["fallback_type"] == "simple_table"
        assert result["component"] == "SimpleTable"
        assert result["retry_available"] is True
        assert "grid rendering failed" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_handle_ag_ui_chart_error(self, error_handler):
        """Test AG-UI chart error handling."""
        error = Exception("Chart data rendering failed")
        context = {
            "data": [{"label": "A", "value": 10}]
        }
        
        result = await error_handler.handle_ag_ui_error(error, "chart", context)
        
        assert result["fallback_type"] == "simple_chart"
        assert result["component"] == "SimpleChart"
        assert result["retry_available"] is True
    
    @pytest.mark.asyncio
    async def test_handle_ag_ui_data_load_error_with_cache(self, error_handler):
        """Test AG-UI data load error with cached data."""
        # Pre-populate cache
        cache_key = f"ag_ui_data_grid_{hash(str({}))}"
        error_handler.error_cache[cache_key] = {
            "data": [{"id": 1, "cached": True}],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        error = Exception("Data loading failed")
        context = {}
        
        result = await error_handler.handle_ag_ui_error(error, "grid", context)
        
        assert result["fallback_type"] == "cached_data"
        assert result["data"][0]["cached"] is True
        assert "cached data" in result["warning"].lower()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self, error_handler):
        """Test circuit breaker opens after threshold failures."""
        error = Exception("Repeated failure")
        context = {"data": []}
        
        # Trigger multiple failures to open circuit breaker
        for _ in range(6):  # Exceeds default threshold of 5
            await error_handler.handle_ag_ui_error(error, "grid", context)
        
        # Check circuit breaker is open
        circuit_breaker = error_handler.circuit_breakers.get("ag_ui_grid")
        assert circuit_breaker is not None
        assert not circuit_breaker.can_execute()
        
        # Next call should return simplified fallback immediately
        result = await error_handler.handle_ag_ui_error(error, "grid", context)
        assert result["fallback_type"] == "simplified_ui"
    
    @pytest.mark.asyncio
    @patch('src.ai_karen_engine.server.enhanced_error_middleware.get_orchestrator')
    async def test_handle_copilotkit_api_unavailable(self, mock_get_orchestrator, error_handler):
        """Test CopilotKit API unavailable error handling."""
        # Mock the orchestrator
        mock_orchestrator = AsyncMock()
        mock_orchestrator.enhanced_route.return_value = "LLM fallback response"
        mock_get_orchestrator.return_value = mock_orchestrator
        error_handler.llm_orchestrator = mock_orchestrator
        
        error = Exception("CopilotKit API unavailable")
        context = {"prompt": "Help me with code"}
        
        result = await error_handler.handle_copilotkit_error(error, context)
        
        assert result["fallback_type"] == "llm_provider"
        assert result["response"] == "LLM fallback response"
        assert "copilotkit unavailable" in result["warning"].lower()
        
        # Verify LLM orchestrator was called
        mock_orchestrator.enhanced_route.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_copilotkit_context_too_large(self, error_handler):
        """Test CopilotKit context too large error handling."""
        error = Exception("Context too large")
        context = {
            "prompt": "x" * 10000,  # Large prompt
            "conversation_history": [{"role": "user", "content": "msg"}] * 20
        }
        
        with patch.object(error_handler.llm_orchestrator, 'route_with_copilotkit') as mock_route:
            mock_route.return_value = "Truncated response"
            
            result = await error_handler.handle_copilotkit_error(error, context)
            
            assert result["fallback_type"] == "truncated_context"
            assert result["response"] == "Truncated response"
            assert "truncated" in result["warning"].lower()
            
            # Verify context was truncated
            call_args = mock_route.call_args
            truncated_context = call_args[0][1]  # Second argument
            assert len(truncated_context["conversation_history"]) <= 10
    
    @pytest.mark.asyncio
    async def test_handle_copilotkit_rate_limit_with_backoff(self, error_handler):
        """Test CopilotKit rate limit handling with exponential backoff."""
        error = Exception("Rate limit exceeded")
        context = {"prompt": "Test prompt"}
        
        with patch.object(error_handler.llm_orchestrator, 'route_with_copilotkit') as mock_route:
            # First two calls fail, third succeeds
            mock_route.side_effect = [
                Exception("Rate limit"),
                Exception("Rate limit"),
                "Success after backoff"
            ]
            
            with patch('asyncio.sleep') as mock_sleep:
                result = await error_handler.handle_copilotkit_error(error, context)
                
                assert result["fallback_type"] == "retry_after_backoff"
                assert result["response"] == "Success after backoff"
                assert result["attempts"] == 3
                
                # Verify exponential backoff was used
                assert mock_sleep.call_count == 2  # Two delays before success
    
    @pytest.mark.asyncio
    async def test_handle_hook_system_timeout(self, error_handler):
        """Test hook system timeout error handling."""
        error = Exception("Hook execution timeout")
        context = {"hook_data": "test"}
        
        result = await error_handler.handle_hook_system_error(error, "pre_message", context)
        
        assert result["fallback_type"] == "hook_bypass"
        assert result["hook_type"] == "pre_message"
        assert result["status"] == "bypassed"
        assert "timed out" in result["warning"].lower()
    
    @pytest.mark.asyncio
    async def test_handle_llm_provider_fallback_chain(self, error_handler):
        """Test LLM provider fallback chain."""
        error = Exception("Primary provider failed")
        context = {"prompt": "Test prompt"}
        
        with patch.object(error_handler, '_try_fallback_providers') as mock_fallback:
            mock_fallback.return_value = {
                "fallback_type": "provider_fallback",
                "response": "Fallback provider response",
                "provider": "anthropic"
            }
            
            result = await error_handler.handle_llm_provider_error(error, "openai", context)
            
            assert result["fallback_type"] == "provider_fallback"
            assert result["provider"] == "anthropic"
            assert result["response"] == "Fallback provider response"
    
    @pytest.mark.asyncio
    async def test_cached_response_fallback(self, error_handler):
        """Test cached response when all providers fail."""
        # Pre-populate cache
        cache_key = f"response_{hash('test prompt')}"
        error_handler.error_cache[cache_key] = {
            "response": "Cached response",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        error = Exception("All providers failed")
        context = {"prompt": "test prompt"}
        
        with patch.object(error_handler, '_try_fallback_providers') as mock_fallback:
            mock_fallback.side_effect = Exception("All providers failed")
            
            result = await error_handler.handle_llm_provider_error(error, "openai", context)
            
            assert result["fallback_type"] == "cached_response"
            assert result["response"] == "Cached response"


class TestCopilotKitFallbackHandler:
    """Test CopilotKit fallback handler."""
    
    @pytest.fixture
    def fallback_handler(self):
        """Create CopilotKit fallback handler."""
        return CopilotKitFallbackHandler()
    
    @pytest.fixture
    def mock_llm_orchestrator(self):
        """Mock LLM orchestrator."""
        mock = AsyncMock()
        mock.enhanced_route.return_value = "LLM fallback response"
        return mock
    
    @pytest.mark.asyncio
    async def test_handle_code_suggestions_error_with_llm_fallback(self, fallback_handler):
        """Test code suggestions error with LLM fallback."""
        error = Exception("CopilotKit API unavailable")
        code = "def hello():\n    pass"
        
        with patch.object(fallback_handler.llm_orchestrator, 'enhanced_route') as mock_route:
            mock_route.return_value = "1. Add docstring\n2. Add type hints\n3. Implement function body"
            
            result = await fallback_handler.handle_code_suggestions_error(error, code, "python")
            
            assert len(result) > 0
            assert result[0]["type"] == "improvement"
            assert result[0]["language"] == "python"
            assert result[0]["source"] == "llm_fallback"
    
    @pytest.mark.asyncio
    async def test_handle_debugging_assistance_error(self, fallback_handler):
        """Test debugging assistance error handling."""
        error = Exception("CopilotKit debugging unavailable")
        code = "print(undefined_variable)"
        error_message = "NameError: name 'undefined_variable' is not defined"
        
        with patch.object(fallback_handler.llm_orchestrator, 'enhanced_route') as mock_route:
            mock_route.return_value = "The error occurs because 'undefined_variable' is not defined. Define the variable before using it."
            
            result = await fallback_handler.handle_debugging_assistance_error(
                error, code, error_message, "python"
            )
            
            assert result["source"] == "llm_fallback"
            assert result["language"] == "python"
            assert "undefined_variable" in result["analysis"]
    
    @pytest.mark.asyncio
    async def test_handle_contextual_suggestions_error(self, fallback_handler):
        """Test contextual suggestions error handling."""
        error = Exception("CopilotKit suggestions unavailable")
        message = "How do I optimize this code?"
        context = {"language": "python", "file_type": "script"}
        
        with patch.object(fallback_handler.llm_orchestrator, 'enhanced_route') as mock_route:
            mock_route.return_value = "1. Use list comprehensions\n2. Avoid nested loops\n3. Use built-in functions"
            
            result = await fallback_handler.handle_contextual_suggestions_error(
                error, message, context
            )
            
            assert len(result) > 0
            assert result[0]["type"] == "contextual"
            assert result[0]["source"] == "llm_fallback"
    
    @pytest.mark.asyncio
    async def test_generic_fallback_when_llm_fails(self, fallback_handler):
        """Test generic fallback when LLM also fails."""
        error = Exception("CopilotKit API unavailable")
        code = "def test(): pass"
        
        with patch.object(fallback_handler.llm_orchestrator, 'enhanced_route') as mock_route:
            mock_route.side_effect = Exception("LLM also failed")
            
            result = await fallback_handler.handle_code_suggestions_error(error, code, "python")
            
            assert len(result) > 0
            assert result[0]["source"] == "generic_fallback"
            assert result[0]["confidence"] == 0.3
    
    def test_error_classification(self, fallback_handler):
        """Test error classification."""
        # Test API unavailable
        error1 = Exception("API unavailable")
        assert fallback_handler._classify_error(error1) == CopilotKitErrorType.API_UNAVAILABLE
        
        # Test rate limit
        error2 = Exception("Rate limit exceeded")
        assert fallback_handler._classify_error(error2) == CopilotKitErrorType.RATE_LIMIT_EXCEEDED
        
        # Test context too large
        error3 = Exception("Context too large")
        assert fallback_handler._classify_error(error3) == CopilotKitErrorType.CONTEXT_TOO_LARGE
        
        # Test timeout
        error4 = Exception("Request timeout")
        assert fallback_handler._classify_error(error4) == CopilotKitErrorType.TIMEOUT


class TestHookErrorRecoveryManager:
    """Test hook error recovery manager."""
    
    @pytest.fixture
    def recovery_manager(self):
        """Create hook error recovery manager."""
        return HookErrorRecoveryManager()
    
    @pytest.fixture
    def mock_hook_manager(self):
        """Mock hook manager."""
        mock = AsyncMock()
        mock.trigger_hooks.return_value = Mock(successful_hooks=1, total_hooks=1)
        return mock
    
    @pytest.fixture
    def mock_hook_context(self):
        """Mock hook context."""
        from ai_karen_engine.hooks import HookContext
        return HookContext(
            hook_type="test_hook",
            data={"test": "data"},
            user_context={"user_id": "test_user"}
        )
    
    @pytest.mark.asyncio
    async def test_execute_hook_with_retry_strategy(self, recovery_manager, mock_hook_context):
        """Test hook execution with retry strategy."""
        hook_type = "test_hook"
        
        with patch.object(recovery_manager, '_execute_hook_safely') as mock_execute:
            # First call fails, second succeeds
            mock_execute.side_effect = [
                Exception("Temporary failure"),
                {"success": True, "hook_type": hook_type}
            ]
            
            with patch('asyncio.sleep'):  # Mock sleep to speed up test
                result = await recovery_manager.execute_hook_with_recovery(
                    hook_type, mock_hook_context, RecoveryStrategy.RETRY_WITH_BACKOFF
                )
                
                assert result["success"] is True
                assert result["retry_metadata"]["attempts"] == 2
                assert result["retry_metadata"]["strategy"] == "retry_with_backoff"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self, recovery_manager, mock_hook_context):
        """Test circuit breaker opens after threshold failures."""
        hook_type = "test_hook"
        
        with patch.object(recovery_manager, '_execute_hook_safely') as mock_execute:
            mock_execute.side_effect = Exception("Persistent failure")
            
            # Trigger failures to open circuit breaker
            for _ in range(6):  # Exceeds default threshold
                await recovery_manager.execute_hook_with_recovery(
                    hook_type, mock_hook_context, RecoveryStrategy.CIRCUIT_BREAKER
                )
            
            # Check circuit breaker is open
            circuit_breaker = recovery_manager.circuit_breakers.get(hook_type)
            assert circuit_breaker.state == "open"
            
            # Next execution should be bypassed
            result = await recovery_manager.execute_hook_with_recovery(
                hook_type, mock_hook_context, RecoveryStrategy.CIRCUIT_BREAKER
            )
            
            assert result["bypassed"] is True
            assert result["bypass_reason"] == "circuit_breaker_open"
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_strategy(self, recovery_manager, mock_hook_context):
        """Test graceful degradation strategy."""
        hook_type = "test_hook"
        
        with patch.object(recovery_manager, '_execute_hook_safely') as mock_execute:
            mock_execute.side_effect = Exception("Hook failure")
            
            result = await recovery_manager.execute_hook_with_recovery(
                hook_type, mock_hook_context, RecoveryStrategy.GRACEFUL_DEGRADATION
            )
            
            assert result["success"] is True
            assert result["degraded"] is True
            assert result["limited_functionality"] is True
    
    @pytest.mark.asyncio
    async def test_fallback_hook_strategy(self, recovery_manager, mock_hook_context):
        """Test fallback hook strategy."""
        hook_type = "pre_message"  # Has known fallbacks
        
        with patch.object(recovery_manager, '_execute_hook_safely') as mock_execute:
            # Primary hook fails, fallback succeeds
            mock_execute.side_effect = [
                Exception("Primary hook failed"),
                {"success": True, "hook_type": "message_validation"}
            ]
            
            result = await recovery_manager.execute_hook_with_recovery(
                hook_type, mock_hook_context, RecoveryStrategy.FALLBACK_HOOK
            )
            
            assert result["success"] is True
            assert result["fallback_metadata"]["used_fallback"] is True
            assert result["fallback_metadata"]["original_hook"] == hook_type
    
    @pytest.mark.asyncio
    async def test_hook_bypass_functionality(self, recovery_manager, mock_hook_context):
        """Test hook bypass functionality."""
        hook_type = "test_hook"
        
        # Bypass the hook
        recovery_manager.bypass_hook(hook_type)
        
        result = await recovery_manager.execute_hook_with_recovery(
            hook_type, mock_hook_context
        )
        
        assert result["bypassed"] is True
        assert result["bypass_reason"] == "hook_bypassed"
        
        # Re-enable the hook
        recovery_manager.enable_hook(hook_type)
        assert hook_type not in recovery_manager.bypass_hooks
    
    def test_hook_health_status(self, recovery_manager):
        """Test hook health status reporting."""
        hook_type = "test_hook"
        
        # Record some failures
        for _ in range(3):
            recovery_manager._record_hook_failure(hook_type, Exception("Test failure"))
        
        health_status = recovery_manager.get_hook_health_status(hook_type)
        
        assert health_status["hook_type"] == hook_type
        assert health_status["failure_count"] == 3
        assert health_status["recent_errors"] == 3
        assert health_status["health_score"] < 1.0
    
    def test_circuit_breaker_reset(self, recovery_manager):
        """Test circuit breaker reset functionality."""
        hook_type = "test_hook"
        
        # Trigger failures to open circuit breaker
        circuit_breaker = recovery_manager.circuit_breakers[hook_type]
        circuit_breaker.failure_count = 10
        circuit_breaker.state = "open"
        
        # Reset circuit breaker
        recovery_manager.reset_circuit_breaker(hook_type)
        
        # Check it's reset
        assert circuit_breaker.failure_count == 0
        assert circuit_breaker.state == "closed"


class TestEnhancedErrorMiddleware:
    """Test enhanced error middleware integration."""
    
    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI app."""
        return Mock()
    
    @pytest.fixture
    def error_middleware(self, mock_app):
        """Create enhanced error middleware."""
        config = ErrorRecoveryConfig()
        return EnhancedErrorMiddleware(mock_app, config)
    
    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI request."""
        request = Mock()
        request.url.path = "/api/test"
        request.method = "GET"
        request.state.request_id = "test-request-123"
        return request
    
    @pytest.mark.asyncio
    async def test_ag_ui_error_handling_in_middleware(self, error_middleware, mock_request):
        """Test AG-UI error handling in middleware."""
        # Mock AG-UI related error
        ag_ui_error = Exception("ag-grid rendering failed")
        mock_request.url.path = "/api/analytics"
        
        with patch.object(error_middleware.error_handler, 'handle_ag_ui_error') as mock_handle:
            mock_handle.return_value = {
                "fallback_type": "simple_table",
                "message": "Grid failed, using simple table"
            }
            
            response = await error_middleware._handle_error(mock_request, ag_ui_error)
            
            assert response.status_code == 200  # Graceful degradation
            mock_handle.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_copilotkit_error_handling_in_middleware(self, error_middleware, mock_request):
        """Test CopilotKit error handling in middleware."""
        # Mock CopilotKit related error
        copilotkit_error = Exception("CopilotKit API unavailable")
        mock_request.url.path = "/api/copilot/suggestions"
        
        with patch.object(error_middleware.error_handler, 'handle_copilotkit_error') as mock_handle:
            mock_handle.return_value = {
                "fallback_type": "llm_provider",
                "message": "Using fallback LLM provider"
            }
            
            response = await error_middleware._handle_error(mock_request, copilotkit_error)
            
            assert response.status_code == 200  # Graceful degradation
            mock_handle.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_hook_error_handling_in_middleware(self, error_middleware, mock_request):
        """Test hook error handling in middleware."""
        # Mock hook related error
        hook_error = Exception("Hook execution timeout")
        mock_request.url.path = "/api/hooks/execute"
        
        with patch.object(error_middleware.error_handler, 'handle_hook_system_error') as mock_handle:
            mock_handle.return_value = {
                "fallback_type": "hook_bypass",
                "message": "Hook bypassed due to timeout"
            }
            
            response = await error_middleware._handle_error(mock_request, hook_error)
            
            assert response.status_code == 200  # Continue processing
            mock_handle.assert_called_once()
    
    def test_error_classification_methods(self, error_middleware, mock_request):
        """Test error classification methods."""
        # Test AG-UI error detection
        ag_ui_error = Exception("ag-grid failed")
        assert error_middleware._is_ag_ui_error(ag_ui_error, mock_request) is True
        
        # Test CopilotKit error detection
        copilotkit_error = Exception("copilotkit unavailable")
        assert error_middleware._is_copilotkit_error(copilotkit_error, mock_request) is True
        
        # Test hook error detection
        hook_error = Exception("hook execution failed")
        assert error_middleware._is_hook_error(hook_error, mock_request) is True
        
        # Test LLM provider error detection
        llm_error = Exception("llm provider failed")
        assert error_middleware._is_llm_provider_error(llm_error, mock_request) is True


class TestIntegrationScenarios:
    """Test integration scenarios with multiple error types."""
    
    @pytest.mark.asyncio
    async def test_cascading_error_recovery(self):
        """Test cascading error recovery across multiple systems."""
        config = ErrorRecoveryConfig()
        error_handler = EnhancedErrorHandler(config)
        
        # Simulate CopilotKit failure leading to LLM provider fallback
        copilotkit_error = Exception("CopilotKit API unavailable")
        context = {"prompt": "Help with code"}
        
        with patch.object(error_handler.llm_orchestrator, 'enhanced_route') as mock_llm:
            mock_llm.return_value = "LLM fallback response"
            
            result = await error_handler.handle_copilotkit_error(copilotkit_error, context)
            
            assert result["fallback_type"] == "llm_provider"
            assert result["response"] == "LLM fallback response"
    
    @pytest.mark.asyncio
    async def test_multiple_system_failures_with_graceful_degradation(self):
        """Test graceful degradation when multiple systems fail."""
        config = ErrorRecoveryConfig()
        error_handler = EnhancedErrorHandler(config)
        
        # Simulate AG-UI failure
        ag_ui_error = Exception("Grid rendering failed")
        ag_ui_context = {"data": [{"id": 1}]}
        
        ag_ui_result = await error_handler.handle_ag_ui_error(ag_ui_error, "grid", ag_ui_context)
        
        # Simulate CopilotKit failure
        copilotkit_error = Exception("CopilotKit unavailable")
        copilotkit_context = {"prompt": "Test"}
        
        with patch.object(error_handler.llm_orchestrator, 'enhanced_route') as mock_llm:
            mock_llm.side_effect = Exception("All LLM providers failed")
            
            copilotkit_result = await error_handler.handle_copilotkit_error(copilotkit_error, copilotkit_context)
            
            # Both should provide fallbacks
            assert ag_ui_result["fallback_type"] == "simple_table"
            assert copilotkit_result["fallback_type"] in ["cached_response", "generic_fallback"]
    
    @pytest.mark.asyncio
    async def test_error_recovery_performance_under_load(self):
        """Test error recovery performance under load."""
        config = ErrorRecoveryConfig()
        error_handler = EnhancedErrorHandler(config)
        
        # Simulate multiple concurrent errors
        errors = [Exception(f"Error {i}") for i in range(10)]
        contexts = [{"data": f"context_{i}"} for i in range(10)]
        
        # Execute all error handlers concurrently
        tasks = [
            error_handler.handle_ag_ui_error(error, "grid", context)
            for error, context in zip(errors, contexts)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete without raising exceptions
        assert len(results) == 10
        assert all(isinstance(result, dict) for result in results)
        assert all(result.get("fallback_type") is not None for result in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])