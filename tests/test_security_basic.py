"""
Basic tests for the security framework to verify implementation.
"""

import pytest
from datetime import datetime
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import directly from modules to avoid __init__.py issues
import ai_karen_engine.security.penetration_testing as pen_testing
import ai_karen_engine.security.compliance as compliance

SecurityVulnerability = pen_testing.SecurityVulnerability
VulnerabilityLevel = pen_testing.VulnerabilityLevel
TestCategory = pen_testing.TestCategory
PenetrationTestSuite = pen_testing.PenetrationTestSuite

ComplianceFramework = compliance.ComplianceFramework
ControlStatus = compliance.ControlStatus
ComplianceControl = compliance.ComplianceControl


def test_security_vulnerability_creation():
    """Test creating security vulnerability objects."""
    vuln = SecurityVulnerability(
        id="test_vuln_1",
        title="Test SQL Injection",
        description="Test vulnerability for SQL injection",
        severity=VulnerabilityLevel.CRITICAL,
        category=TestCategory.SQL_INJECTION,
        affected_endpoint="/api/test",
        proof_of_concept="' OR '1'='1",
        remediation="Use parameterized queries"
    )
    
    assert vuln.id == "test_vuln_1"
    assert vuln.severity == VulnerabilityLevel.CRITICAL
    assert vuln.category == TestCategory.SQL_INJECTION
    assert vuln.affected_endpoint == "/api/test"


def test_vulnerability_risk_calculation():
    """Test risk score calculation for vulnerabilities."""
    vulnerabilities = [
        SecurityVulnerability(
            id="test1", title="Critical Test", description="Test", 
            severity=VulnerabilityLevel.CRITICAL, category=TestCategory.SQL_INJECTION
        ),
        SecurityVulnerability(
            id="test2", title="High Test", description="Test",
            severity=VulnerabilityLevel.HIGH, category=TestCategory.XSS
        ),
        SecurityVulnerability(
            id="test3", title="Medium Test", description="Test",
            severity=VulnerabilityLevel.MEDIUM, category=TestCategory.CSRF
        )
    ]
    
    pen_test_suite = PenetrationTestSuite("http://test.com")
    risk_score = pen_test_suite._calculate_risk_score(vulnerabilities)
    
    assert 0 <= risk_score <= 100
    assert risk_score > 50  # Should be high due to critical vulnerability


def test_compliance_control_creation():
    """Test creating compliance control objects."""
    control = ComplianceControl(
        id="CC6.1",
        framework=ComplianceFramework.SOC2,
        title="Access Controls",
        description="Test access control",
        requirement="Implement access controls",
        control_type="security",
        status=ControlStatus.COMPLIANT,
        risk_level="high"
    )
    
    assert control.id == "CC6.1"
    assert control.framework == ComplianceFramework.SOC2
    assert control.status == ControlStatus.COMPLIANT
    assert control.risk_level == "high"


def test_vulnerability_levels():
    """Test vulnerability severity levels."""
    levels = [
        VulnerabilityLevel.CRITICAL,
        VulnerabilityLevel.HIGH,
        VulnerabilityLevel.MEDIUM,
        VulnerabilityLevel.LOW,
        VulnerabilityLevel.INFO
    ]
    
    assert len(levels) == 5
    assert VulnerabilityLevel.CRITICAL.value == "critical"
    assert VulnerabilityLevel.HIGH.value == "high"


def test_test_categories():
    """Test security test categories."""
    categories = [
        TestCategory.SQL_INJECTION,
        TestCategory.XSS,
        TestCategory.AUTHENTICATION,
        TestCategory.AUTHORIZATION,
        TestCategory.SESSION_MANAGEMENT
    ]
    
    assert len(categories) == 5
    assert TestCategory.SQL_INJECTION.value == "sql_injection"
    assert TestCategory.XSS.value == "xss"


def test_compliance_frameworks():
    """Test compliance framework enumeration."""
    frameworks = [
        ComplianceFramework.SOC2,
        ComplianceFramework.GDPR,
        ComplianceFramework.HIPAA,
        ComplianceFramework.PCI_DSS
    ]
    
    assert len(frameworks) == 4
    assert ComplianceFramework.SOC2.value == "soc2"
    assert ComplianceFramework.GDPR.value == "gdpr"


def test_control_status():
    """Test compliance control status enumeration."""
    statuses = [
        ControlStatus.COMPLIANT,
        ControlStatus.NON_COMPLIANT,
        ControlStatus.PARTIALLY_COMPLIANT,
        ControlStatus.NOT_APPLICABLE,
        ControlStatus.UNDER_REVIEW
    ]
    
    assert len(statuses) == 5
    assert ControlStatus.COMPLIANT.value == "compliant"
    assert ControlStatus.NON_COMPLIANT.value == "non_compliant"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])