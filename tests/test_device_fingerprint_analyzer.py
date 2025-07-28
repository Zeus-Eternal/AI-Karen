"""
Tests for device fingerprint analyzer.
"""

import json
import pytest
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch

from src.ai_karen_engine.security.device_fingerprint_analyzer import (
    DeviceFingerprintAnalyzer,
    UserAgentAnalyzer,
    DeviceFingerprint,
    DeviceAnalysisResult,
    DeviceType,
    DeviceRiskLevel,
    UserDeviceProfile
)


class TestUserAgentAnalyzer:
    """Test UserAgentAnalyzer class."""
    
    def test_analyze_normal_user_agent(self):
        """Test analysis of normal user agent."""
        analyzer = UserAgentAnalyzer()
        
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        result = analyzer.analyze_user_agent(user_agent)
        
        assert result['is_suspicious'] is False
        assert len(result['anomalies']) == 0
        assert result['risk_score'] == 0.0
        assert result['parsed_info']['browser_family'] == 'Chrome'
        assert result['parsed_info']['os_family'] == 'Windows'
    
    def test_analyze_suspicious_user_agent(self):
        """Test analysis of suspicious user agent."""
        analyzer = UserAgentAnalyzer()
        
        user_agent = "sqlmap/1.0"
        
        result = analyzer.analyze_user_agent(user_agent)
        
        assert result['is_suspicious'] is True
        assert len(result['anomalies']) > 0
        assert result['risk_score'] > 0.0
        assert any('suspicious pattern' in anomaly for anomaly in result['anomalies'])
    
    def test_analyze_empty_user_agent(self):
        """Test analysis of empty user agent."""
        analyzer = UserAgentAnalyzer()
        
        result = analyzer.analyze_user_agent("")
        
        assert len(result['anomalies']) > 0
        assert result['risk_score'] > 0.0
        assert any('empty or too short' in anomaly for anomaly in result['anomalies'])
    
    def test_analyze_long_user_agent(self):
        """Test analysis of unusually long user agent."""
        analyzer = UserAgentAnalyzer()
        
        user_agent = "A" * 1500  # Very long user agent
        
        result = analyzer.analyze_user_agent(user_agent)
        
        assert len(result['anomalies']) > 0
        assert result['risk_score'] > 0.0
        assert any('unusually long' in anomaly for anomaly in result['anomalies'])
    
    def test_analyze_bot_user_agent(self):
        """Test analysis of bot user agent."""
        analyzer = UserAgentAnalyzer()
        
        user_agent = "Googlebot/2.1 (+http://www.google.com/bot.html)"
        
        result = analyzer.analyze_user_agent(user_agent)
        
        assert result['parsed_info']['is_bot'] is True
        # Bots might be flagged as suspicious depending on the pattern
    
    def test_analyze_mobile_user_agent(self):
        """Test analysis of mobile user agent."""
        analyzer = UserAgentAnalyzer()
        
        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        
        result = analyzer.analyze_user_agent(user_agent)
        
        assert result['parsed_info']['is_mobile'] is True
        assert result['parsed_info']['os_family'] == 'iOS'
        assert result['is_suspicious'] is False


class TestDeviceFingerprint:
    """Test DeviceFingerprint class."""
    
    def test_fingerprint_serialization(self):
        """Test fingerprint serialization and deserialization."""
        fingerprint = DeviceFingerprint(
            fingerprint_id="test123",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            browser_family="Chrome",
            browser_version="91.0.4472.124",
            os_family="Windows",
            os_version="10",
            device_family="Other",
            device_type=DeviceType.DESKTOP,
            is_mobile=False,
            is_tablet=False,
            is_bot=False,
            screen_resolution="1920x1080",
            timezone="America/Los_Angeles",
            language="en-US",
            plugins=["Flash", "Java"]
        )
        
        # Test serialization
        data = fingerprint.to_dict()
        assert data['fingerprint_id'] == "test123"
        assert data['device_type'] == "desktop"
        assert data['screen_resolution'] == "1920x1080"
        assert "Flash" in data['plugins']
        
        # Test deserialization
        restored = DeviceFingerprint.from_dict(data)
        assert restored.fingerprint_id == fingerprint.fingerprint_id
        assert restored.device_type == fingerprint.device_type
        assert restored.screen_resolution == fingerprint.screen_resolution
        assert restored.plugins == fingerprint.plugins


class TestUserDeviceProfile:
    """Test UserDeviceProfile class."""
    
    def test_profile_serialization(self):
        """Test profile serialization and deserialization."""
        profile = UserDeviceProfile(user_id="test_user")
        
        # Add a device
        device = DeviceFingerprint(
            fingerprint_id="device123",
            user_agent="Mozilla/5.0",
            browser_family="Chrome",
            browser_version="91.0",
            os_family="Windows",
            os_version="10",
            device_family="Other",
            device_type=DeviceType.DESKTOP,
            is_mobile=False,
            is_tablet=False,
            is_bot=False
        )
        
        profile.known_devices["device123"] = device
        profile.primary_device = "device123"
        profile.device_usage_patterns["device123"] = 5
        profile.suspicious_devices.add("suspicious123")
        
        # Test serialization
        data = profile.to_dict()
        assert data['user_id'] == "test_user"
        assert "device123" in data['known_devices']
        assert data['primary_device'] == "device123"
        assert "suspicious123" in data['suspicious_devices']
        
        # Test deserialization
        restored = UserDeviceProfile.from_dict(data)
        assert restored.user_id == profile.user_id
        assert "device123" in restored.known_devices
        assert restored.primary_device == profile.primary_device
        assert "suspicious123" in restored.suspicious_devices


class TestDeviceFingerprintAnalyzer:
    """Test DeviceFingerprintAnalyzer class."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        config = {'persistence_file': temp_file}
        analyzer = DeviceFingerprintAnalyzer(config)
        
        assert analyzer.config == config
        assert analyzer.persistence_file == temp_file
        assert isinstance(analyzer.ua_analyzer, UserAgentAnalyzer)
    
    def test_generate_device_fingerprint(self):
        """Test device fingerprint generation."""
        config = {}
        analyzer = DeviceFingerprintAnalyzer(config)
        
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        additional_info = {
            'screen_resolution': '1920x1080',
            'timezone': 'America/Los_Angeles',
            'language': 'en-US',
            'plugins': ['Flash', 'Java']
        }
        
        fingerprint = analyzer.generate_device_fingerprint(user_agent, additional_info)
        
        assert fingerprint.user_agent == user_agent
        assert fingerprint.browser_family == 'Chrome'
        assert fingerprint.os_family == 'Windows'
        assert fingerprint.device_type == DeviceType.DESKTOP
        assert fingerprint.screen_resolution == '1920x1080'
        assert fingerprint.timezone == 'America/Los_Angeles'
        assert fingerprint.language == 'en-US'
        assert 'Flash' in fingerprint.plugins
        assert len(fingerprint.fingerprint_id) == 16  # SHA256 truncated to 16 chars
    
    def test_generate_mobile_fingerprint(self):
        """Test mobile device fingerprint generation."""
        config = {}
        analyzer = DeviceFingerprintAnalyzer(config)
        
        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        
        fingerprint = analyzer.generate_device_fingerprint(user_agent)
        
        assert fingerprint.device_type == DeviceType.MOBILE
        assert fingerprint.is_mobile is True
        assert fingerprint.os_family == 'iOS'
        assert fingerprint.browser_family == 'Mobile Safari'
    
    def test_generate_bot_fingerprint(self):
        """Test bot device fingerprint generation."""
        config = {}
        analyzer = DeviceFingerprintAnalyzer(config)
        
        user_agent = "Googlebot/2.1 (+http://www.google.com/bot.html)"
        
        fingerprint = analyzer.generate_device_fingerprint(user_agent)
        
        assert fingerprint.device_type == DeviceType.BOT
        assert fingerprint.is_bot is True
    
    def test_analyze_device_new_user(self):
        """Test device analysis for new user."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        config = {'persistence_file': temp_file}
        analyzer = DeviceFingerprintAnalyzer(config)
        
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        result = analyzer.analyze_device("new_user", user_agent)
        
        assert isinstance(result, DeviceAnalysisResult)
        assert result.is_known_device is False
        assert result.new_device_for_user is True
        assert result.device_similarity_score == 0.0  # No previous devices to compare
        assert result.is_suspicious_user_agent is False
        assert result.device_fingerprint.browser_family == 'Chrome'
    
    def test_analyze_device_known_user(self):
        """Test device analysis for known user with existing device."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        config = {'persistence_file': temp_file}
        analyzer = DeviceFingerprintAnalyzer(config)
        
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        # First analysis - creates the device
        result1 = analyzer.analyze_device("known_user", user_agent)
        assert result1.is_known_device is False
        assert result1.new_device_for_user is True
        
        # Second analysis - should recognize the device
        result2 = analyzer.analyze_device("known_user", user_agent)
        assert result2.is_known_device is True
        assert result2.new_device_for_user is False
        assert result2.device_similarity_score == 1.0  # Exact match
    
    def test_analyze_device_suspicious_user_agent(self):
        """Test device analysis with suspicious user agent."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        config = {'persistence_file': temp_file}
        analyzer = DeviceFingerprintAnalyzer(config)
        
        user_agent = "sqlmap/1.0"
        
        result = analyzer.analyze_device("test_user", user_agent)
        
        assert result.is_suspicious_user_agent is True
        assert len(result.user_agent_anomalies) > 0
        assert result.risk_score > 0.4  # Should have high risk due to suspicious UA
        assert result.risk_level in [DeviceRiskLevel.HIGH, DeviceRiskLevel.VERY_HIGH]
    
    def test_calculate_fingerprint_similarity(self):
        """Test fingerprint similarity calculation."""
        config = {}
        analyzer = DeviceFingerprintAnalyzer(config)
        
        # Create two similar devices (same browser, OS, device type)
        device1 = DeviceFingerprint(
            fingerprint_id="device1",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0",
            browser_family="Chrome",
            browser_version="91.0",
            os_family="Windows",
            os_version="10",
            device_family="Other",
            device_type=DeviceType.DESKTOP,
            is_mobile=False,
            is_tablet=False,
            is_bot=False
        )
        
        device2 = DeviceFingerprint(
            fingerprint_id="device2",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/92.0",
            browser_family="Chrome",
            browser_version="92.0",  # Different version
            os_family="Windows",
            os_version="10",
            device_family="Other",
            device_type=DeviceType.DESKTOP,
            is_mobile=False,
            is_tablet=False,
            is_bot=False
        )
        
        similarity = analyzer._calculate_fingerprint_similarity(device1, device2)
        
        # Should be high similarity (browser family, OS, device type match)
        assert similarity >= 0.7  # 0.3 + 0.25 + 0.15 = 0.7 minimum
    
    def test_calculate_fingerprint_similarity_different(self):
        """Test fingerprint similarity calculation for different devices."""
        config = {}
        analyzer = DeviceFingerprintAnalyzer(config)
        
        # Create two very different devices
        device1 = DeviceFingerprint(
            fingerprint_id="device1",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0",
            browser_family="Chrome",
            browser_version="91.0",
            os_family="Windows",
            os_version="10",
            device_family="Other",
            device_type=DeviceType.DESKTOP,
            is_mobile=False,
            is_tablet=False,
            is_bot=False
        )
        
        device2 = DeviceFingerprint(
            fingerprint_id="device2",
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_6) Safari/604.1",
            browser_family="Mobile Safari",
            browser_version="14.0",
            os_family="iOS",
            os_version="14.6",
            device_family="iPhone",
            device_type=DeviceType.MOBILE,
            is_mobile=True,
            is_tablet=False,
            is_bot=False
        )
        
        similarity = analyzer._calculate_fingerprint_similarity(device1, device2)
        
        # Should be low similarity (different browser, OS, device type)
        # Note: might have small similarity due to matching null fields
        assert similarity <= 0.1
    
    def test_device_change_detection(self):
        """Test device change detection."""
        config = {}
        analyzer = DeviceFingerprintAnalyzer(config)
        
        profile = UserDeviceProfile(user_id="test_user")
        profile.last_device_used = "device1"
        
        device = DeviceFingerprint(
            fingerprint_id="device2",
            user_agent="Mozilla/5.0",
            browser_family="Chrome",
            browser_version="91.0",
            os_family="Windows",
            os_version="10",
            device_family="Other",
            device_type=DeviceType.DESKTOP,
            is_mobile=False,
            is_tablet=False,
            is_bot=False
        )
        
        change_detected = analyzer._detect_device_change(device, profile)
        assert change_detected is True
        
        # Test no change
        device.fingerprint_id = "device1"
        change_detected = analyzer._detect_device_change(device, profile)
        assert change_detected is False
    
    def test_mark_device_suspicious(self):
        """Test marking device as suspicious."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        config = {'persistence_file': temp_file}
        analyzer = DeviceFingerprintAnalyzer(config)
        
        analyzer.mark_device_suspicious("test_user", "suspicious_device_123")
        
        profile = analyzer._get_user_profile("test_user")
        assert "suspicious_device_123" in profile.suspicious_devices
    
    def test_get_user_device_statistics(self):
        """Test getting user device statistics."""
        config = {}
        analyzer = DeviceFingerprintAnalyzer(config)
        
        # Create a user profile with some devices
        profile = UserDeviceProfile(user_id="test_user")
        
        device1 = DeviceFingerprint(
            fingerprint_id="device1",
            user_agent="Mozilla/5.0",
            browser_family="Chrome",
            browser_version="91.0",
            os_family="Windows",
            os_version="10",
            device_family="Other",
            device_type=DeviceType.DESKTOP,
            is_mobile=False,
            is_tablet=False,
            is_bot=False
        )
        
        device2 = DeviceFingerprint(
            fingerprint_id="device2",
            user_agent="Mozilla/5.0",
            browser_family="Safari",
            browser_version="14.0",
            os_family="iOS",
            os_version="14.6",
            device_family="iPhone",
            device_type=DeviceType.MOBILE,
            is_mobile=True,
            is_tablet=False,
            is_bot=False
        )
        
        profile.known_devices["device1"] = device1
        profile.known_devices["device2"] = device2
        profile.device_usage_patterns["device1"] = 10
        profile.device_usage_patterns["device2"] = 5
        profile.primary_device = "device1"
        profile.suspicious_devices.add("device2")
        
        analyzer.user_profiles["test_user"] = profile
        
        stats = analyzer.get_user_device_statistics("test_user")
        
        assert stats['user_id'] == "test_user"
        assert stats['total_devices'] == 2
        assert stats['primary_device'] == "device1"
        assert stats['suspicious_devices_count'] == 1
        assert 'desktop' in stats['device_types']
        assert 'mobile' in stats['device_types']
        assert 'Chrome' in stats['browsers']
        assert 'Safari' in stats['browsers']
        assert 'Windows' in stats['operating_systems']
        assert 'iOS' in stats['operating_systems']
        
        # Check most used devices
        most_used = stats['most_used_devices']
        assert len(most_used) == 2
        assert most_used[0][0] == "device1"  # Most used
        assert most_used[0][1] == 10
        
        # Test non-existent user
        stats = analyzer.get_user_device_statistics("non_existent")
        assert 'error' in stats
    
    def test_get_global_device_statistics(self):
        """Test getting global device statistics."""
        config = {}
        analyzer = DeviceFingerprintAnalyzer(config)
        
        # Add some devices to the database
        device1 = DeviceFingerprint(
            fingerprint_id="device1",
            user_agent="Mozilla/5.0",
            browser_family="Chrome",
            browser_version="91.0",
            os_family="Windows",
            os_version="10",
            device_family="Other",
            device_type=DeviceType.DESKTOP,
            is_mobile=False,
            is_tablet=False,
            is_bot=False
        )
        
        device2 = DeviceFingerprint(
            fingerprint_id="device2",
            user_agent="Mozilla/5.0",
            browser_family="Safari",
            browser_version="14.0",
            os_family="iOS",
            os_version="14.6",
            device_family="iPhone",
            device_type=DeviceType.MOBILE,
            is_mobile=True,
            is_tablet=False,
            is_bot=False
        )
        
        analyzer.device_database["device1"] = device1
        analyzer.device_database["device2"] = device2
        
        # Add a user profile
        profile = UserDeviceProfile(user_id="test_user")
        analyzer.user_profiles["test_user"] = profile
        
        stats = analyzer.get_global_device_statistics()
        
        assert stats['total_devices'] == 2
        assert stats['total_users'] == 1
        assert 'desktop' in stats['device_types']
        assert 'mobile' in stats['device_types']
        assert len(stats['top_browsers']) > 0
        assert len(stats['top_operating_systems']) > 0


if __name__ == "__main__":
    pytest.main([__file__])