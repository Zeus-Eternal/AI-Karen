"""
Tests for database configuration functionality.

Tests database connection settings, validation, and error handling.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validate_database_config import (
    validate_database_connection,
    get_database_connection_status,
    DatabaseConfigError,
    DatabaseConnectionStatus
)


class TestDatabaseConnectionValidation:
    """Test database connection validation functionality."""
    
    def test_valid_postgresql_config(self):
        """Test validation of valid PostgreSQL configuration."""
        valid_config = {
            "type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "username": "test_user",
            "password": "test_password",
            "ssl_mode": "require"
        }
        
        result = validate_database_connection(valid_config)
        
        assert result.is_valid is True
        assert result.config_type == "postgresql"
        assert result.connection_string is not None
    
    def test_valid_redis_config(self):
        """Test validation of valid Redis configuration."""
        valid_config = {
            "type": "redis",
            "host": "localhost",
            "port": 6379,
            "database": 0,
            "password": "test_password"
        }
        
        result = validate_database_connection(valid_config)
        
        assert result.is_valid is True
        assert result.config_type == "redis"
        assert result.connection_string is not None
    
    def test_invalid_config_missing_type(self):
        """Test validation of config with missing type."""
        invalid_config = {
            "host": "localhost",
            "port": 5432,
            "database": "test_db"
        }
        
        result = validate_database_connection(invalid_config)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("type" in error.lower() for error in result.errors)
    
    def test_invalid_config_invalid_port(self):
        """Test validation of config with invalid port."""
        invalid_config = {
            "type": "postgresql",
            "host": "localhost",
            "port": "invalid_port",
            "database": "test_db",
            "username": "test_user",
            "password": "test_password"
        }
        
        result = validate_database_connection(invalid_config)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("port" in error.lower() for error in result.errors)
    
    def test_invalid_config_missing_required_fields(self):
        """Test validation of config with missing required fields."""
        invalid_config = {
            "type": "postgresql"
            # Missing host, database, username, password
        }
        
        result = validate_database_connection(invalid_config)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    def test_unsupported_database_type(self):
        """Test validation of unsupported database type."""
        invalid_config = {
            "type": "unsupported_db",
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "username": "test_user",
            "password": "test_password"
        }
        
        result = validate_database_connection(invalid_config)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("unsupported" in error.lower() for error in result.errors)


class TestDatabaseConnectionStatus:
    """Test database connection status functionality."""
    
    def test_get_connection_status_healthy(self):
        """Test getting status of healthy database connection."""
        with patch('validate_database_config.check_database_health') as mock_health_check:
            mock_health_check.return_value = {
                "status": "healthy",
                "response_time": 0.05,
                "last_check": "2023-01-01T00:00:00Z"
            }
            
            status = get_database_connection_status("postgresql")
            
            assert status.status == DatabaseConnectionStatus.HEALTHY
            assert status.response_time == 0.05
            assert status.last_check == "2023-01-01T00:00:00Z"
    
    def test_get_connection_status_degraded(self):
        """Test getting status of degraded database connection."""
        with patch('validate_database_config.check_database_health') as mock_health_check:
            mock_health_check.return_value = {
                "status": "degraded",
                "response_time": 0.5,
                "last_check": "2023-01-01T00:00:00Z",
                "error": "High latency detected"
            }
            
            status = get_database_connection_status("postgresql")
            
            assert status.status == DatabaseConnectionStatus.DEGRADED
            assert status.response_time == 0.5
            assert status.error == "High latency detected"
    
    def test_get_connection_status_unhealthy(self):
        """Test getting status of unhealthy database connection."""
        with patch('validate_database_config.check_database_health') as mock_health_check:
            mock_health_check.return_value = {
                "status": "unhealthy",
                "response_time": None,
                "last_check": "2023-01-01T00:00:00Z",
                "error": "Connection failed"
            }
            
            status = get_database_connection_status("postgresql")
            
            assert status.status == DatabaseConnectionStatus.UNHEALTHY
            assert status.response_time is None
            assert status.error == "Connection failed"
    
    def test_get_connection_status_with_exception(self):
        """Test getting status when health check raises exception."""
        with patch('validate_database_config.check_database_health', side_effect=Exception("Database error")):
            status = get_database_connection_status("postgresql")
            
            assert status.status == DatabaseConnectionStatus.ERROR
            assert "Database error" in status.error


class TestDatabaseConfigError:
    """Test DatabaseConfigError exception class."""
    
    def test_database_config_error_creation(self):
        """Test creating DatabaseConfigError with message."""
        error = DatabaseConfigError("Test error message")
        
        assert str(error) == "Test error message"
        assert "DatabaseConfigError" in str(type(error))
    
    def test_database_config_error_with_code(self):
        """Test creating DatabaseConfigError with message and code."""
        error = DatabaseConfigError("Test error", code="DB001")
        
        assert str(error) == "Test error"
        assert error.code == "DB001"
    
    def test_database_config_error_with_details(self):
        """Test creating DatabaseConfigError with message and details."""
        details = {"host": "localhost", "port": 5432}
        error = DatabaseConfigError("Test error", details=details)
        
        assert str(error) == "Test error"
        assert error.details == details


class TestDatabaseConfigIntegration:
    """Test database configuration integration with other components."""
    
    @patch('validate_database_config.psycopg2')
    @patch('validate_database_config.redis')
    def test_postgresql_connection_string_generation(self, mock_redis, mock_psycopg2):
        """Test PostgreSQL connection string generation."""
        from validate_database_config import generate_postgresql_connection_string
        
        mock_psycopg2.connect.return_value = Mock()  # Mock successful connection
        
        config = {
            "type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "username": "test_user",
            "password": "test_password",
            "ssl_mode": "require"
        }
        
        connection_string = generate_postgresql_connection_string(config)
        
        # Verify the connection string format
        assert "postgresql://" in connection_string
        assert "test_user" in connection_string
        assert "test_password" in connection_string
        assert "localhost" in connection_string
        assert "5432" in connection_string
        assert "test_db" in connection_string
    
    @patch('validate_database_config.redis')
    def test_redis_connection_string_generation(self, mock_redis):
        """Test Redis connection string generation."""
        from validate_database_config import generate_redis_connection_string
        
        config = {
            "type": "redis",
            "host": "localhost",
            "port": 6379,
            "database": 0,
            "password": "test_password"
        }
        
        connection_string = generate_redis_connection_string(config)
        
        # Verify the connection string format
        assert "redis://" in connection_string
        assert "test_password" in connection_string
        assert "localhost" in connection_string
        assert "6379" in connection_string
        assert "0" in connection_string
    
    def test_database_connection_retry_logic(self):
        """Test database connection retry logic."""
        with patch('validate_database_config.time.sleep') as mock_sleep:
            with patch('validate_database_config.check_database_health') as mock_health_check:
                # First attempt fails
                mock_health_check.side_effect = [
                    {"status": "unhealthy", "error": "Connection failed"},
                    {"status": "healthy"}  # Second attempt succeeds
                ]
                
                from validate_database_config import connect_with_retry
                
                config = {
                    "type": "postgresql",
                    "host": "localhost",
                    "port": 5432,
                    "database": "test_db",
                    "username": "test_user",
                    "password": "test_password"
                }
                
                # Should retry and succeed
                result = connect_with_retry(config, max_retries=2)
                
                assert result is not None
                # Verify sleep was called for retry
                mock_sleep.assert_called_once_with(1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])