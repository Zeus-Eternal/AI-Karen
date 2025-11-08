"""
Enterprise Security Features for Extensions System

This module provides enterprise-grade security features including:
- Extension code signing and verification
- Audit logging and compliance reporting
- Access control policies
- Vulnerability scanning
"""

from .code_signing import ExtensionCodeSigner, ExtensionVerifier
from .audit_logger import ExtensionAuditLogger
from .access_control import ExtensionAccessControlManager
from .vulnerability_scanner import ExtensionVulnerabilityScanner
from .compliance_reporter import ExtensionComplianceReporter

__all__ = [
    'ExtensionCodeSigner',
    'ExtensionVerifier', 
    'ExtensionAuditLogger',
    'ExtensionAccessControlManager',
    'ExtensionVulnerabilityScanner',
    'ExtensionComplianceReporter'
]