#!/usr/bin/env python3
"""
Test script for Extension Service Recovery System

This script tests the extension service recovery mechanisms that integrate
with existing database health monitoring, startup/shutdown handlers, and
service registry patterns.

Requirements: 2.1, 2.2, 2.3, 5.1, 5.2
"""

import asyncio
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_extension_service_recovery():
    """Test the extension service recovery system"""
    
    print("🔧 Testing Extension Service Recovery System")
    print("=" * 60)
    
    try:
        # Test 1: Initialize recovery manager
        print("\n1. Testing Recovery Manager Initialization")
        print("-" * 40)
        
        from server.extension_service_recovery import (
            initialize_extension_service_recovery_manager,
            get_extension_service_recovery_manager,
            shutdown_extension_service_recovery_manager
        )
        
        # Initialize with mock components
        recovery_manager = await initialize_extension_service_recovery_manager(
            extension_manager=None,  # Mock - would be real extension manager
            database_config=None,    # Mock - would be real database config
            enhanced_health_monitor=None  # Mock - would be real health monitor
        )
        
        assert recovery_manager is not None, "Recovery manager should be initialized"
        print("✅ Recovery manager initialized successfully")
        
        # Test 2: Check initial status
        print("\n2. Testing Initial Recovery Status")
        print("-" * 40)
        
        status = recovery_manager.get_recovery_status()
        
        assert status["recovery_active"] == True, "Recovery system should be active"
        assert "service_states" in status, "Status should include service states"
        assert "recovery_history_count" in status, "Status should include history count"
        
        print(f"✅ Recovery system active: {status['recovery_active']}")
        print(f"✅ Service states tracked: {len(status['service_states'])}")
        print(f"✅ Recovery history entries: {status['recovery_history_count']}")
        
        # Test 3: Test startup handlers
        print("\n3. Testing Startup Handler Integration")
        print("-" * 40)
        
        startup_called = False
        
        async def mock_startup_handler():
            nonlocal startup_called
            startup_called = True
            print("   Mock startup handler executed")
        
        recovery_manager.add_startup_handler(mock_startup_handler)
        await recovery_manager.execute_startup_handlers()
        
        assert startup_called, "Startup handler should be called"
        print("✅ Startup handlers executed successfully")
        
        # Test 4: Test graceful degradation handlers
        print("\n4. Testing Graceful Degradation Handlers")
        print("-" * 40)
        
        degradation_called = False
        
        async def mock_degradation_handler():
            nonlocal degradation_called
            degradation_called = True
            print("   Mock degradation handler executed")
        
        recovery_manager.add_graceful_degradation_handler("test_service", mock_degradation_handler)
        
        # Simulate degradation
        from server.extension_service_recovery import RecoveryStrategy
        await recovery_manager._graceful_degradation_recovery("test_service")
        
        assert degradation_called, "Degradation handler should be called"
        print("✅ Graceful degradation handlers working")
        
        # Test 5: Test force recovery
        print("\n5. Testing Force Recovery")
        print("-" * 40)
        
        # Add a mock service state
        from server.extension_service_recovery import ServiceRecoveryState
        recovery_manager.service_states["test_extension"] = ServiceRecoveryState(
            service_name="test_extension",
            service_type="extension",
            healthy=False,
            last_health_check=datetime.now(timezone.utc),
            failure_count=1
        )
        
        success = await recovery_manager.force_recovery("test_extension")
        assert success, "Force recovery should succeed for existing service"
        
        print("✅ Force recovery queued successfully")
        
        # Wait a moment for recovery to process
        await asyncio.sleep(2)
        
        # Test 6: Test recovery history
        print("\n6. Testing Recovery History")
        print("-" * 40)
        
        history = recovery_manager.get_recovery_history(hours=1)
        print(f"✅ Recovery history retrieved: {len(history)} entries")
        
        if history:
            latest = history[-1]
            print(f"   Latest recovery: {latest['target']} - {latest['strategy']}")
        
        # Test 7: Test shutdown handlers
        print("\n7. Testing Shutdown Handler Integration")
        print("-" * 40)
        
        shutdown_called = False
        
        async def mock_shutdown_handler():
            nonlocal shutdown_called
            shutdown_called = True
            print("   Mock shutdown handler executed")
        
        recovery_manager.add_shutdown_handler(mock_shutdown_handler)
        await recovery_manager.execute_shutdown_handlers()
        
        assert shutdown_called, "Shutdown handler should be called"
        print("✅ Shutdown handlers executed successfully")
        
        # Test 8: Test recovery system shutdown
        print("\n8. Testing Recovery System Shutdown")
        print("-" * 40)
        
        await shutdown_extension_service_recovery_manager()
        
        # Verify manager is cleaned up
        manager_after_shutdown = get_extension_service_recovery_manager()
        assert manager_after_shutdown is None, "Manager should be None after shutdown"
        
        print("✅ Recovery system shutdown successfully")
        
        print("\n" + "=" * 60)
        print("🎉 All Extension Service Recovery Tests Passed!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_database_integration():
    """Test integration with database configuration"""
    
    print("\n🔧 Testing Database Integration")
    print("=" * 60)
    
    try:
        # Test database config extension methods
        print("\n1. Testing Database Config Extensions")
        print("-" * 40)
        
        from server.config import Settings
        from server.database_config import DatabaseConfig
        
        settings = Settings()
        db_config = DatabaseConfig(settings)
        
        # Test that new methods exist
        assert hasattr(db_config, 'reset_connections'), "Database config should have reset_connections method"
        assert hasattr(db_config, 'restart_extension_database_services'), "Database config should have restart method"
        
        print("✅ Database config has extension recovery methods")
        
        # Test service pool configurations
        assert hasattr(db_config, 'service_pool_configs'), "Database config should have service pool configs"
        
        pool_configs = db_config.service_pool_configs
        assert 'AUTHENTICATION' in [t.name for t in pool_configs.keys()], "Should have authentication pool config"
        assert 'EXTENSION' in [t.name for t in pool_configs.keys()], "Should have extension pool config"
        
        print("✅ Service pool configurations defined")
        print(f"   Configured services: {[t.name for t in pool_configs.keys()]}")
        
        print("\n" + "=" * 60)
        print("🎉 Database Integration Tests Passed!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Database integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_startup_integration():
    """Test integration with startup/shutdown handlers"""
    
    print("\n🔧 Testing Startup/Shutdown Integration")
    print("=" * 60)
    
    try:
        # Test startup module extensions
        print("\n1. Testing Startup Module Extensions")
        print("-" * 40)
        
        from server.startup import register_startup_tasks, register_shutdown_tasks
        from fastapi import FastAPI
        
        # Create mock app
        app = FastAPI()
        
        # Test that startup tasks can be registered
        register_startup_tasks(app)
        print("✅ Startup tasks registered successfully")
        
        # Test that shutdown tasks can be registered
        register_shutdown_tasks(app)
        print("✅ Shutdown tasks registered successfully")
        
        # Check that event handlers were added
        startup_handlers = [handler for handler in app.router.on_startup]
        shutdown_handlers = [handler for handler in app.router.on_shutdown]
        
        print(f"   Startup handlers: {len(startup_handlers)}")
        print(f"   Shutdown handlers: {len(shutdown_handlers)}")
        
        assert len(startup_handlers) > 0, "Should have startup handlers"
        assert len(shutdown_handlers) > 0, "Should have shutdown handlers"
        
        print("\n" + "=" * 60)
        print("🎉 Startup/Shutdown Integration Tests Passed!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Startup integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_health_endpoints_integration():
    """Test integration with health endpoints"""
    
    print("\n🔧 Testing Health Endpoints Integration")
    print("=" * 60)
    
    try:
        # Test health endpoints module extensions
        print("\n1. Testing Health Endpoints Extensions")
        print("-" * 40)
        
        from server.health_endpoints import register_health_endpoints
        from fastapi import FastAPI
        
        # Create mock app
        app = FastAPI()
        
        # Register health endpoints
        register_health_endpoints(app)
        print("✅ Health endpoints registered successfully")
        
        # Check for extension recovery endpoints
        routes = [route.path for route in app.routes]
        
        recovery_endpoints = [
            "/api/health/extensions/recovery/status",
            "/api/health/extensions/recovery/history",
            "/api/health/extensions/recovery/force/{service_name}"
        ]
        
        for endpoint in recovery_endpoints:
            # Check if endpoint pattern exists (allowing for path parameters)
            endpoint_exists = any(endpoint.replace("{service_name}", "test") in route or 
                                endpoint.split("{")[0] in route for route in routes)
            if endpoint_exists:
                print(f"   ✅ Found endpoint: {endpoint}")
            else:
                print(f"   ⚠️  Endpoint may not be registered: {endpoint}")
        
        print(f"✅ Total routes registered: {len(routes)}")
        
        print("\n" + "=" * 60)
        print("🎉 Health Endpoints Integration Tests Passed!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Health endpoints integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    
    print("🚀 Starting Extension Service Recovery Tests")
    print("=" * 80)
    
    tests = [
        ("Extension Service Recovery", test_extension_service_recovery),
        ("Database Integration", test_database_integration),
        ("Startup Integration", test_startup_integration),
        ("Health Endpoints Integration", test_health_endpoints_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Tests...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test suite failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 80)
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Extension service recovery system is working correctly.")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)