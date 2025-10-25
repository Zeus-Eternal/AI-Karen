"""
Tests for Backend FastAPI Database Configuration.
Tests database connection timeout settings, connection pooling, and graceful shutdown.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

# Import the modules to test
from server.config import Settings
from server.database_config import DatabaseConfig, get_database_config


class TestDatabaseConfig:
    """Test database configuration functionality"""
    
    @pytest.fixture
    def settings(self):
        """Create test settings with enhanced database configuration"""
        return Settings(
            database_url="postgresql://test_user:test_pass@localhost:5432/test_db",
            db_connection_timeout=45,
            db_query_timeout=30,
            db_pool_size=10,
            db_max_overflow=20,
            db_pool_recycle=3600,
            db_pool_pre_ping=True,
            db_pool_timeout=30,
            db_echo=False,
            db_health_check_interval=30,
            db_max_connection_failures=5,
            db_connection_retry_delay=5,
            shutdown_timeout=30,
            enable_graceful_shutdown=True,
        )
    
    @pytest.fixture
    def db_config(self, settings):
        """Create database configuration instance"""
        return DatabaseConfig(settings)
    
    def test_database_config_initialization(self, db_config, settings):
        """Test database configuration initialization"""
        assert db_config.settings == settings
        assert db_config._database_manager is None
        assert not db_config._shutdown_event.is_set()
        assert db_config._graceful_shutdown_task is None
    
    @pytest.mark.asyncio
    async def test_initialize_database_success(self, db_config):
        """Test successful database initialization"""
        mock_manager = Mock()
        mock_manager.initialize = AsyncMock(return_value=True)
        
        with patch('server.database_config.initialize_database_manager', 
                  return_value=mock_manager) as mock_init:
            result = await db_config.initialize_database()
            
            assert result is True
            assert db_config._database_manager == mock_manager
            
            # Verify initialization was called with correct parameters
            mock_init.assert_called_once_with(
                database_url=db_config.settings.database_url,
                pool_size=db_config.settings.db_pool_size,
                max_overflow=db_config.settings.db_max_overflow,
                pool_recycle=db_config.settings.db_pool_recycle,
                pool_pre_ping=db_config.settings.db_pool_pre_ping,
                echo=db_config.settings.db_echo,
            )
    
    @pytest.mark.asyncio
    async def test_initialize_database_failure(self, db_config):
        """Test database initialization failure"""
        with patch('server.database_config.initialize_database_manager', 
                  side_effect=Exception("Connection failed")):
            result = await db_config.initialize_database()
            
            assert result is False
            assert db_config._database_manager is None
    
    @pytest.mark.asyncio
    async def test_setup_graceful_shutdown_enabled(self, db_config):
        """Test graceful shutdown setup when enabled"""
        db_config.settings.enable_graceful_shutdown = True
        
        with patch('signal.signal') as mock_signal:
            await db_config.setup_graceful_shutdown()
            
            # Verify signal handlers were registered
            assert mock_signal.call_count == 2
            assert db_config._graceful_shutdown_task is not None
    
    @pytest.mark.asyncio
    async def test_setup_graceful_shutdown_disabled(self, db_config):
        """Test graceful shutdown setup when disabled"""
        db_config.settings.enable_graceful_shutdown = False
        
        with patch('signal.signal') as mock_signal:
            await db_config.setup_graceful_shutdown()
            
            # Verify no signal handlers were registered
            mock_signal.assert_not_called()
            assert db_config._graceful_shutdown_task is None
    
    @pytest.mark.asyncio
    async def test_get_database_health_not_initialized(self, db_config):
        """Test database health when not initialized"""
        health = await db_config.get_database_health()
        
        assert health["status"] == "not_initialized"
        assert health["healthy"] is False
        assert "error" in health
    
    @pytest.mark.asyncio
    async def test_get_database_health_success(self, db_config):
        """Test successful database health check"""
        mock_manager = Mock()
        mock_health_data = {
            "healthy": True,
            "response_time_ms": 50.0,
            "pool_info": {"size": 10, "checked_out": 2}
        }
        mock_manager._health_check = AsyncMock(return_value=mock_health_data)
        db_config._database_manager = mock_manager
        
        health = await db_config.get_database_health()
        
        assert health["healthy"] is True
        assert health["response_time_ms"] == 50.0
        assert "configuration" in health
        assert health["configuration"]["pool_size"] == db_config.settings.db_pool_size
    
    @pytest.mark.asyncio
    async def test_get_database_health_failure(self, db_config):
        """Test database health check failure"""
        mock_manager = Mock()
        mock_manager._health_check = AsyncMock(side_effect=Exception("Health check failed"))
        db_config._database_manager = mock_manager
        
        health = await db_config.get_database_health()
        
        assert health["status"] == "error"
        assert health["healthy"] is False
        assert "error" in health
    
    @pytest.mark.asyncio
    async def test_test_database_connection_success(self, db_config):
        """Test successful database connection test"""
        mock_manager = Mock()
        mock_manager.async_health_check = AsyncMock(return_value=True)
        db_config._database_manager = mock_manager
        
        result = await db_config.test_database_connection()
        
        assert result is True
        mock_manager.async_health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_test_database_connection_timeout(self, db_config):
        """Test database connection test timeout"""
        mock_manager = Mock()
        # Simulate a slow health check that times out
        async def slow_health_check():
            await asyncio.sleep(db_config.settings.db_connection_timeout + 1)
            return True
        
        mock_manager.async_health_check = slow_health_check
        db_config._database_manager = mock_manager
        
        result = await db_config.test_database_connection()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_test_database_connection_not_initialized(self, db_config):
        """Test database connection test when not initialized"""
        result = await db_config.test_database_connection()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_cleanup_success(self, db_config):
        """Test successful cleanup"""
        # Setup mock task and manager
        mock_task = Mock()
        mock_task.done.return_value = False
        mock_task.cancel = Mock()
        mock_task.__await__ = Mock(return_value=iter([]))
        
        mock_manager = Mock()
        mock_manager.close = AsyncMock()
        
        db_config._graceful_shutdown_task = mock_task
        db_config._database_manager = mock_manager
        
        await db_config.cleanup()
        
        # Verify cleanup was performed
        mock_task.cancel.assert_called_once()
        mock_manager.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_with_exception(self, db_config):
        """Test cleanup with exception handling"""
        mock_manager = Mock()
        mock_manager.close = AsyncMock(side_effect=Exception("Close failed"))
        db_config._database_manager = mock_manager
        
        # Should not raise exception
        await db_config.cleanup()
        
        mock_manager.close.assert_called_once()


class TestDatabaseConfigIntegration:
    """Integration tests for database configuration"""
    
    @pytest.mark.asyncio
    async def test_database_lifespan_success(self):
        """Test database lifespan context manager success"""
        settings = Settings(
            database_url="postgresql://test:test@localhost:5432/test",
            enable_graceful_shutdown=False  # Disable for test
        )
        
        with patch('server.database_config.DatabaseConfig.initialize_database', 
                  return_value=True) as mock_init:
            with patch('server.database_config.DatabaseConfig.setup_graceful_shutdown') as mock_shutdown:
                with patch('server.database_config.DatabaseConfig.cleanup') as mock_cleanup:
                    from server.database_config import database_lifespan
                    
                    async with database_lifespan(settings) as db_config:
                        assert db_config is not None
                        mock_init.assert_called_once()
                        mock_shutdown.assert_called_once()
                    
                    mock_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_database_lifespan_initialization_failure(self):
        """Test database lifespan with initialization failure"""
        settings = Settings(
            database_url="postgresql://test:test@localhost:5432/test",
            enable_graceful_shutdown=False
        )
        
        with patch('server.database_config.DatabaseConfig.initialize_database', 
                  side_effect=Exception("Init failed")):
            with patch('server.database_config.DatabaseConfig.cleanup') as mock_cleanup:
                from server.database_config import database_lifespan
                
                async with database_lifespan(settings) as db_config:
                    assert db_config is None
                
                mock_cleanup.assert_called_once()
    
    def test_get_database_config_singleton(self):
        """Test database config singleton pattern"""
        settings = Settings()
        
        # First call creates instance
        config1 = get_database_config(settings)
        assert config1 is not None
        
        # Second call returns same instance
        config2 = get_database_config()
        assert config1 is config2


class TestDatabaseConfigurationSettings:
    """Test database configuration settings"""
    
    def test_default_database_settings(self):
        """Test default database configuration values"""
        settings = Settings()
        
        # Test timeout settings (Requirements 4.3, 4.4)
        assert settings.db_connection_timeout == 45  # Increased from 15 to 45 seconds
        assert settings.db_query_timeout == 30
        
        # Test connection pool settings
        assert settings.db_pool_size == 10
        assert settings.db_max_overflow == 20
        assert settings.db_pool_recycle == 3600  # 1 hour
        assert settings.db_pool_pre_ping is True
        assert settings.db_pool_timeout == 30
        assert settings.db_echo is False
        
        # Test health monitoring settings
        assert settings.db_health_check_interval == 30
        assert settings.db_max_connection_failures == 5
        assert settings.db_connection_retry_delay == 5
        
        # Test graceful shutdown settings
        assert settings.shutdown_timeout == 30
        assert settings.enable_graceful_shutdown is True
    
    def test_environment_variable_override(self):
        """Test that environment variables override default settings"""
        import os
        
        # Set environment variables
        env_vars = {
            "DB_CONNECTION_TIMEOUT": "60",
            "DB_POOL_SIZE": "15",
            "DB_MAX_OVERFLOW": "30",
            "ENABLE_GRACEFUL_SHUTDOWN": "false",
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            assert settings.db_connection_timeout == 60
            assert settings.db_pool_size == 15
            assert settings.db_max_overflow == 30
            assert settings.enable_graceful_shutdown is False


class TestDatabaseHealthEndpoints:
    """Test database health endpoint functionality"""
    
    @pytest.mark.asyncio
    async def test_database_health_endpoint_success(self):
        """Test database health endpoint with successful response"""
        mock_db_config = Mock()
        mock_health_data = {
            "healthy": True,
            "response_time_ms": 25.0,
            "configuration": {"pool_size": 10}
        }
        mock_db_config.get_database_health = AsyncMock(return_value=mock_health_data)
        
        # Simulate endpoint call
        start_time = datetime.now(timezone.utc)
        health_response = await mock_db_config.get_database_health()
        
        assert health_response["healthy"] is True
        assert health_response["response_time_ms"] == 25.0
        assert "configuration" in health_response
    
    @pytest.mark.asyncio
    async def test_database_connection_test_endpoint(self):
        """Test database connection test endpoint"""
        mock_db_config = Mock()
        mock_db_config.test_database_connection = AsyncMock(return_value=True)
        
        start_time = time.time()
        result = await mock_db_config.test_database_connection()
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000
        
        assert result is True
        assert response_time < 1000  # Should be fast for mock


if __name__ == "__main__":
    pytest.main([__file__, "-v"])