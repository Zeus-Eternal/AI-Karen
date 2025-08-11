"""
Security enhancement layer for the consolidated authentication service.

This module provides security features including rate limiting, audit logging,
and session validation to protect against attacks and provide comprehensive
monitoring of authentication activities.
"""

import asyncio
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from .config import AuthConfig
from .exceptions import RateLimitExceededError
from .models import AuthEvent, AuthEventType, SessionData
from .monitoring import metrics_hook as monitoring_metrics_hook
from .rate_limit_store import (
    InMemoryRateLimitStore,
    RateLimitStore,
    RedisRateLimitStore,
    build_limit_key,
)


class RateLimiter:
    """
    Rate limiting component to prevent brute force attacks and abuse.

    Implements sliding window rate limiting with configurable limits
    and automatic cleanup of expired entries.
    """

    def __init__(self, config: AuthConfig, store: Optional[RateLimitStore] = None):
        self.config = config
        self.security_config = config.security

        # Configure storage backend
        if store is not None:
            self.store = store
        else:
            backend = self.security_config.rate_limit_storage
            if backend == "redis":
                try:
                    import redis.asyncio as redis_asyncio  # type: ignore

                    redis_url = (
                        self.security_config.rate_limit_redis_url
                        or "redis://localhost:6379/0"
                    )
                    client = redis_asyncio.from_url(redis_url, decode_responses=True)
                    self.store = RedisRateLimitStore(client)
                except Exception:
                    self.store = InMemoryRateLimitStore()
            else:
                self.store = InMemoryRateLimitStore()

        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.time()

        # Rate limiting configuration
        self.max_requests = self.security_config.rate_limit_max_requests
        self.window_minutes = self.security_config.rate_limit_window_minutes
        self.max_failed_attempts = self.security_config.max_failed_attempts
        self.lockout_duration_minutes = self.security_config.lockout_duration_minutes

        self.logger = logging.getLogger(__name__)

    def _build_key(
        self, ip_address: str, email: Optional[str], event_type: str
    ) -> str:
        """Construct the storage key for rate limiting."""

        identifier = f"user:{email}" if email else "ip"
        return build_limit_key(identifier, event_type, ip_address)

    async def _cleanup_expired_entries(self) -> None:
        """Clean up expired rate limiting entries."""
        current_time = time.time()

        # Only cleanup periodically to avoid performance impact
        if current_time - self._last_cleanup < self._cleanup_interval:
            return

        window_seconds = self.window_minutes * 60
        cutoff_time = current_time - window_seconds

        await self.store.cleanup(current_time, cutoff_time)

        self._last_cleanup = current_time

    async def check_rate_limit(
        self, ip_address: str, email: Optional[str] = None, event_type: str = "general"
    ) -> bool:
        """
        Check if a request should be rate limited.

        Args:
            ip_address: Client IP address
            email: User email (optional)
            event_type: Type of event being rate limited

        Returns:
            True if request is allowed, False if rate limited

        Raises:
            RateLimitExceededError: If rate limit is exceeded
        """
        if not self.security_config.enable_rate_limiting:
            return True

        await self._cleanup_expired_entries()

        key = self._build_key(ip_address, email, event_type)
        identifier = f"user:{email}" if email else f"ip:{ip_address}"
        current_time = time.time()

        # Check if currently locked out
        lockout_until = await self.store.get_lockout(key)
        if lockout_until and lockout_until > current_time:
            lockout_remaining = int(lockout_until - current_time)
            raise RateLimitExceededError(
                message=f"Rate limit exceeded for {key}",
                retry_after=lockout_remaining,
                limit=self.max_requests,
                details={
                    "identifier": identifier,
                    "event_type": event_type,
                    "lockout_remaining_seconds": lockout_remaining,
                },
            )

        # Check rate limit window
        window_seconds = self.window_minutes * 60
        cutoff_time = current_time - window_seconds

        # Get recent attempts within the window
        recent_attempts = await self.store.get_recent_attempts(key, cutoff_time)

        if len(recent_attempts) >= self.max_requests:
            # Rate limit exceeded, add lockout
            lockout_until = current_time + (self.lockout_duration_minutes * 60)
            await self.store.set_lockout(key, lockout_until)

            self.logger.warning(
                f"Rate limit exceeded for {key}. "
                f"Locked out until {datetime.fromtimestamp(lockout_until)}"
            )

            raise RateLimitExceededError(
                message=f"Rate limit exceeded for {key}",
                retry_after=self.lockout_duration_minutes * 60,
                limit=self.max_requests,
                details={
                    "identifier": identifier,
                    "event_type": event_type,
                    "attempts_in_window": len(recent_attempts),
                    "window_minutes": self.window_minutes,
                },
            )

        return True

    async def record_attempt(
        self,
        ip_address: str,
        email: Optional[str] = None,
        success: bool = True,
        event_type: str = "general",
    ) -> None:
        """
        Record an authentication attempt for rate limiting.

        Args:
            ip_address: Client IP address
            email: User email (optional)
            success: Whether the attempt was successful
            event_type: Type of event being recorded
        """
        if not self.security_config.enable_rate_limiting:
            return

        key = self._build_key(ip_address, email, event_type)
        current_time = time.time()

        window_seconds = self.window_minutes * 60
        await self.store.add_attempt(key, current_time, window_seconds)

        # For failed attempts, also check if we should lock the account
        if not success and email:
            user_key = build_limit_key(f"user:{email}", "failed_login")
            await self.store.add_attempt(user_key, current_time, window_seconds)
            failed_attempts = await self.store.get_recent_attempts(
                user_key, current_time - window_seconds
            )

            if len(failed_attempts) >= self.max_failed_attempts:
                lockout_until = current_time + (self.lockout_duration_minutes * 60)
                await self.store.set_lockout(user_key, lockout_until)

                self.logger.warning(
                    f"User {email} locked out due to {len(failed_attempts)} failed attempts"
                )

    async def is_locked_out(self, ip_address: str, email: Optional[str] = None) -> bool:
        """Check if an identifier is currently locked out."""
        if not self.security_config.enable_rate_limiting:
            return False

        key = self._build_key(ip_address, email, "general")
        current_time = time.time()

        lockout_until = await self.store.get_lockout(key)
        if lockout_until:
            return lockout_until > current_time

        return False

    async def get_remaining_lockout_time(
        self, ip_address: str, email: Optional[str] = None
    ) -> int:
        """Get remaining lockout time in seconds."""
        if not self.security_config.enable_rate_limiting:
            return 0

        key = self._build_key(ip_address, email, "general")
        current_time = time.time()

        lockout_until = await self.store.get_lockout(key)
        if lockout_until:
            remaining = lockout_until - current_time
            return max(0, int(remaining))

        return 0

    async def clear_lockout(self, ip_address: str, email: Optional[str] = None) -> None:
        """Clear lockout for an identifier (admin function)."""
        key = self._build_key(ip_address, email, "general")
        await self.store.clear(key)

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        current_time = time.time()
        store_stats = self.store.stats(current_time)

        return {
            **store_stats,
            "max_requests_per_window": self.max_requests,
            "window_minutes": self.window_minutes,
            "lockout_duration_minutes": self.lockout_duration_minutes,
        }


class AuditLogger:
    """
    Comprehensive authentication event logging for security monitoring.

    Provides structured logging of all authentication events with
    configurable output formats, security-focused event tracking and
    optional metrics forwarding.
    """

    def __init__(
        self,
        config: AuthConfig,
        metrics_hook: Optional[
            Callable[[str, Dict[str, Any]], None]
        ] = monitoring_metrics_hook,
    ):
        self.config = config
        self.security_config = config.security
        self.metrics_hook = metrics_hook

        # Set up structured logging
        self.logger = logging.getLogger(f"{__name__}.audit")
        self.logger.setLevel(logging.INFO)

        # Create formatter for structured logging
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Add console handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # Event counters for monitoring
        self._event_counts: Dict[str, int] = defaultdict(int)
        self._security_events: List[Dict[str, Any]] = []
        self._max_security_events = 1000  # Keep last 1000 security events in memory

    async def log_auth_event(self, event: AuthEvent) -> None:
        """
        Log an authentication event with appropriate detail level.

        Args:
            event: AuthEvent instance to log
        """
        if not self.security_config.enable_audit_logging:
            return

        # Check if we should log this event type
        should_log = self._should_log_event(event)
        if not should_log:
            return

        # Increment event counter
        self._event_counts[event.event_type.value] += 1

        # Create log entry
        log_data = self._create_log_entry(event)

        # Determine log level based on event type and success
        log_level = self._get_log_level(event)

        # Log the event
        self.logger.log(
            log_level,
            f"AUTH_EVENT: {event.event_type.value}",
            extra={
                "auth_event": log_data,
                "event_id": event.event_id,
                "user_id": event.user_id,
                "email": event.email,
                "ip_address": event.ip_address,
                "success": event.success,
                "risk_score": event.risk_score,
            },
        )

        # Store security events for monitoring
        if self._is_security_event(event):
            self._store_security_event(log_data)

        # Forward to metrics hook if available
        if self.metrics_hook:
            try:
                self.metrics_hook(
                    event.event_type.value,
                    {"processing_time_ms": event.processing_time_ms},
                )
            except Exception:  # pragma: no cover - metrics are best effort
                self.logger.debug("Metrics hook failed", exc_info=True)

    def _should_log_event(self, event: AuthEvent) -> bool:
        """Determine if an event should be logged based on configuration."""
        if not event.success and self.security_config.log_failed_logins:
            return True

        if (
            event.success
            and event.event_type
            in {AuthEventType.LOGIN_SUCCESS, AuthEventType.SESSION_CREATED}
            and self.security_config.log_successful_logins
        ):
            return True

        if self._is_security_event(event) and self.security_config.log_security_events:
            return True

        # Always log critical security events
        critical_events = {
            AuthEventType.LOGIN_BLOCKED,
            AuthEventType.RATE_LIMIT_EXCEEDED,
            AuthEventType.SECURITY_BLOCK,
            AuthEventType.ANOMALY_DETECTED,
            AuthEventType.THREAT_DETECTED,
        }

        return event.event_type in critical_events

    def _is_security_event(self, event: AuthEvent) -> bool:
        """Check if an event is security-related."""
        security_events = {
            AuthEventType.LOGIN_FAILED,
            AuthEventType.LOGIN_BLOCKED,
            AuthEventType.RATE_LIMIT_EXCEEDED,
            AuthEventType.SECURITY_BLOCK,
            AuthEventType.ANOMALY_DETECTED,
            AuthEventType.THREAT_DETECTED,
            AuthEventType.TWO_FACTOR_FAILED,
        }

        return (
            event.event_type in security_events
            or not event.success
            or event.blocked_by_security
            or event.risk_score > 0.5
        )

    def _get_log_level(self, event: AuthEvent) -> int:
        """Get appropriate log level for an event."""
        if event.event_type in {
            AuthEventType.LOGIN_BLOCKED,
            AuthEventType.SECURITY_BLOCK,
            AuthEventType.ANOMALY_DETECTED,
            AuthEventType.THREAT_DETECTED,
        }:
            return logging.ERROR

        if not event.success or event.risk_score > 0.7:
            return logging.WARNING

        return logging.INFO

    def _create_log_entry(self, event: AuthEvent) -> Dict[str, Any]:
        """Create a structured log entry from an auth event."""
        log_entry = {
            "timestamp": event.timestamp.isoformat(),
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "success": event.success,
            "user_id": event.user_id,
            "email": event.email,
            "tenant_id": event.tenant_id,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
            "session_token": event.session_token,
            "risk_score": event.risk_score,
            "security_flags": event.security_flags,
            "blocked_by_security": event.blocked_by_security,
            "processing_time_ms": event.processing_time_ms,
            "service_version": event.service_version,
        }

        # Add error information if present
        if event.error_message:
            log_entry["error_message"] = event.error_message

        # Add details if present
        if event.details:
            log_entry["details"] = event.details

        # Add request context if available
        if event.request_id:
            log_entry["request_id"] = event.request_id

        return log_entry

    def _store_security_event(self, log_data: Dict[str, Any]) -> None:
        """Store security event for monitoring and analysis."""
        self._security_events.append(log_data)

        # Keep only the most recent events
        if len(self._security_events) > self._max_security_events:
            self._security_events = self._security_events[-self._max_security_events :]

    async def log_login_attempt(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        user_id: Optional[str] = None,
        error_message: Optional[str] = None,
        risk_score: float = 0.0,
        processing_time_ms: float = 0.0,
        **kwargs,
    ) -> None:
        """Log a login attempt with standard fields."""
        event_type = (
            AuthEventType.LOGIN_SUCCESS if success else AuthEventType.LOGIN_FAILED
        )

        event = AuthEvent(
            event_type=event_type,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
            risk_score=risk_score,
            processing_time_ms=processing_time_ms,
            **kwargs,
        )

        await self.log_auth_event(event)

    async def log_session_event(
        self,
        event_type: AuthEventType,
        session_data: SessionData,
        success: bool = True,
        error_message: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Log a session-related event."""
        event = AuthEvent(
            event_type=event_type,
            user_id=session_data.user_data.user_id,
            email=session_data.user_data.email,
            tenant_id=session_data.user_data.tenant_id,
            ip_address=session_data.ip_address,
            user_agent=session_data.user_agent,
            session_token=session_data.session_token,
            success=success,
            error_message=error_message,
            risk_score=session_data.risk_score,
            security_flags=session_data.security_flags,
            **kwargs,
        )

        await self.log_auth_event(event)

    async def log_security_event(
        self,
        event_type: AuthEventType,
        ip_address: str,
        user_agent: str = "",
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        risk_score: float = 0.0,
        security_flags: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> None:
        """Log a security-related event."""
        event = AuthEvent(
            event_type=event_type,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,  # Security events are typically failures
            risk_score=risk_score,
            security_flags=security_flags or [],
            blocked_by_security=True,
            details=details or {},
            **kwargs,
        )

        await self.log_auth_event(event)

    def get_event_counts(self) -> Dict[str, int]:
        """Get event counts for monitoring."""
        return dict(self._event_counts)

    def get_recent_security_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent security events for analysis."""
        return self._security_events[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get audit logging statistics."""
        total_events = sum(self._event_counts.values())
        security_event_count = len(self._security_events)

        return {
            "total_events_logged": total_events,
            "security_events_stored": security_event_count,
            "event_counts_by_type": dict(self._event_counts),
            "logging_enabled": self.security_config.enable_audit_logging,
            "log_successful_logins": self.security_config.log_successful_logins,
            "log_failed_logins": self.security_config.log_failed_logins,
            "log_security_events": self.security_config.log_security_events,
        }


class SessionValidator:
    """
    Session validation component for enhanced session security.

    Provides validation of session integrity, security context,
    and detection of suspicious session activity.
    """

    def __init__(self, config: AuthConfig):
        self.config = config
        self.security_config = config.security
        self.session_config = config.session

        self.logger = logging.getLogger(__name__)

        # Session validation cache to avoid repeated validations
        self._validation_cache: Dict[str, Tuple[bool, float]] = {}
        self._cache_ttl = 300  # 5 minutes

    async def validate_session_security(
        self,
        session: SessionData,
        current_ip: str,
        current_user_agent: str,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate session security and detect suspicious activity.

        Args:
            session: Session data to validate
            current_ip: Current request IP address
            current_user_agent: Current request user agent
            request_context: Additional request context

        Returns:
            Dictionary with validation results and security flags
        """
        if not self.security_config.enable_session_validation:
            return {
                "valid": True,
                "security_flags": [],
                "risk_score": 0.0,
                "warnings": [],
            }

        validation_result = {
            "valid": True,
            "security_flags": [],
            "risk_score": session.risk_score,
            "warnings": [],
            "details": {},
        }

        # Check if session is active first
        if not session.is_active:
            validation_result["valid"] = False
            validation_result["security_flags"].append("session_inactive")
            validation_result["warnings"].append("Session is not active")
            return validation_result

        # Check if session is expired
        if session.is_expired():
            validation_result["valid"] = False
            validation_result["security_flags"].append("session_expired")
            validation_result["warnings"].append("Session has expired")
            return validation_result

        # Validate IP address if configured
        if self.security_config.validate_ip_address:
            ip_validation = await self._validate_ip_address(session, current_ip)
            validation_result["security_flags"].extend(ip_validation["flags"])
            validation_result["risk_score"] = max(
                validation_result["risk_score"], ip_validation["risk_score"]
            )
            if ip_validation["warnings"]:
                validation_result["warnings"].extend(ip_validation["warnings"])

        # Validate user agent if configured
        if self.security_config.validate_user_agent:
            ua_validation = await self._validate_user_agent(session, current_user_agent)
            validation_result["security_flags"].extend(ua_validation["flags"])
            validation_result["risk_score"] = max(
                validation_result["risk_score"], ua_validation["risk_score"]
            )
            if ua_validation["warnings"]:
                validation_result["warnings"].extend(ua_validation["warnings"])

        # Check session age and activity
        session_validation = await self._validate_session_activity(session)
        validation_result["security_flags"].extend(session_validation["flags"])
        validation_result["risk_score"] = max(
            validation_result["risk_score"], session_validation["risk_score"]
        )
        if session_validation["warnings"]:
            validation_result["warnings"].extend(session_validation["warnings"])

        # Check for device fingerprint changes if enabled
        if self.security_config.enable_device_fingerprinting and request_context:
            device_validation = await self._validate_device_fingerprint(
                session, request_context
            )
            validation_result["security_flags"].extend(device_validation["flags"])
            validation_result["risk_score"] = max(
                validation_result["risk_score"], device_validation["risk_score"]
            )
            if device_validation["warnings"]:
                validation_result["warnings"].extend(device_validation["warnings"])

        # Update session with new security flags
        for flag in validation_result["security_flags"]:
            session.add_security_flag(flag)

        session.update_risk_score(validation_result["risk_score"])
        session.update_last_accessed()

        return validation_result

    async def _validate_ip_address(
        self, session: SessionData, current_ip: str
    ) -> Dict[str, Any]:
        """Validate IP address consistency."""
        result = {"flags": [], "risk_score": 0.0, "warnings": []}

        if session.ip_address != current_ip:
            result["flags"].append("ip_address_changed")
            result["risk_score"] = 0.3
            result["warnings"].append(
                f"IP address changed from {session.ip_address} to {current_ip}"
            )

            # Check if it's a significant change (different subnet)
            if not self._is_same_subnet(session.ip_address, current_ip):
                result["flags"].append("ip_subnet_changed")
                result["risk_score"] = 0.6
                result["warnings"].append("IP address changed to different subnet")

        return result

    async def _validate_user_agent(
        self, session: SessionData, current_user_agent: str
    ) -> Dict[str, Any]:
        """Validate user agent consistency."""
        result = {"flags": [], "risk_score": 0.0, "warnings": []}

        if session.user_agent != current_user_agent:
            result["flags"].append("user_agent_changed")
            result["risk_score"] = 0.2
            result["warnings"].append("User agent changed")

            # Check for significant changes (different browser/OS)
            if not self._is_similar_user_agent(session.user_agent, current_user_agent):
                result["flags"].append("user_agent_major_change")
                result["risk_score"] = 0.5
                result["warnings"].append("Major user agent change detected")

        return result

    async def _validate_session_activity(self, session: SessionData) -> Dict[str, Any]:
        """Validate session activity patterns."""
        result = {"flags": [], "risk_score": 0.0, "warnings": []}

        now = datetime.now(timezone.utc)

        # Check session age
        session_age = now - session.created_at
        max_session_age = self.session_config.session_timeout

        if session_age > max_session_age:
            result["flags"].append("session_too_old")
            result["risk_score"] = 0.8
            result["warnings"].append("Session exceeds maximum age")

        # Check last access time
        time_since_access = now - session.last_accessed
        if time_since_access > timedelta(hours=1):
            result["flags"].append("session_inactive")
            result["risk_score"] = max(result["risk_score"], 0.3)
            result["warnings"].append("Session has been inactive for extended period")

        return result

    async def _validate_device_fingerprint(
        self, session: SessionData, request_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate device fingerprint consistency."""
        result = {"flags": [], "risk_score": 0.0, "warnings": []}

        current_fingerprint = request_context.get("device_fingerprint")
        if not current_fingerprint or not session.device_fingerprint:
            return result

        if session.device_fingerprint != current_fingerprint:
            result["flags"].append("device_fingerprint_changed")
            result["risk_score"] = 0.7
            result["warnings"].append("Device fingerprint changed")

        return result

    def _is_same_subnet(self, ip1: str, ip2: str) -> bool:
        """Check if two IP addresses are in the same subnet (simplified)."""
        try:
            # Simple check for IPv4 - same first 3 octets
            parts1 = ip1.split(".")
            parts2 = ip2.split(".")

            if len(parts1) == 4 and len(parts2) == 4:
                return parts1[:3] == parts2[:3]
        except Exception:
            pass

        return False

    def _is_similar_user_agent(self, ua1: str, ua2: str) -> bool:
        """Check if two user agents are similar (same browser family)."""
        if not ua1 or not ua2:
            return False

        # Extract browser name (simplified)
        browsers = ["Chrome", "Firefox", "Safari", "Edge", "Opera"]

        ua1_browser = None
        ua2_browser = None

        for browser in browsers:
            if browser in ua1:
                ua1_browser = browser
            if browser in ua2:
                ua2_browser = browser

        return ua1_browser == ua2_browser

    async def validate_session_token(self, session_token: str) -> bool:
        """Validate session token format and structure."""
        if not session_token:
            return False

        # Basic token format validation
        if len(session_token) < 32:
            return False

        # Check for valid characters (alphanumeric and some special chars)
        allowed_chars = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
        )
        if not all(c in allowed_chars for c in session_token):
            return False

        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get session validation statistics."""
        return {
            "validation_enabled": self.security_config.enable_session_validation,
            "validate_ip_address": self.security_config.validate_ip_address,
            "validate_user_agent": self.security_config.validate_user_agent,
            "device_fingerprinting_enabled": self.security_config.enable_device_fingerprinting,
            "cache_entries": len(self._validation_cache),
        }


class SecurityEnhancer:
    """
    Main security enhancement layer that orchestrates all security components.

    This class provides the unified interface for all security features
    including rate limiting, audit logging, and session validation.
    """

    def __init__(
        self,
        config: AuthConfig,
        metrics_hook: Optional[
            Callable[[str, Dict[str, Any]], None]
        ] = monitoring_metrics_hook,
    ):
        self.config = config
        self.security_config = config.security

        # Initialize security components
        self.rate_limiter = RateLimiter(config)
        self.audit_logger = AuditLogger(config, metrics_hook=metrics_hook)
        self.session_validator = SessionValidator(config)

        self.logger = logging.getLogger(__name__)

    async def check_request_security(
        self,
        ip_address: str,
        user_agent: str,
        email: Optional[str] = None,
        event_type: str = "authentication",
        request_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Comprehensive security check for authentication requests.

        Args:
            ip_address: Client IP address
            user_agent: Client user agent
            email: User email (optional)
            event_type: Type of authentication event
            request_context: Additional request context

        Returns:
            Dictionary with security check results
        """
        security_result = {
            "allowed": True,
            "security_flags": [],
            "risk_score": 0.0,
            "warnings": [],
            "rate_limit_info": {},
            "details": {},
        }

        try:
            # Check rate limiting
            await self.rate_limiter.check_rate_limit(
                ip_address=ip_address, email=email, event_type=event_type
            )

            # Get rate limit info
            is_locked = await self.rate_limiter.is_locked_out(ip_address, email)
            if is_locked:
                remaining_time = await self.rate_limiter.get_remaining_lockout_time(
                    ip_address, email
                )
                security_result["allowed"] = False
                security_result["security_flags"].append("rate_limited")
                security_result["rate_limit_info"] = {
                    "locked_out": True,
                    "remaining_seconds": remaining_time,
                }

            return security_result

        except RateLimitExceededError as e:
            security_result["allowed"] = False
            security_result["security_flags"].append("rate_limit_exceeded")
            security_result["details"]["rate_limit_error"] = str(e)
            return security_result

        except Exception as e:
            self.logger.error(f"Security check error: {e}")
            security_result["warnings"].append(f"Security check failed: {e}")
            return security_result

    async def initialize(self) -> None:
        """Initialize the security enhancer."""
        # Any async initialization can go here
        pass

    async def check_rate_limit(
        self, ip_address: str, email: Optional[str] = None, event_type: str = "general"
    ) -> bool:
        """Check rate limit for a request."""
        return await self.rate_limiter.check_rate_limit(ip_address, email, event_type)

    async def record_successful_attempt(
        self, ip_address: str, email: str, user_id: str, event_type: str = "login"
    ) -> None:
        """Record a successful authentication attempt."""
        await self.rate_limiter.record_attempt(
            ip_address=ip_address, email=email, success=True, event_type=event_type
        )

        await self.audit_logger.log_login_attempt(
            email=email,
            ip_address=ip_address,
            user_agent="",
            success=True,
            user_id=user_id,
        )

    async def record_failed_attempt(
        self,
        ip_address: str,
        email: str,
        error_type: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a failed authentication attempt."""
        await self.rate_limiter.record_attempt(
            ip_address=ip_address, email=email, success=False, event_type="login_failed"
        )

        await self.audit_logger.log_login_attempt(
            email=email,
            ip_address=ip_address,
            user_agent="",
            success=False,
            error_message=error_type,
        )

    async def validate_session_security(
        self,
        session: SessionData,
        current_ip: str,
        current_user_agent: str,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Validate session security."""
        return await self.session_validator.validate_session_security(
            session, current_ip, current_user_agent, request_context
        )

    async def log_auth_event(self, event: AuthEvent) -> None:
        """Log an authentication event."""
        await self.audit_logger.log_auth_event(event)

    async def log_session_event(
        self,
        event_type: AuthEventType,
        session_data: SessionData,
        success: bool = True,
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a session-related event."""
        await self.audit_logger.log_session_event(
            event_type, session_data, success, error_message, **details or {}
        )

    async def log_security_event(
        self,
        event_type: AuthEventType,
        ip_address: str,
        user_agent: str = "",
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        risk_score: float = 0.0,
        security_flags: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a security-related event."""
        await self.audit_logger.log_security_event(
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id,
            email=email,
            risk_score=risk_score,
            security_flags=security_flags,
            details=details,
        )

    async def get_user_auth_history(
        self, user_id: str, days: int = 30
    ) -> List[AuthEvent]:
        """Get authentication history for a user."""
        # This would typically query the database for auth events
        # For now, return empty list as placeholder
        return []

    async def update_user_intelligence_data(
        self, user_id: str, intelligence_result: Any
    ) -> None:
        """Update user intelligence data."""
        # Placeholder for updating user intelligence data
        pass

    async def get_stats(self) -> Dict[str, Any]:
        """Get security layer statistics."""
        rate_limiter_stats = self.rate_limiter.get_stats()
        audit_logger_stats = self.audit_logger.get_stats()

        return {
            "rate_limiter": rate_limiter_stats,
            "audit_logger": audit_logger_stats,
            "security_enabled": True,
            "components": {
                "rate_limiter": "active",
                "audit_logger": "active",
                "session_validator": "active",
            },
        }

    async def validate_session_request(
        self,
        session: SessionData,
        ip_address: str,
        user_agent: str,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate a session-based request for security issues.

        Args:
            session: Session data
            ip_address: Current request IP
            user_agent: Current request user agent
            request_context: Additional request context

        Returns:
            Dictionary with validation results
        """
        validation_result = await self.session_validator.validate_session_security(
            session=session,
            current_ip=ip_address,
            current_user_agent=user_agent,
            request_context=request_context,
        )

        # Log session validation events if there are security concerns
        if validation_result["security_flags"] or validation_result["risk_score"] > 0.5:
            await self.audit_logger.log_session_event(
                event_type=AuthEventType.SESSION_CREATED,  # Or appropriate type
                session_data=session,
                success=validation_result["valid"],
                details={
                    "validation_result": validation_result,
                    "security_flags": validation_result["security_flags"],
                    "risk_score": validation_result["risk_score"],
                },
            )

        return validation_result

    async def log_authentication_attempt(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        user_id: Optional[str] = None,
        error_message: Optional[str] = None,
        risk_score: float = 0.0,
        processing_time_ms: float = 0.0,
        session_data: Optional[SessionData] = None,
        **kwargs,
    ) -> None:
        """
        Log an authentication attempt with security context.

        Args:
            email: User email
            ip_address: Client IP address
            user_agent: Client user agent
            success: Whether authentication succeeded
            user_id: User ID (if successful)
            error_message: Error message (if failed)
            risk_score: Calculated risk score
            processing_time_ms: Processing time in milliseconds
            session_data: Session data (if created)
            **kwargs: Additional context
        """
        # Record the attempt for rate limiting
        await self.rate_limiter.record_attempt(
            ip_address=ip_address, email=email, success=success, event_type="login"
        )

        # Log the authentication attempt
        await self.audit_logger.log_login_attempt(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            user_id=user_id,
            error_message=error_message,
            risk_score=risk_score,
            processing_time_ms=processing_time_ms,
            **kwargs,
        )

        # Log session creation if successful
        if success and session_data:
            await self.audit_logger.log_session_event(
                event_type=AuthEventType.SESSION_CREATED,
                session_data=session_data,
                success=True,
            )

    async def log_security_event(
        self,
        event_type: AuthEventType,
        ip_address: str,
        user_agent: str = "",
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        risk_score: float = 0.0,
        security_flags: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> None:
        """Log a security-related event."""
        await self.audit_logger.log_security_event(
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id,
            email=email,
            risk_score=risk_score,
            security_flags=security_flags,
            details=details,
            **kwargs,
        )

    def get_security_stats(self) -> Dict[str, Any]:
        """Get comprehensive security statistics."""
        return {
            "rate_limiter": self.rate_limiter.get_stats(),
            "audit_logger": self.audit_logger.get_stats(),
            "session_validator": self.session_validator.get_stats(),
            "security_features_enabled": self.security_config.enable_rate_limiting,
        }

    async def clear_user_lockout(self, email: str, ip_address: str) -> None:
        """Clear lockout for a user (admin function)."""
        await self.rate_limiter.clear_lockout(ip_address, email)

        await self.audit_logger.log_security_event(
            event_type=AuthEventType.USER_UPDATED,
            ip_address=ip_address,
            email=email,
            details={"action": "lockout_cleared", "admin_action": True},
        )

    def is_enabled(self) -> bool:
        """Check if security features are enabled."""
        return (
            self.security_config.enable_rate_limiting
            or self.security_config.enable_audit_logging
            or self.security_config.enable_session_validation
        )

    async def shutdown(self) -> None:
        """Gracefully shutdown the security enhancer and its components."""
        self.logger.info("Shutting down security enhancer")

        try:
            if hasattr(self.rate_limiter, "shutdown"):
                await self.rate_limiter.shutdown()
            else:
                store = getattr(self.rate_limiter, "store", None)
                client = getattr(store, "client", None)
                close = getattr(client, "close", None)
                if close:
                    if asyncio.iscoroutinefunction(close):
                        await close()
                    else:
                        close()
        except Exception as e:  # pragma: no cover - defensive
            self.logger.error(f"Error shutting down rate limiter: {e}")

        try:
            if hasattr(self.audit_logger, "shutdown"):
                await self.audit_logger.shutdown()
        except Exception as e:  # pragma: no cover - defensive
            self.logger.error(f"Error shutting down audit logger: {e}")

        try:
            if hasattr(self.session_validator, "shutdown"):
                await self.session_validator.shutdown()
        except Exception as e:  # pragma: no cover - defensive
            self.logger.error(f"Error shutting down session validator: {e}")

        self.logger.info("Security enhancer shutdown complete")
