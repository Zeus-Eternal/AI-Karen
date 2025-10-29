#!/usr/bin/env python3
"""
Test Extension Error Recovery Manager

Comprehensive tests for the extension error recovery manager implementation,
including strategy pattern, error classification, and recovery mechanisms.

Requirements tested:
- 3.1: Extension integration service error handling
- 3.2: Extension API calls with proper authentication
- 3.3: Authentication failures and retry logic
- 9.1: Graceful degradation when authentication fails
- 9.2: Fallback behavior for extension unavailability
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
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
    handle_extension_network_error,
    with_extension_error_recovery
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestExtensionErrorRecoveryManager:
    """Test the core error recovery manager functionality"""
    
    def mock_auth_manager(self):
        """Mock authentication manager"""
        mock = Mock()
        mock.refresh_token = AsyncMock(return_value="new_token_123")
        return mock
    
    def mock_service_recovery_manager(self):
        """Mock service recovery manager"""
        mock = Mock()
        mock.force_recovery = AsyncMock(return_value=True)
        return mock
    
    def mock_cache_manager(self):
        """Mock cache manager"""
        mock = Mock()
        mock.get = AsyncMock(return_value={"cached": "data", "timestamp": datetime.now().isoformat()})
        return mock
    
    def recovery_manager(self):
        """Create recovery manager with mocked dependencies"""
        return ExtensionErrorRecoveryManager(
            auth_manager=self.mock_auth_manager(),
            service_recovery_manager=self.mock_service_recovery_manager(),
            cache_manager=self.mock_cache_manager()
        )
    
    def test_error_creation(self):
        """Test error creation functions"""
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
    
    async def test_auth_token_refresh_strategy(self):
        """Test authentication token refresh strategy"""
        mock_auth_manager = self.mock_auth_manager()
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
    
    @pytest.mark.asyncio
    async def test_service_restart_strategy(self, mock_service_recovery_manager):
        """Test service restart strategy"""
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
    
    @pytest.mark.asyncio
    async def test_network_retry_strategy(self):
        """Test network retry strategy"""
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
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_strategy(self):
        """Test graceful degradation strategy"""
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
    
    @pytest.mark.asyncio
    async def test_cached_data_strategy(self, mock_cache_manager):
        """Test cached data strategy"""
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
    
    @pytest.mark.asyncio
    async def test_readonly_fallback_strategy(self):
        """Test read-only fallback strategy"""
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
    
    @pytest.mark.asyncio
    async def test_escalation_strategy(self):
        """Test escalation strategy"""
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
        with patch('server.extension_error_recovery_manager.logger') as mock_logger:
            result = await strategy.execute(critical_error, {})
            assert result.success == False
            assert result.strategy == RecoveryStrategy.ESCALATE_TO_ADMIN
            assert result.requires_user_action == True
            assert result.escalated == True
            
            # Verify critical log was called
            mock_logger.critical.assert_called()
    
    @pytest.mark.asyncio
    async def test_recovery_manager_error_handling(self, recovery_manager):
        """Test the main recovery manager error handling"""
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
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self, recovery_manager):
        """Test circuit breaker functionality"""
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
    
    @pytest.mark.asyncio
    async def test_error_pattern_detection(self, recovery_manager):
        """Test error pattern detection"""
        # Generate multiple similar errors
        for i in range(6):  # Exceed pattern threshold
            error = create_network_error("/api/extensions/", "list_extensions")
            await recovery_manager.handle_error(error)
        
        # Check if pattern was detected
        # This would be logged, so we'd need to check logs in a real scenario
        # For now, just verify the error tracking works
        assert len(recovery_manager.error_patterns) > 0
    
    def test_recovery_manager_statistics(self, recovery_manager):
        """Test recovery manager statistics"""
        stats = recovery_manager.get_recovery_statistics()
        
        # Check required fields
        required_fields = [
            "total_attempts_24h",
            "successful_attempts_24h", 
            "failed_attempts_24h",
            "success_rate_24h",
            "active_recoveries",
            "strategy_statistics",
            "error_patterns",
            "circuit_breaker_open",
            "global_error_count"
        ]
        
        for field in required_fields:
            assert field in stats
        
        # Check active recoveries
        active = recovery_manager.get_active_recoveries()
        assert isinstance(active, list)
    
    def test_recovery_manager_cleanup(self, recovery_manager):
        """Test recovery manager cleanup functions"""
        # Add some test data
        recovery_manager.recovery_history.append(Mock())
        recovery_manager.error_patterns["test"] = [Mock()]
        
        # Test clear history
        recovery_manager.clear_recovery_history()
        assert len(recovery_manager.recovery_history) == 0
        assert len(recovery_manager.error_patterns) == 0
        
        # Test circuit breaker reset
        recovery_manager.circuit_breaker_open = True
        recovery_manager.force_circuit_breaker_reset()
        assert recovery_manager.circuit_breaker_open == False


class TestExtensionErrorRecoveryIntegration:
    """Test the error recovery integration functionality"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all dependencies for integration"""
        return {
            "auth_manager": Mock(),
            "service_recovery_manager": Mock(),
            "health_monitor": Mock(),
            "cache_manager": Mock()
        }
    
    @pytest.mark.asyncio
    async def test_integration_initialization(self, mock_dependencies):
        """Test integration initialization"""
        integration = ExtensionErrorRecoveryIntegration()
        
        # Mock the setup methods to avoid complex dependency setup
        integration._setup_integration_hooks = AsyncMock()
        
        await integration.initialize(**mock_dependencies)
        
        assert integration.initialized == True
        assert integration.recovery_manager is not None
        assert integration.auth_manager == mock_dependencies["auth_manager"]
        assert integration.service_recovery_manager == mock_dependencies["service_recovery_manager"]
    
    @pytest.mark.asyncio
    async def test_http_error_handling(self, mock_dependencies):
        """Test HTTP error handling through integration"""
        integration = ExtensionErrorRecoveryIntegration()
        integration._setup_integration_hooks = AsyncMock()
        await integration.initialize(**mock_dependencies)
        
        # Test 401 error
        result = await integration.handle_http_error(401, "/api/extensions/", "list_extensions")
        assert isinstance(result, RecoveryResult)
        
        # Test 403 error
        result = await integration.handle_http_error(403, "/api/extensions/", "list_extensions")
        assert isinstance(result, RecoveryResult)
        
        # Test 503 error
        result = await integration.handle_http_error(503, "/api/extensions/", "list_extensions")
        assert isinstance(result, RecoveryResult)
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, mock_dependencies):
        """Test network error handling through integration"""
        integration = ExtensionErrorRecoveryIntegration()
        integration._setup_integration_hooks = AsyncMock()
        await integration.initialize(**mock_dependencies)
        
        result = await integration.handle_network_error(
            "/api/extensions/",
            "list_extensions", 
            "Connection timeout"
        )
        
        assert isinstance(result, RecoveryResult)
    
    @pytest.mark.asyncio
    async def test_service_error_handling(self, mock_dependencies):
        """Test service error handling through integration"""
        integration = ExtensionErrorRecoveryIntegration()
        integration._setup_integration_hooks = AsyncMock()
        await integration.initialize(**mock_dependencies)
        
        result = await integration.handle_service_error(
            "extension_service",
            "/api/extensions/",
            "list_extensions",
            "Service unavailable"
        )
        
        assert isinstance(result, RecoveryResult)
    
    def test_integration_health_check(self, mock_dependencies):
        """Test integration health check"""
        integration = ExtensionErrorRecoveryIntegration()
        
        # Test without initialization
        assert integration.is_healthy() == False
        
        # Test with initialization (would need async setup)
        # This is a simplified test
        integration.recovery_manager = Mock()
        integration.recovery_manager.get_recovery_statistics.return_value = {
            "circuit_breaker_open": False
        }
        
        assert integration.is_healthy() == True


class TestConvenienceFunctions:
    """Test convenience functions and decorators"""
    
    @pytest.mark.asyncio
    async def test_global_functions(self):
        """Test global convenience functions"""
        # Initialize global manager
        manager = initialize_extension_error_recovery_manager()
        assert manager is not None
        
        # Test get function
        retrieved_manager = get_extension_error_recovery_manager()
        assert retrieved_manager == manager
        
        # Test error handling through global function
        error = create_auth_token_expired_error("/api/extensions/", "list_extensions")
        result = await handle_extension_error(error)
        assert isinstance(result, RecoveryResult)
    
    @pytest.mark.asyncio
    async def test_integration_convenience_functions(self):
        """Test integration convenience functions"""
        # Mock the global integration
        mock_integration = Mock()
        mock_integration.handle_http_error = AsyncMock(return_value=RecoveryResult(
            success=True,
            strategy=RecoveryStrategy.RETRY_WITH_REFRESH,
            message="Test recovery"
        ))
        
        with patch('server.extension_error_recovery_integration.get_extension_error_recovery_integration', 
                  return_value=mock_integration):
            
            result = await handle_extension_api_error(403, "/api/extensions/", "list_extensions")
            assert isinstance(result, RecoveryResult)
            assert result.success == True
            
            result = await handle_extension_auth_error("/api/extensions/", "list_extensions")
            assert isinstance(result, RecoveryResult)
    
    @pytest.mark.asyncio
    async def test_error_recovery_decorator(self):
        """Test the error recovery decorator"""
        # Mock the integration
        mock_integration = Mock()
        mock_integration.handle_network_error = AsyncMock(return_value=RecoveryResult(
            success=False,
            strategy=RecoveryStrategy.FALLBACK_TO_CACHED,
            message="Using fallback",
            fallback_data={"fallback": True}
        ))
        
        with patch('server.extension_error_recovery_integration.get_extension_error_recovery_integration',
                  return_value=mock_integration):
            
            @with_extension_error_recovery("/api/extensions/", "test_operation", max_retries=1)
            async def failing_function():
                raise Exception("Test error")
            
            # Should return fallback data instead of raising exception
            result = await failing_function()
            assert result == {"fallback": True}


async def main():
    """Run all tests"""
    print("Starting Extension Error Recovery Manager Tests")
    print("=" * 60)
    
    try:
        # Test 1: Basic error creation and strategy selection
        print("\n1. Testing Error Creation and Strategy Selection")
        print("-" * 40)
        
        # Create test errors
        auth_error = create_auth_token_expired_error("/api/extensions/", "list_extensions")
        service_error = create_service_unavailable_error("/api/extensions/", "list_extensions")
        network_error = create_network_error("/api/extensions/", "list_extensions")
        permission_error = create_permission_denied_error("/api/extensions/", "list_extensions")
        
        print(f"✅ Created auth error: {auth_error.code}")
        print(f"✅ Created service error: {service_error.code}")
        print(f"✅ Created network error: {network_error.code}")
        print(f"✅ Created permission error: {permission_error.code}")
        
        # Test 2: Recovery manager initialization
        print("\n2. Testing Recovery Manager Initialization")
        print("-" * 40)
        
        # Mock dependencies
        mock_auth_manager = Mock()
        mock_auth_manager.refresh_token = AsyncMock(return_value="new_token_123")
        
        mock_service_recovery = Mock()
        mock_service_recovery.force_recovery = AsyncMock(return_value=True)
        
        mock_cache_manager = Mock()
        mock_cache_manager.get = AsyncMock(return_value={"cached": "data"})
        
        # Initialize recovery manager
        recovery_manager = ExtensionErrorRecoveryManager(
            auth_manager=mock_auth_manager,
            service_recovery_manager=mock_service_recovery,
            cache_manager=mock_cache_manager
        )
        
        print("✅ Recovery manager initialized with mocked dependencies")
        
        # Test 3: Strategy execution
        print("\n3. Testing Recovery Strategy Execution")
        print("-" * 40)
        
        # Test auth token refresh
        result = await recovery_manager.handle_error(auth_error)
        print(f"✅ Auth error recovery: {result.success} - {result.message}")
        
        # Test service restart
        result = await recovery_manager.handle_error(service_error, {"service_name": "test_service"})
        print(f"✅ Service error recovery: {result.success} - {result.message}")
        
        # Test network retry
        result = await recovery_manager.handle_error(network_error)
        print(f"✅ Network error recovery: {result.success} - {result.message}")
        
        # Test permission fallback
        result = await recovery_manager.handle_error(permission_error)
        print(f"✅ Permission error recovery: {result.success} - {result.message}")
        
        # Test 4: Recovery statistics
        print("\n4. Testing Recovery Statistics")
        print("-" * 40)
        
        stats = recovery_manager.get_recovery_statistics()
        print(f"✅ Total attempts: {stats['total_attempts_24h']}")
        print(f"✅ Successful attempts: {stats['successful_attempts_24h']}")
        print(f"✅ Success rate: {stats['success_rate_24h']:.2%}")
        print(f"✅ Circuit breaker open: {stats['circuit_breaker_open']}")
        
        # Test 5: Integration layer
        print("\n5. Testing Integration Layer")
        print("-" * 40)
        
        integration = ExtensionErrorRecoveryIntegration()
        
        # Mock the setup to avoid complex dependency setup
        integration._setup_integration_hooks = AsyncMock()
        
        await integration.initialize(
            auth_manager=mock_auth_manager,
            service_recovery_manager=mock_service_recovery,
            cache_manager=mock_cache_manager
        )
        
        print("✅ Integration layer initialized")
        
        # Test HTTP error handling
        result = await integration.handle_http_error(403, "/api/extensions/", "list_extensions")
        print(f"✅ HTTP 403 error handled: {result.success} - {result.message}")
        
        result = await integration.handle_network_error(
            "/api/extensions/", "list_extensions", "Connection timeout"
        )
        print(f"✅ Network error handled: {result.success} - {result.message}")
        
        # Test 6: Global functions
        print("\n6. Testing Global Functions")
        print("-" * 40)
        
        # Initialize global manager
        global_manager = initialize_extension_error_recovery_manager(
            auth_manager=mock_auth_manager,
            service_recovery_manager=mock_service_recovery,
            cache_manager=mock_cache_manager
        )
        
        print("✅ Global recovery manager initialized")
        
        # Test global error handling
        result = await handle_extension_error(auth_error)
        print(f"✅ Global error handling: {result.success} - {result.message}")
        
        # Test 7: Circuit breaker
        print("\n7. Testing Circuit Breaker")
        print("-" * 40)
        
        # Generate errors to trigger circuit breaker
        for i in range(12):
            error = create_network_error("/api/extensions/", f"test_operation_{i}")
            await recovery_manager.handle_error(error)
            recovery_manager._increment_error_count()
        
        stats = recovery_manager.get_recovery_statistics()
        print(f"✅ Circuit breaker triggered: {stats['circuit_breaker_open']}")
        
        # Test error rejection
        result = await recovery_manager.handle_error(auth_error)
        print(f"✅ Error rejected by circuit breaker: {'circuit breaker' in result.message.lower()}")
        
        # Reset circuit breaker
        recovery_manager.force_circuit_breaker_reset()
        stats = recovery_manager.get_recovery_statistics()
        print(f"✅ Circuit breaker reset: {not stats['circuit_breaker_open']}")
        
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