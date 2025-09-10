"""
Unit tests for SecurityAnalyzer class.

Tests comprehensive security analysis functionality including:
- Attack pattern detection
- Threat intelligence management
- Security assessment generation
- Behavioral analysis
- Client reputation tracking
"""

import json
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request
from fastapi.datastructures import URL, Headers

from src.ai_karen_engine.server.security_analyzer import (
    SecurityAnalyzer,
    SecurityAssessment,
    ThreatIntelligence
)


class TestSecurityAnalyzer:
    """Test cases for SecurityAnalyzer class."""
    
    @pytest.fixture
    def temp_intelligence_file(self):
        """Create a temporary file for threat intelligence storage."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({}, f)  # Initialize with empty JSON object
            temp_file = f.name
        yield temp_file
        # Cleanup
        Path(temp_file).unlink(missing_ok=True)
    
    @pytest.fixture
    def analyzer(self, temp_intelligence_file):
        """Create a SecurityAnalyzer instance for testing."""
        return SecurityAnalyzer(threat_intelligence_file=temp_intelligence_file)
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI Request object."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock(spec=URL)
        request.url.path = "/api/test"
        request.url.query = ""
        request.headers = Headers({"user-agent": "test-browser/1.0"})
        request.client = Mock()
        request.client.host = "192.168.1.100"
        return request
    
    def test_analyzer_initialization(self, temp_intelligence_file):
        """Test SecurityAnalyzer initialization."""
        analyzer = SecurityAnalyzer(threat_intelligence_file=temp_intelligence_file)
        
        assert analyzer.threat_intelligence_file == temp_intelligence_file
        assert isinstance(analyzer.threat_intelligence, dict)
        assert isinstance(analyzer.attack_patterns, dict)
        assert len(analyzer.attack_patterns) > 0
        assert "sql_injection" in analyzer.attack_patterns
        assert "xss" in analyzer.attack_patterns
        assert "path_traversal" in analyzer.attack_patterns
    
    def test_attack_patterns_loading(self, analyzer):
        """Test that attack patterns are properly loaded."""
        patterns = analyzer.attack_patterns
        
        # Check that all expected categories are present
        expected_categories = [
            "sql_injection", "xss", "path_traversal", "command_injection",
            "ldap_injection", "xml_injection", "csrf", "header_injection", "nosql_injection"
        ]
        
        for category in expected_categories:
            assert category in patterns
            assert len(patterns[category]) > 0
            
        # Check that patterns are compiled regex objects
        for category_patterns in patterns.values():
            for pattern in category_patterns:
                assert hasattr(pattern, 'search')  # regex pattern method
    
    def test_ip_hashing(self, analyzer):
        """Test IP address hashing for privacy."""
        ip1 = "192.168.1.100"
        ip2 = "10.0.0.1"
        
        hash1 = analyzer._hash_ip(ip1)
        hash2 = analyzer._hash_ip(ip2)
        
        assert hash1 != hash2
        assert len(hash1) == 16  # SHA256 truncated to 16 chars
        assert len(hash2) == 16
        
        # Same IP should produce same hash
        assert analyzer._hash_ip(ip1) == hash1
    
    def test_client_ip_extraction(self, analyzer):
        """Test client IP extraction from various headers."""
        # Test with x-forwarded-for header
        request = Mock(spec=Request)
        request.headers = Headers({"x-forwarded-for": "203.0.113.1, 192.168.1.1"})
        request.client = Mock()
        request.client.host = "192.168.1.1"
        
        ip = analyzer._get_client_ip(request)
        assert ip == "203.0.113.1"
        
        # Test with x-real-ip header
        request.headers = Headers({"x-real-ip": "203.0.113.2"})
        ip = analyzer._get_client_ip(request)
        assert ip == "203.0.113.2"
        
        # Test fallback to client.host
        request.headers = Headers({})
        ip = analyzer._get_client_ip(request)
        assert ip == "192.168.1.1"
    
    @pytest.mark.asyncio
    async def test_basic_request_analysis(self, analyzer, mock_request):
        """Test basic security analysis of a clean request."""
        assessment = await analyzer.analyze_request(mock_request)
        
        assert isinstance(assessment, SecurityAssessment)
        assert assessment.threat_level in ["none", "low", "medium", "high", "critical"]
        assert assessment.client_reputation in ["trusted", "unknown", "suspicious", "malicious"]
        assert assessment.recommended_action in ["allow", "monitor", "rate_limit", "block"]
        assert 0.0 <= assessment.confidence_score <= 1.0
        assert assessment.client_ip_hash is not None
    
    @pytest.mark.asyncio
    async def test_sql_injection_detection(self, analyzer):
        """Test SQL injection attack pattern detection."""
        # Create request with SQL injection attempt
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock(spec=URL)
        request.url.path = "/api/users"
        request.url.query = "id=1' OR 1=1--"
        request.headers = Headers({"user-agent": "test-browser/1.0"})
        request.client = Mock()
        request.client.host = "192.168.1.100"
        
        assessment = await analyzer.analyze_request(request)
        
        assert assessment.threat_level in ["medium", "high", "critical"]
        assert "sql_injection" in assessment.attack_categories
        assert len(assessment.detected_patterns) > 0
        assert any("sql_injection" in pattern for pattern in assessment.detected_patterns)
        assert assessment.recommended_action in ["rate_limit", "block"]
    
    @pytest.mark.asyncio
    async def test_xss_detection(self, analyzer):
        """Test XSS attack pattern detection."""
        request = Mock(spec=Request)
        request.method = "POST"
        request.url = Mock(spec=URL)
        request.url.path = "/api/comments"
        request.url.query = "content=<script>alert('xss')</script>"
        request.headers = Headers({"user-agent": "test-browser/1.0"})
        request.client = Mock()
        request.client.host = "192.168.1.101"
        
        assessment = await analyzer.analyze_request(request)
        
        assert assessment.threat_level in ["medium", "high", "critical"]
        assert "xss" in assessment.attack_categories
        assert any("xss" in pattern for pattern in assessment.detected_patterns)
    
    @pytest.mark.asyncio
    async def test_path_traversal_detection(self, analyzer):
        """Test path traversal attack pattern detection."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock(spec=URL)
        request.url.path = "/api/files"
        request.url.query = "file=../../../etc/passwd"
        request.headers = Headers({"user-agent": "test-browser/1.0"})
        request.client = Mock()
        request.client.host = "192.168.1.102"
        
        assessment = await analyzer.analyze_request(request)
        
        assert assessment.threat_level in ["medium", "high", "critical"]
        assert "path_traversal" in assessment.attack_categories
    
    @pytest.mark.asyncio
    async def test_header_injection_detection(self, analyzer):
        """Test header injection attack pattern detection."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock(spec=URL)
        request.url.path = "/api/test"
        request.url.query = ""
        request.headers = Headers({
            "user-agent": "test-browser/1.0",
            "x-custom-header": "value\r\nSet-Cookie: malicious=true"
        })
        request.client = Mock()
        request.client.host = "192.168.1.103"
        
        assessment = await analyzer.analyze_request(request)
        
        assert assessment.threat_level in ["medium", "high", "critical"]
        assert "header_injection" in assessment.attack_categories
    
    @pytest.mark.asyncio
    async def test_behavioral_analysis(self, analyzer):
        """Test behavioral analysis functionality."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock(spec=URL)
        request.url.path = "/api/test" + "A" * 600  # Very long path
        request.url.query = ""
        request.headers = Headers({})  # No user-agent
        request.client = Mock()
        request.client.host = "192.168.1.104"
        
        client_ip_hash = analyzer._hash_ip("192.168.1.104")
        behavioral_score = await analyzer._analyze_behavior(request, client_ip_hash)
        
        assert 0.0 <= behavioral_score <= 1.0
        assert behavioral_score > 0.0  # Should detect suspicious behavior
    
    def test_client_reputation_unknown(self, analyzer):
        """Test client reputation for unknown IP."""
        ip_hash = analyzer._hash_ip("192.168.1.200")
        reputation = analyzer._get_client_reputation(ip_hash)
        assert reputation == "unknown"
    
    def test_client_reputation_with_intelligence(self, analyzer):
        """Test client reputation with existing threat intelligence."""
        ip_hash = analyzer._hash_ip("192.168.1.201")
        
        # Add threat intelligence
        analyzer.threat_intelligence[ip_hash] = ThreatIntelligence(
            ip_hash=ip_hash,
            threat_score=0.9,
            attack_count=10,
            last_seen=datetime.now()
        )
        
        reputation = analyzer._get_client_reputation(ip_hash)
        assert reputation == "malicious"
        
        # Test suspicious reputation
        analyzer.threat_intelligence[ip_hash].threat_score = 0.6
        reputation = analyzer._get_client_reputation(ip_hash)
        assert reputation == "suspicious"
    
    def test_threat_level_calculation(self, analyzer):
        """Test threat level calculation logic."""
        # Test critical threat
        threat_level, confidence = analyzer._calculate_threat_level(
            detected_patterns=["sql_injection:pattern1", "xss:pattern2"],
            attack_categories=["sql_injection", "xss"],
            behavioral_score=0.8,
            client_reputation="malicious"
        )
        
        assert threat_level in ["high", "critical"]
        assert confidence > 0.5
        
        # Test low threat
        threat_level, confidence = analyzer._calculate_threat_level(
            detected_patterns=[],
            attack_categories=[],
            behavioral_score=0.0,
            client_reputation="trusted"
        )
        
        assert threat_level in ["none", "low"]
    
    def test_action_determination(self, analyzer):
        """Test recommended action determination."""
        # Test block action
        action = analyzer._determine_action("critical", 0.9, "malicious")
        assert action == "block"
        
        # Test rate limit action
        action = analyzer._determine_action("medium", 0.7, "suspicious")
        assert action == "rate_limit"
        
        # Test allow action (none threat level with trusted reputation)
        action = analyzer._determine_action("none", 0.5, "trusted")
        assert action == "allow"
        
        # Test monitor action (low confidence)
        action = analyzer._determine_action("none", 0.1, "unknown")
        assert action == "monitor"
    
    def test_attack_pattern_detection_method(self, analyzer):
        """Test the detect_attack_patterns method."""
        request_data = {
            "path": "/api/users",
            "query": "id=1' OR 1=1--",
            "headers": {"user-agent": "test"},
            "body": "<script>alert('xss')</script>"
        }
        
        detected = analyzer.detect_attack_patterns(request_data)
        
        assert len(detected) > 0
        assert any("sql_injection" in pattern for pattern in detected)
        assert any("xss" in pattern for pattern in detected)
    
    def test_threat_intelligence_update(self, analyzer):
        """Test threat intelligence update functionality."""
        ip_hash = analyzer._hash_ip("192.168.1.300")
        
        # Initial update
        analyzer.update_threat_intelligence(ip_hash, "high", ["sql_injection"])
        
        assert ip_hash in analyzer.threat_intelligence
        intel = analyzer.threat_intelligence[ip_hash]
        assert intel.attack_count == 1
        assert intel.threat_score > 0.0
        assert "sql_injection" in intel.attack_types
        
        # Second update
        analyzer.update_threat_intelligence(ip_hash, "critical", ["xss"])
        
        intel = analyzer.threat_intelligence[ip_hash]
        assert intel.attack_count == 2
        assert intel.threat_score > 0.2  # Should have increased
        assert "xss" in intel.attack_types
    
    def test_threat_intelligence_persistence(self, temp_intelligence_file):
        """Test threat intelligence saving and loading."""
        # Create analyzer and add some intelligence
        analyzer1 = SecurityAnalyzer(threat_intelligence_file=temp_intelligence_file)
        ip_hash = analyzer1._hash_ip("192.168.1.400")
        analyzer1.update_threat_intelligence(ip_hash, "high", ["sql_injection"])
        analyzer1._save_threat_intelligence()
        
        # Create new analyzer and verify data is loaded
        analyzer2 = SecurityAnalyzer(threat_intelligence_file=temp_intelligence_file)
        
        assert ip_hash in analyzer2.threat_intelligence
        intel = analyzer2.threat_intelligence[ip_hash]
        assert intel.attack_count == 1
        assert "sql_injection" in intel.attack_types
    
    @pytest.mark.asyncio
    async def test_analysis_caching(self, analyzer, mock_request):
        """Test that analysis results are cached properly."""
        # First analysis
        assessment1 = await analyzer.analyze_request(mock_request)
        cache_size_after_first = len(analyzer.analysis_cache)
        
        # Second analysis of same request should use cache
        assessment2 = await analyzer.analyze_request(mock_request)
        cache_size_after_second = len(analyzer.analysis_cache)
        
        assert cache_size_after_first == cache_size_after_second
        assert assessment1.threat_level == assessment2.threat_level
        assert assessment1.confidence_score == assessment2.confidence_score
    
    def test_threat_statistics(self, analyzer):
        """Test threat statistics generation."""
        # Add some test data
        ip_hash1 = analyzer._hash_ip("192.168.1.500")
        ip_hash2 = analyzer._hash_ip("192.168.1.501")
        
        analyzer.threat_intelligence[ip_hash1] = ThreatIntelligence(
            ip_hash=ip_hash1,
            threat_score=0.9,
            attack_count=5,
            last_seen=datetime.now(),
            attack_types={"sql_injection", "xss"},
            blocked=True
        )
        
        analyzer.threat_intelligence[ip_hash2] = ThreatIntelligence(
            ip_hash=ip_hash2,
            threat_score=0.8,
            attack_count=3,
            last_seen=datetime.now(),
            attack_types={"path_traversal"}
        )
        
        stats = analyzer.get_threat_statistics()
        
        assert stats["total_tracked_ips"] == 2
        assert stats["blocked_ips"] == 1
        assert stats["high_risk_ips"] == 2
        assert "sql_injection" in stats["attack_type_distribution"]
        assert stats["attack_type_distribution"]["sql_injection"] == 1
    
    def test_cleanup_old_intelligence(self, analyzer):
        """Test cleanup of old threat intelligence entries."""
        # Add old and new entries
        old_ip = analyzer._hash_ip("192.168.1.600")
        new_ip = analyzer._hash_ip("192.168.1.601")
        
        analyzer.threat_intelligence[old_ip] = ThreatIntelligence(
            ip_hash=old_ip,
            threat_score=0.3,
            attack_count=1,
            last_seen=datetime.now() - timedelta(days=35)  # Old entry
        )
        
        analyzer.threat_intelligence[new_ip] = ThreatIntelligence(
            ip_hash=new_ip,
            threat_score=0.5,
            attack_count=2,
            last_seen=datetime.now()  # Recent entry
        )
        
        # Cleanup entries older than 30 days
        removed_count = analyzer.cleanup_old_intelligence(days_old=30)
        
        assert removed_count == 1
        assert old_ip not in analyzer.threat_intelligence
        assert new_ip in analyzer.threat_intelligence
    
    def test_error_handling_in_analysis(self, analyzer):
        """Test error handling during security analysis."""
        # Create a malformed request that might cause errors
        request = Mock(spec=Request)
        request.method = None  # This should cause an error
        request.url = None
        request.headers = None
        request.client = None
        
        # Analysis should not crash and should return a safe result
        import asyncio
        assessment = asyncio.run(analyzer.analyze_request(request))
        
        assert isinstance(assessment, SecurityAssessment)
        assert assessment.threat_level == "low"
        assert "analysis_error" in assessment.detected_patterns
        assert assessment.recommended_action == "monitor"
    
    def test_cache_cleanup(self, analyzer):
        """Test analysis cache cleanup functionality."""
        import time
        current_time = time.time()
        
        # Add some cache entries
        analyzer.analysis_cache["key1"] = (Mock(), current_time - 400)  # Old entry (beyond TTL)
        analyzer.analysis_cache["key2"] = (Mock(), current_time - 100)  # Recent entry (within TTL)
        
        analyzer._clean_cache()
        
        assert "key1" not in analyzer.analysis_cache
        assert "key2" in analyzer.analysis_cache


class TestSecurityAssessment:
    """Test cases for SecurityAssessment data class."""
    
    def test_security_assessment_creation(self):
        """Test SecurityAssessment creation and default values."""
        assessment = SecurityAssessment(
            threat_level="high",
            detected_patterns=["sql_injection"],
            client_reputation="suspicious",
            recommended_action="block",
            confidence_score=0.8
        )
        
        assert assessment.threat_level == "high"
        assert assessment.detected_patterns == ["sql_injection"]
        assert assessment.client_reputation == "suspicious"
        assert assessment.recommended_action == "block"
        assert assessment.confidence_score == 0.8
        assert isinstance(assessment.analysis_timestamp, datetime)
        assert assessment.attack_categories == []
        assert assessment.risk_factors == {}


class TestThreatIntelligence:
    """Test cases for ThreatIntelligence data class."""
    
    def test_threat_intelligence_creation(self):
        """Test ThreatIntelligence creation and default values."""
        intel = ThreatIntelligence(
            ip_hash="abc123",
            threat_score=0.7,
            attack_count=5,
            last_seen=datetime.now()
        )
        
        assert intel.ip_hash == "abc123"
        assert intel.threat_score == 0.7
        assert intel.attack_count == 5
        assert isinstance(intel.last_seen, datetime)
        assert isinstance(intel.first_seen, datetime)
        assert intel.attack_types == set()
        assert intel.blocked is False
        assert intel.notes == ""


if __name__ == "__main__":
    pytest.main([__file__])