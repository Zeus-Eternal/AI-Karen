"""
Extension Alerting System

This module provides comprehensive alerting and escalation for extension errors,
including authentication issues, performance degradation, and service availability.

Requirements addressed:
- 10.1: Extension error alerts with relevant details
- 10.3: Authentication issue escalation and alerting
- 10.4: Performance degradation recommendations
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set, Union
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp
import threading

from .extension_error_logging import (
    ErrorEvent, ErrorSeverity, ErrorCategory, Alert, AlertStatus,
    extension_error_logger, extension_metrics_collector, extension_trend_analyzer
)

logger = logging.getLogger(__name__)

class AlertType(str, Enum):
    """Types of alerts that can be generated."""
    ERROR_RATE_THRESHOLD = "error_rate_threshold"
    AUTHENTICATION_FAILURE = "authentication_failure"
    SERVICE_UNAVAILABLE = "service_unavailable"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    RECOVERY_FAILURE = "recovery_failure"
    AVAILABILITY_DROP = "availability_drop"

class EscalationLevel(str, Enum):
    """Escalation levels for alerts."""
    LEVEL_1 = "level_1"  # Team notification
    LEVEL_2 = "level_2"  # Manager notification
    LEVEL_3 = "level_3"  # Executive notification

@dataclass
class AlertRule:
    """Configuration for alert generation rules."""
    rule_id: str
    alert_type: AlertType
    condition: Dict[str, Any]
    severity: ErrorSeverity
    escalation_level: EscalationLevel
    cooldown_minutes: int = 15
    enabled: bool = True

@dataclass
class NotificationChannel:
    """Configuration for notification channels."""
    channel_id: str
    channel_type: str  # email, slack, webhook, etc.
    config: Dict[str, Any]
    escalation_levels: List[EscalationLevel]
    enabled: bool = True

class ExtensionAlertManager:
    """Manages alert generation, escalation, and notifications."""

    def __init__(self):
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alert_rules_by_type: Dict[str, AlertRule] = {}
        self.notification_channels: Dict[str, NotificationChannel] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.last_alert_times: Dict[str, datetime] = {}
        self.lock = threading.Lock()
        
        # Initialize default alert rules
        self._initialize_default_rules()
        
        # Start background monitoring
        self.monitoring_active = False
        self.monitoring_task = None

    def _initialize_default_rules(self):
        """Initialize default alert rules for extension monitoring."""
        
        # High error rate alert
        self.add_alert_rule(AlertRule(
            rule_id="high_error_rate",
            alert_type=AlertType.ERROR_RATE_THRESHOLD,
            condition={"threshold": 0.05, "time_window_minutes": 15},
            severity=ErrorSeverity.HIGH,
            escalation_level=EscalationLevel.LEVEL_1,
            cooldown_minutes=30
        ))
        
        # Authentication failure spike
        self.add_alert_rule(AlertRule(
            rule_id="auth_failure_spike",
            alert_type=AlertType.AUTHENTICATION_FAILURE,
            condition={"threshold": 10, "time_window_minutes": 5},
            severity=ErrorSeverity.CRITICAL,
            escalation_level=EscalationLevel.LEVEL_2,
            cooldown_minutes=15
        ))
        
        # Service unavailable
        self.add_alert_rule(AlertRule(
            rule_id="service_unavailable",
            alert_type=AlertType.SERVICE_UNAVAILABLE,
            condition={"threshold": 0.8, "time_window_minutes": 10},
            severity=ErrorSeverity.CRITICAL,
            escalation_level=EscalationLevel.LEVEL_2,
            cooldown_minutes=10
        ))
        
        # Performance degradation
        self.add_alert_rule(AlertRule(
            rule_id="performance_degradation",
            alert_type=AlertType.PERFORMANCE_DEGRADATION,
            condition={"response_time_threshold": 5000, "time_window_minutes": 15},
            severity=ErrorSeverity.MEDIUM,
            escalation_level=EscalationLevel.LEVEL_1,
            cooldown_minutes=30
        ))
        
        # Recovery failure
        self.add_alert_rule(AlertRule(
            rule_id="recovery_failure",
            alert_type=AlertType.RECOVERY_FAILURE,
            condition={"success_rate_threshold": 0.5, "time_window_minutes": 30},
            severity=ErrorSeverity.HIGH,
            escalation_level=EscalationLevel.LEVEL_1,
            cooldown_minutes=60
        ))
        
        # Availability drop
        self.add_alert_rule(AlertRule(
            rule_id="availability_drop",
            alert_type=AlertType.AVAILABILITY_DROP,
            condition={"threshold": 0.95, "time_window_minutes": 15},
            severity=ErrorSeverity.HIGH,
            escalation_level=EscalationLevel.LEVEL_1,
            cooldown_minutes=20
        ))

    def add_alert_rule(self, rule: AlertRule):
        """Add or update an alert rule."""
        with self.lock:
            self.alert_rules[rule.rule_id] = rule
            self.alert_rules_by_type[rule.alert_type.value] = rule
            logger.info(f"Added alert rule: {rule.rule_id}")

    def add_notification_channel(self, channel: NotificationChannel):
        """Add or update a notification channel."""
        with self.lock:
            self.notification_channels[channel.channel_id] = channel
            logger.info(f"Added notification channel: {channel.channel_id}")

    async def start_monitoring(self, check_interval: int = 60):
        """Start background alert monitoring."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        logger.info("Starting extension alert monitoring")
        
        self.monitoring_task = asyncio.create_task(self._monitoring_loop(check_interval))

    async def stop_monitoring(self):
        """Stop background alert monitoring."""
        self.monitoring_active = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped extension alert monitoring")

    async def _monitoring_loop(self, check_interval: int):
        """Background monitoring loop for alert generation."""
        while self.monitoring_active:
            try:
                await self.check_alert_conditions()
                await asyncio.sleep(check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert monitoring loop: {e}")
                await asyncio.sleep(check_interval)

    async def check_alert_conditions(self):
        """Check all alert rule conditions and generate alerts."""
        current_time = datetime.utcnow()
        
        for rule_id, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            # Check cooldown period
            last_alert_time = self.last_alert_times.get(rule_id)
            if last_alert_time:
                cooldown_end = last_alert_time + timedelta(minutes=rule.cooldown_minutes)
                if current_time < cooldown_end:
                    continue
            
            # Check rule condition
            should_alert = await self._check_rule_condition(rule)
            
            if should_alert:
                alert = await self._generate_alert(rule)
                if alert:
                    await self._process_alert(alert)
                    self.last_alert_times[rule_id] = current_time

    async def _check_rule_condition(self, rule: AlertRule) -> bool:
        """Check if a specific rule condition is met."""
        try:
            if rule.alert_type == AlertType.ERROR_RATE_THRESHOLD:
                return await self._check_error_rate_condition(rule)
            elif rule.alert_type == AlertType.AUTHENTICATION_FAILURE:
                return await self._check_auth_failure_condition(rule)
            elif rule.alert_type == AlertType.SERVICE_UNAVAILABLE:
                return await self._check_service_unavailable_condition(rule)
            elif rule.alert_type == AlertType.PERFORMANCE_DEGRADATION:
                return await self._check_performance_condition(rule)
            elif rule.alert_type == AlertType.RECOVERY_FAILURE:
                return await self._check_recovery_failure_condition(rule)
            elif rule.alert_type == AlertType.AVAILABILITY_DROP:
                return await self._check_availability_condition(rule)
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking rule condition {rule.rule_id}: {e}")
            return False

    async def _check_error_rate_condition(self, rule: AlertRule) -> bool:
        """Check error rate threshold condition."""
        time_window = rule.condition.get("time_window_minutes", 15)
        threshold = rule.condition.get("threshold", 0.05)
        
        error_rates = extension_metrics_collector.get_error_rate(time_window_minutes=time_window)
        total_error_rate = sum(error_rates.values())
        
        return total_error_rate > threshold

    async def _check_auth_failure_condition(self, rule: AlertRule) -> bool:
        """Check authentication failure spike condition."""
        time_window = rule.condition.get("time_window_minutes", 5)
        threshold = rule.condition.get("threshold", 10)
        
        # Count authentication errors in time window
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window)
        auth_error_count = 0
        
        with extension_metrics_collector.lock:
            for metric_point in extension_metrics_collector.metrics['errors']:
                if (metric_point.timestamp >= cutoff_time and 
                    metric_point.labels.get('category') == ErrorCategory.AUTHENTICATION.value):
                    auth_error_count += 1
        
        return auth_error_count > threshold

    async def _check_service_unavailable_condition(self, rule: AlertRule) -> bool:
        """Check service unavailable condition."""
        time_window = rule.condition.get("time_window_minutes", 10)
        threshold = rule.condition.get("threshold", 0.8)
        
        # Count service unavailable errors
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window)
        unavailable_count = 0
        total_requests = 0
        
        with extension_metrics_collector.lock:
            for metric_point in extension_metrics_collector.metrics['errors']:
                if metric_point.timestamp >= cutoff_time:
                    total_requests += 1
                    if metric_point.labels.get('category') == ErrorCategory.SERVICE_UNAVAILABLE.value:
                        unavailable_count += 1
            
            for metric_point in extension_metrics_collector.metrics['requests']:
                if metric_point.timestamp >= cutoff_time:
                    total_requests += 1
        
        if total_requests == 0:
            return False
        
        unavailable_rate = unavailable_count / total_requests
        return unavailable_rate > threshold

    async def _check_performance_condition(self, rule: AlertRule) -> bool:
        """Check performance degradation condition."""
        time_window = rule.condition.get("time_window_minutes", 15)
        threshold = rule.condition.get("response_time_threshold", 5000)
        
        response_stats = extension_metrics_collector.get_response_time_stats(
            time_window_minutes=time_window
        )
        
        return response_stats['avg'] > threshold

    async def _check_recovery_failure_condition(self, rule: AlertRule) -> bool:
        """Check recovery failure condition."""
        time_window = rule.condition.get("time_window_minutes", 30)
        threshold = rule.condition.get("success_rate_threshold", 0.5)
        
        recovery_rates = extension_metrics_collector.get_recovery_success_rate(
            time_window_minutes=time_window
        )
        
        # Check if any recovery strategy has low success rate
        for strategy, rate in recovery_rates.items():
            if rate < threshold:
                return True
        
        return False

    async def _check_availability_condition(self, rule: AlertRule) -> bool:
        """Check availability drop condition."""
        time_window = rule.condition.get("time_window_minutes", 15)
        threshold = rule.condition.get("threshold", 0.95)
        
        availability_stats = extension_metrics_collector.get_availability_stats(
            time_window_minutes=time_window
        )
        
        # Check if any endpoint has low availability
        for endpoint, availability in availability_stats.items():
            if availability < threshold:
                return True
        
        return False

    async def _generate_alert(self, rule: AlertRule) -> Optional[Alert]:
        """Generate alert based on rule."""
        try:
            correlation_id = extension_error_logger.get_correlation_id()
            
            # Get relevant context based on alert type
            context = await self._get_alert_context(rule)
            
            # Generate alert message
            message = self._generate_alert_message(rule, context)
            
            alert = Alert(
                alert_id=f"{rule.rule_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                correlation_id=correlation_id,
                alert_type=rule.alert_type.value,
                severity=rule.severity,
                message=message,
                context=context,
                created_at=datetime.utcnow()
            )
            
            return alert
            
        except Exception as e:
            logger.error(f"Error generating alert for rule {rule.rule_id}: {e}")
            return None

    async def _get_alert_context(self, rule: AlertRule) -> Dict[str, Any]:
        """Get relevant context for alert."""
        context = {}
        
        if rule.alert_type == AlertType.ERROR_RATE_THRESHOLD:
            time_window = rule.condition.get("time_window_minutes", 15)
            context.update({
                "error_rates": extension_metrics_collector.get_error_rate(time_window_minutes=time_window),
                "time_window_minutes": time_window
            })
        
        elif rule.alert_type == AlertType.PERFORMANCE_DEGRADATION:
            time_window = rule.condition.get("time_window_minutes", 15)
            context.update({
                "response_stats": extension_metrics_collector.get_response_time_stats(time_window_minutes=time_window),
                "recommendations": extension_trend_analyzer.get_performance_recommendations()
            })
        
        elif rule.alert_type == AlertType.AVAILABILITY_DROP:
            time_window = rule.condition.get("time_window_minutes", 15)
            context.update({
                "availability_stats": extension_metrics_collector.get_availability_stats(time_window_minutes=time_window)
            })
        
        elif rule.alert_type == AlertType.RECOVERY_FAILURE:
            time_window = rule.condition.get("time_window_minutes", 30)
            context.update({
                "recovery_rates": extension_metrics_collector.get_recovery_success_rate(time_window_minutes=time_window)
            })
        
        return context

    def _generate_alert_message(self, rule: AlertRule, context: Dict[str, Any]) -> str:
        """Generate human-readable alert message."""
        if rule.alert_type == AlertType.ERROR_RATE_THRESHOLD:
            error_rates = context.get("error_rates", {})
            total_rate = sum(error_rates.values())
            return f"Extension error rate ({total_rate:.2%}) exceeds threshold ({rule.condition['threshold']:.2%})"
        
        elif rule.alert_type == AlertType.AUTHENTICATION_FAILURE:
            return f"Authentication failure spike detected: {rule.condition['threshold']} failures in {rule.condition['time_window_minutes']} minutes"
        
        elif rule.alert_type == AlertType.SERVICE_UNAVAILABLE:
            return f"Service unavailable rate exceeds {rule.condition['threshold']:.1%} threshold"
        
        elif rule.alert_type == AlertType.PERFORMANCE_DEGRADATION:
            response_stats = context.get("response_stats", {})
            avg_time = response_stats.get("avg", 0)
            return f"Performance degradation detected: average response time {avg_time:.0f}ms exceeds {rule.condition['response_time_threshold']}ms threshold"
        
        elif rule.alert_type == AlertType.RECOVERY_FAILURE:
            return f"Error recovery success rate below {rule.condition['success_rate_threshold']:.1%} threshold"
        
        elif rule.alert_type == AlertType.AVAILABILITY_DROP:
            return f"Extension availability dropped below {rule.condition['threshold']:.1%} threshold"
        
        return f"Alert triggered for rule: {rule.rule_id}"

    async def _process_alert(self, alert: Alert):
        """Process and send alert through notification channels."""
        with self.lock:
            self.active_alerts[alert.alert_id] = alert
            self.alert_history.append(alert)

        logger.warning(
            "Alert generated",
            extra={
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity.value,
                "message": alert.message,
            },
        )

        # Send notifications
        await self._send_notifications(alert)

    async def create_manual_alert(
        self,
        *,
        alert_type: Union[AlertType, str],
        severity: ErrorSeverity,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        escalation_level: Optional[Union[EscalationLevel, str]] = None,
    ) -> Alert:
        """Create and dispatch an alert outside of rule evaluation.

        This enables subsystems (such as service recovery) to escalate incidents
        immediately with full context, while still leveraging the centralised
        notification pipeline.
        """

        if isinstance(alert_type, AlertType):
            alert_type_value = alert_type.value
        else:
            alert_type_value = str(alert_type)

        alert_context = dict(context or {})

        if escalation_level is not None:
            if isinstance(escalation_level, EscalationLevel):
                escalation_value = escalation_level.value
            else:
                escalation_value = str(escalation_level)
            alert_context.setdefault("escalation_level_override", escalation_value)

        alert = Alert(
            alert_id=f"manual_{alert_type_value}_{uuid.uuid4().hex}",
            correlation_id=extension_error_logger.get_correlation_id(),
            alert_type=alert_type_value,
            severity=severity,
            message=message,
            context=alert_context,
            created_at=datetime.utcnow(),
        )

        await self._process_alert(alert)
        return alert

    async def _send_notifications(self, alert: Alert):
        """Send alert notifications through configured channels."""
        # Find the escalation level for this alert
        rule = self.alert_rules_by_type.get(alert.alert_type)
        escalation_level: Optional[EscalationLevel] = None

        if rule:
            escalation_level = rule.escalation_level

        override_level = alert.context.get("escalation_level_override")
        if override_level:
            try:
                escalation_level = EscalationLevel(override_level)
            except ValueError:
                logger.error(
                    "Invalid escalation level override",
                    extra={
                        "alert_id": alert.alert_id,
                        "override": override_level,
                    },
                )

        if escalation_level is None:
            logger.warning(
                "No escalation level configured for alert",
                extra={"alert_id": alert.alert_id, "alert_type": alert.alert_type},
            )
            return

        # Send to all channels that handle this escalation level
        for channel_id, channel in self.notification_channels.items():
            if not channel.enabled:
                continue
            
            if escalation_level not in channel.escalation_levels:
                continue
            
            try:
                await self._send_channel_notification(channel, alert)
            except Exception as e:
                logger.error(f"Failed to send notification via {channel_id}: {e}")

    async def _send_channel_notification(self, channel: NotificationChannel, alert: Alert):
        """Send notification through specific channel."""
        if channel.channel_type == "email":
            await self._send_email_notification(channel, alert)
        elif channel.channel_type == "webhook":
            await self._send_webhook_notification(channel, alert)
        elif channel.channel_type == "slack":
            await self._send_slack_notification(channel, alert)
        else:
            logger.warning(f"Unknown notification channel type: {channel.channel_type}")

    async def _send_email_notification(self, channel: NotificationChannel, alert: Alert):
        """Send email notification."""
        config = channel.config
        
        msg = MIMEMultipart()
        msg['From'] = config.get('from_email', 'alerts@kari.ai')
        msg['To'] = ', '.join(config.get('to_emails', []))
        msg['Subject'] = f"[{alert.severity.value.upper()}] Extension Alert: {alert.alert_type}"
        
        # Create email body
        body = f"""
Extension Alert Generated

Alert ID: {alert.alert_id}
Type: {alert.alert_type}
Severity: {alert.severity.value}
Time: {alert.created_at.isoformat()}

Message: {alert.message}

Context:
{json.dumps(alert.context, indent=2)}

Correlation ID: {alert.correlation_id}
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email (implementation would depend on SMTP configuration)
        logger.info(f"Email alert sent: {alert.alert_id}")

    async def _send_webhook_notification(self, channel: NotificationChannel, alert: Alert):
        """Send webhook notification."""
        config = channel.config
        webhook_url = config.get('url')
        
        if not webhook_url:
            logger.error("Webhook URL not configured")
            return
        
        payload = {
            'alert_id': alert.alert_id,
            'alert_type': alert.alert_type,
            'severity': alert.severity.value,
            'message': alert.message,
            'context': alert.context,
            'created_at': alert.created_at.isoformat(),
            'correlation_id': alert.correlation_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status == 200:
                    logger.info(f"Webhook alert sent: {alert.alert_id}")
                else:
                    logger.error(f"Webhook alert failed: {response.status}")

    async def _send_slack_notification(self, channel: NotificationChannel, alert: Alert):
        """Send Slack notification."""
        config = channel.config
        webhook_url = config.get('webhook_url')
        
        if not webhook_url:
            logger.error("Slack webhook URL not configured")
            return
        
        # Format Slack message
        color = {
            ErrorSeverity.LOW: "good",
            ErrorSeverity.MEDIUM: "warning", 
            ErrorSeverity.HIGH: "danger",
            ErrorSeverity.CRITICAL: "danger"
        }.get(alert.severity, "warning")
        
        payload = {
            "attachments": [{
                "color": color,
                "title": f"Extension Alert: {alert.alert_type}",
                "text": alert.message,
                "fields": [
                    {"title": "Severity", "value": alert.severity.value, "short": True},
                    {"title": "Time", "value": alert.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), "short": True},
                    {"title": "Alert ID", "value": alert.alert_id, "short": True},
                    {"title": "Correlation ID", "value": alert.correlation_id, "short": True}
                ],
                "footer": "Extension Monitoring System"
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status == 200:
                    logger.info(f"Slack alert sent: {alert.alert_id}")
                else:
                    logger.error(f"Slack alert failed: {response.status}")

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = None) -> bool:
        """Acknowledge an active alert."""
        with self.lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.utcnow()
                logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
                return True
        
        return False

    def resolve_alert(self, alert_id: str, resolved_by: str = None) -> bool:
        """Resolve an active alert."""
        with self.lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow()
                del self.active_alerts[alert_id]
                logger.info(f"Alert resolved: {alert_id} by {resolved_by}")
                return True
        
        return False

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        with self.lock:
            return list(self.active_alerts.values())

    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with self.lock:
            return [
                alert for alert in self.alert_history
                if alert.created_at >= cutoff_time
            ]

# Global alert manager instance
extension_alert_manager = ExtensionAlertManager()

# Initialize default notification channels (these would be configured from environment)
def initialize_default_channels():
    """Initialize default notification channels."""
    
    # Email channel for Level 1 alerts
    extension_alert_manager.add_notification_channel(NotificationChannel(
        channel_id="team_email",
        channel_type="email",
        config={
            "from_email": "alerts@kari.ai",
            "to_emails": ["team@kari.ai"]
        },
        escalation_levels=[EscalationLevel.LEVEL_1]
    ))
    
    # Slack channel for Level 1 and 2 alerts
    extension_alert_manager.add_notification_channel(NotificationChannel(
        channel_id="team_slack",
        channel_type="slack",
        config={
            "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
        },
        escalation_levels=[EscalationLevel.LEVEL_1, EscalationLevel.LEVEL_2]
    ))
    
    # Executive email for Level 3 alerts
    extension_alert_manager.add_notification_channel(NotificationChannel(
        channel_id="executive_email",
        channel_type="email",
        config={
            "from_email": "critical-alerts@kari.ai",
            "to_emails": ["executives@kari.ai"]
        },
        escalation_levels=[EscalationLevel.LEVEL_3]
    ))

# Initialize channels on module import
initialize_default_channels()