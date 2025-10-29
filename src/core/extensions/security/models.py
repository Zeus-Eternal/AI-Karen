"""
Security models for extension enterprise features
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class SecurityLevel(str, Enum):
    """Security levels for extensions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VulnerabilityStatus(str, Enum):
    """Status of vulnerability findings"""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    FIXED = "fixed"
    FALSE_POSITIVE = "false_positive"


class AuditEventType(str, Enum):
    """Types of audit events"""
    EXTENSION_INSTALL = "extension_install"
    EXTENSION_UNINSTALL = "extension_uninstall"
    EXTENSION_ENABLE = "extension_enable"
    EXTENSION_DISABLE = "extension_disable"
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    DATA_ACCESS = "data_access"
    API_CALL = "api_call"
    SECURITY_VIOLATION = "security_violation"
    VULNERABILITY_DETECTED = "vulnerability_detected"


# Database Models
class ExtensionSignature(Base):
    """Extension code signature records"""
    __tablename__ = "extension_signatures"
    
    id = Column(Integer, primary_key=True)
    extension_name = Column(String(255), nullable=False)
    extension_version = Column(String(50), nullable=False)
    signature_hash = Column(String(512), nullable=False)
    public_key_id = Column(String(255), nullable=False)
    signed_at = Column(DateTime, default=datetime.utcnow)
    signed_by = Column(String(255), nullable=False)
    is_valid = Column(Boolean, default=True)
    metadata = Column(JSON)


class ExtensionAuditLog(Base):
    """Audit log for extension activities"""
    __tablename__ = "extension_audit_logs"
    
    id = Column(Integer, primary_key=True)
    extension_name = Column(String(255), nullable=False)
    tenant_id = Column(String(255), nullable=False)
    user_id = Column(String(255))
    event_type = Column(String(50), nullable=False)
    event_data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    session_id = Column(String(255))
    risk_score = Column(Integer, default=0)


class ExtensionAccessPolicy(Base):
    """Access control policies for extensions"""
    __tablename__ = "extension_access_policies"
    
    id = Column(Integer, primary_key=True)
    extension_name = Column(String(255), nullable=False)
    tenant_id = Column(String(255))
    policy_name = Column(String(255), nullable=False)
    policy_rules = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)


class ExtensionVulnerability(Base):
    """Vulnerability findings for extensions"""
    __tablename__ = "extension_vulnerabilities"
    
    id = Column(Integer, primary_key=True)
    extension_name = Column(String(255), nullable=False)
    extension_version = Column(String(50), nullable=False)
    vulnerability_id = Column(String(255), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    cve_id = Column(String(50))
    cvss_score = Column(Integer)
    status = Column(String(20), default=VulnerabilityStatus.OPEN)
    detected_at = Column(DateTime, default=datetime.utcnow)
    fixed_at = Column(DateTime)
    metadata = Column(JSON)


# Pydantic Models
class ExtensionSignatureCreate(BaseModel):
    """Model for creating extension signatures"""
    extension_name: str
    extension_version: str
    signature_hash: str
    public_key_id: str
    signed_by: str
    metadata: Optional[Dict[str, Any]] = None


class ExtensionSignatureResponse(BaseModel):
    """Response model for extension signatures"""
    id: int
    extension_name: str
    extension_version: str
    signature_hash: str
    public_key_id: str
    signed_at: datetime
    signed_by: str
    is_valid: bool
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class AuditLogEntry(BaseModel):
    """Model for audit log entries"""
    extension_name: str
    tenant_id: str
    user_id: Optional[str] = None
    event_type: AuditEventType
    event_data: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    risk_score: int = 0


class AuditLogResponse(BaseModel):
    """Response model for audit log entries"""
    id: int
    extension_name: str
    tenant_id: str
    user_id: Optional[str]
    event_type: str
    event_data: Dict[str, Any]
    timestamp: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[str]
    risk_score: int

    class Config:
        from_attributes = True


class AccessPolicyRule(BaseModel):
    """Individual access policy rule"""
    resource: str
    action: str
    conditions: Dict[str, Any] = Field(default_factory=dict)
    effect: str = "allow"  # allow or deny


class AccessPolicy(BaseModel):
    """Access control policy"""
    extension_name: str
    tenant_id: Optional[str] = None
    policy_name: str
    rules: List[AccessPolicyRule]
    is_active: bool = True


class AccessPolicyResponse(BaseModel):
    """Response model for access policies"""
    id: int
    extension_name: str
    tenant_id: Optional[str]
    policy_name: str
    policy_rules: List[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    created_by: str
    updated_at: datetime

    class Config:
        from_attributes = True


class VulnerabilityFinding(BaseModel):
    """Vulnerability finding model"""
    extension_name: str
    extension_version: str
    vulnerability_id: str
    severity: SecurityLevel
    title: str
    description: str
    cve_id: Optional[str] = None
    cvss_score: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VulnerabilityResponse(BaseModel):
    """Response model for vulnerabilities"""
    id: int
    extension_name: str
    extension_version: str
    vulnerability_id: str
    severity: str
    title: str
    description: str
    cve_id: Optional[str]
    cvss_score: Optional[int]
    status: str
    detected_at: datetime
    fixed_at: Optional[datetime]
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class ComplianceReport(BaseModel):
    """Compliance report model"""
    tenant_id: str
    report_type: str
    period_start: datetime
    period_end: datetime
    extensions_covered: List[str]
    findings: Dict[str, Any]
    recommendations: List[str]
    compliance_score: float
    generated_at: datetime


class SecurityScanRequest(BaseModel):
    """Request model for security scans"""
    extension_name: str
    extension_version: str
    scan_types: List[str] = Field(default=["code", "dependencies", "permissions"])
    deep_scan: bool = False


class SecurityScanResult(BaseModel):
    """Result model for security scans"""
    extension_name: str
    extension_version: str
    scan_id: str
    scan_types: List[str]
    vulnerabilities: List[VulnerabilityFinding]
    security_score: float
    recommendations: List[str]
    scanned_at: datetime