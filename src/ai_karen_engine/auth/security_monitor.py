"""
Enhanced Security Monitoring for Authentication System

This module provides advanced security monitoring capabilities including:
- Suspicious activity detection
- Security alerts for failed attempts and anomalies
- Enhanced rate limiting with exponential backoff
- Real-time threat analysis
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum

from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.auth.exceptions import (
    AnomalyDetectedError,
    RateLimitExceededError,
    SecurityError,
    SuspiciousActivityError,
)
from ai_karen_engine.auth.models import AuthEvent, AuthEventType
from ai_karen_engine.core.logging import get_logger


class ThreatLevel(Enum):
    """Security threat levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(Enum):
    """Types of security anomalies"""
    RAPID_FAILED_ATTEMPTS = "rapid_failed_attempts"
    UNUSUAL_LOCATION = "unusual_location"
    UNUSUAL_TIME = "unusual_time"
    MULTIPLE_IPS = "multiple_ips"
    BRUTE_FORCE_PATTERN = "brute_force_pattern"
    CREDENTIAL_STUFFING = "credential_stuffing"
    ACCOUNT_ENUMERATION = "account_enumeration"
    SESSION_HIJACKING = "session_hijacking"


@dataclass
class SecurityAlert:
    """Security alert data structure"""
    alert_id: str
    alert_type: str
    threat_level: ThreatLevel
    timestamp: datetime
    source_ip: str
    user_email: Optional[str] = None
    user_id: Optional[str] = None
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_notes: Optional[str] = None


@dataclass
class SuspiciousActivity:
    """Suspicious activity detection result"""
    is_suspicious: bool
    anomaly_types: List[AnomalyType]
    risk_score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthAttempt:
    """Authentication attempt record"""
    timestamp: datetime
    ip_address: str
    user_agent: str
    email: Optional[str]
    success: bool
    failure_reason: Optional[str] = None
    geolocation: Optional[Dict[str, Any]] = None
    device_fingerprint: Optional[str] = None


class ExponentialBackoffRateLimiter:
    """
    Enhanced rate limiter with exponential backoff for authentication endpoints
    """
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Rate limiting configuration
        self.base_window_seconds = 60  # Base window: 1 minute
        self.max_attempts_per_window = 50  # Increased from 5 to 50 attempts per window
        self.backoff_multiplier = 1.5  # Reduced from 2.0 to 1.5 for gentler backoff
        self.max_backoff_hours = 1  # Reduced from 24 to 1 hour maximum backoff
        
        # In-memory storage for rate limiting
        self._attempt_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._lockout_until: Dict[str, datetime] = {}
        self._backoff_level: Dict[str, int] = defaultdict(int)
        
    def _get_key(self, ip_address: str, email: Optional[str] = None) -> str:
        """Generate rate limiting key"""
        if email:
            return f"user:{email}:{ip_address}"
        return f"ip:{ip_address}"
    
    def _calculate_backoff_duration(self, backoff_level: int) -> int:
        """Calculate exponential backoff duration in seconds"""
        duration_seconds = self.base_window_seconds * (self.backoff_multiplier ** backoff_level)
        max_duration_seconds = self.max_backoff_hours * 3600
        return min(int(duration_seconds), max_duration_seconds)
    
    async def check_rate_limit(
        self, 
        ip_address: str, 
        email: Optional[str] = None,
        endpoint: str = "auth"
    ) -> bool:
        """
        Check if request should be rate limited with exponential backoff
        
        Returns:
            True if request is allowed, False if rate limited
            
        Raises:
            RateLimitExceededError: If rate limit is exceeded
        """
        key = self._get_key(ip_address, email)
        current_time = datetime.now(timezone.utc)
        
        # Check if currently locked out
        if key in self._lockout_until:
            lockout_until = self._lockout_until[key]
            if lockout_until > current_time:
                remaining_seconds = int((lockout_until - current_time).total_seconds())
                backoff_level = self._backoff_level[key]
                
                raise RateLimitExceededError(
                    message=f"Rate limit exceeded with exponential backoff",
                    retry_after=remaining_seconds,
                    details={
                        "endpoint": endpoint,
                        "backoff_level": backoff_level,
                        "lockout_until": lockout_until.isoformat(),
                        "ip_address": ip_address,
                        "email": email,
                    }
                )
            else:
                # Lockout expired, remove it
                del self._lockout_until[key]
        
        # Check recent attempts within current window
        window_start = current_time - timedelta(seconds=self.base_window_seconds)
        recent_attempts = self._attempt_history[key]
        
        # Remove old attempts outside the window
        while recent_attempts and recent_attempts[0] < window_start:
            recent_attempts.popleft()
        
        # Check if we've exceeded the limit
        if len(recent_attempts) >= self.max_attempts_per_window:
            # Increase backoff level and set lockout
            self._backoff_level[key] += 1
            backoff_duration = self._calculate_backoff_duration(self._backoff_level[key])
            lockout_until = current_time + timedelta(seconds=backoff_duration)
            self._lockout_until[key] = lockout_until
            
            self.logger.warning(
                f"Rate limit exceeded for {key}, backoff level {self._backoff_level[key]}, "
                f"locked out until {lockout_until}"
            )
            
            raise RateLimitExceededError(
                message=f"Rate limit exceeded with exponential backoff",
                retry_after=backoff_duration,
                details={
                    "endpoint": endpoint,
                    "backoff_level": self._backoff_level[key],
                    "lockout_until": lockout_until.isoformat(),
                    "attempts_in_window": len(recent_attempts),
                    "ip_address": ip_address,
                    "email": email,
                }
            )
        
        return True
    
    async def record_attempt(
        self, 
        ip_address: str, 
        email: Optional[str] = None,
        success: bool = True
    ) -> None:
        """Record an authentication attempt"""
        key = self._get_key(ip_address, email)
        current_time = datetime.now(timezone.utc)
        
        # Record the attempt
        self._attempt_history[key].append(current_time)
        
        # Reset backoff level on successful authentication
        if success and key in self._backoff_level:
            self._backoff_level[key] = 0
            if key in self._lockout_until:
                del self._lockout_until[key]
    
    def get_current_backoff_level(self, ip_address: str, email: Optional[str] = None) -> int:
        """Get current backoff level for debugging/monitoring"""
        key = self._get_key(ip_address, email)
        return self._backoff_level[key]


class SuspiciousActivityDetector:
    """
    Detects suspicious authentication patterns and anomalies
    """
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Detection thresholds
        self.rapid_attempts_threshold = 10  # attempts per minute
        self.multiple_ip_threshold = 3  # different IPs per user per hour
        self.unusual_time_threshold = 0.1  # probability threshold for unusual times
        
        # Historical data storage
        self._user_attempts: Dict[str, List[AuthAttempt]] = defaultdict(list)
        self._ip_attempts: Dict[str, List[AuthAttempt]] = defaultdict(list)
        self._user_locations: Dict[str, Set[str]] = defaultdict(set)
        self._user_typical_times: Dict[str, List[int]] = defaultdict(list)  # hours of day
        
    async def analyze_attempt(
        self,
        ip_address: str,
        user_agent: str,
        email: Optional[str] = None,
        success: bool = True,
        failure_reason: Optional[str] = None,
        geolocation: Optional[Dict[str, Any]] = None,
        device_fingerprint: Optional[str] = None,
    ) -> SuspiciousActivity:
        """
        Analyze an authentication attempt for suspicious patterns
        
        Returns:
            SuspiciousActivity object with detection results
        """
        current_time = datetime.now(timezone.utc)
        
        # Create attempt record
        attempt = AuthAttempt(
            timestamp=current_time,
            ip_address=ip_address,
            user_agent=user_agent,
            email=email,
            success=success,
            failure_reason=failure_reason,
            geolocation=geolocation,
            device_fingerprint=device_fingerprint,
        )
        
        # Store attempt for analysis
        if email:
            self._user_attempts[email].append(attempt)
            # Keep only last 100 attempts per user
            self._user_attempts[email] = self._user_attempts[email][-100:]
        
        self._ip_attempts[ip_address].append(attempt)
        # Keep only last 100 attempts per IP
        self._ip_attempts[ip_address] = self._ip_attempts[ip_address][-100:]
        
        # Perform anomaly detection
        anomalies = []
        risk_score = 0.0
        confidence = 0.0
        details = {}
        
        # 1. Rapid failed attempts detection
        if not success:
            rapid_anomaly = await self._detect_rapid_failed_attempts(ip_address, email)
            if rapid_anomaly:
                anomalies.append(AnomalyType.RAPID_FAILED_ATTEMPTS)
                risk_score = max(risk_score, 0.8)
                confidence = max(confidence, 0.9)
                details["rapid_attempts"] = rapid_anomaly
        
        # 2. Multiple IPs for same user
        if email:
            multi_ip_anomaly = await self._detect_multiple_ips(email)
            if multi_ip_anomaly:
                anomalies.append(AnomalyType.MULTIPLE_IPS)
                risk_score = max(risk_score, 0.6)
                confidence = max(confidence, 0.7)
                details["multiple_ips"] = multi_ip_anomaly
        
        # 3. Unusual location detection
        if geolocation and email:
            location_anomaly = await self._detect_unusual_location(email, geolocation)
            if location_anomaly:
                anomalies.append(AnomalyType.UNUSUAL_LOCATION)
                risk_score = max(risk_score, 0.5)
                confidence = max(confidence, 0.6)
                details["unusual_location"] = location_anomaly
        
        # 4. Unusual time detection
        if email:
            time_anomaly = await self._detect_unusual_time(email, current_time)
            if time_anomaly:
                anomalies.append(AnomalyType.UNUSUAL_TIME)
                risk_score = max(risk_score, 0.3)
                confidence = max(confidence, 0.5)
                details["unusual_time"] = time_anomaly
        
        # 5. Brute force pattern detection
        brute_force_anomaly = await self._detect_brute_force_pattern(ip_address)
        if brute_force_anomaly:
            anomalies.append(AnomalyType.BRUTE_FORCE_PATTERN)
            risk_score = max(risk_score, 0.9)
            confidence = max(confidence, 0.8)
            details["brute_force"] = brute_force_anomaly
        
        # 6. Account enumeration detection
        if not success and failure_reason == "user_not_found":
            enum_anomaly = await self._detect_account_enumeration(ip_address)
            if enum_anomaly:
                anomalies.append(AnomalyType.ACCOUNT_ENUMERATION)
                risk_score = max(risk_score, 0.7)
                confidence = max(confidence, 0.6)
                details["account_enumeration"] = enum_anomaly
        
        is_suspicious = len(anomalies) > 0 and risk_score > 0.4
        
        return SuspiciousActivity(
            is_suspicious=is_suspicious,
            anomaly_types=anomalies,
            risk_score=risk_score,
            confidence=confidence,
            details=details,
        )
    
    async def _detect_rapid_failed_attempts(
        self, ip_address: str, email: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Detect rapid failed authentication attempts"""
        current_time = datetime.now(timezone.utc)
        one_minute_ago = current_time - timedelta(minutes=1)
        
        # Check IP-based attempts
        ip_attempts = self._ip_attempts[ip_address]
        recent_ip_failures = [
            a for a in ip_attempts 
            if a.timestamp > one_minute_ago and not a.success
        ]
        
        if len(recent_ip_failures) >= self.rapid_attempts_threshold:
            return {
                "ip_failures_per_minute": len(recent_ip_failures),
                "threshold": self.rapid_attempts_threshold,
                "time_window": "1 minute",
            }
        
        # Check user-based attempts if email provided
        if email:
            user_attempts = self._user_attempts[email]
            recent_user_failures = [
                a for a in user_attempts 
                if a.timestamp > one_minute_ago and not a.success
            ]
            
            if len(recent_user_failures) >= self.rapid_attempts_threshold:
                return {
                    "user_failures_per_minute": len(recent_user_failures),
                    "threshold": self.rapid_attempts_threshold,
                    "time_window": "1 minute",
                }
        
        return None
    
    async def _detect_multiple_ips(self, email: str) -> Optional[Dict[str, Any]]:
        """Detect multiple IPs used by same user within short time"""
        current_time = datetime.now(timezone.utc)
        one_hour_ago = current_time - timedelta(hours=1)
        
        user_attempts = self._user_attempts[email]
        recent_attempts = [a for a in user_attempts if a.timestamp > one_hour_ago]
        
        unique_ips = set(a.ip_address for a in recent_attempts)
        
        if len(unique_ips) >= self.multiple_ip_threshold:
            return {
                "unique_ips_per_hour": len(unique_ips),
                "threshold": self.multiple_ip_threshold,
                "ip_addresses": list(unique_ips),
                "time_window": "1 hour",
            }
        
        return None
    
    async def _detect_unusual_location(
        self, email: str, geolocation: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Detect login from unusual geographic location"""
        if not geolocation or "country" not in geolocation:
            return None
        
        country = geolocation["country"]
        user_locations = self._user_locations[email]
        
        # If user has established location patterns and this is new
        if len(user_locations) >= 3 and country not in user_locations:
            return {
                "new_country": country,
                "known_countries": list(user_locations),
                "is_new_location": True,
            }
        
        # Add location to user's known locations
        user_locations.add(country)
        
        return None
    
    async def _detect_unusual_time(
        self, email: str, timestamp: datetime
    ) -> Optional[Dict[str, Any]]:
        """Detect login at unusual time based on user's historical patterns"""
        hour = timestamp.hour
        user_times = self._user_typical_times[email]
        
        # Need at least 10 historical logins to establish pattern
        if len(user_times) < 10:
            user_times.append(hour)
            return None
        
        # Calculate probability of this hour based on historical data
        hour_count = user_times.count(hour)
        probability = hour_count / len(user_times)
        
        # Add current hour to history
        user_times.append(hour)
        # Keep only last 100 login times
        self._user_typical_times[email] = user_times[-100:]
        
        if probability < self.unusual_time_threshold:
            return {
                "login_hour": hour,
                "probability": probability,
                "threshold": self.unusual_time_threshold,
                "is_unusual_time": True,
            }
        
        return None
    
    async def _detect_brute_force_pattern(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Detect brute force attack patterns from IP"""
        current_time = datetime.now(timezone.utc)
        one_hour_ago = current_time - timedelta(hours=1)
        
        ip_attempts = self._ip_attempts[ip_address]
        recent_attempts = [a for a in ip_attempts if a.timestamp > one_hour_ago]
        
        if len(recent_attempts) < 20:  # Need significant volume
            return None
        
        # Check for patterns indicating brute force
        failed_attempts = [a for a in recent_attempts if not a.success]
        unique_emails = set(a.email for a in recent_attempts if a.email)
        
        # High failure rate + multiple different emails = likely brute force
        failure_rate = len(failed_attempts) / len(recent_attempts)
        
        if failure_rate > 0.8 and len(unique_emails) > 5:
            return {
                "total_attempts": len(recent_attempts),
                "failed_attempts": len(failed_attempts),
                "failure_rate": failure_rate,
                "unique_emails_targeted": len(unique_emails),
                "time_window": "1 hour",
            }
        
        return None
    
    async def _detect_account_enumeration(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Detect account enumeration attempts"""
        current_time = datetime.now(timezone.utc)
        one_hour_ago = current_time - timedelta(hours=1)
        
        ip_attempts = self._ip_attempts[ip_address]
        recent_attempts = [a for a in ip_attempts if a.timestamp > one_hour_ago]
        
        # Look for many "user not found" errors
        user_not_found_attempts = [
            a for a in recent_attempts 
            if not a.success and a.failure_reason == "user_not_found"
        ]
        
        if len(user_not_found_attempts) >= 10:
            unique_emails = set(a.email for a in user_not_found_attempts if a.email)
            return {
                "user_not_found_attempts": len(user_not_found_attempts),
                "unique_emails_tested": len(unique_emails),
                "time_window": "1 hour",
            }
        
        return None


class SecurityAlertManager:
    """
    Manages security alerts and notifications
    """
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Alert storage
        self._alerts: List[SecurityAlert] = []
        self._alert_handlers: List[callable] = []
        
    def add_alert_handler(self, handler: callable) -> None:
        """Add a custom alert handler function"""
        self._alert_handlers.append(handler)
    
    async def create_alert(
        self,
        alert_type: str,
        threat_level: ThreatLevel,
        source_ip: str,
        description: str,
        user_email: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> SecurityAlert:
        """Create and process a new security alert"""
        alert = SecurityAlert(
            alert_id=f"alert_{int(time.time())}_{len(self._alerts)}",
            alert_type=alert_type,
            threat_level=threat_level,
            timestamp=datetime.now(timezone.utc),
            source_ip=source_ip,
            user_email=user_email,
            user_id=user_id,
            description=description,
            details=details or {},
        )
        
        # Store alert
        self._alerts.append(alert)
        
        # Log alert
        self.logger.warning(
            f"Security alert created: {alert_type}",
            extra={
                "alert_id": alert.alert_id,
                "threat_level": threat_level.value,
                "source_ip": source_ip,
                "user_email": user_email,
                "description": description,
                "details": details,
            }
        )
        
        # Notify handlers
        for handler in self._alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler failed: {e}")
        
        return alert
    
    async def create_failed_attempt_alert(
        self,
        ip_address: str,
        email: Optional[str],
        attempt_count: int,
        time_window: str,
    ) -> SecurityAlert:
        """Create alert for excessive failed authentication attempts"""
        threat_level = ThreatLevel.HIGH if attempt_count > 20 else ThreatLevel.MEDIUM
        
        return await self.create_alert(
            alert_type="excessive_failed_attempts",
            threat_level=threat_level,
            source_ip=ip_address,
            user_email=email,
            description=f"Excessive failed authentication attempts detected",
            details={
                "attempt_count": attempt_count,
                "time_window": time_window,
                "ip_address": ip_address,
                "email": email,
            }
        )
    
    async def create_anomaly_alert(
        self,
        ip_address: str,
        suspicious_activity: SuspiciousActivity,
        email: Optional[str] = None,
    ) -> SecurityAlert:
        """Create alert for detected anomalies"""
        # Determine threat level based on risk score
        if suspicious_activity.risk_score >= 0.8:
            threat_level = ThreatLevel.CRITICAL
        elif suspicious_activity.risk_score >= 0.6:
            threat_level = ThreatLevel.HIGH
        elif suspicious_activity.risk_score >= 0.4:
            threat_level = ThreatLevel.MEDIUM
        else:
            threat_level = ThreatLevel.LOW
        
        anomaly_names = [anomaly.value for anomaly in suspicious_activity.anomaly_types]
        
        return await self.create_alert(
            alert_type="authentication_anomaly",
            threat_level=threat_level,
            source_ip=ip_address,
            user_email=email,
            description=f"Authentication anomaly detected: {', '.join(anomaly_names)}",
            details={
                "anomaly_types": anomaly_names,
                "risk_score": suspicious_activity.risk_score,
                "confidence": suspicious_activity.confidence,
                "analysis_details": suspicious_activity.details,
            }
        )
    
    def get_recent_alerts(
        self, 
        hours: int = 24,
        threat_level: Optional[ThreatLevel] = None
    ) -> List[SecurityAlert]:
        """Get recent alerts, optionally filtered by threat level"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        alerts = [a for a in self._alerts if a.timestamp > cutoff_time]
        
        if threat_level:
            alerts = [a for a in alerts if a.threat_level == threat_level]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def get_alert_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics for monitoring dashboard"""
        recent_alerts = self.get_recent_alerts(hours)
        
        stats = {
            "total_alerts": len(recent_alerts),
            "by_threat_level": {level.value: 0 for level in ThreatLevel},
            "by_alert_type": defaultdict(int),
            "unique_source_ips": set(),
            "affected_users": set(),
        }
        
        for alert in recent_alerts:
            stats["by_threat_level"][alert.threat_level.value] += 1
            stats["by_alert_type"][alert.alert_type] += 1
            stats["unique_source_ips"].add(alert.source_ip)
            if alert.user_email:
                stats["affected_users"].add(alert.user_email)
        
        stats["unique_source_ips"] = len(stats["unique_source_ips"])
        stats["affected_users"] = len(stats["affected_users"])
        stats["by_alert_type"] = dict(stats["by_alert_type"])
        
        return stats


class EnhancedSecurityMonitor:
    """
    Main security monitoring service that orchestrates all security components
    """
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.rate_limiter = ExponentialBackoffRateLimiter(config)
        self.activity_detector = SuspiciousActivityDetector(config)
        self.alert_manager = SecurityAlertManager(config)
        
        # Enable/disable features based on config
        self.enable_rate_limiting = getattr(config.security, 'enable_rate_limiting', True)
        self.enable_anomaly_detection = getattr(config.security, 'enable_anomaly_detection', True)
        self.enable_security_alerts = getattr(config.security, 'enable_security_alerts', True)
    
    async def check_authentication_security(
        self,
        ip_address: str,
        user_agent: str,
        email: Optional[str] = None,
        endpoint: str = "auth",
        geolocation: Optional[Dict[str, Any]] = None,
        device_fingerprint: Optional[str] = None,
    ) -> None:
        """
        Comprehensive security check before authentication attempt
        
        Raises:
            RateLimitExceededError: If rate limit is exceeded
            SuspiciousActivityError: If suspicious activity is detected
            AnomalyDetectedError: If anomalies are detected
        """
        # 1. Rate limiting check
        if self.enable_rate_limiting:
            await self.rate_limiter.check_rate_limit(ip_address, email, endpoint)
        
        # 2. Suspicious activity analysis (pre-attempt)
        if self.enable_anomaly_detection:
            suspicious_activity = await self.activity_detector.analyze_attempt(
                ip_address=ip_address,
                user_agent=user_agent,
                email=email,
                success=False,  # Pre-attempt analysis
                geolocation=geolocation,
                device_fingerprint=device_fingerprint,
            )
            
            if suspicious_activity.is_suspicious and suspicious_activity.risk_score > 0.7:
                # Create alert for high-risk activity
                if self.enable_security_alerts:
                    await self.alert_manager.create_anomaly_alert(
                        ip_address, suspicious_activity, email
                    )
                
                raise AnomalyDetectedError(
                    message="Authentication blocked due to suspicious activity",
                    anomaly_types=[a.value for a in suspicious_activity.anomaly_types],
                    risk_score=suspicious_activity.risk_score,
                    confidence=suspicious_activity.confidence,
                    details=suspicious_activity.details,
                )
    
    async def record_authentication_result(
        self,
        ip_address: str,
        user_agent: str,
        success: bool,
        email: Optional[str] = None,
        failure_reason: Optional[str] = None,
        geolocation: Optional[Dict[str, Any]] = None,
        device_fingerprint: Optional[str] = None,
    ) -> None:
        """
        Record authentication result and perform post-attempt analysis
        """
        # 1. Record attempt for rate limiting
        if self.enable_rate_limiting:
            await self.rate_limiter.record_attempt(ip_address, email, success)
        
        # 2. Analyze attempt for suspicious patterns
        if self.enable_anomaly_detection:
            suspicious_activity = await self.activity_detector.analyze_attempt(
                ip_address=ip_address,
                user_agent=user_agent,
                email=email,
                success=success,
                failure_reason=failure_reason,
                geolocation=geolocation,
                device_fingerprint=device_fingerprint,
            )
            
            # Create alerts for suspicious activity
            if self.enable_security_alerts and suspicious_activity.is_suspicious:
                await self.alert_manager.create_anomaly_alert(
                    ip_address, suspicious_activity, email
                )
        
        # 3. Create alerts for failed attempts
        if not success and self.enable_security_alerts:
            # Check if this IP has excessive failed attempts
            current_time = datetime.now(timezone.utc)
            one_hour_ago = current_time - timedelta(hours=1)
            
            ip_attempts = self.activity_detector._ip_attempts[ip_address]
            recent_failures = [
                a for a in ip_attempts 
                if a.timestamp > one_hour_ago and not a.success
            ]
            
            if len(recent_failures) >= 10:  # Threshold for alert
                await self.alert_manager.create_failed_attempt_alert(
                    ip_address, email, len(recent_failures), "1 hour"
                )
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get comprehensive security statistics"""
        return {
            "alerts": self.alert_manager.get_alert_stats(),
            "rate_limiting": {
                "enabled": self.enable_rate_limiting,
                "active_lockouts": len(self.rate_limiter._lockout_until),
            },
            "anomaly_detection": {
                "enabled": self.enable_anomaly_detection,
                "monitored_users": len(self.activity_detector._user_attempts),
                "monitored_ips": len(self.activity_detector._ip_attempts),
            },
        }