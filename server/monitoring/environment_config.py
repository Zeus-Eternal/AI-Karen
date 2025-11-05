"""
Extension Monitoring Configuration Examples

Example configurations for different deployment scenarios.
"""

import os
from typing import Dict, Any

# Development configuration
DEVELOPMENT_CONFIG: Dict[str, Any] = {
    'notifications': {
        'log': {
            'enabled': True,
            'level': 'warning'
        },
        'webhook': {
            'enabled': False,
            'url': 'http://localhost:8080/test-webhook'
        }
    },
    'monitoring': {
        'dashboard_check_interval': 10,  # More frequent in dev
        'resource_check_interval': 15,
        'alert_check_interval': 5
    },
    'performance': {
        'response_time_threshold': 5.0,  # More lenient in dev
        'error_rate_threshold': 10.0,
        'cpu_threshold': 90.0,
        'memory_threshold': 90.0
    }
}

# Staging configuration
STAGING_CONFIG: Dict[str, Any] = {
    'notifications': {
        'slack': {
            'enabled': True,
            'webhook_url': os.getenv('SLACK_WEBHOOK_URL_STAGING'),
            'channel': '#alerts-staging'
        },
        'email': {
            'enabled': True,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD'),
            'from_email': 'alerts-staging@example.com',
            'to_emails': ['dev-team@example.com']
        },
        'log': {
            'enabled': True,
            'level': 'info'
        }
    },
    'monitoring': {
        'dashboard_check_interval': 30,
        'resource_check_interval': 30,
        'alert_check_interval': 15
    },
    'performance': {
        'response_time_threshold': 3.0,
        'error_rate_threshold': 7.0,
        'cpu_threshold': 85.0,
        'memory_threshold': 85.0
    }
}

# Production configuration
PRODUCTION_CONFIG: Dict[str, Any] = {
    'notifications': {
        'slack': {
            'enabled': True,
            'webhook_url': os.getenv('SLACK_WEBHOOK_URL_PROD'),
            'channel': '#alerts-production'
        },
        'email': {
            'enabled': True,
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD'),
            'from_email': os.getenv('ALERT_FROM_EMAIL', 'alerts@example.com'),
            'to_emails': os.getenv('ALERT_TO_EMAILS', '').split(',')
        },
        'discord': {
            'enabled': bool(os.getenv('DISCORD_WEBHOOK_URL')),
            'webhook_url': os.getenv('DISCORD_WEBHOOK_URL')
        },
        'webhook': {
            'enabled': bool(os.getenv('ALERT_WEBHOOK_URL')),
            'url': os.getenv('ALERT_WEBHOOK_URL'),
            'headers': {
                'Authorization': f"Bearer {os.getenv('ALERT_WEBHOOK_TOKEN')}",
                'Content-Type': 'application/json'
            }
        },
        'log': {
            'enabled': True,
            'level': 'warning'
        }
    },
    'monitoring': {
        'dashboard_check_interval': 30,
        'resource_check_interval': 30,
        'alert_check_interval': 15
    },
    'performance': {
        'response_time_threshold': 2.0,
        'error_rate_threshold': 5.0,
        'cpu_threshold': 80.0,
        'memory_threshold': 85.0
    }
}

# High-traffic production configuration
HIGH_TRAFFIC_CONFIG: Dict[str, Any] = {
    'notifications': {
        'slack': {
            'enabled': True,
            'webhook_url': os.getenv('SLACK_WEBHOOK_URL_PROD'),
            'channel': '#alerts-critical'
        },
        'email': {
            'enabled': True,
            'smtp_server': os.getenv('SMTP_SERVER'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD'),
            'from_email': os.getenv('ALERT_FROM_EMAIL'),
            'to_emails': os.getenv('ALERT_TO_EMAILS', '').split(',')
        },
        'webhook': {
            'enabled': True,
            'url': os.getenv('PAGERDUTY_WEBHOOK_URL'),
            'headers': {
                'Authorization': f"Token token={os.getenv('PAGERDUTY_TOKEN')}",
                'Content-Type': 'application/json'
            }
        }
    },
    'monitoring': {
        'dashboard_check_interval': 15,  # More frequent monitoring
        'resource_check_interval': 15,
        'alert_check_interval': 10
    },
    'performance': {
        'response_time_threshold': 1.0,  # Stricter thresholds
        'error_rate_threshold': 2.0,
        'cpu_threshold': 70.0,
        'memory_threshold': 80.0
    },
    'retention': {
        'metrics_hours': 48,  # Longer retention
        'alerts_days': 30
    }
}

def get_config_for_environment(environment: str = None) -> Dict[str, Any]:
    """Get configuration for the specified environment."""
    if environment is None:
        environment = os.getenv('ENVIRONMENT', 'development').lower()
    
    config_map = {
        'development': DEVELOPMENT_CONFIG,
        'dev': DEVELOPMENT_CONFIG,
        'staging': STAGING_CONFIG,
        'stage': STAGING_CONFIG,
        'production': PRODUCTION_CONFIG,
        'prod': PRODUCTION_CONFIG,
        'high-traffic': HIGH_TRAFFIC_CONFIG
    }
    
    return config_map.get(environment, DEVELOPMENT_CONFIG)

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate monitoring configuration."""
    required_sections = ['notifications', 'monitoring']
    
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required configuration section: {section}")
    
    # Validate notification channels
    notifications = config['notifications']
    for channel, channel_config in notifications.items():
        if not isinstance(channel_config, dict):
            raise ValueError(f"Invalid configuration for notification channel: {channel}")
        
        if channel == 'email' and channel_config.get('enabled'):
            required_email_fields = ['smtp_server', 'from_email', 'to_emails']
            for field in required_email_fields:
                if not channel_config.get(field):
                    raise ValueError(f"Missing required email configuration: {field}")
        
        if channel == 'slack' and channel_config.get('enabled'):
            if not channel_config.get('webhook_url'):
                raise ValueError("Missing required Slack webhook_url")
        
        if channel == 'webhook' and channel_config.get('enabled'):
            if not channel_config.get('url'):
                raise ValueError("Missing required webhook URL")
    
    # Validate monitoring intervals
    monitoring = config['monitoring']
    required_intervals = ['dashboard_check_interval', 'resource_check_interval', 'alert_check_interval']
    for interval in required_intervals:
        if interval not in monitoring or monitoring[interval] <= 0:
            raise ValueError(f"Invalid monitoring interval: {interval}")
    
    return True

# Environment variable documentation
ENV_VARS_DOCUMENTATION = """
Required Environment Variables for Production:

Email Notifications:
- SMTP_SERVER: SMTP server hostname (e.g., smtp.gmail.com)
- SMTP_PORT: SMTP server port (default: 587)
- SMTP_USERNAME: SMTP username
- SMTP_PASSWORD: SMTP password or app password
- ALERT_FROM_EMAIL: From email address for alerts
- ALERT_TO_EMAILS: Comma-separated list of recipient emails

Slack Notifications:
- SLACK_WEBHOOK_URL_PROD: Slack webhook URL for production alerts
- SLACK_WEBHOOK_URL_STAGING: Slack webhook URL for staging alerts

Discord Notifications:
- DISCORD_WEBHOOK_URL: Discord webhook URL

Webhook Notifications:
- ALERT_WEBHOOK_URL: Custom webhook URL for alerts
- ALERT_WEBHOOK_TOKEN: Authentication token for webhook

General:
- ENVIRONMENT: Deployment environment (development/staging/production)

Example .env file:
ENVIRONMENT=production
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alerts@example.com
SMTP_PASSWORD=your_app_password
ALERT_FROM_EMAIL=alerts@example.com
ALERT_TO_EMAILS=admin@example.com,team@example.com
SLACK_WEBHOOK_URL_PROD=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK
"""