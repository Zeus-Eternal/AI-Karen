#!/usr/bin/env python3
"""
Test Extension Health Monitoring Integration

This test verifies that the extension health monitoring system is properly
integrated with the existing health endpoints and monitoring infrastructure.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_extension_health_monitor():
    """Test the extension health monitor functionality"""
    logger.info("Testing Extension Health Monitor")
    
    try:
        from server.extension_health_monitor import ExtensionHealthMonitor, ExtensionHealthStatus
        
        # Create a mock extension manager
        class MockExtensionManager:
            def __init__(self):
                self.registry = MockRegistry()
            
            async def get_extension_background_tasks(self, name):
                return [
                    {"status": "running", "name": "test_task_1"},
                    {"status": "failed", "name": "test_task_2"}
                ]
        
        class MockRegistry:
            def get_all_extensions(self):
                return {
                    "test-extension": MockExtensionRecord("test-extension", "active"),
                    "failing-extension": MockExtensionRecord("failing-extension", "error")
                }
        
        class MockExtensionRecord:
            def __init__(self, name, status):
                self.manifest = MockManifest(name)
                self.status = MockStatus(status)
                self.loaded_at = datetime.now(timezone.utc)
                self.error = "Test error" if status == "error" else None
                self.error_count = 5 if status == "error" else 0
                self.success_count = 10
        
        class MockManifest:
            def __init__(self, name):
                self.name = name
                self.version = "1.0.0"
                self.display_name = f"Test {name}"
                self.description = f"Test extension {name}"
                self.category = "test"
        
        class MockStatus:
            def __init__(self, status):
                self.value = status
        
        # Initialize the health monitor
        mock_manager = MockExtensionManager()
        health_monitor = ExtensionHealthMonitor(mock_manager)
        
        # Test individual extension health check
        logger.info("Testing individual extension health check")
        extensions = mock_manager.registry.get_all_extensions()
        
        for name, record in extensions.items():
            metrics = await health_monitor._check_individual_extension_health(name, record)
            logger.info(f"Extension {name}: status={metrics.status.value}, response_time={metrics.response_time_ms:.1f}ms")
            
            # Verify metrics
            assert metrics.name == name
            assert isinstance(metrics.status, ExtensionHealthStatus)
            assert metrics.response_time_ms >= 0
            assert metrics.last_check is not None
        
        # Test system health check
        logger.info("Testing extension system health check")
        system_health = await health_monitor.check_extension_system_health()
        
        logger.info(f"System health: {system_health.overall_status.value}")
        logger.info(f"Total extensions: {system_health.total_extensions}")
        logger.info(f"Healthy: {system_health.healthy_extensions}")
        logger.info(f"Degraded: {system_health.degraded_extensions}")
        logger.info(f"Unhealthy: {system_health.unhealthy_extensions}")
        
        # Verify system health
        assert system_health.total_extensions == 2
        assert system_health.healthy_extensions >= 0
        assert system_health.unhealthy_extensions >= 0
        assert system_health.extension_metrics is not None
        
        # Test API format
        logger.info("Testing API health format")
        api_health = await health_monitor.get_extension_health_for_api()
        
        assert "status" in api_health
        assert "extensions" in api_health
        assert "supporting_services" in api_health
        assert api_health["extensions"]["total"] == 2
        
        logger.info("✅ Extension Health Monitor tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Extension Health Monitor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_health_endpoints_integration():
    """Test integration with existing health endpoints"""
    logger.info("Testing Health Endpoints Integration")
    
    try:
        from server.health_endpoints import _check_extension_system_health
        
        # Test the extension system health check function
        logger.info("Testing _check_extension_system_health function")
        health = await _check_extension_system_health()
        
        logger.info(f"Extension system health status: {health.get('status', 'unknown')}")
        
        # Verify health response structure
        assert "status" in health
        assert "total_extensions" in health
        assert "healthy_extensions" in health
        assert "degraded_extensions" in health
        assert "unhealthy_extensions" in health
        
        logger.info("✅ Health Endpoints Integration tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Health Endpoints Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_enhanced_database_health_integration():
    """Test integration with enhanced database health monitoring"""
    logger.info("Testing Enhanced Database Health Integration")
    
    try:
        from server.enhanced_database_health_monitor import EnhancedDatabaseHealthMonitor
        
        # Create enhanced monitor without service isolated manager (for testing)
        enhanced_monitor = EnhancedDatabaseHealthMonitor(None)
        
        # Test health check without service manager
        logger.info("Testing enhanced health check without service manager")
        health = await enhanced_monitor.check_extension_service_health()
        
        logger.info(f"Enhanced health status: {health.overall_health}")
        
        # Verify health response structure
        assert health.overall_health in ["healthy", "degraded", "unhealthy", "unavailable"]
        assert hasattr(health, 'extension_service_healthy')
        assert hasattr(health, 'authentication_service_healthy')
        assert hasattr(health, 'timestamp')
        
        # Test API format
        api_health = await enhanced_monitor.get_current_health_with_extension_focus()
        
        assert "timestamp" in api_health
        assert "extension_service_isolated" in api_health
        assert "overall_health" in api_health
        
        logger.info("✅ Enhanced Database Health Integration tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced Database Health Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all extension health monitoring tests"""
    logger.info("🚀 Starting Extension Health Monitoring Tests")
    
    tests = [
        test_extension_health_monitor,
        test_health_endpoints_integration,
        test_enhanced_database_health_integration,
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            logger.error(f"Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All extension health monitoring tests passed!")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)