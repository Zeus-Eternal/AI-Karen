#!/usr/bin/env python3
"""
Test script to verify the enhanced MultiTenantPostgresClient implementation.
"""

import os
import sys
import logging
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, 'src')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_config_loading():
    """Test that database configuration loading works correctly."""
    print("Testing database configuration loading...")
    
    # Mock environment variables
    test_env = {
        'POSTGRES_HOST': 'testhost',
        'POSTGRES_PORT': '5433',
        'POSTGRES_USER': 'testuser',
        'POSTGRES_PASSWORD': 'testpass',
        'POSTGRES_DB': 'testdb'
    }
    
    with patch.dict(os.environ, test_env):
        from ai_karen_engine.database.config import load_database_config
        
        config = load_database_config()
        
        assert config.host == 'testhost'
        assert config.port == 5433
        assert config.user == 'testuser'
        assert config.password == 'testpass'
        assert config.database == 'testdb'
        assert config.is_valid()
        
        print("✓ Database configuration loading works correctly")

def test_connection_retry_manager():
    """Test the ConnectionRetryManager functionality."""
    print("Testing ConnectionRetryManager...")
    
    from ai_karen_engine.database.client import ConnectionRetryManager, DatabaseConnectionError
    
    retry_manager = ConnectionRetryManager(max_retries=2, base_delay=0.1, max_delay=1.0)
    
    # Test successful operation
    def successful_operation():
        return "success"
    
    result = retry_manager.execute_with_retry(successful_operation, "test operation")
    assert result == "success"
    
    # Test operation that fails then succeeds
    call_count = 0
    def flaky_operation():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("connection refused")
        return "success"
    
    call_count = 0
    result = retry_manager.execute_with_retry(flaky_operation, "flaky operation")
    assert result == "success"
    assert call_count == 2
    
    # Test operation that always fails
    def failing_operation():
        raise Exception("authentication failed")
    
    try:
        retry_manager.execute_with_retry(failing_operation, "failing operation")
        assert False, "Should have raised DatabaseConnectionError"
    except DatabaseConnectionError as e:
        assert "authentication" in e.error_type
    
    print("✓ ConnectionRetryManager works correctly")

def test_error_classification():
    """Test error classification functionality."""
    print("Testing error classification...")
    
    from ai_karen_engine.database.client import ConnectionRetryManager
    
    retry_manager = ConnectionRetryManager()
    
    # Test authentication error
    auth_error = Exception("password authentication failed for user 'postgres'")
    assert retry_manager._classify_error(auth_error) == "authentication"
    
    # Test connection error
    conn_error = Exception("connection refused")
    assert retry_manager._classify_error(conn_error) == "connection"
    
    # Test database not found error
    db_error = Exception("database does not exist")
    assert retry_manager._classify_error(db_error) == "database_not_found"
    
    # Test timeout error
    timeout_error = Exception("connection timed out")
    assert retry_manager._classify_error(timeout_error) == "connection"  # "timed out" is classified as connection error
    
    print("✓ Error classification works correctly")

def test_client_initialization():
    """Test MultiTenantPostgresClient initialization with enhanced error handling."""
    print("Testing client initialization...")
    
    # Mock the database configuration
    with patch('ai_karen_engine.database.client.load_database_config') as mock_load_config:
        from ai_karen_engine.database.config import DatabaseConfig
        from ai_karen_engine.database.client import MultiTenantPostgresClient
        
        # Create a valid config
        config = DatabaseConfig(
            host='localhost',
            port=5432,
            user='testuser',
            password='testpass',
            database='testdb'
        )
        mock_load_config.return_value = config
        
        # Mock SQLAlchemy components
        with patch('ai_karen_engine.database.client.create_engine') as mock_create_engine, \
             patch('ai_karen_engine.database.client.sessionmaker') as mock_sessionmaker:
            
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            
            # Mock successful connection test
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn
            
            client = MultiTenantPostgresClient()
            
            # Verify configuration was loaded
            assert client.config == config
            assert client.database_url == config.build_database_url()
            
            # Verify retry manager was initialized
            assert hasattr(client, '_retry_manager')
            
            print("✓ Client initialization works correctly")

def test_health_check_enhancement():
    """Test enhanced health check functionality."""
    print("Testing enhanced health check...")
    
    # Test that health check returns proper structure
    from ai_karen_engine.database.config import DatabaseConfig
    from ai_karen_engine.database.client import MultiTenantPostgresClient
    
    config = DatabaseConfig(
        host='localhost',
        port=5432,
        user='testuser',
        password='testpass',
        database='testdb'
    )
    
    with patch('ai_karen_engine.database.client.load_database_config', return_value=config), \
         patch('ai_karen_engine.database.client.create_engine') as mock_create_engine, \
         patch('ai_karen_engine.database.client.sessionmaker'):
        
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        # Mock successful connection for initialization
        mock_conn_init = MagicMock()
        mock_context_init = MagicMock()
        mock_context_init.__enter__.return_value = mock_conn_init
        mock_context_init.__exit__.return_value = None
        
        # Mock pool
        mock_pool = MagicMock()
        mock_pool.size.return_value = 10
        mock_pool.checkedin.return_value = 8
        mock_pool.checkedout.return_value = 2
        mock_pool.overflow.return_value = 0
        mock_pool.invalid.return_value = 0
        mock_engine.pool = mock_pool
        
        # First call for initialization (success), second call for health check (failure)
        mock_engine.connect.side_effect = [mock_context_init, Exception("health check failed")]
        
        client = MultiTenantPostgresClient(config=config)
        health_result = client.health_check()
        
        # Should return unhealthy status with proper error information
        assert health_result['status'] == 'unhealthy'
        assert 'error' in health_result
        assert 'error_type' in health_result
        assert 'timestamp' in health_result
        assert 'pool_config' in health_result
        
        print("✓ Enhanced health check works correctly")

def main():
    """Run all tests."""
    print("Running enhanced MultiTenantPostgresClient tests...\n")
    
    try:
        test_database_config_loading()
        test_connection_retry_manager()
        test_error_classification()
        test_client_initialization()
        test_health_check_enhancement()
        
        print("\n✅ All tests passed! The enhanced MultiTenantPostgresClient implementation is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()