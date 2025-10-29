"""
Configuration validation and health checks for extension authentication.
Provides comprehensive validation, health monitoring, and diagnostic capabilities.

Requirements: 8.3, 8.4, 8.5
"""

import os
import json
import yaml
import logging
import asyncio
import aiohttp
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import socket
import ssl
import subprocess
import tempfile
from urllib.parse import urlparse

from .extension_environment_config import (
    ExtensionEnvironmentConfig,
    Environment,
    get_config_manager
)

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Validation issue severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(str, Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ValidationIssue:
    """Represents a configuration validation issue."""
    severity: ValidationSeverity
    category: str
    message: str
    field: Optional[str] = None
    recommendation: Optional[str] = None
    auto_fixable: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = None
    duration_ms: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.details is None:
            self.details = {}
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class ExtensionConfigValidator:
    """Validates extension configuration for security, performance, and correctness."""
    
    def __init__(self):
        self.validation_rules = []
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register default validation rules."""
        self.validation_rules.extend([
            self._validate_authentication_security,
            self._validate_rate_limiting,
            self._validate_token_settings,
            self._validate_environment_consistency,
            self._validate_permission_settings,
            self._validate_logging_settings,
            self._validate_health_check_settings,
            self._validate_production_security,
            self._validate_development_settings,
            self._validate_network_security,
        ])
    
    def validate_config(self, config: ExtensionEnvironmentConfig) -> List[ValidationIssue]:
        """Validate configuration and return list of issues."""
        issues = []
        
        try:
            for rule in self.validation_rules:
                try:
                    rule_issues = rule(config)
                    if rule_issues:
                        issues.extend(rule_issues)
                except Exception as e:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="validation_error",
                        message=f"Validation rule failed: {e}",
                        recommendation="Check validation rule implementation"
                    ))
            
            # Sort issues by severity
            severity_order = {
                ValidationSeverity.CRITICAL: 0,
                ValidationSeverity.ERROR: 1,
                ValidationSeverity.WARNING: 2,
                ValidationSeverity.INFO: 3
            }
            issues.sort(key=lambda x: severity_order.get(x.severity, 999))
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="validation_failure",
                message=f"Configuration validation failed: {e}"
            ))
        
        return issues
    
    def _validate_authentication_security(self, config: ExtensionEnvironmentConfig) -> List[ValidationIssue]:
        """Validate authentication security settings."""
        issues = []
        
        # Secret key validation
        if not config.secret_key:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="authentication",
                field="secret_key",
                message="Secret key is required for authentication",
                recommendation="Generate a secure secret key using secrets.token_urlsafe(32)"
            ))
        elif len(config.secret_key) < 32:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="authentication",
                field="secret_key",
                message="Secret key is too short (minimum 32 characters)",
                recommendation="Use a longer, more secure secret key"
            ))
        elif config.secret_key in ["dev-extension-secret-key-change-in-production", "change-me", "secret"]:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="authentication",
                field="secret_key",
                message="Using default or weak secret key",
                recommendation="Generate a unique, secure secret key for this environment"
            ))
        
        # API key validation
        if not config.api_key:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="authentication",
                field="api_key",
                message="API key is required",
                recommendation="Generate a secure API key"
            ))
        elif config.api_key in ["dev-extension-api-key-change-in-production", "change-me", "api-key"]:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="authentication",
                field="api_key",
                message="Using default or weak API key",
                recommendation="Generate a unique, secure API key for this environment"
            ))
        
        # JWT algorithm validation
        secure_algorithms = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
        if config.jwt_algorithm not in secure_algorithms:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="authentication",
                field="jwt_algorithm",
                message=f"Unsupported JWT algorithm: {config.jwt_algorithm}",
                recommendation=f"Use one of: {', '.join(secure_algorithms)}"
            ))
        
        return issues
    
    def _validate_rate_limiting(self, config: ExtensionEnvironmentConfig) -> List[ValidationIssue]:
        """Validate rate limiting settings."""
        issues = []
        
        if not config.enable_rate_limiting:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="rate_limiting",
                field="enable_rate_limiting",
                message="Rate limiting is disabled",
                recommendation="Enable rate limiting to prevent abuse"
            ))
        
        if config.rate_limit_per_minute <= 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="rate_limiting",
                field="rate_limit_per_minute",
                message="Rate limit must be positive",
                recommendation="Set a reasonable rate limit (e.g., 100 requests per minute)"
            ))
        elif config.rate_limit_per_minute > 10000:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="rate_limiting",
                field="rate_limit_per_minute",
                message="Rate limit is very high",
                recommendation="Consider lowering the rate limit for better protection"
            ))
        
        if config.burst_limit <= 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="rate_limiting",
                field="burst_limit",
                message="Burst limit must be positive",
                recommendation="Set a reasonable burst limit (e.g., 20 requests)"
            ))
        elif config.burst_limit > config.rate_limit_per_minute:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="rate_limiting",
                field="burst_limit",
                message="Burst limit is higher than rate limit",
                recommendation="Burst limit should be lower than or equal to rate limit"
            ))
        
        return issues
    
    def _validate_token_settings(self, config: ExtensionEnvironmentConfig) -> List[ValidationIssue]:
        """Validate token expiration settings."""
        issues = []
        
        if config.access_token_expire_minutes <= 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="tokens",
                field="access_token_expire_minutes",
                message="Access token expiration must be positive",
                recommendation="Set a reasonable expiration time (e.g., 60 minutes)"
            ))
        elif config.access_token_expire_minutes > 1440:  # 24 hours
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="tokens",
                field="access_token_expire_minutes",
                message="Access token expiration is very long",
                recommendation="Consider shorter expiration for better security"
            ))
        
        if config.service_token_expire_minutes <= 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="tokens",
                field="service_token_expire_minutes",
                message="Service token expiration must be positive",
                recommendation="Set a reasonable expiration time (e.g., 30 minutes)"
            ))
        elif config.service_token_expire_minutes > config.access_token_expire_minutes:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="tokens",
                field="service_token_expire_minutes",
                message="Service token expiration is longer than access token",
                recommendation="Service tokens should expire sooner than access tokens"
            ))
        
        return issues
    
    def _validate_environment_consistency(self, config: ExtensionEnvironmentConfig) -> List[ValidationIssue]:
        """Validate environment-specific consistency."""
        issues = []
        
        env = config.environment
        
        # Check auth mode consistency
        if env == Environment.PRODUCTION and config.auth_mode == "development":
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="environment",
                field="auth_mode",
                message="Development auth mode in production environment",
                recommendation="Use 'strict' auth mode in production"
            ))
        
        if env == Environment.DEVELOPMENT and config.auth_mode == "strict":
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category="environment",
                field="auth_mode",
                message="Strict auth mode in development environment",
                recommendation="Consider using 'development' or 'hybrid' mode for easier development"
            ))
        
        # Check HTTPS requirements
        if env == Environment.PRODUCTION and not config.require_https:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="environment",
                field="require_https",
                message="HTTPS not required in production",
                recommendation="Enable HTTPS requirement in production"
            ))
        
        # Check development bypass
        if env == Environment.PRODUCTION and config.dev_bypass_enabled:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="environment",
                field="dev_bypass_enabled",
                message="Development bypass enabled in production",
                recommendation="Disable development bypass in production"
            ))
        
        return issues
    
    def _validate_permission_settings(self, config: ExtensionEnvironmentConfig) -> List[ValidationIssue]:
        """Validate permission configuration."""
        issues = []
        
        if not config.default_permissions:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="permissions",
                field="default_permissions",
                message="No default permissions configured",
                recommendation="Configure appropriate default permissions"
            ))
        
        if not config.admin_permissions:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="permissions",
                field="admin_permissions",
                message="No admin permissions configured",
                recommendation="Configure admin permissions"
            ))
        
        if not config.service_permissions:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="permissions",
                field="service_permissions",
                message="No service permissions configured",
                recommendation="Configure service-to-service permissions"
            ))
        
        # Check for overly permissive settings
        if config.default_permissions and "*" in config.default_permissions:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="permissions",
                field="default_permissions",
                message="Default permissions include wildcard (*)",
                recommendation="Use specific permissions instead of wildcards"
            ))
        
        return issues
    
    def _validate_logging_settings(self, config: ExtensionEnvironmentConfig) -> List[ValidationIssue]:
        """Validate logging configuration."""
        issues = []
        
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if config.log_level not in valid_log_levels:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="logging",
                field="log_level",
                message=f"Invalid log level: {config.log_level}",
                recommendation=f"Use one of: {', '.join(valid_log_levels)}"
            ))
        
        if config.environment == Environment.PRODUCTION and config.log_sensitive_data:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="logging",
                field="log_sensitive_data",
                message="Sensitive data logging enabled in production",
                recommendation="Disable sensitive data logging in production"
            ))
        
        if config.environment == Environment.PRODUCTION and config.enable_debug_logging:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="logging",
                field="enable_debug_logging",
                message="Debug logging enabled in production",
                recommendation="Disable debug logging in production for performance"
            ))
        
        return issues
    
    def _validate_health_check_settings(self, config: ExtensionEnvironmentConfig) -> List[ValidationIssue]:
        """Validate health check configuration."""
        issues = []
        
        if not config.health_check_enabled:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="health_checks",
                field="health_check_enabled",
                message="Health checks are disabled",
                recommendation="Enable health checks for better monitoring"
            ))
        
        if config.health_check_interval_seconds <= 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="health_checks",
                field="health_check_interval_seconds",
                message="Health check interval must be positive",
                recommendation="Set a reasonable interval (e.g., 30 seconds)"
            ))
        elif config.health_check_interval_seconds < 10:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="health_checks",
                field="health_check_interval_seconds",
                message="Health check interval is very short",
                recommendation="Consider a longer interval to reduce overhead"
            ))
        
        if config.health_check_timeout_seconds <= 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="health_checks",
                field="health_check_timeout_seconds",
                message="Health check timeout must be positive",
                recommendation="Set a reasonable timeout (e.g., 5 seconds)"
            ))
        elif config.health_check_timeout_seconds >= config.health_check_interval_seconds:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="health_checks",
                field="health_check_timeout_seconds",
                message="Health check timeout is too long relative to interval",
                recommendation="Timeout should be shorter than interval"
            ))
        
        return issues
    
    def _validate_production_security(self, config: ExtensionEnvironmentConfig) -> List[ValidationIssue]:
        """Validate production-specific security settings."""
        issues = []
        
        if config.environment != Environment.PRODUCTION:
            return issues
        
        # Security lockdown checks
        if config.max_failed_attempts > 5:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="security",
                field="max_failed_attempts",
                message="Max failed attempts is high for production",
                recommendation="Use a lower value (3-5) in production"
            ))
        
        if config.lockout_duration_minutes < 15:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="security",
                field="lockout_duration_minutes",
                message="Lockout duration is short for production",
                recommendation="Use a longer lockout duration (15+ minutes) in production"
            ))
        
        if not config.token_blacklist_enabled:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="security",
                field="token_blacklist_enabled",
                message="Token blacklist is disabled in production",
                recommendation="Enable token blacklist for better security"
            ))
        
        if not config.audit_logging_enabled:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="security",
                field="audit_logging_enabled",
                message="Audit logging is disabled in production",
                recommendation="Enable audit logging for compliance and security"
            ))
        
        return issues
    
    def _validate_development_settings(self, config: ExtensionEnvironmentConfig) -> List[ValidationIssue]:
        """Validate development-specific settings."""
        issues = []
        
        if config.environment != Environment.DEVELOPMENT:
            return issues
        
        # Development convenience checks
        if not config.enable_debug_logging:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category="development",
                field="enable_debug_logging",
                message="Debug logging is disabled in development",
                recommendation="Enable debug logging for easier development"
            ))
        
        if config.rate_limit_per_minute < 100:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category="development",
                field="rate_limit_per_minute",
                message="Rate limit is low for development",
                recommendation="Consider higher rate limits for development convenience"
            ))
        
        return issues
    
    def _validate_network_security(self, config: ExtensionEnvironmentConfig) -> List[ValidationIssue]:
        """Validate network security settings."""
        issues = []
        
        # HTTPS validation
        if config.environment in [Environment.PRODUCTION, Environment.STAGING] and not config.require_https:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="network_security",
                field="require_https",
                message="HTTPS not required in production/staging environment",
                recommendation="Enable HTTPS requirement for secure communication"
            ))
        
        return issues


class ExtensionConfigHealthChecker:
    """Performs health checks on extension configuration and related services."""
    
    def __init__(self):
        self.health_checks = [
            self._check_config_validity,
            self._check_credential_health,
            self._check_file_permissions,
            self._check_network_connectivity,
            self._check_database_connectivity,
            self._check_redis_connectivity,
            self._check_disk_space,
            self._check_memory_usage,
            self._check_certificate_validity,
            self._check_service_dependencies,
        ]
    
    async def run_all_health_checks(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status."""
        start_time = datetime.utcnow()
        results = []
        overall_status = HealthStatus.HEALTHY
        
        try:
            for check in self.health_checks:
                try:
                    check_start = datetime.utcnow()
                    result = await check()
                    check_duration = (datetime.utcnow() - check_start).total_seconds() * 1000
                    result.duration_ms = check_duration
                    results.append(result)
                    
                    # Update overall status
                    if result.status == HealthStatus.UNHEALTHY:
                        overall_status = HealthStatus.UNHEALTHY
                    elif result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.DEGRADED
                        
                except Exception as e:
                    logger.error(f"Health check failed: {e}")
                    results.append(HealthCheckResult(
                        name=check.__name__,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Health check failed: {e}"
                    ))
                    overall_status = HealthStatus.UNHEALTHY
            
            total_duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                'overall_status': overall_status.value,
                'total_duration_ms': total_duration,
                'checks_count': len(results),
                'healthy_count': len([r for r in results if r.status == HealthStatus.HEALTHY]),
                'degraded_count': len([r for r in results if r.status == HealthStatus.DEGRADED]),
                'unhealthy_count': len([r for r in results if r.status == HealthStatus.UNHEALTHY]),
                'timestamp': start_time.isoformat(),
                'results': [r.to_dict() for r in results]
            }
            
        except Exception as e:
            logger.error(f"Health check suite failed: {e}")
            return {
                'overall_status': HealthStatus.UNHEALTHY.value,
                'error': str(e),
                'timestamp': start_time.isoformat(),
                'results': [r.to_dict() for r in results]
            }
    
    async def _check_config_validity(self) -> HealthCheckResult:
        """Check if current configuration is valid."""
        try:
            config_manager = get_config_manager()
            current_config = config_manager.get_current_config()
            
            validator = ExtensionConfigValidator()
            issues = validator.validate_config(current_config)
            
            critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
            error_issues = [i for i in issues if i.severity == ValidationSeverity.ERROR]
            
            if critical_issues:
                return HealthCheckResult(
                    name="config_validity",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Configuration has {len(critical_issues)} critical issues",
                    details={
                        'critical_issues': len(critical_issues),
                        'error_issues': len(error_issues),
                        'total_issues': len(issues),
                        'environment': current_config.environment.value
                    }
                )
            elif error_issues:
                return HealthCheckResult(
                    name="config_validity",
                    status=HealthStatus.DEGRADED,
                    message=f"Configuration has {len(error_issues)} error issues",
                    details={
                        'error_issues': len(error_issues),
                        'total_issues': len(issues),
                        'environment': current_config.environment.value
                    }
                )
            else:
                return HealthCheckResult(
                    name="config_validity",
                    status=HealthStatus.HEALTHY,
                    message="Configuration is valid",
                    details={
                        'total_issues': len(issues),
                        'environment': current_config.environment.value
                    }
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="config_validity",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to validate configuration: {e}"
            )
    
    async def _check_credential_health(self) -> HealthCheckResult:
        """Check credential storage and expiration status."""
        try:
            config_manager = get_config_manager()
            credentials_list = config_manager.credentials_manager.list_credentials()
            
            expired_credentials = [c for c in credentials_list if c.get('expired')]
            expiring_soon = []
            
            # Check for credentials expiring within 7 days
            for cred in credentials_list:
                if cred.get('expires_at'):
                    expires_at = datetime.fromisoformat(cred['expires_at'])
                    days_until_expiry = (expires_at - datetime.utcnow()).days
                    if 0 < days_until_expiry <= 7:
                        expiring_soon.append(cred)
            
            if expired_credentials:
                return HealthCheckResult(
                    name="credential_health",
                    status=HealthStatus.UNHEALTHY,
                    message=f"{len(expired_credentials)} credentials have expired",
                    details={
                        'total_credentials': len(credentials_list),
                        'expired_count': len(expired_credentials),
                        'expiring_soon_count': len(expiring_soon),
                        'expired_credentials': [c['name'] for c in expired_credentials]
                    }
                )
            elif expiring_soon:
                return HealthCheckResult(
                    name="credential_health",
                    status=HealthStatus.DEGRADED,
                    message=f"{len(expiring_soon)} credentials expire within 7 days",
                    details={
                        'total_credentials': len(credentials_list),
                        'expiring_soon_count': len(expiring_soon),
                        'expiring_credentials': [c['name'] for c in expiring_soon]
                    }
                )
            else:
                return HealthCheckResult(
                    name="credential_health",
                    status=HealthStatus.HEALTHY,
                    message="All credentials are healthy",
                    details={
                        'total_credentials': len(credentials_list)
                    }
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="credential_health",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check credential health: {e}"
            )
    
    async def _check_file_permissions(self) -> HealthCheckResult:
        """Check file system permissions for configuration files."""
        try:
            config_manager = get_config_manager()
            config_dir = config_manager.config_dir
            credentials_dir = config_manager.credentials_manager.storage_path
            
            issues = []
            
            # Check config directory permissions
            if not os.access(config_dir, os.R_OK):
                issues.append(f"Cannot read config directory: {config_dir}")
            if not os.access(config_dir, os.W_OK):
                issues.append(f"Cannot write to config directory: {config_dir}")
            
            # Check credentials directory permissions
            if not os.access(credentials_dir, os.R_OK):
                issues.append(f"Cannot read credentials directory: {credentials_dir}")
            if not os.access(credentials_dir, os.W_OK):
                issues.append(f"Cannot write to credentials directory: {credentials_dir}")
            
            # Check specific files
            credentials_file = credentials_dir / "credentials.enc"
            if credentials_file.exists():
                if not os.access(credentials_file, os.R_OK):
                    issues.append(f"Cannot read credentials file: {credentials_file}")
                if not os.access(credentials_file, os.W_OK):
                    issues.append(f"Cannot write to credentials file: {credentials_file}")
                
                # Check file permissions (should be restrictive)
                stat_info = credentials_file.stat()
                permissions = oct(stat_info.st_mode)[-3:]
                if permissions != '600':
                    issues.append(f"Credentials file has insecure permissions: {permissions} (should be 600)")
            
            if issues:
                return HealthCheckResult(
                    name="file_permissions",
                    status=HealthStatus.UNHEALTHY,
                    message=f"File permission issues found: {len(issues)}",
                    details={'issues': issues}
                )
            else:
                return HealthCheckResult(
                    name="file_permissions",
                    status=HealthStatus.HEALTHY,
                    message="File permissions are correct"
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="file_permissions",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check file permissions: {e}"
            )
    
    async def _check_network_connectivity(self) -> HealthCheckResult:
        """Check network connectivity for external dependencies."""
        try:
            # Test basic internet connectivity
            test_hosts = [
                ("8.8.8.8", 53),  # Google DNS
                ("1.1.1.1", 53),  # Cloudflare DNS
            ]
            
            connectivity_issues = []
            
            for host, port in test_hosts:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    
                    if result != 0:
                        connectivity_issues.append(f"Cannot connect to {host}:{port}")
                except Exception as e:
                    connectivity_issues.append(f"Network test failed for {host}:{port}: {e}")
            
            if connectivity_issues:
                return HealthCheckResult(
                    name="network_connectivity",
                    status=HealthStatus.DEGRADED,
                    message=f"Network connectivity issues: {len(connectivity_issues)}",
                    details={'issues': connectivity_issues}
                )
            else:
                return HealthCheckResult(
                    name="network_connectivity",
                    status=HealthStatus.HEALTHY,
                    message="Network connectivity is good"
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="network_connectivity",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check network connectivity: {e}"
            )
    
    async def _check_database_connectivity(self) -> HealthCheckResult:
        """Check database connectivity."""
        try:
            # This would typically test the actual database connection
            # For now, we'll check if the database URL is configured
            database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
            
            if not database_url:
                return HealthCheckResult(
                    name="database_connectivity",
                    status=HealthStatus.UNHEALTHY,
                    message="Database URL not configured"
                )
            
            # Parse database URL to check format
            try:
                parsed = urlparse(database_url)
                if not parsed.scheme or not parsed.hostname:
                    return HealthCheckResult(
                        name="database_connectivity",
                        status=HealthStatus.UNHEALTHY,
                        message="Invalid database URL format"
                    )
            except Exception as e:
                return HealthCheckResult(
                    name="database_connectivity",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Failed to parse database URL: {e}"
                )
            
            # TODO: Add actual database connection test
            return HealthCheckResult(
                name="database_connectivity",
                status=HealthStatus.HEALTHY,
                message="Database configuration appears valid",
                details={'url_configured': True}
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="database_connectivity",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check database connectivity: {e}"
            )
    
    async def _check_redis_connectivity(self) -> HealthCheckResult:
        """Check Redis connectivity."""
        try:
            redis_url = os.getenv("REDIS_URL")
            
            if not redis_url:
                return HealthCheckResult(
                    name="redis_connectivity",
                    status=HealthStatus.DEGRADED,
                    message="Redis URL not configured (optional)"
                )
            
            # Parse Redis URL
            try:
                parsed = urlparse(redis_url)
                if not parsed.scheme or not parsed.hostname:
                    return HealthCheckResult(
                        name="redis_connectivity",
                        status=HealthStatus.UNHEALTHY,
                        message="Invalid Redis URL format"
                    )
            except Exception as e:
                return HealthCheckResult(
                    name="redis_connectivity",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Failed to parse Redis URL: {e}"
                )
            
            # TODO: Add actual Redis connection test
            return HealthCheckResult(
                name="redis_connectivity",
                status=HealthStatus.HEALTHY,
                message="Redis configuration appears valid",
                details={'url_configured': True}
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="redis_connectivity",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check Redis connectivity: {e}"
            )
    
    async def _check_disk_space(self) -> HealthCheckResult:
        """Check available disk space."""
        try:
            config_manager = get_config_manager()
            config_dir = config_manager.config_dir
            
            # Get disk usage for config directory
            disk_usage = psutil.disk_usage(str(config_dir))
            free_space_gb = disk_usage.free / (1024**3)
            total_space_gb = disk_usage.total / (1024**3)
            used_percent = (disk_usage.used / disk_usage.total) * 100
            
            if free_space_gb < 0.1:  # Less than 100MB
                return HealthCheckResult(
                    name="disk_space",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Very low disk space: {free_space_gb:.2f}GB free",
                    details={
                        'free_space_gb': round(free_space_gb, 2),
                        'total_space_gb': round(total_space_gb, 2),
                        'used_percent': round(used_percent, 1)
                    }
                )
            elif used_percent > 90:
                return HealthCheckResult(
                    name="disk_space",
                    status=HealthStatus.DEGRADED,
                    message=f"High disk usage: {used_percent:.1f}% used",
                    details={
                        'free_space_gb': round(free_space_gb, 2),
                        'total_space_gb': round(total_space_gb, 2),
                        'used_percent': round(used_percent, 1)
                    }
                )
            else:
                return HealthCheckResult(
                    name="disk_space",
                    status=HealthStatus.HEALTHY,
                    message=f"Disk space is adequate: {free_space_gb:.2f}GB free",
                    details={
                        'free_space_gb': round(free_space_gb, 2),
                        'total_space_gb': round(total_space_gb, 2),
                        'used_percent': round(used_percent, 1)
                    }
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check disk space: {e}"
            )
    
    async def _check_memory_usage(self) -> HealthCheckResult:
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            available_gb = memory.available / (1024**3)
            
            if memory_percent > 95:
                return HealthCheckResult(
                    name="memory_usage",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Very high memory usage: {memory_percent:.1f}%",
                    details={
                        'memory_percent': round(memory_percent, 1),
                        'available_gb': round(available_gb, 2)
                    }
                )
            elif memory_percent > 85:
                return HealthCheckResult(
                    name="memory_usage",
                    status=HealthStatus.DEGRADED,
                    message=f"High memory usage: {memory_percent:.1f}%",
                    details={
                        'memory_percent': round(memory_percent, 1),
                        'available_gb': round(available_gb, 2)
                    }
                )
            else:
                return HealthCheckResult(
                    name="memory_usage",
                    status=HealthStatus.HEALTHY,
                    message=f"Memory usage is normal: {memory_percent:.1f}%",
                    details={
                        'memory_percent': round(memory_percent, 1),
                        'available_gb': round(available_gb, 2)
                    }
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="memory_usage",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check memory usage: {e}"
            )
    
    async def _check_certificate_validity(self) -> HealthCheckResult:
        """Check SSL certificate validity if HTTPS is required."""
        try:
            config_manager = get_config_manager()
            current_config = config_manager.get_current_config()
            
            if not current_config.require_https:
                return HealthCheckResult(
                    name="certificate_validity",
                    status=HealthStatus.HEALTHY,
                    message="HTTPS not required, certificate check skipped"
                )
            
            # Check for certificate files
            cert_paths = [
                "/app/certs/tls.crt",
                "/etc/ssl/certs/server.crt",
                "certs/server.crt",
                "server.crt"
            ]
            
            cert_file = None
            for path in cert_paths:
                if os.path.exists(path):
                    cert_file = path
                    break
            
            if not cert_file:
                return HealthCheckResult(
                    name="certificate_validity",
                    status=HealthStatus.DEGRADED,
                    message="HTTPS required but no certificate file found",
                    details={'searched_paths': cert_paths}
                )
            
            # TODO: Add actual certificate validation
            return HealthCheckResult(
                name="certificate_validity",
                status=HealthStatus.HEALTHY,
                message=f"Certificate file found: {cert_file}",
                details={'certificate_path': cert_file}
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="certificate_validity",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check certificate validity: {e}"
            )
    
    async def _check_service_dependencies(self) -> HealthCheckResult:
        """Check if required services are running."""
        try:
            # Check for common service processes
            required_services = []
            optional_services = ["redis-server", "postgresql", "nginx"]
            
            running_services = []
            missing_services = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info['name'].lower()
                    cmdline = ' '.join(proc.info['cmdline'] or []).lower()
                    
                    for service in optional_services:
                        if service in proc_name or service in cmdline:
                            running_services.append(service)
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Check for missing required services
            for service in required_services:
                if service not in running_services:
                    missing_services.append(service)
            
            if missing_services:
                return HealthCheckResult(
                    name="service_dependencies",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Missing required services: {', '.join(missing_services)}",
                    details={
                        'running_services': running_services,
                        'missing_services': missing_services
                    }
                )
            else:
                return HealthCheckResult(
                    name="service_dependencies",
                    status=HealthStatus.HEALTHY,
                    message="Service dependencies are satisfied",
                    details={'running_services': running_services}
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="service_dependencies",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check service dependencies: {e}"
            )


async def validate_extension_config() -> Dict[str, Any]:
    """Validate the current extension configuration."""
    try:
        config_manager = get_config_manager()
        current_config = config_manager.get_current_config()
        
        validator = ExtensionConfigValidator()
        issues = validator.validate_config(current_config)
        
        return {
            'valid': len([i for i in issues if i.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]]) == 0,
            'environment': current_config.environment.value,
            'total_issues': len(issues),
            'critical_issues': len([i for i in issues if i.severity == ValidationSeverity.CRITICAL]),
            'error_issues': len([i for i in issues if i.severity == ValidationSeverity.ERROR]),
            'warning_issues': len([i for i in issues if i.severity == ValidationSeverity.WARNING]),
            'info_issues': len([i for i in issues if i.severity == ValidationSeverity.INFO]),
            'issues': [issue.to_dict() for issue in issues],
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return {
            'valid': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


async def run_extension_health_checks() -> Dict[str, Any]:
    """Run comprehensive health checks for extension configuration."""
    try:
        health_checker = ExtensionConfigHealthChecker()
        return await health_checker.run_all_health_checks()
    except Exception as e:
        logger.error(f"Health checks failed: {e}")
        return {
            'overall_status': HealthStatus.UNHEALTHY.value,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }