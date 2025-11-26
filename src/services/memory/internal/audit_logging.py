"""
Comprehensive Audit Logging Service

This service provides structured audit logging for authentication events,
intelligent response usage, session lifecycle, and performance metrics.
Integrates with the existing structured logging infrastructure.
"""

import json
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict

from src.services.structured_logging import (
    get_structured_logging_service,
    get_security_logger,
    SecurityEvent,
    SecurityEventType,
    PIIRedactor
)
from ai_karen_engine.core.logging.logger import get_logger
from src.services.audit_deduplication import (
    get_audit_deduplication_service,
    EventType,
    EventKey
)


class AuditEventType(str, Enum):
    """Types of audit events"""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT_SUCCESS = "logout_success"
    REFRESH_SUCCESS = "refresh_success"
    REFRESH_FAILURE = "refresh_failure"
    TOKEN_ROTATION = "token_rotation"
    TOKEN_REVOCATION = "token_revocation"
    SESSION_CREATED = "session_created"
    SESSION_EXPIRED = "session_expired"
    SESSION_INVALIDATED = "session_invalidated"
    
    # Security events
    SUSPICIOUS_LOGIN_PATTERN = "suspicious_login_pattern"
    MULTIPLE_FAILED_ATTEMPTS = "multiple_failed_attempts"
    ACCOUNT_LOCKED = "account_locked"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    ANOMALY_DETECTED = "anomaly_detected"
    
    # Intelligent response events
    ERROR_RESPONSE_GENERATED = "error_response_generated"
    AI_ANALYSIS_REQUESTED = "ai_analysis_requested"
    AI_ANALYSIS_COMPLETED = "ai_analysis_completed"
    RESPONSE_CACHED = "response_cached"
    RESPONSE_SERVED_FROM_CACHE = "response_served_from_cache"
    
    # Performance events
    TOKEN_OPERATION_PERFORMANCE = "token_operation_performance"
    LLM_RESPONSE_PERFORMANCE = "llm_response_performance"
    DATABASE_OPERATION_PERFORMANCE = "database_operation_performance"
    API_REQUEST_PERFORMANCE = "api_request_performance"


class AuditSeverity(str, Enum):
    """Audit event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Structured audit event"""
    event_type: AuditEventType
    severity: AuditSeverity
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    correlation_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthenticationAuditEvent(AuditEvent):
    """Authentication-specific audit event"""
    email: Optional[str] = None
    failure_reason: Optional[str] = None
    token_type: Optional[str] = None
    token_jti: Optional[str] = None
    previous_login: Optional[datetime] = None
    login_count: Optional[int] = None


@dataclass
class IntelligentResponseAuditEvent(AuditEvent):
    """Intelligent response-specific audit event"""
    error_category: Optional[str] = None
    error_severity: Optional[str] = None
    provider_name: Optional[str] = None
    ai_analysis_used: bool = False
    response_cached: bool = False
    cache_hit: bool = False
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    response_quality_score: Optional[float] = None


@dataclass
class PerformanceAuditEvent(AuditEvent):
    """Performance-specific audit event"""
    operation_name: str = ""
    operation_type: str = ""
    success: bool = True
    error_message: Optional[str] = None
    resource_usage: Optional[Dict[str, Any]] = None
    cache_hit: bool = False
    retry_count: int = 0


class AuditLogger:
    """Comprehensive audit logging service"""
    
    def __init__(self):
        self.structured_logging = get_structured_logging_service()
        self.security_logger = get_security_logger()
        self.audit_logger = get_logger("audit")
        self.performance_logger = get_logger("performance")
        self.auth_logger = get_logger("auth_audit")
        self.response_logger = get_logger("response_audit")
        self.deduplication_service = get_audit_deduplication_service()
        
        # Metrics tracking
        self._event_counts: Dict[str, int] = {}
        self._performance_metrics: Dict[str, List[float]] = {}
        
    def log_audit_event(self, event: AuditEvent) -> None:
        """Log a general audit event"""
        # Convert to dict and redact sensitive data
        event_dict = asdict(event)
        event_dict["timestamp"] = event.timestamp.isoformat()
        event_dict["event_type"] = event.event_type.value
        event_dict["severity"] = event.severity.value
        
        # Redact PII from metadata
        if event_dict.get("metadata"):
            event_dict["metadata"] = PIIRedactor.redact_dict(event_dict["metadata"])
        
        # Hash sensitive identifiers
        if event_dict.get("session_id"):
            event_dict["session_id_hash"] = PIIRedactor.hash_sensitive_data(event_dict["session_id"])
            del event_dict["session_id"]
        
        # Track event counts for metrics
        self._event_counts[event.event_type.value] = self._event_counts.get(event.event_type.value, 0) + 1
        
        # Log to appropriate logger based on severity
        extra = {
            "audit_event": event_dict,
            "correlation_id": event.correlation_id,
            "user_id": event.user_id,
            "tenant_id": event.tenant_id,
            "ip_address": event.ip_address,
            "endpoint": event.endpoint,
            "method": event.method,
            "status_code": event.status_code,
            "duration_ms": event.duration_ms
        }
        
        if event.severity == AuditSeverity.CRITICAL:
            self.audit_logger.critical(event.message, **extra)
        elif event.severity == AuditSeverity.ERROR:
            self.audit_logger.error(event.message, **extra)
        elif event.severity == AuditSeverity.WARNING:
            self.audit_logger.warning(event.message, **extra)
        else:
            self.audit_logger.info(event.message, **extra)
    
    # Authentication Event Logging
    
    def log_login_success(
        self,
        user_id: str,
        email: str,
        ip_address: str,
        user_agent: str = None,
        tenant_id: str = None,
        correlation_id: str = None,
        session_id: str = None,
        previous_login: datetime = None,
        login_count: int = None,
        logged_by: str = "auth_routes",
        **metadata
    ) -> None:
        """Log successful login event with deduplication"""
        # Check if this event should be logged (not a duplicate)
        if not self.deduplication_service.should_log_authentication_event(
            event_type=EventType.LOGIN_SUCCESS,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            email=email,
            logged_by=logged_by,
            ttl_seconds=300  # 5 minutes
        ):
            return  # Skip duplicate event
        
        event = AuthenticationAuditEvent(
            event_type=AuditEventType.LOGIN_SUCCESS,
            severity=AuditSeverity.INFO,
            message=f"User {email} logged in successfully",
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            email=email,
            previous_login=previous_login,
            login_count=login_count,
            metadata={**metadata, "logged_by": logged_by}
        )
        
        self.log_audit_event(event)
        self.auth_logger.info(
            f"Login success: {email}",
            user_id=user_id,
            ip_address=ip_address,
            correlation_id=correlation_id
        )
    
    def log_login_failure(
        self,
        email: str,
        ip_address: str,
        failure_reason: str,
        user_agent: str = None,
        correlation_id: str = None,
        attempt_count: int = None,
        logged_by: str = "auth_routes",
        **metadata
    ) -> None:
        """Log failed login attempt with deduplication"""
        # Check if this event should be logged (not a duplicate)
        if not self.deduplication_service.should_log_authentication_event(
            event_type=EventType.LOGIN_FAILURE,
            user_id=None,  # No user_id for failed login
            session_id=None,
            ip_address=ip_address,
            email=email,
            logged_by=logged_by,
            ttl_seconds=60  # Shorter TTL for failures to allow legitimate retries
        ):
            return  # Skip duplicate event
        
        event = AuthenticationAuditEvent(
            event_type=AuditEventType.LOGIN_FAILURE,
            severity=AuditSeverity.WARNING,
            message=f"Login failed for {email}: {failure_reason}",
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            email=email,
            failure_reason=failure_reason,
            metadata={**metadata, "attempt_count": attempt_count, "logged_by": logged_by}
        )
        
        self.log_audit_event(event)
        
        # Also log as security event if multiple failures
        if attempt_count and attempt_count >= 3:
            security_event = SecurityEvent(
                event_type=SecurityEventType.AUTHENTICATION_FAILURE,
                severity="HIGH",
                description=f"Multiple failed login attempts for {email}",
                ip_address=ip_address,
                user_agent=user_agent,
                correlation_id=correlation_id,
                metadata={"attempt_count": attempt_count, "failure_reason": failure_reason}
            )
            self.security_logger.log_security_event(security_event)
    
    def log_logout_success(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str = None,
        tenant_id: str = None,
        correlation_id: str = None,
        session_id: str = None,
        session_duration_minutes: float = None,
        logged_by: str = "auth_routes",
        **metadata
    ) -> None:
        """Log successful logout event with deduplication"""
        # Check if this event should be logged (not a duplicate)
        if not self.deduplication_service.should_log_authentication_event(
            event_type=EventType.LOGOUT_SUCCESS,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            logged_by=logged_by,
            ttl_seconds=300  # 5 minutes
        ):
            return  # Skip duplicate event
        
        event = AuthenticationAuditEvent(
            event_type=AuditEventType.LOGOUT_SUCCESS,
            severity=AuditSeverity.INFO,
            message=f"User {user_id} logged out successfully",
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            metadata={**metadata, "session_duration_minutes": session_duration_minutes, "logged_by": logged_by}
        )
        
        self.log_audit_event(event)
        self.auth_logger.info(
            f"Logout success: {user_id}",
            user_id=user_id,
            ip_address=ip_address,
            correlation_id=correlation_id
        )
    
    def log_token_refresh_success(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str = None,
        tenant_id: str = None,
        correlation_id: str = None,
        old_token_jti: str = None,
        new_token_jti: str = None,
        logged_by: str = "auth_routes",
        **metadata
    ) -> None:
        """Log successful token refresh with deduplication"""
        # Check if this event should be logged (not a duplicate)
        if not self.deduplication_service.should_log_authentication_event(
            event_type=EventType.TOKEN_REFRESH,
            user_id=user_id,
            ip_address=ip_address,
            logged_by=logged_by,
            ttl_seconds=60  # Short TTL for token refresh events
        ):
            return  # Skip duplicate event
        
        event = AuthenticationAuditEvent(
            event_type=AuditEventType.REFRESH_SUCCESS,
            severity=AuditSeverity.INFO,
            message=f"Token refreshed successfully for user {user_id}",
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            token_type="refresh",
            metadata={
                **metadata,
                "old_token_jti_hash": PIIRedactor.hash_sensitive_data(old_token_jti) if old_token_jti else None,
                "new_token_jti_hash": PIIRedactor.hash_sensitive_data(new_token_jti) if new_token_jti else None,
                "logged_by": logged_by
            }
        )
        
        self.log_audit_event(event)
        self.auth_logger.info(
            f"Token refresh success: {user_id}",
            user_id=user_id,
            ip_address=ip_address,
            correlation_id=correlation_id
        )
    
    def log_token_refresh_failure(
        self,
        ip_address: str,
        failure_reason: str,
        user_agent: str = None,
        correlation_id: str = None,
        token_jti: str = None,
        **metadata
    ) -> None:
        """Log failed token refresh attempt"""
        event = AuthenticationAuditEvent(
            event_type=AuditEventType.REFRESH_FAILURE,
            severity=AuditSeverity.WARNING,
            message=f"Token refresh failed: {failure_reason}",
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            failure_reason=failure_reason,
            token_type="refresh",
            metadata={
                **metadata,
                "token_jti_hash": PIIRedactor.hash_sensitive_data(token_jti) if token_jti else None
            }
        )
        
        self.log_audit_event(event)
    
    def log_token_rotation(
        self,
        user_id: str,
        ip_address: str,
        old_token_jti: str,
        new_access_jti: str,
        new_refresh_jti: str,
        user_agent: str = None,
        tenant_id: str = None,
        correlation_id: str = None,
        **metadata
    ) -> None:
        """Log token rotation event"""
        event = AuthenticationAuditEvent(
            event_type=AuditEventType.TOKEN_ROTATION,
            severity=AuditSeverity.INFO,
            message=f"Tokens rotated for user {user_id}",
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            metadata={
                **metadata,
                "old_token_jti_hash": PIIRedactor.hash_sensitive_data(old_token_jti),
                "new_access_jti_hash": PIIRedactor.hash_sensitive_data(new_access_jti),
                "new_refresh_jti_hash": PIIRedactor.hash_sensitive_data(new_refresh_jti)
            }
        )
        
        self.log_audit_event(event)
    
    def log_session_created(
        self,
        user_id: str,
        session_id: str,
        ip_address: str,
        user_agent: str = None,
        tenant_id: str = None,
        correlation_id: str = None,
        expires_at: datetime = None,
        **metadata
    ) -> None:
        """Log session creation"""
        event = AuthenticationAuditEvent(
            event_type=AuditEventType.SESSION_CREATED,
            severity=AuditSeverity.INFO,
            message=f"Session created for user {user_id}",
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            metadata={
                **metadata,
                "expires_at": expires_at.isoformat() if expires_at else None
            }
        )
        
        self.log_audit_event(event)
    
    def log_session_expired(
        self,
        user_id: str,
        session_id: str,
        ip_address: str = None,
        user_agent: str = None,
        tenant_id: str = None,
        correlation_id: str = None,
        session_duration_minutes: float = None,
        **metadata
    ) -> None:
        """Log session expiration"""
        event = AuthenticationAuditEvent(
            event_type=AuditEventType.SESSION_EXPIRED,
            severity=AuditSeverity.INFO,
            message=f"Session expired for user {user_id}",
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            metadata={
                **metadata,
                "session_duration_minutes": session_duration_minutes
            }
        )
        
        self.log_audit_event(event)
    
    # Intelligent Response Event Logging
    
    def log_error_response_generated(
        self,
        error_category: str,
        error_severity: str,
        provider_name: str = None,
        ai_analysis_used: bool = False,
        response_cached: bool = False,
        user_id: str = None,
        tenant_id: str = None,
        correlation_id: str = None,
        llm_provider: str = None,
        llm_model: str = None,
        generation_time_ms: float = None,
        **metadata
    ) -> None:
        """Log intelligent error response generation"""
        event = IntelligentResponseAuditEvent(
            event_type=AuditEventType.ERROR_RESPONSE_GENERATED,
            severity=AuditSeverity.INFO,
            message=f"Error response generated for {error_category} error",
            user_id=user_id,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            duration_ms=generation_time_ms,
            error_category=error_category,
            error_severity=error_severity,
            provider_name=provider_name,
            ai_analysis_used=ai_analysis_used,
            response_cached=response_cached,
            llm_provider=llm_provider,
            llm_model=llm_model,
            metadata=metadata
        )
        
        self.log_audit_event(event)
        self.response_logger.info(
            f"Error response generated: {error_category}",
            error_category=error_category,
            ai_analysis_used=ai_analysis_used,
            correlation_id=correlation_id
        )
    
    def log_ai_analysis_requested(
        self,
        error_message: str,
        provider_name: str = None,
        user_id: str = None,
        tenant_id: str = None,
        correlation_id: str = None,
        **metadata
    ) -> None:
        """Log AI analysis request"""
        event = IntelligentResponseAuditEvent(
            event_type=AuditEventType.AI_ANALYSIS_REQUESTED,
            severity=AuditSeverity.INFO,
            message="AI analysis requested for error response",
            user_id=user_id,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            provider_name=provider_name,
            ai_analysis_used=True,
            metadata={**metadata, "error_message_hash": PIIRedactor.hash_sensitive_data(error_message)}
        )
        
        self.log_audit_event(event)
    
    def log_ai_analysis_completed(
        self,
        success: bool,
        llm_provider: str,
        llm_model: str,
        generation_time_ms: float,
        user_id: str = None,
        tenant_id: str = None,
        correlation_id: str = None,
        response_quality_score: float = None,
        error_message: str = None,
        **metadata
    ) -> None:
        """Log AI analysis completion"""
        event = IntelligentResponseAuditEvent(
            event_type=AuditEventType.AI_ANALYSIS_COMPLETED,
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            message=f"AI analysis {'completed' if success else 'failed'}",
            user_id=user_id,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            duration_ms=generation_time_ms,
            ai_analysis_used=True,
            llm_provider=llm_provider,
            llm_model=llm_model,
            response_quality_score=response_quality_score,
            metadata={
                **metadata,
                "success": success,
                "error_message": error_message if not success else None
            }
        )
        
        self.log_audit_event(event)
    
    def log_response_cache_event(
        self,
        cache_hit: bool,
        error_category: str = None,
        user_id: str = None,
        tenant_id: str = None,
        correlation_id: str = None,
        **metadata
    ) -> None:
        """Log response cache hit/miss"""
        event_type = AuditEventType.RESPONSE_SERVED_FROM_CACHE if cache_hit else AuditEventType.RESPONSE_CACHED
        
        event = IntelligentResponseAuditEvent(
            event_type=event_type,
            severity=AuditSeverity.INFO,
            message=f"Response {'served from cache' if cache_hit else 'cached'}",
            user_id=user_id,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            error_category=error_category,
            cache_hit=cache_hit,
            response_cached=not cache_hit,
            metadata=metadata
        )
        
        self.log_audit_event(event)
    
    # Performance Event Logging
    
    def log_token_operation_performance(
        self,
        operation_name: str,
        duration_ms: float,
        success: bool = True,
        user_id: str = None,
        tenant_id: str = None,
        correlation_id: str = None,
        error_message: str = None,
        cache_hit: bool = False,
        token_jti: str = None,
        logged_by: str = "token_manager",
        **metadata
    ) -> None:
        """Log token operation performance with deduplication"""
        # Check if this token operation should be logged (not a duplicate)
        if user_id and not self.deduplication_service.should_log_token_operation(
            operation_name=operation_name,
            user_id=user_id,
            token_jti=token_jti,
            logged_by=logged_by,
            ttl_seconds=30  # Short TTL for token operations
        ):
            return  # Skip duplicate event
        
        event = PerformanceAuditEvent(
            event_type=AuditEventType.TOKEN_OPERATION_PERFORMANCE,
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            message=f"Token operation {operation_name} {'completed' if success else 'failed'}",
            user_id=user_id,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            duration_ms=duration_ms,
            operation_name=operation_name,
            operation_type="token",
            success=success,
            error_message=error_message,
            cache_hit=cache_hit,
            metadata={**metadata, "token_jti": token_jti, "logged_by": logged_by}
        )
        
        self.log_audit_event(event)
        
        # Track performance metrics
        if operation_name not in self._performance_metrics:
            self._performance_metrics[operation_name] = []
        self._performance_metrics[operation_name].append(duration_ms)
        
        self.performance_logger.info(
            f"Token operation: {operation_name} - {duration_ms:.2f}ms",
            operation=operation_name,
            duration_ms=duration_ms,
            success=success,
            correlation_id=correlation_id
        )
    
    def log_llm_response_performance(
        self,
        provider: str,
        model: str,
        duration_ms: float,
        success: bool = True,
        user_id: str = None,
        tenant_id: str = None,
        correlation_id: str = None,
        error_message: str = None,
        token_count: int = None,
        **metadata
    ) -> None:
        """Log LLM response performance"""
        event = PerformanceAuditEvent(
            event_type=AuditEventType.LLM_RESPONSE_PERFORMANCE,
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            message=f"LLM response from {provider}/{model} {'completed' if success else 'failed'}",
            user_id=user_id,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            duration_ms=duration_ms,
            operation_name=f"{provider}_{model}",
            operation_type="llm",
            success=success,
            error_message=error_message,
            metadata={
                **metadata,
                "provider": provider,
                "model": model,
                "token_count": token_count
            }
        )
        
        self.log_audit_event(event)
        
        # Track performance metrics
        operation_key = f"llm_{provider}_{model}"
        if operation_key not in self._performance_metrics:
            self._performance_metrics[operation_key] = []
        self._performance_metrics[operation_key].append(duration_ms)
        
        self.performance_logger.info(
            f"LLM response: {provider}/{model} - {duration_ms:.2f}ms",
            provider=provider,
            model=model,
            duration_ms=duration_ms,
            success=success,
            correlation_id=correlation_id
        )
    
    def log_session_validation(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str = None,
        tenant_id: str = None,
        correlation_id: str = None,
        session_id: str = None,
        validation_method: str = "token",
        logged_by: str = "session_validator",
        **metadata
    ) -> None:
        """Log session validation event (separate from login events)"""
        # Check if this session validation should be logged (not a duplicate)
        if not self.deduplication_service.should_log_session_validation(
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            logged_by=logged_by,
            ttl_seconds=60  # Short TTL for session validations
        ):
            return  # Skip duplicate event
        
        event = AuthenticationAuditEvent(
            event_type=AuditEventType.SESSION_CREATED,  # Use session event type, not login
            severity=AuditSeverity.INFO,
            message=f"Session validated for user {user_id}",
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            metadata={
                **metadata, 
                "validation_method": validation_method,
                "logged_by": logged_by,
                "event_category": "session_validation"
            }
        )
        
        self.log_audit_event(event)
        # Don't log to auth_logger to avoid confusion with actual logins

    # Security Event Logging
    
    def log_suspicious_activity(
        self,
        description: str,
        user_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        correlation_id: str = None,
        **metadata
    ) -> None:
        """Log suspicious activity"""
        event = AuditEvent(
            event_type=AuditEventType.SUSPICIOUS_LOGIN_PATTERN,
            severity=AuditSeverity.ERROR,
            message=f"Suspicious activity detected: {description}",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            metadata=metadata
        )
        
        self.log_audit_event(event)
        
        # Also log as security event
        security_event = SecurityEvent(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity="HIGH",
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            metadata=metadata
        )
        self.security_logger.log_security_event(security_event)
    
    def log_rate_limit_exceeded(
        self,
        user_id: str,
        endpoint: str,
        limit: int,
        current_count: int,
        ip_address: str = None,
        correlation_id: str = None,
        **metadata
    ) -> None:
        """Log rate limit exceeded"""
        event = AuditEvent(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            severity=AuditSeverity.WARNING,
            message=f"Rate limit exceeded for user {user_id} on {endpoint}",
            user_id=user_id,
            ip_address=ip_address,
            correlation_id=correlation_id,
            endpoint=endpoint,
            metadata={
                **metadata,
                "limit": limit,
                "current_count": current_count
            }
        )
        
        self.log_audit_event(event)
        
        # Also log as security event
        self.security_logger.log_rate_limit_violation(
            user_id=user_id,
            endpoint=endpoint,
            limit=limit,
            current_count=current_count,
            correlation_id=correlation_id,
            **metadata
        )
    
    # Metrics and Analytics
    
    def get_audit_metrics(self) -> Dict[str, Any]:
        """Get audit metrics summary"""
        return {
            "event_counts": self._event_counts.copy(),
            "performance_metrics": {
                operation: {
                    "count": len(times),
                    "avg_ms": sum(times) / len(times) if times else 0,
                    "min_ms": min(times) if times else 0,
                    "max_ms": max(times) if times else 0
                }
                for operation, times in self._performance_metrics.items()
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def reset_metrics(self) -> None:
        """Reset metrics counters"""
        self._event_counts.clear()
        self._performance_metrics.clear()


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


# Export main classes and functions
__all__ = [
    "AuditLogger",
    "AuditEvent",
    "AuthenticationAuditEvent", 
    "IntelligentResponseAuditEvent",
    "PerformanceAuditEvent",
    "AuditEventType",
    "AuditSeverity",
    "get_audit_logger"
]