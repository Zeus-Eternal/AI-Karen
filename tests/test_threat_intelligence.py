"""
Tests for threat intelligence engine.
"""

import asyncio
import json
import pytest
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from aiohttp import ClientSession

from src.ai_karen_engine.security.threat_intelligence import (
    ThreatIntelligenceEngine,
    ThreatIndicator,
    ThreatIndicatorType,
    ReputationLevel,
    ThreatSource,
    IPReputationResult,
    ThreatContext,
    ThreatFeedManager,
    ThreatIndicatorDatabase
)
from src.ai_karen_engine.security.models import AuthContext


class TestThreatIndicator:
    """Test ThreatIndicator class."""
    
    def test_create_threat_indicator(self):
        """Test creating a threat indicator."""
        now = datetime.utcnow()
        indicator = ThreatIndicator(
            value="192.168.1.1",
            indicator_type=ThreatIndicatorType.IP_ADDRESS,
            reputation_level=ReputationLevel.MALICIOUS,
            source=ThreatSource.INTERNAL,
            first_seen=now,
            last_seen=now,
            confidence=0.9,
            tags=["malware", "botnet"],
            description="Known malicious IP"
        )
        
        assert indicator.value == "192.168.1.1"
        assert indicator.indicator_type == ThreatIndicatorType.IP_ADDRESS
        assert indicator.reputation_level == ReputationLevel.MALICIOUS
        assert indicator.confidence == 0.9
        assert "malware" in indicator.tags
    
    def test_indicator_serialization(self):
        """Test indicator serialization and deserialization."""
        now = datetime.utcnow()
        indicator = ThreatIndicator(
            value="malicious.com",
            indicator_type=ThreatIndicatorType.DOMAIN,
            reputation_level=ReputationLevel.SUSPICIOUS,
            source=ThreatSource.COMMERCIAL_FEED,
            first_seen=now,
            last_seen=now,
            confidence=0.7,
            tags=["phishing"]
        )
        
        # Test serialization
        data = indicator.to_dict()
        assert data['value'] == "malicious.com"
        assert data['indicator_type'] == "domain"
        assert data['reputation_level'] == "suspicious"
        
        # Test deserialization
        restored = ThreatIndicator.from_dict(data)
        assert restored.value == indicator.value
        assert restored.indicator_type == indicator.indicator_type
        assert restored.reputation_level == indicator.reputation_level
        assert restored.confidence == indicator.confidence
    
    def test_indicator_expiration(self):
        """Test indicator expiration logic."""
        now = datetime.utcnow()
        
        # Non-expiring indicator
        indicator1 = ThreatIndicator(
            value="test1",
            indicator_type=ThreatIndicatorType.IP_ADDRESS,
            reputation_level=ReputationLevel.MALICIOUS,
            source=ThreatSource.INTERNAL,
            first_seen=now,
            last_seen=now,
            confidence=0.9
        )
        assert not indicator1.is_expired()
        
        # Expired indicator
        indicator2 = ThreatIndicator(
            value="test2",
            indicator_type=ThreatIndicatorType.IP_ADDRESS,
            reputation_level=ReputationLevel.MALICIOUS,
            source=ThreatSource.INTERNAL,
            first_seen=now - timedelta(hours=2),
            last_seen=now - timedelta(hours=2),
            confidence=0.9,
            ttl=3600  # 1 hour TTL
        )
        assert indicator2.is_expired()


class TestThreatIndicatorDatabase:
    """Test ThreatIndicatorDatabase class."""
    
    def test_add_and_get_indicator(self):
        """Test adding and retrieving indicators."""
        db = ThreatIndicatorDatabase()
        now = datetime.utcnow()
        
        indicator = ThreatIndicator(
            value="192.168.1.1",
            indicator_type=ThreatIndicatorType.IP_ADDRESS,
            reputation_level=ReputationLevel.MALICIOUS,
            source=ThreatSource.INTERNAL,
            first_seen=now,
            last_seen=now,
            confidence=0.9
        )
        
        db.add_indicator(indicator)
        
        # Test retrieval
        retrieved = db.get_indicator("192.168.1.1", ThreatIndicatorType.IP_ADDRESS)
        assert retrieved is not None
        assert retrieved.value == "192.168.1.1"
        assert retrieved.confidence == 0.9
        
        # Test non-existent indicator
        not_found = db.get_indicator("1.1.1.1", ThreatIndicatorType.IP_ADDRESS)
        assert not_found is None
    
    def test_ip_matching(self):
        """Test IP address and network matching."""
        db = ThreatIndicatorDatabase()
        now = datetime.utcnow()
        
        # Add network indicator
        network_indicator = ThreatIndicator(
            value="192.168.1.0/24",
            indicator_type=ThreatIndicatorType.IP_ADDRESS,
            reputation_level=ReputationLevel.SUSPICIOUS,
            source=ThreatSource.INTERNAL,
            first_seen=now,
            last_seen=now,
            confidence=0.7
        )
        db.add_indicator(network_indicator)
        
        # Add specific IP indicator
        ip_indicator = ThreatIndicator(
            value="192.168.1.100",
            indicator_type=ThreatIndicatorType.IP_ADDRESS,
            reputation_level=ReputationLevel.MALICIOUS,
            source=ThreatSource.INTERNAL,
            first_seen=now,
            last_seen=now,
            confidence=0.9
        )
        db.add_indicator(ip_indicator)
        
        # Test matching IP in network
        matches = db.match_ip("192.168.1.50")
        assert len(matches) == 1
        assert matches[0].value == "192.168.1.0/24"
        
        # Test matching specific IP (should match both network and specific)
        matches = db.match_ip("192.168.1.100")
        assert len(matches) == 2
        values = [match.value for match in matches]
        assert "192.168.1.100" in values
        assert "192.168.1.0/24" in values
        
        # Test non-matching IP
        matches = db.match_ip("10.0.0.1")
        assert len(matches) == 0
    
    def test_search_indicators(self):
        """Test searching indicators by criteria."""
        db = ThreatIndicatorDatabase()
        now = datetime.utcnow()
        
        # Add various indicators
        indicators = [
            ThreatIndicator(
                value="malicious1.com",
                indicator_type=ThreatIndicatorType.DOMAIN,
                reputation_level=ReputationLevel.MALICIOUS,
                source=ThreatSource.COMMERCIAL_FEED,
                first_seen=now,
                last_seen=now,
                confidence=0.9,
                tags=["malware"]
            ),
            ThreatIndicator(
                value="suspicious1.com",
                indicator_type=ThreatIndicatorType.DOMAIN,
                reputation_level=ReputationLevel.SUSPICIOUS,
                source=ThreatSource.OPEN_SOURCE,
                first_seen=now,
                last_seen=now,
                confidence=0.6,
                tags=["phishing"]
            ),
            ThreatIndicator(
                value="192.168.1.1",
                indicator_type=ThreatIndicatorType.IP_ADDRESS,
                reputation_level=ReputationLevel.MALICIOUS,
                source=ThreatSource.INTERNAL,
                first_seen=now,
                last_seen=now,
                confidence=0.8,
                tags=["malware", "botnet"]
            )
        ]
        
        for indicator in indicators:
            db.add_indicator(indicator)
        
        # Search by type
        domain_indicators = db.search_indicators(indicator_type=ThreatIndicatorType.DOMAIN)
        assert len(domain_indicators) == 2
        
        # Search by reputation level
        malicious_indicators = db.search_indicators(reputation_level=ReputationLevel.MALICIOUS)
        assert len(malicious_indicators) == 2
        
        # Search by tags
        malware_indicators = db.search_indicators(tags=["malware"])
        assert len(malware_indicators) == 2
        
        # Combined search
        malicious_domains = db.search_indicators(
            indicator_type=ThreatIndicatorType.DOMAIN,
            reputation_level=ReputationLevel.MALICIOUS
        )
        assert len(malicious_domains) == 1
        assert malicious_domains[0].value == "malicious1.com"
    
    def test_persistence(self):
        """Test indicator persistence to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            persistence_file = f.name
        
        # Create database with persistence
        db1 = ThreatIndicatorDatabase(persistence_file)
        now = datetime.utcnow()
        
        indicator = ThreatIndicator(
            value="test.com",
            indicator_type=ThreatIndicatorType.DOMAIN,
            reputation_level=ReputationLevel.MALICIOUS,
            source=ThreatSource.INTERNAL,
            first_seen=now,
            last_seen=now,
            confidence=0.9
        )
        
        db1.add_indicator(indicator)
        db1.save_to_file()
        
        # Create new database instance and load from file
        db2 = ThreatIndicatorDatabase(persistence_file)
        
        # Verify indicator was loaded
        loaded_indicator = db2.get_indicator("test.com", ThreatIndicatorType.DOMAIN)
        assert loaded_indicator is not None
        assert loaded_indicator.value == "test.com"
        assert loaded_indicator.confidence == 0.9


class TestThreatFeedManager:
    """Test ThreatFeedManager class."""
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        config = {}
        manager = ThreatFeedManager(config)
        
        # Test rate limit check
        assert manager._check_rate_limit('test_service', 5, 60)  # First request
        assert manager._check_rate_limit('test_service', 5, 60)  # Second request
        
        # Fill up the rate limit
        for _ in range(3):
            manager._check_rate_limit('test_service', 5, 60)
        
        # Should now be at limit
        assert not manager._check_rate_limit('test_service', 5, 60)
    
    @pytest.mark.asyncio
    async def test_abuseipdb_query_mock(self):
        """Test AbuseIPDB query with mocked response."""
        config = {'abuseipdb_api_key': 'test_key'}
        
        mock_response_data = {
            'data': {
                'ipAddress': '192.168.1.1',
                'abuseConfidencePercentage': 75,
                'countryCode': 'US',
                'usageType': 'Data Center/Web Hosting/Transit'
            }
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with ThreatFeedManager(config) as manager:
                result = await manager.query_abuse_ipdb('192.168.1.1')
                
                assert result is not None
                assert result['ipAddress'] == '192.168.1.1'
                assert result['abuseConfidencePercentage'] == 75
    
    @pytest.mark.asyncio
    async def test_virustotal_query_mock(self):
        """Test VirusTotal query with mocked response."""
        config = {'virustotal_api_key': 'test_key'}
        
        mock_response_data = {
            'data': {
                'attributes': {
                    'last_analysis_stats': {
                        'harmless': 70,
                        'malicious': 5,
                        'suspicious': 2,
                        'undetected': 8
                    }
                }
            }
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with ThreatFeedManager(config) as manager:
                result = await manager.query_virustotal('192.168.1.1')
                
                assert result is not None
                assert 'attributes' in result
                assert 'last_analysis_stats' in result['attributes']


class TestThreatIntelligenceEngine:
    """Test ThreatIntelligenceEngine class."""
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        config = {
            'persistence_file': 'test_indicators.json',
            'threat_feeds': {
                'abuseipdb_api_key': 'test_key'
            }
        }
        
        engine = ThreatIntelligenceEngine(config)
        
        assert engine.config == config
        assert engine.indicator_db is not None
        assert engine.feed_manager_config == config['threat_feeds']
        
        # Check that default indicators were loaded
        stats = engine.get_threat_statistics()
        assert stats['total_indicators'] > 0
    
    @pytest.mark.asyncio
    async def test_ip_reputation_analysis(self):
        """Test IP reputation analysis."""
        config = {}
        engine = ThreatIntelligenceEngine(config)
        
        # Add a known malicious IP to the database
        now = datetime.utcnow()
        malicious_indicator = ThreatIndicator(
            value="192.168.1.100",
            indicator_type=ThreatIndicatorType.IP_ADDRESS,
            reputation_level=ReputationLevel.MALICIOUS,
            source=ThreatSource.INTERNAL,
            first_seen=now,
            last_seen=now,
            confidence=0.9,
            tags=["malware"]
        )
        engine.indicator_db.add_indicator(malicious_indicator)
        
        # Test reputation analysis
        result = await engine.analyze_ip_reputation("192.168.1.100")
        
        assert result.ip_address == "192.168.1.100"
        assert result.reputation_level == ReputationLevel.MALICIOUS
        assert result.confidence == 0.9
        assert "internal" in result.sources
        assert "malware" in result.tags
    
    @pytest.mark.asyncio
    async def test_threat_context_analysis(self):
        """Test comprehensive threat context analysis."""
        config = {}
        engine = ThreatIntelligenceEngine(config)
        
        # Create auth context
        auth_context = AuthContext(
            email="test@example.com",
            password_hash="hashed_password",
            client_ip="192.168.1.100",
            user_agent="sqlmap/1.0",
            timestamp=datetime.utcnow(),
            request_id="test_request_123"
        )
        
        # Add threat indicators
        now = datetime.utcnow()
        ip_indicator = ThreatIndicator(
            value="192.168.1.100",
            indicator_type=ThreatIndicatorType.IP_ADDRESS,
            reputation_level=ReputationLevel.MALICIOUS,
            source=ThreatSource.INTERNAL,
            first_seen=now,
            last_seen=now,
            confidence=0.8,
            tags=["botnet"]
        )
        
        ua_indicator = ThreatIndicator(
            value="sqlmap",
            indicator_type=ThreatIndicatorType.USER_AGENT,
            reputation_level=ReputationLevel.MALICIOUS,
            source=ThreatSource.INTERNAL,
            first_seen=now,
            last_seen=now,
            confidence=0.95,
            tags=["sql_injection", "scanner"]
        )
        
        engine.indicator_db.add_indicator(ip_indicator)
        engine.indicator_db.add_indicator(ua_indicator)
        
        # Analyze threat context
        threat_context = await engine.get_threat_context(auth_context)
        
        assert threat_context.ip_reputation.reputation_level == ReputationLevel.MALICIOUS
        assert len(threat_context.threat_indicators) >= 2  # IP and UA indicators
        assert threat_context.risk_score > 0.5  # Should be high risk
        assert "botnet" in threat_context.threat_categories
        assert "sql_injection" in threat_context.threat_categories
    
    def test_risk_score_calculation(self):
        """Test threat risk score calculation."""
        config = {}
        engine = ThreatIntelligenceEngine(config)
        
        # Test with clean IP reputation
        clean_reputation = IPReputationResult(
            ip_address="1.1.1.1",
            reputation_level=ReputationLevel.CLEAN,
            confidence=0.9,
            sources=["test"]
        )
        
        risk_score = engine._calculate_threat_risk_score(clean_reputation, [])
        assert risk_score == 0.0
        
        # Test with malicious IP reputation
        malicious_reputation = IPReputationResult(
            ip_address="192.168.1.1",
            reputation_level=ReputationLevel.MALICIOUS,
            confidence=0.9,
            sources=["test"]
        )
        
        risk_score = engine._calculate_threat_risk_score(malicious_reputation, [])
        assert risk_score > 0.5
        
        # Test with additional threat indicators
        now = datetime.utcnow()
        threat_indicator = ThreatIndicator(
            value="malicious_pattern",
            indicator_type=ThreatIndicatorType.PATTERN,
            reputation_level=ReputationLevel.CRITICAL,
            source=ThreatSource.INTERNAL,
            first_seen=now,
            last_seen=now,
            confidence=0.95
        )
        
        risk_score = engine._calculate_threat_risk_score(malicious_reputation, [threat_indicator])
        assert risk_score > 0.8  # Should be very high with both IP and indicator
    
    def test_threat_categories_determination(self):
        """Test threat categories determination."""
        config = {}
        engine = ThreatIntelligenceEngine(config)
        
        # Create IP reputation with tags
        ip_reputation = IPReputationResult(
            ip_address="192.168.1.1",
            reputation_level=ReputationLevel.MALICIOUS,
            confidence=0.9,
            sources=["test"],
            tags=["botnet", "malware"]
        )
        
        # Create threat indicators with tags
        now = datetime.utcnow()
        indicator = ThreatIndicator(
            value="test_pattern",
            indicator_type=ThreatIndicatorType.PATTERN,
            reputation_level=ReputationLevel.SUSPICIOUS,
            source=ThreatSource.INTERNAL,
            first_seen=now,
            last_seen=now,
            confidence=0.7,
            tags=["scanner", "sql_injection"]
        )
        
        categories = engine._determine_threat_categories(ip_reputation, [indicator])
        
        assert "botnet" in categories
        assert "malware" in categories
        assert "scanner" in categories
        assert "sql_injection" in categories
    
    def test_threat_attribution(self):
        """Test threat attribution logic."""
        config = {}
        engine = ThreatIntelligenceEngine(config)
        
        # Test with APT indicator
        now = datetime.utcnow()
        apt_indicator = ThreatIndicator(
            value="apt_pattern",
            indicator_type=ThreatIndicatorType.PATTERN,
            reputation_level=ReputationLevel.CRITICAL,
            source=ThreatSource.COMMERCIAL_FEED,
            first_seen=now,
            last_seen=now,
            confidence=0.95,
            tags=["apt", "targeted"]
        )
        
        attribution = engine._attempt_attribution([apt_indicator])
        assert attribution is not None
        assert "APT" in attribution
        
        # Test with botnet indicator
        botnet_indicator = ThreatIndicator(
            value="botnet_pattern",
            indicator_type=ThreatIndicatorType.PATTERN,
            reputation_level=ReputationLevel.MALICIOUS,
            source=ThreatSource.OPEN_SOURCE,
            first_seen=now,
            last_seen=now,
            confidence=0.8,
            tags=["botnet"]
        )
        
        attribution = engine._attempt_attribution([botnet_indicator])
        assert attribution is not None
        assert "Botnet" in attribution
        
        # Test with no attribution indicators
        clean_indicator = ThreatIndicator(
            value="clean_pattern",
            indicator_type=ThreatIndicatorType.PATTERN,
            reputation_level=ReputationLevel.CLEAN,
            source=ThreatSource.INTERNAL,
            first_seen=now,
            last_seen=now,
            confidence=0.5,
            tags=["test"]
        )
        
        attribution = engine._attempt_attribution([clean_indicator])
        assert attribution is None
    
    def test_update_threat_intelligence(self):
        """Test updating threat intelligence."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        config = {'persistence_file': temp_file}
        engine = ThreatIntelligenceEngine(config)
        
        initial_stats = engine.get_threat_statistics()
        initial_count = initial_stats['total_indicators']
        
        # Add new indicators
        now = datetime.utcnow()
        new_indicators = [
            ThreatIndicator(
                value="new_malicious.com",
                indicator_type=ThreatIndicatorType.DOMAIN,
                reputation_level=ReputationLevel.MALICIOUS,
                source=ThreatSource.COMMERCIAL_FEED,
                first_seen=now,
                last_seen=now,
                confidence=0.9,
                tags=["phishing"]
            ),
            ThreatIndicator(
                value="10.0.0.100",
                indicator_type=ThreatIndicatorType.IP_ADDRESS,
                reputation_level=ReputationLevel.SUSPICIOUS,
                source=ThreatSource.OPEN_SOURCE,
                first_seen=now,
                last_seen=now,
                confidence=0.7,
                tags=["scanner"]
            )
        ]
        
        engine.update_threat_intelligence(new_indicators)
        
        # Verify indicators were added
        updated_stats = engine.get_threat_statistics()
        assert updated_stats['total_indicators'] == initial_count + 2
        
        # Verify specific indicators can be retrieved
        domain_indicator = engine.indicator_db.get_indicator(
            "new_malicious.com", 
            ThreatIndicatorType.DOMAIN
        )
        assert domain_indicator is not None
        assert domain_indicator.reputation_level == ReputationLevel.MALICIOUS
        
        ip_matches = engine.indicator_db.match_ip("10.0.0.100")
        assert len(ip_matches) >= 1
        assert any(match.value == "10.0.0.100" for match in ip_matches)
    
    def test_get_threat_statistics(self):
        """Test getting threat statistics."""
        config = {}
        engine = ThreatIntelligenceEngine(config)
        
        stats = engine.get_threat_statistics()
        
        # Verify structure
        assert 'total_indicators' in stats
        assert 'by_type' in stats
        assert 'by_reputation' in stats
        assert 'by_source' in stats
        assert 'cache_size' in stats
        
        # Verify counts are reasonable
        assert stats['total_indicators'] > 0
        assert isinstance(stats['by_type'], dict)
        assert isinstance(stats['by_reputation'], dict)
        assert isinstance(stats['by_source'], dict)



class TestCampaignCorrelation:
    """Test campaign correlation functionality in threat intelligence engine."""
    
    @pytest.mark.asyncio
    async def test_campaign_correlation_detection(self):
        """Test detection of campaign correlation."""
        config = {
            'persistence_file': 'test_indicators.json',
            'campaign_analysis': {
                'correlation_threshold': 0.7,
                'min_events_for_campaign': 3,
                'campaign_timeout_hours': 72
            }
        }
        
        engine = ThreatIntelligenceEngine(config)
        
        # Create test authentication context
        auth_context = AuthContext(
            email="test@example.com",
            password_hash="hashed_password",
            client_ip="192.168.1.100",
            user_agent="Mozilla/5.0",
            timestamp=datetime.utcnow(),
            request_id="test_request"
        )
        
        # Create test threat analysis
        from src.ai_karen_engine.security.models import ThreatAnalysis
        threat_analysis = ThreatAnalysis(
            ip_reputation_score=0.8,
            known_attack_patterns=["brute_force"],
            threat_actor_indicators=["automated_tool"]
        )
        
        # Test campaign correlation detection (should return None for new attempt)
        campaign_id = await engine.detect_attack_campaign_correlation(auth_context, threat_analysis)
        assert campaign_id is None
    
    @pytest.mark.asyncio
    async def test_analyze_attack_campaigns(self):
        """Test analysis of attack campaigns."""
        config = {
            'persistence_file': 'test_indicators.json',
            'campaign_analysis': {
                'correlation_threshold': 0.7,
                'min_events_for_campaign': 3,
                'campaign_timeout_hours': 72
            }
        }
        
        engine = ThreatIntelligenceEngine(config)
        
        # Create multiple authentication attempts that could form a campaign
        auth_attempts = []
        base_time = datetime.utcnow()
        
        for i in range(5):
            auth_context = AuthContext(
                email=f"user{i}@example.com",
                password_hash="hashed_password",
                client_ip="192.168.1.100",  # Same IP for all attempts
                user_agent="Mozilla/5.0",
                timestamp=base_time + timedelta(minutes=i),
                request_id=f"test_request_{i}"
            )
            
            from src.ai_karen_engine.security.models import ThreatAnalysis
            threat_analysis = ThreatAnalysis(
                ip_reputation_score=0.8,
                known_attack_patterns=["brute_force"],
                threat_actor_indicators=["automated_tool"]
            )
            
            auth_attempts.append((auth_context, threat_analysis))
        
        # Analyze for campaigns
        result = await engine.analyze_attack_campaigns(auth_attempts)
        
        assert result is not None
        assert hasattr(result, 'detected_campaigns')
        assert hasattr(result, 'new_campaigns')
        assert hasattr(result, 'threat_intelligence_updates')
    
    def test_campaign_analyzer_integration(self):
        """Test that campaign analyzer is properly integrated."""
        config = {
            'campaign_analysis': {
                'correlation_threshold': 0.7,
                'min_events_for_campaign': 3
            }
        }
        
        engine = ThreatIntelligenceEngine(config)
        
        assert hasattr(engine, 'campaign_analyzer')
        assert engine.campaign_analyzer is not None
        assert hasattr(engine.campaign_analyzer, 'campaign_db')
        assert hasattr(engine.campaign_analyzer, 'attack_signatures')


if __name__ == "__main__":
    pytest.main([__file__])