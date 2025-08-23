"""
Correlation Service

This module provides correlation ID tracking for copilot operations
across services with structured logging and audit trail support.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Phase(Enum):
    """Operation phases for correlation tracking."""
    START = "start"
    PROCESSING = "processing"
    FINISH = "finish"
    ERROR = "error"


@dataclass
class CorrelationContext:
    """Context information for correlated operations."""
    correlation_id: str
    operation_type: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Request context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    surface: Optional[str] = None  # "chat", "copilot", "api"
    
    # Operation tracking
    started_at: datetime = field(default_factory=datetime.utcnow)
    current_phase: Phase = Phase.START
    steps_completed: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class CorrelationService:
    """
    Service for tracking operations across multiple services with correlation IDs.
    """
    
    def __init__(self):
        """Initialize correlation service."""
        self.active_operations: Dict[str, CorrelationContext] = {}
        self.operation_history: List[CorrelationContext] = []
        self.max_history_size = 1000
    
    def start_operation(
        self,
        operation_type: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        surface: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start tracking a new operation.
        
        Args:
            operation_type: Type of operation (e.g., "copilot_action", "settings_change")
            user_id: User performing the operation
            session_id: Session ID
            ip_address: Client IP address
            user_agent: Client user agent
            surface: Interface used
            correlation_id: Existing correlation ID (generates new if None)
            metadata: Additional metadata
            
        Returns:
            Correlation ID for the operation
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        context = CorrelationContext(
            correlation_id=correlation_id,
            operation_type=operation_type,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            surface=surface,
            metadata=metadata or {}
        )
        
        self.active_operations[correlation_id] = context
        
        logger.info(
            f"Started operation: {operation_type}",
            extra={
                "correlation_id": correlation_id,
                "operation_type": operation_type,
                "user_id": user_id,
                "surface": surface
            }
        )
        
        return correlation_id
    
    def update_operation(
        self,
        correlation_id: str,
        phase: Phase,
        step: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an operation's phase and progress.
        
        Args:
            correlation_id: Correlation ID of the operation
            phase: Current phase of the operation
            step: Current step being performed
            metadata: Additional metadata to merge
            
        Returns:
            True if operation was found and updated, False otherwise
        """
        if correlation_id not in self.active_operations:
            logger.warning(f"Attempted to update unknown operation: {correlation_id}")
            return False
        
        context = self.active_operations[correlation_id]
        context.current_phase = phase
        
        if step:
            context.steps_completed.append(f"{datetime.utcnow().isoformat()}: {step}")
        
        if metadata:
            context.metadata.update(metadata)
        
        logger.debug(
            f"Updated operation: {context.operation_type} - {phase.value}",
            extra={
                "correlation_id": correlation_id,
                "operation_type": context.operation_type,
                "phase": phase.value,
                "step": step
            }
        )
        
        return True
    
    def complete_operation(
        self,
        correlation_id: str,
        success: bool = True,
        error_message: Optional[str] = None,
        result_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Complete an operation and move it to history.
        
        Args:
            correlation_id: Correlation ID of the operation
            success: Whether the operation completed successfully
            error_message: Error message if operation failed
            result_metadata: Final result metadata
            
        Returns:
            True if operation was found and completed, False otherwise
        """
        if correlation_id not in self.active_operations:
            logger.warning(f"Attempted to complete unknown operation: {correlation_id}")
            return False
        
        context = self.active_operations[correlation_id]
        context.current_phase = Phase.FINISH if success else Phase.ERROR
        
        if result_metadata:
            context.metadata.update(result_metadata)
        
        if error_message:
            context.metadata["error_message"] = error_message
        
        # Add completion metadata
        context.metadata.update({
            "completed_at": datetime.utcnow().isoformat(),
            "success": success,
            "duration_seconds": (datetime.utcnow() - context.started_at).total_seconds()
        })
        
        # Move to history
        self.operation_history.append(context)
        del self.active_operations[correlation_id]
        
        # Trim history if needed
        if len(self.operation_history) > self.max_history_size:
            self.operation_history = self.operation_history[-self.max_history_size:]
        
        logger.info(
            f"Completed operation: {context.operation_type}",
            extra={
                "correlation_id": correlation_id,
                "operation_type": context.operation_type,
                "success": success,
                "duration_seconds": context.metadata["duration_seconds"]
            }
        )
        
        return True
    
    def get_operation_context(self, correlation_id: str) -> Optional[CorrelationContext]:
        """
        Get context for an active operation.
        
        Args:
            correlation_id: Correlation ID to look up
            
        Returns:
            CorrelationContext if found, None otherwise
        """
        return self.active_operations.get(correlation_id)
    
    def get_operation_history(
        self,
        operation_type: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[CorrelationContext]:
        """
        Get operation history with optional filtering.
        
        Args:
            operation_type: Filter by operation type
            user_id: Filter by user ID
            limit: Maximum number of operations to return
            
        Returns:
            List of historical operations
        """
        filtered_history = self.operation_history
        
        if operation_type:
            filtered_history = [op for op in filtered_history if op.operation_type == operation_type]
        
        if user_id:
            filtered_history = [op for op in filtered_history if op.user_id == user_id]
        
        # Sort by start time (most recent first) and limit
        filtered_history.sort(key=lambda x: x.started_at, reverse=True)
        return filtered_history[:limit]
    
    def get_active_operations(
        self,
        operation_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[CorrelationContext]:
        """
        Get currently active operations with optional filtering.
        
        Args:
            operation_type: Filter by operation type
            user_id: Filter by user ID
            
        Returns:
            List of active operations
        """
        operations = list(self.active_operations.values())
        
        if operation_type:
            operations = [op for op in operations if op.operation_type == operation_type]
        
        if user_id:
            operations = [op for op in operations if op.user_id == user_id]
        
        return operations
    
    def cleanup_stale_operations(self, max_age_hours: int = 24) -> int:
        """
        Clean up operations that have been active for too long.
        
        Args:
            max_age_hours: Maximum age in hours before considering stale
            
        Returns:
            Number of operations cleaned up
        """
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        stale_operations = []
        
        for correlation_id, context in self.active_operations.items():
            if context.started_at < cutoff_time:
                stale_operations.append(correlation_id)
        
        # Move stale operations to history with error status
        for correlation_id in stale_operations:
            context = self.active_operations[correlation_id]
            context.current_phase = Phase.ERROR
            context.metadata.update({
                "error_message": "Operation timed out",
                "completed_at": datetime.utcnow().isoformat(),
                "success": False,
                "stale_cleanup": True
            })
            
            self.operation_history.append(context)
            del self.active_operations[correlation_id]
        
        if stale_operations:
            logger.warning(f"Cleaned up {len(stale_operations)} stale operations")
        
        return len(stale_operations)


# Global correlation service instance
_correlation_service_instance: Optional[CorrelationService] = None


def get_correlation_service() -> CorrelationService:
    """Get global correlation service instance."""
    global _correlation_service_instance
    if _correlation_service_instance is None:
        _correlation_service_instance = CorrelationService()
    return _correlation_service_instance


def get_request_id() -> str:
    """Generate a new request/correlation ID."""
    return str(uuid.uuid4())


# Convenience functions for common operations
def start_copilot_operation(
    capability: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    surface: str = "copilot",
    files: Optional[List[str]] = None
) -> str:
    """Start tracking a copilot operation."""
    correlation_service = get_correlation_service()
    
    metadata = {
        "capability": capability,
        "files_count": len(files) if files else 0
    }
    
    if files:
        metadata["files"] = files
    
    return correlation_service.start_operation(
        operation_type="copilot_action",
        user_id=user_id,
        session_id=session_id,
        ip_address=ip_address,
        user_agent=user_agent,
        surface=surface,
        metadata=metadata
    )


def start_settings_operation(
    setting_type: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> str:
    """Start tracking a settings change operation."""
    correlation_service = get_correlation_service()
    
    return correlation_service.start_operation(
        operation_type="settings_change",
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        surface="api",
        metadata={"setting_type": setting_type}
    )


def auth_event(
    event_name: str,
    phase: Phase,
    success: Optional[bool] = None,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    auth_method: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
    processing_time_ms: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    risk_score: Optional[float] = None,
    security_flags: Optional[List[str]] = None,
    blocked_by_security: Optional[bool] = None,
    service_version: Optional[str] = None
) -> None:
    """
    Log authentication events with correlation tracking.
    
    This function provides compatibility with the existing auth event logging
    while integrating with the correlation service.
    """
    correlation_service = get_correlation_service()
    
    # Create or update correlation context
    if request_id:
        if phase == Phase.START:
            correlation_service.start_operation(
                operation_type="auth_event",
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                surface="auth",
                correlation_id=request_id,
                metadata={
                    "event_name": event_name,
                    "auth_method": auth_method,
                    "email": email,
                    "service_version": service_version
                }
            )
        else:
            # Update existing operation
            update_metadata = {
                "phase": phase.value,
                "success": success,
                "processing_time_ms": processing_time_ms,
                "risk_score": risk_score,
                "security_flags": security_flags or [],
                "blocked_by_security": blocked_by_security
            }
            
            if details:
                update_metadata.update(details)
            
            if error:
                update_metadata["error"] = error
            
            correlation_service.update_operation(
                correlation_id=request_id,
                phase=phase,
                step=f"{event_name}_{phase.value}",
                metadata=update_metadata
            )
            
            # Complete operation if this is the final phase
            if phase in [Phase.FINISH, Phase.ERROR]:
                correlation_service.complete_operation(
                    correlation_id=request_id,
                    success=success if success is not None else phase == Phase.FINISH,
                    error_message=error,
                    result_metadata=update_metadata
                )
    
    # Log the event
    logger.info(
        f"Auth event: {event_name} - {phase.value}",
        extra={
            "event_name": event_name,
            "phase": phase.value,
            "success": success,
            "user_id": user_id,
            "email": email,
            "auth_method": auth_method,
            "request_id": request_id,
            "processing_time_ms": processing_time_ms,
            "risk_score": risk_score,
            "security_flags": security_flags,
            "blocked_by_security": blocked_by_security
        }
    )