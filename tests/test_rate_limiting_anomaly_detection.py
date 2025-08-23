"""
Focused tests for rate limiting and anomaly detection features

This module provides comprehensive tests for the enhanced rate limiting
with exponential backoff and anomaly detection capabilities.
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from unittest.mock import MagicMock, patch

from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.auth.security_monitor import (
    ExponentialBackoffRateLimiter,
    SuspiciousActivityDetector,
    AnomalyType,
    AuthAttempt,
)
from ai_karen_engine.auth.exceptions import RateLimitExceededError


class TestRateLimitingScenarios:
    """Test various rate limiting scenarios"""
    
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        config = MagicMock()
        config.security = MagicMock()
        config.security.enable_rate_limiting = True
        return config
    
    @pytest.fixture
    def rate_limiter(self, config):
        """Create rate limiter with test configuration"""
        limiter = ExponentialBackoffRateLimiter(config)
        # Override defaults for faster testing
        limiter.base_window_seconds = 10  # 10 second window
        limiter.max_attempts_per_window = 3  # 3 attempts max
        limiter.backoff_multiplier = 2.0
        limiter.max_backoff_hours = 1  # 1 hour max
        return limiter
    
    @pytest.mark.asyncio
    async def test_basic_rate_limiting_flow(self, rate_limiter):
        """Test basic rate limiting flow"""
        ip = "10.0.0.1"
        email = "user@test.com"
        
        # First 3 attempts should succeed
        for i in range(3):
            result = await rate_limiter.check_rate_limit(ip, email, "login")
            assert result is True
            await rate_limiter.record_attempt(ip, email, success=False)
        
        # 4th attempt should fail with rate limit
        with pytest.raises(RateLimitExceededError) as exc_info:
            await rate_limiter.check_rate_limit(ip, email, "login")
        
        error = exc_info.value
        assert error.details["backoff_level"] == 1
        assert error.details["endpoint"] == "login"
        assert "retry_after" in error.details
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_calculation(self, rate_limiter):
        """Test exponential backoff duration calculation"""
        ip = "10.0.0.2"
        email = "user2@test.com"
        
        # Trigger first lockout
        for i in range(4):
            try:
                await rate_limiter.check_rate_limit(ip, email, "login")
                await rate_limiter.record_attempt(ip, email, success=False)
            except RateLimitExceededError as e:
                first_backoff = e.details["retry_after"]
                break
        
        # Clear lockout to simulate expiry
        rate_limiter._lockout_until.clear()
        
        # Trigger second lockout
        for i in range(4):
            try:
                await rate_limiter.check_rate_limit(ip, email, "login")
                await rate_limiter.record_attempt(ip, email, success=False)
            except RateLimitExceededError as e:
                second_backoff = e.details["retry_after"]
                break
        
        # Second backoff should be longer (exponential)
        assert second_backoff > first_backoff
        assert rate_limiter.get_current_backoff_level(ip, email) == 2
    
    @pytest.mark.asyncio
    async def test_successful_auth_resets_backoff(self, rate_limiter):
        """Test that successful authentication resets backoff"""
        ip = "10.0.0.3"
        email = "user3@test.com"
        
        # Build up backoff level
        for attempt_round in range(2):
            for i in range(4):
                try:
                    await rate_limiter.check_rate_limit(ip, email, "login")
                    await rate_limiter.record_attempt(ip, email, success=False)
                except RateLimitExceededError:
                    pass
            # Clear lockout to continue
            rate_limiter._lockout_until.clear()
        
        backoff_before = rate_limiter.get_current_backoff_level(ip, email)
        assert backoff_before >= 2
        
        # Successful authentication should reset
        await rate_limiter.record_attempt(ip, email, success=True)
        
        backoff_after = rate_limiter.get_current_backoff_level(ip, email)
        assert backoff_after == 0
    
    @pytest.mark.asyncio
    async def test_different_endpoints_separate_limits(self, rate_limiter):
        """Test that different endpoints have separate rate limits"""
        ip = "10.0.0.4"
        email = "user4@test.com"
        
        # Fill up login endpoint limit
        for i in range(3):
            await rate_limiter.check_rate_limit(ip, email, "login")
            await rate_limiter.record_attempt(ip, email, success=False)
        
        # Login should be blocked
        with pytest.raises(RateLimitExceededError):
            await rate_limiter.check_rate_limit(ip, email, "login")
        
        # But register should still work (different endpoint)
        result = await rate_limiter.check_rate_limit(ip, email, "register")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_ip_vs_user_rate_limiting(self, rate_limiter):
        """Test IP-based vs user-based rate limiting"""
        ip1 = "10.0.0.5"
        ip2 = "10.0.0.6"
        email = "shared@test.com"
        
        # Fill up limit for email from IP1
        for i in range(3):
            await rate_limiter.check_rate_limit(ip1, email, "login")
            await rate_limiter.record_attempt(ip1, email, success=False)
        
        # Same email from IP1 should be blocked
        with pytest.raises(RateLimitExceededError):
            await rate_limiter.check_rate_limit(ip1, email, "login")
        
        # But same email from different IP should work initially
        # (though it will contribute to user-based limiting)
        result = await rate_limiter.check_rate_limit(ip2, email, "login")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_lockout_expiry_simulation(self, rate_limiter):
        """Test lockout expiry behavior"""
        ip = "10.0.0.7"
        email = "user7@test.com"
        
        # Trigger lockout
        for i in range(4):
            try:
                await rate_limiter.check_rate_limit(ip, email, "login")
                await rate_limiter.record_attempt(ip, email, success=False)
            except RateLimitExceededError:
                break
        
        # Should be locked out
        with pytest.raises(RateLimitExceededError):
            await rate_limiter.check_rate_limit(ip, email, "login")
        
        # Simulate lockout expiry by clearing it
        rate_limiter._lockout_until.clear()
        
        # Should work again after expiry
        result = await rate_limiter.check_rate_limit(ip, email, "login")
        assert result is True


class TestAnomalyDetectionScenarios:
    """Test various anomaly detection scenarios"""
    
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        config = MagicMock()
        config.security = MagicMock()
        return config
    
    @pytest.fixture
    def detector(self, config):
        """Create detector with test configuration"""
        detector = SuspiciousActivityDetector(config)
        # Override thresholds for testing
        detector.rapid_attempts_threshold = 5  # 5 attempts per minute
        detector.multiple_ip_threshold = 2  # 2 different IPs per hour
        return detector
    
    @pytest.mark.asyncio
    async def test_rapid_attempts_threshold_detection(self, detector):
        """Test rapid attempts detection with exact threshold"""
        ip = "10.1.0.1"
        email = "rapid@test.com"
        user_agent = "TestAgent/1.0"
        
        # Just under threshold should not trigger
        for i in range(4):
            result = await detector.analyze_attempt(
                ip_address=ip,
                user_agent=user_agent,
                email=email,
                success=False,
                failure_reason="invalid_credentials",
            )
        
        assert not result.is_suspicious
        
        # At threshold should trigger
        result = await detector.analyze_attempt(
            ip_address=ip,
            user_agent=user_agent,
            email=email,
            success=False,
            failure_reason="invalid_credentials",
        )
        
        assert result.is_suspicious
        assert AnomalyType.RAPID_FAILED_ATTEMPTS in result.anomaly_types
    
    @pytest.mark.asyncio
    async def test_multiple_ip_detection_timing(self, detector):
        """Test multiple IP detection with timing considerations"""
        email = "multi_ip@test.com"
        user_agent = "TestAgent/1.0"
        
        # Login from first IP
        result1 = await detector.analyze_attempt(
            ip_address="10.1.0.10",
            user_agent=user_agent,
            email=email,
            success=True,
        )
        assert not result1.is_suspicious
        
        # Login from second IP (should trigger)
        result2 = await detector.analyze_attempt(
            ip_address="10.1.0.11",
            user_agent=user_agent,
            email=email,
            success=True,
        )
        
        assert result2.is_suspicious
        assert AnomalyType.MULTIPLE_IPS in result2.anomaly_types
        assert result2.details["multiple_ips"]["unique_ips_per_hour"] == 2
    
    @pytest.mark.asyncio
    async def test_location_based_anomaly_detection(self, detector):
        """Test location-based anomaly detection"""
        email = "traveler@test.com"
        user_agent = "TestAgent/1.0"
        ip = "10.1.0.20"
        
        # Establish pattern with US locations
        us_locations = [
            {"country": "US", "city": "New York"},
            {"country": "US", "city": "San Francisco"},
            {"country": "US", "city": "Chicago"},
        ]
        
        for location in us_locations:
            result = await detector.analyze_attempt(
                ip_address=ip,
                user_agent=user_agent,
                email=email,
                success=True,
                geolocation=location,
            )
            # Should not be suspicious yet
            assert not result.is_suspicious
        
        # Login from different country should be suspicious
        foreign_location = {"country": "CN", "city": "Beijing"}
        result = await detector.analyze_attempt(
            ip_address=ip,
            user_agent=user_agent,
            email=email,
            success=True,
            geolocation=foreign_location,
        )
        
        assert result.is_suspicious
        assert AnomalyType.UNUSUAL_LOCATION in result.anomaly_types
        assert result.details["unusual_location"]["new_country"] == "CN"
    
    @pytest.mark.asyncio
    async def test_time_based_anomaly_detection(self, detector):
        """Test time-based anomaly detection"""
        email = "worker@test.com"
        user_agent = "TestAgent/1.0"
        ip = "10.1.0.30"
        
        # Establish pattern - user typically logs in during business hours (9-17)
        business_hours = [9, 10, 11, 14, 15, 16, 9, 10, 11, 14]  # 10 logins
        
        for hour in business_hours:
            with patch('ai_karen_engine.auth.security_monitor.datetime') as mock_dt:
                mock_dt.now.return_value = datetime(2024, 1, 1, hour, 0, 0, tzinfo=timezone.utc)
                mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
                
                result = await detector.analyze_attempt(
                    ip_address=ip,
                    user_agent=user_agent,
                    email=email,
                    success=True,
                )
        
        # Login at unusual time (3 AM) should be suspicious
        with patch('ai_karen_engine.auth.security_monitor.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = await detector.analyze_attempt(
                ip_address=ip,
                user_agent=user_agent,
                email=email,
                success=True,
            )
        
        assert result.is_suspicious
        assert AnomalyType.UNUSUAL_TIME in result.anomaly_types
        assert result.details["unusual_time"]["login_hour"] == 3
    
    @pytest.mark.asyncio
    async def test_brute_force_pattern_detection(self, detector):
        """Test brute force pattern detection"""
        ip = "10.1.0.40"
        user_agent = "AttackBot/1.0"
        
        # Simulate brute force - many failures across different emails
        emails = [f"target{i}@test.com" for i in range(10)]
        
        # Create enough attempts to trigger detection
        for email in emails:
            for attempt in range(3):  # 3 attempts per email = 30 total
                await detector.analyze_attempt(
                    ip_address=ip,
                    user_agent=user_agent,
                    email=email,
                    success=False,
                    failure_reason="invalid_credentials",
                )
        
        # Final attempt should detect brute force
        result = await detector.analyze_attempt(
            ip_address=ip,
            user_agent=user_agent,
            email="final@test.com",
            success=False,
            failure_reason="invalid_credentials",
        )
        
        assert result.is_suspicious
        assert AnomalyType.BRUTE_FORCE_PATTERN in result.anomaly_types
        assert result.details["brute_force"]["failure_rate"] > 0.8
        assert result.details["brute_force"]["unique_emails_targeted"] >= 5
    
    @pytest.mark.asyncio
    async def test_account_enumeration_detection(self, detector):
        """Test account enumeration detection"""
        ip = "10.1.0.50"
        user_agent = "EnumBot/1.0"
        
        # Simulate account enumeration - many "user not found" errors
        for i in range(12):  # Above threshold
            await detector.analyze_attempt(
                ip_address=ip,
                user_agent=user_agent,
                email=f"probe{i}@test.com",
                success=False,
                failure_reason="user_not_found",
            )
        
        # Should detect enumeration
        result = await detector.analyze_attempt(
            ip_address=ip,
            user_agent=user_agent,
            email="probe_final@test.com",
            success=False,
            failure_reason="user_not_found",
        )
        
        assert result.is_suspicious
        assert AnomalyType.ACCOUNT_ENUMERATION in result.anomaly_types
        assert result.details["account_enumeration"]["user_not_found_attempts"] >= 10
    
    @pytest.mark.asyncio
    async def test_combined_anomalies_risk_scoring(self, detector):
        """Test risk scoring when multiple anomalies are detected"""
        ip = "10.1.0.60"
        email = "victim@test.com"
        user_agent = "MaliciousBot/1.0"
        
        # Create conditions for multiple anomalies
        
        # 1. Rapid failed attempts
        for i in range(6):
            await detector.analyze_attempt(
                ip_address=ip,
                user_agent=user_agent,
                email=email,
                success=False,
                failure_reason="invalid_credentials",
            )
        
        # 2. Multiple IPs for same user (simulate)
        await detector.analyze_attempt(
            ip_address="10.1.0.61",  # Different IP
            user_agent=user_agent,
            email=email,
            success=False,
            failure_reason="invalid_credentials",
        )
        
        # 3. Unusual location
        unusual_location = {"country": "XX", "city": "Unknown"}
        result = await detector.analyze_attempt(
            ip_address=ip,
            user_agent=user_agent,
            email=email,
            success=False,
            failure_reason="invalid_credentials",
            geolocation=unusual_location,
        )
        
        # Should detect multiple anomalies with high risk score
        assert result.is_suspicious
        assert len(result.anomaly_types) >= 2  # Multiple anomalies
        assert result.risk_score > 0.7  # High risk due to multiple factors
        assert result.confidence > 0.6  # High confidence
    
    @pytest.mark.asyncio
    async def test_anomaly_detection_with_successful_attempts(self, detector):
        """Test that successful attempts don't trigger false positives"""
        ip = "10.1.0.70"
        email = "legitimate@test.com"
        user_agent = "LegitBrowser/1.0"
        
        # Many successful attempts should not be suspicious
        for i in range(20):
            result = await detector.analyze_attempt(
                ip_address=ip,
                user_agent=user_agent,
                email=email,
                success=True,
            )
        
        # Should not be suspicious
        assert not result.is_suspicious
        assert len(result.anomaly_types) == 0
        assert result.risk_score < 0.3


class TestRateLimitingAndAnomalyIntegration:
    """Test integration between rate limiting and anomaly detection"""
    
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        config = MagicMock()
        config.security = MagicMock()
        config.security.enable_rate_limiting = True
        config.security.enable_anomaly_detection = True
        return config
    
    @pytest.mark.asyncio
    async def test_rate_limiting_prevents_anomaly_buildup(self, config):
        """Test that rate limiting prevents anomaly detection buildup"""
        from ai_karen_engine.auth.security_monitor import EnhancedSecurityMonitor
        
        monitor = EnhancedSecurityMonitor(config)
        
        ip = "10.2.0.1"
        email = "test@integration.com"
        user_agent = "TestClient/1.0"
        
        # Attempt to make many requests
        attempts = 0
        rate_limited = False
        anomaly_detected = False
        
        for i in range(20):
            try:
                await monitor.check_authentication_security(
                    ip_address=ip,
                    user_agent=user_agent,
                    email=email,
                    endpoint="login",
                )
                
                await monitor.record_authentication_result(
                    ip_address=ip,
                    user_agent=user_agent,
                    success=False,
                    email=email,
                    failure_reason="invalid_credentials",
                )
                
                attempts += 1
                
            except RateLimitExceededError:
                rate_limited = True
                break
            except Exception:  # AnomalyDetectedError or others
                anomaly_detected = True
                break
        
        # Either rate limiting or anomaly detection should have kicked in
        assert rate_limited or anomaly_detected
        assert attempts < 20  # Should not have completed all attempts
    
    @pytest.mark.asyncio
    async def test_security_stats_integration(self, config):
        """Test that security statistics integrate properly"""
        from ai_karen_engine.auth.security_monitor import EnhancedSecurityMonitor
        
        monitor = EnhancedSecurityMonitor(config)
        
        # Generate some activity
        ip = "10.2.0.2"
        email = "stats@integration.com"
        user_agent = "StatsClient/1.0"
        
        for i in range(5):
            try:
                await monitor.record_authentication_result(
                    ip_address=ip,
                    user_agent=user_agent,
                    success=False,
                    email=email,
                    failure_reason="invalid_credentials",
                )
            except Exception:
                pass
        
        # Get stats
        stats = monitor.get_security_stats()
        
        # Verify structure
        assert "alerts" in stats
        assert "rate_limiting" in stats
        assert "anomaly_detection" in stats
        
        assert isinstance(stats["alerts"]["total_alerts"], int)
        assert isinstance(stats["rate_limiting"]["enabled"], bool)
        assert isinstance(stats["anomaly_detection"]["enabled"], bool)
        
        # Should have some monitored activity
        assert stats["anomaly_detection"]["monitored_ips"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])