"""
Extension Monitoring Alerting System

Advanced alerting system for extension authentication failures,
service health issues, and performance degradation.
"""

import asyncio
import logging
import smtplib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import aiohttp
import os

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    LOG = "log"


class EscalationLevel(Enum):
    LEVEL_1 = "level_1"  # Immediate notification
    LEVEL_2 = "level_2"  # Escalate after 5 minutes
    LEVEL_3 = "level_3"  # Escalate after 15 minutes
    LEVEL_4 = "level_4"  # Escalate after 30 minutes


@dataclass
class NotificationConfig:
    """Configuration for notification channels."""
    channel: NotificationChannel
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    escalation_levels: List[EscalationLevel] = field(default_factory=lambda: [EscalationLevel.LEVEL_1])


@dataclass
class AlertRule:
    """Enhanced alert rule with escalation and notification settings."""
    id: str
    name: str
    description: str
    condition: str
    threshold: float
    severity: str
    enabled: bool = True
    notification_channels: List[NotificationChannel] = field(default_factory=list)
    escalation_enabled: bool = False
    escalation_interval_minutes: int = 5
    max_escalation_level: EscalationLevel = EscalationLevel.LEVEL_2
    cooldown_minutes: int = 30
    
    # State tracking
    is_active: bool = False
    triggered_at: Optional[datetime] = None
    last_notification: Optional[datetime] = None
    escalation_level: EscalationLevel = EscalationLevel.LEVEL_1
    notification_count: int = 0


class ExtensionAlertingSystem:
    """Advanced alerting system for extension monitoring."""

    def __init__(self):
        self.alert_rules: Dict[str, AlertRule] = {}
        self.notification_configs: Dict[NotificationChannel, NotificationConfig] = {}
        self.notification_handlers: Dict[NotificationChannel, Callable] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.escalation_tasks: Dict[str, asyncio.Task] = {}
        
        # Setup default notification handlers
        self._setup_notification_handlers()
        self._setup_default_alert_rules()

    def _setup_notification_handlers(self):
        """Setup notification handlers for different channels."""
        self.notification_handlers = {
            NotificationChannel.EMAIL: self._send_email_notification,
            NotificationChannel.WEBHOOK: self._send_webhook_notification,
            NotificationChannel.SLACK: self._send_slack_notification,
            NotificationChannel.DISCORD: self._send_discord_notification,
            NotificationChannel.LOG: self._send_log_notification,
        }

    def _setup_default_alert_rules(self):
        """Setup default alert rules."""
        
        # Critical authentication failure rate
        self.add_alert_rule(AlertRule(
            id="auth_failure_critical",
            name="Critical Authentication Failure Rate",
            description="Authentication failure rate exceeds 25%",
            condition="auth_failure_rate > 25",
            threshold=25.0,
            severity="critical",
            notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
            escalation_enabled=True,
            escalation_interval_minutes=2,
            max_escalation_level=EscalationLevel.LEVEL_3
        ))
        
        # High authentication failure rate
        self.add_alert_rule(AlertRule(
            id="auth_failure_high",
            name="High Authentication Failure Rate",
            description="Authentication failure rate exceeds 10%",
            condition="auth_failure_rate > 10",
            threshold=10.0,
            severity="warning",
            notification_channels=[NotificationChannel.SLACK, NotificationChannel.LOG],
            escalation_enabled=True,
            escalation_interval_minutes=5
        ))
        
        # Service health critical
        self.add_alert_rule(AlertRule(
            id="service_health_critical",
            name="Critical Service Health",
            description="Service health below 50%",
            condition="service_health_percentage < 50",
            threshold=50.0,
            severity="critical",
            notification_channels=[NotificationChannel.EMAIL, NotificationChannel.WEBHOOK],
            escalation_enabled=True,
            escalation_interval_minutes=1,
            max_escalation_level=EscalationLevel.LEVEL_4
        ))
        
        # API error rate high
        self.add_alert_rule(AlertRule(
            id="api_error_rate_high",
            name="High API Error Rate",
            description="API error rate exceeds 15%",
            condition="api_error_rate > 15",
            threshold=15.0,
            severity="error",
            notification_channels=[NotificationChannel.SLACK, NotificationChannel.LOG],
            escalation_enabled=True
        ))
        
        # Response time degradation
        self.add_alert_rule(AlertRule(
            id="response_time_degraded",
            name="Response Time Degradation",
            description="Average response time exceeds 5 seconds",
            condition="avg_response_time > 5000",
            threshold=5000.0,
            severity="warning",
            notification_channels=[NotificationChannel.LOG, NotificationChannel.WEBHOOK]
        ))

    def configure_notification_channel(self, channel: NotificationChannel, config: Dict[str, Any]):
        """Configure a notification channel."""
        self.notification_configs[channel] = NotificationConfig(
            channel=channel,
            enabled=config.get('enabled', True),
            config=config
        )
        logger.info(f"Configured notification channel: {channel.value}")

    def add_alert_rule(self, alert_rule: AlertRule):
        """Add a new alert rule."""
        self.alert_rules[alert_rule.id] = alert_rule
        logger.info(f"Added alert rule: {alert_rule.name}")

    def remove_alert_rule(self, alert_id: str):
        """Remove an alert rule."""
        if alert_id in self.alert_rules:
            # Cancel any active escalation tasks
            if alert_id in self.escalation_tasks:
                self.escalation_tasks[alert_id].cancel()
                del self.escalation_tasks[alert_id]
            
            del self.alert_rules[alert_id]
            logger.info(f"Removed alert rule: {alert_id}")

    async def evaluate_alerts(self, metrics: Dict[str, float]):
        """Evaluate all alert rules against current metrics."""
        for alert_id, alert_rule in self.alert_rules.items():
            if not alert_rule.enabled:
                continue
            
            try:
                await self._evaluate_single_alert(alert_rule, metrics)
            except Exception as e:
                logger.error(f"Error evaluating alert {alert_id}: {e}")

    async def _evaluate_single_alert(self, alert_rule: AlertRule, metrics: Dict[str, float]):
        """Evaluate a single alert rule."""
        condition_met = self._evaluate_condition(alert_rule.condition, alert_rule.threshold, metrics)
        
        if condition_met and not alert_rule.is_active:
            # Trigger alert
            await self._trigger_alert(alert_rule, metrics)
        elif not condition_met and alert_rule.is_active:
            # Resolve alert
            await self._resolve_alert(alert_rule, metrics)
        elif condition_met and alert_rule.is_active:
            # Check for escalation
            await self._check_escalation(alert_rule, metrics)

    def _evaluate_condition(self, condition: str, threshold: float, metrics: Dict[str, float]) -> bool:
        """Evaluate alert condition against metrics."""
        try:
            # Simple condition evaluation - can be enhanced with more complex logic
            if "auth_failure_rate" in condition:
                return metrics.get('auth_failure_rate', 0) > threshold
            elif "service_health_percentage" in condition:
                return metrics.get('service_health_percentage', 100) < threshold
            elif "api_error_rate" in condition:
                return metrics.get('api_error_rate', 0) > threshold
            elif "avg_response_time" in condition:
                return metrics.get('avg_response_time', 0) > threshold
            
            return False
        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False

    async def _trigger_alert(self, alert_rule: AlertRule, metrics: Dict[str, float]):
        """Trigger an alert."""
        alert_rule.is_active = True
        alert_rule.triggered_at = datetime.utcnow()
        alert_rule.escalation_level = EscalationLevel.LEVEL_1
        alert_rule.notification_count = 0
        
        alert_data = {
            'alert_id': alert_rule.id,
            'name': alert_rule.name,
            'description': alert_rule.description,
            'severity': alert_rule.severity,
            'triggered_at': alert_rule.triggered_at.isoformat(),
            'metrics': metrics,
            'threshold': alert_rule.threshold,
            'escalation_level': alert_rule.escalation_level.value
        }
        
        # Record in history
        self.alert_history.append({
            **alert_data,
            'action': 'triggered'
        })
        
        logger.warning(f"Alert triggered: {alert_rule.name}")
        
        # Send notifications
        await self._send_notifications(alert_rule, alert_data, 'triggered')
        
        # Start escalation if enabled
        if alert_rule.escalation_enabled:
            self._start_escalation_timer(alert_rule, metrics)

    async def _resolve_alert(self, alert_rule: AlertRule, metrics: Dict[str, float]):
        """Resolve an alert."""
        duration = (datetime.utcnow() - alert_rule.triggered_at).total_seconds() if alert_rule.triggered_at else 0
        
        alert_rule.is_active = False
        resolved_at = datetime.utcnow()
        
        alert_data = {
            'alert_id': alert_rule.id,
            'name': alert_rule.name,
            'description': alert_rule.description,
            'severity': alert_rule.severity,
            'resolved_at': resolved_at.isoformat(),
            'duration_seconds': duration,
            'metrics': metrics,
            'escalation_level': alert_rule.escalation_level.value,
            'notification_count': alert_rule.notification_count
        }
        
        # Record in history
        self.alert_history.append({
            **alert_data,
            'action': 'resolved'
        })
        
        logger.info(f"Alert resolved: {alert_rule.name} (duration: {duration:.1f}s)")
        
        # Send resolution notifications
        await self._send_notifications(alert_rule, alert_data, 'resolved')
        
        # Cancel escalation timer
        if alert_rule.id in self.escalation_tasks:
            self.escalation_tasks[alert_rule.id].cancel()
            del self.escalation_tasks[alert_rule.id]

    async def _check_escalation(self, alert_rule: AlertRule, metrics: Dict[str, float]):
        """Check if alert should be escalated."""
        if not alert_rule.escalation_enabled or not alert_rule.triggered_at:
            return
        
        time_since_trigger = (datetime.utcnow() - alert_rule.triggered_at).total_seconds() / 60
        time_since_last_notification = 0
        
        if alert_rule.last_notification:
            time_since_last_notification = (datetime.utcnow() - alert_rule.last_notification).total_seconds() / 60
        
        # Check if it's time to escalate
        if time_since_last_notification >= alert_rule.escalation_interval_minutes:
            await self._escalate_alert(alert_rule, metrics)

    async def _escalate_alert(self, alert_rule: AlertRule, metrics: Dict[str, float]):
        """Escalate an alert to the next level."""
        # Determine next escalation level
        current_level_value = list(EscalationLevel).index(alert_rule.escalation_level)
        max_level_value = list(EscalationLevel).index(alert_rule.max_escalation_level)
        
        if current_level_value < max_level_value:
            alert_rule.escalation_level = list(EscalationLevel)[current_level_value + 1]
        
        alert_data = {
            'alert_id': alert_rule.id,
            'name': alert_rule.name,
            'description': alert_rule.description,
            'severity': alert_rule.severity,
            'escalated_at': datetime.utcnow().isoformat(),
            'escalation_level': alert_rule.escalation_level.value,
            'metrics': metrics,
            'duration_minutes': (datetime.utcnow() - alert_rule.triggered_at).total_seconds() / 60
        }
        
        # Record escalation in history
        self.alert_history.append({
            **alert_data,
            'action': 'escalated'
        })
        
        logger.warning(f"Alert escalated: {alert_rule.name} to {alert_rule.escalation_level.value}")
        
        # Send escalation notifications
        await self._send_notifications(alert_rule, alert_data, 'escalated')

    def _start_escalation_timer(self, alert_rule: AlertRule, metrics: Dict[str, float]):
        """Start escalation timer for an alert."""
        async def escalation_timer():
            try:
                while alert_rule.is_active:
                    await asyncio.sleep(alert_rule.escalation_interval_minutes * 60)
                    if alert_rule.is_active:
                        await self._escalate_alert(alert_rule, metrics)
            except asyncio.CancelledError:
                pass
        
        if alert_rule.id in self.escalation_tasks:
            self.escalation_tasks[alert_rule.id].cancel()
        
        self.escalation_tasks[alert_rule.id] = asyncio.create_task(escalation_timer())

    async def _send_notifications(self, alert_rule: AlertRule, alert_data: Dict[str, Any], action: str):
        """Send notifications for an alert."""
        for channel in alert_rule.notification_channels:
            if channel not in self.notification_configs:
                continue
            
            config = self.notification_configs[channel]
            if not config.enabled:
                continue
            
            try:
                handler = self.notification_handlers.get(channel)
                if handler:
                    await handler(alert_data, action, config.config)
                    alert_rule.notification_count += 1
                    alert_rule.last_notification = datetime.utcnow()
            except Exception as e:
                logger.error(f"Error sending {channel.value} notification: {e}")

    async def _send_email_notification(self, alert_data: Dict[str, Any], action: str, config: Dict[str, Any]):
        """Send email notification."""
        smtp_server = config.get('smtp_server', 'localhost')
        smtp_port = config.get('smtp_port', 587)
        username = config.get('username')
        password = config.get('password')
        from_email = config.get('from_email', 'alerts@example.com')
        to_emails = config.get('to_emails', [])
        
        if not to_emails:
            logger.warning("No email recipients configured")
            return
        
        subject = f"[{alert_data['severity'].upper()}] {alert_data['name']} - {action.title()}"
        
        body = f"""
Alert {action.title()}: {alert_data['name']}

Description: {alert_data['description']}
Severity: {alert_data['severity']}
Alert ID: {alert_data['alert_id']}

"""
        
        if action == 'triggered':
            body += f"Triggered at: {alert_data['triggered_at']}\n"
            body += f"Threshold: {alert_data['threshold']}\n"
        elif action == 'resolved':
            body += f"Resolved at: {alert_data['resolved_at']}\n"
            body += f"Duration: {alert_data['duration_seconds']:.1f} seconds\n"
        elif action == 'escalated':
            body += f"Escalated at: {alert_data['escalated_at']}\n"
            body += f"Escalation Level: {alert_data['escalation_level']}\n"
            body += f"Duration: {alert_data['duration_minutes']:.1f} minutes\n"
        
        body += f"\nCurrent Metrics:\n"
        for key, value in alert_data.get('metrics', {}).items():
            body += f"  {key}: {value}\n"
        
        try:
            msg = MimeMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            if username and password:
                server.starttls()
                server.login(username, password)
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email notification sent for alert {alert_data['alert_id']}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

    async def _send_webhook_notification(self, alert_data: Dict[str, Any], action: str, config: Dict[str, Any]):
        """Send webhook notification."""
        webhook_url = config.get('url')
        headers = config.get('headers', {'Content-Type': 'application/json'})
        
        if not webhook_url:
            logger.warning("No webhook URL configured")
            return
        
        payload = {
            'action': action,
            'alert': alert_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        logger.info(f"Webhook notification sent for alert {alert_data['alert_id']}")
                    else:
                        logger.error(f"Webhook notification failed: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")

    async def _send_slack_notification(self, alert_data: Dict[str, Any], action: str, config: Dict[str, Any]):
        """Send Slack notification."""
        webhook_url = config.get('webhook_url')
        channel = config.get('channel', '#alerts')
        
        if not webhook_url:
            logger.warning("No Slack webhook URL configured")
            return
        
        color = {
            'critical': '#ff0000',
            'error': '#ff6600',
            'warning': '#ffcc00',
            'info': '#0099cc'
        }.get(alert_data['severity'], '#cccccc')
        
        emoji = {
            'triggered': ':warning:',
            'resolved': ':white_check_mark:',
            'escalated': ':rotating_light:'
        }.get(action, ':bell:')
        
        payload = {
            'channel': channel,
            'username': 'Extension Monitor',
            'icon_emoji': ':robot_face:',
            'attachments': [{
                'color': color,
                'title': f"{emoji} Alert {action.title()}: {alert_data['name']}",
                'text': alert_data['description'],
                'fields': [
                    {'title': 'Severity', 'value': alert_data['severity'], 'short': True},
                    {'title': 'Alert ID', 'value': alert_data['alert_id'], 'short': True}
                ],
                'footer': 'Extension Monitoring System',
                'ts': int(datetime.utcnow().timestamp())
            }]
        }
        
        if action == 'triggered':
            payload['attachments'][0]['fields'].append({
                'title': 'Threshold', 'value': str(alert_data['threshold']), 'short': True
            })
        elif action == 'resolved':
            payload['attachments'][0]['fields'].append({
                'title': 'Duration', 'value': f"{alert_data['duration_seconds']:.1f}s", 'short': True
            })
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack notification sent for alert {alert_data['alert_id']}")
                    else:
                        logger.error(f"Slack notification failed: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

    async def _send_discord_notification(self, alert_data: Dict[str, Any], action: str, config: Dict[str, Any]):
        """Send Discord notification."""
        webhook_url = config.get('webhook_url')
        
        if not webhook_url:
            logger.warning("No Discord webhook URL configured")
            return
        
        color = {
            'critical': 16711680,  # Red
            'error': 16753920,     # Orange
            'warning': 16776960,   # Yellow
            'info': 65535          # Cyan
        }.get(alert_data['severity'], 8421504)  # Gray
        
        embed = {
            'title': f"Alert {action.title()}: {alert_data['name']}",
            'description': alert_data['description'],
            'color': color,
            'fields': [
                {'name': 'Severity', 'value': alert_data['severity'], 'inline': True},
                {'name': 'Alert ID', 'value': alert_data['alert_id'], 'inline': True}
            ],
            'footer': {'text': 'Extension Monitoring System'},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        payload = {'embeds': [embed]}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status in [200, 204]:
                        logger.info(f"Discord notification sent for alert {alert_data['alert_id']}")
                    else:
                        logger.error(f"Discord notification failed: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")

    async def _send_log_notification(self, alert_data: Dict[str, Any], action: str, config: Dict[str, Any]):
        """Send log notification."""
        log_level = config.get('level', 'warning').upper()
        
        message = f"Alert {action}: {alert_data['name']} - {alert_data['description']}"
        
        if log_level == 'CRITICAL':
            logger.critical(message)
        elif log_level == 'ERROR':
            logger.error(message)
        elif log_level == 'WARNING':
            logger.warning(message)
        else:
            logger.info(message)

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alerting system statistics."""
        active_alerts = sum(1 for rule in self.alert_rules.values() if rule.is_active)
        total_rules = len(self.alert_rules)
        
        # Count alerts by severity
        severity_counts = {}
        for rule in self.alert_rules.values():
            if rule.is_active:
                severity_counts[rule.severity] = severity_counts.get(rule.severity, 0) + 1
        
        # Recent alert activity
        recent_alerts = [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert.get('triggered_at', alert.get('resolved_at', alert.get('escalated_at', '1970-01-01T00:00:00')))) > datetime.utcnow() - timedelta(hours=24)
        ]
        
        return {
            'active_alerts': active_alerts,
            'total_rules': total_rules,
            'severity_breakdown': severity_counts,
            'recent_activity_24h': len(recent_alerts),
            'configured_channels': list(self.notification_configs.keys()),
            'escalation_tasks_active': len(self.escalation_tasks),
            'total_notifications_sent': sum(rule.notification_count for rule in self.alert_rules.values()),
            'last_updated': datetime.utcnow().isoformat()
        }


# Global alerting system instance
extension_alerting = ExtensionAlertingSystem()