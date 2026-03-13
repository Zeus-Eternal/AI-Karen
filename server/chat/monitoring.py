"""
Security monitoring for the AI-Karen production chat system.
Provides real-time monitoring, alerting, and audit trail functionality.
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import time

from .security import SecurityEvent, ThreatLevel, get_security_monitor

logger = logging.getLogger(__name__)


class AlertStatus(Enum):
    """Alert status enumeration."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class MetricType(Enum):
    """Types of metrics to monitor."""
    REQUEST_COUNT = "request_count"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    AUTH_FAILURES = "auth_failures"
    RATE_LIMIT_VIOLATIONS = "rate_limit_violations"
    ACTIVE_USERS = "active_users"
    MESSAGE_VOLUME = "message_volume"
    PROVIDER_HEALTH = "provider_health"


@dataclass
class SecurityAlert:
    """Security alert data structure."""
    id: str
    timestamp: datetime
    alert_type: str
    severity: ThreatLevel
    status: AlertStatus
    title: str
    description: str
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


@dataclass
class SystemMetric:
    """System metric data structure."""
    timestamp: datetime
    metric_type: MetricType
    value: float
    unit: str
    tags: Optional[Dict[str, str]] = None


@dataclass
class ChatSessionMetrics:
    """Chat session metrics."""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    message_count: int = 0
    provider_used: Optional[str] = None
    total_response_time: float = 0.0
    error_count: int = 0
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class ChatMonitoringService:
    """Main monitoring service for chat security and performance."""
    
    def __init__(self):
        self.security_monitor = get_security_monitor()
        self.alerts: List[SecurityAlert] = []
        self.metrics: List[SystemMetric] = []
        self.active_sessions: Dict[str, ChatSessionMetrics] = {}
        self.alert_handlers: List[Callable] = []
        self.metric_handlers: List[Callable] = []
        
        # Monitoring thresholds
        self.thresholds = {
            "auth_failure_rate": 0.05,  # 5%
            "error_rate": 0.1,        # 10%
            "response_time_ms": 5000,     # 5 seconds
            "message_rate_per_minute": 100,
            "concurrent_sessions_per_user": 5,
            "provider_failure_rate": 0.2   # 20%
        }
        
        # Alert suppression rules
        self.suppression_rules = {
            "same_ip_same_alert": {
                "window_minutes": 5,
                "max_alerts": 3
            },
            "same_user_same_alert": {
                "window_minutes": 10,
                "max_alerts": 5
            }
        }
    
    async def start_monitoring(self):
        """Start the monitoring service."""
        logger.info("Starting chat monitoring service")
        
        # Start background tasks
        asyncio.create_task(self._metric_collection_loop())
        asyncio.create_task(self._alert_processing_loop())
        asyncio.create_task(self._session_cleanup_loop())
    
    def register_alert_handler(self, handler: Callable):
        """Register a handler for security alerts."""
        self.alert_handlers.append(handler)
    
    def register_metric_handler(self, handler: Callable):
        """Register a handler for system metrics."""
        self.metric_handlers.append(handler)
    
    async def log_security_event(self, event: SecurityEvent):
        """Log a security event and potentially create an alert."""
        # Log to security monitor
        self.security_monitor.log_event(event)
        
        # Check if this event should trigger an alert
        alert = await self._evaluate_event_for_alert(event)
        if alert:
            await self._create_alert(alert)
    
    async def record_metric(self, metric_type: MetricType, value: float, unit: str = "", tags: Optional[Dict[str, str]] = None):
        """Record a system metric."""
        metric = SystemMetric(
            timestamp=datetime.utcnow(),
            metric_type=metric_type,
            value=value,
            unit=unit,
            tags=tags or {}
        )
        
        self.metrics.append(metric)
        
        # Keep only last 10000 metrics in memory
        if len(self.metrics) > 10000:
            self.metrics = self.metrics[-10000:]
        
        # Notify metric handlers
        for handler in self.metric_handlers:
            try:
                await handler(metric)
            except Exception as e:
                logger.error(f"Metric handler error: {e}")
    
    async def start_session(self, session_id: str, user_id: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        """Start tracking a chat session."""
        # Check for concurrent session limit
        user_sessions = [
            s for s in self.active_sessions.values()
            if s.user_id == user_id and s.end_time is None
        ]
        
        if len(user_sessions) >= self.thresholds["concurrent_sessions_per_user"]:
            await self.log_security_event(SecurityEvent(
                timestamp=datetime.utcnow(),
                event_type="concurrent_session_limit_exceeded",
                threat_level=ThreatLevel.MEDIUM,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details={
                    "session_count": len(user_sessions),
                    "limit": self.thresholds["concurrent_sessions_per_user"]
                }
            ))
        
        # Create new session
        session = ChatSessionMetrics(
            session_id=session_id,
            user_id=user_id,
            start_time=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.active_sessions[session_id] = session
        
        # Record session start metric
        await self.record_metric(
            MetricType.ACTIVE_USERS,
            len([s for s in self.active_sessions.values() if s.end_time is None]),
            "count"
        )
    
    async def update_session(self, session_id: str, message_count: int = 0, response_time: float = 0.0, 
                           error_count: int = 0, provider_used: Optional[str] = None):
        """Update session metrics."""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        session.message_count += message_count
        session.total_response_time += response_time
        session.error_count += error_count
        
        if provider_used:
            session.provider_used = provider_used
        
        # Record message volume metric
        if message_count > 0:
            await self.record_metric(
                MetricType.MESSAGE_VOLUME,
                message_count,
                "count",
                {"user_id": session.user_id}
            )
        
        # Record response time metric
        if response_time > 0:
            await self.record_metric(
                MetricType.RESPONSE_TIME,
                response_time,
                "ms",
                {"user_id": session.user_id, "provider": provider_used or ""}
            )
        
        # Record error rate metric
        if error_count > 0:
            await self.record_metric(
                MetricType.ERROR_RATE,
                error_count / max(1, session.message_count),
                "ratio",
                {"user_id": session.user_id}
            )
    
    async def end_session(self, session_id: str):
        """End tracking a chat session."""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        session.end_time = datetime.utcnow()
        
        # Calculate session duration
        duration = (session.end_time - session.start_time).total_seconds()
        
        # Record session metrics
        await self.record_metric(
            MetricType.ACTIVE_USERS,
            len([s for s in self.active_sessions.values() if s.end_time is None]),
            "count"
        )
        
        logger.info(f"Session ended: {session_id}, duration: {duration}s, messages: {session.message_count}")
    
    async def _evaluate_event_for_alert(self, event: SecurityEvent) -> Optional[SecurityAlert]:
        """Evaluate if a security event should trigger an alert."""
        alert_type_mapping = {
            "authentication_failed": self._check_auth_failure_alert,
            "brute_force_detected": self._check_brute_force_alert,
            "rate_limit_exceeded": self._check_rate_limit_alert,
            "suspicious_content": self._check_content_alert,
            "unauthorized_access": self._check_unauthorized_alert,
            "concurrent_session_limit_exceeded": self._check_session_limit_alert
        }
        
        alert_handler = alert_type_mapping.get(event.event_type)
        if alert_handler:
            return await alert_handler(event)
        
        return None
    
    async def _check_auth_failure_alert(self, event: SecurityEvent) -> Optional[SecurityAlert]:
        """Check if auth failure should trigger alert."""
        # Count recent auth failures
        recent_failures = [
            e for e in self.security_monitor.events
            if (e.event_type == "authentication_failed" and 
                e.user_id == event.user_id and
                (datetime.utcnow() - e.timestamp).total_seconds() < 300)  # 5 minutes
        ]
        
        if len(recent_failures) >= 5:
            return SecurityAlert(
                id=self._generate_alert_id(),
                timestamp=datetime.utcnow(),
                alert_type="multiple_auth_failures",
                severity=ThreatLevel.HIGH,
                status=AlertStatus.ACTIVE,
                title="Multiple Authentication Failures",
                description=f"User {event.user_id} has {len(recent_failures)} failed authentication attempts in 5 minutes",
                user_id=event.user_id,
                source_ip=event.ip_address,
                metadata={"failure_count": len(recent_failures)}
            )
        
        return None
    
    async def _check_brute_force_alert(self, event: SecurityEvent) -> Optional[SecurityAlert]:
        """Check if brute force should trigger alert."""
        return SecurityAlert(
            id=self._generate_alert_id(),
            timestamp=datetime.utcnow(),
            alert_type="brute_force_attack",
            severity=ThreatLevel.CRITICAL,
            status=AlertStatus.ACTIVE,
            title="Brute Force Attack Detected",
            description=f"Brute force attack detected from IP {event.ip_address}",
            source_ip=event.ip_address,
            metadata=event.details
        )
    
    async def _check_rate_limit_alert(self, event: SecurityEvent) -> Optional[SecurityAlert]:
        """Check if rate limit violation should trigger alert."""
        return SecurityAlert(
            id=self._generate_alert_id(),
            timestamp=datetime.utcnow(),
            alert_type="rate_limit_violation",
            severity=ThreatLevel.MEDIUM,
            status=AlertStatus.ACTIVE,
            title="Rate Limit Violation",
            description=f"Rate limit exceeded by {event.ip_address}",
            source_ip=event.ip_address,
            metadata=event.details
        )
    
    async def _check_content_alert(self, event: SecurityEvent) -> Optional[SecurityAlert]:
        """Check if suspicious content should trigger alert."""
        return SecurityAlert(
            id=self._generate_alert_id(),
            timestamp=datetime.utcnow(),
            alert_type="suspicious_content_detected",
            severity=ThreatLevel.MEDIUM,
            status=AlertStatus.ACTIVE,
            title="Suspicious Content Detected",
            description=f"Suspicious content detected from user {event.user_id}",
            user_id=event.user_id,
            source_ip=event.ip_address,
            metadata=event.details
        )
    
    async def _check_unauthorized_alert(self, event: SecurityEvent) -> Optional[SecurityAlert]:
        """Check if unauthorized access should trigger alert."""
        return SecurityAlert(
            id=self._generate_alert_id(),
            timestamp=datetime.utcnow(),
            alert_type="unauthorized_access_attempt",
            severity=ThreatLevel.HIGH,
            status=AlertStatus.ACTIVE,
            title="Unauthorized Access Attempt",
            description=f"Unauthorized access attempt from {event.ip_address}",
            source_ip=event.ip_address,
            metadata=event.details
        )
    
    async def _check_session_limit_alert(self, event: SecurityEvent) -> Optional[SecurityAlert]:
        """Check if session limit should trigger alert."""
        return SecurityAlert(
            id=self._generate_alert_id(),
            timestamp=datetime.utcnow(),
            alert_type="concurrent_session_limit",
            severity=ThreatLevel.MEDIUM,
            status=AlertStatus.ACTIVE,
            title="Concurrent Session Limit Exceeded",
            description=f"User {event.user_id} exceeded concurrent session limit",
            user_id=event.user_id,
            source_ip=event.ip_address,
            metadata=event.details
        )
    
    async def _create_alert(self, alert: SecurityAlert):
        """Create and process a security alert."""
        # Check suppression rules
        if await self._is_alert_suppressed(alert):
            logger.info(f"Alert suppressed: {alert.alert_type}")
            return
        
        # Add to alerts list
        self.alerts.append(alert)
        
        # Keep only last 1000 alerts
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
        
        # Notify alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
        
        logger.warning(f"Security alert created: {alert.title} - {alert.description}")
    
    async def _is_alert_suppressed(self, alert: SecurityAlert) -> bool:
        """Check if an alert should be suppressed."""
        current_time = datetime.utcnow()
        
        # Check same IP suppression
        if alert.source_ip:
            recent_ip_alerts = [
                a for a in self.alerts
                if (a.source_ip == alert.source_ip and 
                    a.alert_type == alert.alert_type and
                    a.status == AlertStatus.ACTIVE and
                    (current_time - a.timestamp).total_seconds() < 300)  # 5 minutes
            ]
            
            if len(recent_ip_alerts) >= self.suppression_rules["same_ip_same_alert"]["max_alerts"]:
                return True
        
        # Check same user suppression
        if alert.user_id:
            recent_user_alerts = [
                a for a in self.alerts
                if (a.user_id == alert.user_id and 
                    a.alert_type == alert.alert_type and
                    a.status == AlertStatus.ACTIVE and
                    (current_time - a.timestamp).total_seconds() < 600)  # 10 minutes
            ]
            
            if len(recent_user_alerts) >= self.suppression_rules["same_user_same_alert"]["max_alerts"]:
                return True
        
        return False
    
    async def _metric_collection_loop(self):
        """Background task to collect system metrics."""
        while True:
            try:
                # Collect active user count
                active_users = len([
                    s for s in self.active_sessions.values() 
                    if s.end_time is None
                ])
                await self.record_metric(MetricType.ACTIVE_USERS, active_users, "count")
                
                # Collect error rate
                recent_metrics = [
                    m for m in self.metrics
                    if (m.metric_type == MetricType.ERROR_RATE and
                        (datetime.utcnow() - m.timestamp).total_seconds() < 300)  # 5 minutes
                ]
                
                if recent_metrics:
                    avg_error_rate = sum(m.value for m in recent_metrics) / len(recent_metrics)
                    await self.record_metric(MetricType.ERROR_RATE, avg_error_rate, "ratio")
                
                # Wait before next collection
                await asyncio.sleep(60)  # Collect every minute
                
            except Exception as e:
                logger.error(f"Metric collection error: {e}")
                await asyncio.sleep(60)
    
    async def _alert_processing_loop(self):
        """Background task to process and resolve alerts."""
        while True:
            try:
                current_time = datetime.utcnow()
                
                # Auto-resolve old alerts
                for alert in self.alerts:
                    if (alert.status == AlertStatus.ACTIVE and
                        (current_time - alert.timestamp).total_seconds() > 3600):  # 1 hour
                        alert.status = AlertStatus.RESOLVED
                        alert.resolved_at = current_time
                        alert.resolved_by = "auto_resolve"
                
                await asyncio.sleep(300)  # Process every 5 minutes
                
            except Exception as e:
                logger.error(f"Alert processing error: {e}")
                await asyncio.sleep(300)
    
    async def _session_cleanup_loop(self):
        """Background task to clean up old sessions."""
        while True:
            try:
                current_time = datetime.utcnow()
                
                # Clean up sessions inactive for more than 1 hour
                for session_id, session in list(self.active_sessions.items()):
                    if (session.end_time is None and
                        (current_time - session.start_time).total_seconds() > 3600):
                        
                        session.end_time = current_time
                        logger.info(f"Session cleaned up due to inactivity: {session_id}")
                
                await asyncio.sleep(600)  # Clean up every 10 minutes
                
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
                await asyncio.sleep(600)
    
    def _generate_alert_id(self) -> str:
        """Generate a unique alert ID."""
        return f"alert_{int(time.time() * 1000)}_{hash(str(time.time())) % 10000}"
    
    def get_alerts(self, limit: int = 100, status: Optional[AlertStatus] = None, 
                  severity: Optional[ThreatLevel] = None) -> List[SecurityAlert]:
        """Get security alerts with optional filtering."""
        alerts = self.alerts
        
        if status:
            alerts = [a for a in alerts if a.status == status]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return alerts[-limit:]
    
    def get_metrics(self, metric_type: Optional[MetricType] = None, hours: int = 24) -> List[SystemMetric]:
        """Get system metrics with optional filtering."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        metrics = [
            m for m in self.metrics
            if m.timestamp > cutoff_time
        ]
        
        if metric_type:
            metrics = [m for m in metrics if m.metric_type == metric_type]
        
        return metrics
    
    def get_active_sessions(self, user_id: Optional[str] = None) -> List[ChatSessionMetrics]:
        """Get active chat sessions."""
        sessions = [
            s for s in self.active_sessions.values()
            if s.end_time is None
        ]
        
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        
        return sessions
    
    def get_session_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get session summary for the specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get sessions from the time period
        all_sessions = list(self.active_sessions.values())
        
        recent_sessions = [
            s for s in all_sessions
            if s.start_time > cutoff_time or (s.end_time and s.end_time > cutoff_time)
        ]
        
        # Calculate statistics
        total_sessions = len(recent_sessions)
        active_sessions = len([s for s in recent_sessions if s.end_time is None])
        completed_sessions = len([s for s in recent_sessions if s.end_time])
        
        total_messages = sum(s.message_count for s in recent_sessions)
        total_errors = sum(s.error_count for s in recent_sessions)
        
        avg_response_time = 0
        sessions_with_response = [s for s in recent_sessions if s.total_response_time > 0 and s.message_count > 0]
        if sessions_with_response:
            avg_response_time = sum(
                s.total_response_time / s.message_count for s in sessions_with_response
            ) / len(sessions_with_response)
        
        # Provider usage
        provider_usage = {}
        for s in recent_sessions:
            if s.provider_used:
                provider_usage[s.provider_used] = provider_usage.get(s.provider_used, 0) + 1
        
        return {
            "timeframe_hours": hours,
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "completed_sessions": completed_sessions,
            "total_messages": total_messages,
            "total_errors": total_errors,
            "error_rate": total_errors / max(1, total_messages),
            "avg_response_time_ms": avg_response_time,
            "provider_usage": provider_usage,
            "unique_users": len(set(s.user_id for s in recent_sessions))
        }


# Global monitoring service instance
monitoring_service = ChatMonitoringService()


def get_chat_monitoring_service() -> ChatMonitoringService:
    """Get the global chat monitoring service."""
    return monitoring_service


# Utility functions
async def log_security_event(event_type: str, details: Dict[str, Any],
                          user_id: Optional[str] = None, ip_address: Optional[str] = None,
                          threat_level: ThreatLevel = ThreatLevel.MEDIUM):
    """Log a security event using the monitoring service."""
    event = SecurityEvent(
        timestamp=datetime.utcnow(),
        event_type=event_type,
        threat_level=threat_level,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=None,
        details=details
    )
    
    await monitoring_service.log_security_event(event)


async def record_chat_metric(metric_type: MetricType, value: float, unit: str = "", tags: Optional[Dict[str, str]] = None):
    """Record a chat metric using the monitoring service."""
    await monitoring_service.record_metric(metric_type, value, unit, tags)


async def start_chat_session(session_id: str, user_id: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None):
    """Start tracking a chat session."""
    await monitoring_service.start_session(session_id, user_id, ip_address, user_agent)


async def update_chat_session(session_id: str, message_count: int = 0, response_time: float = 0.0, 
                           error_count: int = 0, provider_used: Optional[str] = None):
    """Update chat session metrics."""
    await monitoring_service.update_session(session_id, message_count, response_time, error_count, provider_used)


async def end_chat_session(session_id: str):
    """End tracking a chat session."""
    await monitoring_service.end_session(session_id)