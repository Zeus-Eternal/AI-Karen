"""
Structured Logging Service

Replaces development logging with structured JSON logs, adds correlation IDs,
implements user action tracking, and provides error aggregation.

Requirements: 1.2, 8.5
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from contextvars import ContextVar
from dataclasses import dataclass, field, asdict
from enum import Enum
import traceback

from ai_karen_engine.core.logging import get_logger

# Context variables for correlation tracking
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar('session_id', default=None)


class LogLevel(str, Enum):
    """Structured log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogCategory(str, Enum):
    """Log categories for better organization"""
    SYSTEM = "system"
    AUTH = "authentication"
    API = "api"
    DATABASE = "database"
    LLM = "llm"
    RESPONSE_FORMATTING = "response_formatting"
    USER_ACTION = "user_action"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ERROR = "error"


@dataclass
class StructuredLogEntry:
    """Structured log entry with all required fields"""
    timestamp: str
    level: LogLevel
    category: LogCategory
    message: str
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    service: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    duration_ms: Optional[float] = None
    status_code: Optional[int] = None
    error_type: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None

    def to_json(self) -> str:
        """Convert log entry to JSON string"""
        # Convert to dict and remove None values
        data = {k: v for k, v in asdict(self).items() if v is not None}
        return json.dumps(data, default=str, separators=(',', ':'))


class StructuredLogger:
    """
    Structured logger that produces JSON logs with correlation IDs
    and comprehensive metadata.
    """

    def __init__(self, service_name: str, component_name: Optional[str] = None):
        self.service_name = service_name
        self.component_name = component_name
        self.base_logger = get_logger(f"{service_name}.{component_name}" if component_name else service_name)
        
        # Configure JSON formatter if not already configured
        self._configure_json_logging()

    def _configure_json_logging(self):
        """Configure JSON logging format"""
        # Determine the underlying logging.Logger (KarenLogger wraps it)
        underlying_logger = getattr(self.base_logger, "logger", self.base_logger)
        handlers = getattr(underlying_logger, "handlers", [])

        # Check if handler already has JSON formatter
        for handler in handlers:
            formatter = getattr(handler, "formatter", None)
            if getattr(formatter, "_is_json_formatter", False):
                return

        if not handlers:
            return

        # Add JSON formatter to all handlers
        json_formatter = StructuredLogFormatter()
        for handler in handlers:
            handler.setFormatter(json_formatter)

    def _create_log_entry(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        operation: Optional[str] = None,
        duration_ms: Optional[float] = None,
        status_code: Optional[int] = None,
        error: Optional[Exception] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StructuredLogEntry:
        """Create a structured log entry"""
        
        # Get context variables
        correlation_id = correlation_id_var.get()
        user_id = user_id_var.get()
        session_id = session_id_var.get()
        
        # Handle error information
        error_type = None
        error_details = None
        stack_trace = None
        
        if error:
            error_type = type(error).__name__
            error_details = {
                "message": str(error),
                "type": error_type,
            }
            if hasattr(error, '__dict__'):
                error_details.update({
                    k: v for k, v in error.__dict__.items()
                    if not k.startswith('_') and isinstance(v, (str, int, float, bool, list, dict))
                })
            
            stack_trace = traceback.format_exc()

        return StructuredLogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            level=level,
            category=category,
            message=message,
            correlation_id=correlation_id,
            user_id=user_id,
            session_id=session_id,
            service=self.service_name,
            component=self.component_name,
            operation=operation,
            duration_ms=duration_ms,
            status_code=status_code,
            error_type=error_type,
            error_details=error_details,
            metadata=metadata or {},
            stack_trace=stack_trace
        )

    def debug(
        self,
        message: str,
        category: LogCategory = LogCategory.SYSTEM,
        operation: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log debug message"""
        entry = self._create_log_entry(
            LogLevel.DEBUG, category, message, operation=operation, metadata=metadata
        )
        self.base_logger.debug(entry.to_json())

    def info(
        self,
        message: str,
        category: LogCategory = LogCategory.SYSTEM,
        operation: Optional[str] = None,
        duration_ms: Optional[float] = None,
        status_code: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log info message"""
        entry = self._create_log_entry(
            LogLevel.INFO, category, message,
            operation=operation, duration_ms=duration_ms,
            status_code=status_code, metadata=metadata
        )
        self.base_logger.info(entry.to_json())

    def warning(
        self,
        message: str,
        category: LogCategory = LogCategory.SYSTEM,
        operation: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log warning message"""
        entry = self._create_log_entry(
            LogLevel.WARNING, category, message, operation=operation, metadata=metadata
        )
        self.base_logger.warning(entry.to_json())

    def error(
        self,
        message: str,
        error: Optional[Exception] = None,
        category: LogCategory = LogCategory.ERROR,
        operation: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log error message"""
        entry = self._create_log_entry(
            LogLevel.ERROR, category, message,
            operation=operation, error=error, metadata=metadata
        )
        self.base_logger.error(entry.to_json())

    def critical(
        self,
        message: str,
        error: Optional[Exception] = None,
        category: LogCategory = LogCategory.ERROR,
        operation: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log critical message"""
        entry = self._create_log_entry(
            LogLevel.CRITICAL, category, message,
            operation=operation, error=error, metadata=metadata
        )
        self.base_logger.critical(entry.to_json())

    def log_user_action(
        self,
        action: str,
        resource: Optional[str] = None,
        result: str = "success",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log user action for audit trail"""
        action_metadata = {
            "action": action,
            "resource": resource,
            "result": result,
        }
        if metadata:
            action_metadata.update(metadata)

        self.info(
            f"User action: {action}",
            category=LogCategory.USER_ACTION,
            operation="user_action",
            metadata=action_metadata
        )

    def log_api_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_ms: float,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Log API request"""
        metadata = {
            "method": method,
            "endpoint": endpoint,
            "user_agent": user_agent,
            "ip_address": ip_address,
        }

        self.info(
            f"{method} {endpoint} - {status_code}",
            category=LogCategory.API,
            operation="api_request",
            duration_ms=duration_ms,
            status_code=status_code,
            metadata=metadata
        )

    def log_database_operation(
        self,
        operation: str,
        table: Optional[str] = None,
        duration_ms: Optional[float] = None,
        affected_rows: Optional[int] = None,
        error: Optional[Exception] = None
    ):
        """Log database operation"""
        metadata = {
            "table": table,
            "affected_rows": affected_rows,
        }

        if error:
            self.error(
                f"Database operation failed: {operation}",
                error=error,
                category=LogCategory.DATABASE,
                operation=operation,
                metadata=metadata
            )
        else:
            self.info(
                f"Database operation: {operation}",
                category=LogCategory.DATABASE,
                operation=operation,
                duration_ms=duration_ms,
                metadata=metadata
            )

    def log_llm_request(
        self,
        provider: str,
        model: str,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        duration_ms: Optional[float] = None,
        error: Optional[Exception] = None
    ):
        """Log LLM request"""
        metadata = {
            "provider": provider,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }

        if error:
            self.error(
                f"LLM request failed: {provider}/{model}",
                error=error,
                category=LogCategory.LLM,
                operation="llm_request",
                metadata=metadata
            )
        else:
            self.info(
                f"LLM request: {provider}/{model}",
                category=LogCategory.LLM,
                operation="llm_request",
                duration_ms=duration_ms,
                metadata=metadata
            )

    def log_security_event(
        self,
        event_type: str,
        severity: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None
    ):
        """Log security event"""
        metadata = {
            "event_type": event_type,
            "severity": severity,
            "ip_address": ip_address,
        }
        metadata.update(details)

        level = LogLevel.CRITICAL if severity == "critical" else LogLevel.WARNING

        entry = self._create_log_entry(
            level, LogCategory.SECURITY,
            f"Security event: {event_type}",
            operation="security_event",
            metadata=metadata
        )

        if level == LogLevel.CRITICAL:
            self.base_logger.critical(entry.to_json())
        else:
            self.base_logger.warning(entry.to_json())


class StructuredLogFormatter(logging.Formatter):
    """Custom formatter that handles structured log entries"""
    
    def __init__(self):
        super().__init__()
        self._is_json_formatter = True

    def format(self, record):
        # If the message is already JSON (from StructuredLogger), return as-is
        try:
            json.loads(record.getMessage())
            return record.getMessage()
        except (json.JSONDecodeError, ValueError):
            pass

        # For non-structured logs, create a basic structured format
        entry = StructuredLogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            level=LogLevel(record.levelname.lower()),
            category=LogCategory.SYSTEM,
            message=record.getMessage(),
            service="legacy",
            metadata={
                "logger_name": record.name,
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
        )

        if record.exc_info:
            entry.stack_trace = self.formatException(record.exc_info)

        return entry.to_json()


# Context management functions

def set_correlation_id(correlation_id: str):
    """Set correlation ID for current context"""
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """Get correlation ID from current context"""
    return correlation_id_var.get()


def generate_correlation_id() -> str:
    """Generate a new correlation ID"""
    return str(uuid.uuid4())


def set_user_context(user_id: str, session_id: Optional[str] = None):
    """Set user context for logging"""
    user_id_var.set(user_id)
    if session_id:
        session_id_var.set(session_id)


def clear_context():
    """Clear all context variables"""
    correlation_id_var.set(None)
    user_id_var.set(None)
    session_id_var.set(None)


# Factory function for creating structured loggers

def get_structured_logger(service_name: str, component_name: Optional[str] = None) -> StructuredLogger:
    """
    Get a structured logger instance.
    
    Args:
        service_name: Name of the service
        component_name: Optional component name
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(service_name, component_name)
