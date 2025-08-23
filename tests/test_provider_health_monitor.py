"""
Unit tests for the Provider Health Monitor Service
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from ai_karen_engine.services.provider_health_monitor import (
    ProviderHealthMonitor,
    ProviderHealthInfo,
    HealthStatus,
    get_health_monitor,
    record_provider_success,
    record_provider_failure
)


class TestProviderHealthInfo:
    """Test provider health info data structure"""
    
    def test_health_info_creation(self):
        """Test creating provider health info"""
        now = datetime.utcnow()
        health_info = ProviderHealthInfo(
            name="OpenAI",
            status=HealthStatus.HEALTHY,
            last_check=now,
            response_time=0.5,
            consecutive_failures=0,
            success_rate=1.0
        )
        
        assert health_info.name == "OpenAI"
        assert health_info.status == HealthStatus.HEALTHY
        assert health_info.last_check == now
        assert health_info.response_time == 0.5
        assert health_info.consecutive_failures == 0
        assert health_info.success_rate == 1.0


class TestProviderHealthMonitor:
    """Test the provider health monitor service"""
    
    @pytest.fixture
    def monitor(self):
        """Create a fresh provider health monitor"""
        return ProviderHealthMonitor(check_interval=60)
    
    def test_monitor_initialization(self, monitor):
        """Test monitor initialization"""
        assert monitor.check_interval == 60
        assert monitor._cache_ttl == 300
        assert len(monitor._health_cache) == 0
        assert len(monitor._known_providers) > 0
        assert "openai" in monitor._known_providers
        assert "anthropic" in monitor._known_providers
    
    def test_update_provider_health_success(self, monitor):
        """Test updating provider health with success"""
        monitor.update_provider_health(
            provider_name="OpenAI",
            is_healthy=True,
            response_time=0.5
        )
        
        health_info = monitor.get_provider_health("OpenAI")
        assert health_info is not None
        assert health_info.name == "OpenAI"
        assert health_info.status == HealthStatus.HEALTHY
        assert health_info.response_time == 0.5
        assert health_info.consecutive_failures == 0
        assert health_info.success_rate == 1.0
        assert health_info.error_message is None
    
    def test_update_provider_health_failure(self, monitor):
        """Test updating provider health with failure"""
        monitor.update_provider_health(
            provider_name="OpenAI",
            is_healthy=False,
            error_message="API key invalid"
        )
        
        health_info = monitor.get_provider_health("OpenAI")
        assert health_info is not None
        assert health_info.status == HealthStatus.HEALTHY  # First failure still healthy
        assert health_info.consecutive_failures == 1
        assert health_info.error_message == "API key invalid"
        assert health_info.last_failure is not None
    
    def test_consecutive_failures_degraded(self, monitor):
        """Test that consecutive failures lead to degraded status"""
        # Record multiple failures
        for i in range(3):
            monitor.update_provider_health(
                provider_name="OpenAI",
                is_healthy=False,
                error_message=f"Error {i+1}"
            )
        
        health_info = monitor.get_provider_health("OpenAI")
        assert health_info.status == HealthStatus.DEGRADED
        assert health_info.consecutive_failures == 3
    
    def test_consecutive_failures_unhealthy(self, monitor):
        """Test that many consecutive failures lead to unhealthy status"""
        # Record many failures
        for i in range(6):
            monitor.update_provider_health(
                provider_name="OpenAI",
                is_healthy=False,
                error_message=f"Error {i+1}"
            )
        
        health_info = monitor.get_provider_health("OpenAI")
        assert health_info.status == HealthStatus.UNHEALTHY
        assert health_info.consecutive_failures == 6
    
    def test_recovery_after_failure(self, monitor):
        """Test recovery after failures"""
        # Record failures first
        for i in range(3):
            monitor.update_provider_health(
                provider_name="OpenAI",
                is_healthy=False,
                error_message=f"Error {i+1}"
            )
        
        # Then record success
        monitor.update_provider_health(
            provider_name="OpenAI",
            is_healthy=True,
            response_time=0.3
        )
        
        health_info = monitor.get_provider_health("OpenAI")
        assert health_info.status == HealthStatus.HEALTHY
        assert health_info.consecutive_failures == 0
        assert health_info.error_message is None
        assert health_info.last_success is not None
    
    def test_get_provider_health_unknown(self, monitor):
        """Test getting health for unknown provider"""
        health_info = monitor.get_provider_health("UnknownProvider")
        assert health_info is not None
        assert health_info.name == "UnknownProvider"
        assert health_info.status == HealthStatus.UNKNOWN
    
    def test_get_provider_health_case_insensitive(self, monitor):
        """Test that provider names are case insensitive"""
        monitor.update_provider_health(
            provider_name="OpenAI",
            is_healthy=True
        )
        
        # Should work with different cases
        health_info1 = monitor.get_provider_health("openai")
        health_info2 = monitor.get_provider_health("OPENAI")
        health_info3 = monitor.get_provider_health("OpenAI")
        
        assert health_info1.name == "OpenAI"
        assert health_info2.name == "OpenAI"
        assert health_info3.name == "OpenAI"
    
    def test_get_all_provider_health(self, monitor):
        """Test getting health for all providers"""
        # Update health for a few providers
        monitor.update_provider_health("OpenAI", True, response_time=0.5)
        monitor.update_provider_health("Anthropic", False, error_message="Rate limited")
        
        all_health = monitor.get_all_provider_health()
        
        assert len(all_health) >= 2
        assert "openai" in all_health
        assert "anthropic" in all_health
        assert all_health["openai"].status == HealthStatus.HEALTHY
        assert all_health["anthropic"].status == HealthStatus.HEALTHY  # First failure
    
    def test_get_healthy_providers(self, monitor):
        """Test getting list of healthy providers"""
        # Set up different health states
        monitor.update_provider_health("OpenAI", True)
        monitor.update_provider_health("Anthropic", True)
        
        # Make one unhealthy
        for _ in range(6):
            monitor.update_provider_health("Google", False)
        
        healthy_providers = monitor.get_healthy_providers()
        
        assert "openai" in healthy_providers
        assert "anthropic" in healthy_providers
        assert "google" not in healthy_providers
    
    def test_get_alternative_providers(self, monitor):
        """Test getting alternative providers"""
        # Set up health states
        monitor.update_provider_health("OpenAI", True, response_time=0.5)
        monitor.update_provider_health("Anthropic", True, response_time=0.3)
        monitor.update_provider_health("Google", True, response_time=0.7)
        
        # Make OpenAI unhealthy
        for _ in range(6):
            monitor.update_provider_health("OpenAI", False)
        
        alternatives = monitor.get_alternative_providers("OpenAI")
        
        assert "openai" not in [alt.lower() for alt in alternatives]
        assert len(alternatives) > 0
        # Should be sorted by success rate (Anthropic should be first due to better response time)
        assert alternatives[0].lower() == "anthropic"
    
    def test_record_provider_interaction_success(self, monitor):
        """Test recording successful provider interaction"""
        monitor.record_provider_interaction(
            provider_name="OpenAI",
            success=True,
            response_time=0.4
        )
        
        health_info = monitor.get_provider_health("OpenAI")
        assert health_info.status == HealthStatus.HEALTHY
        assert health_info.response_time == 0.4
    
    def test_record_provider_interaction_failure(self, monitor):
        """Test recording failed provider interaction"""
        monitor.record_provider_interaction(
            provider_name="OpenAI",
            success=False,
            error_message="Connection timeout"
        )
        
        health_info = monitor.get_provider_health("OpenAI")
        assert health_info.consecutive_failures == 1
        assert health_info.error_message == "Connection timeout"
    
    def test_get_provider_recommendations(self, monitor):
        """Test getting provider recommendations"""
        # Set up health states
        monitor.update_provider_health("OpenAI", True)
        monitor.update_provider_health("Anthropic", True)
        
        # Make OpenAI unhealthy
        for _ in range(6):
            monitor.update_provider_health("OpenAI", False, error_message="Service down")
        
        error_context = {"provider_name": "OpenAI"}
        recommendations = monitor.get_provider_recommendations(error_context)
        
        assert recommendations["failed_provider"] == "OpenAI"
        assert len(recommendations["alternatives"]) > 0
        assert "anthropic" in [alt.lower() for alt in recommendations["alternatives"]]
        assert len(recommendations["suggestions"]) > 0
        assert "health_summary" in recommendations
    
    def test_clear_cache(self, monitor):
        """Test clearing the health cache"""
        monitor.update_provider_health("OpenAI", True)
        assert len(monitor._health_cache) > 0
        
        monitor.clear_cache()
        assert len(monitor._health_cache) == 0
    
    def test_get_cache_stats(self, monitor):
        """Test getting cache statistics"""
        # Add some health data
        monitor.update_provider_health("OpenAI", True, response_time=0.5)
        monitor.update_provider_health("Anthropic", False)
        
        # Make one degraded
        for _ in range(3):
            monitor.update_provider_health("Google", False)
        
        stats = monitor.get_cache_stats()
        
        assert "total_providers" in stats
        assert "healthy_count" in stats
        assert "degraded_count" in stats
        assert "unhealthy_count" in stats
        assert "unknown_count" in stats
        assert "cache_age_seconds" in stats
        assert "average_response_time" in stats
        
        assert stats["total_providers"] >= 3
        assert stats["healthy_count"] >= 1
        assert stats["degraded_count"] >= 1
    
    def test_success_rate_calculation(self, monitor):
        """Test success rate calculation"""
        provider_name = "TestProvider"
        
        # Record mixed results
        results = [True, True, False, True, False, True, True, True, False, True]
        for success in results:
            monitor.update_provider_health(provider_name, success)
        
        health_info = monitor.get_provider_health(provider_name)
        expected_rate = sum(results) / len(results)  # 7/10 = 0.7
        assert abs(health_info.success_rate - expected_rate) < 0.01
    
    @patch('ai_karen_engine.services.provider_health_monitor.datetime')
    def test_cache_expiry(self, mock_datetime, monitor):
        """Test that cache expires after TTL"""
        # Mock initial time
        initial_time = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = initial_time
        
        # Update provider health
        monitor.update_provider_health("OpenAI", True)
        
        # Mock time after cache expiry
        expired_time = initial_time + timedelta(seconds=400)  # Beyond 300s TTL
        mock_datetime.utcnow.return_value = expired_time
        
        # Should return unknown status due to expired cache
        health_info = monitor.get_provider_health("OpenAI")
        assert health_info.status == HealthStatus.UNKNOWN
        assert health_info.metadata.get("cache_miss") is True


class TestGlobalFunctions:
    """Test global convenience functions"""
    
    def test_get_health_monitor_singleton(self):
        """Test that get_health_monitor returns singleton"""
        monitor1 = get_health_monitor()
        monitor2 = get_health_monitor()
        
        assert monitor1 is monitor2
        assert isinstance(monitor1, ProviderHealthMonitor)
    
    def test_record_provider_success(self):
        """Test convenience function for recording success"""
        record_provider_success("TestProvider", response_time=0.3)
        
        monitor = get_health_monitor()
        health_info = monitor.get_provider_health("TestProvider")
        
        assert health_info.status == HealthStatus.HEALTHY
        assert health_info.response_time == 0.3
    
    def test_record_provider_failure(self):
        """Test convenience function for recording failure"""
        record_provider_failure("TestProvider", "Connection failed")
        
        monitor = get_health_monitor()
        health_info = monitor.get_provider_health("TestProvider")
        
        assert health_info.consecutive_failures == 1
        assert health_info.error_message == "Connection failed"


if __name__ == "__main__":
    pytest.main([__file__])