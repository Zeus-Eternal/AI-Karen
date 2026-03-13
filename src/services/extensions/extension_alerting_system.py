"""
Extension Alerting System service for managing alerts and notifications for extensions.

This service provides capabilities for generating, managing, and delivering alerts
and notifications for extension events, errors, and status changes.
"""

from typing import Dict, List, Any, Optional, Set, Callable
import asyncio
import logging
import json
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from enum import Enum

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus, ServiceHealth


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class NotificationChannel(str, Enum):
    """Notification channel types."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    LOG = "log"


class ExtensionAlertingSystem(BaseService):
    """
    Extension Alerting System service for managing alerts and notifications for extensions.
    
    This service provides capabilities for generating, managing, and delivering alerts
    and notifications for extension events, errors, and status changes.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="extension_alerting_system"))
        self._initialized = False
        self._alerts: Dict[str, Dict[str, Any]] = {}  # alert_id -> alert_data
        self._alert_rules: Dict[str, Dict[str, Any]] = {}  # rule_name -> rule_data
        self._notification_channels: Dict[str, Dict[str, Any]] = {}  # channel_name -> channel_data
        self._alert_subscriptions: Dict[str, List[str]] = {}  # rule_name -> list_of_channel_names
        self._alert_history: List[Dict[str, Any]] = []  # list of alert_events
        self._notification_queue: List[Dict[str, Any]] = []  # queue of pending notifications
        self._notification_tasks: List[asyncio.Task] = []  # list of active notification tasks
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize the Extension Alerting System service."""
        if self._initialized:
            return
            
        try:
            self.logger.info("Initializing Extension Alerting System service")
            
            # Initialize alert system components
            self._alerts = {}
            self._alert_rules = {}
            self._notification_channels = {}
            self._alert_subscriptions = {}
            self._alert_history = []
            self._notification_queue = []
            self._notification_tasks = []
            
            # Create default alert rules
            self._alert_rules["extension_error"] = {
                "name": "extension_error",
                "description": "Alert when an extension reports an error",
                "severity": AlertSeverity.ERROR,
                "condition": lambda event: event.get("type") == "error" and event.get("source_type") == "extension",
                "enabled": True,
                "cooldown": 300  # 5 minutes
            }
            
            self._alert_rules["extension_down"] = {
                "name": "extension_down",
                "description": "Alert when an extension goes down",
                "severity": AlertSeverity.CRITICAL,
                "condition": lambda event: event.get("type") == "status_change" and 
                                    event.get("source_type") == "extension" and 
                                    event.get("new_status") == "down",
                "enabled": True,
                "cooldown": 60  # 1 minute
            }
            
            self._alert_rules["high_resource_usage"] = {
                "name": "high_resource_usage",
                "description": "Alert when an extension uses excessive resources",
                "severity": AlertSeverity.WARNING,
                "condition": lambda event: event.get("type") == "resource_usage" and 
                                    event.get("source_type") == "extension" and 
                                    (event.get("cpu_percent", 0) > 80 or 
                                     event.get("memory_percent", 0) > 80),
                "enabled": True,
                "cooldown": 300  # 5 minutes
            }
            
            # Create default notification channels
            self._notification_channels["log"] = {
                "name": "log",
                "type": NotificationChannel.LOG,
                "enabled": True,
                "config": {}
            }
            
            # Create default subscriptions
            self._alert_subscriptions["extension_error"] = ["log"]
            self._alert_subscriptions["extension_down"] = ["log"]
            self._alert_subscriptions["high_resource_usage"] = ["log"]
            
            # Start notification processor
            self._notification_tasks.append(asyncio.create_task(self._process_notifications()))
            
            self._initialized = True
            self._status = ServiceStatus.RUNNING
            self.logger.info("Extension Alerting System service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Extension Alerting System service: {str(e)}")
            self._status = ServiceStatus.ERROR
            raise
            
    async def create_alert_rule(self, rule_name: str, description: str, severity: AlertSeverity,
                               condition: Callable, enabled: bool = True, cooldown: int = 300) -> None:
        """Create a new alert rule."""
        async with self._lock:
            self._alert_rules[rule_name] = {
                "name": rule_name,
                "description": description,
                "severity": severity,
                "condition": condition,
                "enabled": enabled,
                "cooldown": cooldown,
                "last_triggered": None
            }
            
        self.logger.info(f"Created alert rule: {rule_name}")
        
    async def update_alert_rule(self, rule_name: str, updates: Dict[str, Any]) -> None:
        """Update an alert rule."""
        async with self._lock:
            if rule_name not in self._alert_rules:
                raise ValueError(f"Alert rule '{rule_name}' not found")
                
            # Update rule
            self._alert_rules[rule_name].update(updates)
            
        self.logger.info(f"Updated alert rule: {rule_name}")
        
    async def get_alert_rule(self, rule_name: str) -> Dict[str, Any]:
        """Get an alert rule."""
        async with self._lock:
            if rule_name not in self._alert_rules:
                raise ValueError(f"Alert rule '{rule_name}' not found")
                
            return self._alert_rules[rule_name].copy()
            
    async def list_alert_rules(self) -> List[str]:
        """List all alert rule names."""
        async with self._lock:
            return list(self._alert_rules.keys())
            
    async def delete_alert_rule(self, rule_name: str) -> None:
        """Delete an alert rule."""
        async with self._lock:
            if rule_name in self._alert_rules:
                del self._alert_rules[rule_name]
                
            if rule_name in self._alert_subscriptions:
                del self._alert_subscriptions[rule_name]
                
        self.logger.info(f"Deleted alert rule: {rule_name}")
        
    async def create_notification_channel(self, channel_name: str, channel_type: NotificationChannel,
                                      config: Dict[str, Any], enabled: bool = True) -> None:
        """Create a notification channel."""
        async with self._lock:
            self._notification_channels[channel_name] = {
                "name": channel_name,
                "type": channel_type,
                "enabled": enabled,
                "config": config
            }
            
        self.logger.info(f"Created notification channel: {channel_name}")
        
    async def update_notification_channel(self, channel_name: str, updates: Dict[str, Any]) -> None:
        """Update a notification channel."""
        async with self._lock:
            if channel_name not in self._notification_channels:
                raise ValueError(f"Notification channel '{channel_name}' not found")
                
            # Update channel
            self._notification_channels[channel_name].update(updates)
            
        self.logger.info(f"Updated notification channel: {channel_name}")
        
    async def get_notification_channel(self, channel_name: str) -> Dict[str, Any]:
        """Get a notification channel."""
        async with self._lock:
            if channel_name not in self._notification_channels:
                raise ValueError(f"Notification channel '{channel_name}' not found")
                
            return self._notification_channels[channel_name].copy()
            
    async def list_notification_channels(self) -> List[str]:
        """List all notification channel names."""
        async with self._lock:
            return list(self._notification_channels.keys())
            
    async def delete_notification_channel(self, channel_name: str) -> None:
        """Delete a notification channel."""
        async with self._lock:
            if channel_name in self._notification_channels:
                del self._notification_channels[channel_name]
                
            # Remove from subscriptions
            for rule_name, channels in self._alert_subscriptions.items():
                if channel_name in channels:
                    channels.remove(channel_name)
                    
        self.logger.info(f"Deleted notification channel: {channel_name}")
        
    async def subscribe_to_alerts(self, rule_name: str, channel_names: List[str]) -> None:
        """Subscribe to alerts from a rule."""
        async with self._lock:
            if rule_name not in self._alert_rules:
                raise ValueError(f"Alert rule '{rule_name}' not found")
                
            # Validate channels
            for channel_name in channel_names:
                if channel_name not in self._notification_channels:
                    raise ValueError(f"Notification channel '{channel_name}' not found")
                    
            # Set or update subscription
            self._alert_subscriptions[rule_name] = channel_names
            
        self.logger.info(f"Subscribed to alerts from rule: {rule_name}")
        
    async def get_subscription(self, rule_name: str) -> List[str]:
        """Get subscription for a rule."""
        async with self._lock:
            return self._alert_subscriptions.get(rule_name, []).copy()
            
    async def process_event(self, event: Dict[str, Any]) -> None:
        """Process an event and potentially generate alerts."""
        async with self._lock:
            for rule_name, rule in self._alert_rules.items():
                # Skip disabled rules
                if not rule.get("enabled", True):
                    continue
                    
                # Check cooldown
                last_triggered = rule.get("last_triggered")
                if last_triggered:
                    last_time = datetime.fromisoformat(last_triggered)
                    if datetime.now() - last_time < timedelta(seconds=rule.get("cooldown", 300)):
                        continue
                        
                # Check condition
                try:
                    if rule["condition"](event):
                        # Generate alert
                        alert_id = f"{rule_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        
                        alert = {
                            "id": alert_id,
                            "rule_name": rule_name,
                            "severity": rule["severity"],
                            "title": f"Alert: {rule['description']}",
                            "message": f"Event triggered alert rule '{rule_name}': {event}",
                            "event": event,
                            "status": AlertStatus.ACTIVE,
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat()
                        }
                        
                        self._alerts[alert_id] = alert
                        
                        # Update rule last triggered time
                        rule["last_triggered"] = datetime.now().isoformat()
                        
                        # Add to notification queue
                        channels = self._alert_subscriptions.get(rule_name, [])
                        for channel_name in channels:
                            if channel_name in self._notification_channels:
                                channel = self._notification_channels[channel_name]
                                if channel.get("enabled", True):
                                    self._notification_queue.append({
                                        "alert_id": alert_id,
                                        "channel_name": channel_name,
                                        "timestamp": datetime.now().isoformat()
                                    })
                                    
                        # Record alert event
                        self._alert_history.append({
                            "alert_id": alert_id,
                            "rule_name": rule_name,
                            "event": event,
                            "timestamp": datetime.now().isoformat(),
                            "action": "created"
                        })
                        
                        self.logger.warning(f"Generated alert {alert_id} from rule {rule_name}")
                        
                except Exception as e:
                    self.logger.error(f"Error processing event with rule {rule_name}: {str(e)}")
                    
    async def get_alert(self, alert_id: str) -> Dict[str, Any]:
        """Get an alert."""
        async with self._lock:
            if alert_id not in self._alerts:
                raise ValueError(f"Alert '{alert_id}' not found")
                
            return self._alerts[alert_id].copy()
            
    async def list_alerts(self, status: Optional[AlertStatus] = None, severity: Optional[AlertSeverity] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """List alerts."""
        async with self._lock:
            alerts = list(self._alerts.values())
            
            # Filter by status
            if status:
                alerts = [alert for alert in alerts if alert.get("status") == status]
                
            # Filter by severity
            if severity:
                alerts = [alert for alert in alerts if alert.get("severity") == severity]
                
            # Sort by creation time (newest first)
            alerts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            # Limit results
            return alerts[:limit]
            
    async def update_alert_status(self, alert_id: str, status: AlertStatus,
                                 acknowledged_by: Optional[str] = None, resolved_by: Optional[str] = None) -> None:
        """Update the status of an alert."""
        async with self._lock:
            if alert_id not in self._alerts:
                raise ValueError(f"Alert '{alert_id}' not found")
                
            # Update alert
            self._alerts[alert_id]["status"] = status
            self._alerts[alert_id]["updated_at"] = datetime.now().isoformat()
            
            if acknowledged_by:
                self._alerts[alert_id]["acknowledged_by"] = acknowledged_by
                self._alerts[alert_id]["acknowledged_at"] = datetime.now().isoformat()
                
            if resolved_by:
                self._alerts[alert_id]["resolved_by"] = resolved_by
                self._alerts[alert_id]["resolved_at"] = datetime.now().isoformat()
                
            # Record alert event
            self._alert_history.append({
                "alert_id": alert_id,
                "timestamp": datetime.now().isoformat(),
                "action": f"status_changed_to_{status}"
            })
            
        self.logger.info(f"Updated alert {alert_id} status to {status}")
        
    async def get_alert_history(self, alert_id: Optional[str] = None, rule_name: Optional[str] = None,
                             limit: int = 50) -> List[Dict[str, Any]]:
        """Get alert history."""
        async with self._lock:
            history = self._alert_history.copy()
            
            # Filter by alert_id
            if alert_id:
                history = [event for event in history if event.get("alert_id") == alert_id]
                
            # Filter by rule_name
            if rule_name:
                history = [event for event in history if event.get("rule_name") == rule_name]
                
            # Sort by timestamp (newest first)
            history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Limit results
            return history[:limit]
            
    async def _process_notifications(self) -> None:
        """Background task to process notifications."""
        try:
            while True:
                # Get next notification from queue
                async with self._lock:
                    if not self._notification_queue:
                        await asyncio.sleep(1)
                        continue
                        
                    notification = self._notification_queue.pop(0)
                    
                try:
                    # Get alert and channel
                    alert = await self.get_alert(notification["alert_id"])
                    channel = await self.get_notification_channel(notification["channel_name"])
                    
                    # Send notification
                    await self._send_notification(alert, channel)
                    
                    # Record notification event
                    async with self._lock:
                        self._alert_history.append({
                            "alert_id": notification["alert_id"],
                            "channel_name": notification["channel_name"],
                            "timestamp": datetime.now().isoformat(),
                            "action": "notification_sent"
                        })
                        
                except Exception as e:
                    self.logger.error(f"Error sending notification for alert {notification['alert_id']}: {str(e)}")
                    
                    # Record failed notification event
                    async with self._lock:
                        self._alert_history.append({
                            "alert_id": notification["alert_id"],
                            "channel_name": notification["channel_name"],
                            "timestamp": datetime.now().isoformat(),
                            "action": "notification_failed",
                            "error": str(e)
                        })
                        
        except asyncio.CancelledError:
            # Task was cancelled
            pass
        except Exception as e:
            self.logger.error(f"Fatal error in notification processor: {str(e)}")
            
    async def _send_notification(self, alert: Dict[str, Any], channel: Dict[str, Any]) -> None:
        """Send a notification to a channel."""
        channel_type = channel.get("type")
        config = channel.get("config", {})
        
        if channel_type == NotificationChannel.LOG:
            # Log notification
            self.logger.warning(f"ALERT: {alert['title']} - {alert['message']}")
            
        elif channel_type == NotificationChannel.EMAIL:
            # Send email notification
            smtp_server = config.get("smtp_server", "localhost")
            smtp_port = config.get("smtp_port", 587)
            username = config.get("username", "")
            password = config.get("password", "")
            from_addr = config.get("from_addr", "")
            to_addrs = config.get("to_addrs", [])
            
            if not to_addrs:
                raise ValueError("No recipients specified for email notification")
                
            # Create message
            msg = MIMEText(alert["message"])
            msg["Subject"] = alert["title"]
            msg["From"] = from_addr
            msg["To"] = ", ".join(to_addrs)
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if username and password:
                    server.starttls()
                    server.login(username, password)
                server.send_message(msg)
                
        elif channel_type == NotificationChannel.WEBHOOK:
            # Send webhook notification
            import aiohttp
            
            url = config.get("url")
            headers = config.get("headers", {})
            
            if not url:
                raise ValueError("No URL specified for webhook notification")
                
            # Prepare payload
            payload = {
                "alert": alert,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status >= 400:
                        raise ValueError(f"Webhook returned status {response.status}")
                        
        elif channel_type == NotificationChannel.SLACK:
            # Send Slack notification
            import aiohttp
            
            webhook_url = config.get("webhook_url")
            
            if not webhook_url:
                raise ValueError("No webhook URL specified for Slack notification")
                
            # Prepare payload
            payload = {
                "text": f"*{alert['title']}*\n{alert['message']}",
                "attachments": [
                    {
                        "color": self._get_slack_color(alert.get("severity") or AlertSeverity.INFO),
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.get("severity", "").upper(),
                                "short": True
                            },
                            {
                                "title": "Status",
                                "value": alert.get("status", "").upper(),
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": alert.get("created_at", ""),
                                "short": False
                            }
                        ]
                    }
                ]
            }
            
            # Send Slack message
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status >= 400:
                        raise ValueError(f"Slack webhook returned status {response.status}")
                        
        else:
            raise ValueError(f"Unsupported notification channel type: {channel_type}")
            
    def _get_slack_color(self, severity: AlertSeverity) -> str:
        """Get Slack color for alert severity."""
        color_map = {
            AlertSeverity.INFO: "#36a64f",  # green
            AlertSeverity.WARNING: "#ff9500",  # orange
            AlertSeverity.ERROR: "#ff0000",  # red
            AlertSeverity.CRITICAL: "#990000"  # dark red
        }
        return color_map.get(severity, "#808080")  # gray default
        
    async def health_check(self) -> ServiceHealth:
        """Perform a health check of the service."""
        status = ServiceStatus.RUNNING if self._initialized else ServiceStatus.INITIALIZING
        
        # Check if notification processor is running
        if self._notification_tasks:
            for task in self._notification_tasks:
                if task.done():
                    status = ServiceStatus.ERROR
                    break
                    
        return ServiceHealth(
            status=status,
            last_check=datetime.now(),
            details={
                "alert_rules": len(self._alert_rules),
                "notification_channels": len(self._notification_channels),
                "active_alerts": len([a for a in self._alerts.values() if a.get("status") == AlertStatus.ACTIVE]),
                "notification_queue": len(self._notification_queue)
            }
        )
        
    async def shutdown(self) -> None:
        """Shutdown the service."""
        self.logger.info("Shutting down Extension Alerting System service")
        
        # Cancel notification tasks
        for task in self._notification_tasks:
            task.cancel()
            
        # Wait for all tasks to complete
        if self._notification_tasks:
            await asyncio.gather(*self._notification_tasks, return_exceptions=True)
            
        self._alerts.clear()
        self._alert_rules.clear()
        self._notification_channels.clear()
        self._alert_subscriptions.clear()
        self._alert_history.clear()
        self._notification_queue.clear()
        self._notification_tasks.clear()
        
        self._initialized = False
        self._status = ServiceStatus.SHUTDOWN
        self.logger.info("Extension Alerting System service shutdown complete")