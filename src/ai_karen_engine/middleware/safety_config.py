"""
Configuration for Safety Middleware.

This module provides configuration classes and utilities for the Safety Middleware,
including default settings, validation, and environment variable support.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

from src.services.agents.agent_safety_types import SafetyLevel

logger = logging.getLogger(__name__)


class SafetyMiddlewareMode(str, Enum):
    """Enum representing different safety middleware modes."""
    DISABLED = "disabled"
    MONITOR = "monitor"
    ENFORCE = "enforce"
    STRICT = "strict"


@dataclass
class ContentSafetyConfig:
    """Configuration for content safety checks."""
    
    enabled: bool = True
    sensitivity_level: SafetyLevel = SafetyLevel.MEDIUM
    check_input: bool = True
    check_output: bool = True
    max_content_length: int = 1000000  # 1MB
    blocked_keywords: List[str] = field(default_factory=lambda: [
        "malicious", "harmful", "dangerous", "illegal"
    ])
    allowed_content_types: List[str] = field(default_factory=lambda: [
        "text/plain", "application/json"
    ])
    ml_filtering_enabled: bool = True
    adaptive_learning_enabled: bool = True
    custom_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthorizationConfig:
    """Configuration for authorization checks."""
    
    enabled: bool = True
    strict_mode: bool = False
    default_role: str = "user"
    admin_roles: List[str] = field(default_factory=lambda: ["admin", "administrator"])
    protected_paths: Dict[str, List[str]] = field(default_factory=lambda: {
        "admin": ["/admin/", "/api/admin/"],
        "user": ["/api/user/", "/api/profile/"],
        "guest": []
    })
    public_paths: List[str] = field(default_factory=lambda: [
        "/health", "/metrics", "/docs", "/openapi.json", "/redoc",
        "/api/auth/login", "/api/auth/health", "/api/auth/status"
    ])
    session_timeout: int = 3600  # 1 hour
    token_refresh_enabled: bool = True


@dataclass
class BehaviorMonitoringConfig:
    """Configuration for behavior monitoring."""
    
    enabled: bool = True
    track_requests: bool = True
    track_responses: bool = True
    track_errors: bool = True
    anomaly_detection: bool = True
    baseline_learning: bool = True
    risk_assessment: bool = True
    max_events_per_session: int = 1000
    event_retention_days: int = 30
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "error_rate": 0.1,  # 10%
        "request_rate": 100,  # requests per minute
        "response_time": 5.0  # seconds
    })


@dataclass
class ComplianceConfig:
    """Configuration for compliance checking."""
    
    enabled: bool = True
    standards: List[str] = field(default_factory=lambda: [
        "SOC2", "GDPR", "HIPAA", "ISO27001"
    ])
    audit_logging: bool = True
    data_retention_days: int = 365
    report_generation_interval: int = 86400  # 24 hours
    auto_escalation: bool = True
    violation_threshold: int = 3
    escalation_contacts: List[str] = field(default_factory=lambda: [
        "security_team", "compliance_officer"
    ])


@dataclass
class SafetyMiddlewareConfig:
    """Main configuration for the Safety Middleware."""
    
    # General settings
    mode: SafetyMiddlewareMode = SafetyMiddlewareMode.ENFORCE
    enabled: bool = True
    log_safety_events: bool = True
    debug_mode: bool = False
    
    # Component configurations
    content_safety: ContentSafetyConfig = field(default_factory=ContentSafetyConfig)
    authorization: AuthorizationConfig = field(default_factory=AuthorizationConfig)
    behavior_monitoring: BehaviorMonitoringConfig = field(default_factory=BehaviorMonitoringConfig)
    compliance: ComplianceConfig = field(default_factory=ComplianceConfig)
    
    # Response templates
    blocked_response_template: Dict[str, Any] = field(default_factory=lambda: {
        "error": "Content blocked by safety check",
        "message": "The requested content was blocked due to safety concerns",
        "safety_action": "block"
    })
    
    warn_response_template: Dict[str, Any] = field(default_factory=lambda: {
        "warning": "Content safety warning",
        "message": "The content triggered a safety warning but was allowed to proceed",
        "safety_action": "warn"
    })
    
    # Performance settings
    max_processing_time: float = 5.0  # seconds
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5 minutes
    
    @classmethod
    def from_environment(cls) -> 'SafetyMiddlewareConfig':
        """
        Create configuration from environment variables.
        
        Returns:
            SafetyMiddlewareConfig instance with values from environment variables
        """
        # General settings
        mode_str = os.getenv("SAFETY_MIDDLEWARE_MODE", SafetyMiddlewareMode.ENFORCE.value)
        try:
            mode = SafetyMiddlewareMode(mode_str.lower())
        except ValueError:
            logger.warning(f"Invalid safety middleware mode: {mode_str}, using default")
            mode = SafetyMiddlewareMode.ENFORCE
        
        enabled = os.getenv("SAFETY_MIDDLEWARE_ENABLED", "true").lower() == "true"
        log_events = os.getenv("SAFETY_MIDDLEWARE_LOG_EVENTS", "true").lower() == "true"
        debug_mode = os.getenv("SAFETY_MIDDLEWARE_DEBUG", "false").lower() == "true"
        
        # Content safety settings
        content_enabled = os.getenv("SAFETY_CONTENT_ENABLED", "true").lower() == "true"
        content_sensitivity = os.getenv("SAFETY_CONTENT_SENSITIVITY", SafetyLevel.MEDIUM.value)
        try:
            content_sensitivity_level = SafetyLevel(content_sensitivity.lower())
        except ValueError:
            logger.warning(f"Invalid content sensitivity level: {content_sensitivity}, using default")
            content_sensitivity_level = SafetyLevel.MEDIUM
        
        content_safety = ContentSafetyConfig(
            enabled=content_enabled,
            sensitivity_level=content_sensitivity_level
        )
        
        # Authorization settings
        auth_enabled = os.getenv("SAFETY_AUTH_ENABLED", "true").lower() == "true"
        auth_strict = os.getenv("SAFETY_AUTH_STRICT", "false").lower() == "true"
        authorization = AuthorizationConfig(
            enabled=auth_enabled,
            strict_mode=auth_strict
        )
        
        # Behavior monitoring settings
        behavior_enabled = os.getenv("SAFETY_BEHAVIOR_ENABLED", "true").lower() == "true"
        behavior_monitoring = BehaviorMonitoringConfig(enabled=behavior_enabled)
        
        # Compliance settings
        compliance_enabled = os.getenv("SAFETY_COMPLIANCE_ENABLED", "true").lower() == "true"
        compliance = ComplianceConfig(enabled=compliance_enabled)
        
        return cls(
            mode=mode,
            enabled=enabled,
            log_safety_events=log_events,
            debug_mode=debug_mode,
            content_safety=content_safety,
            authorization=authorization,
            behavior_monitoring=behavior_monitoring,
            compliance=compliance
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to a dictionary.
        
        Returns:
            Dictionary representation of the configuration
        """
        result = {
            "mode": self.mode.value,
            "enabled": self.enabled,
            "log_safety_events": self.log_safety_events,
            "debug_mode": self.debug_mode,
            "content_safety": {
                "enabled": self.content_safety.enabled,
                "sensitivity_level": self.content_safety.sensitivity_level.value,
                "check_input": self.content_safety.check_input,
                "check_output": self.content_safety.check_output,
                "max_content_length": self.content_safety.max_content_length,
                "blocked_keywords": self.content_safety.blocked_keywords,
                "allowed_content_types": self.content_safety.allowed_content_types,
                "ml_filtering_enabled": self.content_safety.ml_filtering_enabled,
                "adaptive_learning_enabled": self.content_safety.adaptive_learning_enabled,
                "custom_rules": self.content_safety.custom_rules
            },
            "authorization": {
                "enabled": self.authorization.enabled,
                "strict_mode": self.authorization.strict_mode,
                "default_role": self.authorization.default_role,
                "admin_roles": self.authorization.admin_roles,
                "protected_paths": self.authorization.protected_paths,
                "public_paths": self.authorization.public_paths,
                "session_timeout": self.authorization.session_timeout,
                "token_refresh_enabled": self.authorization.token_refresh_enabled
            },
            "behavior_monitoring": {
                "enabled": self.behavior_monitoring.enabled,
                "track_requests": self.behavior_monitoring.track_requests,
                "track_responses": self.behavior_monitoring.track_responses,
                "track_errors": self.behavior_monitoring.track_errors,
                "anomaly_detection": self.behavior_monitoring.anomaly_detection,
                "baseline_learning": self.behavior_monitoring.baseline_learning,
                "risk_assessment": self.behavior_monitoring.risk_assessment,
                "max_events_per_session": self.behavior_monitoring.max_events_per_session,
                "event_retention_days": self.behavior_monitoring.event_retention_days,
                "alert_thresholds": self.behavior_monitoring.alert_thresholds
            },
            "compliance": {
                "enabled": self.compliance.enabled,
                "standards": self.compliance.standards,
                "audit_logging": self.compliance.audit_logging,
                "data_retention_days": self.compliance.data_retention_days,
                "report_generation_interval": self.compliance.report_generation_interval,
                "auto_escalation": self.compliance.auto_escalation,
                "violation_threshold": self.compliance.violation_threshold,
                "escalation_contacts": self.compliance.escalation_contacts
            },
            "blocked_response_template": self.blocked_response_template,
            "warn_response_template": self.warn_response_template,
            "max_processing_time": self.max_processing_time,
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl
        }
        
        return result
    
    def validate(self) -> List[str]:
        """
        Validate the configuration.
        
        Returns:
            List of validation error messages, empty if valid
        """
        errors = []
        
        # Validate general settings
        if self.max_processing_time <= 0:
            errors.append("max_processing_time must be greater than 0")
        
        if self.cache_ttl < 0:
            errors.append("cache_ttl must be non-negative")
        
        # Validate content safety settings
        if self.content_safety.max_content_length <= 0:
            errors.append("content_safety.max_content_length must be greater than 0")
        
        # Validate authorization settings
        if self.authorization.session_timeout <= 0:
            errors.append("authorization.session_timeout must be greater than 0")
        
        # Validate behavior monitoring settings
        if self.behavior_monitoring.max_events_per_session <= 0:
            errors.append("behavior_monitoring.max_events_per_session must be greater than 0")
        
        if self.behavior_monitoring.event_retention_days < 0:
            errors.append("behavior_monitoring.event_retention_days must be non-negative")
        
        # Validate compliance settings
        if self.compliance.data_retention_days < 0:
            errors.append("compliance.data_retention_days must be non-negative")
        
        if self.compliance.report_generation_interval <= 0:
            errors.append("compliance.report_generation_interval must be greater than 0")
        
        if self.compliance.violation_threshold < 0:
            errors.append("compliance.violation_threshold must be non-negative")
        
        return errors


def get_default_config() -> SafetyMiddlewareConfig:
    """
    Get the default safety middleware configuration.
    
    Returns:
        Default SafetyMiddlewareConfig instance
    """
    return SafetyMiddlewareConfig()


def get_config_from_file(config_path: str) -> Optional[SafetyMiddlewareConfig]:
    """
    Load safety middleware configuration from a file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        SafetyMiddlewareConfig instance if successful, None otherwise
    """
    try:
        import json
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Create configuration from data
        config = SafetyMiddlewareConfig()
        
        # Update configuration with loaded data
        if "mode" in config_data:
            try:
                config.mode = SafetyMiddlewareMode(config_data["mode"].lower())
            except ValueError:
                logger.warning(f"Invalid mode in config file: {config_data['mode']}")
        
        if "enabled" in config_data:
            config.enabled = config_data["enabled"]
        
        if "log_safety_events" in config_data:
            config.log_safety_events = config_data["log_safety_events"]
        
        if "debug_mode" in config_data:
            config.debug_mode = config_data["debug_mode"]
        
        # Validate configuration
        errors = config.validate()
        if errors:
            logger.error(f"Configuration validation errors: {errors}")
            return None
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to load configuration from {config_path}: {e}")
        return None