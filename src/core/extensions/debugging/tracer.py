"""
Extension Tracer

Provides distributed tracing capabilities for extensions including
request tracing, operation tracking, and performance analysis.
"""

import uuid
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, ContextManager
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field

from .models import TraceEvent, TraceEventType


@dataclass
class TraceContext:
    """Context information for a trace."""
    trace_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)
    sampling_rate: float = 1.0


@dataclass
class Span:
    """Represents a span in a distributed trace."""
    span_id: str
    trace_id: str
    parent_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "started"  # started, finished, error
    
    def finish(self, status: str = "finished"):
        """Finish the span."""
        self.end_time = datetime.utcnow()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = status
    
    def log(self, message: str, **fields):
        """Add a log entry to the span."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'message': message,
            **fields
        }
        self.logs.append(log_entry)
    
    def set_tag(self, key: str, value: str):
        """Set a tag on the span."""
        self.tags[key] = value
    
    def set_error(self, error: Exception):
        """Mark the span as having an error."""
        self.status = "error"
        self.set_tag("error", "true")
        self.set_tag("error.type", type(error).__name__)
        self.set_tag("error.message", str(error))
        self.log("error", error_type=type(error).__name__, error_message=str(error))


@dataclass
class Trace:
    """Represents a complete trace with all its spans."""
    trace_id: str
    root_span_id: str
    spans: Dict[str, Span] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    
    def add_span(self, span: Span):
        """Add a span to the trace."""
        self.spans[span.span_id] = span
    
    def finish(self):
        """Finish the trace."""
        self.end_time = datetime.utcnow()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
    
    def get_span_tree(self) -> Dict[str, Any]:
        """Get the span tree structure."""
        root_span = self.spans.get(self.root_span_id)
        if not root_span:
            return {}
        
        return self._build_span_tree(root_span)
    
    def _build_span_tree(self, span: Span) -> Dict[str, Any]:
        """Build span tree recursively."""
        children = [
            self._build_span_tree(child_span)
            for child_span in self.spans.values()
            if child_span.parent_id == span.span_id
        ]
        
        return {
            'span_id': span.span_id,
            'operation_name': span.operation_name,
            'start_time': span.start_time.isoformat(),
            'duration_ms': span.duration_ms,
            'status': span.status,
            'tags': span.tags,
            'logs': span.logs,
            'children': children
        }


class TraceContextManager:
    """Manages trace context across threads."""
    
    def __init__(self):
        self._local = threading.local()
    
    def set_context(self, context: TraceContext):
        """Set the current trace context."""
        self._local.context = context
    
    def get_context(self) -> Optional[TraceContext]:
        """Get the current trace context."""
        return getattr(self._local, 'context', None)
    
    def clear_context(self):
        """Clear the current trace context."""
        if hasattr(self._local, 'context'):
            delattr(self._local, 'context')


class ExtensionTracer:
    """
    Distributed tracing system for extensions.
    
    Features:
    - Distributed trace creation and management
    - Span creation and lifecycle management
    - Context propagation across operations
    - Performance analysis and bottleneck detection
    - Integration with logging and metrics
    """
    
    def __init__(
        self,
        extension_id: str,
        extension_name: str,
        sampling_rate: float = 1.0,
        max_traces: int = 1000,
        debug_manager=None
    ):
        self.extension_id = extension_id
        self.extension_name = extension_name
        self.sampling_rate = sampling_rate
        self.max_traces = max_traces
        self.debug_manager = debug_manager
        
        # Trace storage
        self.active_traces: Dict[str, Trace] = {}
        self.completed_traces: deque = deque(maxlen=max_traces)
        self.active_spans: Dict[str, Span] = {}
        
        # Context management
        self.context_manager = TraceContextManager()
        
        # Statistics
        self.trace_stats = {
            'total_traces': 0,
            'total_spans': 0,
            'avg_trace_duration': 0.0,
            'error_count': 0
        }
        
        # Thread safety
        self.lock = threading.Lock()
    
    def start_trace(
        self,
        operation_name: str,
        trace_id: Optional[str] = None,
        parent_context: Optional[TraceContext] = None
    ) -> TraceContext:
        """Start a new trace."""
        if trace_id is None:
            trace_id = str(uuid.uuid4())
        
        # Check sampling
        if not self._should_sample():
            return TraceContext(trace_id=trace_id, sampling_rate=0.0)
        
        with self.lock:
            # Create root span
            root_span = Span(
                span_id=str(uuid.uuid4()),
                trace_id=trace_id,
                parent_id=None,
                operation_name=operation_name,
                start_time=datetime.utcnow()
            )
            
            root_span.set_tag("extension.id", self.extension_id)
            root_span.set_tag("extension.name", self.extension_name)
            root_span.set_tag("span.kind", "server")
            
            # Create trace
            trace = Trace(
                trace_id=trace_id,
                root_span_id=root_span.span_id
            )
            trace.add_span(root_span)
            
            # Store trace and span
            self.active_traces[trace_id] = trace
            self.active_spans[root_span.span_id] = root_span
            
            # Create context
            context = TraceContext(
                trace_id=trace_id,
                parent_span_id=root_span.span_id,
                sampling_rate=self.sampling_rate
            )
            
            # Set context
            self.context_manager.set_context(context)
            
            # Update stats
            self.trace_stats['total_traces'] += 1
            
            return context
    
    def finish_trace(self, trace_id: str):
        """Finish a trace."""
        with self.lock:
            trace = self.active_traces.get(trace_id)
            if not trace:
                return
            
            # Finish all active spans in this trace
            for span in trace.spans.values():
                if span.status == "started":
                    span.finish()
            
            # Finish trace
            trace.finish()
            
            # Move to completed traces
            self.completed_traces.append(trace)
            del self.active_traces[trace_id]
            
            # Remove spans from active spans
            for span_id in list(trace.spans.keys()):
                if span_id in self.active_spans:
                    del self.active_spans[span_id]
            
            # Update stats
            if trace.duration_ms:
                total_duration = self.trace_stats['avg_trace_duration'] * (self.trace_stats['total_traces'] - 1)
                self.trace_stats['avg_trace_duration'] = (total_duration + trace.duration_ms) / self.trace_stats['total_traces']
    
    @contextmanager
    def start_span(
        self,
        operation_name: str,
        span_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> ContextManager[Span]:
        """Start a new span within the current trace."""
        context = self.context_manager.get_context()
        if not context or context.sampling_rate == 0.0:
            # Create a no-op span if not sampling
            yield self._create_noop_span()
            return
        
        if span_id is None:
            span_id = str(uuid.uuid4())
        
        if parent_id is None:
            parent_id = context.parent_span_id
        
        span = Span(
            span_id=span_id,
            trace_id=context.trace_id,
            parent_id=parent_id,
            operation_name=operation_name,
            start_time=datetime.utcnow()
        )
        
        # Set default tags
        span.set_tag("extension.id", self.extension_id)
        span.set_tag("extension.name", self.extension_name)
        
        # Set custom tags
        if tags:
            for key, value in tags.items():
                span.set_tag(key, value)
        
        with self.lock:
            # Add to active spans
            self.active_spans[span_id] = span
            
            # Add to trace
            trace = self.active_traces.get(context.trace_id)
            if trace:
                trace.add_span(span)
            
            # Update stats
            self.trace_stats['total_spans'] += 1
        
        # Update context
        old_parent = context.parent_span_id
        context.parent_span_id = span_id
        
        try:
            yield span
        except Exception as e:
            span.set_error(e)
            self.trace_stats['error_count'] += 1
            raise
        finally:
            # Finish span
            span.finish()
            
            # Restore context
            context.parent_span_id = old_parent
            
            # Remove from active spans
            with self.lock:
                if span_id in self.active_spans:
                    del self.active_spans[span_id]
    
    def trace_function(self, operation_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None):
        """Decorator to trace a function."""
        def decorator(func):
            nonlocal operation_name
            if operation_name is None:
                operation_name = f"{func.__module__}.{func.__name__}"
            
            def wrapper(*args, **kwargs):
                with self.start_span(operation_name, tags=tags) as span:
                    span.set_tag("function.name", func.__name__)
                    span.set_tag("function.module", func.__module__)
                    
                    try:
                        result = func(*args, **kwargs)
                        span.set_tag("function.result", "success")
                        return result
                    except Exception as e:
                        span.set_tag("function.result", "error")
                        raise
            
            return wrapper
        return decorator
    
    def trace_async_function(self, operation_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None):
        """Decorator to trace an async function."""
        def decorator(func):
            nonlocal operation_name
            if operation_name is None:
                operation_name = f"{func.__module__}.{func.__name__}"
            
            async def wrapper(*args, **kwargs):
                with self.start_span(operation_name, tags=tags) as span:
                    span.set_tag("function.name", func.__name__)
                    span.set_tag("function.module", func.__module__)
                    span.set_tag("function.type", "async")
                    
                    try:
                        result = await func(*args, **kwargs)
                        span.set_tag("function.result", "success")
                        return result
                    except Exception as e:
                        span.set_tag("function.result", "error")
                        raise
            
            return wrapper
        return decorator
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID."""
        with self.lock:
            # Check active traces
            if trace_id in self.active_traces:
                return self.active_traces[trace_id]
            
            # Check completed traces
            for trace in self.completed_traces:
                if trace.trace_id == trace_id:
                    return trace
            
            return None
    
    def get_active_traces(self) -> List[Trace]:
        """Get all active traces."""
        with self.lock:
            return list(self.active_traces.values())
    
    def get_completed_traces(self, limit: Optional[int] = None) -> List[Trace]:
        """Get completed traces."""
        traces = list(self.completed_traces)
        if limit:
            traces = traces[-limit:]
        return traces
    
    def get_trace_statistics(self) -> Dict[str, Any]:
        """Get tracing statistics."""
        with self.lock:
            active_count = len(self.active_traces)
            completed_count = len(self.completed_traces)
            
            # Calculate error rate
            error_rate = 0.0
            if self.trace_stats['total_traces'] > 0:
                error_rate = (self.trace_stats['error_count'] / self.trace_stats['total_traces']) * 100
            
            return {
                'total_traces': self.trace_stats['total_traces'],
                'active_traces': active_count,
                'completed_traces': completed_count,
                'total_spans': self.trace_stats['total_spans'],
                'avg_trace_duration_ms': self.trace_stats['avg_trace_duration'],
                'error_count': self.trace_stats['error_count'],
                'error_rate_percent': error_rate,
                'sampling_rate': self.sampling_rate
            }
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance based on trace data."""
        with self.lock:
            if not self.completed_traces:
                return {'error': 'No completed traces available'}
            
            # Collect span data
            all_spans = []
            for trace in self.completed_traces:
                all_spans.extend(trace.spans.values())
            
            # Group by operation
            operation_stats = defaultdict(list)
            for span in all_spans:
                if span.duration_ms is not None:
                    operation_stats[span.operation_name].append(span.duration_ms)
            
            # Calculate statistics for each operation
            performance_data = {}
            for operation, durations in operation_stats.items():
                if durations:
                    performance_data[operation] = {
                        'count': len(durations),
                        'avg_duration_ms': sum(durations) / len(durations),
                        'min_duration_ms': min(durations),
                        'max_duration_ms': max(durations),
                        'p95_duration_ms': self._percentile(durations, 95),
                        'p99_duration_ms': self._percentile(durations, 99)
                    }
            
            # Find bottlenecks
            bottlenecks = []
            for operation, stats in performance_data.items():
                if stats['avg_duration_ms'] > 1000:  # More than 1 second
                    bottlenecks.append({
                        'operation': operation,
                        'avg_duration_ms': stats['avg_duration_ms'],
                        'count': stats['count']
                    })
            
            bottlenecks.sort(key=lambda x: x['avg_duration_ms'], reverse=True)
            
            return {
                'operations': performance_data,
                'bottlenecks': bottlenecks[:10],  # Top 10 bottlenecks
                'total_operations': len(performance_data),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
    
    def export_traces(self, format: str = "json", limit: Optional[int] = None) -> str:
        """Export traces in specified format."""
        traces = self.get_completed_traces(limit)
        
        if format.lower() == "json":
            import json
            trace_data = []
            for trace in traces:
                trace_data.append({
                    'trace_id': trace.trace_id,
                    'start_time': trace.start_time.isoformat(),
                    'duration_ms': trace.duration_ms,
                    'span_tree': trace.get_span_tree()
                })
            return json.dumps(trace_data, indent=2)
        elif format.lower() == "jaeger":
            return self._export_jaeger_format(traces)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def clear_traces(self):
        """Clear all trace data."""
        with self.lock:
            self.active_traces.clear()
            self.completed_traces.clear()
            self.active_spans.clear()
            self.trace_stats = {
                'total_traces': 0,
                'total_spans': 0,
                'avg_trace_duration': 0.0,
                'error_count': 0
            }
    
    def _should_sample(self) -> bool:
        """Determine if this trace should be sampled."""
        import random
        return random.random() < self.sampling_rate
    
    def _create_noop_span(self) -> Span:
        """Create a no-op span for when not sampling."""
        return Span(
            span_id="noop",
            trace_id="noop",
            parent_id=None,
            operation_name="noop",
            start_time=datetime.utcnow()
        )
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _export_jaeger_format(self, traces: List[Trace]) -> str:
        """Export traces in Jaeger JSON format."""
        import json
        
        jaeger_data = {
            'data': []
        }
        
        for trace in traces:
            spans = []
            for span in trace.spans.values():
                jaeger_span = {
                    'traceID': trace.trace_id,
                    'spanID': span.span_id,
                    'parentSpanID': span.parent_id,
                    'operationName': span.operation_name,
                    'startTime': int(span.start_time.timestamp() * 1000000),  # microseconds
                    'duration': int((span.duration_ms or 0) * 1000),  # microseconds
                    'tags': [{'key': k, 'value': v} for k, v in span.tags.items()],
                    'logs': [
                        {
                            'timestamp': int(datetime.fromisoformat(log['timestamp']).timestamp() * 1000000),
                            'fields': [{'key': k, 'value': v} for k, v in log.items() if k != 'timestamp']
                        }
                        for log in span.logs
                    ],
                    'process': {
                        'serviceName': self.extension_name,
                        'tags': [
                            {'key': 'extension.id', 'value': self.extension_id}
                        ]
                    }
                }
                spans.append(jaeger_span)
            
            jaeger_data['data'].append({
                'traceID': trace.trace_id,
                'spans': spans
            })
        
        return json.dumps(jaeger_data, indent=2)