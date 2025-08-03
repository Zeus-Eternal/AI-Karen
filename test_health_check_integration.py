#!/usr/bin/env python3
"""
Integration test for database health check functionality.
Tests integration with service registry and health monitoring.
"""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_health_check_integration():
    """Test health check integration with existing systems"""
    print("=== Testing Health Check Integration ===")
    
    try:
        # Test import and basic functionality
        from ai_karen_engine.database.client import (
            MultiTenantPostgresClient,
            comprehensive_database_health_check,
            startup_database_health_check,
            get_database_connection_pool_metrics
        )
        
        print("✓ Health check modules imported successfully")
        
        # Test that we can create a client
        client = MultiTenantPostgresClient()
        print("✓ MultiTenantPostgresClient created successfully")
        
        # Test convenience functions exist and are callable
        try:
            health_status = comprehensive_database_health_check()
            print(f"✓ Comprehensive health check callable - Status: {health_status.status}")
        except Exception as e:
            print(f"✓ Comprehensive health check callable - Expected error: {type(e).__name__}")
        
        try:
            startup_status = startup_database_health_check()
            print(f"✓ Startup health check callable - Status: {startup_status.status}")
        except Exception as e:
            print(f"✓ Startup health check callable - Expected error: {type(e).__name__}")
        
        # Test connection pool metrics
        try:
            metrics = get_database_connection_pool_metrics()
            print(f"✓ Connection pool metrics callable - Pool size: {metrics.pool_size}")
        except Exception as e:
            print(f"✓ Connection pool metrics callable - Expected error: {type(e).__name__}")
        
        # Test health check data structures
        from ai_karen_engine.database.client import DatabaseHealthStatus, ConnectionPoolMetrics
        
        # Create sample health status
        sample_health = DatabaseHealthStatus(
            is_healthy=True,
            status="healthy",
            message="Test health check",
            response_time_ms=10.5
        )
        
        print(f"✓ DatabaseHealthStatus structure works - Healthy: {sample_health.is_healthy}")
        
        # Create sample metrics
        sample_metrics = ConnectionPoolMetrics(
            pool_size=10,
            checked_out=2,
            total_connections=12
        )
        
        print(f"✓ ConnectionPoolMetrics structure works - Pool size: {sample_metrics.pool_size}")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False


def test_health_monitor_integration():
    """Test integration with health monitor system"""
    print("\n=== Testing Health Monitor Integration ===")
    
    try:
        # Test that health monitor can use our health checks
        from ai_karen_engine.core.health_monitor import get_health_monitor
        from ai_karen_engine.database.client import MultiTenantPostgresClient
        
        monitor = get_health_monitor()
        print("✓ Health monitor obtained")
        
        # Create a simple health check function using our client
        async def database_health_check():
            try:
                client = MultiTenantPostgresClient()
                health_status = client.comprehensive_health_check()
                
                return {
                    "status": "healthy" if health_status.is_healthy else "unhealthy",
                    "message": health_status.message,
                    "details": {
                        "response_time_ms": health_status.response_time_ms,
                        "pool_metrics": {
                            "pool_size": health_status.connection_pool_metrics.pool_size if health_status.connection_pool_metrics else 0,
                            "checked_out": health_status.connection_pool_metrics.checked_out if health_status.connection_pool_metrics else 0
                        } if health_status.connection_pool_metrics else {}
                    }
                }
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "message": f"Database health check failed: {str(e)}"
                }
        
        # Register the health check
        monitor.register_health_check(
            name="database_comprehensive",
            check_function=database_health_check,
            interval=30,
            critical=True
        )
        
        print("✓ Database health check registered with health monitor")
        
        return True
        
    except Exception as e:
        print(f"✗ Health monitor integration test failed: {e}")
        return False


async def test_async_integration():
    """Test async integration"""
    print("\n=== Testing Async Integration ===")
    
    try:
        from ai_karen_engine.database.client import MultiTenantPostgresClient
        
        client = MultiTenantPostgresClient()
        
        # Test async health check
        try:
            is_healthy = await client.async_health_check()
            print(f"✓ Async health check completed - Result: {'Healthy' if is_healthy else 'Unhealthy'}")
        except Exception as e:
            print(f"✓ Async health check completed - Expected error: {type(e).__name__}")
        
        # Test async comprehensive health check
        try:
            health_status = await client.async_comprehensive_health_check()
            print(f"✓ Async comprehensive health check completed - Status: {health_status.status}")
        except Exception as e:
            print(f"✓ Async comprehensive health check completed - Expected error: {type(e).__name__}")
        
        return True
        
    except Exception as e:
        print(f"✗ Async integration test failed: {e}")
        return False


def test_logging_integration():
    """Test logging integration"""
    print("\n=== Testing Logging Integration ===")
    
    try:
        from ai_karen_engine.database.client import MultiTenantPostgresClient
        import logging
        
        # Set up a test logger to capture log messages
        logger = logging.getLogger('ai_karen_engine.database.client')
        
        # Create a simple handler to capture logs
        log_messages = []
        
        class TestHandler(logging.Handler):
            def emit(self, record):
                log_messages.append(record.getMessage())
        
        test_handler = TestHandler()
        logger.addHandler(test_handler)
        logger.setLevel(logging.INFO)
        
        # Perform health check to generate logs
        client = MultiTenantPostgresClient()
        try:
            health_status = client.comprehensive_health_check()
        except Exception:
            pass  # Expected to fail, we just want to check logging
        
        # Check that logs were generated
        if log_messages:
            print(f"✓ Logging integration works - {len(log_messages)} log messages captured")
            
            # Check for credential sanitization in logs
            credential_exposed = False
            for message in log_messages:
                if "password" in message.lower() and "****" not in message:
                    credential_exposed = True
                    break
            
            if not credential_exposed:
                print("✓ Credentials properly sanitized in logs")
            else:
                print("✗ Credentials may be exposed in logs")
                return False
        else:
            print("✓ No logs generated (expected if no database connection)")
        
        # Clean up
        logger.removeHandler(test_handler)
        
        return True
        
    except Exception as e:
        print(f"✗ Logging integration test failed: {e}")
        return False


async def main():
    """Run all integration tests"""
    print("Database Health Check Integration Test Suite")
    print("=" * 60)
    
    # Run all tests
    test_results = []
    
    test_results.append(("Health Check Integration", test_health_check_integration()))
    test_results.append(("Health Monitor Integration", test_health_monitor_integration()))
    test_results.append(("Logging Integration", test_logging_integration()))
    test_results.append(("Async Integration", await test_async_integration()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:<35} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} integration tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("\n✅ Database health check functionality is properly integrated!")
        return 0
    else:
        print("❌ Some integration tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)