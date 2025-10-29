#!/usr/bin/env python3
"""
Simple Test for Extension Error Recovery Manager

Basic functionality tests without pytest dependencies.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

# Import the modules we're testing
from server.extension_error_recovery_manager import (
    ExtensionErrorRecoveryManager,
    ExtensionError,
    ErrorCategory,
    ErrorSeverity,
    RecoveryStrategy,
    RecoveryResult,
    AuthTokenRefreshStrategy,
    ServiceRestartStrategy,
    NetworkRetryStrategy,
    GracefulDegradationStrategy,
    CachedDataStrategy,
    ReadOnlyFallbackStrategy,
    EscalationStrategy,
    create_extension_error,
    create_auth_token_expired_error,
    create_service_unavailable_error,
    create_network_error,
    create_permission_denied_error,
    initialize_extension_error_recovery_manager,
    get_extension_error_recovery_manager,
    handle_extension_error
)

from server.extension_error_recovery_integration import (
    ExtensionErrorRecoveryIntegration,
    initialize_extension_error_recovery_integration,
    get_extension_error_recovery_integration,
    handle_extension_api_error,
    handle_extension_auth_error,
    handle_extension_service_unavailable,
    handle_extension_network_error
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_error_creation():
    """Test error creation functions"""
    print("Testing error creation...")
    
    # Test basic error creation
    error = create_extension_error(
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.HIGH,
        code="TEST_ERROR",
        message="Test error message",
        endpoint="/api/test",
        operation="test_operation"
    )
    
    assert error.category == ErrorCategory.AUTHENTICATION
    assert error.severity == ErrorSeverity.HIGH
    assert error.code == "TEST_ERROR"
    assert error.message == "Test error message"
    assert error.endpoint == "/api/test"
    assert error.operation == "test_operation"
    assert isinstance(error.timestamp, datetime)
    
    # Test specific error creation functions
    auth_error = create_auth_token_expired_error("/api/extensions/", "list_extensions")
    assert auth_error.category == ErrorCategory.AUTHENTICATION
    assert auth_error.code == "TOKEN_EXPIRED"
    
    service_error = create_service_unavailable_error("/api/extensions/", "list_extensions")
    assert service_error.category == ErrorCategory.SERVICE_UNAVAILABLE
    assert service_error.code == "SERVICE_UNAVAILABLE"
    
    network_error = create_network_error("/api/extensions/", "list_extensions")
    assert network_error.category == ErrorCategory.NETWORK
    assert network_error.code == "NETWORK_ERROR"
    
    permission_error = create_permission_denied_error("/api/extensions/", "list_extensions")
    assert permission_error.category == ErrorCategory.PERMISSION
    assert permission_error.code == "PERMISSION_DENIED"
    
    print("✅ Error creation tests passed")


async def test_auth_token_refresh_strategy():
    """Test authentication token refresh strategy"""
    print("Testing auth token refresh strategy...")
    
    # Mock auth manager
    mock_auth_manager = Mock()
    mock_auth_manager.refresh_token = AsyncMock(return_value="new_token_123")
    
    strategy = AuthTokenRefreshStrategy(mock_auth_manager)
    
    # Test can_handle
    auth_error = create_auth_token_expired_error("/api/extensions/", "list_extensions")
    assert await strategy.can_handle(auth_error) == True
    
    network_error = create_network_error("/api/extensions/", "list_extensions")
    assert await strategy.can_handle(network_error) == False
    
    # Test successful execution
    result = await strategy.execute(auth_error, {})
    assert result.success == True
    assert result.strategy == RecoveryStrategy.RETRY_WITH_REFRESH
    assert "refreshed successfully" in result.message
    assert result.requires_user_action == False
    
    # Test failed execution
    mock_auth_manager.refresh_token.return_value = None
    result = await strategy.execute(auth_error, {})
    assert result.success == False
    assert result.requires_user_action == True
    
    print("✅ Auth token refresh strategy tests passed")


async def test_service_restart_strategy():
    """Test service restart strategy"""
    print("Testing service restart strategy...")
    
    # Mock service recovery manager
    mock_service_recovery_manager = Mock()
    mock_service_recovery_manager.force_recovery = AsyncMock(return_value=True)
    
    strategy = ServiceRestartStrategy(mock_service_recovery_manager)
    
    # Test can_handle
    service_error = create_service_unavailable_error("/api/extensions/", "list_extensions")
    assert await strategy.can_handle(service_error) == True
    
    auth_error = create_auth_token_expired_error("/api/extensions/", "list_extensions")
    assert await strategy.can_handle(auth_error) == False
    
    # Test successful execution
    result = await strategy.execute(service_error, {"service_name": "test_service"})
    assert result.success == True
    assert result.strategy == RecoveryStrategy.SERVICE_RESTART
    assert "restarted successfully" in result.message
    assert result.retry_after == 5.0
    
    # Test failed execution
    mock_service_recovery_manager.force_recovery.return_value = False
    result = await strategy.execute(service_error, {"service_name": "test_service"})
    assert result.success == False
    assert result.retry_after == 30.0
    
    print("✅ Service restart strategy tests passed")


async def test_network_retry_strategy():
    """Test network retry strategy"""
    print("Testing network retry strategy...")
    
    strategy = NetworkRetryStrategy()
    
    # Test can_handle
    network_error = create_network_error("/api/extensions/", "list_extensions")
    assert await strategy.can_handle(network_error) == True
    
    auth_error = create_auth_token_expired_error("/api/extensions/", "list_extensions")
    assert await strategy.can_handle(auth_error) == False
    
    # Test execution with exponential backoff
    result = await strategy.execute(network_error, {})
    assert result.success == False
    assert result.strategy == RecoveryStrategy.RETRY_WITH_BACKOFF
    assert result.retry_after is not None
    assert result.retry_after >= 2.0  # Base delay
    
    # Test with higher retry count
    network_error.retry_count = 3
    result = await strategy.execute(network_error, {})
    assert result.retry_after >= 16.0  # 2 * 2^3
    
    print("✅ Network retry strategy tests passed")


async def test_graceful_degradation_strategy():
    """Test graceful degradation strategy"""
    print("Testing graceful degradation strategy...")
    
    strategy = GracefulDegradationStrategy()
    
    # Test can_handle
    service_error = create_service_unavailable_error("/api/extensions/", "list_extensions")
    assert await strategy.can_handle(service_error) == True
    
    # Test execution
    result = await strategy.execute(service_error, {})
    assert result.success == True
    assert result.strategy == RecoveryStrategy.GRACEFUL_DEGRADATION
    assert "temporarily limited" in result.message
    assert result.fallback_data is not None
    
    print("✅ Graceful degradation strategy tests passed")


async def test_cached_data_strategy():
    """Test cached data strategy"""
    print("Testing cached data strategy...")
    
    # Mock cache manager
    mock_cache_manager = Mock()
    mock_cache_manager.get = AsyncMock(return_value={"cached": "data", "timestamp": datetime.now().isoformat()})
    
    strategy = CachedDataStrategy(mock_cache_manager)
    
    # Test can_handle
    service_error = create_service_unavailable_error("/api/extensions/", "list_extensions")
    assert await strategy.can_handle(service_error) == True
    
    # Test successful execution with cached data
    result = await strategy.execute(service_error, {})
    assert result.success == True
    assert result.strategy == RecoveryStrategy.FALLBACK_TO_CACHED
    assert "cached data" in result.message
    assert result.fallback_data is not None
    
    # Test execution without cached data
    mock_cache_manager.get.return_value = None
    result = await strategy.execute(service_error, {})
    assert result.success == False
    assert "No cached data available" in result.message
    
    print("✅ Cached data strategy tests passed")


async def test_readonly_fallback_strategy():
    """Test read-only fallback strategy"""
    print("Testing read-only fallback strategy...")
    
    strategy = ReadOnlyFallbackStrategy()
    
    # Test can_handle
    permission_error = create_permission_denied_error("/api/extensions/", "list_extensions")
    assert await strategy.can_handle(permission_error) == True
    
    # Test execution
    result = await strategy.execute(permission_error, {"cached_extensions": [{"name": "test"}]})
    assert result.success == True
    assert result.strategy == RecoveryStrategy.FALLBACK_TO_READONLY
    assert "read-only mode" in result.message
    assert result.fallback_data is not None
    assert result.fallback_data["readonly"] == True
    
    print("✅ Read-only fallback strategy tests passed")


async def test_escalation_strategy():
    """Test escalation strategy"""
    print("Testing escalation strategy...")
    
    strategy = EscalationStrategy()
    
    # Test can_handle
    critical_error = create_extension_error(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.CRITICAL,
        code="CRITICAL_ERROR",
        message="Critical system error"
    )
    assert await strategy.can_handle(critical_error) == True
    
    # Test execution
    result = await strategy.execute(critical_error, {})
    assert result.success == False
    assert result.strategy == RecoveryStrategy.ESCALATE_TO_ADMIN
    assert result.requires_user_action == True
    assert result.escalated == True
    
    print("✅ Escalation strategy tests passed")


async def test_recovery_manager():
    """Test the main recovery manager"""
    print("Testing recovery manager...")
    
    # Mock dependencies
    mock_auth_manager = Mock()
    mock_auth_manager.refresh_token = AsyncMock(return_value="new_token_123")
    
    mock_service_recovery = Mock()
    mock_service_recovery.force_recovery = AsyncMock(return_value=True)
    
    mock_cache_manager = Mock()
    mock_cache_manager.get = AsyncMock(return_value={"cached": "data"})
    
    # Create recovery manager
    recovery_manager = ExtensionErrorRecoveryManager(
        auth_manager=mock_auth_manager,
        service_recovery_manager=mock_service_recovery,
        cache_manager=mock_cache_manager
    )
    
    # Test successful recovery
    auth_error = create_auth_token_expired_error("/api/extensions/", "list_extensions")
    result = await recovery_manager.handle_error(auth_error)
    
    assert isinstance(result, RecoveryResult)
    assert result.success == True
    assert result.strategy == RecoveryStrategy.RETRY_WITH_REFRESH
    
    # Test recovery statistics
    stats = recovery_manager.get_recovery_statistics()
    assert "total_attempts_24h" in stats
    assert "successful_attempts_24h" in stats
    assert "success_rate_24h" in stats
    assert stats["total_attempts_24h"] >= 1
    assert stats["successful_attempts_24h"] >= 1
    
    print("✅ Recovery manager tests passed")


async def test_circuit_breaker():
    """Test circuit breaker functionality"""
    print("Testing circuit breaker...")
    
    # Mock dependencies
    mock_auth_manager = Mock()
    mock_auth_manager.refresh_token = AsyncMock(return_value="new_token_123")
    
    recovery_manager = ExtensionErrorRecoveryManager(auth_manager=mock_auth_manager)
    
    # Generate many errors to trigger circuit breaker
    for i in range(15):  # Exceed threshold
        error = create_network_error("/api/extensions/", "list_extensions")
        result = await recovery_manager.handle_error(error)
        # Most should fail to trigger circuit breaker
        if i > 5:
            recovery_manager._increment_error_count()
    
    # Check if circuit breaker is open
    stats = recovery_manager.get_recovery_statistics()
    assert stats.get("circuit_breaker_open", False) == True
    
    # Test that new errors are rejected
    error = create_auth_token_expired_error("/api/extensions/", "list_extensions")
    result = await recovery_manager.handle_error(error)
    assert result.success == False
    assert "circuit breaker" in result.message.lower()
    
    print("✅ Circuit breaker tests passed")


async def test_integration():
    """Test integration layer"""
    print("Testing integration layer...")
    
    # Mock dependencies
    mock_auth_manager = Mock()
    mock_auth_manager.refresh_token = AsyncMock(return_value="new_token_123")
    
    mock_service_recovery = Mock()
    mock_service_recovery.force_recovery = AsyncMock(return_value=True)
    
    mock_cache_manager = Mock()
    mock_cache_manager.get = AsyncMock(return_value={"cached": "data"})
    
    integration = ExtensionErrorRecoveryIntegration()
    
    # Mock the setup to avoid complex dependency setup
    integration._setup_integration_hooks = AsyncMock()
    
    await integration.initialize(
        auth_manager=mock_auth_manager,
        service_recovery_manager=mock_service_recovery,
        cache_manager=mock_cache_manager
    )
    
    assert integration.initialized == True
    assert integration.recovery_manager is not None
    
    # Test HTTP error handling
    result = await integration.handle_http_error(403, "/api/extensions/", "list_extensions")
    assert isinstance(result, RecoveryResult)
    
    result = await integration.handle_network_error(
        "/api/extensions/", "list_extensions", "Connection timeout"
    )
    assert isinstance(result, RecoveryResult)
    
    print("✅ Integration layer tests passed")


async def test_global_functions():
    """Test global convenience functions"""
    print("Testing global functions...")
    
    # Mock dependencies
    mock_auth_manager = Mock()
    mock_auth_manager.refresh_token = AsyncMock(return_value="new_token_123")
    
    # Initialize global manager
    manager = initialize_extension_error_recovery_manager(auth_manager=mock_auth_manager)
    assert manager is not None
    
    # Test get function
    retrieved_manager = get_extension_error_recovery_manager()
    assert retrieved_manager == manager
    
    # Test error handling through global function
    error = create_auth_token_expired_error("/api/extensions/", "list_extensions")
    result = await handle_extension_error(error)
    assert isinstance(result, RecoveryResult)
    
    print("✅ Global functions tests passed")


async def main():
    """Run all tests"""
    print("Starting Extension Error Recovery Manager Tests")
    print("=" * 60)
    
    try:
        await test_error_creation()
        await test_auth_token_refresh_strategy()
        await test_service_restart_strategy()
        await test_network_retry_strategy()
        await test_graceful_degradation_strategy()
        await test_cached_data_strategy()
        await test_readonly_fallback_strategy()
        await test_escalation_strategy()
        await test_recovery_manager()
        await test_circuit_breaker()
        await test_integration()
        await test_global_functions()
        
        print("\n" + "=" * 60)
        print("✅ All Extension Error Recovery Manager tests completed successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)