"""
Integration tests for graceful degradation functionality.

Tests the end-to-end graceful degradation behavior when various
components fail or become unavailable.
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import json
import time

# Import graceful degradation components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from ui_launchers.KAREN-Theme-Default.src.lib.graceful_degradation.enhanced_backend_service import EnhancedBackendService
from ui_launchers.KAREN-Theme-Default.src.lib.graceful_degradation.cache_manager import CacheManager
from ui_launchers.KAREN-Theme-Default.src.lib.graceful_degradation.feature_flags import FeatureFlags


class TestGracefulDegradationIntegration:
    """Integration tests for graceful degradation system."""

    @pytest.fixture
    async def backend_service(self):
        """Create an enhanced backend service for testing."""
        service = EnhancedBackendService("http://localhost:8000")
        yield service
        await service.cleanup()

    @pytest.fixture
    def cache_manager(self):
        """Create a cache manager for testing."""
        return CacheManager()

    @pytest.fixture
    def feature_flags(self):
        """Create feature flags manager for testing."""
        return FeatureFlags()

    @pytest.mark.asyncio
    async def test_backend_service_unavailable_degradation(self, backend_service, cache_manager):
        """Test graceful degradation when backend service is unavailable."""
        # Setup cached data
        cached_extensions = {
            "test_extension": {
                "name": "test_extension",
                "status": "active",
                "version": "1.0.0"
            }
        }
        cache_manager.set("extensions", cached_extensions, ttl=300)
        
        # Mock backend service to simulate unavailability
        with patch.object(backend_service, '_make_request') as mock_request:
            mock_request.side_effect = aiohttp.ClientError("Service unavailable")
            
            # Attempt to get extensions
            result = await backend_service.get_extensions_with_fallback(cache_manager)
            
            # Verify graceful degradation
            assert result is not None
            assert result["source"] == "cache"
            assert "test_extension" in result["data"]
            assert result["degraded"] is True

    @pytest.mark.asyncio
    async def test_authentication_failure_degradation(self, backend_service, feature_flags):
        """Test graceful degradation when authentication fails."""
        # Setup feature flags for read-only mode
        feature_flags.set_flag("readonly_mode", True)
        
        # Mock authentication failure
        with patch.object(backend_service, '_authenticate') as mock_auth:
            mock_auth.side_effect = Exception("Authentication failed")
            
            # Attempt authenticated operation
            result = await backend_service.perform_authenticated_operation_with_fallback(
                "get_extensions", feature_flags
            )
            
            # Verify graceful degradation to read-only mode
            assert result is not None
            assert result["mode"] == "readonly"
            assert result["authenticated"] is False
            assert "limited_functionality" in result

    @pytest.mark.asyncio
    async def test_partial_service_failure_degradation(self, backend_service, cache_manager):
        """Test graceful degradation when some services fail but others work."""
        # Mock partial service failure
        async def mock_request(endpoint, **kwargs):
            if "extensions" in endpoint:
                return {"extensions": {"test": "data"}}
            elif "background-tasks" in endpoint:
                raise aiohttp.ClientError("Background task service unavailable")
            else:
                return {"status": "ok"}
        
        with patch.object(backend_service, '_make_request', side_effect=mock_request):
            # Test mixed service availability
            extensions_result = await backend_service.get_extensions_with_fallback(cache_manager)
            tasks_result = await backend_service.get_background_tasks_with_fallback(cache_manager)
            
            # Verify partial degradation
            assert extensions_result["source"] == "live"
            assert extensions_result["degraded"] is False
            
            assert tasks_result["source"] == "cache" or tasks_result["degraded"] is True

    @pytest.mark.asyncio
    async def test_network_timeout_degradation(self, backend_service, cache_manager):
        """Test graceful degradation when network requests timeout."""
        # Setup cached data
        cache_manager.set("extensions", {"cached": "data"}, ttl=300)
        
        # Mock network timeout
        with patch.object(backend_service, '_make_request') as mock_request:
            mock_request.side_effect = asyncio.TimeoutError("Request timeout")
            
            # Attempt request with timeout
            result = await backend_service.get_extensions_with_fallback(
                cache_manager, timeout=1.0
            )
            
            # Verify timeout degradation
            assert result["source"] == "cache"
            assert result["degraded"] is True
            assert "timeout" in result.get("reason", "")

    @pytest.mark.asyncio
    async def test_progressive_degradation_levels(self, backend_service, cache_manager, feature_flags):
        """Test progressive degradation through multiple failure levels."""
        # Level 1: Normal operation
        with patch.object(backend_service, '_make_request') as mock_request:
            mock_request.return_value = {"extensions": {"live": "data"}}
            
            result = await backend_service.get_extensions_with_fallback(cache_manager)
            assert result["degradation_level"] == 0
            assert result["source"] == "live"
        
        # Level 2: Service slow, use cache if available
        cache_manager.set("extensions", {"cached": "data"}, ttl=300)
        
        with patch.object(backend_service, '_make_request') as mock_request:
            async def slow_response(*args, **kwargs):
                await asyncio.sleep(2.0)  # Simulate slow response
                return {"extensions": {"slow": "data"}}
            
            mock_request.side_effect = slow_response
            
            result = await backend_service.get_extensions_with_fallback(
                cache_manager, timeout=1.0
            )
            assert result["degradation_level"] == 1
            assert result["source"] == "cache"
        
        # Level 3: Service unavailable, use cache
        with patch.object(backend_service, '_make_request') as mock_request:
            mock_request.side_effect = aiohttp.ClientError("Service unavailable")
            
            result = await backend_service.get_extensions_with_fallback(cache_manager)
            assert result["degradation_level"] == 2
            assert result["source"] == "cache"
        
        # Level 4: No cache available, minimal functionality
        cache_manager.clear("extensions")
        
        result = await backend_service.get_extensions_with_fallback(cache_manager)
        assert result["degradation_level"] == 3
        assert result["source"] == "minimal"

    @pytest.mark.asyncio
    async def test_automatic_recovery_from_degradation(self, backend_service, cache_manager):
        """Test automatic recovery when services become available again."""
        # Start in degraded state
        with patch.object(backend_service, '_make_request') as mock_request:
            mock_request.side_effect = aiohttp.ClientError("Service unavailable")
            
            # Cache some data for fallback
            cache_manager.set("extensions", {"cached": "data"}, ttl=300)
            
            result1 = await backend_service.get_extensions_with_fallback(cache_manager)
            assert result1["degraded"] is True
            assert result1["source"] == "cache"
        
        # Service becomes available again
        with patch.object(backend_service, '_make_request') as mock_request:
            mock_request.return_value = {"extensions": {"live": "data"}}
            
            result2 = await backend_service.get_extensions_with_fallback(cache_manager)
            assert result2["degraded"] is False
            assert result2["source"] == "live"

    @pytest.mark.asyncio
    async def test_feature_flag_controlled_degradation(self, backend_service, feature_flags):
        """Test degradation controlled by feature flags."""
        # Enable maintenance mode
        feature_flags.set_flag("maintenance_mode", True)
        feature_flags.set_flag("readonly_mode", True)
        
        # Attempt normal operation
        result = await backend_service.perform_operation_with_feature_flags(
            "create_extension", feature_flags
        )
        
        # Verify feature flag degradation
        assert result["allowed"] is False
        assert result["reason"] == "maintenance_mode"
        assert result["alternative"] == "readonly_operation"

    @pytest.mark.asyncio
    async def test_cascading_failure_handling(self, backend_service, cache_manager):
        """Test handling of cascading failures across multiple services."""
        # Simulate cascading failures
        failure_sequence = [
            ("auth_service", "Authentication service down"),
            ("extension_service", "Extension service down"),
            ("cache_service", "Cache service down")
        ]
        
        results = []
        
        for service, error_msg in failure_sequence:
            with patch.object(backend_service, f'_{service}_request') as mock_service:
                mock_service.side_effect = Exception(error_msg)
                
                result = await backend_service.handle_cascading_failure(
                    service, cache_manager
                )
                results.append(result)
        
        # Verify cascading failure handling
        assert len(results) == 3
        assert all(result["handled"] for result in results)
        assert results[-1]["degradation_level"] == 3  # Maximum degradation

    @pytest.mark.asyncio
    async def test_user_experience_during_degradation(self, backend_service, feature_flags):
        """Test user experience preservation during degradation."""
        # Setup user context
        user_context = {
            "user_id": "test_user",
            "preferences": {"theme": "dark", "language": "en"}
        }
        
        # Simulate service degradation
        feature_flags.set_flag("limited_functionality", True)
        
        with patch.object(backend_service, '_make_request') as mock_request:
            mock_request.side_effect = aiohttp.ClientError("Service degraded")
            
            # Test user experience preservation
            result = await backend_service.get_user_experience_with_degradation(
                user_context, feature_flags
            )
            
            # Verify user experience is preserved
            assert result["user_preferences_preserved"] is True
            assert result["core_functionality_available"] is True
            assert result["degraded_features"] is not None
            assert len(result["available_alternatives"]) > 0

    @pytest.mark.asyncio
    async def test_performance_during_degradation(self, backend_service, cache_manager):
        """Test system performance during degraded operation."""
        # Setup performance monitoring
        start_time = time.time()
        
        # Simulate degraded operation
        with patch.object(backend_service, '_make_request') as mock_request:
            mock_request.side_effect = aiohttp.ClientError("Service unavailable")
            
            # Cache data for fast fallback
            cache_manager.set("extensions", {"cached": "data"}, ttl=300)
            
            # Perform multiple operations
            tasks = []
            for i in range(10):
                task = backend_service.get_extensions_with_fallback(cache_manager)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Verify performance is acceptable during degradation
            assert total_time < 5.0  # Should complete within 5 seconds
            assert all(result["source"] == "cache" for result in results)
            assert all(result["response_time"] < 0.1 for result in results)

    @pytest.mark.asyncio
    async def test_data_consistency_during_degradation(self, backend_service, cache_manager):
        """Test data consistency when operating in degraded mode."""
        # Setup initial data
        live_data = {"extensions": {"ext1": {"version": "2.0.0"}}}
        cached_data = {"extensions": {"ext1": {"version": "1.0.0"}}}
        
        cache_manager.set("extensions", cached_data, ttl=300)
        
        # Test data consistency handling
        with patch.object(backend_service, '_make_request') as mock_request:
            mock_request.side_effect = aiohttp.ClientError("Service unavailable")
            
            result = await backend_service.get_extensions_with_consistency_check(
                cache_manager
            )
            
            # Verify data consistency warnings
            assert result["data_consistency_warning"] is True
            assert result["cache_age"] is not None
            assert result["recommended_action"] == "retry_when_service_available"


class TestErrorRecoveryIntegration:
    """Integration tests for error recovery mechanisms."""

    @pytest.fixture
    def recovery_system(self):
        """Create error recovery system for testing."""
        from server.extension_error_recovery_manager import ExtensionErrorRecoveryManager
        return ExtensionErrorRecoveryManager()

    @pytest.mark.asyncio
    async def test_end_to_end_error_recovery(self, recovery_system):
        """Test end-to-end error recovery flow."""
        # Simulate authentication error
        error_context = {
            "error_type": "authentication_error",
            "extension_name": "test_extension",
            "user_id": "test_user",
            "timestamp": datetime.utcnow()
        }
        
        # Mock recovery components
        with patch.object(recovery_system, 'auth_service') as mock_auth:
            mock_auth.refresh_token.return_value = "new_token"
            
            # Execute recovery
            result = await recovery_system.recover_from_error(error_context)
            
            # Verify recovery success
            assert result["success"] is True
            assert result["recovery_strategy"] == "refresh_credentials"
            assert result["new_token"] is not None

    @pytest.mark.asyncio
    async def test_recovery_with_fallback_chain(self, recovery_system):
        """Test recovery with multiple fallback strategies."""
        # Setup recovery chain
        recovery_chain = [
            "refresh_credentials",
            "reset_connection", 
            "restart_service",
            "graceful_degradation"
        ]
        
        error_context = {
            "error_type": "service_unavailable",
            "extension_name": "test_extension"
        }
        
        # Mock first two strategies to fail
        with patch.object(recovery_system, '_execute_recovery_strategy') as mock_strategy:
            def strategy_side_effect(strategy, context):
                if strategy in ["refresh_credentials", "reset_connection"]:
                    return {"success": False, "strategy": strategy}
                else:
                    return {"success": True, "strategy": strategy}
            
            mock_strategy.side_effect = strategy_side_effect
            
            # Execute recovery with fallback chain
            result = await recovery_system.recover_with_fallback_chain(
                error_context, recovery_chain
            )
            
            # Verify fallback chain execution
            assert result["success"] is True
            assert result["final_strategy"] == "restart_service"
            assert result["failed_strategies"] == ["refresh_credentials", "reset_connection"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])