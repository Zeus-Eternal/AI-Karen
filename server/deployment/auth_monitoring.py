"""
Authentication monitoring and alerting system for deployment.
Monitors authentication health and sends alerts for issues.
"""

import logging
import asyncio
import json
import smtplib
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
try:
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
except ImportError:
    # Fallback for systems without email support
    MimeText = None
    MimeMultipart = None
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
import aiohttp

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"

@dataclass
class Alert:
    id: str
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    created_at: datetime
    updated_at: datetime
    source: str
    metadata: Dict[str, Any]
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None

class AuthMetrics:
    """Tracks authentication metrics for monitoring."""
    
    def __init__(self):
        self.reset_metrics()
    
    def reset_metrics(self):
        """Reset all metrics to zero."""
        self.total_auth_attempts = 0
        self.successful_auths = 0
        self.failed_auths = 0
        self.token_refreshes = 0
        self.token_expirations = 0
        self.permission_denials = 0
        self.service_errors = 0
        self.response_times = []
        self.last_reset = datetime.utcnow()
    
    def record_auth_attempt(self, success: bool, response_time_ms: float):
        """Record an authentication attempt."""
        self.total_auth_attempts += 1
        self.response_times.append(response_time_ms)
        
        if success:
            self.successful_auths += 1
        else:
            self.failed_auths += 1
    
    def record_token_refresh(self):
        """Record a token refresh."""
        self.token_refreshes += 1
    
    def record_token_expiration(self):
        """Record a token expiration."""
        self.token_expirations += 1
    
    def record_permission_denial(self):
        """Record a permission denial."""
        self.permission_denials += 1
    
    def record_service_error(self):
        """Record a service error."""
        self.service_errors += 1
    
    def get_success_rate(self) -> float:
        """Get authentication success rate."""
        if self.total_auth_attempts == 0:
            return 1.0
        return self.successful_auths / self.total_auth_attempts
    
    def get_average_response_time(self) -> float:
        """Get average response time."""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        return {
            'total_auth_attempts': self.total_auth_attempts,
            'successful_auths': self.successful_auths,
            'failed_auths': self.failed_auths,
            'success_rate': self.get_success_rate(),
            'token_refreshes': self.token_refreshes,
            'token_expirations': self.token_expirations,
            'permission_denials': self.permission_denials,
            'service_errors': self.service_errors,
            'average_response_time_ms': self.get_average_response_time(),
            'last_reset': self.last_reset.isoformat()
        }

class AlertManager:
    """Manages alerts for authentication monitoring."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alerts: Dict[str, Alert] = {}
        self.alert_handlers: List[Callable] = []
        self.alerts_file = Path(config.get('alerts_file', 'auth_alerts.json'))
        
        # Load existing alerts
        asyncio.create_task(self.load_alerts())
    
    async def load_alerts(self):
        """Load alerts from file."""
        try:
            if self.alerts_file.exists():
                async with aiofiles.open(self.alerts_file, 'r') as f:
                    content = await f.read()
                
                alerts_data = json.loads(content) if content.strip() else {}
                
                for alert_id, alert_data in alerts_data.items():
                    # Convert datetime strings back to datetime objects
                    alert_data['created_at'] = datetime.fromisoformat(alert_data['created_at'])
                    alert_data['updated_at'] = datetime.fromisoformat(alert_data['updated_at'])
                    
                    if alert_data.get('resolved_at'):
                        alert_data['resolved_at'] = datetime.fromisoformat(alert_data['resolved_at'])
                    if alert_data.get('acknowledged_at'):
                        alert_data['acknowledged_at'] = datetime.fromisoformat(alert_data['acknowledged_at'])
                    
                    # Convert enum strings back to enums
                    alert_data['severity'] = AlertSeverity(alert_data['severity'])
                    alert_data['status'] = AlertStatus(alert_data['status'])
                    
                    self.alerts[alert_id] = Alert(**alert_data)
        
        except Exception as e:
            logger.error(f"Failed to load alerts: {e}")
    
    async def save_alerts(self):
        """Save alerts to file."""
        try:
            # Convert alerts to serializable format
            alerts_data = {}
            for alert_id, alert in self.alerts.items():
                alert_dict = asdict(alert)
                
                # Convert datetime objects to strings
                alert_dict['created_at'] = alert.created_at.isoformat()
                alert_dict['updated_at'] = alert.updated_at.isoformat()
                
                if alert.resolved_at:
                    alert_dict['resolved_at'] = alert.resolved_at.isoformat()
                if alert.acknowledged_at:
                    alert_dict['acknowledged_at'] = alert.acknowledged_at.isoformat()
                
                # Convert enums to strings
                alert_dict['severity'] = alert.severity.value
                alert_dict['status'] = alert.status.value
                
                alerts_data[alert_id] = alert_dict
            
            # Save to file
            self.alerts_file.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(self.alerts_file, 'w') as f:
                await f.write(json.dumps(alerts_data, indent=2))
        
        except Exception as e:
            logger.error(f"Failed to save alerts: {e}")
    
    def add_alert_handler(self, handler: Callable):
        """Add an alert handler function."""
        self.alert_handlers.append(handler)
    
    async def create_alert(self, 
                          title: str, 
                          description: str, 
                          severity: AlertSeverity, 
                          source: str,
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new alert."""
        alert_id = f"auth_{int(datetime.utcnow().timestamp())}_{len(self.alerts)}"
        
        alert = Alert(
            id=alert_id,
            title=title,
            description=description,
            severity=severity,
            status=AlertStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            source=source,
            metadata=metadata or {}
        )
        
        self.alerts[alert_id] = alert
        await self.save_alerts()
        
        # Notify handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
        
        logger.warning(f"Created alert: {title} ({severity.value})")
        return alert_id  
  
    async def resolve_alert(self, alert_id: str, resolved_by: Optional[str] = None) -> bool:
        """Resolve an alert."""
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.updated_at = datetime.utcnow()
        
        if resolved_by:
            alert.metadata['resolved_by'] = resolved_by
        
        await self.save_alerts()
        logger.info(f"Resolved alert: {alert.title}")
        return True
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert."""
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = acknowledged_by
        alert.updated_at = datetime.utcnow()
        
        await self.save_alerts()
        logger.info(f"Acknowledged alert: {alert.title} by {acknowledged_by}")
        return True
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return [alert for alert in self.alerts.values() 
                if alert.status == AlertStatus.ACTIVE]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Get alerts by severity level."""
        return [alert for alert in self.alerts.values() 
                if alert.severity == severity]

class AuthMonitor:
    """Main authentication monitoring system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics = AuthMetrics()
        self.alert_manager = AlertManager(config.get('alerting', {}))
        self.monitoring_active = False
        
        # Monitoring thresholds
        self.success_rate_threshold = config.get('success_rate_threshold', 0.95)
        self.response_time_threshold = config.get('response_time_threshold_ms', 1000)
        self.error_rate_threshold = config.get('error_rate_threshold', 0.05)
        self.check_interval = config.get('check_interval_seconds', 60)
        
        # Setup alert handlers
        self.setup_alert_handlers()
    
    def setup_alert_handlers(self):
        """Setup alert notification handlers."""
        # Email handler
        if self.config.get('email_alerts', {}).get('enabled', False):
            self.alert_manager.add_alert_handler(self.send_email_alert)
        
        # Webhook handler
        if self.config.get('webhook_alerts', {}).get('enabled', False):
            self.alert_manager.add_alert_handler(self.send_webhook_alert)
        
        # Slack handler
        if self.config.get('slack_alerts', {}).get('enabled', False):
            self.alert_manager.add_alert_handler(self.send_slack_alert)
    
    async def start_monitoring(self):
        """Start the monitoring loop."""
        self.monitoring_active = True
        logger.info("Starting authentication monitoring")
        
        while self.monitoring_active:
            try:
                await self.check_metrics()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def stop_monitoring(self):
        """Stop the monitoring loop."""
        self.monitoring_active = False
        logger.info("Stopping authentication monitoring")
    
    async def check_metrics(self):
        """Check metrics and create alerts if thresholds are exceeded."""
        metrics = self.metrics.get_metrics_summary()
        
        # Check success rate
        if metrics['success_rate'] < self.success_rate_threshold:
            await self.alert_manager.create_alert(
                title="Low Authentication Success Rate",
                description=f"Authentication success rate ({metrics['success_rate']:.2%}) is below threshold ({self.success_rate_threshold:.2%})",
                severity=AlertSeverity.HIGH,
                source="auth_monitor",
                metadata=metrics
            )
        
        # Check response time
        if metrics['average_response_time_ms'] > self.response_time_threshold:
            await self.alert_manager.create_alert(
                title="High Authentication Response Time",
                description=f"Average response time ({metrics['average_response_time_ms']:.1f}ms) exceeds threshold ({self.response_time_threshold}ms)",
                severity=AlertSeverity.MEDIUM,
                source="auth_monitor",
                metadata=metrics
            )
        
        # Check error rate
        error_rate = metrics['service_errors'] / max(metrics['total_auth_attempts'], 1)
        if error_rate > self.error_rate_threshold:
            await self.alert_manager.create_alert(
                title="High Authentication Error Rate",
                description=f"Service error rate ({error_rate:.2%}) exceeds threshold ({self.error_rate_threshold:.2%})",
                severity=AlertSeverity.HIGH,
                source="auth_monitor",
                metadata=metrics
            )
        
        # Check for excessive permission denials
        if metrics['total_auth_attempts'] > 0:
            denial_rate = metrics['permission_denials'] / metrics['total_auth_attempts']
            if denial_rate > 0.1:  # 10% denial rate threshold
                await self.alert_manager.create_alert(
                    title="High Permission Denial Rate",
                    description=f"Permission denial rate ({denial_rate:.2%}) is unusually high",
                    severity=AlertSeverity.MEDIUM,
                    source="auth_monitor",
                    metadata=metrics
                )
    
    async def send_email_alert(self, alert: Alert):
        """Send email alert notification."""
        try:
            email_config = self.config.get('email_alerts', {})
            
            if not email_config.get('enabled', False):
                return
            
            # Create email message
            msg = MimeMultipart()
            msg['From'] = email_config.get('from_address')
            msg['To'] = ', '.join(email_config.get('to_addresses', []))
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            # Email body
            body = f"""
Authentication Alert

Title: {alert.title}
Severity: {alert.severity.value.upper()}
Source: {alert.source}
Created: {alert.created_at.isoformat()}

Description:
{alert.description}

Metadata:
{json.dumps(alert.metadata, indent=2)}

Alert ID: {alert.id}
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(
                email_config.get('smtp_host', 'localhost'),
                email_config.get('smtp_port', 587)
            )
            
            if email_config.get('use_tls', True):
                server.starttls()
            
            if email_config.get('username') and email_config.get('password'):
                server.login(email_config['username'], email_config['password'])
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Sent email alert for: {alert.title}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def send_webhook_alert(self, alert: Alert):
        """Send webhook alert notification."""
        try:
            webhook_config = self.config.get('webhook_alerts', {})
            
            if not webhook_config.get('enabled', False):
                return
            
            webhook_url = webhook_config.get('url')
            if not webhook_url:
                return
            
            # Prepare webhook payload
            payload = {
                'alert_id': alert.id,
                'title': alert.title,
                'description': alert.description,
                'severity': alert.severity.value,
                'status': alert.status.value,
                'source': alert.source,
                'created_at': alert.created_at.isoformat(),
                'metadata': alert.metadata
            }
            
            # Send webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Sent webhook alert for: {alert.title}")
                    else:
                        logger.error(f"Webhook alert failed with status {response.status}")
        
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    async def send_slack_alert(self, alert: Alert):
        """Send Slack alert notification."""
        try:
            slack_config = self.config.get('slack_alerts', {})
            
            if not slack_config.get('enabled', False):
                return
            
            webhook_url = slack_config.get('webhook_url')
            if not webhook_url:
                return
            
            # Determine color based on severity
            color_map = {
                AlertSeverity.LOW: '#36a64f',      # Green
                AlertSeverity.MEDIUM: '#ff9500',   # Orange
                AlertSeverity.HIGH: '#ff0000',     # Red
                AlertSeverity.CRITICAL: '#8b0000'  # Dark Red
            }
            
            # Prepare Slack payload
            payload = {
                'attachments': [{
                    'color': color_map.get(alert.severity, '#ff0000'),
                    'title': alert.title,
                    'text': alert.description,
                    'fields': [
                        {
                            'title': 'Severity',
                            'value': alert.severity.value.upper(),
                            'short': True
                        },
                        {
                            'title': 'Source',
                            'value': alert.source,
                            'short': True
                        },
                        {
                            'title': 'Alert ID',
                            'value': alert.id,
                            'short': True
                        },
                        {
                            'title': 'Created',
                            'value': alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
                            'short': True
                        }
                    ],
                    'footer': 'Authentication Monitor',
                    'ts': int(alert.created_at.timestamp())
                }]
            }
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Sent Slack alert for: {alert.title}")
                    else:
                        logger.error(f"Slack alert failed with status {response.status}")
        
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    def record_auth_event(self, event_type: str, success: bool = True, 
                         response_time_ms: float = 0, metadata: Optional[Dict] = None):
        """Record an authentication event for monitoring."""
        if event_type == 'auth_attempt':
            self.metrics.record_auth_attempt(success, response_time_ms)
        elif event_type == 'token_refresh':
            self.metrics.record_token_refresh()
        elif event_type == 'token_expiration':
            self.metrics.record_token_expiration()
        elif event_type == 'permission_denial':
            self.metrics.record_permission_denial()
        elif event_type == 'service_error':
            self.metrics.record_service_error()
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            'monitoring_active': self.monitoring_active,
            'metrics': self.metrics.get_metrics_summary(),
            'active_alerts': len(self.alert_manager.get_active_alerts()),
            'thresholds': {
                'success_rate': self.success_rate_threshold,
                'response_time_ms': self.response_time_threshold,
                'error_rate': self.error_rate_threshold
            }
        }

# Global monitor instance
auth_monitor: Optional[AuthMonitor] = None

def initialize_auth_monitor(config: Dict[str, Any]) -> AuthMonitor:
    """Initialize the global authentication monitor."""
    global auth_monitor
    auth_monitor = AuthMonitor(config)
    return auth_monitor

def get_auth_monitor() -> Optional[AuthMonitor]:
    """Get the global authentication monitor instance."""
    return auth_monitor

async def main():
    """Example usage of authentication monitoring."""
    config = {
        'success_rate_threshold': 0.95,
        'response_time_threshold_ms': 1000,
        'error_rate_threshold': 0.05,
        'check_interval_seconds': 60,
        'email_alerts': {
            'enabled': True,
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True,
            'from_address': 'alerts@example.com',
            'to_addresses': ['admin@example.com'],
            'username': 'alerts@example.com',
            'password': 'app_password'
        },
        'webhook_alerts': {
            'enabled': True,
            'url': 'https://hooks.example.com/webhook'
        },
        'slack_alerts': {
            'enabled': True,
            'webhook_url': 'https://hooks.slack.com/services/...'
        }
    }
    
    monitor = initialize_auth_monitor(config)
    
    try:
        # Start monitoring in background
        monitoring_task = asyncio.create_task(monitor.start_monitoring())
        
        # Simulate some authentication events
        for i in range(100):
            success = i % 10 != 0  # 90% success rate
            response_time = 200 + (i % 5) * 100  # Variable response time
            
            monitor.record_auth_event('auth_attempt', success, response_time)
            
            if i % 20 == 0:
                monitor.record_auth_event('token_refresh')
            
            await asyncio.sleep(0.1)
        
        # Let monitoring run for a bit
        await asyncio.sleep(5)
        
        # Check status
        status = monitor.get_monitoring_status()
        print(f"Monitoring status: {json.dumps(status, indent=2)}")
        
    finally:
        await monitor.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())