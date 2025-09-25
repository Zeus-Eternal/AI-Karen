"""
Tests for Service Health Monitor

Tests health monitoring, automatic recovery attempts, and integration
with the error recovery manager.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import aiohttp
import json
from pathlib import Path

from src.ai_karen_engine.core.service_health_monitor import (
    ServiceHealthMonitor, HealthCheckType, HealthCheckConfig, HealthMetrics,
    get_service_health_monitor
)
from src.ai_karen_engine.core.error_recovery_manager import ErrorRecoveryManager, ServiceStatus


class TestServiceHealthMonitor:
    """Test cases for ServiceHealthMonitor"""
    
    @pytest.fixture
    def error_recovery_manager(self):
        """Create mock error recovery manager"""
        manager = Mock(spec=ErrorRecoveryManager)
        manager.register_service = Mock()
        manager.handle_service_failure = AsyncMock()
        manager.record_service_success = AsyncMock()
        manager._send_alert = AsyncMock()
        return manager
    
    @pytest.fixture
    def health_monitor(self, error_recovery_manager):
        """Create health monitor instance"""
        return ServiceHealthMonitor(error_recovery_manager)
    
    @pytest.fixture
    def mock_service_registry(self):
        """Mock service registry"""
        with patch('src.ai_karen_engine.core.service_health_monitor.ServiceRegistry') as mock:
            registry_instance = Mock()
            mock.return_value = registry_instance
            yield registry_instance
    
    def test_health_check_registration(self, health_monitor):
        """Test registration of health checks"""
        config = HealthCheckConfig(
            check_type=HealthCheckType.HTTP,
            interval=30,
            timeout=5,
            endpoint="http://localhost:8080/health"
        )
        
        health_monitor.register_service_health_check("web_service", config)
        
        assert "web_service" in health_monitor.health_checks
        assert health_monitor.health_checks["web_service"] == config
        assert "web_service" in health_monitor.service_metrics
        assert "web_service" in health_monitor.service_start_times
    
    def test_http_health_check_registration(self, health_monitor):
        """Test HTTP health check registration helper"""
        health_monitor.register_http_health_check(
            "api_service", 
            "http://localhost:3000/api/health",
            interval=60,
            timeout=10
        )
        
        config = health_monitor.health_checks["api_service"]
        assert config.check_type == HealthCheckType.HTTP
        assert config.endpoint == "http://localhost:3000/api/health"
        assert config.interval == 60
        assert config.timeout == 10
    
    def test_resource_health_check_registration(self, health_monitor):
        """Test resource-based health check registration"""
        health_monitor.register_resource_health_check(
            "cpu_intensive_service",
            HealthCheckType.CPU,
            threshold=80.0,
            interval=15
        )
        
        config = health_monitor.health_checks["cpu_intensive_service"]
        assert config.check_type == HealthCheckType.CPU
        assert config.threshold == 80.0
        assert config.interval == 15
    
    def test_custom_health_check_registration(self, health_monitor):
        """Test custom health check registration"""
        async def custom_check():
            return True
        
        health_monitor.register_custom_health_check(
            "custom_service",
            custom_check,
            interval=45
        )
        
        config = health_monitor.health_checks["custom_service"]
        assert config.check_type == HealthCheckType.CUSTOM
        assert config.custom_check == custom_check
        assert config.interval == 45
    
    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self, health_monitor):
        """Test monitoring start and stop"""
        # Register a service first
        health_monitor.register_http_health_check("test_service", "http://localhost/health")
        
        assert not health_monitor.monitoring_active
        
        # Start monitoring
        await health_monitor.start_monitoring()
        assert health_monitor.monitoring_active
        assert health_monitor.global_monitoring_task is not None
        assert "test_service" in health_monitor.monitoring_tasks
        
        # Stop monitoring
        await health_monitor.stop_monitoring()
        assert not health_monitor.monitoring_active
        assert len(health_monitor.monitoring_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_http_health_check(self, health_monitor):
        """Test HTTP health check execution"""
        with patch('aiohttp.ClientSession') as mock_session:
            # Mock successful HTTP response
            mock_response = Mock()
            mock_response.status = 200
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_session_instance = Mock()
            mock_session_instance.get.return_value = mock_response
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_session_instance
            
            # Perform HTTP health check
            response_time = await health_monitor._http_health_check("http://localhost/health", 5)
            
            assert response_time >= 0
            mock_session_instance.get.assert_called_once_with("http://localhost/health")
    
    @pytest.mark.asyncio
    async def test_http_health_check_failure(self, health_monitor):
        """Test HTTP health check failure handling"""
        with patch('aiohttp.ClientSession') as mock_session:
            # Mock HTTP error response
            mock_response = Mock()
            mock_response.status = 500
            mock_response.reason = "Internal Server Error"
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_session_instance = Mock()
            mock_session_instance.get.return_value = mock_response
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_session_instance
            
            # Should raise exception for HTTP error
            with pytest.raises(Exception) as exc_info:
                await health_monitor._http_health_check("http://localhost/health", 5)
            
            assert "HTTP 500" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_ping_health_check(self, health_monitor, mock_service_registry):
        """Test ping-style health check"""
        # Mock service with ping method
        mock_service = Mock()
        mock_service.ping = AsyncMock()
        mock_service_registry.get_service.return_value = mock_service
        
        response_time = await health_monitor._ping_health_check("test_service")
        
        assert response_time >= 0
        mock_service.ping.assert_called_once()
        mock_service_registry.get_service.assert_called_once_with("test_service")
    
    @pytest.mark.asyncio
    async def test_ping_health_check_with_health_check_method(self, health_monitor, mock_service_registry):
        """Test ping health check with health_check method"""
        # Mock service with health_check method but no ping
        mock_service = Mock()
        mock_service.health_check = AsyncMock()
        mock_service_registry.get_service.return_value = mock_service
        
        # Remove ping method
        del mock_service.ping
        
        response_time = await health_monitor._ping_health_check("test_service")
        
        assert response_time >= 0
        mock_service.health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_custom_health_check(self, health_monitor):
        """Test custom health check execution"""
        # Test async custom check
        async def async_check():
            await asyncio.sleep(0.01)  # Simulate some work
            return True
        
        response_time = await health_monitor._custom_health_check(async_check)
        assert response_time >= 0.01
        
        # Test sync custom check
        def sync_check():
            return True
        
        response_time = await health_monitor._custom_health_check(sync_check)
        assert response_time >= 0
    
    @pytest.mark.asyncio
    async def test_custom_health_check_failure(self, health_monitor):
        """Test custom health check failure"""
        def failing_check():
            return False
        
        with pytest.raises(Exception) as exc_info:
            await health_monitor._custom_health_check(failing_check)
        
        assert "Custom health check returned False" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_resource_metrics_collection(self, health_monitor):
        """Test resource metrics collection"""
        with patch('psutil.Process') as mock_process:
            mock_process_instance = Mock()
            mock_process_instance.cpu_percent.return_value = 25.5
            mock_process_instance.memory_info.return_value = Mock(rss=1024 * 1024 * 512)  # 512MB
            mock_process.return_value = mock_process_instance
            
            cpu_usage, memory_usage = await health_monitor._get_resource_metrics("test_service")
            
            assert cpu_usage == 25.5
            assert memory_usage == 512  # MB
    
    @pytest.mark.asyncio
    async def test_error_rate_calculation(self, health_monitor):
        """Test error rate calculation"""
        service_name = "test_service"
        health_monitor.service_metrics[service_name] = []
        
        # Add some metrics with mixed success/failure
        now = datetime.now()
        for i in range(10):
            status = ServiceStatus.FAILED if i < 3 else ServiceStatus.HEALTHY
            metrics = HealthMetrics(
                service_name=service_name,
                timestamp=now - timedelta(minutes=i),
                status=status,
                response_time=0.1,
                cpu_usage=10.0,
                memory_usage=100,
                error_rate=0.0,
                uptime=timedelta(hours=1),
                custom_metrics={}
            )
            health_monitor.service_metrics[service_name].append(metrics)
        
        error_rate = await health_monitor._calculate_error_rate(service_name)
        assert error_rate == 0.3  # 3 failures out of 10
    
    @pytest.mark.asyncio
    async def test_health_check_performance(self, health_monitor, error_recovery_manager):
        """Test complete health check performance"""
        config = HealthCheckConfig(
            check_type=HealthCheckType.CUSTOM,
            custom_check=lambda: True
        )
        
        with patch.object(health_monitor, '_get_resource_metrics', return_value=(15.0, 256)):
            with patch.object(health_monitor, '_calculate_error_rate', return_value=0.05):
                metrics = await health_monitor._perform_health_check("test_service", config)
                
                assert metrics.service_name == "test_service"
                assert metrics.status == ServiceStatus.HEALTHY
                assert metrics.response_time >= 0
                assert metrics.cpu_usage == 15.0
                assert metrics.memory_usage == 256
                assert metrics.error_rate == 0.05
                
                # Should record success with error recovery manager
                error_recovery_manager.record_service_success.assert_called_once_with("test_service")
    
    @pytest.mark.asyncio
    async def test_health_check_failure_reporting(self, health_monitor, error_recovery_manager):
        """Test health check failure reporting to error recovery manager"""
        config = HealthCheckConfig(
            check_type=HealthCheckType.CUSTOM,
            custom_check=lambda: False  # Always fails
        )
        
        with patch.object(health_monitor, '_get_resource_metrics', return_value=(15.0, 256)):
            with patch.object(health_monitor, '_calculate_error_rate', return_value=0.05):
                metrics = await health_monitor._perform_health_check("test_service", config)
                
                assert metrics.status == ServiceStatus.FAILED
                
                # Should report failure to error recovery manager
                error_recovery_manager.handle_service_failure.assert_called_once()
                call_args = error_recovery_manager.handle_service_failure.call_args
                assert call_args[0][0] == "test_service"
                assert isinstance(call_args[0][1], Exception)
    
    @pytest.mark.asyncio
    async def test_health_alerts(self, health_monitor, error_recovery_manager):
        """Test health alert generation"""
        # Set low thresholds for testing
        health_monitor.alert_thresholds = {
            "error_rate": 0.05,
            "response_time": 1.0,
            "cpu_usage": 20.0,
            "memory_usage": 200
        }
        
        # Create metrics that exceed thresholds
        metrics = HealthMetrics(
            service_name="test_service",
            timestamp=datetime.now(),
            status=ServiceStatus.HEALTHY,
            response_time=2.0,      # Exceeds 1.0 threshold
            cpu_usage=30.0,         # Exceeds 20.0 threshold
            memory_usage=300,       # Exceeds 200 threshold
            error_rate=0.1,         # Exceeds 0.05 threshold
            uptime=timedelta(hours=1),
            custom_metrics={}
        )
        
        await health_monitor._check_health_alerts("test_service", metrics)
        
        # Should send alert for threshold violations
        error_recovery_manager._send_alert.assert_called_once()
        call_args = error_recovery_manager._send_alert.call_args
        alert_message = call_args[0][0]
        assert "test_service health alerts" in alert_message
        assert "High error rate" in alert_message
        assert "High response time" in alert_message
        assert "High CPU usage" in alert_message
        assert "High memory usage" in alert_message
    
    @pytest.mark.asyncio
    async def test_service_health_retrieval(self, health_monitor):
        """Test service health data retrieval"""
        service_name = "test_service"
        
        # Add some metrics
        metrics = HealthMetrics(
            service_name=service_name,
            timestamp=datetime.now(),
            status=ServiceStatus.HEALTHY,
            response_time=0.5,
            cpu_usage=15.0,
            memory_usage=128,
            error_rate=0.02,
            uptime=timedelta(hours=2),
            custom_metrics={}
        )
        health_monitor.service_metrics[service_name] = [metrics]
        
        # Test single service health retrieval
        latest_health = await health_monitor.get_service_health(service_name)
        assert latest_health == metrics
        
        # Test all services health retrieval
        all_health = await health_monitor.get_all_service_health()
        assert service_name in all_health
        assert all_health[service_name] == metrics
    
    @pytest.mark.asyncio
    async def test_service_history_retrieval(self, health_monitor):
        """Test service health history retrieval"""
        service_name = "test_service"
        health_monitor.service_metrics[service_name] = []
        
        # Add metrics over time
        now = datetime.now()
        for i in range(48):  # 48 hours of data
            metrics = HealthMetrics(
                service_name=service_name,
                timestamp=now - timedelta(hours=i),
                status=ServiceStatus.HEALTHY,
                response_time=0.1 * (i + 1),
                cpu_usage=10.0,
                memory_usage=100,
                error_rate=0.0,
                uptime=timedelta(hours=i + 1),
                custom_metrics={}
            )
            health_monitor.service_metrics[service_name].append(metrics)
        
        # Get last 24 hours
        history = await health_monitor.get_service_history(service_name, hours=24)
        
        # Should return only metrics from last 24 hours
        assert len(history) == 24
        for metric in history:
            assert metric.timestamp >= now - timedelta(hours=24)
    
    @pytest.mark.asyncio
    async def test_system_health_monitoring(self, health_monitor, error_recovery_manager):
        """Test system-wide health monitoring"""
        # Add multiple services with different health states
        services = {
            "healthy_service": ServiceStatus.HEALTHY,
            "failed_service1": ServiceStatus.FAILED,
            "failed_service2": ServiceStatus.FAILED,
            "degraded_service": ServiceStatus.DEGRADED
        }
        
        for service_name, status in services.items():
            metrics = HealthMetrics(
                service_name=service_name,
                timestamp=datetime.now(),
                status=status,
                response_time=0.1,
                cpu_usage=10.0,
                memory_usage=100,
                error_rate=0.0,
                uptime=timedelta(hours=1),
                custom_metrics={}
            )
            health_monitor.service_metrics[service_name] = [metrics]
        
        # Check system health
        await health_monitor._check_system_health()
        
        # Should send system-wide alert for high failure rate (50% failed/degraded)
        error_recovery_manager._send_alert.assert_called()
        call_args = error_recovery_manager._send_alert.call_args
        alert_message = call_args[0][0]
        assert "System degradation" in alert_message
    
    @pytest.mark.asyncio
    async def test_health_report_generation(self, health_monitor, tmp_path):
        """Test health report generation"""
        # Set custom report path for testing
        health_monitor.health_report_path = tmp_path / "test_health_report.json"
        
        # Add some service metrics
        service_name = "test_service"
        metrics = HealthMetrics(
            service_name=service_name,
            timestamp=datetime.now(),
            status=ServiceStatus.HEALTHY,
            response_time=0.3,
            cpu_usage=25.0,
            memory_usage=256,
            error_rate=0.05,
            uptime=timedelta(hours=3),
            custom_metrics={}
        )
        health_monitor.service_metrics[service_name] = [metrics]
        
        # Generate report
        await health_monitor._generate_health_report()
        
        # Verify report file was created
        assert health_monitor.health_report_path.exists()
        
        # Verify report content
        with open(health_monitor.health_report_path, 'r') as f:
            report = json.load(f)
        
        assert "timestamp" in report
        assert "monitoring_active" in report
        assert "services" in report
        assert service_name in report["services"]
        
        service_data = report["services"][service_name]
        assert service_data["status"] == ServiceStatus.HEALTHY.value
        assert service_data["avg_response_time"] == 0.3
        assert service_data["avg_cpu_usage"] == 25.0
        assert service_data["avg_memory_usage"] == 256
    
    def test_global_instance(self):
        """Test global instance access"""
        monitor1 = get_service_health_monitor()
        monitor2 = get_service_health_monitor()
        
        # Should return same instance
        assert monitor1 is monitor2


class TestHealthCheckConfig:
    """Test health check configuration"""
    
    def test_default_config(self):
        """Test default health check configuration"""
        config = HealthCheckConfig(HealthCheckType.HTTP)
        
        assert config.check_type == HealthCheckType.HTTP
        assert config.interval == 30
        assert config.timeout == 5
        assert config.retries == 3
        assert config.threshold is None
        assert config.endpoint is None
        assert config.custom_check is None
    
    def test_custom_config(self):
        """Test custom health check configuration"""
        def custom_check():
            return True
        
        config = HealthCheckConfig(
            check_type=HealthCheckType.CUSTOM,
            interval=60,
            timeout=10,
            retries=5,
            threshold=75.0,
            endpoint="http://example.com/health",
            custom_check=custom_check
        )
        
        assert config.check_type == HealthCheckType.CUSTOM
        assert config.interval == 60
        assert config.timeout == 10
        assert config.retries == 5
        assert config.threshold == 75.0
        assert config.endpoint == "http://example.com/health"
        assert config.custom_check == custom_check


class TestHealthMetrics:
    """Test health metrics data structure"""
    
    def test_health_metrics_creation(self):
        """Test health metrics object creation"""
        now = datetime.now()
        uptime = timedelta(hours=2)
        
        metrics = HealthMetrics(
            service_name="test_service",
            timestamp=now,
            status=ServiceStatus.HEALTHY,
            response_time=0.25,
            cpu_usage=15.5,
            memory_usage=512,
            error_rate=0.02,
            uptime=uptime,
            custom_metrics={"connections": 42}
        )
        
        assert metrics.service_name == "test_service"
        assert metrics.timestamp == now
        assert metrics.status == ServiceStatus.HEALTHY
        assert metrics.response_time == 0.25
        assert metrics.cpu_usage == 15.5
        assert metrics.memory_usage == 512
        assert metrics.error_rate == 0.02
        assert metrics.uptime == uptime
        assert metrics.custom_metrics["connections"] == 42


@pytest.mark.asyncio
async def test_integration_with_error_recovery_manager():
    """Test integration between health monitor and error recovery manager"""
    error_manager = Mock(spec=ErrorRecoveryManager)
    error_manager.register_service = Mock()
    error_manager.handle_service_failure = AsyncMock()
    error_manager.record_service_success = AsyncMock()
    
    health_monitor = ServiceHealthMonitor(error_manager)
    
    # Register service should call error manager
    health_monitor.register_service_health_check(
        "integration_service",
        HealthCheckConfig(HealthCheckType.PING)
    )
    
    error_manager.register_service.assert_called_once_with("integration_service")


@pytest.mark.asyncio
async def test_concurrent_health_checks():
    """Test concurrent health check execution"""
    health_monitor = ServiceHealthMonitor()
    
    # Register multiple services
    services = ["service1", "service2", "service3"]
    for service in services:
        health_monitor.register_custom_health_check(
            service,
            lambda: True,  # Always healthy
            interval=1  # Short interval for testing
        )
    
    # Start monitoring
    await health_monitor.start_monitoring()
    
    # Let it run for a short time
    await asyncio.sleep(2)
    
    # Stop monitoring
    await health_monitor.stop_monitoring()
    
    # All services should have metrics
    for service in services:
        assert service in health_monitor.service_metrics
        assert len(health_monitor.service_metrics[service]) > 0