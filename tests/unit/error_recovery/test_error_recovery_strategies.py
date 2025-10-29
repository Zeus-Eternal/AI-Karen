"""
Unit tests for error recovery strategies.

Tests the core error recovery mechanisms and strategies used throughout
the extension system for handling various types of failures.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Import the error recovery components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from server.extension_error_recovery_manager import (
    ExtensionErrorRecoveryManager,
    RecoveryStrategy,
    ErrorType,
    RecoveryResult,
    RecoveryContext
)


class TestErrorRecoveryStrategies:
    """Test suite for error recovery strategies."""

    @pytest.fixture
    def recovery_manager(self):
        """Create a recovery manager for testing."""
        return ExtensionErrorRecoveryManager()

    @pytest.fixture
    def mock_extension_manager(self):
        """Create a mock extension manager."""
        manager = Mock()
        manager.reload_extension = AsyncMock()
        manager.restart_extension = AsyncMock()
        manager.get_extension_status = Mock()
        return manager

    @pytest.fixture
    def recovery_context(self):
        """Create a recovery context for testing."""
        return RecoveryContext(
            error_type=ErrorType.AUTHENTICATION_ERROR,
            extension_name="test_extension",
            error_message="Authentication failed",
            timestamp=datetime.utcnow(),
            attempt_count=1,
            metadata={"user_id": "test_user"}
        )

    def test_authentication_error_recovery_strategy(self, recovery_manager, recovery_context):
        """Test authentication error recovery strategy."""
        # Setup
        recovery_context.error_type = ErrorType.AUTHENTICATION_ERROR
        
        # Mock token refresh
        with patch.object(recovery_manager, '_refresh_authentication_token', return_value=True) as mock_refresh:
            # Execute
            result = recovery_manager._execute_authentication_recovery(recovery_context)
            
            # Verify
            assert result.success is True
            assert result.strategy == RecoveryStrategy.REFRESH_CREDENTIALS
            assert "Authentication token refreshed" in result.message
            mock_refresh.assert_called_once()

    def test_service_unavailable_recovery_strategy(self, recovery_manager, recovery_context):
        """Test service unavailable recovery strategy."""
        # Setup
        recovery_context.error_type = ErrorType.SERVICE_UNAVAILABLE
        
        # Mock service restart
        with patch.object(recovery_manager, '_restart_service', return_value=True) as mock_restart:
            # Execute
            result = recovery_manager._execute_service_recovery(recovery_context)
            
            # Verify
            assert result.success is True
            assert result.strategy == RecoveryStrategy.RESTART_SERVICE
            assert "Service restarted successfully" in result.message
            mock_restart.assert_called_once()

    def test_network_error_recovery_strategy(self, recovery_manager, recovery_context):
        """Test network error recovery strategy."""
        # Setup
        recovery_context.error_type = ErrorType.NETWORK_ERROR
        
        # Mock connection reset
        with patch.object(recovery_manager, '_reset_connection', return_value=True) as mock_reset:
            # Execute
            result = recovery_manager._execute_network_recovery(recovery_context)
            
            # Verify
            assert result.success is True
            assert result.strategy == RecoveryStrategy.RESET_CONNECTION
            assert "Network connection reset" in result.message
            mock_reset.assert_called_once()

    def test_configuration_error_recovery_strategy(self, recovery_manager, recovery_context):
        """Test configuration error recovery strategy."""
        # Setup
        recovery_context.error_type = ErrorType.CONFIGURATION_ERROR
        
        # Mock config reload
        with patch.object(recovery_manager, '_reload_configuration', return_value=True) as mock_reload:
            # Execute
            result = recovery_manager._execute_configuration_recovery(recovery_context)
            
            # Verify
            assert result.success is True
            assert result.strategy == RecoveryStrategy.RELOAD_CONFIG
            assert "Configuration reloaded" in result.message
            mock_reload.assert_called_once()

    def test_recovery_strategy_selection(self, recovery_manager):
        """Test that the correct recovery strategy is selected for each error type."""
        test_cases = [
            (ErrorType.AUTHENTICATION_ERROR, RecoveryStrategy.REFRESH_CREDENTIALS),
            (ErrorType.SERVICE_UNAVAILABLE, RecoveryStrategy.RESTART_SERVICE),
            (ErrorType.NETWORK_ERROR, RecoveryStrategy.RESET_CONNECTION),
            (ErrorType.CONFIGURATION_ERROR, RecoveryStrategy.RELOAD_CONFIG),
            (ErrorType.RESOURCE_EXHAUSTION, RecoveryStrategy.SCALE_RESOURCES),
        ]
        
        for error_type, expected_strategy in test_cases:
            strategy = recovery_manager._select_recovery_strategy(error_type)
            assert strategy == expected_strategy

    def test_recovery_attempt_limit(self, recovery_manager, recovery_context):
        """Test that recovery attempts are limited to prevent infinite loops."""
        # Setup - simulate multiple failed attempts
        recovery_context.attempt_count = 5  # Exceed max attempts
        
        # Execute
        result = recovery_manager._should_attempt_recovery(recovery_context)
        
        # Verify
        assert result is False

    def test_recovery_backoff_calculation(self, recovery_manager):
        """Test exponential backoff calculation for recovery attempts."""
        test_cases = [
            (1, 1.0),    # First attempt: 1 second
            (2, 2.0),    # Second attempt: 2 seconds
            (3, 4.0),    # Third attempt: 4 seconds
            (4, 8.0),    # Fourth attempt: 8 seconds
            (5, 16.0),   # Fifth attempt: 16 seconds (capped at max)
        ]
        
        for attempt, expected_delay in test_cases:
            delay = recovery_manager._calculate_backoff_delay(attempt)
            assert delay == expected_delay

    def test_recovery_context_validation(self, recovery_manager):
        """Test recovery context validation."""
        # Valid context
        valid_context = RecoveryContext(
            error_type=ErrorType.AUTHENTICATION_ERROR,
            extension_name="test_extension",
            error_message="Test error",
            timestamp=datetime.utcnow(),
            attempt_count=1
        )
        
        assert recovery_manager._validate_recovery_context(valid_context) is True
        
        # Invalid context - missing required fields
        invalid_context = RecoveryContext(
            error_type=None,
            extension_name="",
            error_message="",
            timestamp=datetime.utcnow(),
            attempt_count=0
        )
        
        assert recovery_manager._validate_recovery_context(invalid_context) is False

    @pytest.mark.asyncio
    async def test_async_recovery_execution(self, recovery_manager, recovery_context):
        """Test asynchronous recovery execution."""
        # Mock async recovery method
        with patch.object(recovery_manager, '_execute_async_recovery', new_callable=AsyncMock) as mock_async:
            mock_async.return_value = RecoveryResult(
                success=True,
                strategy=RecoveryStrategy.REFRESH_CREDENTIALS,
                message="Async recovery completed"
            )
            
            # Execute
            result = await recovery_manager.execute_recovery_async(recovery_context)
            
            # Verify
            assert result.success is True
            assert "Async recovery completed" in result.message
            mock_async.assert_called_once_with(recovery_context)

    def test_recovery_metrics_collection(self, recovery_manager, recovery_context):
        """Test that recovery metrics are properly collected."""
        # Setup metrics mock
        with patch.object(recovery_manager, 'metrics_collector') as mock_metrics:
            # Execute recovery
            recovery_manager._execute_authentication_recovery(recovery_context)
            
            # Verify metrics were recorded
            mock_metrics.record_recovery_attempt.assert_called_once()
            mock_metrics.record_recovery_result.assert_called_once()

    def test_recovery_error_handling(self, recovery_manager, recovery_context):
        """Test error handling during recovery execution."""
        # Mock recovery method to raise exception
        with patch.object(recovery_manager, '_refresh_authentication_token', side_effect=Exception("Recovery failed")):
            # Execute
            result = recovery_manager._execute_authentication_recovery(recovery_context)
            
            # Verify
            assert result.success is False
            assert "Recovery failed" in result.message
            assert result.strategy == RecoveryStrategy.REFRESH_CREDENTIALS

    def test_recovery_state_persistence(self, recovery_manager, recovery_context):
        """Test that recovery state is properly persisted."""
        # Mock state storage
        with patch.object(recovery_manager, 'state_store') as mock_store:
            # Execute recovery
            recovery_manager._execute_authentication_recovery(recovery_context)
            
            # Verify state was saved
            mock_store.save_recovery_state.assert_called_once()

    def test_concurrent_recovery_handling(self, recovery_manager):
        """Test handling of concurrent recovery attempts."""
        # Setup multiple recovery contexts
        contexts = [
            RecoveryContext(
                error_type=ErrorType.AUTHENTICATION_ERROR,
                extension_name=f"extension_{i}",
                error_message=f"Error {i}",
                timestamp=datetime.utcnow(),
                attempt_count=1
            )
            for i in range(3)
        ]
        
        # Mock recovery execution
        with patch.object(recovery_manager, '_execute_authentication_recovery') as mock_recovery:
            mock_recovery.return_value = RecoveryResult(
                success=True,
                strategy=RecoveryStrategy.REFRESH_CREDENTIALS,
                message="Recovery successful"
            )
            
            # Execute concurrent recoveries
            results = []
            for context in contexts:
                result = recovery_manager._execute_authentication_recovery(context)
                results.append(result)
            
            # Verify all recoveries were executed
            assert len(results) == 3
            assert all(result.success for result in results)
            assert mock_recovery.call_count == 3


class TestRecoveryStrategyImplementations:
    """Test specific recovery strategy implementations."""

    @pytest.fixture
    def recovery_manager(self):
        """Create a recovery manager for testing."""
        return ExtensionErrorRecoveryManager()

    def test_credential_refresh_implementation(self, recovery_manager):
        """Test credential refresh recovery implementation."""
        # Mock authentication service
        with patch('server.extension_error_recovery_manager.auth_service') as mock_auth:
            mock_auth.refresh_token.return_value = "new_token"
            
            # Execute
            result = recovery_manager._refresh_authentication_token()
            
            # Verify
            assert result is True
            mock_auth.refresh_token.assert_called_once()

    def test_service_restart_implementation(self, recovery_manager):
        """Test service restart recovery implementation."""
        # Mock service manager
        with patch('server.extension_error_recovery_manager.service_manager') as mock_service:
            mock_service.restart_service.return_value = True
            
            # Execute
            result = recovery_manager._restart_service("test_service")
            
            # Verify
            assert result is True
            mock_service.restart_service.assert_called_once_with("test_service")

    def test_connection_reset_implementation(self, recovery_manager):
        """Test connection reset recovery implementation."""
        # Mock connection manager
        with patch('server.extension_error_recovery_manager.connection_manager') as mock_conn:
            mock_conn.reset_connection.return_value = True
            
            # Execute
            result = recovery_manager._reset_connection()
            
            # Verify
            assert result is True
            mock_conn.reset_connection.assert_called_once()

    def test_configuration_reload_implementation(self, recovery_manager):
        """Test configuration reload recovery implementation."""
        # Mock config manager
        with patch('server.extension_error_recovery_manager.config_manager') as mock_config:
            mock_config.reload_configuration.return_value = True
            
            # Execute
            result = recovery_manager._reload_configuration()
            
            # Verify
            assert result is True
            mock_config.reload_configuration.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])