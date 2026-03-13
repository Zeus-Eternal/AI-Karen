"""
Error Notification System

This module provides comprehensive error notification capabilities with multiple
channels, intelligent alerting, and user-friendly message delivery.
"""

import asyncio
import json
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from .error_monitoring import ErrorAlert, AlertLevel


class NotificationChannel(Enum):
    """Types of notification channels."""
    
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    IN_APP = "in_app"
    LOG = "log"
    CUSTOM = "custom"


class NotificationStatus(Enum):
    """Status of notification delivery."""
    
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class NotificationMessage:
    """Notification message with delivery information."""
    
    channel: NotificationChannel
    recipient: str
    subject: str
    message: str
    alert_level: AlertLevel
    timestamp: datetime
    status: NotificationStatus = NotificationStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "channel": self.channel.value,
            "recipient": self.recipient,
            "subject": self.subject,
            "message": self.message,
            "alert_level": self.alert_level.value,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "metadata": self.metadata
        }


class NotificationChannelBase(ABC):
    """Base class for notification channels."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", True)
    
    @abstractmethod
    async def send(self, message: NotificationMessage) -> bool:
        """Send notification message."""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate channel configuration."""
        pass
    
    def format_message(self, alert: ErrorAlert, template: Optional[str] = None) -> tuple[str, str]:
        """Format alert into subject and message."""
        if template:
            # Use custom template
            subject = template.format(
                alert_level=alert.alert_level.value,
                title=alert.title,
                message=alert.message
            )
            message = template.format(
                alert_level=alert.alert_level.value,
                title=alert.title,
                message=alert.message,
                details=json.dumps(alert.metadata, indent=2)
            )
        else:
            # Use default formatting
            subject = f"[{alert.alert_level.value.upper()}] {alert.title}"
            
            message_parts = [
                f"Alert: {alert.title}",
                f"Level: {alert.alert_level.value}",
                f"Message: {alert.message}",
                f"Time: {alert.timestamp.isoformat()}"
            ]
            
            if alert.pattern:
                message_parts.append(f"Pattern: {alert.pattern.pattern_type.value}")
                message_parts.append(f"Confidence: {alert.pattern.confidence:.2f}")
            
            message = "\n\n".join(message_parts)
        
        return subject, message


class EmailNotificationChannel(NotificationChannelBase):
    """Email notification channel."""
    
    async def send(self, message: NotificationMessage) -> bool:
        """Send email notification."""
        if not self.enabled:
            return False
        
        try:
            # Create email message
            email_msg = MimeMultipart()
            email_msg['From'] = self.config["sender"]
            email_msg['To'] = message.recipient
            email_msg['Subject'] = message.subject
            
            # Add body
            body = MimeText(message.message, 'plain')
            email_msg.attach(body)
            
            # Send email
            with smtplib.SMTP(
                self.config["smtp_server"],
                self.config["smtp_port"]
            ) as server:
                server.starttls()
                server.login(self.config["username"], self.config["password"])
                server.send_message(email_msg)
            
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def validate_config(self) -> bool:
        """Validate email configuration."""
        required_keys = ["smtp_server", "smtp_port", "sender", "username", "password"]
        return all(key in self.config for key in required_keys)


class SlackNotificationChannel(NotificationChannelBase):
    """Slack notification channel."""
    
    async def send(self, message: NotificationMessage) -> bool:
        """Send Slack notification."""
        if not self.enabled:
            return False
        
        try:
            import aiohttp
            
            # Prepare Slack payload
            payload = {
                "channel": message.recipient,
                "username": self.config.get("bot_name", "Error Bot"),
                "text": message.subject,
                "attachments": [
                    {
                        "color": self._get_color_for_level(message.alert_level),
                        "fields": [
                            {
                                "title": "Level",
                                "value": message.alert_level.value,
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": message.timestamp.isoformat(),
                                "short": True
                            }
                        ]
                    }
                ]
            }
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config["webhook_url"],
                    json=payload,
                    timeout=30
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            print(f"Failed to send Slack notification: {e}")
            return False
    
    def _get_color_for_level(self, level: AlertLevel) -> str:
        """Get Slack color for alert level."""
        color_map = {
            AlertLevel.INFO: "good",
            AlertLevel.WARNING: "warning",
            AlertLevel.ERROR: "danger",
            AlertLevel.CRITICAL: "danger",
            AlertLevel.FATAL: "#ff0000"
        }
        return color_map.get(level, "warning")
    
    def validate_config(self) -> bool:
        """Validate Slack configuration."""
        return "webhook_url" in self.config


class WebhookNotificationChannel(NotificationChannelBase):
    """Webhook notification channel."""
    
    async def send(self, message: NotificationMessage) -> bool:
        """Send webhook notification."""
        if not self.enabled:
            return False
        
        try:
            import aiohttp
            
            # Prepare webhook payload
            payload = {
                "alert_level": message.alert_level.value,
                "subject": message.subject,
                "message": message.message,
                "timestamp": message.timestamp.isoformat(),
                "metadata": message.metadata
            }
            
            # Add custom headers if configured
            headers = self.config.get("headers", {})
            
            # Send webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config["url"],
                    json=payload,
                    headers=headers,
                    timeout=self.config.get("timeout", 30)
                ) as response:
                    return response.status in [200, 201, 202]
                    
        except Exception as e:
            print(f"Failed to send webhook notification: {e}")
            return False
    
    def validate_config(self) -> bool:
        """Validate webhook configuration."""
        return "url" in self.config


class InAppNotificationChannel(NotificationChannelBase):
    """In-app notification channel."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.notifications: List[NotificationMessage] = []
        self.max_notifications = config.get("max_notifications", 1000)
    
    async def send(self, message: NotificationMessage) -> bool:
        """Send in-app notification."""
        if not self.enabled:
            return False
        
        try:
            # Store notification
            self.notifications.append(message)
            
            # Maintain max size
            if len(self.notifications) > self.max_notifications:
                self.notifications = self.notifications[-self.max_notifications:]
            
            # Trigger callback if configured
            callback = self.config.get("callback")
            if callback:
                await callback(message)
            
            return True
            
        except Exception as e:
            print(f"Failed to send in-app notification: {e}")
            return False
    
    def get_notifications(
        self,
        limit: Optional[int] = None,
        alert_level: Optional[AlertLevel] = None
    ) -> List[NotificationMessage]:
        """Get stored notifications."""
        notifications = self.notifications
        
        # Filter by alert level
        if alert_level:
            notifications = [n for n in notifications if n.alert_level == alert_level]
        
        # Limit results
        if limit:
            notifications = notifications[-limit:]
        
        return notifications
    
    def clear_notifications(self) -> None:
        """Clear all notifications."""
        self.notifications.clear()
    
    def validate_config(self) -> bool:
        """Validate in-app configuration."""
        return True  # No specific validation required


class ErrorNotifier:
    """
    Comprehensive error notification system with multiple channels.
    
    Features:
    - Multiple notification channels
    - Intelligent message formatting
    - Delivery tracking and retry
    - Channel-specific configuration
    - Alert level filtering
    - Rate limiting
    """
    
    def __init__(self):
        self.channels: Dict[NotificationChannel, NotificationChannelBase] = {}
        self.notification_history: List[NotificationMessage] = []
        self.rate_limits: Dict[NotificationChannel, Dict[str, Any]] = {}
        self.callbacks: List[Callable[[NotificationMessage], None]] = []
        
        # Configuration
        self.config = {
            "max_history": 10000,
            "default_retry_attempts": 3,
            "retry_delay": 5.0,
            "enable_rate_limiting": True,
            "rate_limit_window": 300,  # 5 minutes
            "rate_limit_max": 50,  # Max 50 notifications per window
        }
    
    def register_channel(
        self,
        channel: NotificationChannel,
        handler: NotificationChannelBase
    ) -> bool:
        """Register notification channel."""
        if not handler.validate_config():
            return False
        
        self.channels[channel] = handler
        self.rate_limits[channel] = {
            "count": 0,
            "window_start": datetime.utcnow()
        }
        
        return True
    
    def unregister_channel(self, channel: NotificationChannel) -> bool:
        """Unregister notification channel."""
        if channel in self.channels:
            del self.channels[channel]
            if channel in self.rate_limits:
                del self.rate_limits[channel]
            return True
        return False
    
    async def send_alert(
        self,
        alert: ErrorAlert,
        channels: Optional[List[NotificationChannel]] = None,
        recipients: Optional[Dict[NotificationChannel, List[str]]] = None
    ) -> Dict[NotificationChannel, bool]:
        """
        Send alert through notification channels.
        
        Args:
            alert: Error alert to send
            channels: Optional list of channels to use
            recipients: Optional mapping of channels to recipients
            
        Returns:
            Dictionary mapping channels to delivery status
        """
        # Determine channels to use
        if channels is None:
            channels = list(self.channels.keys())
        
        results = {}
        
        for channel in channels:
            if channel not in self.channels:
                results[channel] = False
                continue
            
            # Check rate limiting
            if self.config["enable_rate_limiting"] and self._is_rate_limited(channel):
                results[channel] = False
                continue
            
            # Get recipients for channel
            channel_recipients = recipients.get(channel, []) if recipients else []
            if not channel_recipients:
                # Use default recipients from config
                channel_recipients = self.channels[channel].config.get("default_recipients", [])
            
            if not channel_recipients:
                results[channel] = False
                continue
            
            # Format message
            subject, message = self.channels[channel].format_message(alert)
            
            # Send to all recipients
            channel_success = False
            for recipient in channel_recipients:
                notification = NotificationMessage(
                    channel=channel,
                    recipient=recipient,
                    subject=subject,
                    message=message,
                    alert_level=alert.alert_level,
                    timestamp=datetime.utcnow(),
                    max_attempts=self.config["default_retry_attempts"]
                )
                
                # Send with retry logic
                success = await self._send_with_retry(notification)
                if success:
                    channel_success = True
                
                # Store in history
                self.notification_history.append(notification)
            
            results[channel] = channel_success
        
        return results
    
    async def send_message(
        self,
        subject: str,
        message: str,
        alert_level: AlertLevel,
        channels: Optional[List[NotificationChannel]] = None,
        recipients: Optional[Dict[NotificationChannel, List[str]]] = None
    ) -> Dict[NotificationChannel, bool]:
        """Send custom message through notification channels."""
        # Create mock alert
        mock_alert = ErrorAlert(
            alert_level=alert_level,
            title=subject,
            message=message
        )
        
        return await self.send_alert(mock_alert, channels, recipients)
    
    def add_callback(self, callback: Callable[[NotificationMessage], None]) -> None:
        """Add callback for notification events."""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[NotificationMessage], None]) -> bool:
        """Remove notification callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            return True
        return False
    
    def get_notification_history(
        self,
        limit: Optional[int] = None,
        channel: Optional[NotificationChannel] = None,
        alert_level: Optional[AlertLevel] = None
    ) -> List[NotificationMessage]:
        """Get notification history."""
        history = self.notification_history
        
        # Filter by channel
        if channel:
            history = [n for n in history if n.channel == channel]
        
        # Filter by alert level
        if alert_level:
            history = [n for n in history if n.alert_level == alert_level]
        
        # Limit results
        if limit:
            history = history[-limit:]
        
        return history
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get notification statistics."""
        total_notifications = len(self.notification_history)
        
        # Count by channel
        channel_counts = {}
        for notification in self.notification_history:
            channel = notification.channel
            channel_counts[channel] = channel_counts.get(channel, 0) + 1
        
        # Count by status
        status_counts = {}
        for notification in self.notification_history:
            status = notification.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count by alert level
        level_counts = {}
        for notification in self.notification_history:
            level = notification.alert_level
            level_counts[level] = level_counts.get(level, 0) + 1
        
        return {
            "total_notifications": total_notifications,
            "channels": channel_counts,
            "statuses": status_counts,
            "alert_levels": level_counts,
            "registered_channels": list(self.channels.keys()),
            "rate_limits": self.rate_limits
        }
    
    async def _send_with_retry(self, notification: NotificationMessage) -> bool:
        """Send notification with retry logic."""
        channel = notification.channel
        handler = self.channels[channel]
        
        for attempt in range(notification.max_attempts):
            try:
                notification.attempts = attempt + 1
                
                if attempt > 0:
                    # Add delay for retries
                    await asyncio.sleep(self.config["retry_delay"])
                    notification.status = NotificationStatus.RETRYING
                else:
                    notification.status = NotificationStatus.PENDING
                
                success = await handler.send(notification)
                
                if success:
                    notification.status = NotificationStatus.SENT
                    return True
                else:
                    notification.status = NotificationStatus.FAILED
                    
            except Exception as e:
                print(f"Notification attempt {attempt + 1} failed: {e}")
                notification.status = NotificationStatus.FAILED
        
        return False
    
    def _is_rate_limited(self, channel: NotificationChannel) -> bool:
        """Check if channel is rate limited."""
        if not self.config["enable_rate_limiting"]:
            return False
        
        rate_limit = self.rate_limits.get(channel)
        if not rate_limit:
            return False
        
        now = datetime.utcnow()
        window_elapsed = (now - rate_limit["window_start"]).total_seconds()
        
        # Reset window if expired
        if window_elapsed > self.config["rate_limit_window"]:
            rate_limit["count"] = 0
            rate_limit["window_start"] = now
            return False
        
        # Check limit
        return rate_limit["count"] >= self.config["rate_limit_max"]
    
    def _update_rate_limit(self, channel: NotificationChannel) -> None:
        """Update rate limit counter."""
        if channel in self.rate_limits:
            self.rate_limits[channel]["count"] += 1


# Global error notifier instance
error_notifier = ErrorNotifier()

# Register default channels
error_notifier.register_channel(
    NotificationChannel.IN_APP,
    InAppNotificationChannel({"enabled": True})
)