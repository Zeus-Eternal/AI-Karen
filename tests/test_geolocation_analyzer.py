"""
Tests for geolocation analyzer.
"""

import asyncio
import json
import pytest
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.ai_karen_engine.security.geolocation_analyzer import (
    GeoLocationAnalyzer,
    GeoIPService,
    VPNTorDetector,
    LocationAnalysisResult,
    LocationRiskLevel,
    ConnectionType,
    UserLocationProfile
)
from src.ai_karen_engine.security.models import AuthContext, GeoLocation


class TestGeoIPService:
    """Test GeoIPService class."""
    
    @pytest.mark.asyncio
    async def test_get_location_with_mock(self):
        """Test getting location with mocked response."""
        config = {}
        
        mock_location = GeoLocation(
            country="United States",
            region="California",
            city="San Francisco",
            latitude=37.7749,
            longitude=-122.4194,
            timezone="America/Los_Angeles"
        )
        
        service = GeoIPService(config)
        
        # Mock the internal method
        with patch.object(service, '_get_location_ipapi', return_value=mock_location):
            async with service:
                result = await service.get_location("8.8.8.8")
                
                assert result is not None
                assert result.country == "United States"
                assert result.city == "San Francisco"
                assert result.latitude == 37.7749
    
    @pytest.mark.asyncio
    async def test_get_location_cache(self):
        """Test location caching."""
        config = {}
        service = GeoIPService(config)
        
        mock_location = GeoLocation(
            country="Test Country",
            region="Test Region",
            city="Test City",
            latitude=0.0,
            longitude=0.0,
            timezone="UTC"
        )
        
        with patch.object(service, '_get_location_ipapi', return_value=mock_location) as mock_method:
            async with service:
                # First call should hit the API
                result1 = await service.get_location("1.1.1.1")
                assert result1 == mock_location
                assert mock_method.call_count == 1
                
                # Second call should use cache
                result2 = await service.get_location("1.1.1.1")
                assert result2 == mock_location
                assert mock_method.call_count == 1  # No additional calls


class TestVPNTorDetector:
    """Test VPNTorDetector class."""
    
    @pytest.mark.asyncio
    async def test_analyze_connection_tor(self):
        """Test Tor detection."""
        config = {}
        detector = VPNTorDetector(config)
        
        # Add a test Tor exit node
        detector.tor_exit_nodes.add("192.168.1.100")
        
        async with detector:
            result = await detector.analyze_connection("192.168.1.100")
            
            assert result['is_tor'] is True
            assert result['connection_type'] == ConnectionType.TOR
            assert result['confidence'] == 0.95
            assert 'static_tor_list' in result['sources']
    
    @pytest.mark.asyncio
    async def test_analyze_connection_vpn_range(self):
        """Test VPN range detection."""
        config = {}
        detector = VPNTorDetector(config)
        
        # Add a test VPN range
        from ipaddress import ip_network
        detector.vpn_ranges.append(ip_network("10.0.0.0/8"))
        
        async with detector:
            result = await detector.analyze_connection("10.0.0.1")
            
            assert result['is_vpn'] is True
            assert result['connection_type'] == ConnectionType.VPN
            assert result['confidence'] >= 0.8
            assert 'static_vpn_ranges' in result['sources']
    
    @pytest.mark.asyncio
    async def test_analyze_connection_clean(self):
        """Test clean IP detection."""
        config = {}
        detector = VPNTorDetector(config)
        
        async with detector:
            result = await detector.analyze_connection("8.8.8.8")
            
            assert result['is_tor'] is False
            assert result['is_vpn'] is False
            assert result['is_proxy'] is False
            assert result['connection_type'] == ConnectionType.UNKNOWN


class TestUserLocationProfile:
    """Test UserLocationProfile class."""
    
    def test_profile_serialization(self):
        """Test profile serialization and deserialization."""
        profile = UserLocationProfile(user_id="test_user")
        
        # Add some data
        location = GeoLocation(
            country="US",
            region="CA",
            city="SF",
            latitude=37.7749,
            longitude=-122.4194,
            timezone="America/Los_Angeles"
        )
        
        profile.usual_locations.append(location)
        profile.usual_countries.add("US")
        profile.usual_timezones.add("America/Los_Angeles")
        profile.last_known_location = location
        profile.last_login_time = datetime.utcnow()
        
        # Test serialization
        data = profile.to_dict()
        assert data['user_id'] == "test_user"
        assert len(data['usual_locations']) == 1
        assert "US" in data['usual_countries']
        
        # Test deserialization
        restored = UserLocationProfile.from_dict(data)
        assert restored.user_id == profile.user_id
        assert len(restored.usual_locations) == 1
        assert restored.usual_locations[0].country == "US"
        assert "US" in restored.usual_countries


class TestGeoLocationAnalyzer:
    """Test GeoLocationAnalyzer class."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        config = {
            'high_risk_countries': ['CN', 'RU'],
            'persistence_file': 'test_profiles.json'
        }
        
        analyzer = GeoLocationAnalyzer(config)
        
        assert analyzer.config == config
        assert 'CN' in analyzer.high_risk_countries
        assert 'RU' in analyzer.high_risk_countries
    
    @pytest.mark.asyncio
    async def test_analyze_location_new_user(self):
        """Test location analysis for new user."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        config = {
            'persistence_file': temp_file,
            'high_risk_countries': ['CN']
        }
        
        analyzer = GeoLocationAnalyzer(config)
        
        # Mock the services
        mock_location = GeoLocation(
            country="United States",
            region="California",
            city="San Francisco",
            latitude=37.7749,
            longitude=-122.4194,
            timezone="America/Los_Angeles"
        )
        
        mock_connection = {
            'is_tor': False,
            'is_vpn': False,
            'is_proxy': False,
            'connection_type': ConnectionType.RESIDENTIAL,
            'confidence': 0.9,
            'sources': ['test']
        }
        
        with patch.object(analyzer.geoip_service, 'get_location', return_value=mock_location), \
             patch.object(analyzer.vpn_detector, 'analyze_connection', return_value=mock_connection):
            
            context = AuthContext(
                email="test@example.com",
                password_hash="hashed",
                client_ip="8.8.8.8",
                user_agent="Mozilla/5.0",
                timestamp=datetime.utcnow(),
                request_id="test_123"
            )
            
            result = await analyzer.analyze_location(context)
            
            assert isinstance(result, LocationAnalysisResult)
            assert result.geolocation.country == "United States"
            assert result.connection_type == ConnectionType.RESIDENTIAL
            assert result.is_vpn is False
            assert result.is_tor is False
            assert result.high_risk_country is False
            assert result.is_usual_location is False  # New user, no usual locations yet
    
    @pytest.mark.asyncio
    async def test_analyze_location_high_risk_country(self):
        """Test location analysis for high-risk country."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        config = {
            'persistence_file': temp_file,
            'high_risk_countries': ['CN']
        }
        
        analyzer = GeoLocationAnalyzer(config)
        
        # Mock location in high-risk country
        mock_location = GeoLocation(
            country="CN",
            region="Beijing",
            city="Beijing",
            latitude=39.9042,
            longitude=116.4074,
            timezone="Asia/Shanghai"
        )
        
        mock_connection = {
            'is_tor': False,
            'is_vpn': False,
            'is_proxy': False,
            'connection_type': ConnectionType.RESIDENTIAL,
            'confidence': 0.9,
            'sources': ['test']
        }
        
        with patch.object(analyzer.geoip_service, 'get_location', return_value=mock_location), \
             patch.object(analyzer.vpn_detector, 'analyze_connection', return_value=mock_connection):
            
            context = AuthContext(
                email="test@example.com",
                password_hash="hashed",
                client_ip="1.2.3.4",
                user_agent="Mozilla/5.0",
                timestamp=datetime.utcnow(),
                request_id="test_123"
            )
            
            result = await analyzer.analyze_location(context)
            
            assert result.high_risk_country is True
            assert result.risk_score > 0.2  # Should have elevated risk due to country
    
    @pytest.mark.asyncio
    async def test_analyze_location_vpn_detection(self):
        """Test location analysis with VPN detection."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        config = {'persistence_file': temp_file}
        analyzer = GeoLocationAnalyzer(config)
        
        mock_location = GeoLocation(
            country="United States",
            region="California",
            city="San Francisco",
            latitude=37.7749,
            longitude=-122.4194,
            timezone="America/Los_Angeles"
        )
        
        mock_connection = {
            'is_tor': False,
            'is_vpn': True,
            'is_proxy': False,
            'connection_type': ConnectionType.VPN,
            'confidence': 0.9,
            'sources': ['test']
        }
        
        with patch.object(analyzer.geoip_service, 'get_location', return_value=mock_location), \
             patch.object(analyzer.vpn_detector, 'analyze_connection', return_value=mock_connection):
            
            context = AuthContext(
                email="test@example.com",
                password_hash="hashed",
                client_ip="1.2.3.4",
                user_agent="Mozilla/5.0",
                timestamp=datetime.utcnow(),
                request_id="test_123"
            )
            
            result = await analyzer.analyze_location(context)
            
            assert result.is_vpn is True
            assert result.connection_type == ConnectionType.VPN
            assert result.risk_score > 0.4  # Should have elevated risk due to VPN
    
    def test_distance_calculation(self):
        """Test distance calculation between locations."""
        config = {}
        analyzer = GeoLocationAnalyzer(config)
        
        # San Francisco and Los Angeles
        sf = GeoLocation(
            country="US", region="CA", city="SF",
            latitude=37.7749, longitude=-122.4194, timezone="America/Los_Angeles"
        )
        
        la = GeoLocation(
            country="US", region="CA", city="LA",
            latitude=34.0522, longitude=-118.2437, timezone="America/Los_Angeles"
        )
        
        distance = analyzer._calculate_distance(sf, la)
        
        # Distance between SF and LA is approximately 560 km
        assert 500 < distance < 600
    
    def test_velocity_anomaly_detection(self):
        """Test velocity anomaly detection."""
        config = {}
        analyzer = GeoLocationAnalyzer(config)
        
        # Create user profile with last known location
        profile = UserLocationProfile(user_id="test_user")
        
        # Last location: San Francisco
        profile.last_known_location = GeoLocation(
            country="US", region="CA", city="SF",
            latitude=37.7749, longitude=-122.4194, timezone="America/Los_Angeles"
        )
        profile.last_login_time = datetime.utcnow() - timedelta(hours=1)  # 1 hour ago
        
        # Current location: New York (impossible to travel in 1 hour)
        current_location = GeoLocation(
            country="US", region="NY", city="NYC",
            latitude=40.7128, longitude=-74.0060, timezone="America/New_York"
        )
        
        velocity = analyzer._calculate_velocity_anomaly(
            current_location,
            profile,
            datetime.utcnow()
        )
        
        # Should detect impossible travel (> 800 km/h)
        assert velocity is not None
        assert velocity > 800
    
    def test_usual_location_detection(self):
        """Test usual location detection."""
        config = {}
        analyzer = GeoLocationAnalyzer(config)
        
        # Create user profile with usual locations
        profile = UserLocationProfile(user_id="test_user")
        
        # Add San Francisco as usual location
        sf_location = GeoLocation(
            country="US", region="CA", city="SF",
            latitude=37.7749, longitude=-122.4194, timezone="America/Los_Angeles"
        )
        profile.usual_locations.append(sf_location)
        profile.usual_countries.add("US")
        
        # Test location close to SF (should be usual)
        nearby_location = GeoLocation(
            country="US", region="CA", city="Oakland",
            latitude=37.8044, longitude=-122.2711, timezone="America/Los_Angeles"
        )
        
        is_usual = analyzer._is_usual_location(nearby_location, profile)
        assert is_usual is True
        
        # Test location far from SF (should not be usual)
        far_location = GeoLocation(
            country="US", region="NY", city="NYC",
            latitude=40.7128, longitude=-74.0060, timezone="America/New_York"
        )
        
        is_usual = analyzer._is_usual_location(far_location, profile)
        assert is_usual is True  # Same country, so still usual
        
        # Test location in different country (should not be usual)
        foreign_location = GeoLocation(
            country="CN", region="Beijing", city="Beijing",
            latitude=39.9042, longitude=116.4074, timezone="Asia/Shanghai"
        )
        
        is_usual = analyzer._is_usual_location(foreign_location, profile)
        assert is_usual is False
    
    def test_user_profile_update(self):
        """Test user profile update with new location."""
        config = {}
        analyzer = GeoLocationAnalyzer(config)
        
        profile = UserLocationProfile(user_id="test_user")
        
        location = GeoLocation(
            country="US", region="CA", city="SF",
            latitude=37.7749, longitude=-122.4194, timezone="America/Los_Angeles"
        )
        
        timestamp = datetime.utcnow()
        
        analyzer._update_user_profile(profile, location, timestamp)
        
        # Check that profile was updated
        assert len(profile.location_history) == 1
        assert "US" in profile.usual_countries
        assert "America/Los_Angeles" in profile.usual_timezones
        assert len(profile.usual_locations) == 1
        assert profile.last_known_location == location
        assert profile.last_login_time == timestamp
    
    def test_get_user_location_statistics(self):
        """Test getting user location statistics."""
        config = {}
        analyzer = GeoLocationAnalyzer(config)
        
        # Create a user profile with some data
        profile = UserLocationProfile(user_id="test_user")
        profile.usual_countries.add("US")
        profile.usual_countries.add("CA")
        profile.usual_timezones.add("America/Los_Angeles")
        profile.max_velocity_observed = 500.0
        
        analyzer.user_profiles["test_user"] = profile
        
        stats = analyzer.get_user_location_statistics("test_user")
        
        assert stats['user_id'] == "test_user"
        assert "US" in stats['usual_countries']
        assert "CA" in stats['usual_countries']
        assert stats['max_velocity_observed'] == 500.0
        
        # Test non-existent user
        stats = analyzer.get_user_location_statistics("non_existent")
        assert 'error' in stats


if __name__ == "__main__":
    pytest.main([__file__])