"""
Integration tests for Database Health Monitoring

Tests the complete database health monitoring system including:
- DatabaseHealthMonitor integration with ConnectionHealthManager
- Database connection pool monitoring
- Automatic connection recovery mechanisms
- Health metrics collection and reporting
- API endpoints for health monitoring

Requirements: 4.3, 5.1, 5.4
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

import httpx
from fastapi.testclient import TestClient

from server.app import create_app
from server.config import Settings
from server.database_config import DatabaseConfig
from ai_karen_engine.services.database_health_monitor import (
    DatabaseHealthMonitor,
    DatabaseHealthStatus,
    ConnectionPoolStatus,
    initialize_database_health_monitor,
    shutdown_database_health_monitor,
)


class TestDatabaseHealthMonitoringIntegration:
    """Integration tests for database health monitoring system"""

    @pytest.fixture
    def test_settings(self):
        """Test settings with database health monitoring configuration"""
        return Settings(
            database_url="postgresql://test_user:test_pass@localhost:5432/test_db",
            db_pool_size=5,
            db_max_overflow=10,
            db_connection_timeout=30,
            db_query_timeout=20,
            db_health_check_interval=5,
            db_max_connection_failures=3,
            db_connection_retry_delay=2,
            db_pool_recycle=1800,
            db_pool_pre_ping=True,
            db_echo=False,
        )

    @pytest.fixture
    def database_config(self, test_settings):
        """Database configuration instance for testing"""
        return DatabaseConfig(test_settings)

    @pytest.fixture
    def test_app(self, test_settings):
        """FastAPI test application"""
        with patch('server.config.Settings', return_value=test_settings):
            app = create_app()
            return app

    @pytest.fixture
    def test_client(self, test_app):
        """Test client for API endpoints"""
        return TestClient(test_app)

    @pytest.mark.asyncio
    async def test_database_health_monitor_initialization(self, database_config):
        """Test database health monitor initialization through database config"""
        with patch('ai_karen_engine.services.database_connection_manager.initialize_database_manager') as mock_db_manager, \
             patch('ai_karen_engine.services.database_health_monitor.initialize_database_health_monitor') as mock_health_monitor:
            
            # Mock successful initialization
            mock_db_manager.return_value = Mock()
            mock_health_monitor.return_value = Mock()
            
            result = await database_config.initialize_database()
            
            assert result is True
            mock_db_manager.assert_called_once()
            mock_health_monitor.assert_called_once()
            
            # Verify health monitor was called with correct parameters
            call_args = mock_health_monitor.call_args
            assert call_args[1]['database_url'] == database_config.settings.database_url
            assert call_args[1]['pool_size'] == database_config.settings.db_pool_size
            assert call_args[1]['max_overflow'] == database_config.settings.db_max_overflow
            assert call_args[1]['health_check_interval'] == database_config.settings.db_health_check_interval
            assert call_args[1]['max_connection_failures'] == database_config.settings.db_max_connection_failures
            assert call_args[1]['connection_retry_delay'] == database_config.settings.db_connection_retry_delay
            assert call_args[1]['connection_timeout'] == database_config.settings.db_connection_timeout
            assert call_args[1]['query_timeout'] == database_config.settings.db_query_timeout
            assert call_args[1]['start_monitoring'] is True

    @pytest.mark.asyncio
    async def test_database_health_information_collection(self, database_config):
        """Test comprehensive database health information collection"""
        # Mock database manager
        mock_db_manager = Mock()
        mock_db_manager._health_check = AsyncMock(return_value={
            "status": "healthy",
            "healthy": True,
            "pool_info": {"size": 5, "checked_out": 2}
        })
        database_config._database_manager = mock_db_manager
        
        # Mock database health monitor
        mock_health_monitor = Mock()
        mock_health = Mock()
        mock_health.status.value = "healthy"
        mock_health.is_connected = True
        mock_health.response_time = 45.5
        mock_health.error_count = 0
        mock_health.consecutive_failures = 0
        mock_health.last_success = datetime.utcnow()
        mock_health.last_error = None
        mock_health.degraded_features = []
        mock_health.recovery_attempts = 0
        mock_health.next_recovery_attempt = None
        
        # Mock metrics
        mock_metrics = Mock()
        mock_metrics.pool_size = 5
        mock_metrics.active_connections = 2
        mock_metrics.idle_connections = 3
        mock_metrics.checked_out = 2
        mock_metrics.overflow = 0
        mock_metrics.invalidated = 0
        mock_metrics.pool_status.value = "optimal"
        mock_metrics.query_success_rate = 0.98
        mock_health.metrics = mock_metrics
        
        mock_health_monitor.check_health = AsyncMock(return_value=mock_health)
        database_config._database_health_monitor = mock_health_monitor
        
        # Get health information
        health_info = await database_config.get_database_health()
        
        # Verify comprehensive health information
        assert health_info["status"] == "healthy"
        assert health_info["healthy"] is True
        assert health_info["response_time_ms"] == 45.5
        assert health_info["error_count"] == 0
        assert health_info["consecutive_failures"] == 0
        assert health_info["degraded_features"] == []
        assert health_info["recovery_attempts"] == 0
        
        # Verify pool information
        assert "pool_info" in health_info
        pool_info = health_info["pool_info"]
        assert pool_info["pool_size"] == 5
        assert pool_info["active_connections"] == 2
        assert pool_info["idle_connections"] == 3
        assert pool_info["pool_status"] == "optimal"
        assert pool_info["query_success_rate"] == 0.98
        
        # Verify configuration information
        assert "configuration" in health_info
        config = health_info["configuration"]
        assert config["pool_size"] == database_config.settings.db_pool_size
        assert config["health_check_interval"] == database_config.settings.db_health_check_interval
        assert config["max_connection_failures"] == database_config.settings.db_max_connection_failures

    @pytest.mark.asyncio
    async def test_database_health_monitor_degraded_mode(self, database_config):
        """Test database health monitor in degraded mode"""
        # Mock database health monitor in degraded state
        mock_health_monitor = Mock()
        mock_health = Mock()
        mock_health.status.value = "degraded"
        mock_health.is_connected = False
        mock_health.response_time = 5000.0  # High response time
        mock_health.error_count = 5
        mock_health.consecutive_failures = 2
        mock_health.last_success = datetime.utcnow() - timedelta(minutes=10)
        mock_health.last_error = "Connection timeout"
        mock_health.degraded_features = ["complex_queries", "batch_operations", "reporting"]
        mock_health.recovery_attempts = 2
        mock_health.next_recovery_attempt = datetime.utcnow() + timedelta(seconds=30)
        mock_health.metrics = None  # No metrics in degraded mode
        
        mock_health_monitor.check_health = AsyncMock(return_value=mock_health)
        database_config._database_health_monitor = mock_health_monitor
        
        # Get health information
        health_info = await database_config.get_database_health()
        
        # Verify degraded mode information
        assert health_info["status"] == "degraded"
        assert health_info["healthy"] is False
        assert health_info["error_count"] == 5
        assert health_info["consecutive_failures"] == 2
        assert health_info["last_error"] == "Connection timeout"
        assert "complex_queries" in health_info["degraded_features"]
        assert "batch_operations" in health_info["degraded_features"]
        assert health_info["recovery_attempts"] == 2
        assert health_info["next_recovery_attempt"] is not None

    def test_database_health_api_endpoint(self, test_client):
        """Test database health API endpoint"""
        with patch('server.database_config.get_database_config') as mock_get_config:
            # Mock database config
            mock_config = Mock()
            mock_config.get_database_health = AsyncMock(return_value={
                "status": "healthy",
                "healthy": True,
                "response_time_ms": 25.5,
                "error_count": 0,
                "pool_info": {
                    "pool_size": 5,
                    "active_connections": 2,
                    "checked_out": 2,
                    "pool_status": "optimal"
                },
                "configuration": {
                    "pool_size": 5,
                    "max_overflow": 10,
                    "connection_timeout": 30
                }
            })
            mock_get_config.return_value = mock_config
            
            response = test_client.get("/api/health/database")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "timestamp" in data
            assert "database" in data
            database_info = data["database"]
            assert database_info["status"] == "healthy"
            assert database_info["healthy"] is True
            assert database_info["response_time_ms"] == 25.5
            assert "pool_info" in database_info
            assert "configuration" in database_info

    def test_database_health_monitor_api_endpoint(self, test_client):
        """Test database health monitor specific API endpoint"""
        with patch('server.database_config.get_database_config') as mock_get_config:
            # Mock database config with health monitor
            mock_config = Mock()
            mock_health_monitor = Mock()
            
            # Mock current health
            mock_current_health = Mock()
            mock_current_health.status.value = "healthy"
            mock_current_health.is_connected = True
            mock_current_health.response_time = 35.2
            mock_current_health.error_count = 0
            mock_current_health.consecutive_failures = 0
            mock_current_health.last_check = datetime.utcnow()
            mock_current_health.last_success = datetime.utcnow()
            mock_current_health.last_error = None
            mock_current_health.degraded_features = []
            mock_current_health.recovery_attempts = 0
            mock_current_health.next_recovery_attempt = None
            mock_current_health.metadata = {"test": "data"}
            
            # Mock pool status
            mock_pool_status = {
                "status": "optimal",
                "pool_size": 5,
                "active_connections": 2,
                "idle_connections": 3,
                "usage_ratio": 0.13
            }
            
            # Mock metrics history
            mock_metrics = [
                Mock(
                    timestamp=datetime.utcnow(),
                    connection_count=5,
                    active_connections=2,
                    idle_connections=3,
                    response_time_ms=35.2,
                    query_success_rate=0.99,
                    error_count=0,
                    pool_status=Mock(value="optimal")
                )
            ]
            
            mock_health_monitor.get_current_health.return_value = mock_current_health
            mock_health_monitor.get_pool_status.return_value = mock_pool_status
            mock_health_monitor.get_metrics_history.return_value = mock_metrics
            
            mock_config.get_database_health_monitor.return_value = mock_health_monitor
            mock_get_config.return_value = mock_config
            
            response = test_client.get("/api/health/database/monitor")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "timestamp" in data
            assert "monitor" in data
            assert "pool_status" in data
            assert "metrics_history" in data
            assert "configuration" in data
            
            monitor_info = data["monitor"]
            assert monitor_info["status"] == "healthy"
            assert monitor_info["is_connected"] is True
            assert monitor_info["response_time_ms"] == 35.2
            assert monitor_info["error_count"] == 0
            assert monitor_info["degraded_features"] == []
            
            pool_status = data["pool_status"]
            assert pool_status["status"] == "optimal"
            assert pool_status["pool_size"] == 5
            assert pool_status["active_connections"] == 2
            
            metrics_history = data["metrics_history"]
            assert len(metrics_history) == 1
            assert metrics_history[0]["connection_count"] == 5
            assert metrics_history[0]["pool_status"] == "optimal"

    def test_database_connection_test_endpoint(self, test_client):
        """Test database connection test endpoint"""
        with patch('server.database_config.get_database_config') as mock_get_config:
            mock_config = Mock()
            mock_config.test_database_connection = AsyncMock(return_value=True)
            mock_get_config.return_value = mock_config
            
            response = test_client.get("/api/health/database/test")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "timestamp" in data
            assert "connection_test" in data
            connection_test = data["connection_test"]
            assert connection_test["success"] is True
            assert "response_time_ms" in connection_test
            assert "timeout_configured" in connection_test

    @pytest.mark.asyncio
    async def test_database_health_monitor_recovery_scenario(self):
        """Test database health monitor recovery scenario"""
        database_url = "postgresql://test:test@localhost:5432/test"
        
        # Initialize health monitor
        with patch('ai_karen_engine.services.database_health_monitor.DatabaseHealthMonitor._create_engines'), \
             patch('ai_karen_engine.services.database_health_monitor.DatabaseHealthMonitor._create_session_factories'), \
             patch('ai_karen_engine.services.database_health_monitor.DatabaseHealthMonitor._setup_pool_listeners'):
            
            monitor = await initialize_database_health_monitor(
                database_url=database_url,
                health_check_interval=0.1,  # Fast for testing
                max_connection_failures=2,
                connection_retry_delay=0.1,
                start_monitoring=False,  # Don't start monitoring automatically
            )
            
            # Simulate connection failure
            with patch.object(monitor, '_test_sync_connection', return_value=False), \
                 patch.object(monitor, '_test_async_connection', return_value=False):
                
                health = await monitor.check_health()
                assert health.status in [DatabaseHealthStatus.DEGRADED, DatabaseHealthStatus.UNAVAILABLE]
                assert health.is_connected is False
                assert health.consecutive_failures > 0
            
            # Simulate recovery
            with patch.object(monitor, '_test_sync_connection', return_value=True), \
                 patch.object(monitor, '_test_async_connection', return_value=True), \
                 patch.object(monitor, '_collect_metrics', return_value=None):
                
                health = await monitor.check_health()
                assert health.status == DatabaseHealthStatus.HEALTHY
                assert health.is_connected is True
                assert health.consecutive_failures == 0
            
            # Cleanup
            await shutdown_database_health_monitor()

    @pytest.mark.asyncio
    async def test_database_health_monitor_metrics_collection(self):
        """Test database health monitor metrics collection"""
        database_url = "postgresql://test:test@localhost:5432/test"
        
        with patch('ai_karen_engine.services.database_health_monitor.DatabaseHealthMonitor._create_engines'), \
             patch('ai_karen_engine.services.database_health_monitor.DatabaseHealthMonitor._create_session_factories'), \
             patch('ai_karen_engine.services.database_health_monitor.DatabaseHealthMonitor._setup_pool_listeners'):
            
            monitor = await initialize_database_health_monitor(
                database_url=database_url,
                start_monitoring=False,
            )
            
            # Mock engine with pool
            mock_engine = Mock()
            mock_pool = Mock()
            mock_pool.size = Mock(return_value=5)
            mock_pool.checkedout = Mock(return_value=3)
            mock_pool.overflow = Mock(return_value=1)
            mock_pool.checkedin = Mock(return_value=2)
            mock_pool.invalidated = Mock(return_value=0)
            mock_engine.pool = mock_pool
            monitor.engine = mock_engine
            
            # Set health status for metrics calculation
            monitor._health_status.response_time = 75.5
            monitor._health_status.error_count = 1
            monitor._health_status.is_connected = True
            
            # Collect metrics
            metrics = await monitor._collect_metrics()
            
            assert metrics is not None
            assert metrics.pool_size == 5
            assert metrics.active_connections == 3
            assert metrics.idle_connections == 2
            assert metrics.checked_out == 3
            assert metrics.overflow == 1
            assert metrics.invalidated == 0
            assert metrics.response_time_ms == 75.5
            assert metrics.error_count == 1
            
            # Check pool status calculation
            usage_ratio = 3 / (5 + 10)  # checked_out / (pool_size + max_overflow)
            if usage_ratio >= 0.9:
                expected_status = ConnectionPoolStatus.EXHAUSTED
            elif usage_ratio >= 0.7:
                expected_status = ConnectionPoolStatus.HIGH_USAGE
            else:
                expected_status = ConnectionPoolStatus.OPTIMAL
            
            assert metrics.pool_status == expected_status
            
            # Cleanup
            await shutdown_database_health_monitor()

    @pytest.mark.asyncio
    async def test_database_health_monitor_circuit_breaker(self):
        """Test database health monitor circuit breaker functionality"""
        database_url = "postgresql://test:test@localhost:5432/test"
        
        with patch('ai_karen_engine.services.database_health_monitor.DatabaseHealthMonitor._create_engines'), \
             patch('ai_karen_engine.services.database_health_monitor.DatabaseHealthMonitor._create_session_factories'), \
             patch('ai_karen_engine.services.database_health_monitor.DatabaseHealthMonitor._setup_pool_listeners'):
            
            monitor = await initialize_database_health_monitor(
                database_url=database_url,
                max_connection_failures=3,
                start_monitoring=False,
            )
            
            # Simulate multiple consecutive failures
            with patch.object(monitor, '_test_sync_connection', return_value=False), \
                 patch.object(monitor, '_test_async_connection', return_value=False):
                
                # First few failures should be degraded
                for i in range(2):
                    health = await monitor.check_health()
                    assert health.status == DatabaseHealthStatus.DEGRADED
                    assert health.consecutive_failures == i + 1
                
                # After max failures, should be unavailable
                health = await monitor.check_health()
                assert health.status == DatabaseHealthStatus.UNAVAILABLE
                assert health.consecutive_failures >= monitor.max_connection_failures
            
            # Cleanup
            await shutdown_database_health_monitor()

    @pytest.mark.asyncio
    async def test_database_config_cleanup_with_health_monitor(self, database_config):
        """Test database config cleanup includes health monitor cleanup"""
        # Mock database manager and health monitor
        mock_db_manager = AsyncMock()
        mock_health_monitor = AsyncMock()
        
        database_config._database_manager = mock_db_manager
        database_config._database_health_monitor = mock_health_monitor
        
        # Perform cleanup
        await database_config.cleanup()
        
        # Verify both components were cleaned up
        mock_db_manager.close.assert_called_once()
        mock_health_monitor.cleanup.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])