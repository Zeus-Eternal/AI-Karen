"""
Correlation Service Facade
Provides correlation ID management and tracking for distributed tracing.
"""

import logging
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

@dataclass
class TraceSpan:
    """Single span in a trace"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation: str
    start_time: float
    end_time: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    status: str = "running"  # running, success, error

@dataclass
class TraceContext:
    """Context for a trace"""
    trace_id: str
    operation: str
    start_time: float
    end_time: Optional[float] = None
    status: str = "running"  # running, success, error
    tags: Dict[str, Any] = field(default_factory=dict)
    spans: List[TraceSpan] = field(default_factory=list)

class CorrelationService:
    """
    Correlation service facade.
    Provides correlation ID management and distributed tracing.
    """
    
    def __init__(self):
        """Initialize the correlation service"""
        self.logger = logging.getLogger(__name__)
        self._active_traces: Dict[str, TraceContext] = {}
        self._correlation_id_context = threading.local()
        
    def get_or_create_correlation_id(self, headers: Dict[str, str]) -> str:
        """
        Get or create a correlation ID from request headers
        
        Args:
            headers: Request headers
            
        Returns:
            Correlation ID
        """
        # Try to get from headers
        correlation_id = headers.get("X-Correlation-Id") or headers.get("X-Request-ID")
        
        if not correlation_id:
            # Try to get from thread-local context
            correlation_id = getattr(self._correlation_id_context, "correlation_id", None)
            
        if not correlation_id:
            # Create a new one
            correlation_id = str(uuid.uuid4())
            
        # Store in thread-local context
        self._correlation_id_context.correlation_id = correlation_id
        
        return correlation_id
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """
        Set the correlation ID in the current context
        
        Args:
            correlation_id: Correlation ID to set
        """
        self._correlation_id_context.correlation_id = correlation_id
        
    def get_current_correlation_id(self) -> Optional[str]:
        """
        Get the current correlation ID from context
        
        Returns:
            Current correlation ID or None
        """
        return getattr(self._correlation_id_context, "correlation_id", None)
    
    def start_trace(
        self,
        correlation_id: str,
        operation: str,
        tags: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Start a new trace
        
        Args:
            correlation_id: Correlation ID for the trace
            operation: Operation being traced
            tags: Optional tags for the trace
        """
        if correlation_id in self._active_traces:
            self.logger.warning(f"Trace already exists for correlation ID: {correlation_id}")
            return
            
        trace = TraceContext(
            trace_id=correlation_id,
            operation=operation,
            start_time=datetime.utcnow().timestamp(),
            tags=tags or {}
        )
        
        self._active_traces[correlation_id] = trace
        
    def end_trace(
        self,
        correlation_id: str,
        status: str,
        tags: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        End a trace
        
        Args:
            correlation_id: Correlation ID for the trace
            status: Status of the trace
            tags: Optional tags to add to the trace
        """
        trace = self._active_traces.get(correlation_id)
        if not trace:
            self.logger.warning(f"No active trace found for correlation ID: {correlation_id}")
            return
            
        trace.end_time = datetime.utcnow().timestamp()
        trace.status = status
        
        if tags:
            trace.tags.update(tags)
            
        # Log the completed trace
        duration = trace.end_time - trace.start_time
        self.logger.info(
            f"Trace completed: {correlation_id} - {trace.operation} - {status} - {duration:.3f}s",
            extra={
                "correlation_id": correlation_id,
                "operation": trace.operation,
                "status": status,
                "duration_ms": duration * 1000,
                "tags": trace.tags,
                "spans_count": len(trace.spans)
            }
        )
        
        # Remove from active traces
        del self._active_traces[correlation_id]
    
    def start_span(
        self,
        correlation_id: str,
        operation: str,
        parent_span_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new span within a trace
        
        Args:
            correlation_id: Correlation ID for the trace
            operation: Operation for the span
            parent_span_id: Optional parent span ID
            tags: Optional tags for the span
            
        Returns:
            Span ID
        """
        trace = self._active_traces.get(correlation_id)
        if not trace:
            self.logger.warning(f"No active trace found for correlation ID: {correlation_id}")
            return str(uuid.uuid4())
            
        span_id = str(uuid.uuid4())
        span = TraceSpan(
            trace_id=correlation_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation=operation,
            start_time=datetime.utcnow().timestamp(),
            tags=tags or {}
        )
        
        trace.spans.append(span)
        return span_id
    
    def end_span(
        self,
        correlation_id: str,
        span_id: str,
        status: str = "success",
        tags: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        End a span within a trace
        
        Args:
            correlation_id: Correlation ID for the trace
            span_id: ID of the span to end
            status: Status of the span
            tags: Optional tags to add to the span
        """
        trace = self._active_traces.get(correlation_id)
        if not trace:
            self.logger.warning(f"No active trace found for correlation ID: {correlation_id}")
            return
            
        # Find the span
        span = None
        for s in trace.spans:
            if s.span_id == span_id:
                span = s
                break
                
        if not span:
            self.logger.warning(f"No span found with ID: {span_id}")
            return
            
        span.end_time = datetime.utcnow().timestamp()
        span.status = status
        
        if tags:
            span.tags.update(tags)
    
    def get_trace(self, correlation_id: str) -> Optional[TraceContext]:
        """
        Get a trace by correlation ID
        
        Args:
            correlation_id: Correlation ID
            
        Returns:
            Trace context or None if not found
        """
        return self._active_traces.get(correlation_id)
    
    def get_active_traces(self) -> List[TraceContext]:
        """
        Get all active traces
        
        Returns:
            List of active traces
        """
        return list(self._active_traces.values())

class CorrelationTracker:
    """
    Helper class for tracking correlations in a specific context
    """
    
    def __init__(self, correlation_service: CorrelationService):
        """
        Initialize the correlation tracker
        
        Args:
            correlation_service: Correlation service instance
        """
        self.correlation_service = correlation_service
        
    def start_trace(
        self,
        correlation_id: str,
        operation: str,
        tags: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Start a new trace
        
        Args:
            correlation_id: Correlation ID for the trace
            operation: Operation being traced
            tags: Optional tags for the trace
        """
        self.correlation_service.start_trace(correlation_id, operation, tags)
        
    def end_trace(
        self,
        correlation_id: str,
        status: str,
        tags: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        End a trace
        
        Args:
            correlation_id: Correlation ID for the trace
            status: Status of the trace
            tags: Optional tags to add to the trace
        """
        self.correlation_service.end_trace(correlation_id, status, tags)

# Global instances
_correlation_service: Optional[CorrelationService] = None
_correlation_tracker: Optional[CorrelationTracker] = None

def get_correlation_service() -> CorrelationService:
    """Get the global correlation service instance"""
    global _correlation_service
    if _correlation_service is None:
        _correlation_service = CorrelationService()
    return _correlation_service

def get_correlation_tracker() -> CorrelationTracker:
    """Get the global correlation tracker instance"""
    global _correlation_tracker
    if _correlation_tracker is None:
        _correlation_tracker = CorrelationTracker(get_correlation_service())
    return _correlation_tracker

def create_correlation_logger(name: str) -> logging.Logger:
    """
    Create a logger that automatically includes correlation ID
    
    Args:
        name: Logger name
        
    Returns:
        Logger with correlation ID filter
    """
    logger = logging.getLogger(name)
    
    class CorrelationFilter(logging.Filter):
        def filter(self, record):
            correlation_service = get_correlation_service()
            correlation_id = correlation_service.get_current_correlation_id()
            if correlation_id:
                record.correlation_id = correlation_id
            else:
                record.correlation_id = ""
            return True
    
    logger.addFilter(CorrelationFilter())
    return logger