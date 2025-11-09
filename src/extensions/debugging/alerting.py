"""
Extension Alert Manager

Manages alerts and notifications for extension debugging and monitoring
including threshold-based alerts, pattern detection, and notification delivery.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import json

from .models import Alert, AlertSeverity, MetricPoint, ErrorRecord


class AlertRule:
    """Defines a rule for generating alerts."""
    
    def __init__(
        self,
        rule_id: str,
        name: str,
        condition: Callable[[Any], bool],
        severity: AlertSeverity,
        message_template: str,
        cooldown_minutes: int = 5,
        enabled: bool = True
    ):
        self.rule_id = rule_id
        self.name = name
        self.condition = condition
        self.severity = severity
        self.message_template = message_template
        self.cooldown_minutes = cooldown_minutes
        self.enabled = enabled
        self.last_triggered: Optional[datetime] = None


class NotificationChannel:
    """Base class for notification channels."""
    
    def __init__(self, channel_id: str, name: str, enabled: bool = True):
        self.channel_id = channel_id
        self.name = name
        self.enabled = enabled
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send notification for an alert. Returns True if successful."""
        raise NotImplementedError


class LogNotificationChannel(NotificationChannel):
    """Notification channel that logs alerts."""
    
    def __init__(self, channel_id: str = "log", name: str = "Log Channel"):
        super().__init__(channel_id, name)
        import logging
        self.logger = logging.getLogger(f"extension.alerts.{channel_id}")
    
    async def send_notification(self, alert: Alert) -> bool:
        """Log the alert."""
        try:
            log_level = {
                AlertSeverity.LOW: logging.INFO,
                AlertSeverity.MEDIUM: logging.WARNING,
                AlertSeverity.HIGH: logging.ERROR,
                AlertSeverity.CRITICAL: logging.CRITICAL
            }.get(alert.severity, logging.INFO)
            
            self.logger.log(
                log_level,
                f"ALERT [{alert.severity.value.upper()}] {alert.title}: {alert.message}",
                extra={
                    'alert_id': alert.id,
                    'extension_id': alert.extension_id,
                    'alert_type': alert.alert_type,
                    'metric_name': alert.metric_name,
                    'current_value': alert.current_value,
                    'threshold_value': alert.threshold_value
                }
            )
            return True
        except Exception:
            return False


class WebhookNotificationChannel(NotificationChannel):
    """Notification channel that sends webhooks."""
    
    def __init__(self, channel_id: str, name: str, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        super().__init__(channel_id, name)
        self.webhook_url = webhook_url
        self.headers = headers or {}
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send webhook notification."""
        try:
            import aiohttp
            
            payload = {
                'alert_id': alert.id,
                'extension_id': alert.extension_id,
                'extension_name': alert.extension_name,
                'alert_type': alert.alert_type,
                'severity': alert.severity.value,
                'title': alert.title,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'metric_name': alert.metric_name,
                'current_value': alert.current_value,
                'threshold_value': alert.threshold_value,
                'metadata': alert.metadata
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status < 400
        except Exception:
            return False


class EmailNotificationChannel(NotificationChannel):
    """Notification channel that sends emails."""
    
    def __init__(
        self,
        channel_id: str,
        name: str,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str],
        use_tls: bool = True
    ):
        super().__init__(channel_id, name)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
        self.use_tls = use_tls
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send email notification."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            # Create email body
            body = f"""
Extension Alert

Extension: {alert.extension_name} ({alert.extension_id})
Alert Type: {alert.alert_type}
Severity: {alert.severity.value.upper()}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Message: {alert.message}

"""
            
            if alert.metric_name:
                body += f"Metric: {alert.metric_name}\n"
                body += f"Current Value: {alert.current_value}\n"
                body += f"Threshold: {alert.threshold_value}\n\n"
            
            if alert.metadata:
                body += "Additional Information:\n"
                for key, value in alert.metadata.items():
                    body += f"  {key}: {value}\n"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception:
            return False


@dataclass
class AlertingConfiguration:
    """Configuration for alerting system."""
    enabled: bool = True
    default_cooldown_minutes: int = 5
    max_alerts_per_hour: int = 100
    auto_resolve_after_hours: int = 24
    notification_channels: List[str] = field(default_factory=list)
    severity_filters: Dict[str, List[AlertSeverity]] = field(default_factory=dict)


class ExtensionAlertManager:
    """
    Manages alerts and notifications for extensions.
    
    Features:
    - Rule-based alert generation
    - Multiple notification channels
    - Alert deduplication and cooldowns
    - Alert resolution tracking
    - Performance impact monitoring
    """
    
    def __init__(
        self,
        extension_id: str,
        extension_name: str,
        configuration: Optional[AlertingConfiguration] = None,
        debug_manager=None
    ):
        self.extension_id = extension_id
        self.extension_name = extension_name
        self.configuration = configuration or AlertingConfiguration()
        self.debug_manager = debug_manager
        
        # Alert storage
        self.active_alerts: Dict[str, Alert] = {}
        self.resolved_alerts: deque = deque(maxlen=1000)
        self.alert_history: deque = deque(maxlen=10000)
        
        # Rules and channels
        self.alert_rules: Dict[str, AlertRule] = {}
        self.notification_channels: Dict[str, NotificationChannel] = {}
        
        # Rate limiting
        self.alert_counts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Deduplication
        self.alert_fingerprints: Set[str] = set()
        
        # Default notification channel
        self.notification_channels['log'] = LogNotificationChannel()
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start the alert manager."""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        # Register default rules
        self._register_default_rules()
    
    async def stop(self):
        """Stop the alert manager."""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    def add_notification_channel(self, channel: NotificationChannel):
        """Add a notification channel."""
        self.notification_channels[channel.channel_id] = channel
    
    def remove_notification_channel(self, channel_id: str):
        """Remove a notification channel."""
        if channel_id in self.notification_channels:
            del self.notification_channels[channel_id]
    
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.alert_rules[rule.rule_id] = rule
    
    def remove_alert_rule(self, rule_id: str):
        """Remove an alert rule."""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
    
    async def create_alert(
        self,
        alert_type: str,
        severity: AlertSeverity,
        title: str,
        message: str,
        metric_name: Optional[str] = None,
        current_value: Optional[float] = None,
        threshold_value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Alert]:
        """Create a new alert."""
        if not self.configuration.enabled:
            return None
        
        # Check rate limiting
        if not self._check_rate_limit(alert_type):
            return None
        
        # Create alert
        alert = Alert(
            id=str(uuid.uuid4()),
            extension_id=self.extension_id,
            extension_name=self.extension_name,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.utcnow(),
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            metadata=metadata or {}
        )
        
        # Check deduplication
        fingerprint = self._generate_fingerprint(alert)
        if fingerprint in self.alert_fingerprints:
            return None
        
        # Store alert
        self.active_alerts[alert.id] = alert
        self.alert_history.append(alert)
        self.alert_fingerprints.add(fingerprint)
        
        # Send notifications
        await self._send_notifications(alert)
        
        return alert
    
    async def resolve_alert(self, alert_id: str, resolution_notes: Optional[str] = None):
        """Resolve an active alert."""
        alert = self.active_alerts.get(alert_id)
        if not alert:
            return
        
        # Mark as resolved
        alert.resolve(resolution_notes)
        
        # Move to resolved alerts
        self.resolved_alerts.append(alert)
        del self.active_alerts[alert_id]
        
        # Remove fingerprint
        fingerprint = self._generate_fingerprint(alert)
        self.alert_fingerprints.discard(fingerprint)
    
    async def check_metric_thresholds(self, metric: MetricPoint):
        """Check metric against threshold rules."""
        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue
            
            # Check cooldown
            if rule.last_triggered:
                cooldown_end = rule.last_triggered + timedelta(minutes=rule.cooldown_minutes)
                if datetime.utcnow() < cooldown_end:
                    continue
            
            # Check condition
            try:
                if rule.condition(metric):
                    # Generate alert
                    message = rule.message_template.format(
                        metric_name=metric.metric_name,
                        value=metric.value,
                        unit=metric.unit,
                        extension_name=self.extension_name
                    )
                    
                    await self.create_alert(
                        alert_type="threshold_violation",
                        severity=rule.severity,
                        title=rule.name,
                        message=message,
                        metric_name=metric.metric_name,
                        current_value=metric.value,
                        metadata={'rule_id': rule.rule_id}
                    )
                    
                    rule.last_triggered = datetime.utcnow()
            except Exception:
                # Don't let rule evaluation errors break monitoring
                pass
    
    async def check_error_patterns(self, error: ErrorRecord):
        """Check error against pattern-based rules."""
        # High error rate rule
        recent_errors = [
            e for e in self.alert_history
            if (e.alert_type == "error_pattern" and 
                e.timestamp > datetime.utcnow() - timedelta(minutes=10))
        ]
        
        if len(recent_errors) > 10:  # More than 10 error alerts in 10 minutes
            await self.create_alert(
                alert_type="high_error_rate",
                severity=AlertSeverity.HIGH,
                title="High Error Rate Detected",
                message=f"More than 10 errors in the last 10 minutes",
                metadata={'error_count': len(recent_errors)}
            )
    
    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        alert_type: Optional[str] = None
    ) -> List[Alert]:
        """Get active alerts with optional filtering."""
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def get_resolved_alerts(self, limit: Optional[int] = None) -> List[Alert]:
        """Get resolved alerts."""
        alerts = list(self.resolved_alerts)
        if limit:
            alerts = alerts[-limit:]
        return alerts
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alerting statistics."""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        
        # Count alerts by severity in last 24h
        recent_alerts = [a for a in self.alert_history if a.timestamp > last_24h]
        severity_counts = defaultdict(int)
        for alert in recent_alerts:
            severity_counts[alert.severity.value] += 1
        
        # Count alerts by type
        type_counts = defaultdict(int)
        for alert in recent_alerts:
            type_counts[alert.alert_type] += 1
        
        # Calculate resolution rate
        total_alerts = len(self.active_alerts) + len(self.resolved_alerts)
        resolution_rate = (len(self.resolved_alerts) / total_alerts * 100) if total_alerts > 0 else 0
        
        return {
            'active_alerts': len(self.active_alerts),
            'resolved_alerts': len(self.resolved_alerts),
            'total_alerts_24h': len(recent_alerts),
            'resolution_rate_percent': resolution_rate,
            'severity_breakdown': dict(severity_counts),
            'type_breakdown': dict(type_counts),
            'enabled_rules': len([r for r in self.alert_rules.values() if r.enabled]),
            'notification_channels': len([c for c in self.notification_channels.values() if c.enabled])
        }
    
    def export_alerts(self, format: str = "json", include_resolved: bool = True) -> str:
        """Export alerts in specified format."""
        alerts = list(self.active_alerts.values())
        if include_resolved:
            alerts.extend(self.resolved_alerts)
        
        if format.lower() == "json":
            return json.dumps([a.to_dict() for a in alerts], indent=2)
        elif format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if alerts:
                fieldnames = ['id', 'timestamp', 'severity', 'title', 'message', 'resolved']
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for alert in alerts:
                    writer.writerow({
                        'id': alert.id,
                        'timestamp': alert.timestamp.isoformat(),
                        'severity': alert.severity.value,
                        'title': alert.title,
                        'message': alert.message,
                        'resolved': alert.resolved
                    })
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _register_default_rules(self):
        """Register default alerting rules."""
        # High CPU usage rule
        self.add_alert_rule(AlertRule(
            rule_id="high_cpu",
            name="High CPU Usage",
            condition=lambda m: m.metric_name == "resource_cpu_percent" and m.value > 80,
            severity=AlertSeverity.HIGH,
            message_template="CPU usage is {value}% which exceeds the threshold",
            cooldown_minutes=10
        ))
        
        # High memory usage rule
        self.add_alert_rule(AlertRule(
            rule_id="high_memory",
            name="High Memory Usage",
            condition=lambda m: m.metric_name == "resource_memory_mb" and m.value > 1000,
            severity=AlertSeverity.HIGH,
            message_template="Memory usage is {value}MB which exceeds the threshold",
            cooldown_minutes=10
        ))
        
        # High error rate rule
        self.add_alert_rule(AlertRule(
            rule_id="high_error_rate",
            name="High Error Rate",
            condition=lambda m: m.metric_name == "error_rate" and m.value > 5,
            severity=AlertSeverity.MEDIUM,
            message_template="Error rate is {value}% which exceeds the threshold",
            cooldown_minutes=5
        ))
        
        # Slow response time rule
        self.add_alert_rule(AlertRule(
            rule_id="slow_response",
            name="Slow Response Time",
            condition=lambda m: m.metric_name == "avg_response_time" and m.value > 5000,
            severity=AlertSeverity.MEDIUM,
            message_template="Average response time is {value}ms which exceeds the threshold",
            cooldown_minutes=5
        ))
    
    def _check_rate_limit(self, alert_type: str) -> bool:
        """Check if alert type is within rate limits."""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        # Clean old entries
        self.alert_counts[alert_type] = deque(
            [timestamp for timestamp in self.alert_counts[alert_type] if timestamp > hour_ago],
            maxlen=100
        )
        
        # Check limit
        if len(self.alert_counts[alert_type]) >= self.configuration.max_alerts_per_hour:
            return False
        
        # Add current timestamp
        self.alert_counts[alert_type].append(now)
        return True
    
    def _generate_fingerprint(self, alert: Alert) -> str:
        """Generate a fingerprint for alert deduplication."""
        import hashlib
        
        fingerprint_data = f"{alert.alert_type}:{alert.title}:{alert.metric_name}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()
    
    async def _send_notifications(self, alert: Alert):
        """Send notifications for an alert."""
        # Determine which channels to use
        channels_to_use = self.configuration.notification_channels
        if not channels_to_use:
            channels_to_use = list(self.notification_channels.keys())
        
        # Check severity filters
        for channel_id in channels_to_use:
            channel = self.notification_channels.get(channel_id)
            if not channel or not channel.enabled:
                continue
            
            # Check severity filter
            severity_filter = self.configuration.severity_filters.get(channel_id)
            if severity_filter and alert.severity not in severity_filter:
                continue
            
            # Send notification
            try:
                await channel.send_notification(alert)
            except Exception:
                # Don't let notification failures break alerting
                pass
    
    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while self._running:
            try:
                await self._cleanup_old_alerts()
                await asyncio.sleep(3600)  # Run every hour
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(3600)
    
    async def _cleanup_old_alerts(self):
        """Clean up old alerts and auto-resolve stale ones."""
        now = datetime.utcnow()
        auto_resolve_cutoff = now - timedelta(hours=self.configuration.auto_resolve_after_hours)
        
        # Auto-resolve old alerts
        alerts_to_resolve = []
        for alert_id, alert in self.active_alerts.items():
            if alert.timestamp < auto_resolve_cutoff:
                alerts_to_resolve.append(alert_id)
        
        for alert_id in alerts_to_resolve:
            await self.resolve_alert(alert_id, "Auto-resolved due to age")
        
        # Clean up fingerprints for resolved alerts
        active_fingerprints = {self._generate_fingerprint(alert) for alert in self.active_alerts.values()}
        self.alert_fingerprints = active_fingerprints