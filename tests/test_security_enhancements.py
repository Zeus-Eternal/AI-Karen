"""
Tests for security enhancements and monitoring (Task 13)

This module tests the enhanced security features including:
- Rate limiting with exponential backoff
- Suspicious activity detection
- Security alerts for failed attempts and anomalies
- CSRF protection for state-changing operations
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException, Request, Response
from fastapi.testclient import TestClient

from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.auth.security_monitor import (
    EnhancedSecurityMonitor,
    ExponentialBackoffRateLimiter,
    SuspiciousActivityDetector,
    SecurityAlertManager,
    ThreatLevel,
    AnomalyType,
)
from ai_karen_engine.auth.csrf_protection import (
    CSRFProtectionMiddleware,
    CSRFTokenManager,
    validate_csrf_token,
)
from ai_karen_engine.auth.exceptions import (
    RateLimitExceededError,
    AnomalyDetectedError,
    SuspiciousActivityError,
)


class TestExponentialBackoffRateLimiter:
    """Test exponential backoff rate limiting"""
    
    @pytest.fixture
    def config(self):
        """Create test auth config"""
        config = MagicMock()
        config.security = MagicMock()
        config.security.enable_rate_limiting = True
        return config
    
    @pytest.fixture
    def rate_limiter(self, config):
        """Create rate limiter instance"""
        return ExponentialBackoffRateLimiter(config)
    
    @pytest.mark.asyncio
    async def test_rate_limit_allows_initial_requests(self, rate_limiter):
        """Test that initial requests are allowed"""
        ip_address = "192.168.1.1"
        email = "test@example.com"
        
        # First few requests should be allowed
        for i in range(5):
            result = await rate_limiter.check_rate_limit(ip_address, email)
            assert result is True
            await rate_limiter.record_attempt(ip_address, email, success=False)
    
    @pytest.mark.asyncio
    async def test_rate_limit_blocks_excessive_requests(self, rate_limiter):
        """Test that excessive requests are blocked with exponential backoff"""
        ip_address = "192.168.1.2"
        email = "test2@example.com"
        
        # Fill up the rate limit
        for i in range(5):
            await rate_limiter.check_rate_limit(ip_address, email)
            await rate_limiter.record_attempt(ip_address, email, success=False)
        
        # Next request should be blocked
        with pytest.raises(RateLimitExceededError) as exc_info:
            await rate_limiter.check_rate_limit(ip_address, email)
        
        error = exc_info.value
        assert error.details["backoff_level"] == 1
        assert error.details["ip_address"] == ip_address
        assert error.details["email"] == email
        assert "retry_after" in error.details
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_increases(self, rate_limiter):
        """Test that backoff level increases with repeated violations"""
        ip_address = "192.168.1.3"
        email = "test3@example.com"
        
        # First violation
        for i in range(6):  # Exceed limit
            try:
                await rate_limiter.check_rate_limit(ip_address, email)
                await rate_limiter.record_attempt(ip_address, email, success=False)
            except RateLimitExceededError:
                pass
        
        backoff_level_1 = rate_limiter.get_current_backoff_level(ip_address, email)
        assert backoff_level_1 >= 1
        
        # Wait for lockout to expire (simulate)
        rate_limiter._lockout_until.clear()
        
        # Second violation should increase backoff
        for i in range(6):
            try:
                await rate_limiter.check_rate_limit(ip_address, email)
                await rate_limiter.record_attempt(ip_address, email, success=False)
            except RateLimitExceededError:
                pass
        
        backoff_level_2 = rate_limiter.get_current_backoff_level(ip_address, email)
        assert backoff_level_2 > backoff_level_1
    
    @pytest.mark.asyncio
    async def test_successful_auth_resets_backoff(self, rate_limiter):
        """Test that successful authentication resets backoff level"""
        ip_address = "192.168.1.4"
        email = "test4@example.com"
        
        # Create a violation
        for i in range(6):
            try:
                await rate_limiter.check_rate_limit(ip_address, email)
                await rate_limiter.record_attempt(ip_address, email, success=False)
            except RateLimitExceededError:
                pass
        
        initial_backoff = rate_limiter.get_current_backoff_level(ip_address, email)
        assert initial_backoff >= 1
        
        # Successful authentication should reset backoff
        await rate_limiter.record_attempt(ip_address, email, success=True)
        
        final_backoff = rate_limiter.get_current_backoff_level(ip_address, email)
        assert final_backoff == 0


class TestSuspiciousActivityDetector:
    """Test suspicious activity detection"""
    
    @pytest.fixture
    def config(self):
        """Create test auth config"""
        config = MagicMock()
        config.security = MagicMock()
        return config
    
    @pytest.fixture
    def detector(self, config):
        """Create activity detector instance"""
        return SuspiciousActivityDetector(config)
    
    @pytest.mark.asyncio
    async def test_rapid_failed_attempts_detection(self, detector):
        """Test detection of rapid failed attempts"""
        ip_address = "192.168.1.5"
        email = "test5@example.com"
        user_agent = "TestAgent/1.0"
        
        # Simulate rapid failed attempts
        for i in range(15):  # Above threshold
            result = await detector.analyze_attempt(
                ip_address=ip_address,
                user_agent=user_agent,
                email=email,
                success=False,
                failure_reason="invalid_credentials",
            )
        
        # Last attempt should detect anomaly
        assert result.is_suspicious
        assert AnomalyType.RAPID_FAILED_ATTEMPTS in result.anomaly_types
        assert result.risk_score > 0.7
        assert result.confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_multiple_ips_detection(self, detector):
        """Test detection of multiple IPs for same user"""
        email = "test6@example.com"
        user_agent = "TestAgent/1.0"
        
        # Simulate logins from multiple IPs
        ips = ["192.168.1.10", "192.168.1.11", "192.168.1.12", "192.168.1.13"]
        
        for ip in ips:
            result = await detector.analyze_attempt(
                ip_address=ip,
                user_agent=user_agent,
                email=email,
                success=True,
            )
        
        # Should detect multiple IPs anomaly
        assert result.is_suspicious
        assert AnomalyType.MULTIPLE_IPS in result.anomaly_types
        assert result.risk_score > 0.5
    
    @pytest.mark.asyncio
    async def test_unusual_location_detection(self, detector):
        """Test detection of unusual geographic locations"""
        email = "test7@example.com"
        user_agent = "TestAgent/1.0"
        ip_address = "192.168.1.15"
        
        # Establish normal locations
        normal_locations = [
            {"country": "US", "city": "New York"},
            {"country": "US", "city": "Los Angeles"},
            {"country": "US", "city": "Chicago"},
        ]
        
        for location in normal_locations:
            await detector.analyze_attempt(
                ip_address=ip_address,
                user_agent=user_agent,
                email=email,
                success=True,
                geolocation=location,
            )
        
        # Login from unusual location
        unusual_location = {"country": "RU", "city": "Moscow"}
        result = await detector.analyze_attempt(
            ip_address=ip_address,
            user_agent=user_agent,
            email=email,
            success=True,
            geolocation=unusual_location,
        )
        
        assert result.is_suspicious
        assert AnomalyType.UNUSUAL_LOCATION in result.anomaly_types
    
    @pytest.mark.asyncio
    async def test_brute_force_pattern_detection(self, detector):
        """Test detection of brute force attack patterns"""
        ip_address = "192.168.1.20"
        user_agent = "AttackBot/1.0"
        
        # Simulate brute force attack with multiple emails
        emails = [f"user{i}@example.com" for i in range(10)]
        
        for email in emails:
            for attempt in range(3):  # Multiple attempts per email
                await detector.analyze_attempt(
                    ip_address=ip_address,
                    user_agent=user_agent,
                    email=email,
                    success=False,
                    failure_reason="invalid_credentials",
                )
        
        # Should detect brute force pattern
        result = await detector.analyze_attempt(
            ip_address=ip_address,
            user_agent=user_agent,
            email="final@example.com",
            success=False,
            failure_reason="invalid_credentials",
        )
        
        assert result.is_suspicious
        assert AnomalyType.BRUTE_FORCE_PATTERN in result.anomaly_types
        assert result.risk_score > 0.8
    
    @pytest.mark.asyncio
    async def test_account_enumeration_detection(self, detector):
        """Test detection of account enumeration attempts"""
        ip_address = "192.168.1.25"
        user_agent = "EnumBot/1.0"
        
        # Simulate account enumeration with many "user not found" errors
        for i in range(15):
            await detector.analyze_attempt(
                ip_address=ip_address,
                user_agent=user_agent,
                email=f"nonexistent{i}@example.com",
                success=False,
                failure_reason="user_not_found",
            )
        
        # Should detect account enumeration
        result = await detector.analyze_attempt(
            ip_address=ip_address,
            user_agent=user_agent,
            email="another@example.com",
            success=False,
            failure_reason="user_not_found",
        )
        
        assert result.is_suspicious
        assert AnomalyType.ACCOUNT_ENUMERATION in result.anomaly_types


class TestSecurityAlertManager:
    """Test security alert management"""
    
    @pytest.fixture
    def config(self):
        """Create test auth config"""
        config = MagicMock()
        return config
    
    @pytest.fixture
    def alert_manager(self, config):
        """Create alert manager instance"""
        return SecurityAlertManager(config)
    
    @pytest.mark.asyncio
    async def test_create_failed_attempt_alert(self, alert_manager):
        """Test creation of failed attempt alerts"""
        ip_address = "192.168.1.30"
        email = "test@example.com"
        attempt_count = 25
        time_window = "1 hour"
        
        alert = await alert_manager.create_failed_attempt_alert(
            ip_address, email, attempt_count, time_window
        )
        
        assert alert.alert_type == "excessive_failed_attempts"
        assert alert.threat_level == ThreatLevel.HIGH  # > 20 attempts
        assert alert.source_ip == ip_address
        assert alert.user_email == email
        assert alert.details["attempt_count"] == attempt_count
        assert alert.details["time_window"] == time_window
    
    @pytest.mark.asyncio
    async def test_create_anomaly_alert(self, alert_manager):
        """Test creation of anomaly alerts"""
        ip_address = "192.168.1.31"
        email = "test@example.com"
        
        # Create mock suspicious activity
        suspicious_activity = MagicMock()
        suspicious_activity.risk_score = 0.9
        suspicious_activity.confidence = 0.8
        suspicious_activity.anomaly_types = [AnomalyType.BRUTE_FORCE_PATTERN]
        suspicious_activity.details = {"test": "data"}
        
        alert = await alert_manager.create_anomaly_alert(
            ip_address, suspicious_activity, email
        )
        
        assert alert.alert_type == "authentication_anomaly"
        assert alert.threat_level == ThreatLevel.CRITICAL  # risk_score >= 0.8
        assert alert.source_ip == ip_address
        assert alert.user_email == email
        assert alert.details["risk_score"] == 0.9
        assert alert.details["confidence"] == 0.8
    
    def test_get_recent_alerts(self, alert_manager):
        """Test retrieval of recent alerts"""
        # Create some test alerts
        alert1 = MagicMock()
        alert1.timestamp = datetime.now(timezone.utc) - timedelta(hours=1)
        alert1.threat_level = ThreatLevel.HIGH
        
        alert2 = MagicMock()
        alert2.timestamp = datetime.now(timezone.utc) - timedelta(hours=25)  # Too old
        alert2.threat_level = ThreatLevel.MEDIUM
        
        alert3 = MagicMock()
        alert3.timestamp = datetime.now(timezone.utc) - timedelta(minutes=30)
        alert3.threat_level = ThreatLevel.CRITICAL
        
        alert_manager._alerts = [alert1, alert2, alert3]
        
        # Get recent alerts (24 hours)
        recent_alerts = alert_manager.get_recent_alerts(hours=24)
        assert len(recent_alerts) == 2  # alert2 is too old
        assert alert3 in recent_alerts  # Most recent first
        assert alert1 in recent_alerts
        
        # Filter by threat level
        high_alerts = alert_manager.get_recent_alerts(hours=24, threat_level=ThreatLevel.HIGH)
        assert len(high_alerts) == 1
        assert alert1 in high_alerts
    
    def test_get_alert_stats(self, alert_manager):
        """Test alert statistics generation"""
        # Create test alerts
        alerts = []
        for i in range(5):
            alert = MagicMock()
            alert.timestamp = datetime.now(timezone.utc) - timedelta(minutes=i*10)
            alert.threat_level = ThreatLevel.HIGH if i % 2 == 0 else ThreatLevel.MEDIUM
            alert.alert_type = "test_alert"
            alert.source_ip = f"192.168.1.{i}"
            alert.user_email = f"user{i}@example.com"
            alerts.append(alert)
        
        alert_manager._alerts = alerts
        
        stats = alert_manager.get_alert_stats(hours=24)
        
        assert stats["total_alerts"] == 5
        assert stats["by_threat_level"]["high"] == 3
        assert stats["by_threat_level"]["medium"] == 2
        assert stats["by_alert_type"]["test_alert"] == 5
        assert stats["unique_source_ips"] == 5
        assert stats["affected_users"] == 5


class TestCSRFProtection:
    """Test CSRF protection functionality"""
    
    @pytest.fixture
    def config(self):
        """Create test auth config"""
        config = MagicMock()
        config.jwt = MagicMock()
        config.jwt.secret_key = "test-secret-key"
        config.security = MagicMock()
        config.security.enable_csrf_protection = True
        return config
    
    @pytest.fixture
    def csrf_manager(self, config):
        """Create CSRF token manager instance"""
        return CSRFTokenManager(config)
    
    @pytest.fixture
    def csrf_middleware(self, config):
        """Create CSRF protection middleware instance"""
        return CSRFProtectionMiddleware(config)
    
    def test_generate_csrf_token(self, csrf_manager):
        """Test CSRF token generation"""
        user_id = "test-user-123"
        token = csrf_manager.generate_csrf_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert ":" in token  # Should contain separators
    
    def test_validate_csrf_token(self, csrf_manager):
        """Test CSRF token validation"""
        user_id = "test-user-123"
        token = csrf_manager.generate_csrf_token(user_id)
        
        # Valid token should pass
        assert csrf_manager.validate_csrf_token(token, user_id) is True
        
        # Invalid token should fail
        assert csrf_manager.validate_csrf_token("invalid-token", user_id) is False
        
        # Token for different user should fail
        assert csrf_manager.validate_csrf_token(token, "different-user") is False
    
    def test_csrf_token_expiry(self, csrf_manager):
        """Test CSRF token expiry"""
        user_id = "test-user-123"
        
        # Mock time to simulate expired token
        with patch('time.time') as mock_time:
            # Generate token at time 0
            mock_time.return_value = 0
            token = csrf_manager.generate_csrf_token(user_id)
            
            # Validate at time within expiry (should pass)
            mock_time.return_value = 1800  # 30 minutes
            assert csrf_manager.validate_csrf_token(token, user_id) is True
            
            # Validate at time beyond expiry (should fail)
            mock_time.return_value = 7200  # 2 hours (beyond 1 hour limit)
            assert csrf_manager.validate_csrf_token(token, user_id) is False
    
    def test_csrf_cookie_operations(self, csrf_manager):
        """Test CSRF cookie setting and retrieval"""
        token = "test-csrf-token"
        
        # Mock response and request
        response = MagicMock()
        request = MagicMock()
        request.cookies = {"csrf_token": token}
        
        # Set cookie
        csrf_manager.set_csrf_cookie(response, token, secure=True)
        response.set_cookie.assert_called_once()
        
        # Get cookie
        retrieved_token = csrf_manager.get_csrf_token_from_cookie(request)
        assert retrieved_token == token
        
        # Clear cookie
        csrf_manager.clear_csrf_cookie(response)
        response.delete_cookie.assert_called_once()
    
    def test_csrf_middleware_protection_check(self, csrf_middleware):
        """Test CSRF middleware protection requirements"""
        # Mock request
        request = MagicMock()
        
        # POST request to auth endpoint should be protected
        request.method = "POST"
        request.url.path = "/api/auth/login"
        assert csrf_middleware.is_protected_request(request) is True
        
        # GET request should not be protected
        request.method = "GET"
        request.url.path = "/api/auth/me"
        assert csrf_middleware.is_protected_request(request) is False
        
        # Exempt path should not be protected
        request.method = "POST"
        request.url.path = "/api/auth/refresh"
        assert csrf_middleware.is_protected_request(request) is False
    
    @pytest.mark.asyncio
    async def test_csrf_validation_success(self, csrf_middleware):
        """Test successful CSRF validation"""
        user_id = "test-user-123"
        token = "valid-csrf-token"
        
        # Mock request with matching tokens
        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/auth/login"
        request.cookies = {"csrf_token": token}
        request.headers = {"X-CSRF-Token": token}
        
        # Mock token validation
        with patch.object(csrf_middleware.token_manager, 'validate_csrf_token', return_value=True):
            # Should not raise exception
            await csrf_middleware.validate_csrf_protection(request, user_id)
    
    @pytest.mark.asyncio
    async def test_csrf_validation_missing_token(self, csrf_middleware):
        """Test CSRF validation with missing tokens"""
        # Mock request without tokens
        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/auth/login"
        request.cookies = {}
        request.headers = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await csrf_middleware.validate_csrf_protection(request)
        
        assert exc_info.value.status_code == 403
        assert "CSRF token missing" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_csrf_validation_token_mismatch(self, csrf_middleware):
        """Test CSRF validation with mismatched tokens"""
        # Mock request with mismatched tokens
        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/auth/login"
        request.cookies = {"csrf_token": "token1"}
        request.headers = {"X-CSRF-Token": "token2"}
        
        with pytest.raises(HTTPException) as exc_info:
            await csrf_middleware.validate_csrf_protection(request)
        
        assert exc_info.value.status_code == 403
        assert "CSRF token mismatch" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_csrf_validation_invalid_token(self, csrf_middleware):
        """Test CSRF validation with invalid token"""
        token = "invalid-token"
        
        # Mock request with matching but invalid tokens
        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/auth/login"
        request.cookies = {"csrf_token": token}
        request.headers = {"X-CSRF-Token": token}
        
        # Mock token validation to return False
        with patch.object(csrf_middleware.token_manager, 'validate_csrf_token', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await csrf_middleware.validate_csrf_protection(request)
            
            assert exc_info.value.status_code == 403
            assert "CSRF token invalid or expired" in exc_info.value.detail


class TestEnhancedSecurityMonitor:
    """Test the main security monitoring service"""
    
    @pytest.fixture
    def config(self):
        """Create test auth config"""
        config = MagicMock()
        config.security = MagicMock()
        config.security.enable_rate_limiting = True
        config.security.enable_anomaly_detection = True
        config.security.enable_security_alerts = True
        return config
    
    @pytest.fixture
    def security_monitor(self, config):
        """Create security monitor instance"""
        return EnhancedSecurityMonitor(config)
    
    @pytest.mark.asyncio
    async def test_check_authentication_security_allows_normal_request(self, security_monitor):
        """Test that normal requests are allowed"""
        ip_address = "192.168.1.100"
        user_agent = "NormalBrowser/1.0"
        email = "normal@example.com"
        
        # Should not raise any exceptions
        await security_monitor.check_authentication_security(
            ip_address=ip_address,
            user_agent=user_agent,
            email=email,
            endpoint="login",
        )
    
    @pytest.mark.asyncio
    async def test_check_authentication_security_blocks_suspicious_activity(self, security_monitor):
        """Test that suspicious activity is blocked"""
        ip_address = "192.168.1.101"
        user_agent = "AttackBot/1.0"
        email = "attacker@example.com"
        
        # First, create suspicious activity by making many failed attempts
        for i in range(15):
            await security_monitor.record_authentication_result(
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                email=email,
                failure_reason="invalid_credentials",
            )
        
        # Next request should be blocked due to suspicious activity
        with pytest.raises(AnomalyDetectedError):
            await security_monitor.check_authentication_security(
                ip_address=ip_address,
                user_agent=user_agent,
                email=email,
                endpoint="login",
            )
    
    @pytest.mark.asyncio
    async def test_record_authentication_result_creates_alerts(self, security_monitor):
        """Test that authentication results create appropriate alerts"""
        ip_address = "192.168.1.102"
        user_agent = "TestBrowser/1.0"
        email = "test@example.com"
        
        # Record many failed attempts to trigger alert
        for i in range(12):  # Above threshold for alert
            await security_monitor.record_authentication_result(
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                email=email,
                failure_reason="invalid_credentials",
            )
        
        # Check that alerts were created
        recent_alerts = security_monitor.alert_manager.get_recent_alerts(hours=1)
        assert len(recent_alerts) > 0
        
        # Should have failed attempt alert
        failed_attempt_alerts = [
            a for a in recent_alerts 
            if a.alert_type == "excessive_failed_attempts"
        ]
        assert len(failed_attempt_alerts) > 0
    
    def test_get_security_stats(self, security_monitor):
        """Test security statistics generation"""
        stats = security_monitor.get_security_stats()
        
        assert "alerts" in stats
        assert "rate_limiting" in stats
        assert "anomaly_detection" in stats
        
        assert "enabled" in stats["rate_limiting"]
        assert "enabled" in stats["anomaly_detection"]
        
        assert isinstance(stats["alerts"], dict)
        assert isinstance(stats["rate_limiting"]["enabled"], bool)
        assert isinstance(stats["anomaly_detection"]["enabled"], bool)


class TestSecurityIntegration:
    """Integration tests for security enhancements"""
    
    @pytest.mark.asyncio
    async def test_rate_limiting_integration_with_auth_routes(self):
        """Test rate limiting integration with authentication routes"""
        # This would require a full FastAPI test client setup
        # For now, we'll test the components work together
        
        config = MagicMock()
        config.security = MagicMock()
        config.security.enable_rate_limiting = True
        config.security.enable_anomaly_detection = True
        config.security.enable_security_alerts = True
        
        security_monitor = EnhancedSecurityMonitor(config)
        
        ip_address = "192.168.1.200"
        user_agent = "TestClient/1.0"
        email = "integration@example.com"
        
        # Simulate multiple failed login attempts
        for i in range(10):
            try:
                await security_monitor.check_authentication_security(
                    ip_address=ip_address,
                    user_agent=user_agent,
                    email=email,
                    endpoint="login",
                )
                
                await security_monitor.record_authentication_result(
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    email=email,
                    failure_reason="invalid_credentials",
                )
            except (RateLimitExceededError, AnomalyDetectedError):
                # Expected after several attempts
                break
        
        # Verify that security monitoring is working
        stats = security_monitor.get_security_stats()
        assert stats["rate_limiting"]["enabled"] is True
        assert stats["anomaly_detection"]["enabled"] is True
    
    @pytest.mark.asyncio
    async def test_csrf_protection_integration(self):
        """Test CSRF protection integration"""
        config = MagicMock()
        config.jwt = MagicMock()
        config.jwt.secret_key = "test-secret"
        config.security = MagicMock()
        config.security.enable_csrf_protection = True
        
        csrf_middleware = CSRFProtectionMiddleware(config)
        
        # Test token generation and validation flow
        user_id = "test-user"
        response = MagicMock()
        
        # Generate token
        token = csrf_middleware.generate_csrf_response(response, user_id, secure=True)
        assert len(token) > 0
        
        # Verify cookie was set
        response.set_cookie.assert_called_once()
        
        # Test validation
        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/auth/login"
        request.cookies = {"csrf_token": token}
        request.headers = {"X-CSRF-Token": token}
        
        # Should not raise exception with valid token
        await csrf_middleware.validate_csrf_protection(request, user_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])