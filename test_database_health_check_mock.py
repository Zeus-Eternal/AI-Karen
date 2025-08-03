#!/usr/bin/env python3
"""
Test script for database health check functionality with mocked database.
Tests the success path of the health check implementation.
"""

import asyncio
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from ai_karen_engine.database.client import (
        MultiTenantPostgresClient,
        DatabaseHealthStatus,
        ConnectionPoolMetrics
    )
    print("✓ Successfully imported database health check modules")
except ImportError as e:
    print(f"✗ Failed to import modules: {e}")
    sys.exit(1)


def test_health_check_success_path():
    """Test health check with mocked successful database connection"""
    print("\n=== Testing Health Check Success Path ===")
    
    try:
        # Mock the database connection to simulate success
        with patch('ai_karen_engine.database.client.create_engine') as mock_create_engine, \
             patch('ai_karen_engine.database.client.create_async_engine') as mock_create_async_engine, \
             patch('ai_karen_engine.database.client.sessionmaker') as mock_sessionmaker, \
             patch('ai_karen_engine.database.client.async_sessionmaker') as mock_async_sessionmaker:
            
            # Setup mocks
            mock_engine = Mock()
            mock_async_engine = Mock()
            mock_session = Mock()
            mock_async_session = Mock()
            
            # Mock pool for metrics
            mock_pool = Mock()
            mock_pool.size.return_value = 10
            mock_pool.checkedout.return_value = 2
            mock_pool.overflow.return_value = 0
            mock_pool.checkedin.return_value = 8
            mock_pool.invalidated.return_value = 0
            mock_engine.pool = mock_pool
            
            mock_create_engine.return_value = mock_engine
            mock_create_async_engine.return_value = mock_async_engine
            
            # Mock session factory
            mock_session_factory = Mock()
            mock_session_factory.return_value = mock_session
            mock_sessionmaker.return_value = mock_session_factory
            
            # Mock session context manager
            mock_session.__enter__ = Mock(return_value=mock_session)
            mock_session.__exit__ = Mock(return_value=None)
            
            # Mock execute method to simulate successful query
            mock_session.execute.return_value = None
            mock_session.commit.return_value = None
            mock_session.rollback.return_value = None
            mock_session.close.return_value = None
            
            # Mock database version query result
            mock_result = Mock()
            mock_result.__getitem__ = Mock(return_value="PostgreSQL 13.7 on x86_64-pc-linux-gnu")
            mock_session.execute.return_value.fetchone.return_value = mock_result
            
            # Create client and test
            client = MultiTenantPostgresClient()
            
            # Test basic health check
            is_healthy = client.health_check()
            print(f"Basic health check: {'✓ PASS' if is_healthy else '✗ FAIL'}")
            
            # Test comprehensive health check
            health_status = client.comprehensive_health_check()
            print(f"Comprehensive health check: {'✓ PASS' if health_status.is_healthy else '✗ FAIL'}")
            print(f"  Status: {health_status.status}")
            print(f"  Message: {health_status.message}")
            print(f"  Response Time: {health_status.response_time_ms:.2f}ms")
            
            if health_status.connection_pool_metrics:
                metrics = health_status.connection_pool_metrics
                print(f"  Pool Metrics: size={metrics.pool_size}, active={metrics.checked_out}")
            
            # Test startup health check
            startup_status = client.startup_health_check()
            print(f"Startup health check: {'✓ PASS' if startup_status.is_healthy else '✗ FAIL'}")
            print(f"  Message: {startup_status.message}")
            
            return is_healthy and health_status.is_healthy and startup_status.is_healthy
            
    except Exception as e:
        print(f"✗ Health check success path test failed: {e}")
        return False


async def test_async_health_check_success_path():
    """Test async health check with mocked successful database connection"""
    print("\n=== Testing Async Health Check Success Path ===")
    
    try:
        # Mock the database connection to simulate success
        with patch('ai_karen_engine.database.client.create_engine') as mock_create_engine, \
             patch('ai_karen_engine.database.client.create_async_engine') as mock_create_async_engine, \
             patch('ai_karen_engine.database.client.sessionmaker') as mock_sessionmaker, \
             patch('ai_karen_engine.database.client.async_sessionmaker') as mock_async_sessionmaker:
            
            # Setup mocks
            mock_engine = Mock()
            mock_async_engine = Mock()
            mock_session = Mock()
            mock_async_session = Mock()
            
            # Mock pool for metrics
            mock_pool = Mock()
            mock_pool.size.return_value = 10
            mock_pool.checkedout.return_value = 3
            mock_pool.overflow.return_value = 1
            mock_pool.checkedin.return_value = 7
            mock_pool.invalidated.return_value = 0
            mock_engine.pool = mock_pool
            
            mock_create_engine.return_value = mock_engine
            mock_create_async_engine.return_value = mock_async_engine
            
            # Mock async session factory
            mock_async_session_factory = Mock()
            mock_async_session_factory.return_value = mock_async_session
            mock_async_sessionmaker.return_value = mock_async_session_factory
            
            # Mock async session context manager
            mock_async_session.__aenter__ = Mock(return_value=mock_async_session)
            mock_async_session.__aexit__ = Mock(return_value=None)
            
            # Mock async execute method
            async def mock_execute(*args, **kwargs):
                return None
            
            async def mock_commit():
                return None
                
            async def mock_rollback():
                return None
            
            mock_async_session.execute = mock_execute
            mock_async_session.commit = mock_commit
            mock_async_session.rollback = mock_rollback
            
            # Create client and test
            client = MultiTenantPostgresClient()
            
            # Test basic async health check
            is_healthy = await client.async_health_check()
            print(f"Async basic health check: {'✓ PASS' if is_healthy else '✗ FAIL'}")
            
            # Test comprehensive async health check
            health_status = await client.async_comprehensive_health_check()
            print(f"Async comprehensive health check: {'✓ PASS' if health_status.is_healthy else '✗ FAIL'}")
            print(f"  Status: {health_status.status}")
            print(f"  Message: {health_status.message}")
            print(f"  Response Time: {health_status.response_time_ms:.2f}ms")
            
            return is_healthy and health_status.is_healthy
            
    except Exception as e:
        print(f"✗ Async health check success path test failed: {e}")
        return False


def test_connection_pool_metrics():
    """Test connection pool metrics collection"""
    print("\n=== Testing Connection Pool Metrics ===")
    
    try:
        with patch('ai_karen_engine.database.client.create_engine') as mock_create_engine:
            # Setup mock engine with pool
            mock_engine = Mock()
            mock_pool = Mock()
            
            # Mock pool methods
            mock_pool.size.return_value = 15
            mock_pool.checkedout.return_value = 5
            mock_pool.overflow.return_value = 2
            mock_pool.checkedin.return_value = 10
            mock_pool.invalidated.return_value = 1
            
            mock_engine.pool = mock_pool
            mock_create_engine.return_value = mock_engine
            
            client = MultiTenantPostgresClient()
            metrics = client._get_connection_pool_metrics()
            
            print(f"Pool Size: {metrics.pool_size}")
            print(f"Checked Out: {metrics.checked_out}")
            print(f"Overflow: {metrics.overflow}")
            print(f"Checked In: {metrics.checked_in}")
            print(f"Total Connections: {metrics.total_connections}")
            print(f"Invalid Connections: {metrics.invalid_connections}")
            print(f"Timestamp: {metrics.timestamp}")
            
            # Verify metrics are correct
            expected_total = metrics.pool_size + metrics.overflow
            if (metrics.pool_size == 15 and 
                metrics.checked_out == 5 and 
                metrics.total_connections == expected_total):
                print("✓ Connection pool metrics correctly collected")
                return True
            else:
                print("✗ Connection pool metrics incorrect")
                return False
                
    except Exception as e:
        print(f"✗ Connection pool metrics test failed: {e}")
        return False


def test_error_handling_and_logging():
    """Test error handling and logging functionality"""
    print("\n=== Testing Error Handling and Logging ===")
    
    try:
        # Test credential sanitization
        client = MultiTenantPostgresClient()
        
        test_urls = [
            "postgresql://user:password123@localhost:5432/db",
            "postgresql://admin:super_secret@db.example.com:5432/mydb",
            "postgresql://test:@localhost/testdb",  # Empty password
            "invalid_url"  # Invalid URL format
        ]
        
        for url in test_urls:
            sanitized = client._sanitize_database_url(url)
            print(f"Original: {url}")
            print(f"Sanitized: {sanitized}")
            
            # Check that no actual passwords are exposed
            if "password123" not in sanitized and "super_secret" not in sanitized:
                print("✓ Credentials properly sanitized")
            else:
                print("✗ Credentials not properly sanitized")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


async def main():
    """Run all mocked health check tests"""
    print("Database Health Check Test Suite (Mocked)")
    print("=" * 50)
    
    # Run all tests
    test_results = []
    
    # Synchronous tests
    test_results.append(("Health Check Success Path", test_health_check_success_path()))
    test_results.append(("Connection Pool Metrics", test_connection_pool_metrics()))
    test_results.append(("Error Handling and Logging", test_error_handling_and_logging()))
    
    # Asynchronous tests
    test_results.append(("Async Health Check Success Path", await test_async_health_check_success_path()))
    
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
        print("🎉 All mocked health check tests passed!")
        return 0
    else:
        print("❌ Some mocked health check tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)