"""
Structured Logging Service Facade
Provides structured logging capabilities for the entire system.
"""

import logging
import json
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class PIIRedactor:
    """PII redaction utility for sensitive data"""
    
    @staticmethod
    def redact_pii(text: str) -> str:
        """
        Redact PII from text content
        
        Args:
            text: Text to redact
            
        Returns:
            Text with PII redacted
        """
        if not text:
            return text
            
        # Simple PII patterns (in production, use a more comprehensive solution)
        pii_patterns = [
            (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),  # SSN
            (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CREDIT_CARD]'),  # Credit Card
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),  # Email
            (r'\b\d{10}\b', '[PHONE]'),  # Phone
        ]
        
        import re
        redacted_text = text
        for pattern, replacement in pii_patterns:
            redacted_text = re.sub(pattern, replacement, redacted_text)
            
        return redacted_text

class StructuredLoggingService:
    """
    Structured logging service facade.
    Provides centralized logging with structured output and PII redaction.
    """
    
    def __init__(self):
        """Initialize the structured logging service"""
        self.logger = logging.getLogger(__name__)
        
    def log_structured_event(
        self,
        level: LogLevel,
        event_type: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        redact_pii: bool = True
    ) -> None:
        """
        Log a structured event
        
        Args:
            level: Log level
            event_type: Type of event
            message: Log message
            data: Additional event data
            user_id: User ID
            org_id: Organization ID
            correlation_id: Correlation ID
            redact_pii: Whether to redact PII from the log message
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.value,
            "event_type": event_type,
            "message": PIIRedactor.redact_pii(message) if redact_pii else message,
            "data": data or {},
            "user_id": user_id,
            "org_id": org_id,
            "correlation_id": correlation_id,
        }
        
        # Log using the appropriate level
        if level == LogLevel.DEBUG:
            self.logger.debug(json.dumps(log_entry))
        elif level == LogLevel.INFO:
            self.logger.info(json.dumps(log_entry))
        elif level == LogLevel.WARNING:
            self.logger.warning(json.dumps(log_entry))
        elif level == LogLevel.ERROR:
            self.logger.error(json.dumps(log_entry))
        elif level == LogLevel.CRITICAL:
            self.logger.critical(json.dumps(log_entry))
    
    def log_memory_access(
        self,
        operation: str,
        memory_id: str,
        user_id: str,
        org_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        hits_count: int = 0,
        query_length: int = 0,
        top_k: int = 0,
    ) -> None:
        """
        Log memory access events
        
        Args:
            operation: Operation performed (search, commit, update, delete)
            memory_id: Memory ID accessed
            user_id: User ID
            org_id: Organization ID
            correlation_id: Correlation ID
            hits_count: Number of hits (for search)
            query_length: Query length (for search)
            top_k: Top K value (for search)
        """
        self.log_structured_event(
            level=LogLevel.INFO,
            event_type="memory_access",
            message=f"Memory {operation} operation",
            data={
                "operation": operation,
                "memory_id": memory_id,
                "hits_count": hits_count,
                "query_length": query_length,
                "top_k": top_k,
            },
            user_id=user_id,
            org_id=org_id,
            correlation_id=correlation_id,
        )
    
    def log_api_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        correlation_id: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Log API request events
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
            user_id: User ID
            org_id: Organization ID
            ip_address: Client IP address
            user_agent: User agent string
            correlation_id: Correlation ID
            **kwargs: Additional data to log
        """
        self.log_structured_event(
            level=LogLevel.INFO,
            event_type="api_request",
            message=f"API {method} {endpoint} - {status_code}",
            data={
                "method": method,
                "endpoint": endpoint,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "ip_address": ip_address,
                "user_agent": user_agent,
                **kwargs
            },
            user_id=user_id,
            org_id=org_id,
            correlation_id=correlation_id,
        )

# Global instance
_structured_logging_service: Optional[StructuredLoggingService] = None

def get_structured_logging_service() -> StructuredLoggingService:
    """Get the global structured logging service instance"""
    global _structured_logging_service
    if _structured_logging_service is None:
        _structured_logging_service = StructuredLoggingService()
    return _structured_logging_service