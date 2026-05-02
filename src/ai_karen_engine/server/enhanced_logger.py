from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, Optional

from ai_karen_engine.core.logging import get_logger

class EnhancedLogger:
    """
    Compatibility shim for legacy EnhancedLogger.
    Routes security and validation events to the canonical system.
    """
    def __init__(self, config: Any = None):
        self.logger = get_logger("kari.legacy.enhanced")

    def log_invalid_request(self, **kwargs):
        self.logger.event("security.http.invalid", **kwargs)

    def log_security_event(self, **kwargs):
        self.logger.event("security.event", **kwargs)

    def log_rate_limit_violation(self, **kwargs):
        self.logger.event("security.ratelimit.violation", **kwargs)

def get_enhanced_logger(config: Any = None) -> EnhancedLogger:
    return EnhancedLogger(config)

def init_enhanced_logging(config: Any = None) -> EnhancedLogger:
    return get_enhanced_logger(config)

# Compatibility Symbols
class ThreatLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityEventType(str, Enum):
    AUTHENTICATION = "auth"
    AUTHORIZATION = "rbac"
    VALIDATION = "validation"
    THREAT = "threat"

class SecurityEvent:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class LoggingConfig:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class DataSanitizer:
    @staticmethod
    def sanitize(data): return data

class SecurityAlertManager:
    def __init__(self, **kwargs): pass
