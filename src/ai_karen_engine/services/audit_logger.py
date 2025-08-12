"""
Comprehensive Audit Logging System - Phase 4.1.c
Implements structured audit logs with correlation IDs and PII protection for all memory operations.
"""

import hashlib
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class AuditEventType(str, Enum):
    """Types of audit events"""
    MEMORY_CREATE = "memory_create"
    MEMORY_READ = "memory_read"
    MEMORY_UPDATE = "memory_update"
    MEMORY_DELETE = "memory_delete"
    MEMORY_SEARCH = "memory_search"
    MEMORY_CONFIRM = "memory_confirm"
    CONTEXT_BUILD = "context_build"
    TENANT_ACCESS = "tenant_access"
    SECURITY_INCIDENT = "security_incident"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"

class AuditLevel(str, Enum):
    """Audit logging levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class AuditContext:
    """Context information for audit events"""
    user_id: str
    tenant_id: Optional[str] = None
    org_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None

@dataclass
class AuditEvent:
    """Structured audit event"""
    event_type: AuditEventType
    level: AuditLevel
    timestamp: datetime
    context: AuditContext
    resource_type: str
    resource_id: Optional[str] = None
    action: str = ""
    outcome: str = "success"  # success, failure, partial
    details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        event_dict = asdict(self)
        # Convert datetime to ISO string
        event_dict["timestamp"] = self.timestamp.isoformat()
        return event_dict

class PIIProtector:
    """Protects PII in audit logs"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PIIProtector")
        
        # PII patterns to detect and protect
        self.pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-?\d{2}-?\d{4}\b',
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        }
    
    def create_content_hash(self, content: str) -> str:
        """Create SHA-256 hash of content for audit purposes"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def create_shard_id(self, content: str, user_id: str, timestamp: datetime) -> str:
        """Create unique shard ID for content tracking"""
        shard_data = f"{content[:100]}{user_id}{timestamp.isoformat()}"
        return hashlib.sha256(shard_data.encode('utf-8')).hexdigest()[:16]
    
    def extract_content_metadata(self, content: str) -> Dict[str, Any]:
        """Extract safe metadata from content without storing PII"""
        import re
        
        metadata = {
            "content_length": len(content),
            "word_count": len(content.split()),
            "line_count": content.count('\n') + 1,
            "has_urls": bool(re.search(r'https?://', content)),
            "has_mentions": bool(re.search(r'@\w+', content)),
            "has_hashtags": bool(re.search(r'#\w+', content)),
            "content_hash": self.create_content_hash(content),
            "content_preview": content[:50] + "..." if len(content) > 50 else content
        }
        
        # Check for potential PII
        pii_detected = {}
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                pii_detected[pii_type] = len(matches)
        
        if pii_detected:
            metadata["pii_detected"] = pii_detected
            metadata["contains_pii"] = True
        else:
            metadata["contains_pii"] = False
        
        return metadata
    
    def sanitize_for_logging(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data for safe logging (remove/hash PII)"""
        import re
        
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Replace potential PII with placeholders
                sanitized_value = value
                for pii_type, pattern in self.pii_patterns.items():
                    sanitized_value = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", sanitized_value, flags=re.IGNORECASE)
                
                # Truncate long strings
                if len(sanitized_value) > 200:
                    sanitized_value = sanitized_value[:200] + "...[TRUNCATED]"
                
                sanitized[key] = sanitized_value
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_for_logging(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitize_for_logging(item) if isinstance(item, dict) else str(item)[:100]
                    for item in value[:10]  # Limit list size
                ]
            else:
                sanitized[key] = value
        
        return sanitized

class AuditLogger:
    """Main audit logging service"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AuditLogger")
        self.pii_protector = PIIProtector()
        
        # Configure structured logging
        self.audit_logger = logging.getLogger("audit")
        self.audit_logger.setLevel(logging.INFO)
        
        # Create audit-specific handler if not exists
        if not self.audit_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.audit_logger.addHandler(handler)
    
    def _generate_correlation_id(self) -> str:
        """Generate correlation ID if not provided"""
        return str(uuid.uuid4())
    
    def log_event(self, event: AuditEvent):
        """Log audit event with structured format"""
        try:
            # Convert to dictionary
            event_dict = event.to_dict()
            
            # Sanitize for PII protection
            sanitized_event = self.pii_protector.sanitize_for_logging(event_dict)
            
            # Log with appropriate level
            log_message = json.dumps(sanitized_event, default=str)
            
            if event.level == AuditLevel.CRITICAL:
                self.audit_logger.critical(log_message)
            elif event.level == AuditLevel.ERROR:
                self.audit_logger.error(log_message)
            elif event.level == AuditLevel.WARNING:
                self.audit_logger.warning(log_message)
            else:
                self.audit_logger.info(log_message)
            
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")
    
    def log_memory_create(
        self,
        context: AuditContext,
        memory_content: str,
        memory_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        outcome: str = "success",
        error_message: Optional[str] = None
    ):
        """Log memory creation event"""
        # Extract safe metadata from content
        content_metadata = self.pii_protector.extract_content_metadata(memory_content)
        
        # Create shard ID for tracking
        shard_id = self.pii_protector.create_shard_id(
            memory_content, context.user_id, datetime.utcnow()
        )
        
        details = {
            "shard_id": shard_id,
            "content_metadata": content_metadata,
            "memory_metadata": metadata or {}
        }
        
        event = AuditEvent(
            event_type=AuditEventType.MEMORY_CREATE,
            level=AuditLevel.ERROR if outcome == "failure" else AuditLevel.INFO,
            timestamp=datetime.utcnow(),
            context=context,
            resource_type="memory",
            resource_id=memory_id,
            action="create",
            outcome=outcome,
            details=details,
            error_message=error_message,
            duration_ms=duration_ms
        )
        
        self.log_event(event)
    
    def log_memory_read(
        self,
        context: AuditContext,
        query: str,
        results_count: int,
        memory_ids: Optional[List[str]] = None,
        duration_ms: Optional[float] = None,
        outcome: str = "success",
        error_message: Optional[str] = None
    ):
        """Log memory read/search event"""
        # Create query metadata without storing full query
        query_metadata = self.pii_protector.extract_content_metadata(query)
        
        details = {
            "query_metadata": query_metadata,
            "results_count": results_count,
            "memory_shard_ids": memory_ids[:10] if memory_ids else [],  # Limit to first 10
            "total_results": len(memory_ids) if memory_ids else 0
        }
        
        event = AuditEvent(
            event_type=AuditEventType.MEMORY_READ,
            level=AuditLevel.ERROR if outcome == "failure" else AuditLevel.INFO,
            timestamp=datetime.utcnow(),
            context=context,
            resource_type="memory",
            action="read",
            outcome=outcome,
            details=details,
            error_message=error_message,
            duration_ms=duration_ms
        )
        
        self.log_event(event)
    
    def log_memory_update(
        self,
        context: AuditContext,
        memory_id: str,
        updated_fields: Dict[str, Any],
        duration_ms: Optional[float] = None,
        outcome: str = "success",
        error_message: Optional[str] = None
    ):
        """Log memory update event"""
        # Sanitize updated fields
        sanitized_fields = self.pii_protector.sanitize_for_logging(updated_fields)
        
        details = {
            "updated_fields": sanitized_fields,
            "field_count": len(updated_fields)
        }
        
        event = AuditEvent(
            event_type=AuditEventType.MEMORY_UPDATE,
            level=AuditLevel.ERROR if outcome == "failure" else AuditLevel.INFO,
            timestamp=datetime.utcnow(),
            context=context,
            resource_type="memory",
            resource_id=memory_id,
            action="update",
            outcome=outcome,
            details=details,
            error_message=error_message,
            duration_ms=duration_ms
        )
        
        self.log_event(event)
    
    def log_memory_delete(
        self,
        context: AuditContext,
        memory_id: str,
        delete_type: str = "soft",  # soft, hard
        duration_ms: Optional[float] = None,
        outcome: str = "success",
        error_message: Optional[str] = None
    ):
        """Log memory deletion event"""
        details = {
            "delete_type": delete_type,
            "permanent": delete_type == "hard"
        }
        
        event = AuditEvent(
            event_type=AuditEventType.MEMORY_DELETE,
            level=AuditLevel.WARNING if delete_type == "hard" else AuditLevel.INFO,
            timestamp=datetime.utcnow(),
            context=context,
            resource_type="memory",
            resource_id=memory_id,
            action="delete",
            outcome=outcome,
            details=details,
            error_message=error_message,
            duration_ms=duration_ms
        )
        
        self.log_event(event)
    
    def log_context_build(
        self,
        context: AuditContext,
        query: str,
        memories_used: int,
        context_tokens: int,
        duration_ms: Optional[float] = None,
        outcome: str = "success",
        error_message: Optional[str] = None
    ):
        """Log context building event"""
        query_metadata = self.pii_protector.extract_content_metadata(query)
        
        details = {
            "query_metadata": query_metadata,
            "memories_used": memories_used,
            "context_tokens": context_tokens,
            "context_efficiency": memories_used / max(context_tokens, 1)
        }
        
        event = AuditEvent(
            event_type=AuditEventType.CONTEXT_BUILD,
            level=AuditLevel.ERROR if outcome == "failure" else AuditLevel.INFO,
            timestamp=datetime.utcnow(),
            context=context,
            resource_type="context",
            action="build",
            outcome=outcome,
            details=details,
            error_message=error_message,
            duration_ms=duration_ms
        )
        
        self.log_event(event)
    
    def log_tenant_access(
        self,
        context: AuditContext,
        target_tenant_id: str,
        access_granted: bool,
        resource_type: str = "data",
        duration_ms: Optional[float] = None
    ):
        """Log tenant access attempt"""
        details = {
            "target_tenant_id": target_tenant_id,
            "access_granted": access_granted,
            "resource_type": resource_type,
            "cross_tenant_access": target_tenant_id != context.tenant_id
        }
        
        event = AuditEvent(
            event_type=AuditEventType.TENANT_ACCESS,
            level=AuditLevel.WARNING if not access_granted else AuditLevel.INFO,
            timestamp=datetime.utcnow(),
            context=context,
            resource_type=resource_type,
            action="access",
            outcome="success" if access_granted else "failure",
            details=details,
            duration_ms=duration_ms
        )
        
        self.log_event(event)
    
    def log_security_incident(
        self,
        context: AuditContext,
        incident_type: str,
        incident_details: Dict[str, Any],
        severity: str = "medium"
    ):
        """Log security incident"""
        sanitized_details = self.pii_protector.sanitize_for_logging(incident_details)
        
        details = {
            "incident_type": incident_type,
            "severity": severity,
            "incident_details": sanitized_details
        }
        
        level = AuditLevel.CRITICAL if severity == "high" else AuditLevel.WARNING
        
        event = AuditEvent(
            event_type=AuditEventType.SECURITY_INCIDENT,
            level=level,
            timestamp=datetime.utcnow(),
            context=context,
            resource_type="security",
            action="incident",
            outcome="detected",
            details=details
        )
        
        self.log_event(event)
    
    def log_authentication(
        self,
        context: AuditContext,
        auth_method: str,
        outcome: str = "success",
        error_message: Optional[str] = None
    ):
        """Log authentication event"""
        details = {
            "auth_method": auth_method,
            "session_created": outcome == "success"
        }
        
        event = AuditEvent(
            event_type=AuditEventType.AUTHENTICATION,
            level=AuditLevel.WARNING if outcome == "failure" else AuditLevel.INFO,
            timestamp=datetime.utcnow(),
            context=context,
            resource_type="authentication",
            action="authenticate",
            outcome=outcome,
            details=details,
            error_message=error_message
        )
        
        self.log_event(event)
    
    def log_authorization(
        self,
        context: AuditContext,
        required_scopes: List[str],
        user_scopes: List[str],
        outcome: str = "success",
        error_message: Optional[str] = None
    ):
        """Log authorization event"""
        details = {
            "required_scopes": required_scopes,
            "user_scopes": user_scopes,
            "scope_match": set(required_scopes).issubset(set(user_scopes))
        }
        
        event = AuditEvent(
            event_type=AuditEventType.AUTHORIZATION,
            level=AuditLevel.WARNING if outcome == "failure" else AuditLevel.INFO,
            timestamp=datetime.utcnow(),
            context=context,
            resource_type="authorization",
            action="authorize",
            outcome=outcome,
            details=details,
            error_message=error_message
        )
        
        self.log_event(event)

# Global audit logger instance
_audit_logger = None

def get_audit_logger() -> AuditLogger:
    """Get or create audit logger instance"""
    global _audit_logger
    
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    
    return _audit_logger

# Utility functions for easy integration
def create_audit_context(
    user_id: str,
    tenant_id: Optional[str] = None,
    org_id: Optional[str] = None,
    session_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_path: Optional[str] = None,
    request_method: Optional[str] = None
) -> AuditContext:
    """Create audit context"""
    return AuditContext(
        user_id=user_id,
        tenant_id=tenant_id,
        org_id=org_id,
        session_id=session_id,
        correlation_id=correlation_id or str(uuid.uuid4()),
        ip_address=ip_address,
        user_agent=user_agent,
        request_path=request_path,
        request_method=request_method
    )

# Export public interface
__all__ = [
    "AuditLogger",
    "AuditEvent",
    "AuditContext",
    "AuditEventType",
    "AuditLevel",
    "PIIProtector",
    "get_audit_logger",
    "create_audit_context"
]