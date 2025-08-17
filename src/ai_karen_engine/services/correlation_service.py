"""
Correlation Service for Request Tracking
Provides correlation ID management and request lifecycle tracking.
"""

import uuid
import logging
from contextvars import ContextVar
from typing import Optional, Dict, Any
from enum import Enum

# Context variable for request correlation
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

logger = logging.getLogger(__name__)


class Phase(str, Enum):
    """Authentication lifecycle phases"""
    START = "start"
    FINISH = "finish"


class CorrelationService:
    """Service for managing request correlation and tracking"""
    
    @staticmethod
    def get_or_create_correlation_id(headers: Dict[str, str]) -> str:
        """Get correlation ID from headers or create a new one"""
        correlation_id = headers.get("x-correlation-id") or headers.get("x-request-id")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        return correlation_id
    
    @staticmethod
    def set_correlation_id(correlation_id: str) -> None:
        """Set correlation ID in context"""
        request_id_ctx.set(correlation_id)
    
    @staticmethod
    def get_correlation_id() -> str:
        """Get correlation ID from context"""
        correlation_id = request_id_ctx.get()
        return correlation_id or str(uuid.uuid4())


def get_request_id() -> str:
    """Get current request ID from context"""
    rid = request_id_ctx.get()
    return rid or str(uuid.uuid4())


def auth_event(
    event_type: str,
    phase: Phase,
    *,
    success: Optional[bool] = None,
    level: Optional[int] = None,
    **fields: Any
) -> None:
    """
    Log authentication events with proper lifecycle management.
    
    Args:
        event_type: Type of auth event (e.g., 'session_validated')
        phase: Lifecycle phase (start or finish)
        success: Success status (None for start, bool for finish)
        level: Log level override
        **fields: Additional event fields
    """
    rid = fields.pop("request_id", None) or get_request_id()
    
    # Enforce lifecycle contract
    if phase == Phase.START:
        success = None  # Never set success on start
        level = level or logging.INFO
        msg = f"AUTH_EVENT: {event_type} START"
    else:
        # finish phase must carry success
        if success is None:
            success = False
        msg = f"AUTH_EVENT: {event_type} {'SUCCESS' if success else 'FAILED'}"
        level = level or (logging.INFO if success else logging.WARNING)
    
    payload: Dict[str, Any] = dict(
        event_id=rid,
        request_id=rid,
        event_type=event_type,
        phase=phase.value,
        success=success,
        **fields,
    )
    
    # Get auth logger
    auth_logger = logging.getLogger("ai_karen_engine.auth")
    auth_logger.log(level, msg, extra={"auth_event": payload, **payload})


def create_correlation_logger(name: str) -> logging.Logger:
    """Create a logger that includes correlation ID in all messages"""
    logger = logging.getLogger(name)
    
    class CorrelationFilter(logging.Filter):
        def filter(self, record):
            record.correlation_id = get_request_id()
            return True
    
    logger.addFilter(CorrelationFilter())
    return logger


# Correlation tracker for complex operations
class CorrelationTracker:
    """Track complex operations across multiple phases"""
    
    def __init__(self):
        self.traces: Dict[str, Dict[str, Any]] = {}
    
    def start_trace(self, correlation_id: str, operation: str, metadata: Dict[str, Any]) -> None:
        """Start tracking an operation"""
        self.traces[correlation_id] = {
            "operation": operation,
            "start_time": logging.time.time(),
            "metadata": metadata,
            "phases": []
        }
    
    def add_phase(self, correlation_id: str, phase: str, data: Dict[str, Any]) -> None:
        """Add a phase to the trace"""
        if correlation_id in self.traces:
            self.traces[correlation_id]["phases"].append({
                "phase": phase,
                "timestamp": logging.time.time(),
                "data": data
            })
    
    def end_trace(self, correlation_id: str, status: str, final_data: Dict[str, Any]) -> None:
        """End tracking an operation"""
        if correlation_id in self.traces:
            trace = self.traces.pop(correlation_id)
            total_duration = logging.time.time() - trace["start_time"]
            
            logger.info(
                f"Operation {trace['operation']} completed",
                extra={
                    "correlation_id": correlation_id,
                    "operation": trace["operation"],
                    "status": status,
                    "total_duration": total_duration,
                    "phases": trace["phases"],
                    "final_data": final_data
                }
            )


# Global tracker instance
_correlation_tracker = CorrelationTracker()


def get_correlation_tracker() -> CorrelationTracker:
    """Get the global correlation tracker"""
    return _correlation_tracker