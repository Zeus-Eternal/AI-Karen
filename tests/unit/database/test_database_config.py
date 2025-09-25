"""
Unit tests for database configuration validation module.
"""

import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from src.ai_karen_engine.database.config import (
    DatabaseConfig,
    DatabaseConfigurationError,
    DatabaseConfigLoader,
    load_database_config,
    validate_database_connection
)


class TestDatabaseConfig:
    """Test DatabaseConfig class."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = DatabaseConfig()
        
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.user == "postgres"
        assert config.password == ""
        assert config.database == "ai_karen"
        assert config.pool_size == 10
        assert config.max_overflow == 20
        assert config.pool_timeout == 30
        assert config.pool_recycle == 3600
        assert config.ssl_mode == "prefer"
        assert config.debug_sql is False
        assert config.url is None
    
    def test_valid_configuration(self):
        """Test valid configuration."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            user="testuser",
            password="testpass",
            database="testdb"
        )
        
        assert config.is_valid()
        assert len(config.validation_errors) == 0
        assert len(config.validation_warnings) == 0
    
    def test_empty_host_validation(self):
        """Test validation with empty host."""
        config = DatabaseConfig(host="")
        
        assert not config.is_valid()
        assert "Database host cannot be empty" in config.validation_errors
    
    def test_invalid_port_validation(self):
        """Test validation with invalid port."""
        config = DatabaseConfig(port=0)
        assert not config.is_valid()
        assert "Invalid database port: 0" in config.validation_errors[0]
        
        config = DatabaseConfig(port=70000)
        assert not config.is_valid()
        assert "Invalid database port: 70000" in config.validation_errors[0]
    
    def test_empty_user_validation(self):
        """Test validation with empty user."""
        config = DatabaseConfig(user="")
        
        assert not config.is_valid()
        assert "Database user cannot be empty" in config.validation_errors
    
    def test_empty_password_warning(self):
        """Test warning for empty password."""
        config = DatabaseConfig(password="")
        
        assert "Database password is empty" in config.validation_warnings[0]
    
    def test_invalid_database_name_validation(self):
        """Test validation with invalid database name."""
        config = DatabaseConfig(database="")
        assert not config.is_valid()
        assert "Database name cannot be empty" in config.validation_errors
        
        config = DatabaseConfig(database="123invalid")
        assert not config.is_valid()
        assert "Invalid database name: 123invalid" in config.validation_errors[0]
    
    def test_invalid_pool_configuration(self):
        """Test validation with invalid pool configuration."""
        config = DatabaseConfig(pool_size=0)
        assert not config.is_valid()
        assert "Pool size must be positive: 0" in config.validation_errors
        
        config = DatabaseConfig(max_overflow=-1)
        assert not config.is_valid()
        assert "Max overflow cannot be negative: -1" in config.validation_errors
    
    def test_invalid_ssl_mode(self):
        """Test validation with invalid SSL mode."""
        config = DatabaseConfig(ssl_mode="invalid")
        
        assert not config.is_valid()
        assert "Invalid SSL mode: invalid" in config.validation_errors[0]
    
    def test_invalid_url_validation(self):
        """Test validation with invalid URL."""
        config = DatabaseConfig(url="invalid://url")
        
        assert not config.is_valid()
        assert "Invalid database URL scheme: invalid" in config.validation_errors[0]
        
        config = DatabaseConfig(url="postgresql://")
        assert not config.is_valid()
        assert "Database URL must contain a hostname" in config.validation_errors
    
    def test_build_database_url(self):
        """Test database URL building."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            user="testuser",
            password="testpass",
            database="testdb"
        )
        
        url = config.build_database_url()
        assert url == "postgresql://testuser:testpass@localhost:5432/testdb"
    
    def test_build_database_url_with_special_chars(self):
        """Test database URL building with special characters in password."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            user="testuser",
            password="test@pass:with/special",
            database="testdb"
        )
        
        url = config.build_database_url()
        assert url == "postgresql://testuser:test%40pass%3Awith%2Fspecial@localhost:5432/testdb"
    
    def test_build_database_url_with_ssl(self):
        """Test database URL building with SSL parameters."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            user="testuser",
            password="testpass",
            database="testdb",
            ssl_mode="require",
            ssl_cert="/path/to/cert.pem"
        )
        
        url = config.build_database_url()
        assert "sslmode=require" in url
        assert "sslcert=/path/to/cert.pem" in url
    
    def test_build_async_database_url(self):
        """Test async database URL building."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            user="testuser",
            password="testpass",
            database="testdb"
        )
        
        url = config.build_async_database_url()
        assert url == "postgresql+asyncpg://testuser:testpass@localhost:5432/testdb"
    
    def test_url_override(self):
        """Test URL override functionality."""
        config = DatabaseConfig(url="postgresql://custom:pass@custom:5433/customdb")
        
        url = config.build_database_url()
        assert url == "postgresql://custom:pass@custom:5433/customdb"
    
    def test_get_sanitized_config(self):
        """Test sanitized configuration output."""
        config = DatabaseConfig(
            user="testuser",
            password="secretpass",
            database="testdb"
        )
        
        sanitized = config.get_sanitized_config()
        
        assert sanitized["user"] == "testuser"
        assert sanitized["password"] == "***"
        assert sanitized["database"] == "testdb"
        assert "validation_status" in sanitized
    
    def test_validation_summary(self):
        """Test validation summary."""
        config = DatabaseConfig(host="", port=0)
        
        summary = config.get_validation_summary()
        
        assert summary["valid"] is False
        assert summary["error_count"] > 0
        assert len(summary["errors"]) > 0
        assert isinstance(summary["warnings"], list)


class TestDatabaseConfigLoader:
    """Test DatabaseConfigLoader class."""
    
    def test_load_from_environment_with_all_vars(self):
        """Test loading configuration with all environment variables set."""
        env_vars = {
            "POSTGRES_HOST": "testhost",
            "POSTGRES_PORT": "5433",
            "POSTGRES_USER": "testuser",
            "POSTGRES_PASSWORD": "testpass",
            "POSTGRES_DB": "testdb",
            "DB_POOL_SIZE": "15",
            "DB_MAX_OVERFLOW": "25",
            "SQL_DEBUG": "true"
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = DatabaseConfigLoader.load_from_environment()
            
            assert config.host == "testhost"
            assert config.port == 5433
            assert config.user == "testuser"
            assert config.password == "testpass"
            assert config.database == "testdb"
            assert config.pool_size == 15
            assert config.max_overflow == 25
            assert config.debug_sql is True
    
    def test_load_from_environment_with_url_override(self):
        """Test loading configuration with DATABASE_URL override."""
        env_vars = {
            "DATABASE_URL": "postgresql://urluser:urlpass@urlhost:5434/urldb",
            "POSTGRES_HOST": "ignored",
            "POSTGRES_USER": "ignored"
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = DatabaseConfigLoader.load_from_environment()
            
            assert config.url == "postgresql://urluser:urlpass@urlhost:5434/urldb"
    
    def test_load_from_environment_with_missing_vars(self):
        """Test loading configuration with missing critical variables."""
        # Clear relevant environment variables
        env_vars_to_clear = [
            "POSTGRES_HOST", "DATABASE_HOST", "DB_HOST",
            "POSTGRES_USER", "DATABASE_USER", "DB_USER",
            "POSTGRES_PASSWORD", "DATABASE_PASSWORD", "DB_PASSWORD",
            "POSTGRES_DB", "DATABASE_NAME", "DB_NAME"
        ]
        
        with patch.dict(os.environ, {}, clear=False):
            # Remove variables that might exist
            for var in env_vars_to_clear:
                os.environ.pop(var, None)
            
            config = DatabaseConfigLoader.load_from_environment()
            
            # Should have warnings about missing variables
            assert len(config.validation_warnings) > 0
            assert any("Environment variable not found" in warning for warning in config.validation_warnings)
    
    def test_load_from_environment_with_invalid_values(self):
        """Test loading configuration with invalid environment variable values."""
        env_vars = {
            "POSTGRES_PORT": "invalid_port",
            "DB_POOL_SIZE": "not_a_number"
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = DatabaseConfigLoader.load_from_environment()
            
            # Should use default values for invalid integers
            assert config.port == 5432  # default
            assert config.pool_size == 10  # default
    
    def test_load_env_file(self):
        """Test loading environment variables from .env file."""
        env_content = """
# Test .env file
POSTGRES_HOST=filehost
POSTGRES_PORT=5433
POSTGRES_USER=fileuser
POSTGRES_PASSWORD="file pass with spaces"
POSTGRES_DB=filedb

# Comment line
INVALID_LINE_WITHOUT_EQUALS

SQL_DEBUG=true
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(env_content)
            f.flush()
            
            try:
                # Clear environment first
                for var in ["POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "SQL_DEBUG"]:
                    os.environ.pop(var, None)
                
                config = DatabaseConfigLoader.load_from_environment(f.name)
                
                assert config.host == "filehost"
                assert config.port == 5433
                assert config.user == "fileuser"
                assert config.password == "file pass with spaces"
                assert config.database == "filedb"
                assert config.debug_sql is True
                
            finally:
                os.unlink(f.name)
    
    def test_load_env_file_with_variable_substitution(self):
        """Test loading .env file with variable substitution."""
        env_content = """
POSTGRES_USER=testuser
POSTGRES_PASSWORD=testpass
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/testdb
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(env_content)
            f.flush()
            
            try:
                # Clear environment first
                for var in ["POSTGRES_USER", "POSTGRES_PASSWORD", "DATABASE_URL"]:
                    os.environ.pop(var, None)
                
                config = DatabaseConfigLoader.load_from_environment(f.name)
                
                assert config.url == "postgresql://testuser:testpass@localhost:5432/testdb"
                
            finally:
                os.unlink(f.name)


class TestDatabaseConfigurationError:
    """Test DatabaseConfigurationError exception."""
    
    def test_exception_creation(self):
        """Test exception creation with errors and warnings."""
        errors = ["Error 1", "Error 2"]
        warnings = ["Warning 1"]
        
        exc = DatabaseConfigurationError("Test message", errors, warnings)
        
        assert str(exc) == "Test message"
        assert exc.errors == errors
        assert exc.warnings == warnings


class TestLoadDatabaseConfig:
    """Test load_database_config convenience function."""
    
    def test_load_database_config_default(self):
        """Test loading database config with default .env file."""
        with patch.object(DatabaseConfigLoader, 'load_from_environment') as mock_load:
            mock_config = DatabaseConfig()
            mock_load.return_value = mock_config
            
            result = load_database_config()
            
            mock_load.assert_called_once_with(".env")
            assert result == mock_config
    
    def test_load_database_config_custom_path(self):
        """Test loading database config with custom .env file path."""
        with patch.object(DatabaseConfigLoader, 'load_from_environment') as mock_load:
            mock_config = DatabaseConfig()
            mock_load.return_value = mock_config
            
            result = load_database_config("/custom/path/.env")
            
            mock_load.assert_called_once_with("/custom/path/.env")
            assert result == mock_config


class TestValidateDatabaseConnection:
    """Test validate_database_connection function."""
    
    def test_successful_connection_validation(self):
        """Test successful database connection validation."""
        config = DatabaseConfig(
            host="localhost",
            user="testuser",
            password="testpass",
            database="testdb"
        )
        
        # Mock SQLAlchemy components
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_version_result = MagicMock()
        mock_version_result.scalar.return_value = "PostgreSQL 13.0"
        mock_db_result = MagicMock()
        mock_db_result.scalar.return_value = "testdb"
        
        mock_conn.execute.side_effect = [mock_version_result, mock_db_result]
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        
        with patch('src.ai_karen_engine.database.config.create_engine', return_value=mock_engine):
            result = validate_database_connection(config)
            
            assert result["success"] is True
            assert result["error"] is None
            assert result["server_version"] == "PostgreSQL 13.0"
            assert result["database_exists"] is True
            assert result["connection_time"] is not None
    
    def test_failed_connection_validation(self):
        """Test failed database connection validation."""
        config = DatabaseConfig(
            host="nonexistent",
            user="testuser",
            password="testpass",
            database="testdb"
        )
        
        with patch('src.ai_karen_engine.database.config.create_engine', side_effect=Exception("Connection failed")):
            result = validate_database_connection(config)
            
            assert result["success"] is False
            assert result["error"] == "Connection failed"
            assert result["server_version"] is None
            assert result["database_exists"] is False
            assert result["connection_time"] is None


if __name__ == "__main__":
    pytest.main([__file__])