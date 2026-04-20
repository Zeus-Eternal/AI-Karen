"""
Enhanced Security Manager for Service Registry

Provides comprehensive security features including authentication, authorization,
network security, and data protection for service registry operations.
"""

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from pathlib import Path
import json
import threading
from contextlib import asynccontextmanager

try:
    import jwt
    from cryptography.fernet import Fernet
    from pydantic import BaseModel, validator
    from pydantic.types import SecretStr

    SECURITY_DEPS_AVAILABLE = True
except ImportError:
    SECURITY_DEPS_AVAILABLE = False
    jwt = None
    Fernet = None
    BaseModel = None
    SecretStr = None


logger = logging.getLogger(__name__)


class AccessLevel(Enum):
    """Access levels for service registry operations"""

    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"
    SYSTEM = "system"


class ProviderSecurityStatus(Enum):
    """Security status for providers"""

    SECURE = "secure"
    AUTH_REQUIRED = "auth_required"
    COMPROMISED = "compromised"
    QUARANTINED = "quarantined"
    MONITORING = "monitoring"


@dataclass
class SecurityPolicy:
    """Security policy configuration"""

    max_login_attempts: int = 5
    account_lockout_duration: int = 300  # seconds
    session_timeout: int = 3600  # seconds
    api_key_rotation_interval: int = 86400  # 24 hours
    rate_limit_requests_per_minute: int = 100
    allowed_origins: Set[str] = field(default_factory=lambda: {"*"})
    require_tls: bool = True
    enable_audit_logging: bool = True
    encryption_enabled: bool = True
    data_classification_levels: List[str] = field(
        default_factory=lambda: ["public", "internal", "confidential"]
    )


@dataclass
class ProviderSecurityConfig:
    """Security configuration for individual providers"""

    provider_name: str
    access_level: AccessLevel = AccessLevel.READ_ONLY
    api_key_required: bool = False
    tls_required: bool = True
    allowed_ips: Optional[Set[str]] = None
    rate_limit_per_minute: int = 60
    max_concurrent_requests: int = 10
    audit_enabled: bool = True
    data_classification: str = "internal"
    encryption_at_rest: bool = True
    backup_required: bool = True


@dataclass
class SecurityEvent:
    """Security event for audit logging"""

    timestamp: datetime
    event_type: str
    severity: str  # info, warning, error, critical
    actor: str
    action: str
    resource: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True


class ProviderSecurityManager:
    """Enhanced security manager for service registry providers"""

    def __init__(self, security_policy: Optional[SecurityPolicy] = None):
        self.security_policy = security_policy or SecurityPolicy()
        self._provider_configs: Dict[str, ProviderSecurityConfig] = {}
        self._security_events: List[SecurityEvent] = []
        self._access_tokens: Dict[str, Dict[str, Any]] = {}
        self._api_keys: Dict[str, Dict[str, Any]] = {}
        self._failed_attempts: Dict[str, int] = {}
        self._locked_accounts: Dict[str, float] = {}
        self._encryption_key = (
            self._generate_encryption_key()
            if self.security_policy.encryption_enabled
            else None
        )
        self._fernet = (
            Fernet(self._encryption_key)
            if self.security_policy.encryption_enabled and Fernet
            else None
        )

        # Thread safety
        self._lock = threading.RLock()
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None

        # Initialize with default provider configurations
        self._initialize_default_configs()

    def _initialize_default_configs(self):
        """Initialize default security configurations for built-in providers"""
        default_configs = {
            "llamacpp": ProviderSecurityConfig(
                provider_name="llamacpp",
                access_level=AccessLevel.READ_WRITE,
                api_key_required=False,
                tls_required=False,
                rate_limit_per_minute=1000,
                data_classification="internal",
            ),
            "ollama": ProviderSecurityConfig(
                provider_name="ollama",
                access_level=AccessLevel.READ_WRITE,
                api_key_required=False,
                tls_required=False,
                rate_limit_per_minute=500,
                data_classification="internal",
            ),
            "openai": ProviderSecurityConfig(
                provider_name="openai",
                access_level=AccessLevel.READ_WRITE,
                api_key_required=True,
                tls_required=True,
                rate_limit_per_minute=60,
                data_classification="confidential",
            ),
            "anthropic": ProviderSecurityConfig(
                provider_name="anthropic",
                access_level=AccessLevel.READ_WRITE,
                api_key_required=True,
                tls_required=True,
                rate_limit_per_minute=30,
                data_classification="confidential",
            ),
            "gemini": ProviderSecurityConfig(
                provider_name="gemini",
                access_level=AccessLevel.READ_WRITE,
                api_key_required=True,
                tls_required=True,
                rate_limit_per_minute=40,
                data_classification="confidential",
            ),
            "fallback": ProviderSecurityConfig(
                provider_name="fallback",
                access_level=AccessLevel.READ_ONLY,
                api_key_required=False,
                tls_required=False,
                rate_limit_per_minute=200,
                data_classification="public",
            ),
        }

        for provider_name, config in default_configs.items():
            self._provider_configs[provider_name] = config

    def _generate_encryption_key(self) -> Optional[bytes]:
        """Generate encryption key for data protection"""
        if not self.security_policy.encryption_enabled:
            return None

        try:
            # Try to load existing key from file
            key_file = Path.home() / ".kari" / "security" / "encryption.key"
            if key_file.exists():
                return key_file.read_bytes()

            # Generate new key
            key = Fernet.generate_key()
            key_file.parent.mkdir(parents=True, exist_ok=True)
            key_file.write_bytes(key)
            return key
        except Exception as e:
            logger.error(f"Failed to generate encryption key: {e}")
            return None

    def encrypt_data(self, data: str) -> Optional[str]:
        """Encrypt sensitive data"""
        if not self._fernet:
            return None

        try:
            return self._fernet.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            return None

    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt sensitive data"""
        if not self._fernet:
            return None

        try:
            return self._fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            return None

    def set_provider_security_config(
        self, provider_name: str, config: ProviderSecurityConfig
    ):
        """Set security configuration for a provider"""
        with self._lock:
            self._provider_configs[provider_name] = config
            self._log_security_event(
                event_type="CONFIG_UPDATE",
                severity="info",
                actor="system",
                action="set_provider_security_config",
                resource=f"provider:{provider_name}",
                details={"config": config.__dict__},
            )

    def get_provider_security_config(
        self, provider_name: str
    ) -> Optional[ProviderSecurityConfig]:
        """Get security configuration for a provider"""
        with self._lock:
            return self._provider_configs.get(provider_name)

    def validate_provider_access(
        self,
        provider_name: str,
        access_level: AccessLevel,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Validate if user has required access level for provider"""
        provider_config = self.get_provider_security_config(provider_name)
        if not provider_config:
            self._log_security_event(
                event_type="ACCESS_DENIED",
                severity="warning",
                actor=user_context.get("user_id", "unknown")
                if user_context
                else "unknown",
                action="validate_provider_access",
                resource=f"provider:{provider_name}",
                details={"reason": "Provider not found in security config"},
            )
            return False

        # Check if access level is sufficient
        if (
            access_level.value not in ["read_only"]
            and provider_config.access_level == AccessLevel.READ_ONLY
        ):
            self._log_security_event(
                event_type="ACCESS_DENIED",
                severity="warning",
                actor=user_context.get("user_id", "unknown")
                if user_context
                else "unknown",
                action="validate_provider_access",
                resource=f"provider:{provider_name}",
                details={
                    "required": access_level.value,
                    "provider_level": provider_config.access_level.value,
                },
            )
            return False

        # Check API key requirement
        if provider_config.api_key_required:
            if not user_context or "api_key" not in user_context:
                self._log_security_event(
                    event_type="ACCESS_DENIED",
                    severity="warning",
                    actor=user_context.get("user_id", "unknown")
                    if user_context
                    else "unknown",
                    action="validate_provider_access",
                    resource=f"provider:{provider_name}",
                    details={"reason": "API key required but not provided"},
                )
                return False

            if not self._validate_api_key(provider_name, user_context["api_key"]):
                self._log_security_event(
                    event_type="ACCESS_DENIED",
                    severity="warning",
                    actor=user_context.get("user_id", "unknown")
                    if user_context
                    else "unknown",
                    action="validate_provider_access",
                    resource=f"provider:{provider_name}",
                    details={"reason": "Invalid API key"},
                )
                return False

        # Check IP restrictions
        if (
            provider_config.allowed_ips
            and user_context
            and "ip_address" in user_context
        ):
            if user_context["ip_address"] not in provider_config.allowed_ips:
                self._log_security_event(
                    event_type="ACCESS_DENIED",
                    severity="warning",
                    actor=user_context.get("user_id", "unknown")
                    if user_context
                    else "unknown",
                    action="validate_provider_access",
                    resource=f"provider:{provider_name}",
                    details={
                        "reason": "IP not allowed",
                        "ip": user_context["ip_address"],
                    },
                )
                return False

        return True

    def _validate_api_key(self, provider_name: str, api_key: str) -> bool:
        """Validate API key for provider"""
        with self._lock:
            provider_keys = self._api_keys.get(provider_name, {})
            for key_info in provider_keys.values():
                if key_info["key"] == api_key and key_info.get("active", True):
                    return True
            return False

    def generate_api_key(
        self, provider_name: str, user_id: str, expires_in: Optional[int] = None
    ) -> Optional[str]:
        """Generate new API key for provider"""
        if not self.get_provider_security_config(provider_name):
            return None

        api_key = f"kari_api_{hashlib.sha256(f'{provider_name}_{user_id}_{time.time()}'.encode()).hexdigest()}"

        key_info = {
            "key": api_key,
            "provider": provider_name,
            "user_id": user_id,
            "created_at": time.time(),
            "expires_at": time.time()
            + (expires_in or self.security_policy.api_key_rotation_interval),
            "last_used": None,
        }

        with self._lock:
            if provider_name not in self._api_keys:
                self._api_keys[provider_name] = {}
            self._api_keys[provider_name][api_key] = key_info

        self._log_security_event(
            event_type="API_KEY_CREATED",
            severity="info",
            actor=user_id,
            action="generate_api_key",
            resource=f"provider:{provider_name}",
            details={"api_key_id": api_key[:8] + "...", "expires_in": expires_in},
        )

        return api_key

    def revoke_api_key(self, provider_name: str, api_key: str, revoked_by: str) -> bool:
        """Revoke API key"""
        with self._lock:
            if (
                provider_name in self._api_keys
                and api_key in self._api_keys[provider_name]
            ):
                del self._api_keys[provider_name][api_key]
                self._log_security_event(
                    event_type="API_KEY_REVOKED",
                    severity="info",
                    actor=revoked_by,
                    action="revoke_api_key",
                    resource=f"provider:{provider_name}",
                    details={"api_key_id": api_key[:8] + "..."},
                )
                return True
            return False

    def _log_security_event(
        self,
        event_type: str,
        severity: str,
        actor: str,
        action: str,
        resource: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        success: bool = True,
    ):
        """Log security event for audit trail"""
        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            actor=actor,
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address,
            success=success,
        )

        with self._lock:
            self._security_events.append(event)

            # Keep only last 10000 events
            if len(self._security_events) > 10000:
                self._security_events = self._security_events[-10000:]

        # Log to external system if enabled
        if self.security_policy.enable_audit_logging:
            logger.info(
                f"Security Event: {event_type} - {severity} - {actor} - {action}"
            )

    def get_security_events(
        self,
        limit: int = 100,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        actor: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get security events with filtering"""
        with self._lock:
            events = self._security_events.copy()

        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if severity:
            events = [e for e in events if e.severity == severity]
        if actor:
            events = [e for e in events if e.actor == actor]

        # Convert to dict format and limit
        result = [event.__dict__ for event in events[-limit:]]
        return result

    def get_provider_security_status(self, provider_name: str) -> Dict[str, Any]:
        """Get comprehensive security status for provider"""
        config = self.get_provider_security_config(provider_name)
        if not config:
            return {"status": "not_found"}

        # Count recent security events
        recent_events = [
            e
            for e in self._security_events
            if e.resource == f"provider:{provider_name}"
            and (datetime.now() - e.timestamp).total_seconds() < 3600
        ]

        failed_attempts = self._failed_attempts.get(provider_name, 0)

        status = ProviderSecurityStatus.SECURE
        if failed_attempts > self.security_policy.max_login_attempts:
            status = ProviderSecurityStatus.QUARANTINED
        elif config.api_key_required and not self._validate_api_key(
            provider_name, "dummy"
        ):
            status = ProviderSecurityStatus.AUTH_REQUIRED
        elif len([e for e in recent_events if e.severity == "error"]) > 5:
            status = ProviderSecurityStatus.MONITORING

        return {
            "provider_name": provider_name,
            "status": status.value,
            "access_level": config.access_level.value,
            "api_key_required": config.api_key_required,
            "tls_required": config.tls_required,
            "rate_limit_per_minute": config.rate_limit_per_minute,
            "max_concurrent_requests": config.max_concurrent_requests,
            "failed_attempts": failed_attempts,
            "recent_events": len(recent_events),
            "last_check": datetime.now().isoformat(),
            "security_config": config.__dict__,
        }

    async def start_background_tasks(self):
        """Start background security maintenance tasks"""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._security_maintenance_loop())
        logger.info("Security manager background tasks started")

    async def stop_background_tasks(self):
        """Stop background security maintenance tasks"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Security manager background tasks stopped")

    async def _security_maintenance_loop(self):
        """Background maintenance loop for security tasks"""
        while self._running:
            try:
                await self._cleanup_expired_tokens()
                await self._cleanup_expired_api_keys()
                await self._check_account_lockouts()
                await asyncio.sleep(300)  # Run every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Security maintenance error: {e}")
                await asyncio.sleep(60)

    async def _cleanup_expired_tokens(self):
        """Clean up expired access tokens"""
        current_time = time.time()
        with self._lock:
            expired_tokens = []
            for token, info in self._access_tokens.items():
                if info.get("expires_at", float("inf")) < current_time:
                    expired_tokens.append(token)

            for token in expired_tokens:
                del self._access_tokens[token]

    async def _cleanup_expired_api_keys(self):
        """Clean up expired API keys"""
        current_time = time.time()
        with self._lock:
            for provider_name, keys in self._api_keys.items():
                expired_keys = []
                for key, info in keys.items():
                    if info.get("expires_at", float("inf")) < current_time:
                        expired_keys.append(key)

                for key in expired_keys:
                    del keys[key]
                    self._log_security_event(
                        event_type="API_KEY_EXPIRED",
                        severity="info",
                        actor="system",
                        action="cleanup_expired_api_keys",
                        resource=f"provider:{provider_name}",
                        details={"api_key_id": key[:8] + "..."},
                    )

    async def _check_account_lockouts(self):
        """Check and clear expired account lockouts"""
        current_time = time.time()
        with self._lock:
            expired_lockouts = []
            for account, unlock_time in self._locked_accounts.items():
                if unlock_time < current_time:
                    expired_lockouts.append(account)

            for account in expired_lockouts:
                del self._locked_accounts[account]
                self._log_security_event(
                    event_type="ACCOUNT_UNLOCKED",
                    severity="info",
                    actor="system",
                    action="check_account_lockouts",
                    resource=f"account:{account}",
                    details={"reason": "lockout expired"},
                )

    def record_failed_attempt(
        self, provider_name: str, user_id: str, ip_address: Optional[str] = None
    ):
        """Record failed access attempt"""
        with self._lock:
            if provider_name not in self._failed_attempts:
                self._failed_attempts[provider_name] = 0
            self._failed_attempts[provider_name] += 1

            # Check for account lockout
            if (
                self._failed_attempts[provider_name]
                >= self.security_policy.max_login_attempts
            ):
                lockout_time = (
                    time.time() + self.security_policy.account_lockout_duration
                )
                self._locked_accounts[provider_name] = lockout_time

                self._log_security_event(
                    event_type="ACCOUNT_LOCKED",
                    severity="critical",
                    actor=user_id,
                    action="record_failed_attempt",
                    resource=f"provider:{provider_name}",
                    details={
                        "attempts": self._failed_attempts[provider_name],
                        "lockout_until": lockout_time,
                    },
                    ip_address=ip_address,
                    success=False,
                )
            else:
                self._log_security_event(
                    event_type="FAILED_ATTEMPT",
                    severity="warning",
                    actor=user_id,
                    action="record_failed_attempt",
                    resource=f"provider:{provider_name}",
                    details={"attempts": self._failed_attempts[provider_name]},
                    ip_address=ip_address,
                    success=False,
                )

    def reset_failed_attempts(self, provider_name: str):
        """Reset failed attempts counter"""
        with self._lock:
            if provider_name in self._failed_attempts:
                del self._failed_attempts[provider_name]

    def is_account_locked(self, provider_name: str) -> bool:
        """Check if account is locked"""
        with self._lock:
            if provider_name not in self._locked_accounts:
                return False

            if self._locked_accounts[provider_name] < time.time():
                del self._locked_accounts[provider_name]
                return False

            return True

    def export_security_audit(self, output_file: str) -> bool:
        """Export security audit trail to file"""
        try:
            audit_data = {
                "export_timestamp": datetime.now().isoformat(),
                "security_policy": self.security_policy.__dict__,
                "provider_configs": {
                    name: config.__dict__
                    for name, config in self._provider_configs.items()
                },
                "security_events": [event.__dict__ for event in self._security_events],
                "access_tokens_count": len(self._access_tokens),
                "api_keys_count": sum(len(keys) for keys in self._api_keys.values()),
                "failed_attempts": self._failed_attempts,
                "locked_accounts": self._locked_accounts,
            }

            with open(output_file, "w") as f:
                json.dump(audit_data, f, indent=2, default=str)

            self._log_security_event(
                event_type="AUDIT_EXPORT",
                severity="info",
                actor="system",
                action="export_security_audit",
                resource=f"file:{output_file}",
                details={"record_count": len(self._security_events)},
            )
            return True
        except Exception as e:
            logger.error(f"Failed to export security audit: {e}")
            return False

    def get_security_summary(self) -> Dict[str, Any]:
        """Get comprehensive security summary"""
        return {
            "security_policy": self.security_policy.__dict__,
            "provider_configs_count": len(self._provider_configs),
            "security_events_count": len(self._security_events),
            "access_tokens_count": len(self._access_tokens),
            "api_keys_count": sum(len(keys) for keys in self._api_keys.values()),
            "failed_attempts_total": sum(self._failed_attempts.values()),
            "locked_accounts_count": len(self._locked_accounts),
            "providers_with_security_issues": len(
                [
                    name
                    for name in self._provider_configs
                    if self.is_account_locked(name)
                ]
            ),
            "last_maintenance": datetime.now().isoformat(),
        }
