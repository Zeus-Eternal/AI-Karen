"""
API routes for extension security features
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from .models import (
    ExtensionSignatureCreate, ExtensionSignatureResponse,
    AuditLogResponse, AccessPolicy, AccessPolicyResponse,
    VulnerabilityResponse, ComplianceReport, SecurityScanRequest, SecurityScanResult
)
from .code_signing import ExtensionCodeSigner, ExtensionVerifier, ExtensionSignatureManager
from .audit_logger import ExtensionAuditLogger, ExtensionComplianceReporter, AuditEventType
from .access_control import ExtensionAccessControlManager
from .vulnerability_scanner import ExtensionVulnerabilityScanner, VulnerabilityStatus, SecurityLevel
from ..base.dependencies import get_db_session, get_current_user, require_admin
from ..base.exceptions import ExtensionSecurityError


router = APIRouter(prefix="/api/extensions/security", tags=["Extension Security"])


# Code Signing Routes
@router.post("/sign", response_model=ExtensionSignatureResponse)
async def sign_extension(
    extension_name: str,
    extension_version: str,
    extension_path: str,
    signer_id: str = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    _: None = Depends(require_admin)
):
    """Sign an extension"""
    try:
        # Initialize signer (in production, use proper key management)
        signer = ExtensionCodeSigner()
        signature_manager = ExtensionSignatureManager(db)
        
        # Sign the extension
        signature_hash = signer.sign_extension(
            extension_path=Path(extension_path),
            extension_name=extension_name,
            extension_version=extension_version,
            signer_id=signer_id
        )
        
        # Store signature in database
        signature_data = ExtensionSignatureCreate(
            extension_name=extension_name,
            extension_version=extension_version,
            signature_hash=signature_hash,
            public_key_id="default",  # In production, use proper key ID
            signed_by=signer_id
        )
        
        return signature_manager.store_signature(signature_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sign extension: {e}")


@router.post("/verify")
async def verify_extension(
    extension_path: str,
    _: None = Depends(require_admin)
):
    """Verify an extension signature"""
    try:
        # Initialize verifier (in production, use proper key management)
        verifier = ExtensionVerifier(Path("keys"))  # Configure proper key directory
        
        is_valid, verification_data = verifier.verify_extension(Path(extension_path))
        
        return {
            "valid": is_valid,
            "verification_data": verification_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify extension: {e}")


@router.get("/signatures", response_model=List[ExtensionSignatureResponse])
async def list_signatures(
    extension_name: Optional[str] = None,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_admin)
):
    """List extension signatures"""
    signature_manager = ExtensionSignatureManager(db)
    return signature_manager.list_signatures(extension_name)


# Audit Logging Routes
@router.get("/audit/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    tenant_id: Optional[str] = None,
    extension_name: Optional[str] = None,
    user_id: Optional[str] = None,
    event_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_risk_score: Optional[int] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user),
    _: None = Depends(require_admin)
):
    """Get audit logs with filtering"""
    audit_logger = ExtensionAuditLogger(db)
    
    # Convert event_type string to enum if provided
    event_type_enum = None
    if event_type:
        try:
            event_type_enum = AuditEventType(event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")
    
    return audit_logger.get_audit_logs(
        tenant_id=tenant_id,
        extension_name=extension_name,
        user_id=user_id,
        event_type=event_type_enum,
        start_date=start_date,
        end_date=end_date,
        min_risk_score=min_risk_score,
        limit=limit,
        offset=offset
    )


@router.get("/audit/summary")
async def get_audit_summary(
    tenant_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db_session),
    _: None = Depends(require_admin)
):
    """Get audit summary for a time period"""
    audit_logger = ExtensionAuditLogger(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    return audit_logger.get_audit_summary(tenant_id, start_date, end_date)


@router.post("/audit/cleanup")
async def cleanup_audit_logs(
    retention_days: int = Query(90, ge=30, le=365),
    db: Session = Depends(get_db_session),
    _: None = Depends(require_admin)
):
    """Clean up old audit logs"""
    audit_logger = ExtensionAuditLogger(db)
    deleted_count = audit_logger.cleanup_old_logs(retention_days)
    
    return {"deleted_count": deleted_count}


# Compliance Reporting Routes
@router.post("/compliance/report", response_model=ComplianceReport)
async def generate_compliance_report(
    tenant_id: str,
    report_type: str = Query(..., regex="^(security|data_protection|access_control|general)$"),
    days: int = Query(30, ge=1, le=365),
    extensions: Optional[List[str]] = None,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_admin)
):
    """Generate a compliance report"""
    audit_logger = ExtensionAuditLogger(db)
    compliance_reporter = ExtensionComplianceReporter(db, audit_logger)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    return compliance_reporter.generate_compliance_report(
        tenant_id=tenant_id,
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        extensions=extensions
    )


# Access Control Routes
@router.post("/access/policies", response_model=AccessPolicyResponse)
async def create_access_policy(
    policy: AccessPolicy,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user),
    _: None = Depends(require_admin)
):
    """Create an access control policy"""
    audit_logger = ExtensionAuditLogger(db)
    access_manager = ExtensionAccessControlManager(db, audit_logger)
    
    return access_manager.create_policy(policy, current_user)


@router.get("/access/policies", response_model=List[AccessPolicyResponse])
async def list_access_policies(
    extension_name: Optional[str] = None,
    tenant_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_admin)
):
    """List access control policies"""
    access_manager = ExtensionAccessControlManager(db)
    return access_manager.list_policies(extension_name, tenant_id, is_active)


@router.get("/access/policies/{policy_id}", response_model=AccessPolicyResponse)
async def get_access_policy(
    policy_id: int,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_admin)
):
    """Get a specific access control policy"""
    access_manager = ExtensionAccessControlManager(db)
    policy = access_manager.get_policy(policy_id)
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return policy


@router.put("/access/policies/{policy_id}", response_model=AccessPolicyResponse)
async def update_access_policy(
    policy_id: int,
    policy_updates: dict,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user),
    _: None = Depends(require_admin)
):
    """Update an access control policy"""
    audit_logger = ExtensionAuditLogger(db)
    access_manager = ExtensionAccessControlManager(db, audit_logger)
    
    return access_manager.update_policy(policy_id, policy_updates, current_user)


@router.delete("/access/policies/{policy_id}")
async def delete_access_policy(
    policy_id: int,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user),
    _: None = Depends(require_admin)
):
    """Delete an access control policy"""
    audit_logger = ExtensionAuditLogger(db)
    access_manager = ExtensionAccessControlManager(db, audit_logger)
    
    success = access_manager.delete_policy(policy_id, current_user)
    
    if not success:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return {"message": "Policy deleted successfully"}


@router.post("/access/check")
async def check_access(
    extension_name: str,
    tenant_id: str,
    user_id: str,
    resource: str,
    action: str,
    context: Optional[dict] = None,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_admin)
):
    """Check access permissions"""
    audit_logger = ExtensionAuditLogger(db)
    access_manager = ExtensionAccessControlManager(db, audit_logger)
    
    allowed = access_manager.check_access(
        extension_name=extension_name,
        tenant_id=tenant_id,
        user_id=user_id,
        resource=resource,
        action=action,
        context=context
    )
    
    return {"allowed": allowed}


# Vulnerability Scanning Routes
@router.post("/vulnerabilities/scan", response_model=SecurityScanResult)
async def scan_extension(
    scan_request: SecurityScanRequest,
    extension_path: str,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_admin)
):
    """Scan an extension for vulnerabilities"""
    audit_logger = ExtensionAuditLogger(db)
    scanner = ExtensionVulnerabilityScanner(db, audit_logger)
    
    return scanner.scan_extension(
        extension_path=Path(extension_path),
        extension_name=scan_request.extension_name,
        extension_version=scan_request.extension_version,
        scan_request=scan_request
    )


@router.get("/vulnerabilities", response_model=List[VulnerabilityResponse])
async def get_vulnerabilities(
    extension_name: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_admin)
):
    """Get vulnerabilities with filtering"""
    scanner = ExtensionVulnerabilityScanner(db)
    
    # Convert string parameters to enums
    status_enum = None
    if status:
        try:
            status_enum = VulnerabilityStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    severity_enum = None
    if severity:
        try:
            severity_enum = SecurityLevel(severity)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
    
    return scanner.get_vulnerabilities(extension_name, status_enum, severity_enum)


@router.put("/vulnerabilities/{vulnerability_id}/status")
async def update_vulnerability_status(
    vulnerability_id: int,
    status: str,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user),
    _: None = Depends(require_admin)
):
    """Update vulnerability status"""
    try:
        status_enum = VulnerabilityStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    audit_logger = ExtensionAuditLogger(db)
    scanner = ExtensionVulnerabilityScanner(db, audit_logger)
    
    success = scanner.update_vulnerability_status(vulnerability_id, status_enum, current_user)
    
    if not success:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    return {"message": "Vulnerability status updated successfully"}


# Security Dashboard Routes
@router.get("/dashboard/overview")
async def get_security_overview(
    tenant_id: Optional[str] = None,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_admin)
):
    """Get security overview dashboard data"""
    audit_logger = ExtensionAuditLogger(db)
    scanner = ExtensionVulnerabilityScanner(db)
    
    # Get recent audit summary
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    audit_summary = audit_logger.get_audit_summary(
        tenant_id or "all",
        start_date,
        end_date
    ) if tenant_id else {"total_events": 0, "high_risk_events": 0}
    
    # Get vulnerability summary
    all_vulns = scanner.get_vulnerabilities()
    open_vulns = [v for v in all_vulns if v.status == VulnerabilityStatus.OPEN.value]
    critical_vulns = [v for v in open_vulns if v.severity == SecurityLevel.CRITICAL.value]
    
    return {
        "audit_summary": audit_summary,
        "vulnerability_summary": {
            "total_vulnerabilities": len(all_vulns),
            "open_vulnerabilities": len(open_vulns),
            "critical_vulnerabilities": len(critical_vulns)
        },
        "security_score": max(100 - len(critical_vulns) * 20 - len(open_vulns) * 5, 0)
    }