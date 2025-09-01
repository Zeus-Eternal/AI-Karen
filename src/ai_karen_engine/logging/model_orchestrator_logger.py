"""
Model Orchestrator Structured Logging Integration.

This module provides structured logging for model orchestrator operations,
integrating with existing logging framework and correlation ID system.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from ai_karen_engine.monitoring.model_orchestrator_tracing import (
    get_model_orchestrator_tracer,
    TraceContext
)

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels for model operations."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ModelOperationEvent(Enum):
    """Types of model operation events."""
    OPERATION_STARTED = "operation_started"
    OPERATION_COMPLETED = "operation_completed"
    OPERATION_FAILED = "operation_failed"
    DOWNLOAD_STARTED = "download_started"
    DOWNLOAD_PROGRESS = "download_progress"
    DOWNLOAD_COMPLETED = "download_completed"
    MIGRATION_STARTED = "migration_started"
    MIGRATION_COMPLETED = "migration_completed"
    REGISTRY_UPDATED = "registry_updated"
    REGISTRY_VALIDATED = "registry_validated"
    LICENSE_ACCEPTED = "license_accepted"
    SECURITY_VALIDATION = "security_validation"
    GC_OPERATION = "gc_operation"
    COMPATIBILITY_CHECK = "compatibility_check"
    API_REQUEST = "api_request"
    WEBSOCKET_EVENT = "websocket_event"


@dataclass
class ModelLogEntry:
    """Structured log entry for model operations."""
    timestamp: str
    level: str
    event_type: str
    correlation_id: Optional[str]
    trace_id: Optional[str]
    span_id: Optional[str]
    operation: Optional[str]
    model_id: Optional[str]
    user_id: Optional[str]
    library: Optional[str]
    message: str
    details: Dict[str, Any]
    duration_ms: Optional[float] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None


class ModelOrchestratorLogger:
    """
    Structured logger for model orchestrator operations.
    
    Integrates with existing logging framework and provides
    correlation ID tracking and structured output.
    """
    
    def __init__(self, log_name: str = "model_orchestrator"):
        self.log_name = log_name
        self.logger = logging.getLogger(f"ai_karen_engine.{log_name}")
        self.tracer = get_model_orchestrator_tracer()
        
        # Configure structured logging format
        self._setup_structured_logging()
        
        logger.debug(f"Model orchestrator logger initialized: {log_name}")
    
    def _setup_structured_logging(self):
        """Setup structured logging format if not already configured."""
        # Check if handler already has structured formatter
        for handler in self.logger.handlers:
            if hasattr(handler.formatter, '_structured'):
                return
        
        # Add structured formatter to existing handlers
        for handler in self.logger.handlers:
            if handler.formatter:
                # Wrap existing formatter to add structured data
                original_format = handler.formatter.format
                
                def structured_format(record):
                    # Add structured data to record if available
                    if hasattr(record, 'structured_data'):
                        structured_msg = json.dumps(record.structured_data, default=str)
                        record.msg = f"{record.msg} | {structured_msg}"
                    return original_format(record)
                
                handler.formatter.format = structured_format
                handler.formatter._structured = True
    
    def _create_log_entry(
        self,
        level: LogLevel,
        event_type: ModelOperationEvent,
        message: str,
        operation: Optional[str] = None,
        model_id: Optional[str] = None,
        user_id: Optional[str] = None,
        library: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        error: Optional[Exception] = None,
        trace_context: Optional[TraceContext] = None
    ) -> ModelLogEntry:
        """Create a structured log entry."""
        # Get trace context if not provided
        if trace_context is None:
            correlation_id = self.tracer.get_current_correlation_id()
            trace_id = None
            span_id = None
        else:
            correlation_id = trace_context.correlation_id
            trace_id = trace_context.trace_id
            span_id = trace_context.span_id
        
        # Handle error information
        error_type = None
        error_message = None
        if error:
            error_type = type(error).__name__
            error_message = str(error)
        
        return ModelLogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            level=level.value,
            event_type=event_type.value,
            correlation_id=correlation_id,
            trace_id=trace_id,
            span_id=span_id,
            operation=operation,
            model_id=model_id,
            user_id=user_id,
            library=library,
            message=message,
            details=details or {},
            duration_ms=duration_ms,
            error_type=error_type,
            error_message=error_message
        )
    
    def _log_entry(self, entry: ModelLogEntry):
        """Log a structured entry."""
        try:
            # Convert to dict for JSON serialization
            entry_dict = asdict(entry)
            
            # Create log record with structured data
            log_level = getattr(logging, entry.level)
            record = self.logger.makeRecord(
                name=self.logger.name,
                level=log_level,
                fn="",
                lno=0,
                msg=entry.message,
                args=(),
                exc_info=None
            )
            
            # Add structured data to record
            record.structured_data = entry_dict
            
            # Log the record
            self.logger.handle(record)
            
        except Exception as e:
            # Fallback to simple logging if structured logging fails
            self.logger.error(f"Failed to log structured entry: {e}")
            self.logger.log(
                getattr(logging, entry.level),
                f"{entry.message} (correlation_id: {entry.correlation_id})"
            )
    
    def log_operation_started(
        self,
        operation: str,
        model_id: Optional[str] = None,
        user_id: Optional[str] = None,
        library: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        trace_context: Optional[TraceContext] = None
    ):
        """Log the start of a model operation."""
        entry = self._create_log_entry(
            level=LogLevel.INFO,
            event_type=ModelOperationEvent.OPERATION_STARTED,
            message=f"Started {operation} operation",
            operation=operation,
            model_id=model_id,
            user_id=user_id,
            library=library,
            details=details,
            trace_context=trace_context
        )
        self._log_entry(entry)
    
    def log_operation_completed(
        self,
        operation: str,
        model_id: Optional[str] = None,
        user_id: Optional[str] = None,
        library: Optional[str] = None,
        duration_ms: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
        trace_context: Optional[TraceContext] = None
    ):
        """Log the completion of a model operation."""
        entry = self._create_log_entry(
            level=LogLevel.INFO,
            event_type=ModelOperationEvent.OPERATION_COMPLETED,
            message=f"Completed {operation} operation",
            operation=operation,
            model_id=model_id,
            user_id=user_id,
            library=library,
            duration_ms=duration_ms,
            details=details,
            trace_context=trace_context
        )
        self._log_entry(entry)
    
    def log_operation_failed(
        self,
        operation: str,
        error: Exception,
        model_id: Optional[str] = None,
        user_id: Optional[str] = None,
        library: Optional[str] = None,
        duration_ms: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
        trace_context: Optional[TraceContext] = None
    ):
        """Log a failed model operation."""
        entry = self._create_log_entry(
            level=LogLevel.ERROR,
            event_type=ModelOperationEvent.OPERATION_FAILED,
            message=f"Failed {operation} operation: {str(error)}",
            operation=operation,
            model_id=model_id,
            user_id=user_id,
            library=library,
            duration_ms=duration_ms,
            details=details,
            error=error,
            trace_context=trace_context
        )
        self._log_entry(entry)
    
    def log_download_progress(
        self,
        model_id: str,
        bytes_downloaded: int,
        total_bytes: int,
        speed_bps: float,
        user_id: Optional[str] = None,
        library: Optional[str] = None,
        trace_context: Optional[TraceContext] = None
    ):
        """Log download progress."""
        progress_percent = (bytes_downloaded / total_bytes) * 100 if total_bytes > 0 else 0
        
        entry = self._create_log_entry(
            level=LogLevel.DEBUG,
            event_type=ModelOperationEvent.DOWNLOAD_PROGRESS,
            message=f"Download progress: {progress_percent:.1f}%",
            operation="download",
            model_id=model_id,
            user_id=user_id,
            library=library,
            details={
                "bytes_downloaded": bytes_downloaded,
                "total_bytes": total_bytes,
                "progress_percent": progress_percent,
                "speed_bps": speed_bps
            },
            trace_context=trace_context
        )
        self._log_entry(entry)
    
    def log_registry_operation(
        self,
        operation: str,
        model_id: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
        trace_context: Optional[TraceContext] = None
    ):
        """Log registry operations."""
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"Registry {operation}"
        if not success and error:
            message += f" failed: {str(error)}"
        
        entry = self._create_log_entry(
            level=level,
            event_type=ModelOperationEvent.REGISTRY_UPDATED,
            message=message,
            operation=f"registry_{operation}",
            model_id=model_id,
            details=details,
            error=error,
            trace_context=trace_context
        )
        self._log_entry(entry)
    
    def log_security_event(
        self,
        event_type: str,
        model_id: Optional[str] = None,
        user_id: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
        trace_context: Optional[TraceContext] = None
    ):
        """Log security-related events."""
        level = LogLevel.INFO if success else LogLevel.WARNING
        message = f"Security {event_type}"
        if not success:
            message += " failed"
            if error:
                message += f": {str(error)}"
        
        entry = self._create_log_entry(
            level=level,
            event_type=ModelOperationEvent.SECURITY_VALIDATION,
            message=message,
            operation=f"security_{event_type}",
            model_id=model_id,
            user_id=user_id,
            details=details,
            error=error,
            trace_context=trace_context
        )
        self._log_entry(entry)
    
    def log_license_acceptance(
        self,
        model_id: str,
        license_type: str,
        user_id: str,
        details: Optional[Dict[str, Any]] = None,
        trace_context: Optional[TraceContext] = None
    ):
        """Log license acceptance events."""
        entry = self._create_log_entry(
            level=LogLevel.INFO,
            event_type=ModelOperationEvent.LICENSE_ACCEPTED,
            message=f"License accepted for model {model_id}",
            operation="license_acceptance",
            model_id=model_id,
            user_id=user_id,
            details={
                "license_type": license_type,
                **(details or {})
            },
            trace_context=trace_context
        )
        self._log_entry(entry)
    
    def log_gc_operation(
        self,
        trigger: str,
        models_removed: List[str],
        bytes_freed: int,
        success: bool = True,
        error: Optional[Exception] = None,
        trace_context: Optional[TraceContext] = None
    ):
        """Log garbage collection operations."""
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"Garbage collection ({trigger})"
        if success:
            message += f": removed {len(models_removed)} models, freed {bytes_freed} bytes"
        else:
            message += " failed"
            if error:
                message += f": {str(error)}"
        
        entry = self._create_log_entry(
            level=level,
            event_type=ModelOperationEvent.GC_OPERATION,
            message=message,
            operation="garbage_collection",
            details={
                "trigger": trigger,
                "models_removed": models_removed,
                "bytes_freed": bytes_freed
            },
            error=error,
            trace_context=trace_context
        )
        self._log_entry(entry)
    
    def log_api_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        trace_context: Optional[TraceContext] = None
    ):
        """Log API requests."""
        level = LogLevel.INFO if 200 <= status_code < 400 else LogLevel.WARNING
        message = f"API {method} {endpoint} -> {status_code}"
        
        entry = self._create_log_entry(
            level=level,
            event_type=ModelOperationEvent.API_REQUEST,
            message=message,
            operation="api_request",
            user_id=user_id,
            duration_ms=duration_ms,
            details={
                "method": method,
                "endpoint": endpoint,
                "status_code": status_code,
                **(details or {})
            },
            trace_context=trace_context
        )
        self._log_entry(entry)
    
    def log_websocket_event(
        self,
        event_type: str,
        operation: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        trace_context: Optional[TraceContext] = None
    ):
        """Log WebSocket events."""
        entry = self._create_log_entry(
            level=LogLevel.DEBUG,
            event_type=ModelOperationEvent.WEBSOCKET_EVENT,
            message=f"WebSocket {event_type} for {operation}",
            operation=f"websocket_{operation}",
            user_id=user_id,
            details={
                "event_type": event_type,
                **(details or {})
            },
            trace_context=trace_context
        )
        self._log_entry(entry)
    
    def log_migration_operation(
        self,
        migration_type: str,
        models_processed: int,
        success: bool = True,
        duration_ms: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
        trace_context: Optional[TraceContext] = None
    ):
        """Log migration operations."""
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"Migration ({migration_type})"
        if success:
            message += f": processed {models_processed} models"
        else:
            message += " failed"
            if error:
                message += f": {str(error)}"
        
        entry = self._create_log_entry(
            level=level,
            event_type=ModelOperationEvent.MIGRATION_COMPLETED,
            message=message,
            operation=f"migration_{migration_type}",
            duration_ms=duration_ms,
            details={
                "migration_type": migration_type,
                "models_processed": models_processed,
                **(details or {})
            },
            error=error,
            trace_context=trace_context
        )
        self._log_entry(entry)
    
    def log_compatibility_check(
        self,
        model_id: str,
        check_type: str,
        result: str,
        details: Optional[Dict[str, Any]] = None,
        trace_context: Optional[TraceContext] = None
    ):
        """Log compatibility checks."""
        level = LogLevel.INFO if result == "compatible" else LogLevel.WARNING
        message = f"Compatibility check ({check_type}): {result}"
        
        entry = self._create_log_entry(
            level=level,
            event_type=ModelOperationEvent.COMPATIBILITY_CHECK,
            message=message,
            operation="compatibility_check",
            model_id=model_id,
            details={
                "check_type": check_type,
                "result": result,
                **(details or {})
            },
            trace_context=trace_context
        )
        self._log_entry(entry)


# Global logger instances
_loggers: Dict[str, ModelOrchestratorLogger] = {}


def get_model_orchestrator_logger(name: str = "model_orchestrator") -> ModelOrchestratorLogger:
    """Get a model orchestrator logger instance."""
    if name not in _loggers:
        _loggers[name] = ModelOrchestratorLogger(name)
    return _loggers[name]


def get_default_logger() -> ModelOrchestratorLogger:
    """Get the default model orchestrator logger."""
    return get_model_orchestrator_logger()