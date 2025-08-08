#!/usr/bin/env python3
"""
Test script for database health check functionality.
Tests the comprehensive health check implementation for task 3.
"""

import asyncio
import sys
import time
from datetime import datetime

try:
    from ai_karen_engine.core.chat_memory_config import settings
    from ai_karen_engine.database.client import (
        ConnectionPoolMetrics,
        DatabaseHealthStatus,
        MultiTenantPostgresClient,
        async_comprehensive_database_health_check,
        comprehensive_database_health_check,
        get_database_connection_pool_metrics,
        startup_database_health_check,
    )

    print("✓ Successfully imported database health check modules")
except ImportError as e:
    print(f"✗ Failed to import modules: {e}")
    sys.exit(1)


def test_basic_health_check():
    """Test basic health check functionality"""
    print("\n=== Testing Basic Health Check ===")

    try:
        client = MultiTenantPostgresClient()

        # Test basic boolean health check
        is_healthy = client.health_check()
        print(
            f"Basic health check result: {'✓ HEALTHY' if is_healthy else '✗ UNHEALTHY'}"
        )

        return is_healthy

    except Exception as e:
        print(f"✗ Basic health check failed: {e}")
        return False


def test_comprehensive_health_check():
    """Test comprehensive health check with metrics"""
    print("\n=== Testing Comprehensive Health Check ===")

    try:
        client = MultiTenantPostgresClient()

        # Test comprehensive health check
        health_status = client.comprehensive_health_check()

        print(f"Health Status: {health_status.status}")
        print(f"Is Healthy: {'✓ YES' if health_status.is_healthy else '✗ NO'}")
        print(f"Message: {health_status.message}")
        print(f"Response Time: {health_status.response_time_ms:.2f}ms")
        print(f"Last Check: {health_status.last_check}")

        if health_status.connection_pool_metrics:
            metrics = health_status.connection_pool_metrics
            print(f"Pool Metrics:")
            print(f"  - Pool Size: {metrics.pool_size}")
            print(f"  - Checked Out: {metrics.checked_out}")
            print(f"  - Total Connections: {metrics.total_connections}")
            print(f"  - Timestamp: {metrics.timestamp}")

        if health_status.error_details:
            print(f"Error Details: {health_status.error_details}")

        return health_status.is_healthy

    except Exception as e:
        print(f"✗ Comprehensive health check failed: {e}")
        return False


def test_startup_health_check():
    """Test startup health check with detailed validation"""
    print("\n=== Testing Startup Health Check ===")

    try:
        client = MultiTenantPostgresClient()

        # Test startup health check
        health_status = client.startup_health_check()

        print(f"Startup Health Status: {health_status.status}")
        print(f"Is Healthy: {'✓ YES' if health_status.is_healthy else '✗ NO'}")
        print(f"Message: {health_status.message}")
        print(f"Response Time: {health_status.response_time_ms:.2f}ms")

        return health_status.is_healthy

    except Exception as e:
        print(f"✗ Startup health check failed: {e}")
        return False


async def test_async_health_check():
    """Test async health check functionality"""
    print("\n=== Testing Async Health Check ===")

    try:
        client = MultiTenantPostgresClient()

        # Test basic async health check
        is_healthy = await client.async_health_check()
        print(
            f"Async basic health check: {'✓ HEALTHY' if is_healthy else '✗ UNHEALTHY'}"
        )

        # Test comprehensive async health check
        health_status = await client.async_comprehensive_health_check()

        print(f"Async Health Status: {health_status.status}")
        print(f"Is Healthy: {'✓ YES' if health_status.is_healthy else '✗ NO'}")
        print(f"Message: {health_status.message}")
        print(f"Response Time: {health_status.response_time_ms:.2f}ms")

        return health_status.is_healthy

    except Exception as e:
        print(f"✗ Async health check failed: {e}")
        return False


def test_tenant_specific_health_check():
    """Test tenant-specific health check functionality"""
    print("\n=== Testing Tenant-Specific Health Check ===")

    try:
        client = MultiTenantPostgresClient()

        # Test with tenant ID
        test_tenant_id = "test_tenant_123"
        health_status = client.health_check_with_tenant_support(
            tenant_id=test_tenant_id
        )

        print(f"Tenant Health Status: {health_status.status}")
        print(f"Is Healthy: {'✓ YES' if health_status.is_healthy else '✗ NO'}")
        print(f"Message: {health_status.message}")
        print(f"Response Time: {health_status.response_time_ms:.2f}ms")

        return health_status.is_healthy

    except Exception as e:
        print(f"✗ Tenant-specific health check failed: {e}")
        return False


async def test_async_tenant_health_check():
    """Test async tenant-specific health check functionality"""
    print("\n=== Testing Async Tenant-Specific Health Check ===")

    try:
        client = MultiTenantPostgresClient()

        # Test with tenant ID
        test_tenant_id = "test_tenant_456"
        health_status = await client.async_health_check_with_tenant_support(
            tenant_id=test_tenant_id
        )

        print(f"Async Tenant Health Status: {health_status.status}")
        print(f"Is Healthy: {'✓ YES' if health_status.is_healthy else '✗ NO'}")
        print(f"Message: {health_status.message}")
        print(f"Response Time: {health_status.response_time_ms:.2f}ms")

        return health_status.is_healthy

    except Exception as e:
        print(f"✗ Async tenant-specific health check failed: {e}")
        return False


def test_convenience_functions():
    """Test convenience functions for health checks"""
    print("\n=== Testing Convenience Functions ===")

    try:
        # Test comprehensive health check function
        health_status = comprehensive_database_health_check()
        print(
            f"Convenience comprehensive check: {'✓ HEALTHY' if health_status.is_healthy else '✗ UNHEALTHY'}"
        )

        # Test startup health check function
        startup_status = startup_database_health_check()
        print(
            f"Convenience startup check: {'✓ HEALTHY' if startup_status.is_healthy else '✗ UNHEALTHY'}"
        )

        # Test connection pool metrics function
        metrics = get_database_connection_pool_metrics()
        print(f"Connection pool metrics retrieved: ✓ YES")
        print(f"  - Pool Size: {metrics.pool_size}")
        print(f"  - Active Connections: {metrics.checked_out}")

        return health_status.is_healthy and startup_status.is_healthy

    except Exception as e:
        print(f"✗ Convenience functions test failed: {e}")
        return False


async def test_async_convenience_functions():
    """Test async convenience functions"""
    print("\n=== Testing Async Convenience Functions ===")

    try:
        # Test async comprehensive health check function
        health_status = await async_comprehensive_database_health_check()
        print(
            f"Async convenience check: {'✓ HEALTHY' if health_status.is_healthy else '✗ UNHEALTHY'}"
        )

        return health_status.is_healthy

    except Exception as e:
        print(f"✗ Async convenience functions test failed: {e}")
        return False


def test_credential_sanitization():
    """Test that credentials are properly sanitized in logs"""
    print("\n=== Testing Credential Sanitization ===")

    try:
        client = MultiTenantPostgresClient()

        # Test URL sanitization
        test_url = "postgresql://user:secret_password@localhost:5432/testdb"
        sanitized = client._sanitize_database_url(test_url)

        print(f"Original URL: {test_url}")
        print(f"Sanitized URL: {sanitized}")

        # Check that password is not exposed
        if "secret_password" not in sanitized and "****" in sanitized:
            print("✓ Credentials properly sanitized")
            return True
        else:
            print("✗ Credentials not properly sanitized")
            return False

    except Exception as e:
        print(f"✗ Credential sanitization test failed: {e}")
        return False


def test_performance_metrics():
    """Test performance metrics collection"""
    print("\n=== Testing Performance Metrics ===")

    try:
        client = MultiTenantPostgresClient()

        # Run multiple health checks to test performance
        times = []
        for i in range(5):
            start_time = time.time()
            health_status = client.comprehensive_health_check()
            end_time = time.time()

            response_time = (end_time - start_time) * 1000
            times.append(response_time)

            print(
                f"Check {i+1}: {response_time:.2f}ms - {'✓' if health_status.is_healthy else '✗'}"
            )

        avg_time = sum(times) / len(times)
        print(f"Average response time: {avg_time:.2f}ms")

        # Performance should be reasonable (under 1 second)
        if avg_time < 1000:
            print("✓ Performance metrics within acceptable range")
            return True
        else:
            print("✗ Performance metrics outside acceptable range")
            return False

    except Exception as e:
        print(f"✗ Performance metrics test failed: {e}")
        return False


async def main():
    """Run all health check tests"""
    print("Database Health Check Test Suite")
    print("=" * 50)

    # Print current configuration (sanitized)
    try:
        client = MultiTenantPostgresClient()
        sanitized_url = client._sanitize_database_url(settings.database_url)
        print(f"Testing with database: {sanitized_url}")
    except Exception as e:
        print(f"Could not get database configuration: {e}")

    # Run all tests
    test_results = []

    # Synchronous tests
    test_results.append(("Basic Health Check", test_basic_health_check()))
    test_results.append(
        ("Comprehensive Health Check", test_comprehensive_health_check())
    )
    test_results.append(("Startup Health Check", test_startup_health_check()))
    test_results.append(
        ("Tenant-Specific Health Check", test_tenant_specific_health_check())
    )
    test_results.append(("Convenience Functions", test_convenience_functions()))
    test_results.append(("Credential Sanitization", test_credential_sanitization()))
    test_results.append(("Performance Metrics", test_performance_metrics()))

    # Asynchronous tests
    test_results.append(("Async Health Check", await test_async_health_check()))
    test_results.append(
        ("Async Tenant Health Check", await test_async_tenant_health_check())
    )
    test_results.append(
        ("Async Convenience Functions", await test_async_convenience_functions())
    )

    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:<35} {status}")
        if result:
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All health check tests passed!")
        return 0
    else:
        print("❌ Some health check tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
