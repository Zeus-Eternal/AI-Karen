#!/usr/bin/env python3
"""
Production Configuration Validator
Validates production environment settings and configuration files
"""

import json
import os
import re
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ValidationIssue:
    """Represents a configuration validation issue"""
    category: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    message: str
    file_path: Optional[str] = None
    recommendation: Optional[str] = None

class ProductionConfigValidator:
    """Validates production configuration settings"""
    
    def __init__(self):
        self.issues: List[ValidationIssue] = []
        self.config_files = {
            'env': '.env',
            'production_env': 'config/production.env',
            'production_json': 'config/production.json',
            'security_yml': 'config/security_production.yml',
            'logging_yml': 'config/logging_production.yml'
        }
        
    def add_issue(self, category: str, severity: str, message: str, 
                  file_path: Optional[str] = None, recommendation: Optional[str] = None):
        """Add a validation issue"""
        issue = ValidationIssue(category, severity, message, file_path, recommendation)
        self.issues.append(issue)
        
    def validate_environment_variables(self) -> None:
        """Validate environment variables for production"""
        print("🔍 Validating environment variables...")
        
        # Critical environment variables that must be changed from defaults
        critical_vars = {
            'AUTH_SECRET_KEY': 'change-me-in-production',
            'JWT_SECRET_KEY': 'change-me-in-production', 
            'MINIO_ACCESS_KEY': 'ai-karen-minio',
            'MINIO_SECRET_KEY': 'ai-karen-minio-secret',
            'AUTH_DATABASE_URL': 'karen_secure_pass_change_me'
        }
        
        # Security-related variables that should be set correctly
        security_vars = {
            'AUTH_DEV_MODE': 'false',
            'AUTH_ALLOW_DEV_LOGIN': 'false',
            'AUTH_SESSION_COOKIE_SECURE': 'true',
            'AUTH_ENABLE_SECURITY_FEATURES': 'true',
            'NODE_ENV': 'production',
            'ENVIRONMENT': 'production'
        }
        
        # Check if .env file exists
        env_file = Path('.env')
        if not env_file.exists():
            self.add_issue(
                'Environment',
                'HIGH',
                '.env file not found',
                '.env',
                'Copy config/production.env to .env and customize for your environment'
            )
            return
            
        # Read environment variables
        env_vars = {}
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        except Exception as e:
            self.add_issue(
                'Environment',
                'CRITICAL',
                f'Failed to read .env file: {str(e)}',
                '.env'
            )
            return
            
        # Validate critical variables
        for var, default_value in critical_vars.items():
            if var not in env_vars:
                self.add_issue(
                    'Security',
                    'CRITICAL',
                    f'Missing critical environment variable: {var}',
                    '.env',
                    f'Set {var} to a secure value'
                )
            elif default_value in env_vars[var]:
                self.add_issue(
                    'Security',
                    'CRITICAL',
                    f'Environment variable {var} contains default/insecure value',
                    '.env',
                    f'Change {var} to a secure production value'
                )
                
        # Validate security variables
        for var, expected_value in security_vars.items():
            if var not in env_vars:
                self.add_issue(
                    'Security',
                    'HIGH',
                    f'Missing security environment variable: {var}',
                    '.env',
                    f'Set {var}={expected_value}'
                )
            elif env_vars[var].lower() != expected_value.lower():
                self.add_issue(
                    'Security',
                    'HIGH',
                    f'Security variable {var} has incorrect value: {env_vars[var]}',
                    '.env',
                    f'Set {var}={expected_value}'
                )
                
        # Check for development URLs
        dev_patterns = [
            'localhost',
            '127.0.0.1',
            'dev',
            'test',
            'example.com'
        ]
        
        url_vars = [
            'KAREN_BACKEND_URL',
            'NEXT_PUBLIC_KAREN_BACKEND_URL',
            'NEXT_PUBLIC_BASE_URL',
            'AUTH_DATABASE_URL'
        ]
        
        for var in url_vars:
            if var in env_vars:
                for pattern in dev_patterns:
                    if pattern in env_vars[var].lower():
                        self.add_issue(
                            'Configuration',
                            'HIGH',
                            f'Variable {var} contains development URL: {env_vars[var]}',
                            '.env',
                            f'Update {var} to use production domain'
                        )
                        break
                        
    def validate_security_configuration(self) -> None:
        """Validate security configuration"""
        print("🔒 Validating security configuration...")
        
        security_file = Path(self.config_files['security_yml'])
        if not security_file.exists():
            self.add_issue(
                'Security',
                'HIGH',
                'Security configuration file not found',
                str(security_file),
                'Create security configuration file from template'
            )
            return
            
        try:
            with open(security_file, 'r') as f:
                security_config = yaml.safe_load(f)
        except Exception as e:
            self.add_issue(
                'Security',
                'CRITICAL',
                f'Failed to parse security configuration: {str(e)}',
                str(security_file)
            )
            return
            
        # Validate CSP configuration
        if 'content_security_policy' not in security_config:
            self.add_issue(
                'Security',
                'HIGH',
                'Content Security Policy not configured',
                str(security_file),
                'Configure CSP to prevent XSS attacks'
            )
        else:
            csp = security_config['content_security_policy']
            if "'unsafe-inline'" in str(csp.get('script_src', [])):
                self.add_issue(
                    'Security',
                    'MEDIUM',
                    'CSP allows unsafe-inline scripts',
                    str(security_file),
                    'Remove unsafe-inline from script-src if possible'
                )
                
        # Validate HSTS configuration
        headers = security_config.get('security_headers', {})
        hsts = headers.get('strict_transport_security', {})
        if not hsts or hsts.get('max_age', 0) < 31536000:
            self.add_issue(
                'Security',
                'MEDIUM',
                'HSTS max-age should be at least 1 year (31536000 seconds)',
                str(security_file),
                'Set HSTS max-age to 31536000 or higher'
            )
            
        # Validate password policy
        auth = security_config.get('authentication', {})
        password_policy = auth.get('password_policy', {})
        if password_policy.get('min_length', 0) < 12:
            self.add_issue(
                'Security',
                'MEDIUM',
                'Password minimum length should be at least 12 characters',
                str(security_file),
                'Set password min_length to 12 or higher'
            )
            
    def validate_logging_configuration(self) -> None:
        """Validate logging configuration"""
        print("📝 Validating logging configuration...")
        
        logging_file = Path(self.config_files['logging_yml'])
        if not logging_file.exists():
            self.add_issue(
                'Logging',
                'MEDIUM',
                'Logging configuration file not found',
                str(logging_file),
                'Create logging configuration for structured logging'
            )
            return
            
        try:
            with open(logging_file, 'r') as f:
                logging_config = yaml.safe_load(f)
        except Exception as e:
            self.add_issue(
                'Logging',
                'HIGH',
                f'Failed to parse logging configuration: {str(e)}',
                str(logging_file)
            )
            return
            
        # Check for log file paths
        handlers = logging_config.get('handlers', {})
        for handler_name, handler_config in handlers.items():
            if 'filename' in handler_config:
                log_path = Path(handler_config['filename'])
                log_dir = log_path.parent
                if not log_dir.exists():
                    self.add_issue(
                        'Logging',
                        'HIGH',
                        f'Log directory does not exist: {log_dir}',
                        str(logging_file),
                        f'Create log directory: mkdir -p {log_dir}'
                    )
                    
        # Check for sensitive data filters
        filters = logging_config.get('filters', {})
        if 'sensitive_data_filter' not in filters:
            self.add_issue(
                'Security',
                'MEDIUM',
                'Sensitive data filter not configured in logging',
                str(logging_file),
                'Add sensitive data filter to prevent logging secrets'
            )
            
    def validate_production_json(self) -> None:
        """Validate production JSON configuration"""
        print("⚙️ Validating production JSON configuration...")
        
        config_file = Path(self.config_files['production_json'])
        if not config_file.exists():
            self.add_issue(
                'Configuration',
                'MEDIUM',
                'Production JSON configuration not found',
                str(config_file),
                'Create production configuration file'
            )
            return
            
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except Exception as e:
            self.add_issue(
                'Configuration',
                'HIGH',
                f'Failed to parse production configuration: {str(e)}',
                str(config_file)
            )
            return
            
        # Validate environment setting
        if config.get('environment') != 'production':
            self.add_issue(
                'Configuration',
                'HIGH',
                f'Environment not set to production: {config.get("environment")}',
                str(config_file),
                'Set environment to "production"'
            )
            
        # Validate UI debug settings
        ui_config = config.get('ui', {})
        if ui_config.get('show_debug_info', True):
            self.add_issue(
                'Configuration',
                'MEDIUM',
                'Debug info enabled in UI configuration',
                str(config_file),
                'Set ui.show_debug_info to false'
            )
            
        if ui_config.get('enable_dev_tools', True):
            self.add_issue(
                'Configuration',
                'MEDIUM',
                'Development tools enabled in UI configuration',
                str(config_file),
                'Set ui.enable_dev_tools to false'
            )
            
        # Validate feature flags
        feature_flags = config.get('feature_flags', {})
        if feature_flags.get('experimental_features', True):
            self.add_issue(
                'Configuration',
                'MEDIUM',
                'Experimental features enabled',
                str(config_file),
                'Set feature_flags.experimental_features to false'
            )
            
    def validate_ssl_certificates(self) -> None:
        """Validate SSL certificate configuration"""
        print("🔐 Validating SSL certificates...")
        
        # Check if SSL is configured
        env_file = Path('.env')
        if env_file.exists():
            ssl_enabled = False
            cert_path = None
            key_path = None
            
            with open(env_file, 'r') as f:
                for line in f:
                    if 'SSL_ENABLED=true' in line:
                        ssl_enabled = True
                    elif 'SSL_CERT_PATH=' in line:
                        cert_path = line.split('=', 1)[1].strip()
                    elif 'SSL_KEY_PATH=' in line:
                        key_path = line.split('=', 1)[1].strip()
                        
            if ssl_enabled:
                if cert_path and not Path(cert_path).exists():
                    self.add_issue(
                        'SSL',
                        'CRITICAL',
                        f'SSL certificate file not found: {cert_path}',
                        '.env',
                        'Ensure SSL certificate file exists and is readable'
                    )
                    
                if key_path and not Path(key_path).exists():
                    self.add_issue(
                        'SSL',
                        'CRITICAL',
                        f'SSL private key file not found: {key_path}',
                        '.env',
                        'Ensure SSL private key file exists and is readable'
                    )
            else:
                self.add_issue(
                    'SSL',
                    'HIGH',
                    'SSL not enabled for production deployment',
                    '.env',
                    'Enable SSL by setting SSL_ENABLED=true and configuring certificates'
                )
                
    def validate_database_configuration(self) -> None:
        """Validate database configuration"""
        print("🗄️ Validating database configuration...")
        
        env_file = Path('.env')
        if not env_file.exists():
            return
            
        with open(env_file, 'r') as f:
            content = f.read()
            
        # Check for SQLite in production
        if 'sqlite' in content.lower():
            self.add_issue(
                'Database',
                'HIGH',
                'SQLite database detected in production configuration',
                '.env',
                'Use PostgreSQL for production deployment'
            )
            
        # Check for default database passwords
        if 'karen_secure_pass_change_me' in content:
            self.add_issue(
                'Security',
                'CRITICAL',
                'Default database password detected',
                '.env',
                'Change database password to a secure value'
            )
            
        # Check for localhost database
        if 'localhost' in content and 'AUTH_DATABASE_URL' in content:
            self.add_issue(
                'Configuration',
                'MEDIUM',
                'Database URL uses localhost',
                '.env',
                'Update database URL to use production database server'
            )
            
    def generate_report(self) -> Dict:
        """Generate validation report"""
        issues_by_severity = {
            'CRITICAL': [i for i in self.issues if i.severity == 'CRITICAL'],
            'HIGH': [i for i in self.issues if i.severity == 'HIGH'],
            'MEDIUM': [i for i in self.issues if i.severity == 'MEDIUM'],
            'LOW': [i for i in self.issues if i.severity == 'LOW']
        }
        
        total_issues = len(self.issues)
        critical_issues = len(issues_by_severity['CRITICAL'])
        high_issues = len(issues_by_severity['HIGH'])
        
        # Determine overall status
        if critical_issues > 0:
            status = 'NOT_READY'
        elif high_issues > 0:
            status = 'NEEDS_ATTENTION'
        elif total_issues > 0:
            status = 'MINOR_ISSUES'
        else:
            status = 'READY'
            
        return {
            'status': status,
            'total_issues': total_issues,
            'issues_by_severity': {
                'critical': critical_issues,
                'high': high_issues,
                'medium': len(issues_by_severity['MEDIUM']),
                'low': len(issues_by_severity['LOW'])
            },
            'issues': issues_by_severity
        }
        
    def print_report(self, report: Dict) -> None:
        """Print validation report"""
        print("\n" + "="*60)
        print("🔍 PRODUCTION CONFIGURATION VALIDATION REPORT")
        print("="*60)
        
        status_icons = {
            'READY': '✅',
            'MINOR_ISSUES': '⚠️',
            'NEEDS_ATTENTION': '🔶',
            'NOT_READY': '❌'
        }
        
        print(f"Overall Status: {status_icons.get(report['status'], '❓')} {report['status']}")
        print(f"Total Issues: {report['total_issues']}")
        print()
        
        severity_icons = {
            'CRITICAL': '🚨',
            'HIGH': '⚠️',
            'MEDIUM': '🔶',
            'LOW': '💡'
        }
        
        print("Issues by Severity:")
        for severity, count in report['issues_by_severity'].items():
            icon = severity_icons.get(severity.upper(), '❓')
            print(f"  {icon} {severity.title()}: {count}")
        print()
        
        # Print detailed issues
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            issues = report['issues'][severity]
            if issues:
                print(f"{severity_icons[severity]} {severity} Issues:")
                for issue in issues:
                    print(f"  • [{issue.category}] {issue.message}")
                    if issue.file_path:
                        print(f"    File: {issue.file_path}")
                    if issue.recommendation:
                        print(f"    Fix: {issue.recommendation}")
                    print()
                    
        # Print recommendations
        if report['status'] != 'READY':
            print("🔧 Next Steps:")
            if report['issues_by_severity']['critical'] > 0:
                print("  1. Address all CRITICAL issues before deployment")
            if report['issues_by_severity']['high'] > 0:
                print("  2. Fix HIGH priority issues for security and stability")
            if report['issues_by_severity']['medium'] > 0:
                print("  3. Consider fixing MEDIUM issues for best practices")
            print("  4. Re-run validation after making changes")
            print()
            
        print("="*60)
        
    def run_validation(self) -> Dict:
        """Run all validation checks"""
        print("🚀 Starting Production Configuration Validation")
        print("="*50)
        
        self.validate_environment_variables()
        self.validate_security_configuration()
        self.validate_logging_configuration()
        self.validate_production_json()
        self.validate_ssl_certificates()
        self.validate_database_configuration()
        
        report = self.generate_report()
        self.print_report(report)
        
        return report

def main():
    """Main function"""
    validator = ProductionConfigValidator()
    report = validator.run_validation()
    
    # Exit with appropriate code
    if report['status'] == 'NOT_READY':
        sys.exit(1)
    elif report['status'] == 'NEEDS_ATTENTION':
        sys.exit(2)
    elif report['status'] == 'MINOR_ISSUES':
        sys.exit(3)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()