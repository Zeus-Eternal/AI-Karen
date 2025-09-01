"""
Model Orchestrator OpenTelemetry Tracing Integration.

This module provides distributed tracing for model orchestrator operations,
integrating with existing OpenTelemetry setup and correlation ID system.
"""

import logging
from contextlib import contextmanager
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import uuid

logger = logging.getLogger(__name__)

# Try to import OpenTelemetry components
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    from opentelemetry.baggage.propagation import W3CBaggagePropagator
    from opentelemetry.propagators.composite import CompositePropagator
    TRACING_AVAILABLE = True
except ImportError:
    logger.warning("OpenTelemetry not available, using dummy tracing")
    TRACING_AVAILABLE = False


@dataclass
class TraceContext:
    """Context for distributed tracing."""
    trace_id: str
    span_id: str
    correlation_id: str
    operation: str
    model_id: Optional[str] = None
    user_id: Optional[str] = None
    library: Optional[str] = None


class ModelOrchestratorTracer:
    """
    Distributed tracing for model orchestrator operations.
    
    Integrates with existing OpenTelemetry setup and provides
    correlation IDs for operation tracking across services.
    """
    
    def __init__(self, service_name: str = "model-orchestrator"):
        self.service_name = service_name
        self.tracer = None
        self.propagator = None
        
        if TRACING_AVAILABLE:
            self.tracer = trace.get_tracer(__name__)
            self.propagator = CompositePropagator([
                TraceContextTextMapPropagator(),
                W3CBaggagePropagator()
            ])
            logger.debug(f"OpenTelemetry tracer initialized for {service_name}")
        else:
            self._setup_dummy_tracer()
    
    def _setup_dummy_tracer(self):
        """Setup dummy tracer when OpenTelemetry is not available."""
        class DummySpan:
            def __init__(self, name: str):
                self.name = name
                self.trace_id = str(uuid.uuid4())
                self.span_id = str(uuid.uuid4())[:8]
            
            def set_attribute(self, key: str, value: Any):
                pass
            
            def set_status(self, status: Any, description: str = None):
                pass
            
            def record_exception(self, exception: Exception):
                pass
            
            def add_event(self, name: str, attributes: Dict[str, Any] = None):
                pass
            
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        
        class DummyTracer:
            def start_as_current_span(self, name: str, **kwargs):
                return DummySpan(name)
        
        self.tracer = DummyTracer()
        logger.debug("Dummy tracer initialized")
    
    def generate_correlation_id(self) -> str:
        """Generate a correlation ID for operation tracking."""
        return f"model-op-{uuid.uuid4().hex[:12]}"
    
    def extract_trace_context(self, headers: Dict[str, str]) -> Optional[TraceContext]:
        """Extract trace context from HTTP headers."""
        if not TRACING_AVAILABLE or not self.propagator:
            return None
        
        try:
            # Extract context from headers
            context = self.propagator.extract(headers)
            span_context = trace.get_current_span(context).get_span_context()
            
            if span_context.is_valid:
                return TraceContext(
                    trace_id=format(span_context.trace_id, '032x'),
                    span_id=format(span_context.span_id, '016x'),
                    correlation_id=self.generate_correlation_id(),
                    operation="extracted"
                )
        except Exception as e:
            logger.warning(f"Failed to extract trace context: {e}")
        
        return None
    
    def inject_trace_context(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Inject trace context into HTTP headers."""
        if not TRACING_AVAILABLE or not self.propagator:
            return headers
        
        try:
            self.propagator.inject(headers)
        except Exception as e:
            logger.warning(f"Failed to inject trace context: {e}")
        
        return headers
    
    @contextmanager
    def start_operation_span(
        self,
        operation_name: str,
        model_id: Optional[str] = None,
        user_id: Optional[str] = None,
        library: Optional[str] = None,
        correlation_id: Optional[str] = None,
        parent_context: Optional[TraceContext] = None
    ):
        """Start a span for a model operation."""
        correlation_id = correlation_id or self.generate_correlation_id()
        
        span_name = f"model_orchestrator.{operation_name}"
        
        with self.tracer.start_as_current_span(span_name) as span:
            try:
                # Set standard attributes
                span.set_attribute("service.name", self.service_name)
                span.set_attribute("operation.name", operation_name)
                span.set_attribute("correlation.id", correlation_id)
                
                # Set model-specific attributes
                if model_id:
                    span.set_attribute("model.id", model_id)
                if user_id:
                    span.set_attribute("user.id", user_id)
                if library:
                    span.set_attribute("model.library", library)
                
                # Set parent context if available
                if parent_context:
                    span.set_attribute("parent.trace_id", parent_context.trace_id)
                    span.set_attribute("parent.span_id", parent_context.span_id)
                
                # Create trace context
                if TRACING_AVAILABLE:
                    span_context = span.get_span_context()
                    trace_context = TraceContext(
                        trace_id=format(span_context.trace_id, '032x'),
                        span_id=format(span_context.span_id, '016x'),
                        correlation_id=correlation_id,
                        operation=operation_name,
                        model_id=model_id,
                        user_id=user_id,
                        library=library
                    )
                else:
                    trace_context = TraceContext(
                        trace_id=str(uuid.uuid4()),
                        span_id=str(uuid.uuid4())[:8],
                        correlation_id=correlation_id,
                        operation=operation_name,
                        model_id=model_id,
                        user_id=user_id,
                        library=library
                    )
                
                logger.debug(
                    f"Started span: {span_name} "
                    f"(correlation_id: {correlation_id})"
                )
                
                yield trace_context
                
                # Mark span as successful
                if TRACING_AVAILABLE:
                    span.set_status(Status(StatusCode.OK))
                
            except Exception as e:
                # Record exception and mark span as error
                if TRACING_AVAILABLE:
                    span.record_exception(e)
                    span.set_status(
                        Status(StatusCode.ERROR, f"Operation failed: {str(e)}")
                    )
                
                logger.error(
                    f"Error in span {span_name} "
                    f"(correlation_id: {correlation_id}): {e}"
                )
                raise
    
    def add_span_event(
        self,
        event_name: str,
        attributes: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ):
        """Add an event to the current span."""
        try:
            if TRACING_AVAILABLE:
                current_span = trace.get_current_span()
                if current_span.is_recording():
                    event_attributes = attributes or {}
                    if correlation_id:
                        event_attributes["correlation.id"] = correlation_id
                    
                    current_span.add_event(event_name, event_attributes)
                    
                    logger.debug(
                        f"Added span event: {event_name} "
                        f"(correlation_id: {correlation_id})"
                    )
        except Exception as e:
            logger.warning(f"Failed to add span event: {e}")
    
    def set_span_attributes(
        self,
        attributes: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """Set attributes on the current span."""
        try:
            if TRACING_AVAILABLE:
                current_span = trace.get_current_span()
                if current_span.is_recording():
                    for key, value in attributes.items():
                        current_span.set_attribute(key, value)
                    
                    if correlation_id:
                        current_span.set_attribute("correlation.id", correlation_id)
                    
                    logger.debug(
                        f"Set span attributes: {list(attributes.keys())} "
                        f"(correlation_id: {correlation_id})"
                    )
        except Exception as e:
            logger.warning(f"Failed to set span attributes: {e}")
    
    def trace_download_operation(
        self,
        model_id: str,
        user_id: Optional[str] = None,
        library: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """Create a span context for model download operations."""
        return self.start_operation_span(
            "download",
            model_id=model_id,
            user_id=user_id,
            library=library,
            correlation_id=correlation_id
        )
    
    def trace_migration_operation(
        self,
        migration_type: str,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """Create a span context for migration operations."""
        return self.start_operation_span(
            f"migrate.{migration_type}",
            user_id=user_id,
            correlation_id=correlation_id
        )
    
    def trace_registry_operation(
        self,
        operation: str,
        model_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """Create a span context for registry operations."""
        return self.start_operation_span(
            f"registry.{operation}",
            model_id=model_id,
            correlation_id=correlation_id
        )
    
    def trace_api_request(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """Create a span context for API requests."""
        return self.start_operation_span(
            f"api.{method.lower()}.{endpoint.replace('/', '_')}",
            user_id=user_id,
            correlation_id=correlation_id
        )
    
    def trace_websocket_operation(
        self,
        operation: str,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """Create a span context for WebSocket operations."""
        return self.start_operation_span(
            f"websocket.{operation}",
            user_id=user_id,
            correlation_id=correlation_id
        )
    
    def get_current_correlation_id(self) -> Optional[str]:
        """Get the correlation ID from the current span."""
        try:
            if TRACING_AVAILABLE:
                current_span = trace.get_current_span()
                if current_span.is_recording():
                    # Try to get correlation ID from span attributes
                    # This is a simplified approach - in practice you might
                    # need to store this in span context or baggage
                    return getattr(current_span, '_correlation_id', None)
        except Exception as e:
            logger.warning(f"Failed to get correlation ID: {e}")
        
        return None
    
    def create_child_span_context(
        self,
        parent_context: TraceContext,
        operation_name: str,
        model_id: Optional[str] = None
    ):
        """Create a child span context from a parent context."""
        return self.start_operation_span(
            operation_name,
            model_id=model_id,
            user_id=parent_context.user_id,
            library=parent_context.library,
            correlation_id=parent_context.correlation_id,
            parent_context=parent_context
        )


# Global tracer instance
_model_orchestrator_tracer: Optional[ModelOrchestratorTracer] = None


def get_model_orchestrator_tracer() -> ModelOrchestratorTracer:
    """Get the global model orchestrator tracer instance."""
    global _model_orchestrator_tracer
    if _model_orchestrator_tracer is None:
        _model_orchestrator_tracer = ModelOrchestratorTracer()
    return _model_orchestrator_tracer


def create_correlation_id() -> str:
    """Create a new correlation ID for operation tracking."""
    return get_model_orchestrator_tracer().generate_correlation_id()


def get_current_correlation_id() -> Optional[str]:
    """Get the current correlation ID from the active span."""
    return get_model_orchestrator_tracer().get_current_correlation_id()