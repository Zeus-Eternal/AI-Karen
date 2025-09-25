"""
Audit Logger Service

This module provides comprehensive audit logging for copilot operations
with correlation IDs, structured logging, and security event tracking.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    """Audit event data structure."""
    event_type: str
    user_id: Optional[str]
    session_id: Optional[str]
    correlation_id: str
    timestamp: datetime
    details: Dict[str, Any]
    
    # Security and context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    surface: Optional[str] = None  # "chat", "copilot", "api"
    
    # Result information
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class AuditLogger:
    """
    Comprehensive audit logger for copilot operations.
    
    Provides structured logging with correlation IDs, security event tracking,
    and configurable output formats for compliance and monitoring.
    """
    
    def __init__(self, log_dir: Optional[Path] = None, enable_file_logging: bool = True):
        """
        Initialize audit logger.
        
        Args:
            log_dir: Directory for audit log files (default: logs/audit)
            enable_file_logging: Whether to write audit logs to files
        """
        self.log_dir = log_dir or Path("logs/audit")
        self.enable_file_logging = enable_file_logging
        
        if self.enable_file_logging:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure structured logger
        self.audit_logger = logging.getLogger("kari.audit")
        self.audit_logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers and propagation
        self.audit_logger.propagate = False
        
        # Check if handlers already exist to prevent duplicates
        existing_handlers = [h for h in self.audit_logger.handlers if isinstance(h, logging.FileHandler)]
        if not existing_handlers and self.enable_file_logging:
            self._setup_file_handler()
        
        # Event type registry for validation
        self.registered_event_types = {
            # Copilot events
            "copilot.api_key.set",
            "copilot.api_key.removed",
            "copilot.cloud_toggle",
            "copilot.profile.changed",
            "copilot.action.started",
            "copilot.action.completed",
            "copilot.action.failed",
            
            # LLM routing events
            "llm.route.decision",
            "llm.route.fallback",
            "llm.route.error",
            
            # Security events
            "auth.login.success",
            "auth.login.failed",
            "auth.permission.denied",
            "settings.modified",
            "secret.accessed",
            "secret.validation.failed",
            "secret.format.invalid",
            
            # System events
            "system.startup",
            "system.shutdown",
            "system.error",
            
            # Additional copilot security events
            "copilot.policy.violation",
            "copilot.provider.blocked",
            "copilot.routing.denied"
        }
    
    def _setup_file_handler(self) -> None:
        """Setup file handler for audit logging."""
        try:
            # Create daily rotating log file
            log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # JSON formatter for structured logging
            formatter = logging.Formatter('%(message)s')
            file_handler.setFormatter(formatter)
            
            self.audit_logger.addHandler(file_handler)
            
        except Exception as e:
            logger.error(f"Failed to setup audit file handler: {e}")
    
    async def log_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        surface: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event (must be registered)
            user_id: ID of the user performing the action
            session_id: Session ID for the action
            details: Additional event details
            correlation_id: Correlation ID for tracking related events
            ip_address: Client IP address
            user_agent: Client user agent
            surface: Interface used (chat, copilot, api)
            success: Whether the action was successful
            error_message: Error message if action failed
            
        Returns:
            Correlation ID for the logged event
        """
        # Generate correlation ID if not provided
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Validate event type
        if event_type not in self.registered_event_types:
            logger.warning(f"Unregistered audit event type: {event_type}")
        
        # Create audit event
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            correlation_id=correlation_id,
            timestamp=datetime.utcnow(),
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            surface=surface,
            success=success,
            error_message=error_message
        )
        
        # Log the event
        await self._write_audit_event(event)
        
        return correlation_id
    
    async def _write_audit_event(self, event: AuditEvent) -> None:
        """Write audit event to configured outputs."""
        try:
            # Convert to JSON for structured logging
            event_json = json.dumps(event.to_dict(), ensure_ascii=False)
            
            # Log to structured logger (will go to file if configured)
            self.audit_logger.info(event_json)
            
            # Also log to main logger for debugging
            logger.debug(f"Audit event: {event.event_type} - {event.correlation_id}")
            
        except Exception as e:
            logger.error(f"Failed to write audit event: {e}")
    
    async def log_copilot_action(
        self,
        action_type: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        capability: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        files_affected: Optional[List[str]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Log a copilot action with standardized details.
        
        Args:
            action_type: Type of copilot action (started, completed, failed)
            user_id: User performing the action
            session_id: Session ID
            capability: Copilot capability used
            provider: LLM provider used
            model: Model used
            files_affected: List of files affected by the action
            success: Whether action was successful
            error_message: Error message if failed
            correlation_id: Correlation ID for tracking
            
        Returns:
            Correlation ID for the logged event
        """
        details = {
            "capability": capability,
            "provider": provider,
            "model": model,
            "files_affected": files_affected or [],
            "file_count": len(files_affected) if files_affected else 0
        }
        
        return await self.log_event(
            event_type=f"copilot.action.{action_type}",
            user_id=user_id,
            session_id=session_id,
            details=details,
            correlation_id=correlation_id,
            success=success,
            error_message=error_message
        )
    
    async def log_llm_routing(
        self,
        decision_type: str,
        provider: str,
        model: str,
        routing_reason: str,
        confidence: float,
        privacy_level: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Log LLM routing decision.
        
        Args:
            decision_type: Type of routing decision (decision, fallback, error)
            provider: Selected provider
            model: Selected model
            routing_reason: Reason for routing decision
            confidence: Confidence score
            privacy_level: Privacy level constraint
            user_id: User ID
            session_id: Session ID
            correlation_id: Correlation ID
            
        Returns:
            Correlation ID for the logged event
        """
        details = {
            "provider": provider,
            "model": model,
            "routing_reason": routing_reason,
            "confidence": confidence,
            "privacy_level": privacy_level
        }
        
        return await self.log_event(
            event_type=f"llm.route.{decision_type}",
            user_id=user_id,
            session_id=session_id,
            details=details,
            correlation_id=correlation_id
        )
    
    async def log_settings_change(
        self,
        setting_name: str,
        old_value: Any,
        new_value: Any,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Log settings modification.
        
        Args:
            setting_name: Name of the setting changed
            old_value: Previous value (will be masked if sensitive)
            new_value: New value (will be masked if sensitive)
            user_id: User making the change
            correlation_id: Correlation ID
            
        Returns:
            Correlation ID for the logged event
        """
        # Mask sensitive values
        masked_old = self._mask_sensitive_value(setting_name, old_value)
        masked_new = self._mask_sensitive_value(setting_name, new_value)
        
        details = {
            "setting_name": setting_name,
            "old_value": masked_old,
            "new_value": masked_new,
            "is_sensitive": self._is_sensitive_setting(setting_name)
        }
        
        return await self.log_event(
            event_type="settings.modified",
            user_id=user_id,
            details=details,
            correlation_id=correlation_id
        )
    
    def _mask_sensitive_value(self, setting_name: str, value: Any) -> Any:
        """Mask sensitive values in audit logs."""
        if self._is_sensitive_setting(setting_name):
            if isinstance(value, str) and value:
                return f"***{value[-4:]}" if len(value) > 4 else "***"
            elif value is not None:
                return "***MASKED***"
        return value
    
    def _is_sensitive_setting(self, setting_name: str) -> bool:
        """Check if a setting contains sensitive data."""
        sensitive_keywords = ["key", "secret", "password", "token", "credential"]
        return any(keyword in setting_name.lower() for keyword in sensitive_keywords)
    
    async def get_audit_events(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit events based on filters.
        
        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            session_id: Filter by session ID
            correlation_id: Filter by correlation ID
            start_time: Filter events after this time
            end_time: Filter events before this time
            limit: Maximum number of events to return
            
        Returns:
            List of audit events matching the filters
        """
        # This is a simplified implementation
        # In production, this would query a database or log aggregation system
        events = []
        
        try:
            # Read from current day's log file
            log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
            
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            event_data = json.loads(line.strip())
                            
                            # Apply filters
                            if event_type and event_data.get('event_type') != event_type:
                                continue
                            
                            if user_id and event_data.get('user_id') != user_id:
                                continue
                            
                            if session_id and event_data.get('session_id') != session_id:
                                continue
                            
                            if correlation_id and event_data.get('correlation_id') != correlation_id:
                                continue
                            
                            # Time filters would be applied here
                            
                            events.append(event_data)
                            
                            if len(events) >= limit:
                                break
                                
                        except json.JSONDecodeError:
                            continue
            
        except Exception as e:
            logger.error(f"Failed to retrieve audit events: {e}")
        
        return events
    
    async def log_security_validation(
        self,
        validation_type: str,
        success: bool,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Log security validation events.
        
        Args:
            validation_type: Type of validation (api_key, format, policy)
            success: Whether validation passed
            details: Validation details and results
            user_id: User performing the action
            correlation_id: Correlation ID
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Correlation ID for the logged event
        """
        event_type = f"secret.validation.{'passed' if success else 'failed'}"
        if validation_type == "format":
            event_type = f"secret.format.{'valid' if success else 'invalid'}"
        elif validation_type == "policy":
            event_type = f"copilot.policy.{'allowed' if success else 'violation'}"
        
        return await self.log_event(
            event_type=event_type,
            user_id=user_id,
            details={
                "validation_type": validation_type,
                **details
            },
            correlation_id=correlation_id,
            ip_address=ip_address,
            user_agent=user_agent,
            surface="api",
            success=success
        )
    
    async def log_provider_routing(
        self,
        provider: str,
        model: str,
        routing_decision: str,
        policy_applied: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Log LLM provider routing decisions with policy enforcement.
        
        Args:
            provider: Selected provider
            model: Selected model
            routing_decision: Routing decision made
            policy_applied: Policy that was applied
            user_id: User ID
            session_id: Session ID
            correlation_id: Correlation ID
            
        Returns:
            Correlation ID for the logged event
        """
        details = {
            "provider": provider,
            "model": model,
            "routing_decision": routing_decision,
            "policy_applied": policy_applied,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return await self.log_event(
            event_type="llm.route.decision",
            user_id=user_id,
            session_id=session_id,
            details=details,
            correlation_id=correlation_id,
            surface="copilot"
        )
    
    async def log_correlation_chain(
        self,
        correlation_id: str,
        operation_type: str,
        step: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log a step in a correlation chain for tracking operations across services.
        
        Args:
            correlation_id: Correlation ID linking related operations
            operation_type: Type of operation (copilot_action, settings_change, etc.)
            step: Current step in the operation
            details: Step-specific details
            user_id: User performing the operation
            success: Whether this step was successful
            error_message: Error message if step failed
        """
        await self.log_event(
            event_type=f"{operation_type}.step",
            user_id=user_id,
            details={
                "operation_type": operation_type,
                "step": step,
                "step_details": details
            },
            correlation_id=correlation_id,
            success=success,
            error_message=error_message,
            surface="system"
        )
    
    async def get_audit_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get audit summary statistics.
        
        Args:
            start_time: Start time for summary
            end_time: End time for summary
            
        Returns:
            Dictionary with audit statistics
        """
        # This would be implemented with proper log aggregation in production
        return {
            "total_events": 0,
            "event_types": {},
            "users": {},
            "success_rate": 0.0,
            "time_range": {
                "start": start_time.isoformat() if start_time else None,
                "end": end_time.isoformat() if end_time else None
            }
        }
    
    async def get_correlation_events(
        self,
        correlation_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all events for a specific correlation ID.
        
        Args:
            correlation_id: Correlation ID to search for
            limit: Maximum number of events to return
            
        Returns:
            List of events with the same correlation ID
        """
        return await self.get_audit_events(
            correlation_id=correlation_id,
            limit=limit
        )
    
    async def get_security_events(
        self,
        event_types: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get security-related audit events.
        
        Args:
            event_types: Specific security event types to filter
            user_id: Filter by user ID
            start_time: Filter events after this time
            end_time: Filter events before this time
            limit: Maximum number of events to return
            
        Returns:
            List of security events
        """
        security_event_types = [
            "auth.login.failed",
            "auth.permission.denied", 
            "secret.validation.failed",
            "secret.format.invalid",
            "copilot.policy.violation",
            "copilot.provider.blocked",
            "copilot.routing.denied"
        ]
        
        if event_types:
            # Filter to only security events
            event_types = [et for et in event_types if et in security_event_types]
        else:
            event_types = security_event_types
        
        all_events = []
        for event_type in event_types:
            events = await self.get_audit_events(
                event_type=event_type,
                user_id=user_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
            all_events.extend(events)
        
        # Sort by timestamp and limit
        all_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return all_events[:limit]


# Global audit logger instance
_audit_logger_instance: Optional[AuditLogger] = None
_audit_logger_lock = False


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger_instance, _audit_logger_lock
    if _audit_logger_instance is None and not _audit_logger_lock:
        _audit_logger_lock = True
        try:
            _audit_logger_instance = AuditLogger()
        finally:
            _audit_logger_lock = False
    return _audit_logger_instance