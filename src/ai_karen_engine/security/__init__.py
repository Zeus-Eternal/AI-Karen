"""
Comprehensive Security System for CoPilot Architecture.

This module provides enhanced security capabilities including:
- Multi-factor authentication (MFA)
- Device verification and fingerprinting
- Security monitoring and threat detection
- Data encryption and protection
- Security policies and configuration management
- Vulnerability scanning and security testing
"""

from .auth_service import (
    EnhancedAuthService,
    MFAMethod,
    DeviceInfo,
    SecurityEvent,
    ThreatLevel,
)
from .mfa_service import (
    MFAService,
    TOTPManager,
    SMSManager,
    EmailManager,
    BackupCodeManager,
)
from .device_verification import (
    DeviceVerificationService,
    DeviceFingerprint,
    DeviceTrustLevel,
)
from .security_monitoring import (
    SecurityMonitoringService,
    ThreatDetector,
    AnomalyDetector,
    SecurityIncident,
)
from .encryption_service import (
    EncryptionService,
    DataProtectionService,
    KeyManager,
    EncryptionAlgorithm,
)
from .security_policy import (
    SecurityPolicyService,
    SecurityPolicy,
    PolicyRule,
    PolicyEnforcement,
)
from .vulnerability_scanner import (
    VulnerabilityScanner,
    VulnerabilityConfig,
    VulnerabilityFinding,
    SecurityTest,
    SecurityTestSuite,
    VulnerabilitySeverity,
    VulnerabilityCategory,
    TestType,
    TestStatus,
)
from .compliance_service import (
    ComplianceService,
    ComplianceFramework,
    ComplianceReport,
    AuditTrail,
)

__all__ = [
    # Enhanced Authentication
    "EnhancedAuthService",
    "MFAMethod",
    "DeviceInfo",
    "SecurityEvent",
    "ThreatLevel",
    
    # Multi-Factor Authentication
    "MFAService",
    "TOTPManager",
    "SMSManager",
    "EmailManager",
    "BackupCodeManager",
    
    # Device Verification
    "DeviceVerificationService",
    "DeviceFingerprint",
    "DeviceTrustLevel",
    
    # Security Monitoring
    "SecurityMonitoringService",
    "ThreatDetector",
    "AnomalyDetector",
    "SecurityIncident",
    
    # Encryption and Data Protection
    "EncryptionService",
    "DataProtectionService",
    "KeyManager",
    "EncryptionAlgorithm",
    
    # Security Policy
    "SecurityPolicyService",
    "SecurityPolicy",
    "PolicyRule",
    "PolicyEnforcement",
    
    # Vulnerability Scanning
    "VulnerabilityScanner",
    "VulnerabilityConfig",
    "VulnerabilityFinding",
    "SecurityTest",
    "SecurityTestSuite",
    "VulnerabilitySeverity",
    "VulnerabilityCategory",
    "TestType",
    "TestStatus",
    
    # Compliance
    "ComplianceService",
    "ComplianceFramework",
    "ComplianceReport",
    "AuditTrail",
]