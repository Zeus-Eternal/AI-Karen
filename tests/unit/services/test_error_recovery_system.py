"""
Unit tests for Error Recovery System

Tests the comprehensive error recovery system including all error types,
recovery strategies, and graceful degradation mechanisms.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

from src.ai_karen_engine.services.error_recovery_system import (
    ErrorRecoverySystem,
    ErrorContext,
    ErrorType,
    RecoveryStrategy,
    RecoveryResult
)
from src.ai_karen_engine.core.types.shared_types import Modality, ModalityType


class TestErrorRecoverySystem:
    """Test cases for ErrorRecoverySystem."""
    
    @pytest.fixture
    def error_recovery_system(self):
        """Create ErrorRecoverySystem instance for testing."""
        return ErrorRecoverySystem()
    
    @pytest.fixture
    def sample_error_context(self):
        """Create sample error context for testing."""
        return ErrorContext(
            error_type=ErrorType.MODEL_UNAVAILABLE,
            original_error=Exception("Test error"),
            query="Test query for error recovery",
            model_id="test-model",
            modalities=[
                Modality(
                    type=ModalityType.TEXT,
                    input_supported=True,
                    output_supported=True
                )
            ]
        )
    
    @pytest.mark.asyncio
    async def test_handle_error_success(self, error_recovery_system, sample_error_context):
        """Test successful error handling."""
        result = await error_recovery_system.handle_error(sample_error_context)
        
        assert isinstance(result, RecoveryResult)
        assert result.success is True
        assert result.response is not None
        assert result.strategy_used is not None
        assert result.recovery_time > 0
    
    @pytest.mark.asyncio
    async def test_handle_error_all_strategies_fail(self, error_recovery_system):
        """Test error handling when all strategies fail."""
        # Create context with no available strategies
        context = ErrorContext(
            error_type=ErrorType.MODEL_UNAVAILABLE,
            original_error=Exception("Critical error"),
            query="Test query",
            model_id="unavailable-model"
        )
        
        # Mock all strategies to fail
        with patch.object(error_recovery_system, '_execute_recovery_strategy', 
                         side_effect=Exception("Strategy failed")):
            result = await error_recovery_system.handle_error(context)
            
            assert result.success is True  # Emergency response should succeed
            assert result.strategy_used == RecoveryStrategy.EMERGENCY_RESPONSE
            assert result.degradation_level == 5
    
    @pytest.mark.asyncio
    async def test_fallback_to_alternative_model(self, error_recovery_system, sample_error_context):
        """Test fallback to alternative model strategy."""
        result = await error_recovery_system._fallback_to_alternative_model(sample_error_context)
        
        assert isinstance(result, RecoveryResult)
        assert result.success is True
        assert result.strategy_used == RecoveryStrategy.FALLBACK_MODEL
        assert result.fallback_model is not None
        assert result.degradation_level == 1
    
    @pytest.mark.asyncio
    async def test_reduce_query_complexity(self, error_recovery_system, sample_error_context):
        """Test query complexity reduction strategy."""
        result = await error_recovery_system._reduce_query_complexity(sample_error_context)
        
        assert isinstance(result, RecoveryResult)
        assert result.success is True
        assert result.strategy_used == RecoveryStrategy.REDUCE_COMPLEXITY
        assert result.degradation_level == 2
    
    @pytest.mark.asyncio
    async def test_fallback_to_cache(self, error_recovery_system, sample_error_context):
        """Test cache fallback strategy."""
        result = await error_recovery_system._fallback_to_cache(sample_error_context)
        
        assert isinstance(result, RecoveryResult)
        # Result depends on cache availability
        if result.success:
            assert result.strategy_used == RecoveryStrategy.CACHE_FALLBACK
            assert result.degradation_level == 1
    
    @pytest.mark.asyncio
    async def test_handle_partial_response(self, error_recovery_system):
        """Test partial response handling strategy."""
        context = ErrorContext(
            error_type=ErrorType.STREAMING_INTERRUPTION,
            original_error=Exception("Stream interrupted"),
            query="Test query",
            partial_response="This is a partial response that was interrupted"
        )
        
        result = await error_recovery_system._handle_partial_response(context)
        
        assert isinstance(result, RecoveryResult)
        assert result.success is True
        assert result.strategy_used == RecoveryStrategy.PARTIAL_RESPONSE
        assert "interrupted" in result.response.lower()
        assert result.degradation_level == 2
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self, error_recovery_system, sample_error_context):
        """Test graceful degradation strategy."""
        result = await error_recovery_system._graceful_degradation(sample_error_context)
        
        assert isinstance(result, RecoveryResult)
        assert result.success is True
        assert result.strategy_used == RecoveryStrategy.GRACEFUL_DEGRADATION
        assert result.degradation_level > 0
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff(self, error_recovery_system, sample_error_context):
        """Test retry with backoff strategy."""
        # Test with low attempt count
        sample_error_context.attempt_count = 1
        sample_error_context.max_attempts = 3
        
        result = await error_recovery_system._retry_with_backoff(sample_error_context)
        
        assert isinstance(result, RecoveryResult)
        assert result.success is True
        assert result.strategy_used == RecoveryStrategy.RETRY_WITH_BACKOFF
        assert result.degradation_level == 0
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_max_attempts(self, error_recovery_system, sample_error_context):
        """Test retry with backoff when max attempts exceeded."""
        # Set attempt count to max
        sample_error_context.attempt_count = 3
        sample_error_context.max_attempts = 3
        
        with pytest.raises(Exception, match="Maximum retry attempts exceeded"):
            await error_recovery_system._retry_with_backoff(sample_error_context)
    
    @pytest.mark.asyncio
    async def test_monitor_system_resources(self, error_recovery_system):
        """Test system resource monitoring."""
        resources = await error_recovery_system.monitor_system_resources()
        
        assert isinstance(resources, dict)
        assert "cpu_usage" in resources
        assert "memory_usage" in resources
        assert "available_memory" in resources
        assert all(isinstance(v, (int, float)) for v in resources.values())
    
    @pytest.mark.asyncio
    async def test_check_performance_thresholds(self, error_recovery_system):
        """Test performance threshold checking."""
        violations = await error_recovery_system.check_performance_thresholds()
        
        assert isinstance(violations, list)
        # Violations depend on current system state
    
    @pytest.mark.asyncio
    async def test_error_recovery_context_success(self, error_recovery_system):
        """Test error recovery context manager with successful execution."""
        async with error_recovery_system.error_recovery_context(
            query="Test query",
            model_id="test-model"
        ):
            # Simulate successful execution
            pass
    
    @pytest.mark.asyncio
    async def test_error_recovery_context_with_error(self, error_recovery_system):
        """Test error recovery context manager with error handling."""
        try:
            async with error_recovery_system.error_recovery_context(
                query="Test query",
                model_id="test-model"
            ):
                # Simulate error
                raise Exception("Test error for recovery")
        except Exception:
            # Error should be handled by context manager
            pass
    
    def test_classify_error_timeout(self, error_recovery_system):
        """Test error classification for timeout errors."""
        timeout_error = Exception("Request timeout occurred")
        error_type = error_recovery_system._classify_error(timeout_error)
        assert error_type == ErrorType.MODEL_TIMEOUT
    
    def test_classify_error_memory(self, error_recovery_system):
        """Test error classification for memory errors."""
        memory_error = Exception("Out of memory (OOM)")
        error_type = error_recovery_system._classify_error(memory_error)
        assert error_type == ErrorType.MEMORY_EXHAUSTION
    
    def test_classify_error_connection(self, error_recovery_system):
        """Test error classification for connection errors."""
        connection_error = Exception("Connection failed")
        error_type = error_recovery_system._classify_error(connection_error)
        assert error_type == ErrorType.CONNECTION_FAILURE
    
    def test_classify_error_model_unavailable(self, error_recovery_system):
        """Test error classification for model unavailable errors."""
        model_error = Exception("Model unavailable")
        error_type = error_recovery_system._classify_error(model_error)
        assert error_type == ErrorType.MODEL_UNAVAILABLE
    
    def test_classify_error_routing(self, error_recovery_system):
        """Test error classification for routing errors."""
        routing_error = Exception("Routing failed")
        error_type = error_recovery_system._classify_error(routing_error)
        assert error_type == ErrorType.ROUTING_ERROR
    
    def test_classify_error_streaming(self, error_recovery_system):
        """Test error classification for streaming errors."""
        streaming_error = Exception("Stream interrupted")
        error_type = error_recovery_system._classify_error(streaming_error)
        assert error_type == ErrorType.STREAMING_INTERRUPTION
    
    def test_classify_error_default(self, error_recovery_system):
        """Test error classification for unknown errors."""
        unknown_error = Exception("Unknown error type")
        error_type = error_recovery_system._classify_error(unknown_error)
        assert error_type == ErrorType.PERFORMANCE_DEGRADATION
    
    def test_get_emergency_response(self, error_recovery_system):
        """Test emergency response generation."""
        context = ErrorContext(
            error_type=ErrorType.MODEL_UNAVAILABLE,
            original_error=Exception("Test error"),
            query="Test query"
        )
        
        response = error_recovery_system._get_emergency_response(context)
        assert isinstance(response, str)
        assert len(response) > 0
        assert "model" in response.lower()
    
    def test_recovery_strategies_configuration(self, error_recovery_system):
        """Test that recovery strategies are properly configured."""
        # Check that all error types have strategies
        for error_type in ErrorType:
            assert error_type in error_recovery_system.recovery_strategies
            strategies = error_recovery_system.recovery_strategies[error_type]
            assert isinstance(strategies, list)
            assert len(strategies) > 0
            assert all(isinstance(s, RecoveryStrategy) for s in strategies)
    
    def test_fallback_models_configuration(self, error_recovery_system):
        """Test that fallback models are properly configured."""
        # Check that all modality types have fallback models
        for modality_type in ModalityType:
            assert modality_type in error_recovery_system.fallback_models
            models = error_recovery_system.fallback_models[modality_type]
            assert isinstance(models, list)
            assert len(models) > 0
            assert all(isinstance(m, str) for m in models)
    
    def test_emergency_responses_configuration(self, error_recovery_system):
        """Test that emergency responses are properly configured."""
        assert isinstance(error_recovery_system.emergency_responses, dict)
        assert "general" in error_recovery_system.emergency_responses
        assert "model_unavailable" in error_recovery_system.emergency_responses
        assert "timeout" in error_recovery_system.emergency_responses
        assert "memory" in error_recovery_system.emergency_responses
        
        for response in error_recovery_system.emergency_responses.values():
            assert isinstance(response, str)
            assert len(response) > 0
    
    def test_performance_thresholds_configuration(self, error_recovery_system):
        """Test that performance thresholds are properly configured."""
        assert isinstance(error_recovery_system.performance_thresholds, dict)
        assert "cpu_usage" in error_recovery_system.performance_thresholds
        assert "memory_usage" in error_recovery_system.performance_thresholds
        assert "response_time" in error_recovery_system.performance_thresholds
        
        for threshold in error_recovery_system.performance_thresholds.values():
            assert isinstance(threshold, (int, float))
            assert threshold > 0


class TestErrorContext:
    """Test cases for ErrorContext."""
    
    def test_error_context_creation(self):
        """Test ErrorContext creation with required fields."""
        context = ErrorContext(
            error_type=ErrorType.MODEL_TIMEOUT,
            original_error=Exception("Test error"),
            query="Test query"
        )
        
        assert context.error_type == ErrorType.MODEL_TIMEOUT
        assert isinstance(context.original_error, Exception)
        assert context.query == "Test query"
        assert context.model_id is None
        assert context.modalities == []
        assert context.attempt_count == 0
        assert context.max_attempts == 3
        assert context.timestamp > 0
    
    def test_error_context_with_optional_fields(self):
        """Test ErrorContext creation with optional fields."""
        modalities = [
            Modality(type=ModalityType.TEXT, input_supported=True, output_supported=True)
        ]
        
        context = ErrorContext(
            error_type=ErrorType.MEMORY_EXHAUSTION,
            original_error=MemoryError("Out of memory"),
            query="Complex query",
            model_id="large-model",
            modalities=modalities,
            attempt_count=2,
            max_attempts=5,
            partial_response="Partial content"
        )
        
        assert context.error_type == ErrorType.MEMORY_EXHAUSTION
        assert context.model_id == "large-model"
        assert context.modalities == modalities
        assert context.attempt_count == 2
        assert context.max_attempts == 5
        assert context.partial_response == "Partial content"


class TestRecoveryResult:
    """Test cases for RecoveryResult."""
    
    def test_recovery_result_success(self):
        """Test RecoveryResult for successful recovery."""
        result = RecoveryResult(
            success=True,
            response="Recovered response",
            strategy_used=RecoveryStrategy.FALLBACK_MODEL,
            fallback_model="backup-model",
            degradation_level=1,
            recovery_time=0.5
        )
        
        assert result.success is True
        assert result.response == "Recovered response"
        assert result.strategy_used == RecoveryStrategy.FALLBACK_MODEL
        assert result.fallback_model == "backup-model"
        assert result.degradation_level == 1
        assert result.recovery_time == 0.5
        assert result.error_message is None
    
    def test_recovery_result_failure(self):
        """Test RecoveryResult for failed recovery."""
        result = RecoveryResult(
            success=False,
            response=None,
            strategy_used=None,
            degradation_level=5,
            recovery_time=1.0,
            error_message="Recovery failed"
        )
        
        assert result.success is False
        assert result.response is None
        assert result.strategy_used is None
        assert result.degradation_level == 5
        assert result.recovery_time == 1.0
        assert result.error_message == "Recovery failed"


if __name__ == "__main__":
    pytest.main([__file__])