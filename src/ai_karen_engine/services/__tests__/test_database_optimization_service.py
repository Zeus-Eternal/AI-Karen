"""
Unit tests for Database Optimization Service
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch

from ..database_optimization_service import (
    DatabaseOptimizationService,
    RetryStrategy,
    RetryConfig,
    ConnectionPoolMetrics,
    DatabasePerformanceAlert
)
from ...core.services.base import ServiceConfig


class TestDatabaseOptimizationService:
    """Test cases for DatabaseOptimizationService."""
    
    @pytest.fixture
    def service(self):
        """Create a test service instance."""
        config = ServiceConfig(
            name="test_db_optimization",
            enabled=True,
            config={
                "monitoring_interval_seconds": 1,  # Fast for testing
                "metrics_retention_hours": 1,
                "alerting_enabled": True,
                "pool_optimization_enabled": False,  # Disable for testing
                "alert_thresholds": {
                    "high_connection_usage": 0.8,
                    "response_time_ms": 1000,
                    "connection_error_rate": 0.1
                }
            }
        )
        return DatabaseOptimizationService(config)
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager."""
        mock = Mock()
        mock.initialize = AsyncMock()
        mock.async_health_check = AsyncMock(return_value=True)
        mock._get_pool_metrics = Mock(return_value={
            "sync_pool": {
                "size": 10,
                "checked_out": 5,
                "checked_in": 3,
                "overflow": 2,
                "invalidated": 0
            }
        })
        return mock
    
    @pytest.fixture
    def mock_redis_manager(self):
        """Mock Redis manager."""
        mock = Mock()
        mock.initialize = AsyncMock()
        mock.health_check = AsyncMock(return_value={
            "healthy": True,
            "response_time_ms": 10,
            "connection_info": {
                "max_connections": 20,
                "active_connections": 5,
                "idle_connections": 15
            }
        })
        return mock
    
    @pytest.fixture
    def mock_health_checker(self):
        """Mock health checker."""
        mock = Mock()
        mock.initialize = AsyncMock()
        return mock
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, service, mock_db_manager, mock_redis_manager, mock_health_checker):
        """Test service initialization."""
        with patch.object(service, 'db_manager', mock_db_manager), \
             patch.object(service, 'redis_manager', mock_redis_manager), \
             patch.object(service, 'health_checker', mock_health_checker):
            
            await service.initialize()
            
            mock_db_manager.initialize.assert_called_once()
            mock_redis_manager.initialize.assert_called_once()
            mock_health_checker.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check(self, service, mock_db_manager):
        """Test health check functionality."""
        with patch.object(service, 'db_manager', mock_db_manager):
            health_status = await service.health_check()
            assert health_status is True
            
            # Test with failed database health check
            mock_db_manager.async_health_check.return_value = False
            health_status = await service.health_check()
            assert health_status is False
    
    @pytest.mark.asyncio
    async def test_collect_database_metrics(self, service, mock_db_manager):
        """Test database metrics collection."""
        with patch.object(service, 'db_manager', mock_db_manager):
            metrics = await service._collect_database_metrics()
            
            assert metrics is not None
            assert metrics.database_name == "postgresql"
            assert metrics.pool_size == 10
            assert metrics.active_connections == 5
            assert metrics.idle_connections == 3
            assert metrics.overflow_connections == 2
    
    @pytest.mark.asyncio
    async def test_collect_redis_metrics(self, service, mock_redis_manager):
        """Test Redis metrics collection."""
        with patch.object(service, 'redis_manager', mock_redis_manager):
            metrics = await service._collect_redis_metrics()
            
            assert metrics is not None
            assert metrics.database_name == "redis"
            assert metrics.pool_size == 20
            assert metrics.active_connections == 5
            assert metrics.idle_connections == 15
            assert metrics.avg_connection_time_ms == 10
    
    @pytest.mark.asyncio
    async def test_collect_milvus_metrics(self, service):
        """Test Milvus metrics collection."""
        metrics = await service._collect_milvus_metrics()
        
        assert metrics is not None
        assert metrics.database_name == "milvus"
        assert metrics.pool_size == 1
        assert metrics.active_connections == 1
    
    @pytest.mark.asyncio
    async def test_connection_usage_alert(self, service):
        """Test high connection usage alert."""
        # Create metrics with high connection usage
        high_usage_metric = ConnectionPoolMetrics(
            timestamp=datetime.now(timezone.utc),
            database_name="postgresql",
            pool_size=10,
            active_connections=9,  # 90% usage
            idle_connections=1,
            overflow_connections=0,
            failed_connections=0,
            avg_connection_time_ms=100,
            max_connection_time_ms=200,
            total_queries=100,
            slow_queries=5
        )
        
        await service._check_connection_usage_alerts([high_usage_metric])
        
        # Should create an alert
        assert len(service.active_alerts) == 1
        alert = service.active_alerts[0]
        assert alert.alert_type == "high_connection_usage"
        assert alert.severity == "warning"
        assert alert.database_name == "postgresql"
    
    @pytest.mark.asyncio
    async def test_response_time_alert(self, service):
        """Test high response time alert."""
        # Create metrics with high response time
        slow_metric = ConnectionPoolMetrics(
            timestamp=datetime.now(timezone.utc),
            database_name="postgresql",
            pool_size=10,
            active_connections=5,
            idle_connections=5,
            overflow_connections=0,
            failed_connections=0,
            avg_connection_time_ms=1500,  # Above threshold
            max_connection_time_ms=2000,
            total_queries=100,
            slow_queries=10
        )
        
        await service._check_response_time_alerts([slow_metric])
        
        # Should create an alert
        assert len(service.active_alerts) == 1
        alert = service.active_alerts[0]
        assert alert.alert_type == "high_response_time"
        assert alert.severity == "warning"
        assert alert.database_name == "postgresql"
    
    @pytest.mark.asyncio
    async def test_error_rate_alert(self, service):
        """Test high error rate alert."""
        # Create metrics with high error rate
        error_metrics = [
            ConnectionPoolMetrics(
                timestamp=datetime.now(timezone.utc),
                database_name="postgresql",
                pool_size=10,
                active_connections=5,
                idle_connections=5,
                overflow_connections=0,
                failed_connections=1,  # Failed connection
                avg_connection_time_ms=100,
                max_connection_time_ms=200,
                total_queries=10,
                slow_queries=0
            ),
            ConnectionPoolMetrics(
                timestamp=datetime.now(timezone.utc),
                database_name="postgresql",
                pool_size=10,
                active_connections=5,
                idle_connections=5,
                overflow_connections=0,
                failed_connections=1,  # Another failed connection
                avg_connection_time_ms=100,
                max_connection_time_ms=200,
                total_queries=10,
                slow_queries=0
            )
        ]
        
        await service._check_error_rate_alerts(error_metrics)
        
        # Should create an alert (100% error rate)
        assert len(service.active_alerts) == 1
        alert = service.active_alerts[0]
        assert alert.alert_type == "high_error_rate"
        assert alert.severity == "critical"
        assert alert.database_name == "postgresql"
    
    def test_retry_delay_calculation(self, service):
        """Test retry delay calculation for different strategies."""
        # Test fixed interval
        config = RetryConfig(strategy=RetryStrategy.FIXED_INTERVAL, base_delay=2.0)
        delay = service._calculate_retry_delay(config, 0)
        assert delay == 2.0
        delay = service._calculate_retry_delay(config, 5)
        assert delay == 2.0
        
        # Test linear backoff
        config = RetryConfig(strategy=RetryStrategy.LINEAR_BACKOFF, base_delay=1.0)
        delay = service._calculate_retry_delay(config, 0)
        assert delay == 1.0
        delay = service._calculate_retry_delay(config, 2)
        assert delay == 3.0
        
        # Test exponential backoff
        config = RetryConfig(strategy=RetryStrategy.EXPONENTIAL_BACKOFF, base_delay=1.0, backoff_multiplier=2.0)
        delay = service._calculate_retry_delay(config, 0)
        assert delay == 1.0
        delay = service._calculate_retry_delay(config, 2)
        assert delay == 4.0
        
        # Test max delay cap
        config = RetryConfig(strategy=RetryStrategy.EXPONENTIAL_BACKOFF, base_delay=1.0, max_delay=5.0, backoff_multiplier=2.0)
        delay = service._calculate_retry_delay(config, 10)
        assert delay == 5.0
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self, service):
        """Test successful operation with retry."""
        async def test_operation():
            return "success"
        
        result = await service.execute_with_retry("test_op", test_operation)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_failure_then_success(self, service):
        """Test operation that fails then succeeds."""
        call_count = 0
        
        async def test_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First attempt fails")
            return "success"
        
        result = await service.execute_with_retry("test_op", test_operation)
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_all_failures(self, service):
        """Test operation that always fails."""
        async def test_operation():
            raise Exception("Always fails")
        
        with pytest.raises(Exception, match="Always fails"):
            await service.execute_with_retry("test_op", test_operation)
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_sync_function(self, service):
        """Test retry with synchronous function."""
        def sync_operation():
            return "sync_success"
        
        result = await service.execute_with_retry("sync_op", sync_operation)
        assert result == "sync_success"
    
    @pytest.mark.asyncio
    async def test_pool_optimization(self, service):
        """Test connection pool optimization."""
        # Create metrics showing high usage
        high_usage_metrics = [
            ConnectionPoolMetrics(
                timestamp=datetime.now(timezone.utc),
                database_name="postgresql",
                pool_size=10,
                active_connections=9,
                idle_connections=1,
                overflow_connections=0,
                failed_connections=0,
                avg_connection_time_ms=100,
                max_connection_time_ms=200,
                total_queries=100,
                slow_queries=0
            )
        ]
        
        # This should recommend increasing pool size
        await service._optimize_database_pool("postgresql", high_usage_metrics)
        
        # Create metrics showing low usage
        low_usage_metrics = [
            ConnectionPoolMetrics(
                timestamp=datetime.now(timezone.utc),
                database_name="postgresql",
                pool_size=20,
                active_connections=2,
                idle_connections=18,
                overflow_connections=0,
                failed_connections=0,
                avg_connection_time_ms=100,
                max_connection_time_ms=200,
                total_queries=100,
                slow_queries=0
            )
        ]
        
        # This should recommend decreasing pool size
        await service._optimize_database_pool("postgresql", low_usage_metrics)
    
    @pytest.mark.asyncio
    async def test_metrics_cleanup(self, service):
        """Test old metrics cleanup."""
        # Add old metrics
        old_metric = ConnectionPoolMetrics(
            timestamp=datetime.now(timezone.utc) - timedelta(hours=25),  # Older than retention
            database_name="postgresql",
            pool_size=10,
            active_connections=5,
            idle_connections=5,
            overflow_connections=0,
            failed_connections=0,
            avg_connection_time_ms=100,
            max_connection_time_ms=200,
            total_queries=100,
            slow_queries=0
        )
        
        recent_metric = ConnectionPoolMetrics(
            timestamp=datetime.now(timezone.utc),
            database_name="postgresql",
            pool_size=10,
            active_connections=5,
            idle_connections=5,
            overflow_connections=0,
            failed_connections=0,
            avg_connection_time_ms=100,
            max_connection_time_ms=200,
            total_queries=100,
            slow_queries=0
        )
        
        service.metrics_history = [old_metric, recent_metric]
        
        await service._cleanup_old_metrics()
        
        # Only recent metric should remain
        assert len(service.metrics_history) == 1
        assert service.metrics_history[0] == recent_metric
    
    @pytest.mark.asyncio
    async def test_alert_resolution(self, service):
        """Test alert resolution."""
        # Create an alert
        alert = DatabasePerformanceAlert(
            alert_id="test_alert_123",
            timestamp=datetime.now(timezone.utc),
            database_name="postgresql",
            alert_type="high_connection_usage",
            severity="warning",
            message="Test alert",
            metrics={}
        )
        
        service.active_alerts.append(alert)
        
        # Resolve the alert
        resolved = await service.resolve_alert("test_alert_123")
        assert resolved is True
        assert alert.resolved is True
        assert alert.resolved_at is not None
        
        # Try to resolve non-existent alert
        resolved = await service.resolve_alert("non_existent")
        assert resolved is False
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, service):
        """Test performance metrics retrieval."""
        # Add some test metrics
        metric = ConnectionPoolMetrics(
            timestamp=datetime.now(timezone.utc),
            database_name="postgresql",
            pool_size=10,
            active_connections=5,
            idle_connections=5,
            overflow_connections=0,
            failed_connections=0,
            avg_connection_time_ms=100,
            max_connection_time_ms=200,
            total_queries=100,
            slow_queries=0
        )
        
        service.metrics_history.append(metric)
        
        metrics = await service.get_performance_metrics()
        
        assert "timestamp" in metrics
        assert "databases" in metrics
        assert "postgresql" in metrics["databases"]
        assert metrics["databases"]["postgresql"]["avg_active_connections"] == 5
        assert metrics["databases"]["postgresql"]["avg_pool_size"] == 10
        assert metrics["databases"]["postgresql"]["connection_usage_ratio"] == 0.5
    
    @pytest.mark.asyncio
    async def test_get_active_alerts(self, service):
        """Test active alerts retrieval."""
        # Create test alerts
        active_alert = DatabasePerformanceAlert(
            alert_id="active_alert",
            timestamp=datetime.now(timezone.utc),
            database_name="postgresql",
            alert_type="high_connection_usage",
            severity="warning",
            message="Active alert",
            metrics={}
        )
        
        resolved_alert = DatabasePerformanceAlert(
            alert_id="resolved_alert",
            timestamp=datetime.now(timezone.utc),
            database_name="postgresql",
            alert_type="high_response_time",
            severity="warning",
            message="Resolved alert",
            metrics={},
            resolved=True,
            resolved_at=datetime.now(timezone.utc)
        )
        
        service.active_alerts = [active_alert, resolved_alert]
        
        alerts = await service.get_active_alerts()
        
        # Should only return active alerts
        assert len(alerts) == 1
        assert alerts[0]["alert_id"] == "active_alert"
        assert alerts[0]["resolved"] is False


if __name__ == "__main__":
    pytest.main([__file__])