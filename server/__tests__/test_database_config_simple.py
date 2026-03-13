"""
Tests for database configuration functionality.

Tests database connection settings, validation, and error handling.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
        
        # Mock the validation function
        with patch('server.validate_database_config.validate_database_connection') as mock_validate:
            mock_validate.return_value = Mock(is_valid=True, config_type="postgresql", connection_string=None)
            
            # Import and call the function
            from validate_database_config import validate_database_connection
            result = validate_database_connection(valid_config)
            
            assert result.is_valid is True
            assert result.config_type == "postgresql"
    
    def test_valid_redis_config(self):
        """Test validation of valid Redis configuration."""
        valid_config = {
            "type": "redis",
            "host": "localhost",
            "port": 6379,
            "database": 0,
            "password": "test_password"
        }
        
        # Mock the validation function
        with patch('server.validate_database_config.validate_database_connection') as mock_validate:
            mock_validate.return_value = Mock(is_valid=True, config_type="redis", connection_string=None)
            
            # Import and call the function
            from validate_database_config import validate_database_connection
            result = validate_database_connection(valid_config)
            
            assert result.is_valid is True
            assert result.config_type == "redis"
    
    def test_invalid_config_missing_type(self):
        """Test validation of config with missing type."""
        invalid_config = {
            "host": "localhost",
            "port": 5432,
            "database": "test_db"
        }
        
        # Mock the validation function
        with patch('server.validate_database_config.validate_database_connection') as mock_validate:
            mock_validate.return_value = Mock(is_valid=False, errors=["Missing required field: type"])
            
            # Import and call the function
            from validate_database_config import validate_database_connection
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
        
        # Mock the validation function
        with patch('server.validate_database_config.validate_database_connection') as mock_validate:
            mock_validate.return_value = Mock(is_valid=False, errors=["Invalid port number"])
            
            # Import and call the function
            from validate_database_config import validate_database_connection
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
        
        # Mock the validation function
        with patch('server.validate_database_config.validate_database_connection') as mock_validate:
            mock_validate.return_value = Mock(is_valid=False, errors=["Missing required fields"])
            
            # Import and call the function
            from validate_database_config import validate_database_connection
            result = validate_database_connection(invalid_config)
            
            assert result.is_valid is False
            assert len(result.errors) > 0
            assert any("required" in error.lower() for error in result.errors)
    
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
        
        # Mock the validation function
        with patch('server.validate_database_config.validate_database_connection') as mock_validate:
            mock_validate.return_value = Mock(is_valid=False, errors=["Unsupported database type"])
            
            # Import and call the function
            from validate_database_config import validate_database_connection
            result = validate_database_connection(invalid_config)
            
            assert result.is_valid is False
            assert len(result.errors) > 0
            assert any("unsupported" in error.lower() for error in result.errors)


class TestDatabaseConnectionStatus:
    """Test database connection status functionality."""
    
    def test_get_connection_status_healthy(self):
        """Test getting status of healthy database connection."""
        # Mock the health check function
        with patch('server.validate_database_config.check_database_health') as mock_health_check:
            mock_health_check.return_value = {
                "status": "healthy",
                "response_time": 0.05,
                "last_check": "2023-01-01T00:00:00Z"
            }
            
            # Import and call the function
            from validate_database_config import get_database_connection_status
            status = get_database_connection_status("postgresql")
            
            assert status.status == "healthy"
            assert status.response_time == 0.05
            assert status.last_check == "2023-01-01T00:00:00Z"
    
    def test_get_connection_status_degraded(self):
        """Test getting status of degraded database connection."""
        # Mock the health check function
        with patch('server.validate_database_config.check_database_health') as mock_health_check:
            mock_health_check.return_value = {
                "status": "degraded",
                "response_time": 0.5,
                "last_check": "2023-01-01T00:00:00Z",
                "error": "High latency detected"
            }
            
            # Import and call the function
            from validate_database_config import get_database_connection_status
            status = get_database_connection_status("postgresql")
            
            assert status.status == "degraded"
            assert status.response_time == 0.5
            assert status.error == "High latency detected"
    
    def test_get_connection_status_unhealthy(self):
        """Test getting status of unhealthy database connection."""
        # Mock the health check function
        with patch('server.validate_database_config.check_database_health') as mock_health_check:
            mock_health_check.return_value = {
                "status": "unhealthy",
                "response_time": None,
                "last_check": "2023-01-01T00:00:00Z",
                "error": "Connection failed"
            }
            
            # Import and call the function
            from validate_database_config import get_database_connection_status
            status = get_database_connection_status("postgresql")
            
            assert status.status == "unhealthy"
            assert status.response_time is None
            assert status.error == "Connection failed"
    
    def test_get_connection_status_with_exception(self):
        """Test getting status when health check raises exception."""
        # Mock the health check function to raise exception
        with patch('server.validate_database_config.check_database_health', side_effect=Exception("Database error")):
            # Import and call the function
            from validate_database_config import get_database_connection_status
            status = get_database_connection_status("postgresql")
            
            assert status.status == "error"
            assert "Database error" in status.error


class TestDatabaseConfigError:
    """Test DatabaseConfigError exception class."""
    
    def test_database_config_error_creation(self):
        """Test creating DatabaseConfigError with message."""
        # Import the exception class
        from validate_database_config import DatabaseConfigError
        
        error = DatabaseConfigError("Test error message")
        
        assert str(error) == "Test error message"
        assert "DatabaseConfigError" in str(type(error))
    
    def test_database_config_error_with_code(self):
        """Test creating DatabaseConfigError with message and code."""
        # Import the exception class
        from validate_database_config import DatabaseConfigError
        
        error = DatabaseConfigError("Test error", code="DB001")
        
        assert str(error) == "Test error"
        assert error.code == "DB001"
    
    def test_database_config_error_with_details(self):
        """Test creating DatabaseConfigError with message and details."""
        # Import the exception class
        from validate_database_config import DatabaseConfigError
        
        details = {"host": "localhost", "port": 5432}
        error = DatabaseConfigError("Test error", details=details)
        
        assert str(error) == "Test error"
        assert error.details == details


class TestDatabaseConfigIntegration:
    """Test database configuration integration with other components."""
    
    def test_postgresql_connection_string_generation(self):
        """Test PostgreSQL connection string generation."""
        # Mock psycopg2
        with patch('server.validate_database_config.psycopg2') as mock_psycopg2:
            mock_psycopg2.connect.return_value = Mock()  # Mock successful connection
            
            # Import and call the function
            from validate_database_config import generate_postgresql_connection_string
            
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
    
    def test_redis_connection_string_generation(self):
        """Test Redis connection string generation."""
        # Mock redis
        with patch('server.validate_database_config.redis') as mock_redis:
            mock_redis.return_value = Mock()  # Mock successful connection
            
            # Import and call the function
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])