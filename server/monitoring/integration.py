"""
Extension Monitoring Integration

Integration utilities to connect monitoring system with existing
extension authentication and service infrastructure.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import time

from .extension_metrics_dashboard import extension_dashboard
from .alerting_system import extension_alerting, NotificationChannel
from .performance_monitor import extension_performance_monitor

logger = logging.getLogger(__name__)


class ExtensionMonitoringIntegration:
    """Integration layer for extension monitoring system."""

    def __init__(self):
        self.initialized = False
        self.monitoring_tasks = []

    async def initialize(self, config: Dict[str, Any] = None):
        """Initialize the monitoring integration."""
        if self.initialized:
            logger.warning("Monitoring integration already initialized")
            return

        config = config or {}
        
        try:
            # Configure notification channels
            await self._configure_notifications(config.get('notifications', {}))
            
            # Start monitoring systems
            await self._start_monitoring_systems(config.get('monitoring', {}))
            
            # Setup integration hooks
            self._setup_integration_hooks()
            
            self.initialized = True
            logger.info("Extension monitoring integration initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize monitoring integration: {e}")
            raise

    async def shutdown(self):
        """Shutdown the monitoring integration."""
        if not self.initialized:
            return

        try:
            # Stop monitoring systems
            await extension_dashboard.stop_monitoring()
            await extension_performance_monitor.stop_monitoring()
            
            # Cancel monitoring tasks
            for task in self.monitoring_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            self.monitoring_tasks.clear()
            self.initialized = False
            
            logger.info("Extension monitoring integration shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during monitoring integration shutdown: {e}")

    async def _configure_notifications(self, notification_config: Dict[str, Any]):
        """Configure notification channels for alerting."""
        
        # Configure email notifications
        if 'email' in notification_config:
            email_config = notification_config['email']
            extension_alerting.configure_notification_channel(
                NotificationChannel.EMAIL,
                email_config
            )
            logger.info("Configured email notifications")
        
        # Configure Slack notifications
        if 'slack' in notification_config:
            slack_config = notification_config['slack']
            extension_alerting.configure_notification_channel(
                NotificationChannel.SLACK,
                slack_config
            )
            logger.info("Configured Slack notifications")
        
        # Configure webhook notifications
        if 'webhook' in notification_config:
            webhook_config = notification_config['webhook']
            extension_alerting.configure_notification_channel(
                NotificationChannel.WEBHOOK,
                webhook_config
            )
            logger.info("Configured webhook notifications")
        
        # Configure Discord notifications
        if 'discord' in notification_config:
            discord_config = notification_config['discord']
            extension_alerting.configure_notification_channel(
                NotificationChannel.DISCORD,
                discord_config
            )
            logger.info("Configured Discord notifications")

    async def _start_monitoring_systems(self, monitoring_config: Dict[str, Any]):
        """Start all monitoring systems."""
        
        # Start main dashboard monitoring
        dashboard_interval = monitoring_config.get('dashboard_check_interval', 30)
        await extension_dashboard.start_monitoring(dashboard_interval)
        
        # Start performance monitoring
        resource_interval = monitoring_config.get('resource_check_interval', 30)
        await extension_performance_monitor.start_monitoring(resource_interval)
        
        # Start alerting evaluation loop
        alert_interval = monitoring_config.get('alert_check_interval', 15)
        alert_task = asyncio.create_task(self._alerting_loop(alert_interval))
        self.monitoring_tasks.append(alert_task)
        
        logger.info("Started all monitoring systems")

    def _setup_integration_hooks(self):
        """Setup integration hooks with existing systems."""
        
        # Add performance alert callback
        extension_performance_monitor.add_alert_callback(self._handle_performance_alert)
        
        logger.info("Setup monitoring integration hooks")

    async def _alerting_loop(self, check_interval: int):
        """Main alerting evaluation loop."""
        while True:
            try:
                # Get current metrics
                auth_metrics = extension_dashboard.metrics_collector.get_auth_metrics()
                health_metrics = extension_dashboard.metrics_collector.get_service_health_metrics()
                api_metrics = extension_dashboard.metrics_collector.get_api_performance_metrics()
                
                # Prepare metrics for alert evaluation
                current_metrics = {
                    'auth_failure_rate': (
                        auth_metrics['failure_count'] / auth_metrics['total_requests'] * 100
                        if auth_metrics['total_requests'] > 0 else 0
                    ),
                    'service_health_percentage': health_metrics['health_percentage'],
                    'api_error_rate': api_metrics['error_rate'],
                    'avg_response_time': api_metrics['average_response_time'] * 1000  # Convert to ms
                }
                
                # Evaluate alerts
                await extension_alerting.evaluate_alerts(current_metrics)
                
                await asyncio.sleep(check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alerting loop: {e}")
                await asyncio.sleep(check_interval)

    async def _handle_performance_alert(self, alert: Dict[str, Any]):
        """Handle performance alerts from the performance monitor."""
        logger.warning(f"Performance alert: {alert['type']} - {alert}")
        
        # You could forward these to the main alerting system or handle separately
        # For now, just log them

    # Integration methods for external systems to use

    def record_auth_success(self, response_time: float, user_id: str = None):
        """Record successful authentication (integration method)."""
        if self.initialized:
            extension_dashboard.record_auth_success(response_time, user_id)

    def record_auth_failure(self, response_time: float, error_type: str, user_id: str = None):
        """Record authentication failure (integration method)."""
        if self.initialized:
            extension_dashboard.record_auth_failure(response_time, error_type, user_id)

    def record_token_refresh(self, response_time: float, success: bool):
        """Record token refresh attempt (integration method)."""
        if self.initialized:
            extension_dashboard.record_token_refresh(response_time, success)

    def record_service_health(self, service_name: str, status: str, response_time: float = None):
        """Record service health status (integration method)."""
        if self.initialized:
            extension_dashboard.record_service_health(service_name, status, response_time)

    def record_api_request(self, endpoint: str, method: str, status_code: int, response_time: float):
        """Record API request metrics (integration method)."""
        if self.initialized:
            extension_dashboard.record_api_request(endpoint, method, status_code, response_time)
            extension_performance_monitor.record_request(endpoint, method, response_time, status_code)

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get overall monitoring system status."""
        if not self.initialized:
            return {
                'initialized': False,
                'status': 'not_initialized'
            }
        
        dashboard_data = extension_dashboard.get_dashboard_data()
        performance_summary = extension_performance_monitor.get_performance_summary()
        alert_stats = extension_alerting.get_alert_statistics()
        
        return {
            'initialized': True,
            'status': 'active' if dashboard_data['monitoring_active'] else 'inactive',
            'dashboard': {
                'active': dashboard_data['monitoring_active'],
                'auth_success_rate': dashboard_data['authentication']['success_rate'],
                'service_health': dashboard_data['service_health']['health_percentage'],
                'active_alerts': len(dashboard_data['active_alerts'])
            },
            'performance': {
                'active': performance_summary['monitoring_active'],
                'total_requests': performance_summary['total_requests'],
                'error_rate': performance_summary['error_rate'],
                'avg_response_time': performance_summary['average_response_time']
            },
            'alerting': {
                'active_alerts': alert_stats['active_alerts'],
                'total_rules': alert_stats['total_rules'],
                'notifications_sent': alert_stats['total_notifications_sent']
            },
            'last_updated': datetime.utcnow().isoformat()
        }


# Global monitoring integration instance
monitoring_integration = ExtensionMonitoringIntegration()


# Convenience functions for easy integration
async def initialize_monitoring(config: Dict[str, Any] = None):
    """Initialize extension monitoring system."""
    await monitoring_integration.initialize(config)


async def shutdown_monitoring():
    """Shutdown extension monitoring system."""
    await monitoring_integration.shutdown()


def record_auth_success(response_time: float, user_id: str = None):
    """Record successful authentication."""
    monitoring_integration.record_auth_success(response_time, user_id)


def record_auth_failure(response_time: float, error_type: str, user_id: str = None):
    """Record authentication failure."""
    monitoring_integration.record_auth_failure(response_time, error_type, user_id)


def record_token_refresh(response_time: float, success: bool):
    """Record token refresh attempt."""
    monitoring_integration.record_token_refresh(response_time, success)


def record_service_health(service_name: str, status: str, response_time: float = None):
    """Record service health status."""
    monitoring_integration.record_service_health(service_name, status, response_time)


def record_api_request(endpoint: str, method: str, status_code: int, response_time: float):
    """Record API request metrics."""
    monitoring_integration.record_api_request(endpoint, method, status_code, response_time)


def get_monitoring_status() -> Dict[str, Any]:
    """Get monitoring system status."""
    return monitoring_integration.get_monitoring_status()