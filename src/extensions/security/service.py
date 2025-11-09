"""
Main security service that integrates all security features
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from .models import SecurityScanRequest, VulnerabilityStatus, SecurityLevel
from .code_signing import ExtensionCodeSigner, ExtensionVerifier, ExtensionSignatureManager
from .audit_logger import ExtensionAuditLogger, ExtensionComplianceReporter, AuditEventType
from .access_control import ExtensionAccessControlManager
from .vulnerability_scanner import ExtensionVulnerabilityScanner
from .config import security_config, security_alert_config
from ..base.exceptions import ExtensionSecurityError, ExtensionPermissionError


class ExtensionSecurityService:
    """Main service for extension security management"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.audit_logger = ExtensionAuditLogger(db_session)
        self.access_manager = ExtensionAccessControlManager(db_session, self.audit_logger)
        self.vulnerability_scanner = ExtensionVulnerabilityScanner(db_session, self.audit_logger)
        self.compliance_reporter = ExtensionComplianceReporter(db_session, self.audit_logger)
        
        # Initialize signing components if enabled
        if security_config.signing_enabled:
            self.code_signer = ExtensionCodeSigner(
                security_config.private_key_path,
                security_config.key_id
            )
            self.verifier = ExtensionVerifier(Path(security_config.public_keys_dir))
            self.signature_manager = ExtensionSignatureManager(db_session)
        else:
            self.code_signer = None
            self.verifier = None
            self.signature_manager = None
    
    async def secure_extension_installation(
        self,
        extension_path: Path,
        extension_name: str,
        extension_version: str,
        tenant_id: str,
        user_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Perform comprehensive security checks during extension installation"""
        try:
            security_report = {
                'extension_name': extension_name,
                'extension_version': extension_version,
                'tenant_id': tenant_id,
                'checks_performed': [],
                'security_score': 100.0,
                'warnings': [],
                'errors': [],
                'allowed': True
            }
            
            # 1. Signature verification (if enabled and required)
            if security_config.signing_enabled and security_config.signature_required:
                try:
                    is_valid, verification_data = self.verifier.verify_extension(extension_path)
                    security_report['checks_performed'].append('signature_verification')
                    
                    if not is_valid:
                        security_report['errors'].append(f"Invalid signature: {verification_data.get('error', 'Unknown error')}")
                        security_report['allowed'] = False
                        security_report['security_score'] -= 50
                    else:
                        security_report['signature_valid'] = True
                        
                except Exception as e:
                    security_report['errors'].append(f"Signature verification failed: {e}")
                    security_report['allowed'] = False
            
            # 2. Vulnerability scanning (if enabled)
            if security_config.vulnerability_scanning_enabled and security_config.scan_on_install:
                try:
                    scan_request = SecurityScanRequest(
                        extension_name=extension_name,
                        extension_version=extension_version,
                        scan_types=['code', 'dependencies', 'permissions'],
                        deep_scan=False
                    )
                    
                    scan_result = self.vulnerability_scanner.scan_extension(
                        extension_path, extension_name, extension_version, scan_request
                    )
                    
                    security_report['checks_performed'].append('vulnerability_scan')
                    security_report['vulnerability_scan'] = {
                        'vulnerabilities_found': len(scan_result.vulnerabilities),
                        'security_score': scan_result.security_score,
                        'critical_count': len([v for v in scan_result.vulnerabilities if v.severity == SecurityLevel.CRITICAL]),
                        'high_count': len([v for v in scan_result.vulnerabilities if v.severity == SecurityLevel.HIGH])
                    }
                    
                    # Check against thresholds
                    critical_count = security_report['vulnerability_scan']['critical_count']
                    high_count = security_report['vulnerability_scan']['high_count']
                    
                    if critical_count > security_config.max_critical_vulnerabilities:
                        security_report['errors'].append(f"Too many critical vulnerabilities: {critical_count}")
                        security_report['allowed'] = False
                    
                    if high_count > security_config.max_high_vulnerabilities:
                        security_report['warnings'].append(f"High number of high-severity vulnerabilities: {high_count}")
                    
                    if scan_result.security_score < security_config.min_security_score:
                        security_report['warnings'].append(f"Security score below threshold: {scan_result.security_score}")
                    
                    security_report['security_score'] = min(security_report['security_score'], scan_result.security_score)
                    
                except Exception as e:
                    security_report['warnings'].append(f"Vulnerability scan failed: {e}")
            
            # 3. Create default access policies
            if security_config.access_control_enabled:
                try:
                    default_policies = self.access_manager.create_default_policies(
                        extension_name, tenant_id, user_id
                    )
                    security_report['checks_performed'].append('access_policy_creation')
                    security_report['default_policies_created'] = len(default_policies)
                    
                except Exception as e:
                    security_report['warnings'].append(f"Failed to create default policies: {e}")
            
            # 4. Log installation attempt
            self.audit_logger.log_extension_install(
                extension_name=extension_name,
                extension_version=extension_version,
                tenant_id=tenant_id,
                user_id=user_id,
                source=kwargs.get('source', 'unknown'),
                security_score=security_report['security_score'],
                checks_performed=security_report['checks_performed']
            )
            
            # 5. Send alerts if necessary
            await self._send_security_alerts(security_report, 'installation')
            
            return security_report
            
        except Exception as e:
            self.logger.error(f"Security check failed for {extension_name}: {e}")
            raise ExtensionSecurityError(f"Security check failed: {e}")
    
    async def enforce_runtime_security(
        self,
        extension_name: str,
        tenant_id: str,
        user_id: str,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Enforce security policies during runtime"""
        try:
            # Check access control policies
            if security_config.access_control_enabled:
                self.access_manager.enforce_access(
                    extension_name=extension_name,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    resource=resource,
                    action=action,
                    context=context
                )
            
            # Log the access attempt
            self.audit_logger.log_data_access(
                extension_name=extension_name,
                tenant_id=tenant_id,
                user_id=user_id,
                resource=resource,
                action=action,
                **context or {}
            )
            
        except ExtensionPermissionError:
            # Log security violation
            self.audit_logger.log_security_violation(
                extension_name=extension_name,
                tenant_id=tenant_id,
                violation_type='access_denied',
                details={
                    'resource': resource,
                    'action': action,
                    'context': context
                },
                user_id=user_id
            )
            raise
    
    async def perform_security_audit(
        self,
        tenant_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Perform comprehensive security audit"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get audit summary
            audit_summary = self.audit_logger.get_audit_summary(tenant_id, start_date, end_date)
            
            # Get vulnerability summary
            vulnerabilities = self.vulnerability_scanner.get_vulnerabilities()
            open_vulns = [v for v in vulnerabilities if v.status == VulnerabilityStatus.OPEN.value]
            critical_vulns = [v for v in open_vulns if v.severity == SecurityLevel.CRITICAL.value]
            
            # Get policy summary
            policies = self.access_manager.list_policies(tenant_id=tenant_id)
            active_policies = [p for p in policies if p.is_active]
            
            # Calculate overall security score
            security_score = self._calculate_overall_security_score(
                audit_summary, open_vulns, critical_vulns
            )
            
            audit_report = {
                'tenant_id': tenant_id,
                'audit_period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': days
                },
                'audit_summary': audit_summary,
                'vulnerability_summary': {
                    'total_vulnerabilities': len(vulnerabilities),
                    'open_vulnerabilities': len(open_vulns),
                    'critical_vulnerabilities': len(critical_vulns),
                    'by_severity': self._group_vulnerabilities_by_severity(vulnerabilities)
                },
                'policy_summary': {
                    'total_policies': len(policies),
                    'active_policies': len(active_policies)
                },
                'security_score': security_score,
                'recommendations': self._generate_security_recommendations(
                    audit_summary, open_vulns, critical_vulns
                ),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return audit_report
            
        except Exception as e:
            raise ExtensionSecurityError(f"Security audit failed: {e}")
    
    async def generate_compliance_report(
        self,
        tenant_id: str,
        report_type: str = 'security',
        days: int = 30
    ) -> Dict[str, Any]:
        """Generate compliance report"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            report = self.compliance_reporter.generate_compliance_report(
                tenant_id=tenant_id,
                report_type=report_type,
                start_date=start_date,
                end_date=end_date
            )
            
            # Send alert if compliance score is low
            if report.compliance_score < 80:
                await self._send_compliance_alert(report)
            
            return report.dict()
            
        except Exception as e:
            raise ExtensionSecurityError(f"Compliance report generation failed: {e}")
    
    async def handle_security_incident(
        self,
        incident_type: str,
        extension_name: str,
        tenant_id: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle security incidents"""
        try:
            # Log the incident
            self.audit_logger.log_security_violation(
                extension_name=extension_name,
                tenant_id=tenant_id,
                violation_type=incident_type,
                details=details,
                user_id=user_id
            )
            
            # Determine response actions
            response_actions = []
            
            if incident_type == 'critical_vulnerability':
                response_actions.extend([
                    'disable_extension',
                    'notify_administrators',
                    'create_incident_ticket'
                ])
            elif incident_type == 'access_violation':
                response_actions.extend([
                    'revoke_permissions',
                    'notify_security_team'
                ])
            elif incident_type == 'suspicious_activity':
                response_actions.extend([
                    'increase_monitoring',
                    'notify_administrators'
                ])
            
            # Execute response actions
            executed_actions = []
            for action in response_actions:
                try:
                    await self._execute_response_action(action, extension_name, tenant_id, details)
                    executed_actions.append(action)
                except Exception as e:
                    self.logger.error(f"Failed to execute response action {action}: {e}")
            
            incident_response = {
                'incident_id': f"{incident_type}_{extension_name}_{int(datetime.utcnow().timestamp())}",
                'incident_type': incident_type,
                'extension_name': extension_name,
                'tenant_id': tenant_id,
                'details': details,
                'response_actions': response_actions,
                'executed_actions': executed_actions,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return incident_response
            
        except Exception as e:
            raise ExtensionSecurityError(f"Security incident handling failed: {e}")
    
    def _calculate_overall_security_score(
        self,
        audit_summary: Dict[str, Any],
        open_vulns: List,
        critical_vulns: List
    ) -> float:
        """Calculate overall security score"""
        base_score = 100.0
        
        # Deduct for vulnerabilities
        base_score -= len(critical_vulns) * 25
        base_score -= len(open_vulns) * 5
        
        # Deduct for high-risk events
        high_risk_events = audit_summary.get('high_risk_events', 0)
        base_score -= min(high_risk_events * 2, 20)
        
        return max(base_score, 0.0)
    
    def _group_vulnerabilities_by_severity(self, vulnerabilities: List) -> Dict[str, int]:
        """Group vulnerabilities by severity"""
        severity_counts = {}
        for vuln in vulnerabilities:
            severity = vuln.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        return severity_counts
    
    def _generate_security_recommendations(
        self,
        audit_summary: Dict[str, Any],
        open_vulns: List,
        critical_vulns: List
    ) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        if critical_vulns:
            recommendations.append(f"Address {len(critical_vulns)} critical vulnerabilities immediately")
        
        if len(open_vulns) > 10:
            recommendations.append("Implement regular vulnerability scanning and remediation")
        
        high_risk_events = audit_summary.get('high_risk_events', 0)
        if high_risk_events > 20:
            recommendations.append("Review and strengthen access control policies")
        
        if audit_summary.get('total_events', 0) == 0:
            recommendations.append("Verify audit logging is properly configured")
        
        return recommendations
    
    async def _send_security_alerts(self, security_report: Dict[str, Any], context: str) -> None:
        """Send security alerts based on report"""
        try:
            # Check if alerts should be sent
            if security_report['security_score'] < security_alert_config.get_alert_thresholds()['security_score_threshold']:
                # Send low security score alert
                await self._send_alert('low_security_score', security_report, context)
            
            if security_report.get('vulnerability_scan', {}).get('critical_count', 0) > 0:
                # Send critical vulnerability alert
                await self._send_alert('critical_vulnerability', security_report, context)
            
        except Exception as e:
            self.logger.error(f"Failed to send security alerts: {e}")
    
    async def _send_compliance_alert(self, report) -> None:
        """Send compliance alert"""
        try:
            alert_data = {
                'tenant_id': report.tenant_id,
                'report_type': report.report_type,
                'compliance_score': report.compliance_score,
                'period_start': report.period_start.isoformat(),
                'period_end': report.period_end.isoformat()
            }
            
            await self._send_alert('compliance_report', alert_data, 'compliance')
            
        except Exception as e:
            self.logger.error(f"Failed to send compliance alert: {e}")
    
    async def _send_alert(self, alert_type: str, data: Dict[str, Any], context: str) -> None:
        """Send alert notification"""
        try:
            # This would integrate with notification systems
            # For now, just log the alert
            self.logger.warning(f"SECURITY ALERT [{alert_type}] in {context}: {data}")
            
            # In production, this would send to:
            # - Webhook endpoints
            # - Slack channels
            # - Email notifications
            # - SMS alerts
            # - Incident management systems
            
        except Exception as e:
            self.logger.error(f"Failed to send alert: {e}")
    
    async def _execute_response_action(
        self,
        action: str,
        extension_name: str,
        tenant_id: str,
        details: Dict[str, Any]
    ) -> None:
        """Execute security response action"""
        try:
            if action == 'disable_extension':
                # This would integrate with extension manager to disable extension
                self.logger.info(f"Would disable extension {extension_name} for tenant {tenant_id}")
            
            elif action == 'revoke_permissions':
                # This would revoke specific permissions
                self.logger.info(f"Would revoke permissions for extension {extension_name}")
            
            elif action == 'notify_administrators':
                # This would send notifications to administrators
                await self._send_alert('security_incident', {
                    'extension_name': extension_name,
                    'tenant_id': tenant_id,
                    'details': details
                }, 'incident_response')
            
            elif action == 'increase_monitoring':
                # This would increase monitoring levels
                self.logger.info(f"Would increase monitoring for extension {extension_name}")
            
            # Add more response actions as needed
            
        except Exception as e:
            self.logger.error(f"Failed to execute response action {action}: {e}")
            raise