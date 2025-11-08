"""
Extension Debugging Models

Data models for debugging, monitoring, and diagnostic information.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json


class LogLevel(Enum):
    """Log levels for extension logging."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TraceEventType(Enum):
    """Types of trace events."""
    FUNCTION_CALL = "function_call"
    API_REQUEST = "api_request"
    DATABASE_QUERY = "database_query"
    PLUGIN_EXECUTION = "plugin_execution"
    BACKGROUND_TASK = "background_task"
    ERROR = "error"
    CUSTOM = "custom"


@dataclass
class LogEntry:
    """Represents a log entry from an extension."""
    id: str
    extension_id: str
    extension_name: str
    timestamp: datetime
    level: LogLevel
    message: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary."""
        return {
            'id': self.id,
            'extension_id': self.extension_id,
            'extension_name': self.extension_name,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'message': self.message,
            'source': self.source,
            'metadata': self.metadata,
            'stack_trace': self.stack_trace,
            'correlation_id': self.correlation_id,
            'user_id': self.user_id,
            'tenant_id': self.tenant_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create log entry from dictionary."""
        return cls(
            id=data['id'],
            extension_id=data['extension_id'],
            extension_name=data['extension_name'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            level=LogLevel(data['level']),
            message=data['message'],
            source=data['source'],
            metadata=data.get('metadata', {}),
            stack_trace=data.get('stack_trace'),
            correlation_id=data.get('correlation_id'),
            user_id=data.get('user_id'),
            tenant_id=data.get('tenant_id')
        )


@dataclass
class MetricPoint:
    """Represents a single metric data point."""
    extension_id: str
    metric_name: str
    value: Union[int, float]
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric point to dictionary."""
        return {
            'extension_id': self.extension_id,
            'metric_name': self.metric_name,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags,
            'metadata': self.metadata
        }


@dataclass
class ErrorRecord:
    """Represents an error that occurred in an extension."""
    id: str
    extension_id: str
    extension_name: str
    timestamp: datetime
    error_type: str
    error_message: str
    stack_trace: str
    context: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    resolved: bool = False
    resolution_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error record to dictionary."""
        return {
            'id': self.id,
            'extension_id': self.extension_id,
            'extension_name': self.extension_name,
            'timestamp': self.timestamp.isoformat(),
            'error_type': self.error_type,
            'error_message': self.error_message,
            'stack_trace': self.stack_trace,
            'context': self.context,
            'correlation_id': self.correlation_id,
            'user_id': self.user_id,
            'tenant_id': self.tenant_id,
            'resolved': self.resolved,
            'resolution_notes': self.resolution_notes
        }


@dataclass
class TraceEvent:
    """Represents a trace event in extension execution."""
    id: str
    extension_id: str
    trace_id: str
    parent_id: Optional[str]
    event_type: TraceEventType
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: str = "started"  # started, completed, failed
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    
    def complete(self, status: str = "completed", metadata: Optional[Dict[str, Any]] = None):
        """Mark the trace event as completed."""
        self.end_time = datetime.utcnow()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = status
        if metadata:
            self.metadata.update(metadata)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace event to dictionary."""
        return {
            'id': self.id,
            'extension_id': self.extension_id,
            'trace_id': self.trace_id,
            'parent_id': self.parent_id,
            'event_type': self.event_type.value,
            'name': self.name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_ms': self.duration_ms,
            'status': self.status,
            'metadata': self.metadata,
            'tags': self.tags
        }


@dataclass
class PerformanceProfile:
    """Represents performance profiling data for a function or operation."""
    extension_id: str
    function_name: str
    call_count: int
    total_time_ms: float
    average_time_ms: float
    min_time_ms: float
    max_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert performance profile to dictionary."""
        return {
            'extension_id': self.extension_id,
            'function_name': self.function_name,
            'call_count': self.call_count,
            'total_time_ms': self.total_time_ms,
            'average_time_ms': self.average_time_ms,
            'min_time_ms': self.min_time_ms,
            'max_time_ms': self.max_time_ms,
            'memory_usage_mb': self.memory_usage_mb,
            'cpu_usage_percent': self.cpu_usage_percent,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class Alert:
    """Represents an alert generated by the monitoring system."""
    id: str
    extension_id: str
    extension_name: str
    alert_type: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    metric_name: Optional[str] = None
    current_value: Optional[Union[int, float]] = None
    threshold_value: Optional[Union[int, float]] = None
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def resolve(self, notes: Optional[str] = None):
        """Mark the alert as resolved."""
        self.resolved = True
        self.resolution_time = datetime.utcnow()
        self.resolution_notes = notes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            'id': self.id,
            'extension_id': self.extension_id,
            'extension_name': self.extension_name,
            'alert_type': self.alert_type,
            'severity': self.severity.value,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'metric_name': self.metric_name,
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'resolved': self.resolved,
            'resolution_time': self.resolution_time.isoformat() if self.resolution_time else None,
            'resolution_notes': self.resolution_notes,
            'metadata': self.metadata
        }


@dataclass
class DebugSession:
    """Represents a debugging session for an extension."""
    id: str
    extension_id: str
    extension_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "active"  # active, completed, aborted
    configuration: Dict[str, Any] = field(default_factory=dict)
    collected_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert debug session to dictionary."""
        return {
            'id': self.id,
            'extension_id': self.extension_id,
            'extension_name': self.extension_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'configuration': self.configuration,
            'collected_data': self.collected_data
        }


@dataclass
class DiagnosticResult:
    """Represents the result of a diagnostic check."""
    check_name: str
    status: str  # healthy, warning, error
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert diagnostic result to dictionary."""
        return {
            'check_name': self.check_name,
            'status': self.status,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ExtensionHealthStatus:
    """Represents the overall health status of an extension."""
    extension_id: str
    extension_name: str
    overall_status: str  # healthy, degraded, unhealthy
    last_check: datetime
    diagnostics: List[DiagnosticResult] = field(default_factory=list)
    metrics_summary: Dict[str, Any] = field(default_factory=dict)
    recent_errors: List[ErrorRecord] = field(default_factory=list)
    active_alerts: List[Alert] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert health status to dictionary."""
        return {
            'extension_id': self.extension_id,
            'extension_name': self.extension_name,
            'overall_status': self.overall_status,
            'last_check': self.last_check.isoformat(),
            'diagnostics': [d.to_dict() for d in self.diagnostics],
            'metrics_summary': self.metrics_summary,
            'recent_errors': [e.to_dict() for e in self.recent_errors],
            'active_alerts': [a.to_dict() for a in self.active_alerts]
        }