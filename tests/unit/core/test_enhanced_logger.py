"""
Unit tests for Enhanced Logger system
Tests data sanitization, structured logging for security events,
and security alert generation functionality.
"""

import pytest
import json
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import logging

from src.ai_karen_engine.server.enhanced_logger import (
    EnhancedLogger,
    LoggingConfig,
    SecurityEvent,
    SecurityEventType,
    ThreatLevel,
    DataSanitizer,
    SecurityAlertManager,
    get_enhanced_logger,
    init_enhanced_logging
)


class TestDataSanitizer:
    """Test data sanitization functionality"""
    
    def test_sanitize_text_basic(self):
        """Test basic text sanitization"""
        text = "Contact us at test@example.com or call 555-123-4567"
        sanitized = DataSanitizer.sanitize_text(text)
        
        assert "[REDACTED]" in sanitized
        assert "test@example.com" not in sanitized
        assert "555-123-4567" not in sanitized
    
    def test_sanitize_text_jwt_token(self):
        """Test JWT token sanitization"""
        text = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        sanitized = DataSanitizer.sanitize_text(text)
        
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
        assert "[REDACTED]" in sanitized
    
    def test_sanitize_text_api_key(self):
        """Test API key sanitization"""
        text = "API Key: sk-1234567890abcdef1234567890abcdef"
        sanitized = DataSanitizer.sanitize_text(text)
        
        assert "sk-1234567890abcdef1234567890abcdef" not in sanitized
        assert "[REDACTED]" in sanitized
    
    def test_sanitize_text_password_patterns(self):
        """Test password pattern sanitization"""
        text = "password=secret123 and pwd: mypassword"
        sanitized = DataSanitizer.sanitize_text(text)
        
        assert "secret123" not in sanitized
        assert "mypassword" not in sanitized
        assert "[REDACTED]" in sanitized
    
    def test_sanitize_headers(self):
        """Test header sanitization"""
        headers = {
            "Authorization": "Bearer token123",
            "X-API-Key": "secret-key",
            "Content-Type": "application/json",
            "User-Agent": "TestAgent/1.0"
        }
        
        sanitized = DataSanitizer.sanitize_headers(headers)
        
        assert sanitized["Authorization"] == "[REDACTED]"
        assert sanitized["X-API-Key"] == "[REDACTED]"
        assert sanitized["Content-Type"] == "application/json"
        assert sanitized["User-Agent"] == "TestAgent/1.0"
    
    def test_sanitize_query_params(self):
        """Test query parameter sanitization"""
        params = {
            "password": "secret123",
            "api_key": "key123",
            "search": "test query",
            "limit": "10"
        }
        
        sanitized = DataSanitizer.sanitize_query_params(params)
        
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["api_key"] == "[REDACTED]"
        assert sanitized["search"] == "test query"
        assert sanitized["limit"] == "10"
    
    def test_sanitize_request_data(self):
        """Test complete request data sanitization"""
        request_data = {
            "method": "POST",
            "endpoint": "/api/login",
            "headers": {
                "Authorization": "Bearer token123",
                "Content-Type": "application/json"
            },
            "query_params": {
                "password": "secret123",
                "username": "testuser"
            },
            "body": "password=secret456"
        }
        
        sanitized = DataSanitizer.sanitize_request_data(request_data)
        
        assert sanitized["method"] == "POST"
        assert sanitized["endpoint"] == "/api/login"
        assert sanitized["headers"]["Authorization"] == "[REDACTED]"
        assert sanitized["headers"]["Content-Type"] == "application/json"
        assert sanitized["query_params"]["password"] == "[REDACTED]"
        assert sanitized["query_params"]["username"] == "testuser"
        assert "[REDACTED]" in sanitized["body"]
    
    def test_hash_ip_address(self):
        """Test IP address hashing"""
        ip = "192.168.1.1"
        hashed = DataSanitizer.hash_ip_address(ip)
        
        assert hashed != ip
        assert len(hashed) == 16
        assert isinstance(hashed, str)
        
        # Same IP should produce same hash
        hashed2 = DataSanitizer.hash_ip_address(ip)
        assert hashed == hashed2
    
    def test_hash_ip_address_empty(self):
        """Test hashing empty IP address"""
        assert DataSanitizer.hash_ip_address("") == ""
        assert DataSanitizer.hash_ip_address(None) == ""


class TestSecurityEvent:
    """Test SecurityEvent data structure"""
    
    def test_security_event_creation(self):
        """Test creating a security event"""
        event = SecurityEvent(
            event_type=SecurityEventType.INVALID_HTTP_REQUEST,
            threat_level=ThreatLevel.MEDIUM,
            description="Test security event",
            client_ip="192.168.1.1",
            endpoint="/api/test"
        )
        
        assert event.event_type == SecurityEventType.INVALID_HTTP_REQUEST
        assert event.threat_level == ThreatLevel.MEDIUM
        assert event.description == "Test security event"
        assert event.client_ip == "192.168.1.1"
        assert event.endpoint == "/api/test"
        assert isinstance(event.timestamp, datetime)
        assert event.count == 1
    
    def test_security_event_with_attack_patterns(self):
        """Test security event with attack patterns"""
        patterns = ["sql_injection", "xss_attempt"]
        event = SecurityEvent(
            event_type=SecurityEventType.ATTACK_PATTERN_DETECTED,
            threat_level=ThreatLevel.HIGH,
            description="Attack detected",
            attack_patterns=patterns
        )
        
        assert event.attack_patterns == patterns
        assert event.threat_level == ThreatLevel.HIGH


class TestSecurityAlertManager:
    """Test SecurityAlertManager functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = LoggingConfig(
            alert_threshold_high=3,
            alert_threshold_critical=2
        )
        self.alert_manager = SecurityAlertManager(self.config)
    
    def test_should_generate_alert_low_threat(self):
        """Test that low threat events don't generate alerts"""
        event = SecurityEvent(
            event_type=SecurityEventType.INVALID_HTTP_REQUEST,
            threat_level=ThreatLevel.LOW,
            description="Low threat event"
        )
        
        assert not self.alert_manager.should_generate_alert(event)
    
    def test_should_generate_alert_high_threat_threshold(self):
        """Test high threat alert threshold"""
        event = SecurityEvent(
            event_type=SecurityEventType.ATTACK_PATTERN_DETECTED,
            threat_level=ThreatLevel.HIGH,
            description="High threat event",
            client_ip="192.168.1.1"
        )
        
        # First two events should not trigger alert
        assert not self.alert_manager.should_generate_alert(event)
        assert not self.alert_manager.should_generate_alert(event)
        
        # Third event should trigger alert
        assert self.alert_manager.should_generate_alert(event)
    
    def test_should_generate_alert_critical_threat_threshold(self):
        """Test critical threat alert threshold"""
        event = SecurityEvent(
            event_type=SecurityEventType.SECURITY_SCAN_DETECTED,
            threat_level=ThreatLevel.CRITICAL,
            description="Critical threat event",
            client_ip="192.168.1.1"
        )
        
        # First event should not trigger alert
        assert not self.alert_manager.should_generate_alert(event)
        
        # Second event should trigger alert
        assert self.alert_manager.should_generate_alert(event)
    
    def test_generate_alert(self):
        """Test alert generation"""
        # Create a mock logger and replace the alert manager's logger
        mock_logger = Mock()
        self.alert_manager.alert_logger = mock_logger
        
        event = SecurityEvent(
            event_type=SecurityEventType.ATTACK_PATTERN_DETECTED,
            threat_level=ThreatLevel.CRITICAL,
            description="Critical attack detected",
            client_ip="192.168.1.1",
            attack_patterns=["sql_injection"]
        )
        
        self.alert_manager.generate_alert(event)
        
        mock_logger.critical.assert_called_once()
        call_args = mock_logger.critical.call_args
        assert "SECURITY ALERT" in call_args[0][0]
        assert "CRITICAL" in call_args[0][0]


class TestLoggingConfig:
    """Test LoggingConfig functionality"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = LoggingConfig()
        
        assert config.log_level == "INFO"
        assert config.log_dir == "logs"
        assert config.max_log_size == 10 * 1024 * 1024
        assert config.backup_count == 5
        assert config.enable_console_logging is True
        assert config.enable_file_logging is True
        assert config.enable_security_logging is True
        assert config.sanitize_data is True
        assert config.hash_client_ips is True
        assert config.alert_threshold_high == 10
        assert config.alert_threshold_critical == 5
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = LoggingConfig(
            log_level="DEBUG",
            log_dir="/tmp/test_logs",
            sanitize_data=False,
            alert_threshold_high=5
        )
        
        assert config.log_level == "DEBUG"
        assert config.log_dir == "/tmp/test_logs"
        assert config.sanitize_data is False
        assert config.alert_threshold_high == 5


class TestEnhancedLogger:
    """Test EnhancedLogger functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = LoggingConfig(
            log_dir=self.temp_dir,
            enable_console_logging=False,  # Disable console for tests
            alert_threshold_high=2,
            alert_threshold_critical=1
        )
        self.logger = EnhancedLogger(self.config)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_logger_initialization(self):
        """Test logger initialization"""
        assert self.logger.config == self.config
        assert isinstance(self.logger.sanitizer, DataSanitizer)
        assert isinstance(self.logger.alert_manager, SecurityAlertManager)
        assert self.logger.security_events == []
        assert self.logger.event_stats == {}
    
    def test_log_invalid_request(self):
        """Test logging invalid requests"""
        request_data = {
            "method": "POST",
            "endpoint": "/api/test",
            "client_ip": "192.168.1.1",
            "user_agent": "TestAgent/1.0",
            "headers": {"Authorization": "Bearer token123"}
        }
        
        self.logger.log_invalid_request(
            request_data, 
            "malformed_headers", 
            ThreatLevel.MEDIUM
        )
        
        # Check that security event was created
        assert len(self.logger.security_events) == 1
        event = self.logger.security_events[0]
        assert event.event_type == SecurityEventType.MALFORMED_HEADERS
        assert event.threat_level == ThreatLevel.MEDIUM
        assert event.client_ip == "192.168.1.1"
    
    def test_log_security_event(self):
        """Test logging security events"""
        event = SecurityEvent(
            event_type=SecurityEventType.ATTACK_PATTERN_DETECTED,
            threat_level=ThreatLevel.HIGH,
            description="Test attack detected",
            client_ip="192.168.1.1"
        )
        
        self.logger.log_security_event(event)
        
        # Check event was stored
        assert len(self.logger.security_events) == 1
        assert self.logger.security_events[0] == event
        
        # Check statistics were updated
        event_key = f"{event.event_type.value}_{event.threat_level.value}"
        assert self.logger.event_stats[event_key] == 1
    
    def test_log_rate_limit_violation(self):
        """Test logging rate limit violations"""
        self.logger.log_rate_limit_violation(
            client_ip="192.168.1.1",
            endpoint="/api/test",
            limit=100,
            current_count=150,
            request_id="req-123"
        )
        
        assert len(self.logger.security_events) == 1
        event = self.logger.security_events[0]
        assert event.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED
        assert event.threat_level == ThreatLevel.MEDIUM
        assert event.metadata["limit"] == 100
        assert event.metadata["current_count"] == 150
        assert event.metadata["violation_ratio"] == 1.5
    
    def test_log_attack_pattern_detected(self):
        """Test logging attack pattern detection"""
        patterns = ["sql_injection", "xss_attempt"]
        request_data = {
            "method": "POST",
            "endpoint": "/api/login",
            "client_ip": "192.168.1.1",
            "user_agent": "AttackBot/1.0"
        }
        
        self.logger.log_attack_pattern_detected(
            client_ip="192.168.1.1",
            patterns=patterns,
            request_data=request_data,
            threat_level=ThreatLevel.CRITICAL
        )
        
        assert len(self.logger.security_events) == 1
        event = self.logger.security_events[0]
        assert event.event_type == SecurityEventType.ATTACK_PATTERN_DETECTED
        assert event.threat_level == ThreatLevel.CRITICAL
        assert event.attack_patterns == patterns
        assert "sql_injection" in event.description
        assert "xss_attempt" in event.description
    
    def test_log_protocol_violation(self):
        """Test logging protocol violations"""
        details = {
            "invalid_header": "X-Custom-Header",
            "violation_details": "Header contains null bytes"
        }
        
        self.logger.log_protocol_violation(
            client_ip="192.168.1.1",
            violation_type="invalid_header_format",
            details=details,
            request_id="req-456"
        )
        
        assert len(self.logger.security_events) == 1
        event = self.logger.security_events[0]
        assert event.event_type == SecurityEventType.PROTOCOL_VIOLATION
        assert event.threat_level == ThreatLevel.MEDIUM
        assert event.metadata == details
    
    def test_log_security_scan_detected(self):
        """Test logging security scan detection"""
        indicators = ["port_scan", "directory_traversal", "vulnerability_scan"]
        
        self.logger.log_security_scan_detected(
            client_ip="192.168.1.1",
            scan_type="automated_vulnerability_scan",
            indicators=indicators,
            request_id="req-789"
        )
        
        assert len(self.logger.security_events) == 1
        event = self.logger.security_events[0]
        assert event.event_type == SecurityEventType.SECURITY_SCAN_DETECTED
        assert event.threat_level == ThreatLevel.HIGH
        assert event.attack_patterns == indicators
        assert event.metadata["scan_type"] == "automated_vulnerability_scan"
    
    def test_get_security_statistics(self):
        """Test getting security statistics"""
        # Add some test events
        events = [
            SecurityEvent(SecurityEventType.INVALID_HTTP_REQUEST, ThreatLevel.LOW, "Test 1"),
            SecurityEvent(SecurityEventType.ATTACK_PATTERN_DETECTED, ThreatLevel.HIGH, "Test 2"),
            SecurityEvent(SecurityEventType.RATE_LIMIT_EXCEEDED, ThreatLevel.MEDIUM, "Test 3"),
            SecurityEvent(SecurityEventType.ATTACK_PATTERN_DETECTED, ThreatLevel.CRITICAL, "Test 4")
        ]
        
        for event in events:
            self.logger.log_security_event(event)
        
        stats = self.logger.get_security_statistics()
        
        assert stats["total_events"] == 4
        assert stats["threat_level_distribution"]["low"] == 1
        assert stats["threat_level_distribution"]["medium"] == 1
        assert stats["threat_level_distribution"]["high"] == 1
        assert stats["threat_level_distribution"]["critical"] == 1
        assert stats["event_type_distribution"]["attack_pattern_detected"] == 2
        assert stats["event_type_distribution"]["invalid_http_request"] == 1
        assert stats["event_type_distribution"]["rate_limit_exceeded"] == 1
    
    def test_get_recent_security_events(self):
        """Test getting recent security events"""
        # Add events with different timestamps
        now = datetime.now(timezone.utc)
        events = [
            SecurityEvent(SecurityEventType.INVALID_HTTP_REQUEST, ThreatLevel.LOW, "Old event"),
            SecurityEvent(SecurityEventType.ATTACK_PATTERN_DETECTED, ThreatLevel.HIGH, "Recent event")
        ]
        
        # Set timestamps
        events[0].timestamp = now - timedelta(hours=2)
        events[1].timestamp = now - timedelta(minutes=5)
        
        for event in events:
            self.logger.log_security_event(event)
        
        # Get all recent events
        recent = self.logger.get_recent_security_events(limit=10)
        assert len(recent) == 2
        assert recent[0].description == "Recent event"  # Most recent first
        assert recent[1].description == "Old event"
        
        # Get only high threat events
        high_threat = self.logger.get_recent_security_events(
            limit=10, 
            threat_level=ThreatLevel.HIGH
        )
        assert len(high_threat) == 1
        assert high_threat[0].description == "Recent event"
    
    def test_clear_old_events(self):
        """Test clearing old security events"""
        # Add events with different ages
        now = datetime.now(timezone.utc)
        events = [
            SecurityEvent(SecurityEventType.INVALID_HTTP_REQUEST, ThreatLevel.LOW, "Old event 1"),
            SecurityEvent(SecurityEventType.INVALID_HTTP_REQUEST, ThreatLevel.LOW, "Old event 2"),
            SecurityEvent(SecurityEventType.ATTACK_PATTERN_DETECTED, ThreatLevel.HIGH, "Recent event")
        ]
        
        # Set timestamps
        events[0].timestamp = now - timedelta(hours=25)  # Older than 24 hours
        events[1].timestamp = now - timedelta(hours=30)  # Older than 24 hours
        events[2].timestamp = now - timedelta(hours=1)   # Recent
        
        for event in events:
            self.logger.log_security_event(event)
        
        assert len(self.logger.security_events) == 3
        
        # Clear old events (older than 24 hours)
        cleared_count = self.logger.clear_old_events(max_age_hours=24)
        
        assert cleared_count == 2
        assert len(self.logger.security_events) == 1
        assert self.logger.security_events[0].description == "Recent event"


class TestGlobalFunctions:
    """Test global logger functions"""
    
    def setup_method(self):
        """Setup test environment"""
        # Reset global logger
        import src.ai_karen_engine.server.enhanced_logger as logger_module
        logger_module._enhanced_logger = None
    
    def test_get_enhanced_logger(self):
        """Test getting global enhanced logger"""
        logger1 = get_enhanced_logger()
        logger2 = get_enhanced_logger()
        
        # Should return same instance
        assert logger1 is logger2
        assert isinstance(logger1, EnhancedLogger)
    
    def test_init_enhanced_logging(self):
        """Test initializing enhanced logging with custom config"""
        config = LoggingConfig(log_level="DEBUG", sanitize_data=False)
        logger = init_enhanced_logging(config)
        
        assert isinstance(logger, EnhancedLogger)
        assert logger.config.log_level == "DEBUG"
        assert logger.config.sanitize_data is False
        
        # Should return same instance on subsequent calls
        logger2 = get_enhanced_logger()
        assert logger is logger2


class TestIntegration:
    """Integration tests for enhanced logging system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = LoggingConfig(
            log_dir=self.temp_dir,
            enable_console_logging=False,
            alert_threshold_high=2,
            alert_threshold_critical=1
        )
        self.logger = EnhancedLogger(self.config)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_request_validation_flow(self):
        """Test complete request validation and logging flow"""
        # Simulate invalid request with sensitive data
        request_data = {
            "method": "POST",
            "endpoint": "/api/login",
            "client_ip": "192.168.1.100",
            "user_agent": "AttackBot/1.0",
            "request_id": "req-12345",
            "headers": {
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature",
                "Content-Type": "application/json",
                "X-Forwarded-For": "192.168.1.100"
            },
            "query_params": {
                "password": "secret123",
                "username": "admin"
            },
            "body": "password=admin123&email=admin@test.com"
        }
        
        # Log invalid request
        self.logger.log_invalid_request(
            request_data,
            "malformed_headers",
            ThreatLevel.MEDIUM
        )
        
        # Log attack pattern detection
        self.logger.log_attack_pattern_detected(
            client_ip="192.168.1.100",
            patterns=["sql_injection", "admin_brute_force"],
            request_data=request_data,
            threat_level=ThreatLevel.HIGH
        )
        
        # Log rate limit violation
        self.logger.log_rate_limit_violation(
            client_ip="192.168.1.100",
            endpoint="/api/login",
            limit=10,
            current_count=25,
            request_id="req-12345"
        )
        
        # Verify events were logged
        assert len(self.logger.security_events) == 3
        
        # Verify data sanitization
        events = self.logger.security_events
        for event in events:
            if event.metadata:
                # Check that sensitive data was sanitized
                if 'headers' in event.metadata:
                    assert event.metadata['headers']['Authorization'] == '[REDACTED]'
                if 'query_params' in event.metadata:
                    assert event.metadata['query_params']['password'] == '[REDACTED]'
                if 'body' in event.metadata:
                    assert '[REDACTED]' in event.metadata['body']
        
        # Verify statistics
        stats = self.logger.get_security_statistics()
        assert stats['total_events'] == 3
        assert stats['threat_level_distribution']['medium'] == 2  # invalid request + rate limit
        assert stats['threat_level_distribution']['high'] == 1    # attack pattern
        
        # Verify log files were created
        log_dir = Path(self.temp_dir)
        assert (log_dir / "application.log").exists()
        assert (log_dir / "security_events.log").exists()
    
    def test_security_alert_generation(self):
        """Test security alert generation under attack conditions"""
        # Create a mock logger and replace the alert manager's logger
        mock_logger = Mock()
        self.logger.alert_manager.alert_logger = mock_logger
        
        # Simulate multiple critical events to trigger alert
        for i in range(3):
            self.logger.log_attack_pattern_detected(
                client_ip="192.168.1.100",
                patterns=["sql_injection"],
                request_data={"endpoint": "/api/test", "method": "POST"},
                threat_level=ThreatLevel.CRITICAL
            )
        
        # Verify alert was generated (critical threshold is 1, so first event should trigger)
        assert mock_logger.critical.called
        
        # Verify multiple events were logged
        assert len(self.logger.security_events) == 3


if __name__ == "__main__":
    pytest.main([__file__])