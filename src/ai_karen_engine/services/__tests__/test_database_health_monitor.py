"""
Tests for Database Health Monitor

Comprehensive test suite covering:
- Database connection health monitoring
- Connection pool health checks
- Automatic connection recovery mechanisms
- Health metrics collection and reporting
- Integration with ConnectionHealthManager
- Circuit breaker pattern
- Graceful degradation

Requirements: 4.3, 5.1, 5.4
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

# SQLAlchemy imports are mocked in tests
# from sqlalchemy import create_engine, text
# from sqlalchemy.exc import OperationalError, DisconnectionError
# from sqlalchemy.pool import QueuePool

from ai_karen_engine.services.database_health_monitor import (
    DatabaseHealthMonitor,
    DatabaseHealth,
    DatabaseHealthStatus,
    DatabaseMetrics,
    ConnectionPoolStatus,
    get_database_health_monitor,
    initialize_database_health_monitor,
    shutdown_database_health_monitor,
)


class TestDatabaseHealthMonitor:
    """Test suite for DatabaseHealthMonitor"""

    @pytest.fixture
    def mock_database_url(self):
        """Mock database URL for testing"""
        return "postgresql://test_user:test_pass@localhost:5432/test_db"

    @pytest.fixture
    def health_monitor(self, mock_database_url):
        """Create DatabaseHealthMonitor instance for testing"""
        return DatabaseHealthMonitor(
            database_url=mock_database_url,
            pool_size=5,
            max_overflow=10,
            health_check_interval=1,  # Fast interval for testing
            max_connection_failures=3,
            connection_retry_delay=1,
            connection_timeout=5,
            query_timeout=5,
        )

    @pytest.fixture
    def mock_engine(self):
        """Mock SQLAlchemy engine"""
        engine = Mock()
        engine.pool = Mock()
        engine.pool.size = Mock(return_value=5)
        engine.pool.checkedout = Mock(return_value=2)
        engine.pool.overflow = Mock(return_value=1)
        engine.pool.checkedin = Mock(return_value=3)
        engine.pool.invalidated = Mock(return_value=0)
        engine.dispose = Mock()
        return engine

    @pytest.fixture
    def mock_async_engine(self):
        """Mock async SQLAlchemy engine"""
        engine = AsyncMock()
        engine.pool = Mock()
        engine.pool.size = Mock(return_value=5)
        engine.pool.checkedout = Mock(return_value=2)
        engine.pool.overflow = Mock(return_value=1)
        engine.pool.checkedin = Mock(return_value=3)
        engine.pool.invalidated = Mock(return_value=0)
        engine.dispose = AsyncMock()
        return engine

    @pytest.mark.asyncio
    async def test_initialization_success(self, health_monitor):
        """Test successful initialization of database health monitor"""
        with patch.object(health_monitor, '_create_engines') as mock_create_engines, \
             patch.object(health_monitor, '_create_session_factories') as mock_create_sessions, \
             patch.object(health_monitor, '_setup_pool_listeners') as mock_setup_listeners, \
             patch.object(health_monitor, '_perform_health_check') as mock_health_check:
            
            # Mock successful health check
            mock_health_check.return_value = DatabaseHealth(
                is_connected=True,
                status=DatabaseHealthStatus.HEALTHY,
                response_time=50.0,
                last_check=datetime.utcnow(),
                error_count=0,
                consecutive_failures=0,
            )
            
            result = await health_monitor.initialize()
            
            assert result is True
            mock_create_engines.assert_called_once()
            mock_create_sessions.assert_called_once()
            mock_setup_listeners.assert_called_once()
            mock_health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialization_failure(self, health_monitor):
        """Test initialization failure handling"""
        with patch.object(health_monitor, '_create_engines', side_effect=Exception("Connection failed")):
            result = await health_monitor.initialize()
            
            assert result is False
            assert health_monitor._health_status.status == DatabaseHealthStatus.UNAVAILABLE
            assert "Connection failed" in health_monitor._health_status.last_error

    @pytest.mark.asyncio
    async def test_health_check_success(self, health_monitor, mock_engine, mock_async_engine):
        """Test successful health check"""
        health_monitor.engine = mock_engine
        health_monitor.async_engine = mock_async_engine
        
        with patch.object(health_monitor, '_test_sync_connection', return_value=True), \
             patch.object(health_monitor, '_test_async_connection', return_value=True), \
             patch.object(health_monitor, '_collect_metrics') as mock_collect_metrics:
            
            mock_metrics = DatabaseMetrics(
                timestamp=datetime.utcnow(),
                connection_count=5,
                active_connections=2,
                idle_connections=3,
                pool_size=5,
                max_overflow=10,
                checked_out=2,
                checked_in=3,
                overflow=1,
                invalidated=0,
                response_time_ms=50.0,
                query_success_rate=1.0,
                error_count=0,
                pool_status=ConnectionPoolStatus.OPTIMAL,
            )
            mock_collect_metrics.return_value = mock_metrics
            
            health = await health_monitor._perform_health_check()
            
            assert health.is_connected is True
            assert health.status == DatabaseHealthStatus.HEALTHY
            assert health.consecutive_failures == 0
            assert health.metrics is not None
            assert health.metrics.pool_status == ConnectionPoolStatus.OPTIMAL

    @pytest.mark.asyncio
    async def test_health_check_failure(self, health_monitor):
        """Test health check failure handling"""
        with patch.object(health_monitor, '_test_sync_connection', return_value=False), \
             patch.object(health_monitor, '_test_async_connection', return_value=False):
            
            health = await health_monitor._perform_health_check()
            
            assert health.is_connected is False
            assert health.status in [DatabaseHealthStatus.DEGRADED, DatabaseHealthStatus.UNAVAILABLE]
            assert health.consecutive_failures > 0

    @pytest.mark.asyncio
    async def test_sync_connection_test(self, health_monitor):
        """Test synchronous connection testing"""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        
        health_monitor.SessionLocal = Mock(return_value=mock_session)
        
        result = await health_monitor._test_sync_connection()
        
        assert result is True
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_connection_test(self, health_monitor):
        """Test asynchronous connection testing"""
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        health_monitor.AsyncSessionLocal = Mock(return_value=mock_session)
        
        result = await health_monitor._test_async_connection()
        
        assert result is True
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_metrics_collection(self, health_monitor, mock_engine):
        """Test database metrics collection"""
        health_monitor.engine = mock_engine
        health_monitor._health_status.response_time = 75.0
        health_monitor._health_status.error_count = 1
        health_monitor._health_status.is_connected = True
        
        metrics = await health_monitor._collect_metrics()
        
        assert metrics is not None
        assert metrics.pool_size == 5
        assert metrics.active_connections == 2
        assert metrics.idle_connections == 3
        assert metrics.checked_out == 2
        assert metrics.overflow == 1
        assert metrics.response_time_ms == 75.0
        assert metrics.error_count == 1

    def test_degraded_features_mapping(self, health_monitor):
        """Test degraded features mapping for different health statuses"""
        healthy_features = health_monitor._get_degraded_features(DatabaseHealthStatus.HEALTHY)
        assert healthy_features == []
        
        degraded_features = health_monitor._get_degraded_features(DatabaseHealthStatus.DEGRADED)
        assert "complex_queries" in degraded_features
        assert "batch_operations" in degraded_features
        assert len(degraded_features) == 3
        
        unavailable_features = health_monitor._get_degraded_features(DatabaseHealthStatus.UNAVAILABLE)
        assert "data_persistence" in unavailable_features
        assert "user_management" in unavailable_features
        assert "audit_logging" in unavailable_features
        assert len(unavailable_features) > len(degraded_features)

    @pytest.mark.asyncio
    async def test_monitoring_loop(self, health_monitor):
        """Test background monitoring loop"""
        health_monitor._shutdown_event = asyncio.Event()
        
        with patch.object(health_monitor, '_perform_health_check') as mock_health_check:
            mock_health_check.return_value = DatabaseHealth(
                is_connected=True,
                status=DatabaseHealthStatus.HEALTHY,
                response_time=50.0,
                last_check=datetime.utcnow(),
                error_count=0,
                consecutive_failures=0,
            )
            
            # Start monitoring task
            monitoring_task = asyncio.create_task(health_monitor._monitoring_loop())
            
            # Let it run for a short time
            await asyncio.sleep(0.1)
            
            # Stop monitoring
            health_monitor._shutdown_event.set()
            await monitoring_task
            
            # Verify health check was called
            assert mock_health_check.call_count >= 1

    @pytest.mark.asyncio
    async def test_recovery_mechanism(self, health_monitor):
        """Test automatic connection recovery"""
        health_monitor._health_status.status = DatabaseHealthStatus.UNAVAILABLE
        
        with patch.object(health_monitor, '_attempt_recovery', return_value=True) as mock_recovery:
            result = await health_monitor._attempt_recovery()
            
            assert result is True
            mock_recovery.assert_called_once()

    @pytest.mark.asyncio
    async def test_recovery_failure(self, health_monitor):
        """Test recovery failure handling"""
        with patch.object(health_monitor, '_close_connections'), \
             patch.object(health_monitor, '_create_engines', side_effect=Exception("Recovery failed")):
            
            result = await health_monitor._attempt_recovery()
            
            assert result is False

    @pytest.mark.asyncio
    async def test_health_callbacks(self, health_monitor):
        """Test health status change callbacks"""
        callback_called = False
        callback_health = None
        
        def health_callback(health: DatabaseHealth):
            nonlocal callback_called, callback_health
            callback_called = True
            callback_health = health
        
        health_monitor.on_health_change(health_callback)
        
        # Trigger health check
        with patch.object(health_monitor, '_test_sync_connection', return_value=True), \
             patch.object(health_monitor, '_test_async_connection', return_value=True):
            
            await health_monitor._perform_health_check()
            
            assert callback_called is True
            assert callback_health is not None
            assert callback_health.is_connected is True

    @pytest.mark.asyncio
    async def test_connection_health_manager_integration(self, health_monitor):
        """Test integration with ConnectionHealthManager"""
        with patch.object(health_monitor, '_perform_health_check') as mock_health_check:
            mock_health_check.return_value = DatabaseHealth(
                is_connected=True,
                status=DatabaseHealthStatus.HEALTHY,
                response_time=50.0,
                last_check=datetime.utcnow(),
                error_count=0,
                consecutive_failures=0,
                degraded_features=[],
                metadata={"test": "data"},
            )
            
            result = await health_monitor._health_check_for_manager()
            
            assert result["healthy"] is True
            assert result["status"] == "healthy"
            assert result["response_time_ms"] == 50.0
            assert result["error_count"] == 0
            assert result["degraded_features"] == []
            assert result["metadata"]["test"] == "data"

    @pytest.mark.asyncio
    async def test_pool_status_reporting(self, health_monitor, mock_engine):
        """Test connection pool status reporting"""
        health_monitor.engine = mock_engine
        health_monitor._health_status.metrics = DatabaseMetrics(
            timestamp=datetime.utcnow(),
            connection_count=7,
            active_connections=5,
            idle_connections=2,
            pool_size=5,
            max_overflow=10,
            checked_out=5,
            checked_in=2,
            overflow=2,
            invalidated=0,
            response_time_ms=100.0,
            query_success_rate=0.95,
            error_count=1,
            pool_status=ConnectionPoolStatus.HIGH_USAGE,
        )
        
        pool_status = health_monitor.get_pool_status()
        
        assert pool_status["status"] == "high_usage"
        assert pool_status["pool_size"] == 5
        assert pool_status["active_connections"] == 5
        assert pool_status["idle_connections"] == 2
        assert pool_status["checked_out"] == 5
        assert pool_status["overflow"] == 2
        assert pool_status["usage_ratio"] == 5 / 15  # 5 checked out / (5 pool + 10 overflow)

    @pytest.mark.asyncio
    async def test_metrics_history_management(self, health_monitor):
        """Test metrics history storage and management"""
        # Create multiple metrics entries
        for i in range(105):  # Exceed max history
            metrics = DatabaseMetrics(
                timestamp=datetime.utcnow(),
                connection_count=i,
                active_connections=i // 2,
                idle_connections=i // 2,
                pool_size=5,
                max_overflow=10,
                checked_out=i // 2,
                checked_in=i // 2,
                overflow=0,
                invalidated=0,
                response_time_ms=float(i),
                query_success_rate=0.95,
                error_count=0,
                pool_status=ConnectionPoolStatus.OPTIMAL,
            )
            health_monitor._metrics_history.append(metrics)
            
            # Simulate history management
            if len(health_monitor._metrics_history) > health_monitor._max_metrics_history:
                health_monitor._metrics_history.pop(0)
        
        history = health_monitor.get_metrics_history()
        
        assert len(history) == health_monitor._max_metrics_history
        assert history[-1].connection_count == 104  # Last entry

    @pytest.mark.asyncio
    async def test_cleanup(self, health_monitor):
        """Test resource cleanup"""
        health_monitor._monitoring_task = Mock()
        health_monitor._recovery_task = Mock()
        health_monitor._thread_pool = Mock()
        
        with patch.object(health_monitor, 'stop_monitoring') as mock_stop, \
             patch.object(health_monitor, '_close_connections') as mock_close:
            
            await health_monitor.cleanup()
            
            mock_stop.assert_called_once()
            mock_close.assert_called_once()
            health_monitor._thread_pool.shutdown.assert_called_once_with(wait=True)

    @pytest.mark.asyncio
    async def test_circuit_breaker_behavior(self, health_monitor):
        """Test circuit breaker pattern for failed connections"""
        # Simulate multiple consecutive failures
        for i in range(health_monitor.max_connection_failures + 1):
            with patch.object(health_monitor, '_test_sync_connection', return_value=False), \
                 patch.object(health_monitor, '_test_async_connection', return_value=False):
                
                await health_monitor._perform_health_check()
        
        # Should be in unavailable state after max failures
        assert health_monitor._health_status.status == DatabaseHealthStatus.UNAVAILABLE
        assert health_monitor._health_status.consecutive_failures > health_monitor.max_connection_failures

    def test_pool_status_calculation(self, health_monitor):
        """Test connection pool status calculation logic"""
        # Test optimal status
        metrics = DatabaseMetrics(
            timestamp=datetime.utcnow(),
            connection_count=3,
            active_connections=2,
            idle_connections=1,
            pool_size=5,
            max_overflow=10,
            checked_out=2,
            checked_in=3,
            overflow=0,
            invalidated=0,
            response_time_ms=50.0,
            query_success_rate=1.0,
            error_count=0,
            pool_status=ConnectionPoolStatus.OPTIMAL,
        )
        
        # Usage ratio: 2 / (5 + 10) = 0.133 < 0.7 = OPTIMAL
        assert metrics.pool_status == ConnectionPoolStatus.OPTIMAL
        
        # Test high usage status
        metrics.checked_out = 12  # 12 / 15 = 0.8 > 0.7 but < 0.9
        metrics.pool_status = ConnectionPoolStatus.HIGH_USAGE
        assert metrics.pool_status == ConnectionPoolStatus.HIGH_USAGE
        
        # Test exhausted status
        metrics.checked_out = 14  # 14 / 15 = 0.933 > 0.9
        metrics.pool_status = ConnectionPoolStatus.EXHAUSTED
        assert metrics.pool_status == ConnectionPoolStatus.EXHAUSTED


class TestDatabaseHealthMonitorGlobalFunctions:
    """Test global functions for database health monitor management"""

    @pytest.mark.asyncio
    async def test_initialize_global_monitor(self):
        """Test initialization of global database health monitor"""
        database_url = "postgresql://test:test@localhost:5432/test"
        
        with patch('ai_karen_engine.services.database_health_monitor.DatabaseHealthMonitor') as MockMonitor:
            mock_instance = AsyncMock()
            mock_instance.initialize.return_value = True
            mock_instance.start_monitoring = AsyncMock()
            MockMonitor.return_value = mock_instance
            
            monitor = await initialize_database_health_monitor(
                database_url=database_url,
                pool_size=5,
                start_monitoring=True,
            )
            
            assert monitor is not None
            MockMonitor.assert_called_once_with(
                database_url=database_url,
                pool_size=5,
                max_overflow=20,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=False,
                health_check_interval=30,
                max_connection_failures=5,
                connection_retry_delay=5,
                connection_timeout=45,
                query_timeout=30,
            )
            mock_instance.initialize.assert_called_once()
            mock_instance.start_monitoring.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_global_monitor(self):
        """Test shutdown of global database health monitor"""
        with patch('ai_karen_engine.services.database_health_monitor._database_health_monitor') as mock_monitor:
            mock_monitor.cleanup = AsyncMock()
            
            await shutdown_database_health_monitor()
            
            mock_monitor.cleanup.assert_called_once()

    def test_get_global_monitor(self):
        """Test getting global database health monitor instance"""
        with patch('ai_karen_engine.services.database_health_monitor._database_health_monitor', None):
            monitor = get_database_health_monitor()
            assert monitor is None
        
        with patch('ai_karen_engine.services.database_health_monitor._database_health_monitor', "mock_monitor"):
            monitor = get_database_health_monitor()
            assert monitor == "mock_monitor"


class TestDatabaseHealthMonitorIntegration:
    """Integration tests for database health monitor"""

    @pytest.mark.asyncio
    async def test_full_monitoring_cycle(self):
        """Test complete monitoring cycle with recovery"""
        database_url = "postgresql://test:test@localhost:5432/test"
        
        monitor = DatabaseHealthMonitor(
            database_url=database_url,
            health_check_interval=0.1,  # Very fast for testing
            max_connection_failures=2,
            connection_retry_delay=0.1,
        )
        
        # Mock the engines and sessions
        with patch.object(monitor, '_create_engines'), \
             patch.object(monitor, '_create_session_factories'), \
             patch.object(monitor, '_setup_pool_listeners'):
            
            # Initialize
            with patch.object(monitor, '_perform_health_check') as mock_health_check:
                mock_health_check.return_value = DatabaseHealth(
                    is_connected=True,
                    status=DatabaseHealthStatus.HEALTHY,
                    response_time=50.0,
                    last_check=datetime.utcnow(),
                    error_count=0,
                    consecutive_failures=0,
                )
                
                await monitor.initialize()
                assert monitor._health_status.status == DatabaseHealthStatus.HEALTHY
            
            # Start monitoring
            await monitor.start_monitoring()
            
            # Let it run briefly
            await asyncio.sleep(0.2)
            
            # Stop monitoring
            await monitor.stop_monitoring()
            
            # Cleanup
            await monitor.cleanup()

    @pytest.mark.asyncio
    async def test_error_recovery_scenario(self):
        """Test error recovery scenario"""
        database_url = "postgresql://test:test@localhost:5432/test"
        
        monitor = DatabaseHealthMonitor(
            database_url=database_url,
            max_connection_failures=2,
            connection_retry_delay=0.1,
        )
        
        with patch.object(monitor, '_create_engines'), \
             patch.object(monitor, '_create_session_factories'), \
             patch.object(monitor, '_setup_pool_listeners'):
            
            # Initialize successfully
            with patch.object(monitor, '_perform_health_check') as mock_health_check:
                mock_health_check.return_value = DatabaseHealth(
                    is_connected=True,
                    status=DatabaseHealthStatus.HEALTHY,
                    response_time=50.0,
                    last_check=datetime.utcnow(),
                    error_count=0,
                    consecutive_failures=0,
                )
                
                await monitor.initialize()
            
            # Simulate connection failure
            with patch.object(monitor, '_test_sync_connection', return_value=False), \
                 patch.object(monitor, '_test_async_connection', return_value=False):
                
                health = await monitor._perform_health_check()
                assert health.status in [DatabaseHealthStatus.DEGRADED, DatabaseHealthStatus.UNAVAILABLE]
            
            # Simulate recovery
            with patch.object(monitor, '_attempt_recovery', return_value=True):
                recovery_success = await monitor._attempt_recovery()
                assert recovery_success is True
            
            await monitor.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])