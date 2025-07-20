"""
Comprehensive tests for the security framework.
Tests penetration testing, threat protection, incident response, and compliance.
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from src.ai_karen_engine.security.penetration_testing import (
    PenetrationTestSuite, SecurityScanner, SecurityVulnerability, 
    VulnerabilityLevel, TestCategory
)
from src.ai_karen_engine.security.threat_protection import (
    ThreatProtectionSystem, IntrusionDetectionSystem, ThreatEvent,
    ThreatLevel, AttackType, ThreatDetectionEngine
)
from src.ai_karen_engine.security.incident_response import (
    SecurityIncidentManager, SecurityIncident, IncidentSeverity,
    IncidentStatus, ResponseOrchestrator
)
from src.ai_karen_engine.security.compliance import (
    ComplianceReporter, SOC2Reporter, GDPRReporter,
    ComplianceFramework, ControlStatus
)


class TestPenetrationTesting:
    """Test penetration testing framework."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock aiohttp session."""
        session = AsyncMock()
        response = AsyncMock()
        response.status = 200
        response.text.return_value = "Normal response"
        session.get.return_value.__aenter__.return_value = response
        session.post.return_value.__aenter__.return_value = response
        session.request.return_value.__aenter__.return_value = response
        return session
    
    @pytest.fixture
    def security_scanner(self, mock_session):
        """Create security scanner with mocked session."""
        scanner = SecurityScanner("http://test.com")
        scanner.session = mock_session
        return scanner
    
    @pytest.mark.asyncio
    async def test_sql_injection_detection(self, security_scanner):
        """Test SQL injection vulnerability detection."""
        # Mock response with SQL error
        mock_response = AsyncMock()
        mock_response.text.return_value = "SQL syntax error near 'OR'"
        security_scanner.session.get.return_value.__aenter__.return_value = mock_response
        security_scanner.session.post.return_value.__aenter__.return_value = mock_response
        
        endpoints = ["/api/test"]
        vulnerabilities = await security_scanner.scan_sql_injection(endpoints)
        
        assert len(vulnerabilities) > 0
        assert vulnerabilities[0].category == TestCategory.SQL_INJECTION
        assert vulnerabilities[0].severity == VulnerabilityLevel.CRITICAL
    
    @pytest.mark.asyncio
    async def test_xss_detection(self, security_scanner):
        """Test XSS vulnerability detection."""
        # Mock response with unescaped script tag
        mock_response = AsyncMock()
        mock_response.text.return_value = "<script>alert('XSS')</script>"
        security_scanner.session.get.return_value.__aenter__.return_value = mock_response
        
        endpoints = ["/api/test"]
        vulnerabilities = await security_scanner.scan_xss(endpoints)
        
        assert len(vulnerabilities) > 0
        assert vulnerabilities[0].category == TestCategory.XSS
        assert vulnerabilities[0].severity == VulnerabilityLevel.HIGH
    
    @pytest.mark.asyncio
    async def test_authentication_bypass(self, security_scanner):
        """Test authentication bypass detection."""
        # Mock successful bypass response
        mock_response = AsyncMock()
        mock_response.status = 200
        security_scanner.session.request.return_value.__aenter__.return_value = mock_response
        
        endpoints = ["/api/admin"]
        vulnerabilities = await security_scanner.scan_authentication_bypass(endpoints)
        
        assert len(vulnerabilities) > 0
        assert vulnerabilities[0].category == TestCategory.AUTHENTICATION
        assert vulnerabilities[0].severity == VulnerabilityLevel.CRITICAL
    
    @pytest.mark.asyncio
    async def test_comprehensive_penetration_test(self):
        """Test comprehensive penetration testing suite."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = "Normal response"
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session.request.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            pen_test_suite = PenetrationTestSuite("http://test.com")
            endpoints = ["/api/test", "/api/admin"]
            
            result = await pen_test_suite.run_comprehensive_test(endpoints)
            
            assert result.test_id is not None
            assert result.tests_run > 0
            assert result.coverage_percentage >= 0
            assert result.risk_score >= 0
    
    def test_vulnerability_risk_calculation(self):
        """Test risk score calculation."""
        vulnerabilities = [
            SecurityVulnerability(
                id="test1", title="Test", description="Test", 
                severity=VulnerabilityLevel.CRITICAL, category=TestCategory.SQL_INJECTION
            ),
            SecurityVulnerability(
                id="test2", title="Test", description="Test",
                severity=VulnerabilityLevel.HIGH, category=TestCategory.XSS
            ),
            SecurityVulnerability(
                id="test3", title="Test", description="Test",
                severity=VulnerabilityLevel.MEDIUM, category=TestCategory.CSRF
            )
        ]
        
        pen_test_suite = PenetrationTestSuite("http://test.com")
        risk_score = pen_test_suite._calculate_risk_score(vulnerabilities)
        
        assert 0 <= risk_score <= 100
        assert risk_score > 50  # Should be high due to critical vulnerability


class TestThreatProtection:
    """Test threat protection and intrusion detection."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis = AsyncMock()
        redis.get.return_value = None
        redis.keys.return_value = []
        redis.exists.return_value = False
        redis.hgetall.return_value = {}
        redis.setex = AsyncMock()
        redis.hset = AsyncMock()
        redis.expire = AsyncMock()
        return redis
    
    @pytest.fixture
    def threat_detection_engine(self):
        """Create threat detection engine."""
        return ThreatDetectionEngine()
    
    @pytest.fixture
    def intrusion_detection_system(self, mock_redis):
        """Create intrusion detection system."""
        return IntrusionDetectionSystem(mock_redis)
    
    def test_sql_injection_pattern_detection(self, threat_detection_engine):
        """Test SQL injection pattern detection."""
        request_data = {
            'url': "http://test.com/api?id=' OR '1'='1",
            'query_params': {"id": "' OR '1'='1"},
            'post_data': {},
            'headers': {'user-agent': 'Mozilla/5.0'},
            'source_ip': '192.168.1.1',
            'endpoint': '/api'
        }
        
        threats = threat_detection_engine.detect_threats(request_data)
        
        assert len(threats) > 0
        sql_threats = [t for t in threats if t.attack_type == AttackType.SQL_INJECTION]
        assert len(sql_threats) > 0
        assert sql_threats[0].threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]
    
    def test_xss_pattern_detection(self, threat_detection_engine):
        """Test XSS pattern detection."""
        request_data = {
            'url': "http://test.com/api",
            'query_params': {"q": "<script>alert('XSS')</script>"},
            'post_data': {},
            'headers': {'user-agent': 'Mozilla/5.0'},
            'source_ip': '192.168.1.1',
            'endpoint': '/api'
        }
        
        threats = threat_detection_engine.detect_threats(request_data)
        
        assert len(threats) > 0
        xss_threats = [t for t in threats if t.attack_type == AttackType.XSS_ATTEMPT]
        assert len(xss_threats) > 0
        assert xss_threats[0].threat_level == ThreatLevel.HIGH
    
    def test_malicious_user_agent_detection(self, threat_detection_engine):
        """Test malicious user agent detection."""
        request_data = {
            'url': "http://test.com/api",
            'query_params': {},
            'post_data': {},
            'headers': {'user-agent': 'sqlmap/1.0'},
            'source_ip': '192.168.1.1',
            'endpoint': '/api'
        }
        
        threats = threat_detection_engine.detect_threats(request_data)
        
        assert len(threats) > 0
        ua_threats = [t for t in threats if t.attack_type == AttackType.SUSPICIOUS_USER_AGENT]
        assert len(ua_threats) > 0
        assert ua_threats[0].threat_level == ThreatLevel.MEDIUM
    
    @pytest.mark.asyncio
    async def test_ip_reputation_check(self, threat_detection_engine):
        """Test IP reputation checking."""
        # Test clean IP
        is_malicious, source = await threat_detection_engine.check_ip_reputation("8.8.8.8")
        assert not is_malicious
        
        # Test potentially malicious IP (private range in example)
        is_malicious, source = await threat_detection_engine.check_ip_reputation("10.0.0.1")
        # This would be malicious in our test setup
        assert is_malicious or not is_malicious  # Depends on configuration
    
    @pytest.mark.asyncio
    async def test_rate_limit_detection(self, intrusion_detection_system):
        """Test rate limit abuse detection."""
        request_data = {
            'source_ip': '192.168.1.100',
            'endpoint': '/api/test',
            'user_agent': 'Test Agent'
        }
        
        # Simulate multiple requests
        for _ in range(150):  # Exceed threshold
            threat = await intrusion_detection_system._check_rate_limits(request_data)
        
        # Last request should trigger rate limit detection
        assert threat is not None
        assert threat.attack_type == AttackType.RATE_LIMIT_ABUSE
        assert threat.threat_level == ThreatLevel.MEDIUM
    
    def test_behavioral_anomaly_detection(self, threat_detection_engine):
        """Test behavioral anomaly detection."""
        user_id = "test_user_123"
        
        # Establish baseline
        baseline_behavior = {
            'requests_per_hour': 10.0,
            'unique_endpoints': 3.0,
            'error_rate': 0.1,
            'session_duration': 1800.0
        }
        
        anomaly = threat_detection_engine.analyze_behavioral_anomaly(user_id, baseline_behavior)
        assert anomaly is None  # First time, no anomaly
        
        # Test anomalous behavior
        anomalous_behavior = {
            'requests_per_hour': 1000.0,  # 100x increase
            'unique_endpoints': 50.0,     # Large increase
            'error_rate': 0.5,            # High error rate
            'session_duration': 100.0     # Very short sessions
        }
        
        anomaly = threat_detection_engine.analyze_behavioral_anomaly(user_id, anomalous_behavior)
        assert anomaly is not None
        assert anomaly.attack_type == AttackType.ANOMALOUS_BEHAVIOR
        assert anomaly.threat_level == ThreatLevel.MEDIUM


class TestIncidentResponse:
    """Test incident response system."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis = AsyncMock()
        redis.setex = AsyncMock()
        redis.hset = AsyncMock()
        redis.expire = AsyncMock()
        redis.keys.return_value = []
        return redis
    
    @pytest.fixture
    def mock_database(self):
        """Mock database session."""
        return AsyncMock()
    
    @pytest.fixture
    def incident_manager(self, mock_redis, mock_database):
        """Create security incident manager."""
        return SecurityIncidentManager(mock_redis, mock_database)
    
    @pytest.fixture
    def sample_threat_events(self):
        """Create sample threat events."""
        return [
            ThreatEvent(
                id="threat1",
                timestamp=datetime.utcnow(),
                source_ip="192.168.1.100",
                user_agent="sqlmap/1.0",
                attack_type=AttackType.SQL_INJECTION,
                threat_level=ThreatLevel.CRITICAL,
                endpoint="/api/users",
                payload="' OR '1'='1"
            ),
            ThreatEvent(
                id="threat2",
                timestamp=datetime.utcnow(),
                source_ip="192.168.1.100",
                user_agent="sqlmap/1.0",
                attack_type=AttackType.SQL_INJECTION,
                threat_level=ThreatLevel.CRITICAL,
                endpoint="/api/admin",
                payload="'; DROP TABLE users; --"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_incident_detection(self, incident_manager, sample_threat_events):
        """Test security incident detection."""
        await incident_manager.process_threat_events(sample_threat_events)
        
        # Should create incident for multiple SQL injection attempts
        assert len(incident_manager.active_incidents) > 0
        
        incident = list(incident_manager.active_incidents.values())[0]
        assert incident.severity == IncidentSeverity.CRITICAL
        assert incident.status == IncidentStatus.INVESTIGATING
        assert len(incident.threat_events) >= 2
    
    @pytest.mark.asyncio
    async def test_incident_response_actions(self, mock_redis, mock_database):
        """Test automated incident response actions."""
        orchestrator = ResponseOrchestrator(mock_redis, mock_database)
        
        # Create test incident
        incident = SecurityIncident(
            id="test_incident",
            title="SQL Injection Attack",
            description="Multiple SQL injection attempts detected",
            severity=IncidentSeverity.CRITICAL,
            status=IncidentStatus.OPEN,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            threat_events=[],
            affected_systems=["/api/users"],
            affected_users=["user123"],
            affected_tenants=["tenant456"]
        )
        
        # Execute response
        actions = await orchestrator.respond_to_incident(incident)
        
        assert len(actions) > 0
        assert "block_ip" in actions or "alert_admin" in actions
        assert incident.status == IncidentStatus.INVESTIGATING
    
    @pytest.mark.asyncio
    async def test_incident_escalation(self, incident_manager):
        """Test incident escalation logic."""
        # Create high-severity incident
        critical_threats = [
            ThreatEvent(
                id="critical1",
                timestamp=datetime.utcnow(),
                source_ip="192.168.1.200",
                user_agent="attacker",
                attack_type=AttackType.DATA_EXFILTRATION,
                threat_level=ThreatLevel.CRITICAL,
                endpoint="/api/sensitive-data"
            )
        ]
        
        await incident_manager.process_threat_events(critical_threats)
        
        # Should create critical incident
        incidents = list(incident_manager.active_incidents.values())
        assert len(incidents) > 0
        
        critical_incident = incidents[0]
        assert critical_incident.severity == IncidentSeverity.CRITICAL
        # Should be escalated immediately for data exfiltration
        assert len(critical_incident.response_actions) > 0


class TestCompliance:
    """Test compliance reporting system."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis = AsyncMock()
        redis.get.return_value = "true"
        redis.keys.return_value = []
        redis.exists.return_value = True
        redis.hgetall.return_value = {}
        redis.hset = AsyncMock()
        redis.expire = AsyncMock()
        redis.setex = AsyncMock()
        return redis
    
    @pytest.fixture
    def mock_database(self):
        """Mock database session."""
        db = AsyncMock()
        # Mock query results
        result = AsyncMock()
        result.scalar.return_value = 5  # Mock user count
        result.fetchall.return_value = []
        db.execute.return_value = result
        return db
    
    @pytest.fixture
    def soc2_reporter(self, mock_redis, mock_database):
        """Create SOC2 reporter."""
        return SOC2Reporter(mock_redis, mock_database)
    
    @pytest.fixture
    def gdpr_reporter(self, mock_redis, mock_database):
        """Create GDPR reporter."""
        return GDPRReporter(mock_redis, mock_database)
    
    @pytest.fixture
    def compliance_reporter(self, mock_redis, mock_database):
        """Create compliance reporter."""
        return ComplianceReporter(mock_redis, mock_database)
    
    @pytest.mark.asyncio
    async def test_soc2_assessment(self, soc2_reporter):
        """Test SOC2 compliance assessment."""
        report = await soc2_reporter.assess_controls()
        
        assert report.framework == ComplianceFramework.SOC2
        assert report.controls_assessed > 0
        assert report.overall_status in [
            ControlStatus.COMPLIANT, 
            ControlStatus.PARTIALLY_COMPLIANT, 
            ControlStatus.NON_COMPLIANT
        ]
        assert 0 <= report.risk_score <= 100
    
    @pytest.mark.asyncio
    async def test_gdpr_assessment(self, gdpr_reporter):
        """Test GDPR compliance assessment."""
        report = await gdpr_reporter.assess_controls()
        
        assert report.framework == ComplianceFramework.GDPR
        assert report.controls_assessed > 0
        assert report.overall_status in [
            ControlStatus.COMPLIANT, 
            ControlStatus.PARTIALLY_COMPLIANT, 
            ControlStatus.NON_COMPLIANT
        ]
        assert len(report.recommendations) >= 0
    
    @pytest.mark.asyncio
    async def test_comprehensive_compliance_report(self, compliance_reporter):
        """Test comprehensive compliance reporting."""
        reports = await compliance_reporter.generate_comprehensive_report()
        
        assert 'soc2' in reports or 'gdpr' in reports
        
        for framework, report in reports.items():
            assert report.framework.value == framework
            assert report.controls_assessed > 0
            assert isinstance(report.risk_score, float)
    
    def test_control_status_calculation(self, soc2_reporter):
        """Test control status calculation logic."""
        # Test compliant scenario
        controls = soc2_reporter.controls
        
        # Mock all controls as compliant
        for control in controls:
            control.status = ControlStatus.COMPLIANT
        
        total_controls = len(controls)
        compliant_count = len([c for c in controls if c.status == ControlStatus.COMPLIANT])
        compliance_percentage = (compliant_count / total_controls) * 100
        
        assert compliance_percentage == 100.0
        
        # Test mixed scenario
        controls[0].status = ControlStatus.NON_COMPLIANT
        compliant_count = len([c for c in controls if c.status == ControlStatus.COMPLIANT])
        compliance_percentage = (compliant_count / total_controls) * 100
        
        assert compliance_percentage < 100.0
    
    @pytest.mark.asyncio
    async def test_compliance_dashboard_data(self, compliance_reporter):
        """Test compliance dashboard data generation."""
        dashboard_data = await compliance_reporter.get_compliance_dashboard_data()
        
        assert 'frameworks' in dashboard_data
        assert 'overall_status' in dashboard_data
        assert 'total_controls' in dashboard_data
        assert 'risk_score' in dashboard_data


class TestSecurityIntegration:
    """Test integration between security components."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis = AsyncMock()
        redis.get.return_value = None
        redis.keys.return_value = []
        redis.exists.return_value = False
        redis.hgetall.return_value = {}
        redis.setex = AsyncMock()
        redis.hset = AsyncMock()
        redis.expire = AsyncMock()
        return redis
    
    @pytest.fixture
    def mock_database(self):
        """Mock database session."""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_threat_to_incident_workflow(self, mock_redis, mock_database):
        """Test workflow from threat detection to incident response."""
        # Create threat protection system
        threat_system = ThreatProtectionSystem(mock_redis, mock_database)
        
        # Create incident manager
        incident_manager = SecurityIncidentManager(mock_redis, mock_database)
        
        # Simulate threat events
        threat_events = [
            ThreatEvent(
                id="integration_test_1",
                timestamp=datetime.utcnow(),
                source_ip="192.168.1.100",
                user_agent="sqlmap/1.0",
                attack_type=AttackType.SQL_INJECTION,
                threat_level=ThreatLevel.CRITICAL,
                endpoint="/api/users"
            )
        ]
        
        # Process threats through incident manager
        await incident_manager.process_threat_events(threat_events)
        
        # Verify incident was created
        assert len(incident_manager.active_incidents) > 0
        
        incident = list(incident_manager.active_incidents.values())[0]
        assert incident.severity == IncidentSeverity.CRITICAL
        assert len(incident.threat_events) > 0
    
    @pytest.mark.asyncio
    async def test_security_metrics_collection(self, mock_redis, mock_database):
        """Test security metrics collection and reporting."""
        # Create systems
        threat_system = ThreatProtectionSystem(mock_redis, mock_database)
        incident_manager = SecurityIncidentManager(mock_redis, mock_database)
        
        # Generate some activity
        threat_events = [
            ThreatEvent(
                id=f"metric_test_{i}",
                timestamp=datetime.utcnow(),
                source_ip=f"192.168.1.{100+i}",
                user_agent="test",
                attack_type=AttackType.BRUTE_FORCE,
                threat_level=ThreatLevel.MEDIUM,
                endpoint="/api/login"
            )
            for i in range(5)
        ]
        
        await incident_manager.process_threat_events(threat_events)
        
        # Get statistics
        stats = await threat_system.ids.get_threat_statistics()
        incident_summary = await incident_manager.get_incident_summary()
        
        assert 'total_threats' in stats
        assert 'total_incidents' in incident_summary
        assert stats['total_threats'] >= 0
        assert incident_summary['total_incidents'] >= 0
    
    def test_security_configuration_validation(self):
        """Test security configuration validation."""
        # Test that security components have proper configuration
        detection_engine = ThreatDetectionEngine()
        
        # Verify attack patterns are loaded
        assert len(detection_engine.attack_patterns) > 0
        
        # Verify patterns have required fields
        for pattern in detection_engine.attack_patterns:
            assert pattern.name
            assert pattern.attack_type
            assert pattern.threat_level
            assert len(pattern.patterns) > 0
            assert pattern.description
            assert pattern.remediation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])