"""Tests for the degraded mode system implementation."""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from ai_karen_engine.core.degraded_mode import (
    DegradedModeManager,
    DegradedModeReason,
    TinyLlamaHelper,
    get_degraded_mode_manager
)


class TestTinyLlamaHelper:
    """Test the TinyLlama helper functionality."""

    def test_generate_scaffold_greeting(self):
        """Test greeting detection and response."""
        helper = TinyLlamaHelper()
        result = helper.generate_scaffold("Hello there!")
        assert "Hello!" in result
        assert "degraded mode" in result

    def test_generate_scaffold_question(self):
        """Test question detection and response."""
        helper = TinyLlamaHelper()
        result = helper.generate_scaffold("What is machine learning?")
        assert "understand you're asking about" in result
        assert "machine learning" in result

    def test_generate_scaffold_task(self):
        """Test task detection and response."""
        helper = TinyLlamaHelper()
        result = helper.generate_scaffold("Help me create a Python function")
        assert "help with basic tasks" in result
        assert "Python function" in result

    def test_generate_scaffold_general(self):
        """Test general input handling."""
        helper = TinyLlamaHelper()
        result = helper.generate_scaffold("This is a general statement")
        assert "Based on your input" in result
        assert "general statement" in result

    def test_generate_scaffold_empty(self):
        """Test empty input handling."""
        helper = TinyLlamaHelper()
        result = helper.generate_scaffold("")
        assert "currently in degraded mode" in result


class TestDegradedModeManager:
    """Test the degraded mode manager functionality."""

    def test_initialization(self):
        """Test manager initialization."""
        manager = DegradedModeManager()
        assert not manager.status.is_active
        assert manager.status.reason is None
        assert manager.status.recovery_attempts == 0
        assert "tiny_llama" in manager.status.core_helpers_available

    def test_activate_degraded_mode(self):
        """Test activating degraded mode."""
        manager = DegradedModeManager()
        failed_providers = ["openai", "anthropic"]
        
        manager.activate_degraded_mode(
            DegradedModeReason.ALL_PROVIDERS_FAILED,
            failed_providers
        )
        
        assert manager.status.is_active
        assert manager.status.reason == DegradedModeReason.ALL_PROVIDERS_FAILED
        assert manager.status.failed_providers == failed_providers
        assert manager.status.activated_at is not None

    def test_deactivate_degraded_mode(self):
        """Test deactivating degraded mode."""
        manager = DegradedModeManager()
        
        # First activate
        manager.activate_degraded_mode(DegradedModeReason.MANUAL_ACTIVATION)
        assert manager.status.is_active
        
        # Then deactivate
        manager.deactivate_degraded_mode()
        assert not manager.status.is_active
        assert manager.status.reason is None
        assert manager.status.activated_at is None

    def test_attempt_recovery(self):
        """Test recovery attempt."""
        manager = DegradedModeManager()
        
        # Activate degraded mode first
        manager.activate_degraded_mode(DegradedModeReason.NETWORK_ISSUES)
        initial_attempts = manager.status.recovery_attempts
        
        # Attempt recovery
        result = manager.attempt_recovery()
        
        assert manager.status.recovery_attempts == initial_attempts + 1
        assert manager.status.last_recovery_attempt is not None
        # Recovery should fail in test environment
        assert not result

    @pytest.mark.asyncio
    async def test_generate_degraded_response_basic(self):
        """Test basic degraded response generation."""
        manager = DegradedModeManager()
        
        # Mock the services to avoid dependencies
        with patch.object(manager, 'spacy_service', None), \
             patch.object(manager, 'distilbert_service', None), \
             patch.object(manager, 'nlp_service', None):
            
            response = await manager.generate_degraded_response("Hello, how are you?")
            
            assert "content" in response or isinstance(response, dict)
            # The response should contain degraded mode indicators
            response_content = response.get("content", str(response))
            assert "degraded mode" in response_content.lower()

    @pytest.mark.asyncio
    async def test_generate_degraded_response_with_spacy(self):
        """Test degraded response with spaCy service."""
        manager = DegradedModeManager()
        
        # Mock spaCy service
        mock_spacy = Mock()
        mock_parsed = Mock()
        mock_parsed.entities = [("Python", "LANGUAGE"), ("function", "CONCEPT")]
        mock_parsed.dependencies = [{"text": "create", "pos": "VERB"}]
        mock_spacy.parse_message = AsyncMock(return_value=mock_parsed)
        
        manager.spacy_service = mock_spacy
        manager.status.core_helpers_available["spacy"] = True
        
        with patch.object(manager, 'distilbert_service', None), \
             patch.object(manager, 'nlp_service', None):
            
            response = await manager.generate_degraded_response("Create a Python function")
            
            response_content = response.get("content", str(response))
            assert "Python(LANGUAGE)" in response_content
            assert "function(CONCEPT)" in response_content

    @pytest.mark.asyncio
    async def test_generate_degraded_response_with_distilbert(self):
        """Test degraded response with DistilBERT service."""
        manager = DegradedModeManager()
        
        # Mock DistilBERT service
        mock_distilbert = Mock()
        mock_distilbert.get_embeddings = AsyncMock(return_value=[0.5, -0.2, 0.8])
        
        manager.distilbert_service = mock_distilbert
        manager.status.core_helpers_available["distilbert"] = True
        
        with patch.object(manager, 'spacy_service', None), \
             patch.object(manager, 'nlp_service', None):
            
            response = await manager.generate_degraded_response("I'm feeling great today!")
            
            response_content = response.get("content", str(response))
            assert "Enhanced with semantic understanding" in response_content
            assert "Sentiment: positive" in response_content

    @pytest.mark.asyncio
    async def test_generate_degraded_response_error_handling(self):
        """Test error handling in degraded response generation."""
        manager = DegradedModeManager()
        
        # Mock services to raise exceptions
        mock_spacy = Mock()
        mock_spacy.parse_message = AsyncMock(side_effect=Exception("spaCy failed"))
        manager.spacy_service = mock_spacy
        manager.status.core_helpers_available["spacy"] = True
        
        with patch.object(manager, 'distilbert_service', None), \
             patch.object(manager, 'nlp_service', None):
            
            response = await manager.generate_degraded_response("Test input")
            
            # Should still generate a response despite service failures
            assert response is not None
            response_content = response.get("content", str(response))
            assert "degraded mode" in response_content.lower()

    def test_get_health_summary(self):
        """Test health summary generation."""
        manager = DegradedModeManager()
        health = manager.get_health_summary()
        
        assert "degraded_mode_active" in health
        assert "core_helpers" in health
        assert "tiny_llama" in health["core_helpers"]
        assert health["core_helpers"]["tiny_llama"]["is_healthy"]

    def test_admin_alert_logging(self):
        """Test admin alert logging."""
        manager = DegradedModeManager()
        
        with patch('ai_karen_engine.core.degraded_mode.logger') as mock_logger:
            manager.activate_degraded_mode(
                DegradedModeReason.API_RATE_LIMITS,
                ["openai"]
            )
            
            # Check that warning was logged - there should be multiple calls
            mock_logger.warning.assert_called()
            # Check that at least one call contains the activation message
            calls = mock_logger.warning.call_args_list
            activation_logged = any("Degraded mode activated" in str(call) for call in calls)
            assert activation_logged
            
            # Check that the reason is mentioned in one of the calls
            reason_logged = any("api_rate_limits" in str(call) for call in calls)
            assert reason_logged


class TestDegradedModeIntegration:
    """Test integration with other system components."""

    def test_singleton_manager(self):
        """Test that get_degraded_mode_manager returns singleton."""
        manager1 = get_degraded_mode_manager()
        manager2 = get_degraded_mode_manager()
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_legacy_function_compatibility(self):
        """Test that legacy function still works."""
        from ai_karen_engine.core.degraded_mode import generate_degraded_mode_response
        
        # This should work without raising exceptions
        response = generate_degraded_mode_response("Test input")
        assert response is not None
        assert isinstance(response, dict)

    def test_degraded_mode_reasons_enum(self):
        """Test that all degraded mode reasons are valid."""
        reasons = [
            DegradedModeReason.ALL_PROVIDERS_FAILED,
            DegradedModeReason.NETWORK_ISSUES,
            DegradedModeReason.API_RATE_LIMITS,
            DegradedModeReason.RESOURCE_EXHAUSTION,
            DegradedModeReason.MANUAL_ACTIVATION
        ]
        
        for reason in reasons:
            assert isinstance(reason.value, str)
            assert len(reason.value) > 0

    @pytest.mark.asyncio
    async def test_metrics_integration(self):
        """Test metrics service integration."""
        manager = DegradedModeManager()
        
        with patch.object(manager, 'metrics_service') as mock_metrics:
            manager.activate_degraded_mode(DegradedModeReason.MANUAL_ACTIVATION)
            
            # Should record activation metric - check all calls made
            mock_metrics.record_copilot_request.assert_called()
            calls = mock_metrics.record_copilot_request.call_args_list
            
            # Should have at least one call related to degraded mode
            degraded_calls = [call for call in calls if 'degraded_mode' in str(call)]
            assert len(degraded_calls) > 0

    def test_status_dataclass_serialization(self):
        """Test that status can be serialized for API responses."""
        manager = DegradedModeManager()
        manager.activate_degraded_mode(DegradedModeReason.NETWORK_ISSUES, ["provider1"])
        
        status = manager.get_status()
        
        # Test that all fields are accessible
        assert hasattr(status, 'is_active')
        assert hasattr(status, 'reason')
        assert hasattr(status, 'activated_at')
        assert hasattr(status, 'failed_providers')
        assert hasattr(status, 'recovery_attempts')
        assert hasattr(status, 'core_helpers_available')
        
        # Test that datetime can be serialized
        if status.activated_at:
            assert isinstance(status.activated_at, datetime)


if __name__ == "__main__":
    pytest.main([__file__])