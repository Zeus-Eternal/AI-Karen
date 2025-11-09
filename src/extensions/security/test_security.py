"""
Tests for extension security features
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import (
    Base, ExtensionSignature, ExtensionAuditLog, ExtensionAccessPolicy,
    ExtensionVulnerability, AuditEventType, SecurityLevel, VulnerabilityStatus
)
from .code_signing import ExtensionCodeSigner, ExtensionVerifier, ExtensionSignatureManager
from .audit_logger import ExtensionAuditLogger, ExtensionComplianceReporter
from .access_control import ExtensionAccessControlManager
from .vulnerability_scanner import ExtensionVulnerabilityScanner, SecurityScanRequest
from .service import ExtensionSecurityService


@pytest.fixture
def db_session():
    """Create test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def temp_extension_dir():
    """Create temporary extension directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        ext_dir = Path(temp_dir) / "test_extension"
        ext_dir.mkdir()
        
        # Create extension manifest
        manifest = {
            "name": "test-extension",
            "version": "1.0.0",
            "permissions": {
                "data_access": ["read", "write"],
                "network_access": ["outbound_http"]
            }
        }
        
        with open(ext_dir / "extension.json", "w") as f:
            json.dump(manifest, f)
        
        # Create some Python files
        with open(ext_dir / "__init__.py", "w") as f:
            f.write("# Test extension\n")
        
        with open(ext_dir / "main.py", "w") as f:
            f.write("""
import requests

def fetch_data():
    return requests.get("https://api.example.com/data")

def process_data(data):
    return data.upper()
""")
        
        yield ext_dir


@pytest.fixture
def temp_keys_dir():
    """Create temporary keys directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        keys_dir = Path(temp_dir)
        yield keys_dir


class TestExtensionCodeSigning:
    """Test code signing functionality"""
    
    def test_generate_key_pair(self, temp_keys_dir):
        """Test key pair generation"""
        signer = ExtensionCodeSigner()
        
        private_key_path, public_key_path = signer.generate_key_pair(
            temp_keys_dir, "test_key"
        )
        
        assert Path(private_key_path).exists()
        assert Path(public_key_path).exists()
        assert "test_key_private.pem" in private_key_path
        assert "test_key_public.pem" in public_key_path
    
    def test_sign_extension(self, temp_extension_dir, temp_keys_dir):
        """Test extension signing"""
        # Generate keys
        signer = ExtensionCodeSigner()
        private_key_path, public_key_path = signer.generate_key_pair(
            temp_keys_dir, "test_key"
        )
        
        # Initialize signer with private key
        signer = ExtensionCodeSigner(private_key_path, "test_key")
        
        # Sign extension
        signature_hash = signer.sign_extension(
            extension_path=temp_extension_dir,
            extension_name="test-extension",
            extension_version="1.0.0",
            signer_id="test_signer"
        )
        
        assert signature_hash
        assert (temp_extension_dir / ".signature").exists()
    
    def test_verify_extension(self, temp_extension_dir, temp_keys_dir):
        """Test extension verification"""
        # Generate keys and sign extension
        signer = ExtensionCodeSigner()
        private_key_path, public_key_path = signer.generate_key_pair(
            temp_keys_dir, "test_key"
        )
        
        signer = ExtensionCodeSigner(private_key_path, "test_key")
        signer.sign_extension(
            extension_path=temp_extension_dir,
            extension_name="test-extension",
            extension_version="1.0.0",
            signer_id="test_signer"
        )
        
        # Verify extension
        verifier = ExtensionVerifier(temp_keys_dir)
        is_valid, verification_data = verifier.verify_extension(temp_extension_dir)
        
        assert is_valid
        assert verification_data['signature_valid']
        assert verification_data['hash_valid']
    
    def test_signature_manager(self, db_session):
        """Test signature database management"""
        manager = ExtensionSignatureManager(db_session)
        
        # Store signature
        from .models import ExtensionSignatureCreate
        signature_data = ExtensionSignatureCreate(
            extension_name="test-extension",
            extension_version="1.0.0",
            signature_hash="test_hash",
            public_key_id="test_key",
            signed_by="test_signer"
        )
        
        stored_signature = manager.store_signature(signature_data)
        assert stored_signature.extension_name == "test-extension"
        
        # Retrieve signature
        retrieved_signature = manager.get_signature("test-extension", "1.0.0")
        assert retrieved_signature is not None
        assert retrieved_signature.signature_hash == "test_hash"


class TestExtensionAuditLogger:
    """Test audit logging functionality"""
    
    def test_log_event(self, db_session):
        """Test basic event logging"""
        audit_logger = ExtensionAuditLogger(db_session)
        
        event_id = audit_logger.log_event(
            extension_name="test-extension",
            tenant_id="test-tenant",
            event_type=AuditEventType.EXTENSION_INSTALL,
            event_data={"version": "1.0.0"},
            user_id="test-user"
        )
        
        assert event_id > 0
        
        # Retrieve logs
        logs = audit_logger.get_audit_logs(tenant_id="test-tenant")
        assert len(logs) == 1
        assert logs[0].extension_name == "test-extension"
    
    def test_audit_summary(self, db_session):
        """Test audit summary generation"""
        audit_logger = ExtensionAuditLogger(db_session)
        
        # Log some events
        audit_logger.log_extension_install(
            "test-extension", "1.0.0", "test-tenant", "test-user"
        )
        audit_logger.log_security_violation(
            "test-extension", "test-tenant", "access_denied", {"resource": "data"}
        )
        
        # Generate summary
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=1)
        
        summary = audit_logger.get_audit_summary("test-tenant", start_date, end_date)
        
        assert summary['total_events'] == 2
        assert summary['high_risk_events'] == 1  # Security violation
    
    def test_compliance_reporter(self, db_session):
        """Test compliance report generation"""
        audit_logger = ExtensionAuditLogger(db_session)
        compliance_reporter = ExtensionComplianceReporter(db_session, audit_logger)
        
        # Log some events
        audit_logger.log_extension_install(
            "test-extension", "1.0.0", "test-tenant", "test-user"
        )
        
        # Generate report
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        report = compliance_reporter.generate_compliance_report(
            tenant_id="test-tenant",
            report_type="security",
            start_date=start_date,
            end_date=end_date
        )
        
        assert report.tenant_id == "test-tenant"
        assert report.report_type == "security"
        assert report.compliance_score >= 0


class TestExtensionAccessControl:
    """Test access control functionality"""
    
    def test_create_policy(self, db_session):
        """Test access policy creation"""
        access_manager = ExtensionAccessControlManager(db_session)
        
        from .models import AccessPolicy, AccessPolicyRule
        policy = AccessPolicy(
            extension_name="test-extension",
            tenant_id="test-tenant",
            policy_name="test-policy",
            rules=[
                AccessPolicyRule(
                    resource="data/*",
                    action="read",
                    effect="allow"
                )
            ]
        )
        
        created_policy = access_manager.create_policy(policy, "test-user")
        assert created_policy.policy_name == "test-policy"
    
    def test_check_access(self, db_session):
        """Test access checking"""
        access_manager = ExtensionAccessControlManager(db_session)
        
        # Create policy
        from .models import AccessPolicy, AccessPolicyRule
        policy = AccessPolicy(
            extension_name="test-extension",
            tenant_id="test-tenant",
            policy_name="test-policy",
            rules=[
                AccessPolicyRule(
                    resource="data/*",
                    action="read",
                    effect="allow"
                )
            ]
        )
        
        access_manager.create_policy(policy, "test-user")
        
        # Check access
        allowed = access_manager.check_access(
            extension_name="test-extension",
            tenant_id="test-tenant",
            user_id="test-user",
            resource="data/users",
            action="read"
        )
        
        assert allowed
        
        # Check denied access
        denied = access_manager.check_access(
            extension_name="test-extension",
            tenant_id="test-tenant",
            user_id="test-user",
            resource="data/users",
            action="delete"
        )
        
        assert not denied


class TestExtensionVulnerabilityScanner:
    """Test vulnerability scanning functionality"""
    
    def test_scan_extension(self, db_session, temp_extension_dir):
        """Test extension vulnerability scanning"""
        scanner = ExtensionVulnerabilityScanner(db_session)
        
        # Create a file with potential vulnerability
        vuln_file = temp_extension_dir / "vulnerable.py"
        with open(vuln_file, "w") as f:
            f.write("""
import os

def dangerous_function(user_input):
    # This is a potential code injection vulnerability
    eval(user_input)
    
def another_issue():
    os.system("rm -rf /")
""")
        
        scan_request = SecurityScanRequest(
            extension_name="test-extension",
            extension_version="1.0.0",
            scan_types=["code"],
            deep_scan=False
        )
        
        result = scanner.scan_extension(
            temp_extension_dir, "test-extension", "1.0.0", scan_request
        )
        
        assert len(result.vulnerabilities) > 0
        assert result.security_score < 100
        
        # Check for specific vulnerabilities
        vuln_ids = [v.vulnerability_id for v in result.vulnerabilities]
        assert any("CODE_INJECTION" in vid for vid in vuln_ids)
    
    def test_dependency_scanning(self, db_session, temp_extension_dir):
        """Test dependency vulnerability scanning"""
        scanner = ExtensionVulnerabilityScanner(db_session)
        
        # Create requirements.txt with vulnerable package
        req_file = temp_extension_dir / "requirements.txt"
        with open(req_file, "w") as f:
            f.write("requests==2.19.0\n")  # Old version with known vulnerabilities
        
        scan_request = SecurityScanRequest(
            extension_name="test-extension",
            extension_version="1.0.0",
            scan_types=["dependencies"],
            deep_scan=False
        )
        
        result = scanner.scan_extension(
            temp_extension_dir, "test-extension", "1.0.0", scan_request
        )
        
        # Should detect vulnerable requests version
        dep_vulns = [v for v in result.vulnerabilities if v.vulnerability_id.startswith("DEP_")]
        assert len(dep_vulns) > 0


class TestExtensionSecurityService:
    """Test main security service"""
    
    @pytest.fixture
    def security_service(self, db_session):
        """Create security service instance"""
        return ExtensionSecurityService(db_session)
    
    @patch('src.core.extensions.security.config.security_config.vulnerability_scanning_enabled', True)
    @patch('src.core.extensions.security.config.security_config.scan_on_install', True)
    async def test_secure_extension_installation(self, security_service, temp_extension_dir):
        """Test secure extension installation process"""
        security_report = await security_service.secure_extension_installation(
            extension_path=temp_extension_dir,
            extension_name="test-extension",
            extension_version="1.0.0",
            tenant_id="test-tenant",
            user_id="test-user"
        )
        
        assert security_report['extension_name'] == "test-extension"
        assert 'vulnerability_scan' in security_report['checks_performed']
        assert security_report['security_score'] >= 0
    
    async def test_security_audit(self, security_service):
        """Test security audit functionality"""
        audit_report = await security_service.perform_security_audit(
            tenant_id="test-tenant",
            days=30
        )
        
        assert audit_report['tenant_id'] == "test-tenant"
        assert 'audit_summary' in audit_report
        assert 'vulnerability_summary' in audit_report
        assert 'security_score' in audit_report
    
    async def test_compliance_report(self, security_service):
        """Test compliance report generation"""
        report = await security_service.generate_compliance_report(
            tenant_id="test-tenant",
            report_type="security",
            days=30
        )
        
        assert report['tenant_id'] == "test-tenant"
        assert report['report_type'] == "security"
        assert 'compliance_score' in report


if __name__ == "__main__":
    pytest.main([__file__])