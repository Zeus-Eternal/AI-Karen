"""
Integration tests for validation metrics system

This module tests the complete validation metrics pipeline including
metrics collection, Prometheus integration, and API endpoints.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import Request

from ai_karen_engine.monitoring.validation_metrics import (
    ValidationMetricsCollector,
    ValidationEventType,
    ThreatLevel,
    ValidationMetricsData,
    get_validation_metrics_collector,
    record_validation_event
)
from ai_karen_engine.server.http_validator import HTTPRequestValidator, ValidationConfig
from ai_karen_engine.api_routes.validation_metrics_routes import router


class TestValidationMetricsCollector:
    """Test the ValidationMetricsCollector class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.collector = ValidationMetricsCollector()
    
    def test_collector_initialization(self):
        """Test that collector initializes properly"""
        assert self.collector is not None
        assert self.collector.metrics_manager is not None
        assert hasattr(self.collector, 'validation_requests_total')
        assert hasattr(self.collector, 'security_threats_total')
        assert hasattr(self.collector, 'rate_limit_events_total')
    
    def test_record_validation_event_success(self):
        """Test recording a successful validation event"""
        metrics_data = ValidationMetricsData(
            event_type=ValidationEventType.REQUEST_VALIDATED,
            threat_level=ThreatLevel.NONE,
            validation_rule="standard_validation",
            client_ip_hash="test_hash",
            endpoint="/api/test",
            http_method="GET",
            user_agent_category="browser",
            processing_time_ms=25.5
        )
        
        # Should not raise an exception
        self.collector.record_validation_event(metrics_data)
    
    def test_record_security_threat_event(self):
        """Test recording a security threat event"""
        metrics_data = ValidationMetricsData(
            event_type=ValidationEventType.SECURITY_THREAT_DETECTED,
            threat_level=ThreatLevel.HIGH,
            validation_rule="security_validation",
            client_ip_hash="malicious_hash",
            endpoint="/api/sensitive",
            http_method="POST",
            user_agent_category="security_tool",
            processing_time_ms=45.2,
            attack_categories=["sql_injection", "xss"],
            additional_labels={
                "confidence_score": "0.95",
                "client_reputation": "malicious"
            }
        )
        
        # Should not raise an exception
        self.collector.record_validation_event(metrics_data)
    
    def test_record_rate_limit_event(self):
        """Test recording a rate limit event"""
        metrics_data = ValidationMetricsData(
            event_type=ValidationEventType.RATE_LIMIT_EXCEEDED,
            threat_level=ThreatLevel.LOW,
            validation_rule="rate_limit_validation",
            client_ip_hash="frequent_client",
            endpoint="/api/frequent",
            http_method="POST",
            rate_limit_rule="api_rate_limit",
            additional_labels={
                "rate_limit_scope": "ip",
                "rate_limit_algorithm": "sliding_window",
                "current_usage_percent": "95.0"
            }
        )
        
        # Should not raise an exception
        self.collector.record_validation_event(metrics_data)
    
    def test_record_client_behavior(self):
        """Test recording client behavior metrics"""
        # Should not raise an exception
        self.collector.record_client_behavior(
            client_ip_hash="test_client",
            reputation_score=0.7,
            reputation_category="suspicious",
            endpoint="/api/test",
            activity_type="high_frequency"
        )
    
    def test_record_request_characteristics(self):
        """Test recording request characteristics"""
        # Should not raise an exception
        self.collector.record_request_characteristics(
            endpoint="/api/test",
            method="POST",
            size_bytes=1024,
            headers_count=15,
            validation_result="allowed"
        )
    
    def test_update_system_health(self):
        """Test updating system health metrics"""
        # Should not raise an exception
        self.collector.update_system_health("validator", True)
        self.collector.update_system_health("rate_limiter", False)
    
    def test_update_threat_intelligence_stats(self):
        """Test updating threat intelligence statistics"""
        stats = {
            "total_ips": 1000,
            "blocked_ips": 50,
            "suspicious_ips": 200
        }
        
        # Should not raise an exception
        self.collector.update_threat_intelligence_stats(stats)
    
    def test_get_metrics_summary(self):
        """Test getting metrics summary"""
        summary = self.collector.get_metrics_summary()
        
        assert isinstance(summary, dict)
        assert "collector_uptime_seconds" in summary
        assert "metrics_registered" in summary
        assert "prometheus_available" in summary
    
    def test_endpoint_sanitization(self):
        """Test endpoint sanitization for metrics"""
        # Test UUID replacement
        sanitized = self.collector._sanitize_endpoint("/api/users/123e4567-e89b-12d3-a456-426614174000/profile")
        assert "{uuid}" in sanitized
        
        # Test numeric ID replacement
        sanitized = self.collector._sanitize_endpoint("/api/users/12345/posts")
        assert "{id}" in sanitized
        
        # Test long token replacement
        sanitized = self.collector._sanitize_endpoint("/api/auth/abcdef1234567890abcdef1234567890")
        assert "{token}" in sanitized
        
        # Test length limiting
        long_endpoint = "/api/" + "a" * 200
        sanitized = self.collector._sanitize_endpoint(long_endpoint)
        assert len(sanitized) <= 100
    
    def test_attack_type_categorization(self):
        """Test attack type categorization"""
        assert self.collector._categorize_attack_type("sql_injection") == "injection"
        assert self.collector._categorize_attack_type("xss") == "script"
        assert self.collector._categorize_attack_type("path_traversal") == "traversal"
        assert self.collector._categorize_attack_type("header_injection") == "header"
        assert self.collector._categorize_attack_type("unknown_attack") == "other"
    
    def test_primary_attack_category_selection(self):
        """Test primary attack category selection"""
        categories = ["xss", "sql_injection", "path_traversal"]
        primary = self.collector._get_primary_attack_category(categories)
        assert primary == "sql_injection"  # Should prioritize SQL injection
        
        categories = ["header_injection", "xss"]
        primary = self.collector._get_primary_attack_category(categories)
        assert primary == "xss"  # Should prioritize XSS over header injection


class TestHTTPValidatorMetricsIntegration:
    """Test HTTP validator integration with metrics"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = ValidationConfig()
        self.validator = HTTPRequestValidator(self.config)
    
    @pytest.mark.asyncio
    async def test_validator_records_metrics_on_success(self):
        """Test that validator records metrics on successful validation"""
        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.url.query = ""
        mock_request.headers = {"user-agent": "Mozilla/5.0"}
        mock_request.client.host = "192.168.1.1"
        
        # Mock the metrics collector
        with patch.object(self.validator, 'metrics_collector') as mock_collector:
            result = await self.validator.validate_request(mock_request)
            
            # Verify metrics were recorded
            assert mock_collector.record_validation_event.called
            assert mock_collector.record_request_characteristics.called
    
    @pytest.mark.asyncio
    async def test_validator_records_metrics_on_failure(self):
        """Test that validator records metrics on validation failure"""
        # Create mock request with invalid method
        mock_request = Mock(spec=Request)
        mock_request.method = "INVALID"
        mock_request.url.path = "/api/test"
        mock_request.url.query = ""
        mock_request.headers = {"user-agent": "Mozilla/5.0"}
        mock_request.client.host = "192.168.1.1"
        
        # Mock the metrics collector
        with patch.object(self.validator, 'metrics_collector') as mock_collector:
            result = await self.validator.validate_request(mock_request)
            
            # Verify metrics were recorded for failure
            assert mock_collector.record_validation_event.called
            call_args = mock_collector.record_validation_event.call_args[0][0]
            assert call_args.event_type == ValidationEventType.REQUEST_REJECTED
    
    def test_ip_hashing(self):
        """Test IP address hashing for privacy"""
        ip = "192.168.1.1"
        hashed = self.validator._hash_ip(ip)
        
        assert len(hashed) == 16  # Should be truncated to 16 characters
        assert hashed != ip  # Should be different from original
        
        # Same IP should produce same hash
        assert self.validator._hash_ip(ip) == hashed
    
    def test_threat_level_mapping(self):
        """Test threat level string to enum mapping"""
        assert self.validator._map_threat_level("none") == ThreatLevel.NONE
        assert self.validator._map_threat_level("low") == ThreatLevel.LOW
        assert self.validator._map_threat_level("medium") == ThreatLevel.MEDIUM
        assert self.validator._map_threat_level("high") == ThreatLevel.HIGH
        assert self.validator._map_threat_level("critical") == ThreatLevel.CRITICAL
        assert self.validator._map_threat_level("unknown") == ThreatLevel.NONE
    
    def test_user_agent_categorization(self):
        """Test user agent categorization"""
        assert self.validator._categorize_user_agent("Mozilla/5.0 Chrome") == "browser"
        assert self.validator._categorize_user_agent("Googlebot") == "bot"
        assert self.validator._categorize_user_agent("iPhone") == "mobile"
        assert self.validator._categorize_user_agent("curl/7.68.0") == "api_client"
        assert self.validator._categorize_user_agent("sqlmap/1.0") == "security_tool"
        assert self.validator._categorize_user_agent("") == "unknown"


class TestValidationMetricsAPI:
    """Test validation metrics API endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)
    
    def test_get_metrics_summary(self):
        """Test metrics summary endpoint"""
        response = self.client.get("/api/validation/metrics/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "metrics_summary" in data
        assert "timestamp" in data
    
    def test_get_health_status(self):
        """Test health status endpoint"""
        response = self.client.get("/api/validation/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "timestamp" in data
    
    def test_generate_test_security_event(self):
        """Test generating test security events"""
        response = self.client.post(
            "/api/validation/test/security-event",
            params={
                "threat_level": "high",
                "attack_type": "sql_injection",
                "endpoint": "/api/test",
                "method": "POST"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "event_details" in data
    
    def test_generate_test_rate_limit_event(self):
        """Test generating test rate limit events"""
        response = self.client.post(
            "/api/validation/test/rate-limit-event",
            params={
                "rule_name": "test_rule",
                "endpoint": "/api/test",
                "scope": "ip"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "event_details" in data
    
    def test_get_threat_statistics(self):
        """Test threat statistics endpoint"""
        response = self.client.get("/api/validation/stats/threats?hours=24")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "statistics" in data
        assert data["time_period_hours"] == 24
    
    def test_get_metrics_configuration(self):
        """Test metrics configuration endpoint"""
        response = self.client.get("/api/validation/config/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "configuration" in data
    
    def test_cleanup_metrics_cache(self):
        """Test cache cleanup endpoint"""
        response = self.client.post("/api/validation/maintenance/cleanup")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "message" in data
    
    def test_list_available_metrics(self):
        """Test metrics listing endpoint"""
        response = self.client.get("/api/validation/debug/metrics-list")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "metrics_catalog" in data
        assert "total_metrics" in data


class TestConvenienceFunctions:
    """Test convenience functions for metrics recording"""
    
    def test_record_validation_event_function(self):
        """Test the convenience function for recording validation events"""
        # Should not raise an exception
        record_validation_event(
            event_type=ValidationEventType.REQUEST_VALIDATED,
            threat_level=ThreatLevel.NONE,
            validation_rule="test_rule",
            client_ip_hash="test_hash",
            endpoint="/api/test",
            http_method="GET",
            processing_time_ms=10.0
        )
    
    def test_get_validation_metrics_collector_singleton(self):
        """Test that the collector is a singleton"""
        collector1 = get_validation_metrics_collector()
        collector2 = get_validation_metrics_collector()
        
        assert collector1 is collector2


class TestMetricsPerformance:
    """Test metrics system performance"""
    
    def setup_method(self):
        """Setup test environment"""
        self.collector = ValidationMetricsCollector()
    
    def test_high_volume_metrics_recording(self):
        """Test recording high volume of metrics"""
        start_time = time.time()
        
        # Record 1000 events
        for i in range(1000):
            metrics_data = ValidationMetricsData(
                event_type=ValidationEventType.REQUEST_VALIDATED,
                threat_level=ThreatLevel.NONE,
                validation_rule=f"rule_{i % 10}",
                client_ip_hash=f"client_{i % 100}",
                endpoint=f"/api/endpoint_{i % 20}",
                http_method="GET",
                processing_time_ms=float(i % 100)
            )
            self.collector.record_validation_event(metrics_data)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert duration < 5.0, f"High volume metrics recording took {duration}s"
    
    def test_cache_performance(self):
        """Test metrics cache performance"""
        # Generate many unique endpoints to test cache
        for i in range(1000):
            endpoint = f"/api/test/{i}/data"
            sanitized = self.collector._sanitize_endpoint(endpoint)
            assert sanitized is not None
        
        # Cache should have reasonable size
        assert len(self.collector._metric_cache) <= 1000


@pytest.mark.integration
class TestFullValidationPipeline:
    """Integration test for the complete validation pipeline with metrics"""
    
    def setup_method(self):
        """Setup test environment"""
        self.validator = HTTPRequestValidator()
        self.collector = get_validation_metrics_collector()
    
    @pytest.mark.asyncio
    async def test_complete_validation_with_metrics(self):
        """Test complete validation pipeline with metrics collection"""
        # Create a realistic request
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/users"
        mock_request.url.query = "action=create"
        mock_request.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "content-type": "application/json",
            "content-length": "256"
        }
        mock_request.client.host = "192.168.1.100"
        
        # Validate request
        result = await self.validator.validate_request(mock_request)
        
        # Verify validation result
        assert result.is_valid
        assert result.security_threat_level == "none"
        
        # Verify metrics were collected (indirectly by checking no exceptions)
        summary = self.collector.get_metrics_summary()
        assert summary is not None
    
    @pytest.mark.asyncio
    async def test_malicious_request_with_metrics(self):
        """Test malicious request handling with metrics collection"""
        # Create a malicious request
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/users"
        mock_request.url.query = "id=1' OR '1'='1"  # SQL injection attempt
        mock_request.headers = {
            "user-agent": "sqlmap/1.0",
            "content-type": "application/json",
            "content-length": "512"
        }
        mock_request.client.host = "10.0.0.1"
        
        # Mock security analyzer to detect threats
        with patch('ai_karen_engine.server.http_validator.SecurityAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer_class.return_value = mock_analyzer
            
            # Mock security assessment
            mock_assessment = Mock()
            mock_assessment.threat_level = "high"
            mock_assessment.attack_categories = ["sql_injection"]
            mock_assessment.detected_patterns = ["sql_injection_pattern"]
            mock_assessment.client_reputation = "malicious"
            mock_assessment.recommended_action = "block"
            mock_assessment.confidence_score = 0.95
            mock_assessment.risk_factors = {"sql_patterns": 3}
            
            mock_analyzer.analyze_request = AsyncMock(return_value=mock_assessment)
            
            # Validate request
            result = await self.validator.validate_request(mock_request)
            
            # Verify threat was detected
            assert not result.is_valid
            assert result.security_threat_level == "high"
            
            # Verify metrics were collected
            summary = self.collector.get_metrics_summary()
            assert summary is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])