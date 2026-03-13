"""
Security Monitoring and Threat Detection Service.

This service provides comprehensive security monitoring capabilities including:
- Real-time threat detection
- Anomaly detection
- Security incident management
- Behavioral analysis
- Risk assessment
"""

import asyncio
import json
import secrets
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select, update, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ai_karen_engine.core.services.base import BaseService, ServiceConfig
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.services.audit_logging import (
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    get_audit_logger,
)
from .auth_service import ThreatLevel


@dataclass
class SecurityEvent:
    """Security event data structure."""
    event_id: str
    event_type: str
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    threat_level: ThreatLevel = ThreatLevel.LOW
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_notes: str = ""

logger = get_logger(__name__)


class ThreatType(str, Enum):
    """Security threat types."""
    BRUTE_FORCE = "brute_force"
    INJECTION_ATTACK = "injection_attack"
    XSS_ATTACK = "xss_attack"
    CSRF_ATTACK = "csrf_attack"
    DOS_ATTACK = "dos_attack"
    SUSPICIOUS_LOGIN = "suspicious_login"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    MALICIOUS_PAYLOAD = "malicious_payload"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    SUSPICIOUS_IP = "suspicious_ip"
    SUSPICIOUS_USER_AGENT = "suspicious_user_agent"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    FAILED_MFA = "failed_mfa"
    DEVICE_ANOMALY = "device_anomaly"


class IncidentStatus(str, Enum):
    """Security incident status."""
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"


class AlertSeverity(str, Enum):
    """Security alert severity levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityIncident:
    """Security incident data structure."""
    incident_id: str
    threat_type: ThreatType
    severity: AlertSeverity
    title: str
    description: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    detected_by: str = "system"
    status: IncidentStatus = IncidentStatus.OPEN
    risk_score: float = 0.0
    confidence: float = 0.0
    indicators: List[str] = field(default_factory=list)
    affected_assets: List[str] = field(default_factory=list)
    containment_actions: List[str] = field(default_factory=list)
    resolution_notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThreatIndicator:
    """Threat indicator data structure."""
    indicator_id: str
    indicator_type: ThreatType
    pattern: str
    severity: AlertSeverity
    description: str
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    detection_count: int = 0
    false_positive_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BehavioralProfile:
    """User behavioral profile for anomaly detection."""
    user_id: str
    typical_login_times: List[float] = field(default_factory=list)
    typical_ip_addresses: List[str] = field(default_factory=list)
    typical_user_agents: List[str] = field(default_factory=list)
    typical_request_patterns: Dict[str, float] = field(default_factory=dict)
    typical_session_durations: List[float] = field(default_factory=list)
    typical_api_usage: Dict[str, int] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    anomaly_threshold: float = 2.0  # Standard deviations


@dataclass
class SecurityMonitoringConfig(ServiceConfig):
    """Security monitoring service configuration."""
    # Detection settings
    enable_threat_detection: bool = True
    enable_anomaly_detection: bool = True
    enable_behavioral_analysis: bool = True
    enable_real_time_monitoring: bool = True
    
    # Threshold settings
    failed_login_threshold: int = 5
    failed_login_window_minutes: int = 15
    suspicious_ip_threshold: int = 3
    suspicious_user_agent_threshold: int = 5
    rate_limit_threshold: int = 100
    rate_limit_window_minutes: int = 5
    
    # Anomaly detection settings
    anomaly_detection_window_hours: int = 24
    anomaly_threshold_std_dev: float = 2.0
    min_baseline_samples: int = 10
    
    # Incident management
    auto_incident_creation: bool = True
    incident_escalation_hours: int = 2
    incident_auto_closure_hours: int = 24
    
    # Alert settings
    enable_email_alerts: bool = True
    enable_sms_alerts: bool = False
    enable_webhook_alerts: bool = False
    webhook_url: str = ""
    alert_recipients: List[str] = field(default_factory=list)
    
    # Data retention
    incident_retention_days: int = 365
    indicator_retention_days: int = 90
    log_retention_days: int = 30
    
    def __post_init__(self):
        """Initialize ServiceConfig fields."""
        if not hasattr(self, 'name') or not self.name:
            self.name = "security_monitoring_service"
        if not hasattr(self, 'version') or not self.version:
            self.version = "1.0.0"


class ThreatDetector:
    """Threat detection engine."""
    
    def __init__(self, config: SecurityMonitoringConfig):
        """Initialize threat detector."""
        self.config = config
        self._threat_indicators: Dict[str, ThreatIndicator] = {}
        self._load_default_indicators()
    
    def _load_default_indicators(self) -> None:
        """Load default threat indicators."""
        default_indicators = [
            ThreatIndicator(
                indicator_id="sql_injection_1",
                indicator_type=ThreatType.INJECTION_ATTACK,
                pattern=r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b.*\b(FROM|INTO)\b",
                severity=AlertSeverity.HIGH,
                description="SQL injection attempt detected"
            ),
            ThreatIndicator(
                indicator_id="xss_1",
                indicator_type=ThreatType.XSS_ATTACK,
                pattern=r"<script[^>]*>.*?</script>",
                severity=AlertSeverity.HIGH,
                description="XSS attempt detected"
            ),
            ThreatIndicator(
                indicator_id="brute_force_1",
                indicator_type=ThreatType.BRUTE_FORCE,
                pattern=r"^(?=.*[a-zA-Z])(?=.*[0-9])(?=.*[!@#$%^&*]).{8,}$",
                severity=AlertSeverity.MEDIUM,
                description="Potential brute force attempt"
            ),
            ThreatIndicator(
                indicator_id="malicious_payload_1",
                indicator_type=ThreatType.MALICIOUS_PAYLOAD,
                pattern=r"<(iframe|object|embed|script).*>",
                severity=AlertSeverity.CRITICAL,
                description="Malicious payload detected"
            ),
        ]
        
        for indicator in default_indicators:
            self._threat_indicators[indicator.indicator_id] = indicator
    
    def detect_threats(self, data: Dict[str, Any]) -> List[ThreatIndicator]:
        """
        Detect threats in provided data.
        
        Args:
            data: Data to analyze (request data, logs, etc.)
            
        Returns:
            List of detected threat indicators
        """
        detected_threats = []
        
        # Convert data to string for pattern matching
        data_str = json.dumps(data, default=str)
        
        for indicator in self._threat_indicators.values():
            if not indicator.is_active:
                continue
            
            import re
            if re.search(indicator.pattern, data_str, re.IGNORECASE):
                detected_threats.append(indicator)
                indicator.detection_count += 1
        
        return detected_threats
    
    def add_indicator(self, indicator: ThreatIndicator) -> None:
        """Add a custom threat indicator."""
        self._threat_indicators[indicator.indicator_id] = indicator
        logger.info(f"Added threat indicator: {indicator.indicator_id}")
    
    def remove_indicator(self, indicator_id: str) -> bool:
        """Remove a threat indicator."""
        if indicator_id in self._threat_indicators:
            del self._threat_indicators[indicator_id]
            logger.info(f"Removed threat indicator: {indicator_id}")
            return True
        return False


class AnomalyDetector:
    """Anomaly detection engine."""
    
    def __init__(self, config: SecurityMonitoringConfig):
        """Initialize anomaly detector."""
        self.config = config
        self._behavioral_profiles: Dict[str, BehavioralProfile] = {}
    
    def update_behavioral_profile(
        self,
        user_id: str,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Update behavioral profile for a user.
        
        Args:
            user_id: User ID
            event_data: Event data (login time, IP, etc.)
        """
        if user_id not in self._behavioral_profiles:
            self._behavioral_profiles[user_id] = BehavioralProfile(user_id=user_id)
        
        profile = self._behavioral_profiles[user_id]
        
        # Update profile with new data
        if "login_time" in event_data:
            login_time = event_data["login_time"]
            if isinstance(login_time, datetime):
                profile.typical_login_times.append(login_time.timestamp())
        
        if "ip_address" in event_data:
            ip_address = event_data["ip_address"]
            if ip_address not in profile.typical_ip_addresses:
                profile.typical_ip_addresses.append(ip_address)
        
        if "user_agent" in event_data:
            user_agent = event_data["user_agent"]
            if user_agent not in profile.typical_user_agents:
                profile.typical_user_agents.append(user_agent)
        
        if "session_duration" in event_data:
            duration = event_data["session_duration"]
            profile.typical_session_durations.append(float(duration))
        
        if "api_endpoint" in event_data:
            endpoint = event_data["api_endpoint"]
            profile.typical_api_usage[endpoint] = profile.typical_api_usage.get(endpoint, 0) + 1
        
        # Update last updated timestamp
        profile.last_updated = datetime.utcnow()
        
        # Keep only recent data
        max_samples = 100
        if len(profile.typical_login_times) > max_samples:
            profile.typical_login_times = profile.typical_login_times[-max_samples:]
        
        if len(profile.typical_session_durations) > max_samples:
            profile.typical_session_durations = profile.typical_session_durations[-max_samples:]
        
        logger.debug(f"Updated behavioral profile for user {user_id}")
    
    def detect_anomalies(
        self,
        user_id: str,
        event_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], float]:
        """
        Detect anomalies in user behavior.
        
        Args:
            user_id: User ID
            event_data: Current event data
            
        Returns:
            Tuple of (is_anomaly, anomaly_reason, anomaly_score)
        """
        if user_id not in self._behavioral_profiles:
            return False, None, 0.0
        
        profile = self._behavioral_profiles[user_id]
        
        # Check if we have enough baseline data
        if len(profile.typical_login_times) < self.config.min_baseline_samples:
            return False, None, 0.0
        
        anomaly_score = 0.0
        anomaly_reasons = []
        
        # Check login time anomaly
        if "login_time" in event_data:
            login_time = event_data["login_time"]
            if isinstance(login_time, datetime):
                login_timestamp = login_time.timestamp()
                
                if profile.typical_login_times:
                    mean_time = statistics.mean(profile.typical_login_times)
                    std_time = statistics.stdev(profile.typical_login_times) if len(profile.typical_login_times) > 1 else 0
                    
                    z_score = abs(login_timestamp - mean_time) / std_time if std_time > 0 else 0
                    
                    if z_score > self.config.anomaly_threshold_std_dev:
                        anomaly_score += z_score
                        anomaly_reasons.append(f"Unusual login time (z-score: {z_score:.2f})")
        
        # Check IP address anomaly
        if "ip_address" in event_data:
            ip_address = event_data["ip_address"]
            if ip_address not in profile.typical_ip_addresses:
                anomaly_score += 1.0
                anomaly_reasons.append(f"Unusual IP address: {ip_address}")
        
        # Check user agent anomaly
        if "user_agent" in event_data:
            user_agent = event_data["user_agent"]
            if user_agent not in profile.typical_user_agents:
                anomaly_score += 0.5
                anomaly_reasons.append(f"Unusual user agent: {user_agent}")
        
        # Check session duration anomaly
        if "session_duration" in event_data:
            duration = float(event_data["session_duration"])
            if profile.typical_session_durations:
                mean_duration = statistics.mean(profile.typical_session_durations)
                std_duration = statistics.stdev(profile.typical_session_durations) if len(profile.typical_session_durations) > 1 else 0
                
                z_score = abs(duration - mean_duration) / std_duration if std_duration > 0 else 0
                
                if z_score > self.config.anomaly_threshold_std_dev:
                    anomaly_score += z_score
                    anomaly_reasons.append(f"Unusual session duration (z-score: {z_score:.2f})")
        
        # Determine if anomaly detected
        is_anomaly = anomaly_score > 0.0
        anomaly_reason = "; ".join(anomaly_reasons) if anomaly_reasons else None
        
        return is_anomaly, anomaly_reason, anomaly_score


class SecurityMonitoringService(BaseService):
    """
    Security Monitoring and Threat Detection Service.
    
    This service provides comprehensive security monitoring capabilities including
    real-time threat detection, anomaly detection, and incident management.
    """
    
    def __init__(self, config: Optional[SecurityMonitoringConfig] = None):
        """Initialize Security Monitoring Service."""
        super().__init__(config or SecurityMonitoringConfig())
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Database session will be injected
        self._db_session: Optional[AsyncSession] = None
        
        # Thread-safe data structures
        self._incidents: Dict[str, SecurityIncident] = {}
        self._threat_indicators: Dict[str, ThreatIndicator] = {}
        self._behavioral_profiles: Dict[str, BehavioralProfile] = {}
        
        # Initialize detectors
        self._threat_detector = ThreatDetector(self.config)
        self._anomaly_detector = AnomalyDetector(self.config)
        
        # Initialize audit logger
        self._audit_logger = get_audit_logger()
    
    async def initialize(self) -> None:
        """Initialize Security Monitoring Service."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Validate configuration
                self._validate_config()
                
                self._initialized = True
                logger.info("Security Monitoring Service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Security Monitoring Service: {e}")
                raise RuntimeError(f"Security Monitoring Service initialization failed: {e}")
    
    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if self.config.failed_login_threshold < 3:
            logger.warning("Failed login threshold should be at least 3")
        
        if self.config.anomaly_threshold_std_dev < 1.0:
            logger.warning("Anomaly threshold should be at least 1.0")
    
    def set_db_session(self, session: AsyncSession) -> None:
        """Set database session for the service."""
        self._db_session = session
    
    async def analyze_security_event(
        self,
        event_data: Dict[str, Any],
        *,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None
    ) -> Tuple[List[ThreatIndicator], Optional[SecurityIncident]]:
        """
        Analyze a security event for threats and anomalies.
        
        Args:
            event_data: Event data to analyze
            user_id: User ID
            ip_address: IP address
            user_agent: User agent string
            device_fingerprint: Device fingerprint
            
        Returns:
            Tuple of (detected_threats, created_incident)
        """
        try:
            # Detect threats
            detected_threats = self._threat_detector.detect_threats(event_data)
            
            # Detect anomalies
            is_anomaly = False
            anomaly_reason = None
            anomaly_score = 0.0
            
            if user_id and self.config.enable_anomaly_detection:
                is_anomaly, anomaly_reason, anomaly_score = self._anomaly_detector.detect_anomalies(user_id, event_data)
            
            # Update behavioral profile
            if user_id and self.config.enable_behavioral_analysis:
                self._anomaly_detector.update_behavioral_profile(user_id, event_data)
            
            # Create security incident if needed
            incident = None
            if self.config.auto_incident_creation and (detected_threats or is_anomaly):
                incident = await self._create_security_incident(
                    detected_threats,
                    is_anomaly,
                    anomaly_reason,
                    anomaly_score,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_fingerprint=device_fingerprint
                )
            
            return detected_threats, incident
            
        except Exception as e:
            logger.error(f"Error analyzing security event: {e}")
            return [], None
    
    async def _create_security_incident(
        self,
        threats: List[ThreatIndicator],
        is_anomaly: bool,
        anomaly_reason: Optional[str],
        anomaly_score: float,
        *,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None
    ) -> SecurityIncident:
        """Create a security incident from detected threats and anomalies."""
        try:
            # Determine incident severity
            severity = AlertSeverity.LOW
            risk_score = 0.0
            
            if threats:
                max_threat_severity = max(
                    AlertSeverity.HIGH if t.severity == AlertSeverity.HIGH else 
                    AlertSeverity.MEDIUM if t.severity == AlertSeverity.MEDIUM else 
                    AlertSeverity.LOW for t in threats
                )
                severity = max_threat_severity
                risk_score = len([t for t in threats if t.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]]) * 2.0 + \
                          len([t for t in threats if t.severity == AlertSeverity.MEDIUM]) * 1.0 + \
                          len([t for t in threats if t.severity == AlertSeverity.LOW]) * 0.5
            
            if is_anomaly:
                severity = max(severity, AlertSeverity.MEDIUM)
                risk_score += anomaly_score
            
            # Create incident
            incident = SecurityIncident(
                incident_id=secrets.token_urlsafe(32),
                threat_type=ThreatType.ANOMALOUS_BEHAVIOR if is_anomaly else threats[0].indicator_type if threats else ThreatType.SUSPICIOUS_LOGIN,
                severity=severity,
                title=f"Security Alert: {severity.value.upper()}",
                description=f"Detected: {', '.join([t.description for t in threats])}" if threats else f"Anomalous behavior detected: {anomaly_reason}",
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                risk_score=risk_score,
                indicators=[t.indicator_id for t in threats],
                affected_assets=["user_account", "system"]
            )
            
            # Store incident
            self._incidents[incident.incident_id] = incident
            
            # Log incident creation
            self._audit_logger.log_audit_event({
                "event_type": AuditEventType.SECURITY_EVENT,
                "severity": "warning" if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL] else "info",
                "message": f"Security incident created: {incident.incident_id}",
                "user_id": user_id,
                "metadata": {
                    "incident_id": incident.incident_id,
                    "threat_type": incident.threat_type.value,
                    "severity": incident.severity.value,
                    "risk_score": incident.risk_score,
                    "threats": [t.indicator_id for t in threats],
                    "anomaly_detected": is_anomaly,
                    "anomaly_reason": anomaly_reason
                }
            })
            
            logger.warning(f"Security incident created: {incident.incident_id}")
            return incident
            
        except Exception as e:
            logger.error(f"Error creating security incident: {e}")
            raise
    
    async def get_incident(self, incident_id: str) -> Optional[SecurityIncident]:
        """
        Get a security incident by ID.
        
        Args:
            incident_id: Incident ID
            
        Returns:
            Security incident or None if not found
        """
        return self._incidents.get(incident_id)
    
    async def get_user_incidents(
        self,
        user_id: str,
        *,
        status: Optional[IncidentStatus] = None,
        limit: int = 50
    ) -> List[SecurityIncident]:
        """
        Get security incidents for a user.
        
        Args:
            user_id: User ID
            status: Optional status filter
            limit: Maximum number of incidents to return
            
        Returns:
            List of security incidents
        """
        incidents = []
        
        for incident in self._incidents.values():
            if incident.user_id == user_id:
                if status is None or incident.status == status:
                    incidents.append(incident)
        
        # Sort by timestamp (newest first) and limit
        incidents.sort(key=lambda x: x.timestamp, reverse=True)
        return incidents[:limit]
    
    async def update_incident_status(
        self,
        incident_id: str,
        status: IncidentStatus,
        *,
        resolution_notes: str = ""
    ) -> bool:
        """
        Update the status of a security incident.
        
        Args:
            incident_id: Incident ID
            status: New status
            resolution_notes: Resolution notes
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            incident = self._incidents.get(incident_id)
            if not incident:
                logger.warning(f"Incident not found: {incident_id}")
                return False
            
            # Update incident
            incident.status = status
            if resolution_notes:
                incident.resolution_notes = resolution_notes
            
            # Update incident in storage
            self._incidents[incident_id] = incident
            
            # Log status update
            self._audit_logger.log_audit_event({
                "event_type": AuditEventType.SECURITY_EVENT,
                "severity": "info",
                "message": f"Security incident status updated: {incident_id} -> {status.value}",
                "user_id": incident.user_id,
                "metadata": {
                    "incident_id": incident_id,
                    "old_status": incident.status.value,
                    "new_status": status.value,
                    "resolution_notes": resolution_notes
                }
            })
            
            logger.info(f"Security incident status updated: {incident_id} -> {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating incident status: {e}")
            return False
    
    async def add_threat_indicator(self, indicator: ThreatIndicator) -> bool:
        """
        Add a custom threat indicator.
        
        Args:
            indicator: Threat indicator to add
            
        Returns:
            True if addition was successful, False otherwise
        """
        try:
            self._threat_detector.add_indicator(indicator)
            
            # Log indicator addition
            self._audit_logger.log_audit_event({
                "event_type": AuditEventType.SECURITY_EVENT,
                "severity": "info",
                "message": f"Threat indicator added: {indicator.indicator_id}",
                "metadata": {
                    "indicator_id": indicator.indicator_id,
                    "indicator_type": indicator.indicator_type.value,
                    "severity": indicator.severity.value
                }
            })
            
            logger.info(f"Threat indicator added: {indicator.indicator_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding threat indicator: {e}")
            return False
    
    async def remove_threat_indicator(self, indicator_id: str) -> bool:
        """
        Remove a threat indicator.
        
        Args:
            indicator_id: Indicator ID to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        try:
            success = self._threat_detector.remove_indicator(indicator_id)
            
            if success:
                # Log indicator removal
                self._audit_logger.log_audit_event({
                    "event_type": AuditEventType.SECURITY_EVENT,
                    "severity": "info",
                    "message": f"Threat indicator removed: {indicator_id}",
                    "metadata": {
                        "indicator_id": indicator_id
                    }
                })
                
                logger.info(f"Threat indicator removed: {indicator_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error removing threat indicator: {e}")
            return False
    
    async def get_threat_indicators(
        self,
        *,
        active_only: bool = True
    ) -> List[ThreatIndicator]:
        """
        Get all threat indicators.
        
        Args:
            active_only: Whether to return only active indicators
            
        Returns:
            List of threat indicators
        """
        indicators = list(self._threat_detector._threat_indicators.values())
        
        if active_only:
            indicators = [i for i in indicators if i.is_active]
        
        return indicators
    
    async def get_security_statistics(self) -> Dict[str, Any]:
        """
        Get security monitoring statistics.
        
        Returns:
            Dictionary with security statistics
        """
        try:
            # Count incidents by status
            status_counts = {}
            for incident in self._incidents.values():
                status = incident.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count incidents by severity
            severity_counts = {}
            for incident in self._incidents.values():
                severity = incident.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count incidents by threat type
            threat_counts = {}
            for incident in self._incidents.values():
                threat_type = incident.threat_type.value
                threat_counts[threat_type] = threat_counts.get(threat_type, 0) + 1
            
            # Calculate average risk score
            if self._incidents:
                avg_risk_score = sum(incident.risk_score for incident in self._incidents.values()) / len(self._incidents)
            else:
                avg_risk_score = 0.0
            
            return {
                "total_incidents": len(self._incidents),
                "incidents_by_status": status_counts,
                "incidents_by_severity": severity_counts,
                "incidents_by_threat_type": threat_counts,
                "average_risk_score": avg_risk_score,
                "active_threat_indicators": len([i for i in self._threat_detector._threat_indicators.values() if i.is_active]),
                "behavioral_profiles": len(self._behavioral_profiles),
                "monitoring_enabled": self.config.enable_real_time_monitoring,
                "anomaly_detection_enabled": self.config.enable_anomaly_detection,
            }
            
        except Exception as e:
            logger.error(f"Error getting security statistics: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """Check the health of the Security Monitoring Service."""
        if not self._initialized:
            return False
        
        try:
            # Test threat detection
            test_data = {"test": "data"}
            threats, _ = await self.analyze_security_event(test_data)
            
            # Test anomaly detection
            is_anomaly, _, _ = self._anomaly_detector.detect_anomalies("test-user", {"test": "data"})
            
            # Test incident creation
            if threats or is_anomaly:
                incident = await self._create_security_incident(
                    threats,
                    is_anomaly,
                    "test anomaly",
                    1.0,
                    user_id="test-user"
                )
                
                if not incident.incident_id:
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Security Monitoring Service health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Security Monitoring Service."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Security Monitoring Service started successfully")
    
    async def stop(self) -> None:
        """Stop the Security Monitoring Service."""
        if not self._initialized:
            return
        
        # Clear data structures
        self._incidents.clear()
        self._threat_indicators.clear()
        self._behavioral_profiles.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Security Monitoring Service stopped successfully")


__all__ = [
    "SecurityMonitoringService",
    "SecurityMonitoringConfig",
    "ThreatDetector",
    "AnomalyDetector",
    "SecurityIncident",
    "ThreatIndicator",
    "BehavioralProfile",
    "ThreatType",
    "IncidentStatus",
    "AlertSeverity",
]