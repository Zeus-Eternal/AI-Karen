"""
Configuration for extension security features
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseSettings, Field


class SecurityConfig(BaseSettings):
    """Security configuration settings"""
    
    # Code signing settings
    signing_enabled: bool = Field(True, description="Enable extension code signing")
    private_key_path: Optional[str] = Field(None, description="Path to private signing key")
    public_keys_dir: str = Field("keys/public", description="Directory containing public keys")
    key_id: str = Field("default", description="Default key identifier")
    signature_required: bool = Field(False, description="Require signatures for all extensions")
    
    # Audit logging settings
    audit_enabled: bool = Field(True, description="Enable audit logging")
    audit_retention_days: int = Field(90, description="Audit log retention period in days")
    high_risk_threshold: int = Field(5, description="Risk score threshold for high-risk events")
    
    # Access control settings
    access_control_enabled: bool = Field(True, description="Enable access control policies")
    default_deny: bool = Field(True, description="Default to deny access when no policy matches")
    policy_cache_ttl: int = Field(300, description="Policy cache TTL in seconds")
    
    # Vulnerability scanning settings
    vulnerability_scanning_enabled: bool = Field(True, description="Enable vulnerability scanning")
    scan_on_install: bool = Field(True, description="Scan extensions on installation")
    scan_schedule: str = Field("0 2 * * *", description="Cron schedule for periodic scans")
    safety_check_enabled: bool = Field(True, description="Enable safety dependency checking")
    
    # Security thresholds
    max_critical_vulnerabilities: int = Field(0, description="Maximum allowed critical vulnerabilities")
    max_high_vulnerabilities: int = Field(5, description="Maximum allowed high vulnerabilities")
    min_security_score: float = Field(70.0, description="Minimum required security score")
    
    # Compliance settings
    compliance_reports_enabled: bool = Field(True, description="Enable compliance reporting")
    compliance_report_schedule: str = Field("0 0 1 * *", description="Monthly compliance report schedule")
    
    # Integration settings
    webhook_url: Optional[str] = Field(None, description="Webhook URL for security alerts")
    slack_webhook_url: Optional[str] = Field(None, description="Slack webhook for notifications")
    email_notifications: bool = Field(False, description="Enable email notifications")
    
    class Config:
        env_prefix = "EXTENSION_SECURITY_"
        case_sensitive = False


class SecurityPolicyConfig:
    """Default security policies configuration"""
    
    @staticmethod
    def get_default_dangerous_patterns() -> Dict[str, List[str]]:
        """Get default dangerous code patterns"""
        return {
            'code_injection': [
                r'eval\s*\(',
                r'exec\s*\(',
                r'subprocess\.call\s*\(',
                r'os\.system\s*\(',
                r'__import__\s*\('
            ],
            'sql_injection': [
                r'\.execute\s*\(\s*["\'].*%.*["\']',
                r'\.execute\s*\(\s*f["\'].*{.*}.*["\']',
                r'query\s*\+\s*',
                r'SELECT.*\+.*FROM'
            ],
            'path_traversal': [
                r'\.\./',
                r'\.\.\\',
                r'os\.path\.join\s*\(.*\.\.',
                r'open\s*\(.*\.\.'
            ],
            'hardcoded_secrets': [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']'
            ],
            'unsafe_deserialization': [
                r'pickle\.loads\s*\(',
                r'yaml\.load\s*\(',
                r'json\.loads\s*\(.*user'
            ]
        }
    
    @staticmethod
    def get_vulnerable_packages() -> Dict[str, Dict[str, str]]:
        """Get known vulnerable package versions"""
        return {
            'requests': {'<2.20.0': 'CVE-2018-18074'},
            'urllib3': {'<1.24.2': 'CVE-2019-11324'},
            'pyyaml': {'<5.1': 'CVE-2017-18342'},
            'jinja2': {'<2.10.1': 'CVE-2019-10906'},
            'flask': {'<1.0': 'CVE-2018-1000656'},
            'django': {'<2.2.13': 'CVE-2020-13254'},
            'pillow': {'<6.2.0': 'CVE-2019-16865'},
            'cryptography': {'<3.2': 'CVE-2020-25659'}
        }
    
    @staticmethod
    def get_sensitive_paths() -> List[str]:
        """Get list of sensitive system paths"""
        return [
            '/etc/',
            '/proc/',
            '/sys/',
            '/dev/',
            '/root/',
            '/boot/',
            'C:\\Windows\\',
            'C:\\Program Files\\',
            'C:\\ProgramData\\',
            '/usr/bin/',
            '/usr/sbin/',
            '/bin/',
            '/sbin/'
        ]
    
    @staticmethod
    def get_default_access_policies() -> List[Dict]:
        """Get default access control policies"""
        return [
            {
                'name': 'admin_full_access',
                'description': 'Full access for administrators',
                'rules': [
                    {
                        'resource': '*',
                        'action': '*',
                        'conditions': {'user_roles': ['admin', 'super_admin']},
                        'effect': 'allow'
                    }
                ]
            },
            {
                'name': 'user_read_access',
                'description': 'Read access for regular users',
                'rules': [
                    {
                        'resource': 'data/*',
                        'action': 'read',
                        'conditions': {'user_roles': ['user', 'admin', 'super_admin']},
                        'effect': 'allow'
                    },
                    {
                        'resource': 'api/public/*',
                        'action': '*',
                        'conditions': {'user_roles': ['user', 'admin', 'super_admin']},
                        'effect': 'allow'
                    }
                ]
            },
            {
                'name': 'deny_sensitive_operations',
                'description': 'Deny access to sensitive operations',
                'rules': [
                    {
                        'resource': 'system/*',
                        'action': 'delete',
                        'conditions': {},
                        'effect': 'deny'
                    },
                    {
                        'resource': 'config/*',
                        'action': 'write',
                        'conditions': {'user_roles': ['guest', 'user']},
                        'effect': 'deny'
                    }
                ]
            }
        ]


class SecurityAlertConfig:
    """Security alert configuration"""
    
    @staticmethod
    def get_alert_thresholds() -> Dict[str, int]:
        """Get alert thresholds for different security events"""
        return {
            'critical_vulnerabilities': 1,
            'high_risk_events_per_hour': 10,
            'failed_access_attempts_per_hour': 50,
            'policy_violations_per_day': 20,
            'security_score_threshold': 70
        }
    
    @staticmethod
    def get_notification_templates() -> Dict[str, str]:
        """Get notification message templates"""
        return {
            'critical_vulnerability': (
                "🚨 CRITICAL SECURITY ALERT\n"
                "Extension: {extension_name}\n"
                "Vulnerability: {vulnerability_title}\n"
                "Severity: {severity}\n"
                "Action Required: Immediate attention needed"
            ),
            'high_risk_activity': (
                "⚠️ HIGH RISK ACTIVITY DETECTED\n"
                "Extension: {extension_name}\n"
                "User: {user_id}\n"
                "Activity: {event_type}\n"
                "Risk Score: {risk_score}"
            ),
            'policy_violation': (
                "🔒 ACCESS POLICY VIOLATION\n"
                "Extension: {extension_name}\n"
                "User: {user_id}\n"
                "Resource: {resource}\n"
                "Action: {action}"
            ),
            'compliance_report': (
                "📊 COMPLIANCE REPORT GENERATED\n"
                "Tenant: {tenant_id}\n"
                "Report Type: {report_type}\n"
                "Compliance Score: {compliance_score}%\n"
                "Period: {period_start} to {period_end}"
            )
        }


# Global security configuration instance
security_config = SecurityConfig()
security_policy_config = SecurityPolicyConfig()
security_alert_config = SecurityAlertConfig()