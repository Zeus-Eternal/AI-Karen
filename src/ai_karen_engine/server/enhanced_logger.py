"""
Enhanced Logging System for HTTP Request Validation
Implements comprehensive logging with data sanitization, structured logging for security events,
and security alert generation for high-priority threats.
"""

import json
import logging
import logging.handlers
import re
import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Set
from dataclasses import dataclass, field, asdict
import os
from pathlib import Path


class ThreatLevel(Enum):
    """Threat level enumeration"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(Enum):
    """Security event types for HTTP validation"""
    INVALID_HTTP_REQUEST = "invalid_http_request"
    MALFORMED_HEADERS = "malformed_headers"
    INVALID_METHOD = "invalid_method"
    CONTENT_TOO_LARGE = "content_too_large"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    ATTACK_PATTERN_DETECTED = "attack_pattern_detected"
    SUSPICIOUS_USER_AGENT = "suspicious_user_agent"
    PROTOCOL_VIOLATION = "protocol_violation"
    SECURITY_SCAN_DETECTED = "security_scan_detected"


@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_type: SecurityEventType
    threat_level: ThreatLevel
    description: str
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    request_id: Optional[str] = None
    attack_patterns: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    count: int = 1


@dataclass
class LoggingConfig:
    """Configuration for enhanced logging"""
    log_level: str = "INFO"
    log_dir: str = "logs"
    max_log_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_console_logging: bool = True
    enable_file_logging: bool = True
    enable_security_logging: bool = True
    sanitize_data: bool = True
    hash_client_ips: bool = True
    alert_threshold_high: int = 10  # High threat events per minute
    alert_threshold_critical: int = 5  # Critical threat events per minute


class DataSanitizer:
    """Data sanitization utility for safe logging"""
    
    # Patterns for sensitive data detection
    SENSITIVE_PATTERNS = {
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'phone': re.compile(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'),
        'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
        'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
        'api_key': re.compile(r'\b[A-Za-z0-9]{32,}\b'),
        'jwt_token': re.compile(r'\beyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b'),
        'password': re.compile(r'(?i)(password|passwd|pwd)[\s]*[:=][\s]*[^\s]+'),
        'auth_header': re.compile(r'(?i)(authorization|auth)[\s]*:[\s]*[^\s]+'),
    }
    
    # Sensitive header names
    SENSITIVE_HEADERS = {
        'authorization', 'auth', 'cookie', 'set-cookie', 'x-api-key',
        'x-auth-token', 'x-access-token', 'bearer', 'basic'
    }
    
    # Sensitive query parameters
    SENSITIVE_PARAMS = {
        'password', 'passwd', 'pwd', 'token', 'key', 'secret', 'auth',
        'api_key', 'access_token', 'refresh_token', 'session_id'
    }
    
    @classmethod
    def sanitize_text(cls, text: str, replacement: str = "[REDACTED]") -> str:
        """Sanitize sensitive data from text"""
        if not isinstance(text, str):
            return str(text)
        
        sanitized = text
        for pattern_name, pattern in cls.SENSITIVE_PATTERNS.items():
            sanitized = pattern.sub(replacement, sanitized)
        
        return sanitized
    
    @classmethod
    def sanitize_headers(cls, headers: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive headers"""
        if not isinstance(headers, dict):
            return headers
        
        sanitized = {}
        for key, value in headers.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in cls.SENSITIVE_HEADERS):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = cls.sanitize_text(str(value))
        
        return sanitized
    
    @classmethod
    def sanitize_query_params(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive query parameters"""
        if not isinstance(params, dict):
            return params
        
        sanitized = {}
        for key, value in params.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in cls.SENSITIVE_PARAMS):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = cls.sanitize_text(str(value))
        
        return sanitized
    
    @classmethod
    def sanitize_request_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize complete request data"""
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        for key, value in data.items():
            if key == 'headers':
                sanitized[key] = cls.sanitize_headers(value)
            elif key == 'query_params':
                sanitized[key] = cls.sanitize_query_params(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_request_data(value)
            elif isinstance(value, str):
                sanitized[key] = cls.sanitize_text(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    @classmethod
    def hash_ip_address(cls, ip_address: str, salt: str = "karen_security") -> str:
        """Hash IP address for privacy-preserving logging"""
        if not ip_address:
            return ""
        
        hasher = hashlib.sha256()
        hasher.update((ip_address + salt).encode('utf-8'))
        return hasher.hexdigest()[:16]  # First 16 chars for brevity


class SecurityAlertManager:
    """Manages security alerts for high-priority threats"""
    
    def __init__(self, config: LoggingConfig):
        self.config = config
        self.event_counts: Dict[str, List[datetime]] = {}
        self.alert_logger = logging.getLogger("security_alerts")
    
    def should_generate_alert(self, event: SecurityEvent) -> bool:
        """Determine if an alert should be generated"""
        if event.threat_level in [ThreatLevel.NONE, ThreatLevel.LOW]:
            return False
        
        # Track event counts for rate-based alerting
        now = datetime.now(timezone.utc)
        event_key = f"{event.event_type.value}_{event.client_ip or 'unknown'}"
        
        if event_key not in self.event_counts:
            self.event_counts[event_key] = []
        
        # Clean old events (older than 1 minute)
        self.event_counts[event_key] = [
            timestamp for timestamp in self.event_counts[event_key]
            if (now - timestamp).total_seconds() < 60
        ]
        
        # Add current event
        self.event_counts[event_key].append(now)
        
        # Check thresholds
        event_count = len(self.event_counts[event_key])
        
        if event.threat_level == ThreatLevel.CRITICAL:
            return event_count >= self.config.alert_threshold_critical
        elif event.threat_level == ThreatLevel.HIGH:
            return event_count >= self.config.alert_threshold_high
        
        return False
    
    def generate_alert(self, event: SecurityEvent) -> None:
        """Generate security alert"""
        alert_data = {
            "alert_type": "security_threat_detected",
            "threat_level": event.threat_level.value,
            "event_type": event.event_type.value,
            "description": event.description,
            "client_ip_hash": DataSanitizer.hash_ip_address(event.client_ip) if event.client_ip else None,
            "attack_patterns": event.attack_patterns,
            "timestamp": event.timestamp.isoformat(),
            "metadata": event.metadata
        }
        
        self.alert_logger.critical(
            f"SECURITY ALERT: {event.threat_level.value.upper()} - {event.description}",
            extra={"alert_data": alert_data}
        )


class EnhancedLogger:
    """Enhanced logger with data sanitization and security event handling"""
    
    def __init__(self, config: LoggingConfig = None):
        self.config = config or LoggingConfig()
        self.sanitizer = DataSanitizer()
        self.alert_manager = SecurityAlertManager(self.config)
        
        # Initialize loggers
        self._setup_logging()
        
        # Main loggers
        self.request_logger = logging.getLogger("http_requests")
        self.security_logger = logging.getLogger("security_events")
        self.validation_logger = logging.getLogger("request_validation")
        
        # Event tracking
        self.security_events: List[SecurityEvent] = []
        self.event_stats: Dict[str, int] = {}
    
    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        # Ensure log directory exists
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(exist_ok=True)
        
        # Configure formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        json_formatter = self._create_json_formatter()
        
        # Configure handlers
        handlers = []
        
        if self.config.enable_console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, self.config.log_level))
            console_handler.setFormatter(detailed_formatter)
            handlers.append(console_handler)
        
        if self.config.enable_file_logging:
            # Main application log
            file_handler = logging.handlers.RotatingFileHandler(
                log_dir / "application.log",
                maxBytes=self.config.max_log_size,
                backupCount=self.config.backup_count
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(json_formatter)
            handlers.append(file_handler)
            
            # HTTP requests log
            request_handler = logging.handlers.RotatingFileHandler(
                log_dir / "http_requests.log",
                maxBytes=self.config.max_log_size,
                backupCount=self.config.backup_count
            )
            request_handler.setLevel(logging.INFO)
            request_handler.setFormatter(json_formatter)
            
            # Security events log
            security_handler = logging.handlers.RotatingFileHandler(
                log_dir / "security_events.log",
                maxBytes=self.config.max_log_size,
                backupCount=self.config.backup_count * 2  # Keep more security logs
            )
            security_handler.setLevel(logging.WARNING)
            security_handler.setFormatter(json_formatter)
            
            # Security alerts log
            alert_handler = logging.handlers.RotatingFileHandler(
                log_dir / "security_alerts.log",
                maxBytes=self.config.max_log_size,
                backupCount=self.config.backup_count * 3  # Keep even more alert logs
            )
            alert_handler.setLevel(logging.CRITICAL)
            alert_handler.setFormatter(json_formatter)
            
            # Configure specific loggers
            logging.getLogger("http_requests").addHandler(request_handler)
            logging.getLogger("security_events").addHandler(security_handler)
            logging.getLogger("security_alerts").addHandler(alert_handler)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.log_level))
        for handler in handlers:
            root_logger.addHandler(handler)
    
    def _create_json_formatter(self) -> logging.Formatter:
        """Create JSON formatter for structured logging"""
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno
                }
                
                # Add extra fields
                for key, value in record.__dict__.items():
                    if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                                  'pathname', 'filename', 'module', 'lineno', 'funcName', 
                                  'created', 'msecs', 'relativeCreated', 'thread', 
                                  'threadName', 'processName', 'process', 'getMessage', 
                                  'exc_info', 'exc_text', 'stack_info']:
                        log_entry[key] = value
                
                return json.dumps(log_entry, default=str, separators=(',', ':'))
        
        return JSONFormatter()
    
    def log_invalid_request(self, request_data: Dict[str, Any], error_type: str, 
                           threat_level: ThreatLevel = ThreatLevel.LOW) -> None:
        """Log invalid requests with sanitized data"""
        # Sanitize request data
        sanitized_data = self.sanitizer.sanitize_request_data(request_data) if self.config.sanitize_data else request_data
        
        # Hash client IP if configured
        client_ip = request_data.get('client_ip')
        client_ip_hash = self.sanitizer.hash_ip_address(client_ip) if self.config.hash_client_ips and client_ip else client_ip
        
        # Log the invalid request
        self.request_logger.info(
            f"Invalid HTTP request: {error_type}",
            extra={
                "error_type": error_type,
                "client_ip_hash": client_ip_hash,
                "request_data": sanitized_data,
                "threat_level": threat_level.value
            }
        )
        
        # Create security event if threat level is significant
        if threat_level != ThreatLevel.NONE:
            event_type = SecurityEventType.INVALID_HTTP_REQUEST
            if error_type == "malformed_headers":
                event_type = SecurityEventType.MALFORMED_HEADERS
            elif error_type == "invalid_method":
                event_type = SecurityEventType.INVALID_METHOD
            elif error_type == "content_too_large":
                event_type = SecurityEventType.CONTENT_TOO_LARGE
            
            security_event = SecurityEvent(
                event_type=event_type,
                threat_level=threat_level,
                description=f"Invalid HTTP request: {error_type}",
                client_ip=client_ip,
                user_agent=request_data.get('user_agent'),
                endpoint=request_data.get('endpoint'),
                method=request_data.get('method'),
                request_id=request_data.get('request_id'),
                metadata=sanitized_data
            )
            
            self.log_security_event(security_event)
    
    def log_security_event(self, event: SecurityEvent) -> None:
        """Log security-related events"""
        # Store event for analysis
        self.security_events.append(event)
        
        # Update statistics
        event_key = f"{event.event_type.value}_{event.threat_level.value}"
        self.event_stats[event_key] = self.event_stats.get(event_key, 0) + 1
        
        # Prepare event data for logging
        event_data = {
            "event_type": event.event_type.value,
            "threat_level": event.threat_level.value,
            "description": event.description,
            "client_ip_hash": self.sanitizer.hash_ip_address(event.client_ip) if event.client_ip else None,
            "user_agent": self.sanitizer.sanitize_text(event.user_agent) if event.user_agent else None,
            "endpoint": event.endpoint,
            "method": event.method,
            "request_id": event.request_id,
            "attack_patterns": event.attack_patterns,
            "timestamp": event.timestamp.isoformat(),
            "count": event.count,
            "metadata": event.metadata
        }
        
        # Log based on threat level
        if event.threat_level == ThreatLevel.CRITICAL:
            self.security_logger.critical(
                f"CRITICAL SECURITY EVENT: {event.description}",
                extra={"security_event": event_data}
            )
        elif event.threat_level == ThreatLevel.HIGH:
            self.security_logger.error(
                f"HIGH SECURITY EVENT: {event.description}",
                extra={"security_event": event_data}
            )
        elif event.threat_level == ThreatLevel.MEDIUM:
            self.security_logger.warning(
                f"MEDIUM SECURITY EVENT: {event.description}",
                extra={"security_event": event_data}
            )
        else:
            self.security_logger.info(
                f"SECURITY EVENT: {event.description}",
                extra={"security_event": event_data}
            )
        
        # Check if alert should be generated
        if self.alert_manager.should_generate_alert(event):
            self.generate_security_alert(event)
    
    def generate_security_alert(self, event: SecurityEvent) -> None:
        """Generate security alerts for high-priority threats"""
        self.alert_manager.generate_alert(event)
    
    def log_rate_limit_violation(self, client_ip: str, endpoint: str, 
                               limit: int, current_count: int, 
                               request_id: str = None) -> None:
        """Log rate limit violations"""
        security_event = SecurityEvent(
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            threat_level=ThreatLevel.MEDIUM,
            description=f"Rate limit exceeded: {current_count}/{limit} requests",
            client_ip=client_ip,
            endpoint=endpoint,
            request_id=request_id,
            metadata={
                "limit": limit,
                "current_count": current_count,
                "violation_ratio": current_count / limit if limit > 0 else 0
            }
        )
        
        self.log_security_event(security_event)
    
    def log_attack_pattern_detected(self, client_ip: str, patterns: List[str], 
                                  request_data: Dict[str, Any], 
                                  threat_level: ThreatLevel = ThreatLevel.HIGH) -> None:
        """Log detected attack patterns"""
        security_event = SecurityEvent(
            event_type=SecurityEventType.ATTACK_PATTERN_DETECTED,
            threat_level=threat_level,
            description=f"Attack patterns detected: {', '.join(patterns)}",
            client_ip=client_ip,
            user_agent=request_data.get('user_agent'),
            endpoint=request_data.get('endpoint'),
            method=request_data.get('method'),
            request_id=request_data.get('request_id'),
            attack_patterns=patterns,
            metadata=self.sanitizer.sanitize_request_data(request_data) if self.config.sanitize_data else request_data
        )
        
        self.log_security_event(security_event)
    
    def log_protocol_violation(self, client_ip: str, violation_type: str, 
                             details: Dict[str, Any], request_id: str = None) -> None:
        """Log HTTP protocol violations"""
        security_event = SecurityEvent(
            event_type=SecurityEventType.PROTOCOL_VIOLATION,
            threat_level=ThreatLevel.MEDIUM,
            description=f"HTTP protocol violation: {violation_type}",
            client_ip=client_ip,
            request_id=request_id,
            metadata=details
        )
        
        self.log_security_event(security_event)
    
    def log_security_scan_detected(self, client_ip: str, scan_type: str, 
                                 indicators: List[str], request_id: str = None) -> None:
        """Log detected security scans"""
        security_event = SecurityEvent(
            event_type=SecurityEventType.SECURITY_SCAN_DETECTED,
            threat_level=ThreatLevel.HIGH,
            description=f"Security scan detected: {scan_type}",
            client_ip=client_ip,
            request_id=request_id,
            attack_patterns=indicators,
            metadata={"scan_type": scan_type, "indicators": indicators}
        )
        
        self.log_security_event(security_event)
    
    def get_security_statistics(self) -> Dict[str, Any]:
        """Get security event statistics"""
        total_events = len(self.security_events)
        
        # Count by threat level
        threat_level_counts = {}
        for level in ThreatLevel:
            threat_level_counts[level.value] = sum(
                1 for event in self.security_events if event.threat_level == level
            )
        
        # Count by event type
        event_type_counts = {}
        for event_type in SecurityEventType:
            event_type_counts[event_type.value] = sum(
                1 for event in self.security_events if event.event_type == event_type
            )
        
        # Recent events (last hour)
        now = datetime.now(timezone.utc)
        recent_events = [
            event for event in self.security_events
            if (now - event.timestamp).total_seconds() < 3600
        ]
        
        return {
            "total_events": total_events,
            "recent_events_count": len(recent_events),
            "threat_level_distribution": threat_level_counts,
            "event_type_distribution": event_type_counts,
            "event_stats": self.event_stats.copy()
        }
    
    def get_recent_security_events(self, limit: int = 100, 
                                 threat_level: ThreatLevel = None) -> List[SecurityEvent]:
        """Get recent security events, optionally filtered by threat level"""
        events = self.security_events
        
        if threat_level:
            events = [event for event in events if event.threat_level == threat_level]
        
        # Sort by timestamp (most recent first) and limit
        events.sort(key=lambda x: x.timestamp, reverse=True)
        return events[:limit]
    
    def clear_old_events(self, max_age_hours: int = 24) -> int:
        """Clear old security events to prevent memory buildup"""
        now = datetime.now(timezone.utc)
        cutoff_time = now.timestamp() - (max_age_hours * 3600)
        
        initial_count = len(self.security_events)
        self.security_events = [
            event for event in self.security_events
            if event.timestamp.timestamp() > cutoff_time
        ]
        
        cleared_count = initial_count - len(self.security_events)
        
        if cleared_count > 0:
            self.validation_logger.info(
                f"Cleared {cleared_count} old security events (older than {max_age_hours} hours)"
            )
        
        return cleared_count


# Global enhanced logger instance
_enhanced_logger: Optional[EnhancedLogger] = None


def get_enhanced_logger(config: LoggingConfig = None) -> EnhancedLogger:
    """Get global enhanced logger instance"""
    global _enhanced_logger
    if _enhanced_logger is None:
        _enhanced_logger = EnhancedLogger(config)
    return _enhanced_logger


def init_enhanced_logging(config: LoggingConfig = None) -> EnhancedLogger:
    """Initialize global enhanced logging"""
    global _enhanced_logger
    _enhanced_logger = EnhancedLogger(config)
    return _enhanced_logger


# Export main classes and functions
__all__ = [
    "EnhancedLogger",
    "LoggingConfig", 
    "SecurityEvent",
    "SecurityEventType",
    "ThreatLevel",
    "DataSanitizer",
    "SecurityAlertManager",
    "get_enhanced_logger",
    "init_enhanced_logging"
]