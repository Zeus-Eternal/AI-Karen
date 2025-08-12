"""
Structured Logging with Security Compliance - Phase 4.1.d
Production-ready structured JSON logging with PII protection and security incident logging.
"""

import json
import logging
import logging.config
import re
import hashlib
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
import os

# Security patterns for PII detection
PII_PATTERNS = {
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'phone': re.compile(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'),
    'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
    'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
    'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
    'api_key': re.compile(r'\b[A-Za-z0-9]{32,}\b'),
    'jwt_token': re.compile(r'\beyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b')
}

class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class SecurityEventType(Enum):
    """Security event types"""
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_FAILURE = "authorization_failure"
    CROSS_TENANT_ACCESS_ATTEMPT = "cross_tenant_access_attempt"
    RATE_LIMIT_VIOLATION = "rate_limit_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_ACCESS_VIOLATION = "data_access_violation"
    PRIVILEGE_ESCALATION_ATTEMPT = "privilege_escalation_attempt"
    MALICIOUS_INPUT_DETECTED = "malicious_input_detected"

@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_type: SecurityEventType
    severity: str
    description: str
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class StructuredLogEntry:
    """Structured log entry data structure"""
    timestamp: str
    level: str
    logger: str
    message: str
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    security_event: Optional[Dict[str, Any]] = None

class PIIRedactor:
    """PII redaction utility"""
    
    @staticmethod
    def redact_pii(text: str, replacement: str = "[REDACTED]") -> str:
        """Redact PII from text"""
        if not isinstance(text, str):
            return text
        
        redacted_text = text
        for pii_type, pattern in PII_PATTERNS.items():
            redacted_text = pattern.sub(replacement, redacted_text)
        
        return redacted_text
    
    @staticmethod
    def redact_dict(data: Dict[str, Any], sensitive_keys: List[str] = None) -> Dict[str, Any]:
        """Redact PII from dictionary values"""
        if not isinstance(data, dict):
            return data
        
        sensitive_keys = sensitive_keys or [
            'password', 'token', 'secret', 'key', 'auth', 'credential',
            'email', 'phone', 'ssn', 'credit_card', 'api_key'
        ]
        
        redacted_data = {}
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if key is sensitive
            if any(sensitive_key in key_lower for sensitive_key in sensitive_keys):
                redacted_data[key] = "[REDACTED]"
            elif isinstance(value, str):
                redacted_data[key] = PIIRedactor.redact_pii(value)
            elif isinstance(value, dict):
                redacted_data[key] = PIIRedactor.redact_dict(value, sensitive_keys)
            elif isinstance(value, list):
                redacted_data[key] = [
                    PIIRedactor.redact_dict(item, sensitive_keys) if isinstance(item, dict)
                    else PIIRedactor.redact_pii(str(item)) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                redacted_data[key] = value
        
        return redacted_data
    
    @staticmethod
    def hash_sensitive_data(data: str, salt: str = "") -> str:
        """Hash sensitive data for logging"""
        if not data:
            return ""
        
        hasher = hashlib.sha256()
        hasher.update((data + salt).encode('utf-8'))
        return hasher.hexdigest()[:16]  # First 16 chars for brevity

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def __init__(self, include_pii: bool = False, redact_sensitive: bool = True):
        super().__init__()
        self.include_pii = include_pii
        self.redact_sensitive = redact_sensitive
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        # Extract correlation ID and other context
        correlation_id = getattr(record, 'correlation_id', None)
        user_id = getattr(record, 'user_id', None)
        org_id = getattr(record, 'org_id', None)
        endpoint = getattr(record, 'endpoint', None)
        method = getattr(record, 'method', None)
        status_code = getattr(record, 'status_code', None)
        duration_ms = getattr(record, 'duration_ms', None)
        ip_address = getattr(record, 'ip_address', None)
        user_agent = getattr(record, 'user_agent', None)
        security_event = getattr(record, 'security_event', None)
        
        # Extract metadata from extra fields
        metadata = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info', 'correlation_id', 'user_id', 
                          'org_id', 'endpoint', 'method', 'status_code', 'duration_ms',
                          'ip_address', 'user_agent', 'security_event']:
                metadata[key] = value
        
        # Create structured log entry
        log_entry = StructuredLogEntry(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            logger=record.name,
            message=record.getMessage(),
            correlation_id=correlation_id,
            user_id=user_id,
            org_id=org_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
            security_event=security_event
        )
        
        # Convert to dict and redact if necessary
        log_dict = asdict(log_entry)
        
        if self.redact_sensitive and not self.include_pii:
            log_dict = PIIRedactor.redact_dict(log_dict)
        
        # Remove None values
        log_dict = {k: v for k, v in log_dict.items() if v is not None}
        
        return json.dumps(log_dict, default=str, separators=(',', ':'))

class SecurityLogger:
    """Specialized logger for security events"""
    
    def __init__(self, logger_name: str = "security"):
        self.logger = logging.getLogger(logger_name)
        self.security_events = []
    
    def log_security_event(self, event: SecurityEvent):
        """Log a security event"""
        # Store event for analysis
        self.security_events.append(event)
        
        # Create log entry
        event_dict = asdict(event)
        event_dict['timestamp'] = event.timestamp.isoformat()
        event_dict['event_type'] = event.event_type.value
        
        # Redact PII from metadata
        if event_dict.get('metadata'):
            event_dict['metadata'] = PIIRedactor.redact_dict(event_dict['metadata'])
        
        self.logger.warning(
            f"Security Event: {event.event_type.value} - {event.description}",
            extra={
                'security_event': event_dict,
                'correlation_id': event.correlation_id,
                'user_id': event.user_id,
                'org_id': event.org_id,
                'ip_address': event.ip_address,
                'endpoint': event.endpoint,
                'method': event.method
            }
        )
    
    def log_authentication_failure(self, user_id: str, ip_address: str, 
                                 correlation_id: str = None, **kwargs):
        """Log authentication failure"""
        event = SecurityEvent(
            event_type=SecurityEventType.AUTHENTICATION_FAILURE,
            severity="HIGH",
            description=f"Authentication failed for user {user_id}",
            user_id=user_id,
            ip_address=ip_address,
            correlation_id=correlation_id,
            metadata=kwargs
        )
        self.log_security_event(event)
    
    def log_authorization_failure(self, user_id: str, endpoint: str, 
                                required_scope: str, correlation_id: str = None, **kwargs):
        """Log authorization failure"""
        event = SecurityEvent(
            event_type=SecurityEventType.AUTHORIZATION_FAILURE,
            severity="MEDIUM",
            description=f"Authorization failed for user {user_id} accessing {endpoint}",
            user_id=user_id,
            endpoint=endpoint,
            correlation_id=correlation_id,
            metadata={'required_scope': required_scope, **kwargs}
        )
        self.log_security_event(event)
    
    def log_cross_tenant_access_attempt(self, user_id: str, user_org_id: str, 
                                      attempted_org_id: str, correlation_id: str = None, **kwargs):
        """Log cross-tenant access attempt"""
        event = SecurityEvent(
            event_type=SecurityEventType.CROSS_TENANT_ACCESS_ATTEMPT,
            severity="CRITICAL",
            description=f"User {user_id} from org {user_org_id} attempted to access org {attempted_org_id}",
            user_id=user_id,
            org_id=user_org_id,
            correlation_id=correlation_id,
            metadata={'attempted_org_id': attempted_org_id, **kwargs}
        )
        self.log_security_event(event)
    
    def log_rate_limit_violation(self, user_id: str, endpoint: str, 
                               limit: int, current_count: int, 
                               correlation_id: str = None, **kwargs):
        """Log rate limit violation"""
        event = SecurityEvent(
            event_type=SecurityEventType.RATE_LIMIT_VIOLATION,
            severity="MEDIUM",
            description=f"Rate limit exceeded for user {user_id} on {endpoint}",
            user_id=user_id,
            endpoint=endpoint,
            correlation_id=correlation_id,
            metadata={'limit': limit, 'current_count': current_count, **kwargs}
        )
        self.log_security_event(event)
    
    def log_suspicious_activity(self, description: str, user_id: str = None, 
                              ip_address: str = None, correlation_id: str = None, **kwargs):
        """Log suspicious activity"""
        event = SecurityEvent(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity="HIGH",
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            correlation_id=correlation_id,
            metadata=kwargs
        )
        self.log_security_event(event)
    
    def get_recent_events(self, limit: int = 100) -> List[SecurityEvent]:
        """Get recent security events"""
        return self.security_events[-limit:]

class StructuredLoggingService:
    """Main structured logging service"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.security_logger = SecurityLogger()
        self.configured = False
        
        # Initialize logging configuration
        self.configure_logging()
    
    def configure_logging(self):
        """Configure structured logging"""
        # Default configuration
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'structured': {
                    '()': StructuredFormatter,
                    'include_pii': os.getenv('LOG_INCLUDE_PII', 'false').lower() == 'true',
                    'redact_sensitive': os.getenv('LOG_REDACT_SENSITIVE', 'true').lower() == 'true'
                },
                'simple': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'structured',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'DEBUG',
                    'formatter': 'structured',
                    'filename': 'logs/application.log',
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5
                },
                'security': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'WARNING',
                    'formatter': 'structured',
                    'filename': 'logs/security.log',
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 10
                }
            },
            'loggers': {
                'security': {
                    'level': 'WARNING',
                    'handlers': ['security', 'console'],
                    'propagate': False
                },
                'ai_karen_engine': {
                    'level': 'INFO',
                    'handlers': ['file', 'console'],
                    'propagate': False
                }
            },
            'root': {
                'level': 'INFO',
                'handlers': ['console']
            }
        }
        
        # Load custom configuration if provided
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    custom_config = json.load(f)
                    config.update(custom_config)
            except Exception as e:
                print(f"Failed to load logging config from {self.config_path}: {e}")
        
        # Ensure log directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Apply configuration
        logging.config.dictConfig(config)
        self.configured = True
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a configured logger"""
        if not self.configured:
            self.configure_logging()
        
        return logging.getLogger(name)
    
    def get_security_logger(self) -> SecurityLogger:
        """Get security logger"""
        return self.security_logger
    
    def create_request_logger(self, correlation_id: str, user_id: str = None, 
                            org_id: str = None, ip_address: str = None) -> logging.Logger:
        """Create a logger with request context"""
        logger = self.get_logger('request')
        
        # Create a logger adapter that adds context to all log records
        class ContextAdapter(logging.LoggerAdapter):
            def process(self, msg, kwargs):
                extra = kwargs.get('extra', {})
                extra.update({
                    'correlation_id': correlation_id,
                    'user_id': user_id,
                    'org_id': org_id,
                    'ip_address': ip_address
                })
                kwargs['extra'] = extra
                return msg, kwargs
        
        return ContextAdapter(logger, {})
    
    def log_api_request(self, method: str, endpoint: str, status_code: int, 
                       duration_ms: float, user_id: str = None, org_id: str = None,
                       ip_address: str = None, user_agent: str = None, 
                       correlation_id: str = None, **kwargs):
        """Log API request"""
        logger = self.get_logger('api')
        
        level = logging.INFO
        if status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING
        
        logger.log(
            level,
            f"{method} {endpoint} - {status_code} - {duration_ms:.2f}ms",
            extra={
                'method': method,
                'endpoint': endpoint,
                'status_code': status_code,
                'duration_ms': duration_ms,
                'user_id': user_id,
                'org_id': org_id,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'correlation_id': correlation_id,
                **kwargs
            }
        )
    
    def log_memory_access(self, operation: str, memory_id: str, user_id: str, 
                         org_id: str = None, correlation_id: str = None, **kwargs):
        """Log memory access (without content for privacy)"""
        logger = self.get_logger('memory')
        
        # Hash memory ID for privacy
        memory_id_hash = PIIRedactor.hash_sensitive_data(memory_id)
        
        logger.info(
            f"Memory {operation}: {memory_id_hash}",
            extra={
                'operation': operation,
                'memory_id_hash': memory_id_hash,
                'user_id': user_id,
                'org_id': org_id,
                'correlation_id': correlation_id,
                **kwargs
            }
        )

# Global structured logging service instance
_structured_logging_service: Optional[StructuredLoggingService] = None

def get_structured_logging_service() -> StructuredLoggingService:
    """Get global structured logging service instance"""
    global _structured_logging_service
    if _structured_logging_service is None:
        _structured_logging_service = StructuredLoggingService()
    return _structured_logging_service

def init_structured_logging(config_path: str = None) -> StructuredLoggingService:
    """Initialize global structured logging service"""
    global _structured_logging_service
    _structured_logging_service = StructuredLoggingService(config_path)
    return _structured_logging_service

def get_security_logger() -> SecurityLogger:
    """Get security logger instance"""
    return get_structured_logging_service().get_security_logger()

# Export main classes and functions
__all__ = [
    "StructuredLoggingService",
    "SecurityLogger",
    "SecurityEvent",
    "SecurityEventType",
    "StructuredLogEntry",
    "StructuredFormatter",
    "PIIRedactor",
    "get_structured_logging_service",
    "init_structured_logging",
    "get_security_logger"
]