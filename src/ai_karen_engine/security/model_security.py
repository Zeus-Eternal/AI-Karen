"""
Model Security Manager for RBAC and security validation.
Extends existing RBAC system for model operations with license tracking and audit logging.
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ai_karen_engine.middleware.rbac import (
    RBACMiddleware, 
    ScopeValidator, 
    RBACError, 
    VALID_SCOPES, 
    DEFAULT_ROLE_SCOPES,
    require_scopes,
    check_scope,
    get_user_scopes
)
from ai_karen_engine.security.access_control import RBAC, AuditLogger
from ai_karen_engine.utils.model_security_utils import (
    ModelSecurityIntegrator,
    ModelSecurityReport,
    FileValidationResult
)

logger = logging.getLogger(__name__)

# Model operation scopes - extending existing RBAC system
MODEL_SCOPES = {
    "model:read",      # Permission to browse and view model information
    "model:download",  # Permission to download models
    "model:remove",    # Permission to remove models
    "model:migrate",   # Permission to migrate model layouts
    "model:admin",     # Administrative model operations (GC, registry management)
}

# Update valid scopes to include model operations
VALID_SCOPES.update(MODEL_SCOPES)

# Update default role scopes for model operations
DEFAULT_ROLE_SCOPES.update({
    "admin": DEFAULT_ROLE_SCOPES["admin"] | {"model:read", "model:download", "model:remove", "model:migrate", "model:admin"},
    "user": DEFAULT_ROLE_SCOPES["user"] | {"model:read", "model:download"},
    "readonly": DEFAULT_ROLE_SCOPES["readonly"] | {"model:read"},
    "guest": DEFAULT_ROLE_SCOPES["guest"],  # No model permissions for guests
})


class LicenseType(Enum):
    """Model license types requiring different handling."""
    OPEN = "open"
    RESTRICTED = "restricted"
    COMMERCIAL = "commercial"
    RESEARCH_ONLY = "research_only"
    CUSTOM = "custom"


class SecurityValidationResult(Enum):
    """Security validation results."""
    APPROVED = "approved"
    BLOCKED = "blocked"
    REQUIRES_REVIEW = "requires_review"


@dataclass
class LicenseAcceptance:
    """License acceptance record."""
    user_id: str
    model_id: str
    license_type: str
    license_text: str
    accepted_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    acceptance_method: str = "web_ui"  # web_ui, cli, api


@dataclass
class SecurityValidation:
    """Security validation result for a model."""
    model_id: str
    result: SecurityValidationResult
    reasons: List[str] = field(default_factory=list)
    checksum_verified: bool = False
    owner_approved: bool = True
    size_approved: bool = True
    license_compliant: bool = True
    validation_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ModelAuditEvent:
    """Model operation audit event."""
    event_id: str
    user_id: str
    operation: str  # download, remove, migrate, browse, etc.
    model_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ModelSecurityManager:
    """Security manager for model operations with RBAC integration."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.rbac = RBAC()
        self.audit_logger = ModelAuditLogger()
        self.license_manager = LicenseManager()
        self.security_validator = ModelSecurityValidator(self.config)
        self.security_integrator = ModelSecurityIntegrator(self.config)
        self.logger = logging.getLogger(f"{__name__}.ModelSecurityManager")
    
    async def check_download_permission(self, user: Dict[str, Any], model_id: str, request=None) -> bool:
        """Check if user has permission to download a model."""
        try:
            # Check basic RBAC permission
            self.rbac.require(user, "user")  # Minimum user role required
            
            # Check model-specific scope
            if request:
                has_scope = await check_scope(request, "model:download")
                if not has_scope:
                    self.logger.warning(f"User {user.get('user_id')} lacks model:download scope")
                    return False
            else:
                # Fallback to role-based check
                user_scopes = self._get_user_scopes_from_roles(user.get("roles", []))
                if "model:download" not in user_scopes:
                    self.logger.warning(f"User {user.get('user_id')} lacks model:download scope")
                    return False
            
            # Check license compliance
            license_compliant = await self.license_manager.check_license_compliance(
                user.get("user_id"), model_id
            )
            if not license_compliant:
                self.logger.warning(f"User {user.get('user_id')} has not accepted license for model {model_id}")
                return False
            
            # Check security validation
            security_result = await self.security_validator.validate_model_security(model_id)
            if security_result.result == SecurityValidationResult.BLOCKED:
                self.logger.warning(f"Model {model_id} is blocked by security policy")
                return False
            
            return True
            
        except PermissionError as e:
            self.logger.warning(f"Permission denied for user {user.get('user_id')}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error checking download permission: {e}")
            return False
    
    async def check_migration_permission(self, user: Dict[str, Any], request=None) -> bool:
        """Check if user has permission to perform model migration."""
        try:
            # Migration requires admin role
            self.rbac.require(user, "admin")
            
            # Check migration scope
            if request:
                has_scope = await check_scope(request, "model:migrate")
                if not has_scope:
                    self.logger.warning(f"User {user.get('user_id')} lacks model:migrate scope")
                    return False
            else:
                # Fallback to role-based check
                user_scopes = self._get_user_scopes_from_roles(user.get("roles", []))
                if "model:migrate" not in user_scopes:
                    self.logger.warning(f"User {user.get('user_id')} lacks model:migrate scope")
                    return False
            
            return True
            
        except PermissionError as e:
            self.logger.warning(f"Migration permission denied for user {user.get('user_id')}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error checking migration permission: {e}")
            return False
    
    async def check_remove_permission(self, user: Dict[str, Any], model_id: str, request=None) -> bool:
        """Check if user has permission to remove a model."""
        try:
            # Remove requires admin role
            self.rbac.require(user, "admin")
            
            # Check remove scope
            if request:
                has_scope = await check_scope(request, "model:remove")
                if not has_scope:
                    self.logger.warning(f"User {user.get('user_id')} lacks model:remove scope")
                    return False
            else:
                # Fallback to role-based check
                user_scopes = self._get_user_scopes_from_roles(user.get("roles", []))
                if "model:remove" not in user_scopes:
                    self.logger.warning(f"User {user.get('user_id')} lacks model:remove scope")
                    return False
            
            return True
            
        except PermissionError as e:
            self.logger.warning(f"Remove permission denied for user {user.get('user_id')}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error checking remove permission: {e}")
            return False
    
    async def check_browse_permission(self, user: Dict[str, Any], request=None) -> bool:
        """Check if user has permission to browse models (read-only)."""
        try:
            # Browse is allowed for all authenticated users
            if not user.get("user_id"):
                return False
            
            # Check read scope
            if request:
                has_scope = await check_scope(request, "model:read")
                if not has_scope:
                    self.logger.warning(f"User {user.get('user_id')} lacks model:read scope")
                    return False
            else:
                # Fallback to role-based check
                user_scopes = self._get_user_scopes_from_roles(user.get("roles", []))
                if "model:read" not in user_scopes:
                    self.logger.warning(f"User {user.get('user_id')} lacks model:read scope")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking browse permission: {e}")
            return False
    
    async def check_admin_permission(self, user: Dict[str, Any], request=None) -> bool:
        """Check if user has admin permissions for model operations."""
        try:
            # Admin operations require admin role
            self.rbac.require(user, "admin")
            
            # Check admin scope
            if request:
                has_scope = await check_scope(request, "model:admin")
                if not has_scope:
                    self.logger.warning(f"User {user.get('user_id')} lacks model:admin scope")
                    return False
            else:
                # Fallback to role-based check
                user_scopes = self._get_user_scopes_from_roles(user.get("roles", []))
                if "model:admin" not in user_scopes:
                    self.logger.warning(f"User {user.get('user_id')} lacks model:admin scope")
                    return False
            
            return True
            
        except PermissionError as e:
            self.logger.warning(f"Admin permission denied for user {user.get('user_id')}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error checking admin permission: {e}")
            return False
    
    def _get_user_scopes_from_roles(self, roles: List[str]) -> Set[str]:
        """Get user scopes based on roles (fallback method)."""
        user_scopes = set()
        for role in roles:
            role_scopes = DEFAULT_ROLE_SCOPES.get(role, set())
            user_scopes.update(role_scopes)
        return user_scopes
    
    async def audit_model_operation(
        self, 
        user_id: str, 
        operation: str, 
        model_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request=None
    ) -> None:
        """Audit a model operation."""
        event = ModelAuditEvent(
            event_id=f"model_{int(time.time() * 1000)}_{user_id}",
            user_id=user_id,
            operation=operation,
            model_id=model_id,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        if request:
            if hasattr(request, 'client') and request.client:
                event.ip_address = request.client.host
            if hasattr(request, 'headers'):
                event.user_agent = request.headers.get("user-agent")
        
        await self.audit_logger.log_event(event)
    
    async def validate_model_download_security(
        self,
        user_id: str,
        model_id: str,
        model_info: Dict[str, Any],
        models_dir: Path,
        request=None
    ) -> Tuple[bool, List[str]]:
        """Comprehensive security validation for model download."""
        try:
            # Perform integrated security validation
            is_valid, issues = self.security_integrator.validate_model_download(
                model_id=model_id,
                model_info=model_info,
                models_dir=models_dir,
                user_id=user_id
            )
            
            # Log security validation event
            await self.audit_logger.log_security_event(
                user_id=user_id,
                event_type="download_validation",
                details={
                    "model_id": model_id,
                    "validation_passed": is_valid,
                    "issues": issues,
                    "model_size": model_info.get("total_size", 0)
                },
                severity="high" if not is_valid else "low",
                request=request
            )
            
            return is_valid, issues
            
        except Exception as e:
            self.logger.error(f"Error during security validation: {e}")
            await self.audit_logger.log_security_event(
                user_id=user_id,
                event_type="validation_error",
                details={
                    "model_id": model_id,
                    "error": str(e)
                },
                severity="critical",
                request=request
            )
            return False, [f"Security validation error: {str(e)}"]
    
    async def validate_model_files_integrity(
        self,
        user_id: str,
        model_id: str,
        files_info: List[Dict[str, Any]],
        model_dir: Path,
        request=None
    ) -> ModelSecurityReport:
        """Validate model files for integrity and security."""
        try:
            # Perform file validation
            report = self.security_integrator.validate_model_files_post_download(
                model_id=model_id,
                files_info=files_info,
                model_dir=model_dir
            )
            
            # Log file validation results
            await self.audit_logger.log_security_event(
                user_id=user_id,
                event_type="file_validation",
                details={
                    "model_id": model_id,
                    "total_files": report.total_files,
                    "validated_files": report.validated_files,
                    "failed_validations": report.failed_validations,
                    "quarantined_files": report.quarantined_files,
                    "security_issues": report.security_issues
                },
                severity="high" if report.failed_validations > 0 else "low",
                request=request
            )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error during file validation: {e}")
            await self.audit_logger.log_security_event(
                user_id=user_id,
                event_type="file_validation_error",
                details={
                    "model_id": model_id,
                    "error": str(e)
                },
                severity="critical",
                request=request
            )
            
            # Return empty report on error
            return ModelSecurityReport(
                model_id=model_id,
                total_files=0,
                validated_files=0,
                failed_validations=0,
                quarantined_files=0,
                total_size=0,
                validation_timestamp=datetime.utcnow(),
                file_results=[],
                security_issues=[f"Validation error: {str(e)}"]
            )
    
    async def cleanup_security_artifacts(
        self,
        user_id: str,
        max_age_days: int = 30,
        request=None
    ) -> Dict[str, int]:
        """Clean up old security artifacts like quarantined files."""
        try:
            # Clean up quarantined files
            cleaned_files = self.security_integrator.cleanup_quarantined_files(max_age_days)
            
            # Log cleanup operation
            await self.audit_logger.log_security_event(
                user_id=user_id,
                event_type="security_cleanup",
                details={
                    "cleaned_files": cleaned_files,
                    "max_age_days": max_age_days
                },
                severity="low",
                request=request
            )
            
            return {
                "quarantined_files_cleaned": cleaned_files
            }
            
        except Exception as e:
            self.logger.error(f"Error during security cleanup: {e}")
            await self.audit_logger.log_security_event(
                user_id=user_id,
                event_type="cleanup_error",
                details={
                    "error": str(e)
                },
                severity="medium",
                request=request
            )
            return {"error": str(e)}


class LicenseManager:
    """Manages model license acceptance and compliance."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("data/model_licenses.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(f"{__name__}.LicenseManager")
    
    async def require_license_acceptance(
        self, 
        user_id: str, 
        model_id: str, 
        license_info: Dict[str, Any],
        request=None
    ) -> LicenseAcceptance:
        """Require user to accept model license."""
        license_acceptance = LicenseAcceptance(
            user_id=user_id,
            model_id=model_id,
            license_type=license_info.get("type", "custom"),
            license_text=license_info.get("text", ""),
            accepted_at=datetime.utcnow(),
            acceptance_method="api" if request else "cli"
        )
        
        if request:
            if hasattr(request, 'client') and request.client:
                license_acceptance.ip_address = request.client.host
            if hasattr(request, 'headers'):
                license_acceptance.user_agent = request.headers.get("user-agent")
        
        await self._store_license_acceptance(license_acceptance)
        self.logger.info(f"License accepted by user {user_id} for model {model_id}")
        
        return license_acceptance
    
    async def check_license_compliance(self, user_id: str, model_id: str) -> bool:
        """Check if user has accepted required license for model."""
        try:
            acceptances = await self._load_license_acceptances()
            
            # Check if user has accepted license for this model
            for acceptance in acceptances:
                if (acceptance.get("user_id") == user_id and 
                    acceptance.get("model_id") == model_id):
                    return True
            
            # Check if model requires license acceptance
            # For now, assume all models with restrictive licenses require acceptance
            # This would be enhanced to check actual model license information
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking license compliance: {e}")
            return False
    
    async def get_license_acceptance_record(
        self, 
        user_id: str, 
        model_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get license acceptance record for user and model."""
        try:
            acceptances = await self._load_license_acceptances()
            
            for acceptance in acceptances:
                if (acceptance.get("user_id") == user_id and 
                    acceptance.get("model_id") == model_id):
                    return acceptance
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting license acceptance record: {e}")
            return None
    
    async def generate_compliance_report(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate license compliance report."""
        try:
            acceptances = await self._load_license_acceptances()
            
            if start_date:
                acceptances = [
                    a for a in acceptances 
                    if datetime.fromisoformat(a.get("accepted_at", "")) >= start_date
                ]
            
            if end_date:
                acceptances = [
                    a for a in acceptances 
                    if datetime.fromisoformat(a.get("accepted_at", "")) <= end_date
                ]
            
            report = {
                "report_generated": datetime.utcnow().isoformat(),
                "period_start": start_date.isoformat() if start_date else None,
                "period_end": end_date.isoformat() if end_date else None,
                "total_acceptances": len(acceptances),
                "unique_users": len(set(a.get("user_id") for a in acceptances)),
                "unique_models": len(set(a.get("model_id") for a in acceptances)),
                "acceptances_by_type": {},
                "acceptances_by_method": {},
                "acceptances": acceptances
            }
            
            # Group by license type
            for acceptance in acceptances:
                license_type = acceptance.get("license_type", "unknown")
                report["acceptances_by_type"][license_type] = (
                    report["acceptances_by_type"].get(license_type, 0) + 1
                )
            
            # Group by acceptance method
            for acceptance in acceptances:
                method = acceptance.get("acceptance_method", "unknown")
                report["acceptances_by_method"][method] = (
                    report["acceptances_by_method"].get(method, 0) + 1
                )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating compliance report: {e}")
            return {"error": str(e)}
    
    async def _store_license_acceptance(self, acceptance: LicenseAcceptance) -> None:
        """Store license acceptance record."""
        try:
            acceptances = await self._load_license_acceptances()
            
            # Convert to dict for storage
            acceptance_dict = {
                "user_id": acceptance.user_id,
                "model_id": acceptance.model_id,
                "license_type": acceptance.license_type,
                "license_text": acceptance.license_text,
                "accepted_at": acceptance.accepted_at.isoformat(),
                "ip_address": acceptance.ip_address,
                "user_agent": acceptance.user_agent,
                "acceptance_method": acceptance.acceptance_method
            }
            
            acceptances.append(acceptance_dict)
            
            # Save to file
            with open(self.storage_path, 'w') as f:
                json.dump(acceptances, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error storing license acceptance: {e}")
            raise
    
    async def _load_license_acceptances(self) -> List[Dict[str, Any]]:
        """Load license acceptance records."""
        try:
            if not self.storage_path.exists():
                return []
            
            with open(self.storage_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Error loading license acceptances: {e}")
            return []


class ModelSecurityValidator:
    """Validates model security based on policies."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ModelSecurityValidator")
        
        # Security policies from config
        self.max_model_size_gb = config.get("max_model_size_gb", 50.0)
        self.allowed_owners = set(config.get("allowed_owners", []))
        self.blocked_owners = set(config.get("blocked_owners", []))
        self.require_checksum_verification = config.get("require_checksum_verification", True)
    
    async def validate_model_security(self, model_id: str, model_info: Optional[Dict] = None) -> SecurityValidation:
        """Validate model against security policies."""
        validation = SecurityValidation(model_id=model_id, result=SecurityValidationResult.APPROVED)
        
        try:
            if not model_info:
                # In a real implementation, this would fetch model info from HuggingFace
                # For now, we'll create a placeholder
                model_info = {"owner": "unknown", "total_size": 0}
            
            # Check owner allowlist/blocklist
            owner = model_info.get("owner", "").lower()
            if self.blocked_owners and owner in self.blocked_owners:
                validation.result = SecurityValidationResult.BLOCKED
                validation.reasons.append(f"Owner '{owner}' is blocked")
                validation.owner_approved = False
            elif self.allowed_owners and owner not in self.allowed_owners:
                validation.result = SecurityValidationResult.REQUIRES_REVIEW
                validation.reasons.append(f"Owner '{owner}' not in allowlist")
                validation.owner_approved = False
            
            # Check model size
            total_size_gb = model_info.get("total_size", 0) / (1024**3)  # Convert to GB
            if total_size_gb > self.max_model_size_gb:
                validation.result = SecurityValidationResult.BLOCKED
                validation.reasons.append(f"Model size {total_size_gb:.1f}GB exceeds limit {self.max_model_size_gb}GB")
                validation.size_approved = False
            
            # Checksum verification would be done during download
            validation.checksum_verified = True  # Placeholder
            
            self.logger.info(f"Security validation for {model_id}: {validation.result.value}")
            
        except Exception as e:
            self.logger.error(f"Error validating model security: {e}")
            validation.result = SecurityValidationResult.REQUIRES_REVIEW
            validation.reasons.append(f"Validation error: {str(e)}")
        
        return validation


class ModelAuditLogger:
    """Audit logger for model operations with security event integration."""
    
    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or Path("logs/model_audit.log")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(f"{__name__}.ModelAuditLogger")
        
        # Integration with existing audit logging framework
        try:
            from ai_karen_engine.security.access_control import audit_logger
            self.system_audit_logger = audit_logger
        except ImportError:
            self.system_audit_logger = None
    
    async def log_event(self, event: ModelAuditEvent) -> None:
        """Log a model audit event with integration to existing audit framework."""
        try:
            log_entry = {
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                "user_id": event.user_id,
                "operation": event.operation,
                "model_id": event.model_id,
                "success": event.success,
                "error_message": event.error_message,
                "ip_address": event.ip_address,
                "user_agent": event.user_agent,
                "metadata": event.metadata
            }
            
            # Write to model-specific audit log file
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            # Integrate with existing system audit logger for cloud usage tracking
            if self.system_audit_logger and event.model_id:
                # Map model operations to cloud usage for compliance
                provider = "huggingface"  # Default provider
                if event.metadata.get("library") == "llama-cpp":
                    provider = "llama-cpp"
                elif event.metadata.get("library") == "transformers":
                    provider = "transformers"
                
                self.system_audit_logger.log_cloud_usage(
                    user_id=event.user_id,
                    provider=provider,
                    model=event.model_id
                )
            
            # Also log to standard logger with security context
            if event.success:
                self.logger.info(
                    f"Model operation: {event.operation} by {event.user_id} "
                    f"{'on ' + event.model_id if event.model_id else ''}",
                    extra={
                        "security_event": True,
                        "operation": event.operation,
                        "user_id": event.user_id,
                        "model_id": event.model_id,
                        "ip_address": event.ip_address
                    }
                )
            else:
                self.logger.warning(
                    f"Failed model operation: {event.operation} by {event.user_id} "
                    f"{'on ' + event.model_id if event.model_id else ''} - {event.error_message}",
                    extra={
                        "security_event": True,
                        "security_issue": True,
                        "operation": event.operation,
                        "user_id": event.user_id,
                        "model_id": event.model_id,
                        "error": event.error_message,
                        "ip_address": event.ip_address
                    }
                )
                
        except Exception as e:
            self.logger.error(f"Error logging audit event: {e}")
    
    async def log_security_event(
        self, 
        user_id: str, 
        event_type: str, 
        details: Dict[str, Any],
        severity: str = "medium",
        request=None
    ) -> None:
        """Log a security-specific event."""
        event = ModelAuditEvent(
            event_id=f"security_{int(time.time() * 1000)}_{user_id}",
            user_id=user_id,
            operation=f"security_{event_type}",
            success=severity != "critical",
            metadata={
                "event_type": event_type,
                "severity": severity,
                **details
            }
        )
        
        if request:
            if hasattr(request, 'client') and request.client:
                event.ip_address = request.client.host
            if hasattr(request, 'headers'):
                event.user_agent = request.headers.get("user-agent")
        
        await self.log_event(event)
    
    async def get_audit_trail(
        self, 
        user_id: Optional[str] = None,
        operation: Optional[str] = None,
        model_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit trail with optional filters."""
        try:
            if not self.log_path.exists():
                return []
            
            events = []
            with open(self.log_path, 'r') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        
                        # Apply filters
                        if user_id and event.get("user_id") != user_id:
                            continue
                        if operation and event.get("operation") != operation:
                            continue
                        if model_id and event.get("model_id") != model_id:
                            continue
                        
                        event_time = datetime.fromisoformat(event.get("timestamp", ""))
                        if start_date and event_time < start_date:
                            continue
                        if end_date and event_time > end_date:
                            continue
                        
                        events.append(event)
                        
                    except json.JSONDecodeError:
                        continue
            
            # Sort by timestamp (newest first) and limit
            events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return events[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting audit trail: {e}")
            return []


# Permission decorators for model operations
def require_model_download_permission(func):
    """Decorator to require model download permission."""
    async def wrapper(*args, **kwargs):
        # Extract request and user from args/kwargs
        request = kwargs.get('request') or (args[0] if args else None)
        if not request or not hasattr(request, 'state'):
            raise RBACError("Authentication required")
        
        user = {
            "user_id": getattr(request.state, 'user', None),
            "roles": getattr(request.state, 'roles', [])
        }
        
        security_manager = ModelSecurityManager()
        has_permission = await security_manager.check_download_permission(user, "", request)
        
        if not has_permission:
            raise RBACError("Insufficient permissions for model download")
        
        return await func(*args, **kwargs)
    
    return wrapper


def require_model_admin_permission(func):
    """Decorator to require model admin permission."""
    async def wrapper(*args, **kwargs):
        # Extract request and user from args/kwargs
        request = kwargs.get('request') or (args[0] if args else None)
        if not request or not hasattr(request, 'state'):
            raise RBACError("Authentication required")
        
        user = {
            "user_id": getattr(request.state, 'user', None),
            "roles": getattr(request.state, 'roles', [])
        }
        
        security_manager = ModelSecurityManager()
        has_permission = await security_manager.check_admin_permission(user, request)
        
        if not has_permission:
            raise RBACError("Insufficient permissions for model administration")
        
        return await func(*args, **kwargs)
    
    return wrapper


# Export public interface
__all__ = [
    "ModelSecurityManager",
    "LicenseManager", 
    "ModelSecurityValidator",
    "ModelAuditLogger",
    "LicenseAcceptance",
    "SecurityValidation",
    "ModelAuditEvent",
    "LicenseType",
    "SecurityValidationResult",
    "MODEL_SCOPES",
    "require_model_download_permission",
    "require_model_admin_permission",
]