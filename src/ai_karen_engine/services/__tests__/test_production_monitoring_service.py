"""
Tests for Production Monitoring Service

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from ai_karen_engine.services.production_monitoring_service import (
    ProductionMonitoringService,
    MetricType,
    AlertSeverity,
    ResponseFormattingMetrics,
    DatabaseConsistencyMetrics,
    AuthenticationAnomalyMetrics,
    PerformanceDegradationMetrics,
    get_production_monitoring_service,
)


class TestProductionMonitoringService:
    """Test ProductionMonitoringService class"""

    @pytest.fixture
    def monitoring_service(self):
        """Create monitoring service instance"""
        with patch('ai_karen_engine.services.production_monitoring_service.get_metrics_manager'), \
             patch('ai_karen_engine.services.production_monitoring_service.get_database_health_checker'):
            service = ProductionMonitoringService()
            return service

    def test_initialization(self, monitoring_service):
        """Test service initialization"""
        assert isinstance(monitoring_service.response_formatting_metrics, ResponseFormattingMetrics)
        assert isinstance(monitoring_service.database_consistency_metrics, DatabaseConsistencyMetrics)
        assert isinstance(monitoring_service.auth_anomaly_metrics, AuthenticationAnomalyMetrics)
        assert isinstance(monitoring_service.performance_metrics, PerformanceDegradationMetrics)
        assert not monitoring_service._monitoring_active
        assert len(monitoring_service.active_alerts) == 0

    def test_record_response_formatting_success(self, monitoring_service):
        """Test recording response formatting success"""
        monitoring_service.record_response_formatting_success(
            formatter_type="movie",
            content_type="entertainment",
            duration_ms=150.5
        )
        
        metrics = monitoring_service.response_formatting_metrics
        assert metrics.total_requests == 1
        assert metrics.successful_formats == 1
        assert metrics.failed_formats == 0
        assert metrics.formatter_usage["movie"] == 1
        assert metrics.avg_format_time_ms == 150.5

    def test_record_response_formatting_failure(self, monitoring_service):
        """Test recording response formatting failure"""
        monitoring_service.record_response_formatting_failure(
            formatter_type="recipe",
            error_type="TemplateError",
            error_message="Template not found"
        )
        
        metrics = monitoring_service.response_formatting_metrics
        assert metrics.total_requests == 1
        assert metrics.successful_formats == 0
        assert metrics.failed_formats == 1
        assert metrics.error_types["TemplateError"] == 1

    def test_record_response_formatting_fallback(self, monitoring_service):
        """Test recording response formatting fallback"""
        monitoring_service.record_response_formatting_fallback(
            original_formatter="weather",
            fallback_reason="formatter_error"
        )
        
        metrics = monitoring_service.response_formatting_metrics
        assert metrics.fallback_used == 1

    def test_record_authentication_failure(self, monitoring_service):
        """Test recording authentication failure"""
        monitoring_service.record_authentication_failure(
            failure_reason="invalid_token",
            source_ip="192.168.1.100",
            user_agent="test-agent"
        )
        
        metrics = monitoring_service.auth_anomaly_metrics
        assert metrics.failed_login_attempts == 1
        assert len(monitoring_service._auth_failures) == 1

    def test_brute_force_detection(self, monitoring_service):
        """Test brute force attack detection"""
        # Record multiple failures from same IP
        for i in range(6):
            monitoring_service.record_authentication_failure(
                failure_reason="invalid_password",
                source_ip="192.168.1.100"
            )
        
        metrics = monitoring_service.auth_anomaly_metrics
        assert metrics.brute_force_attempts >= 1
        assert "192.168.1.100" in metrics.blocked_ips

    def test_record_api_response_time(self, monitoring_service):
        """Test recording API response time"""
        monitoring_service.record_api_response_time(
            endpoint="/api/test",
            method="GET",
            response_time_ms=250.0,
            status_code=200
        )
        
        assert len(monitoring_service._response_times) == 1
        response_data = monitoring_service._response_times[0]
        assert response_data["endpoint"] == "/api/test"
        assert response_data["method"] == "GET"
        assert response_data["response_time_ms"] == 250.0
        assert response_data["status_code"] == 200

    def test_record_api_error(self, monitoring_service):
        """Test recording API error"""
        monitoring_service.record_api_response_time(
            endpoint="/api/test",
            method="POST",
            response_time_ms=100.0,
            status_code=500
        )
        
        assert len(monitoring_service._error_counts) == 1
        error_data = monitoring_service._error_counts[0]
        assert error_data["endpoint"] == "/api/test"
        assert error_data["status_code"] == 500

    @pytest.mark.asyncio
    async def test_update_database_consistency_metrics(self, monitoring_service):
        """Test updating database consistency metrics"""
        # Mock database health checker
        mock_health_result = Mock()
        mock_health_result.consistency_issues = 2
        mock_health_result.critical_issues = 1
        mock_health_result.warning_issues = 3
        mock_health_result.database_connections = []
        
        monitoring_service.db_health_checker.check_health = AsyncMock(return_value=mock_health_result)
        
        await monitoring_service.update_database_consistency_metrics()
        
        metrics = monitoring_service.database_consistency_metrics
        assert metrics.cross_db_issues == 2
        assert metrics.orphaned_records == 1
        assert metrics.missing_references == 3
        assert metrics.consistency_score < 100.0  # Should be reduced due to issues

    def test_get_production_metrics_summary(self, monitoring_service):
        """Test getting production metrics summary"""
        # Add some test data
        monitoring_service.record_response_formatting_success("movie", "entertainment", 100.0)
        monitoring_service.record_authentication_failure("invalid_token", "192.168.1.1")
        
        summary = monitoring_service.get_production_metrics_summary()
        
        assert "timestamp" in summary
        assert "monitoring_active" in summary
        assert "response_formatting" in summary
        assert "database_consistency" in summary
        assert "authentication_anomalies" in summary
        assert "performance" in summary
        assert "alerts" in summary
        
        # Check response formatting metrics
        rf_metrics = summary["response_formatting"]
        assert rf_metrics["total_requests"] == 1
        assert rf_metrics["success_rate"] == 100.0

    def test_get_active_alerts(self, monitoring_service):
        """Test getting active alerts"""
        # Create a test alert
        monitoring_service._create_alert(
            MetricType.RESPONSE_FORMATTING,
            AlertSeverity.WARNING,
            "Test alert",
            {"test": "data"}
        )
        
        active_alerts = monitoring_service.get_active_alerts()
        
        assert len(active_alerts) == 1
        alert = active_alerts[0]
        assert alert["metric_type"] == "response_formatting"
        assert alert["severity"] == "warning"
        assert alert["message"] == "Test alert"
        assert alert["details"]["test"] == "data"
        assert not alert["resolved"]

    @pytest.mark.asyncio
    async def test_resolve_alert(self, monitoring_service):
        """Test resolving an alert"""
        # Create a test alert
        monitoring_service._create_alert(
            MetricType.AUTHENTICATION_ANOMALY,
            AlertSeverity.CRITICAL,
            "Test critical alert",
            {"test": "data"}
        )
        
        # Resolve the alert
        resolved = await monitoring_service.resolve_alert("Test critical alert")
        
        assert resolved is True
        
        # Check that alert is resolved
        active_alerts = monitoring_service.get_active_alerts()
        assert len(active_alerts) == 0

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, monitoring_service):
        """Test starting and stopping monitoring"""
        assert not monitoring_service._monitoring_active
        
        # Start monitoring
        with patch.object(monitoring_service, '_monitor_response_formatting'), \
             patch.object(monitoring_service, '_monitor_database_consistency'), \
             patch.object(monitoring_service, '_monitor_authentication_anomalies'), \
             patch.object(monitoring_service, '_monitor_performance_degradation'), \
             patch.object(monitoring_service, '_process_alerts'):
            
            await monitoring_service.start_monitoring()
            assert monitoring_service._monitoring_active
            
            # Stop monitoring
            await monitoring_service.stop_monitoring()
            assert not monitoring_service._monitoring_active

    def test_alert_creation_deduplication(self, monitoring_service):
        """Test that duplicate alerts are not created"""
        # Create first alert
        monitoring_service._create_alert(
            MetricType.PERFORMANCE_DEGRADATION,
            AlertSeverity.WARNING,
            "Performance issue",
            {"metric": "response_time"}
        )
        
        # Create duplicate alert
        monitoring_service._create_alert(
            MetricType.PERFORMANCE_DEGRADATION,
            AlertSeverity.WARNING,
            "Performance issue",
            {"metric": "error_rate"}
        )
        
        # Should only have one alert
        active_alerts = monitoring_service.get_active_alerts()
        assert len(active_alerts) == 1
        
        # Details should be updated
        alert = active_alerts[0]
        assert "error_rate" in str(alert["details"])

    def test_response_formatting_failure_alert_threshold(self, monitoring_service):
        """Test that high failure rate triggers alert"""
        # Record failures to trigger alert
        for i in range(15):  # 15 failures
            monitoring_service.record_response_formatting_failure(
                formatter_type="test",
                error_type="TestError",
                error_message="Test error"
            )
        
        # Record some successes to get total > 0
        for i in range(5):  # 5 successes
            monitoring_service.record_response_formatting_success(
                formatter_type="test",
                content_type="test",
                duration_ms=100.0
            )
        
        # Should have created an alert due to high failure rate (75%)
        active_alerts = monitoring_service.get_active_alerts()
        assert len(active_alerts) > 0
        
        # Find the formatting alert
        formatting_alerts = [
            alert for alert in active_alerts
            if alert["metric_type"] == "response_formatting"
        ]
        assert len(formatting_alerts) > 0


class TestGlobalInstance:
    """Test global instance management"""

    def test_get_production_monitoring_service(self):
        """Test getting global service instance"""
        service1 = get_production_monitoring_service()
        service2 = get_production_monitoring_service()
        
        # Should return same instance
        assert service1 is service2
        assert isinstance(service1, ProductionMonitoringService)