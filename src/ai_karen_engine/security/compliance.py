"""
Security compliance reporting for SOC2, GDPR, and other regulations.
Provides automated compliance monitoring, reporting, and audit trail generation.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
import uuid

try:
    import aioredis
except ImportError:
    aioredis = None
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ai_karen_engine.security.threat_protection import ThreatEvent
from ai_karen_engine.security.incident_response import SecurityIncident

logger = logging.getLogger(__name__)


class ComplianceFramework(Enum):
    """Supported compliance frameworks."""
    SOC2 = "soc2"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"
    NIST = "nist"
    CCPA = "ccpa"
    SOX = "sox"


class ControlStatus(Enum):
    """Status of compliance controls."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NOT_APPLICABLE = "not_applicable"
    UNDER_REVIEW = "under_review"


@dataclass
class ComplianceControl:
    """Represents a compliance control requirement."""
    id: str
    framework: ComplianceFramework
    title: str
    description: str
    requirement: str
    control_type: str
    status: ControlStatus
    evidence: List[str] = field(default_factory=list)
    last_assessed: Optional[datetime] = None
    next_assessment: Optional[datetime] = None
    responsible_party: Optional[str] = None
    remediation_notes: Optional[str] = None
    risk_level: str = "medium"


@dataclass
class ComplianceReport:
    """Compliance assessment report."""
    id: str
    framework: ComplianceFramework
    report_date: datetime
    assessment_period_start: datetime
    assessment_period_end: datetime
    overall_status: ControlStatus
    controls_assessed: int
    controls_compliant: int
    controls_non_compliant: int
    controls_partially_compliant: int
    risk_score: float
    findings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    evidence_collected: List[str] = field(default_factory=list)


class SOC2Reporter:
    """SOC 2 compliance reporting and monitoring."""
    
    def __init__(self, redis_client: aioredis.Redis, database_session: AsyncSession):
        self.redis = redis_client
        self.database_session = database_session
        self.controls = self._load_soc2_controls()
        
    def _load_soc2_controls(self) -> List[ComplianceControl]:
        """Load SOC 2 Type II controls."""
        return [
            # Security Controls
            ComplianceControl(
                id="CC6.1",
                framework=ComplianceFramework.SOC2,
                title="Logical and Physical Access Controls",
                description="The entity implements logical and physical access controls to protect against threats from sources outside its system boundaries.",
                requirement="Implement access controls to restrict access to system resources",
                control_type="security",
                status=ControlStatus.UNDER_REVIEW,
                risk_level="high"
            ),
            ComplianceControl(
                id="CC6.2",
                framework=ComplianceFramework.SOC2,
                title="Access Control Management",
                description="Prior to issuing system credentials and granting system access, the entity registers and authorizes new internal and external users.",
                requirement="Implement user registration and authorization processes",
                control_type="security",
                status=ControlStatus.UNDER_REVIEW,
                risk_level="high"
            ),
            ComplianceControl(
                id="CC6.3",
                framework=ComplianceFramework.SOC2,
                title="Access Credentials Management",
                description="The entity authorizes, modifies, or removes access to data, software, functions, and other protected information assets.",
                requirement="Manage access credentials throughout their lifecycle",
                control_type="security",
                status=ControlStatus.UNDER_REVIEW,
                risk_level="high"
            ),
            ComplianceControl(
                id="CC6.7",
                framework=ComplianceFramework.SOC2,
                title="Data Transmission Controls",
                description="The entity restricts the transmission, movement, and removal of information to authorized internal and external users.",
                requirement="Implement controls for data transmission and movement",
                control_type="security",
                status=ControlStatus.UNDER_REVIEW,
                risk_level="medium"
            ),
            ComplianceControl(
                id="CC6.8",
                framework=ComplianceFramework.SOC2,
                title="System Monitoring",
                description="The entity implements controls to prevent or detect and act upon the introduction of unauthorized or malicious software.",
                requirement="Monitor systems for unauthorized or malicious software",
                control_type="security",
                status=ControlStatus.UNDER_REVIEW,
                risk_level="high"
            )
        ]
    
    async def assess_controls(self) -> ComplianceReport:
        """Assess SOC 2 controls and generate report."""
        report_id = str(uuid.uuid4())
        assessment_date = datetime.utcnow()
        period_start = assessment_date - timedelta(days=90)  # 90-day assessment period
        
        logger.info("Starting SOC 2 controls assessment")
        
        # Assess each control
        compliant_count = 0
        non_compliant_count = 0
        partially_compliant_count = 0
        findings = []
        
        for control in self.controls:
            status, evidence, finding = await self._assess_control(control, period_start, assessment_date)
            control.status = status
            control.evidence = evidence
            control.last_assessed = assessment_date
            
            if status == ControlStatus.COMPLIANT:
                compliant_count += 1
            elif status == ControlStatus.NON_COMPLIANT:
                non_compliant_count += 1
                if finding:
                    findings.append(finding)
            elif status == ControlStatus.PARTIALLY_COMPLIANT:
                partially_compliant_count += 1
                if finding:
                    findings.append(finding)
        
        # Calculate overall status and risk score
        total_controls = len(self.controls)
        compliance_percentage = (compliant_count / total_controls) * 100 if total_controls > 0 else 0
        
        if compliance_percentage >= 95:
            overall_status = ControlStatus.COMPLIANT
        elif compliance_percentage >= 80:
            overall_status = ControlStatus.PARTIALLY_COMPLIANT
        else:
            overall_status = ControlStatus.NON_COMPLIANT
        
        risk_score = 100 - compliance_percentage
        
        # Generate recommendations
        recommendations = self._generate_soc2_recommendations(findings)
        
        report = ComplianceReport(
            id=report_id,
            framework=ComplianceFramework.SOC2,
            report_date=assessment_date,
            assessment_period_start=period_start,
            assessment_period_end=assessment_date,
            overall_status=overall_status,
            controls_assessed=total_controls,
            controls_compliant=compliant_count,
            controls_non_compliant=non_compliant_count,
            controls_partially_compliant=partially_compliant_count,
            risk_score=risk_score,
            findings=findings,
            recommendations=recommendations
        )
        
        await self._save_report(report)
        logger.info(f"SOC 2 assessment completed. Overall status: {overall_status.value}")
        
        return report
    
    async def _assess_control(
        self, 
        control: ComplianceControl, 
        period_start: datetime, 
        period_end: datetime
    ) -> Tuple[ControlStatus, List[str], Optional[Dict[str, Any]]]:
        """Assess a specific SOC 2 control."""
        evidence = []
        finding = None
        
        try:
            if control.id == "CC6.1":  # Logical and Physical Access Controls
                status, evidence, finding = await self._assess_access_controls(period_start, period_end)
            elif control.id == "CC6.2":  # Access Control Management
                status, evidence, finding = await self._assess_user_management(period_start, period_end)
            elif control.id == "CC6.3":  # Access Credentials Management
                status, evidence, finding = await self._assess_credential_management(period_start, period_end)
            elif control.id == "CC6.7":  # Data Transmission Controls
                status, evidence, finding = await self._assess_data_transmission(period_start, period_end)
            elif control.id == "CC6.8":  # System Monitoring
                status, evidence, finding = await self._assess_system_monitoring(period_start, period_end)
            else:
                status = ControlStatus.NOT_APPLICABLE
                evidence = ["Control assessment not implemented"]
                
        except Exception as e:
            logger.error(f"Error assessing control {control.id}: {e}")
            status = ControlStatus.UNDER_REVIEW
            evidence = [f"Assessment error: {str(e)}"]
            finding = {
                'control_id': control.id,
                'issue': 'Assessment Error',
                'description': f"Unable to assess control due to error: {str(e)}",
                'severity': 'high'
            }
        
        return status, evidence, finding
    
    async def _assess_access_controls(self, start: datetime, end: datetime) -> Tuple[ControlStatus, List[str], Optional[Dict]]:
        """Assess logical and physical access controls."""
        evidence = []
        issues = []
        
        # Check for failed login attempts
        failed_logins_key = "security_metrics:failed_logins"
        failed_logins = await self.redis.get(failed_logins_key)
        if failed_logins:
            failed_count = int(failed_logins)
            evidence.append(f"Failed login attempts in period: {failed_count}")
            if failed_count > 1000:  # Threshold
                issues.append("High number of failed login attempts detected")
        
        # Check for blocked IPs
        blocked_ips = await self.redis.keys("blocked_ip:*")
        evidence.append(f"Blocked IP addresses: {len(blocked_ips)}")
        
        # Check authentication configuration
        auth_config_exists = await self.redis.exists("auth_config")
        if auth_config_exists:
            evidence.append("Authentication configuration present")
        else:
            issues.append("Authentication configuration not found")
        
        if issues:
            finding = {
                'control_id': 'CC6.1',
                'issue': 'Access Control Issues',
                'description': '; '.join(issues),
                'severity': 'high'
            }
            return ControlStatus.NON_COMPLIANT, evidence, finding
        
        return ControlStatus.COMPLIANT, evidence, None
    
    async def _assess_user_management(self, start: datetime, end: datetime) -> Tuple[ControlStatus, List[str], Optional[Dict]]:
        """Assess user registration and authorization processes."""
        evidence = []
        issues = []
        
        try:
            # Check user creation logs
            if self.database_session:
                query = text("""
                    SELECT COUNT(*) as user_count 
                    FROM users 
                    WHERE created_at BETWEEN :start AND :end
                """)
                result = await self.database_session.execute(query, {"start": start, "end": end})
                user_count = result.scalar()
                evidence.append(f"Users created in period: {user_count}")
                
                # Check for users without proper roles
                query = text("""
                    SELECT COUNT(*) as users_without_roles 
                    FROM users 
                    WHERE roles = '{}' OR roles IS NULL
                """)
                result = await self.database_session.execute(query)
                users_without_roles = result.scalar()
                evidence.append(f"Users without roles: {users_without_roles}")
                
                if users_without_roles > 0:
                    issues.append(f"{users_without_roles} users found without proper role assignments")
        
        except Exception as e:
            issues.append(f"Unable to assess user management: {str(e)}")
        
        if issues:
            finding = {
                'control_id': 'CC6.2',
                'issue': 'User Management Issues',
                'description': '; '.join(issues),
                'severity': 'medium'
            }
            return ControlStatus.PARTIALLY_COMPLIANT, evidence, finding
        
        return ControlStatus.COMPLIANT, evidence, None
    
    async def _assess_credential_management(self, start: datetime, end: datetime) -> Tuple[ControlStatus, List[str], Optional[Dict]]:
        """Assess access credentials management."""
        evidence = []
        issues = []
        
        # Check for credential rotation policies
        credential_policy = await self.redis.get("credential_policy")
        if credential_policy:
            evidence.append("Credential management policy exists")
        else:
            issues.append("No credential management policy found")
        
        # Check for expired tokens
        expired_tokens = await self.redis.keys("expired_token:*")
        evidence.append(f"Expired tokens tracked: {len(expired_tokens)}")
        
        if issues:
            finding = {
                'control_id': 'CC6.3',
                'issue': 'Credential Management Issues',
                'description': '; '.join(issues),
                'severity': 'medium'
            }
            return ControlStatus.PARTIALLY_COMPLIANT, evidence, finding
        
        return ControlStatus.COMPLIANT, evidence, None
    
    async def _assess_data_transmission(self, start: datetime, end: datetime) -> Tuple[ControlStatus, List[str], Optional[Dict]]:
        """Assess data transmission controls."""
        evidence = []
        issues = []
        
        # Check for HTTPS enforcement
        https_config = await self.redis.get("https_enforced")
        if https_config == "true":
            evidence.append("HTTPS enforcement enabled")
        else:
            issues.append("HTTPS enforcement not configured")
        
        # Check for data encryption in transit
        encryption_config = await self.redis.get("encryption_in_transit")
        if encryption_config:
            evidence.append("Data encryption in transit configured")
        else:
            issues.append("Data encryption in transit not configured")
        
        if issues:
            finding = {
                'control_id': 'CC6.7',
                'issue': 'Data Transmission Issues',
                'description': '; '.join(issues),
                'severity': 'high'
            }
            return ControlStatus.NON_COMPLIANT, evidence, finding
        
        return ControlStatus.COMPLIANT, evidence, None
    
    async def _assess_system_monitoring(self, start: datetime, end: datetime) -> Tuple[ControlStatus, List[str], Optional[Dict]]:
        """Assess system monitoring controls."""
        evidence = []
        issues = []
        
        # Check for security monitoring
        monitoring_active = await self.redis.get("security_monitoring_active")
        if monitoring_active == "true":
            evidence.append("Security monitoring active")
        else:
            issues.append("Security monitoring not active")
        
        # Check for threat detection
        threat_events = await self.redis.keys("threat:*")
        evidence.append(f"Threat events detected: {len(threat_events)}")
        
        if issues:
            finding = {
                'control_id': 'CC6.8',
                'issue': 'System Monitoring Issues',
                'description': '; '.join(issues),
                'severity': 'high'
            }
            return ControlStatus.NON_COMPLIANT, evidence, finding
        
        return ControlStatus.COMPLIANT, evidence, None
    
    def _generate_soc2_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on SOC 2 findings."""
        recommendations = []
        
        for finding in findings:
            issue = finding.get('issue', '')
            
            if 'Access Control' in issue:
                recommendations.append("Implement multi-factor authentication for all user accounts")
                recommendations.append("Establish regular access reviews and user provisioning procedures")
            elif 'User Management' in issue:
                recommendations.append("Implement role-based access control with proper role assignments")
                recommendations.append("Establish user onboarding and offboarding procedures")
            elif 'Credential Management' in issue:
                recommendations.append("Implement password policies and regular credential rotation")
                recommendations.append("Deploy privileged access management solution")
            elif 'Data Transmission' in issue:
                recommendations.append("Enforce HTTPS/TLS for all data transmission")
                recommendations.append("Implement data encryption at rest and in transit")
            elif 'System Monitoring' in issue:
                recommendations.append("Deploy comprehensive security monitoring and SIEM solution")
                recommendations.append("Implement automated threat detection and response")
        
        # Remove duplicates
        return list(set(recommendations))
    
    async def _save_report(self, report: ComplianceReport):
        """Save compliance report to storage."""
        # Save to Redis
        report_key = f"compliance_report:{report.framework.value}:{report.id}"
        report_data = {
            'id': report.id,
            'framework': report.framework.value,
            'report_date': report.report_date.isoformat(),
            'overall_status': report.overall_status.value,
            'controls_assessed': report.controls_assessed,
            'controls_compliant': report.controls_compliant,
            'controls_non_compliant': report.controls_non_compliant,
            'risk_score': report.risk_score,
            'findings': json.dumps(report.findings),
            'recommendations': json.dumps(report.recommendations)
        }
        
        await self.redis.hset(report_key, mapping=report_data)
        await self.redis.expire(report_key, 86400 * 365)  # Keep for 1 year
        
        # Save to file
        reports_dir = Path("compliance_reports")
        reports_dir.mkdir(exist_ok=True)
        
        report_file = reports_dir / f"{report.framework.value}_report_{report.id}.json"
        
        with open(report_file, 'w') as f:
            json.dump({
                'id': report.id,
                'framework': report.framework.value,
                'report_date': report.report_date.isoformat(),
                'assessment_period_start': report.assessment_period_start.isoformat(),
                'assessment_period_end': report.assessment_period_end.isoformat(),
                'overall_status': report.overall_status.value,
                'controls_assessed': report.controls_assessed,
                'controls_compliant': report.controls_compliant,
                'controls_non_compliant': report.controls_non_compliant,
                'controls_partially_compliant': report.controls_partially_compliant,
                'risk_score': report.risk_score,
                'findings': report.findings,
                'recommendations': report.recommendations,
                'evidence_collected': report.evidence_collected
            }, f, indent=2)
        
        logger.info(f"Compliance report saved: {report_file}")


class GDPRReporter:
    """GDPR compliance reporting and monitoring."""
    
    def __init__(self, redis_client: aioredis.Redis, database_session: AsyncSession):
        self.redis = redis_client
        self.database_session = database_session
        self.controls = self._load_gdpr_controls()
    
    def _load_gdpr_controls(self) -> List[ComplianceControl]:
        """Load GDPR compliance controls."""
        return [
            ComplianceControl(
                id="GDPR.6",
                framework=ComplianceFramework.GDPR,
                title="Lawfulness of Processing",
                description="Processing shall be lawful only if and to the extent that at least one legal basis applies.",
                requirement="Establish legal basis for all data processing activities",
                control_type="data_protection",
                status=ControlStatus.UNDER_REVIEW,
                risk_level="high"
            ),
            ComplianceControl(
                id="GDPR.7",
                framework=ComplianceFramework.GDPR,
                title="Conditions for Consent",
                description="Where processing is based on consent, demonstrate that the data subject has consented.",
                requirement="Implement consent management system",
                control_type="data_protection",
                status=ControlStatus.UNDER_REVIEW,
                risk_level="high"
            ),
            ComplianceControl(
                id="GDPR.17",
                framework=ComplianceFramework.GDPR,
                title="Right to Erasure",
                description="The data subject shall have the right to obtain erasure of personal data.",
                requirement="Implement data deletion capabilities",
                control_type="data_rights",
                status=ControlStatus.UNDER_REVIEW,
                risk_level="medium"
            ),
            ComplianceControl(
                id="GDPR.32",
                framework=ComplianceFramework.GDPR,
                title="Security of Processing",
                description="Implement appropriate technical and organizational measures to ensure security.",
                requirement="Implement data security measures",
                control_type="security",
                status=ControlStatus.UNDER_REVIEW,
                risk_level="high"
            ),
            ComplianceControl(
                id="GDPR.33",
                framework=ComplianceFramework.GDPR,
                title="Notification of Personal Data Breach",
                description="Notify supervisory authority of personal data breaches within 72 hours.",
                requirement="Implement breach notification procedures",
                control_type="incident_response",
                status=ControlStatus.UNDER_REVIEW,
                risk_level="critical"
            )
        ]
    
    async def assess_controls(self) -> ComplianceReport:
        """Assess GDPR controls and generate report."""
        report_id = str(uuid.uuid4())
        assessment_date = datetime.utcnow()
        period_start = assessment_date - timedelta(days=365)  # Annual assessment
        
        logger.info("Starting GDPR compliance assessment")
        
        # Assess each control
        compliant_count = 0
        non_compliant_count = 0
        partially_compliant_count = 0
        findings = []
        
        for control in self.controls:
            status, evidence, finding = await self._assess_gdpr_control(control, period_start, assessment_date)
            control.status = status
            control.evidence = evidence
            control.last_assessed = assessment_date
            
            if status == ControlStatus.COMPLIANT:
                compliant_count += 1
            elif status == ControlStatus.NON_COMPLIANT:
                non_compliant_count += 1
                if finding:
                    findings.append(finding)
            elif status == ControlStatus.PARTIALLY_COMPLIANT:
                partially_compliant_count += 1
                if finding:
                    findings.append(finding)
        
        # Calculate overall status and risk score
        total_controls = len(self.controls)
        compliance_percentage = (compliant_count / total_controls) * 100 if total_controls > 0 else 0
        
        if compliance_percentage >= 90:
            overall_status = ControlStatus.COMPLIANT
        elif compliance_percentage >= 70:
            overall_status = ControlStatus.PARTIALLY_COMPLIANT
        else:
            overall_status = ControlStatus.NON_COMPLIANT
        
        risk_score = 100 - compliance_percentage
        
        # Generate recommendations
        recommendations = self._generate_gdpr_recommendations(findings)
        
        report = ComplianceReport(
            id=report_id,
            framework=ComplianceFramework.GDPR,
            report_date=assessment_date,
            assessment_period_start=period_start,
            assessment_period_end=assessment_date,
            overall_status=overall_status,
            controls_assessed=total_controls,
            controls_compliant=compliant_count,
            controls_non_compliant=non_compliant_count,
            controls_partially_compliant=partially_compliant_count,
            risk_score=risk_score,
            findings=findings,
            recommendations=recommendations
        )
        
        await self._save_report(report)
        logger.info(f"GDPR assessment completed. Overall status: {overall_status.value}")
        
        return report
    
    async def _assess_gdpr_control(
        self, 
        control: ComplianceControl, 
        period_start: datetime, 
        period_end: datetime
    ) -> Tuple[ControlStatus, List[str], Optional[Dict[str, Any]]]:
        """Assess a specific GDPR control."""
        evidence = []
        finding = None
        
        try:
            if control.id == "GDPR.6":  # Lawfulness of Processing
                status, evidence, finding = await self._assess_lawful_processing(period_start, period_end)
            elif control.id == "GDPR.7":  # Conditions for Consent
                status, evidence, finding = await self._assess_consent_management(period_start, period_end)
            elif control.id == "GDPR.17":  # Right to Erasure
                status, evidence, finding = await self._assess_data_erasure(period_start, period_end)
            elif control.id == "GDPR.32":  # Security of Processing
                status, evidence, finding = await self._assess_data_security(period_start, period_end)
            elif control.id == "GDPR.33":  # Breach Notification
                status, evidence, finding = await self._assess_breach_notification(period_start, period_end)
            else:
                status = ControlStatus.NOT_APPLICABLE
                evidence = ["Control assessment not implemented"]
                
        except Exception as e:
            logger.error(f"Error assessing GDPR control {control.id}: {e}")
            status = ControlStatus.UNDER_REVIEW
            evidence = [f"Assessment error: {str(e)}"]
            finding = {
                'control_id': control.id,
                'issue': 'Assessment Error',
                'description': f"Unable to assess control due to error: {str(e)}",
                'severity': 'high'
            }
        
        return status, evidence, finding
    
    async def _assess_lawful_processing(self, start: datetime, end: datetime) -> Tuple[ControlStatus, List[str], Optional[Dict]]:
        """Assess lawfulness of processing."""
        evidence = []
        issues = []
        
        # Check for data processing register
        processing_register = await self.redis.get("data_processing_register")
        if processing_register:
            evidence.append("Data processing register exists")
        else:
            issues.append("Data processing register not found")
        
        # Check for legal basis documentation
        legal_basis_docs = await self.redis.get("legal_basis_documentation")
        if legal_basis_docs:
            evidence.append("Legal basis documentation exists")
        else:
            issues.append("Legal basis documentation not found")
        
        if issues:
            finding = {
                'control_id': 'GDPR.6',
                'issue': 'Lawful Processing Issues',
                'description': '; '.join(issues),
                'severity': 'high'
            }
            return ControlStatus.NON_COMPLIANT, evidence, finding
        
        return ControlStatus.COMPLIANT, evidence, None
    
    async def _assess_consent_management(self, start: datetime, end: datetime) -> Tuple[ControlStatus, List[str], Optional[Dict]]:
        """Assess consent management system."""
        evidence = []
        issues = []
        
        # Check for consent records
        consent_records = await self.redis.keys("consent:*")
        evidence.append(f"Consent records: {len(consent_records)}")
        
        # Check for consent withdrawal mechanism
        consent_withdrawal = await self.redis.get("consent_withdrawal_mechanism")
        if consent_withdrawal:
            evidence.append("Consent withdrawal mechanism exists")
        else:
            issues.append("Consent withdrawal mechanism not implemented")
        
        if issues:
            finding = {
                'control_id': 'GDPR.7',
                'issue': 'Consent Management Issues',
                'description': '; '.join(issues),
                'severity': 'high'
            }
            return ControlStatus.NON_COMPLIANT, evidence, finding
        
        return ControlStatus.COMPLIANT, evidence, None
    
    async def _assess_data_erasure(self, start: datetime, end: datetime) -> Tuple[ControlStatus, List[str], Optional[Dict]]:
        """Assess right to erasure implementation."""
        evidence = []
        issues = []
        
        # Check for data deletion capabilities
        deletion_capability = await self.redis.get("data_deletion_capability")
        if deletion_capability:
            evidence.append("Data deletion capability implemented")
        else:
            issues.append("Data deletion capability not implemented")
        
        # Check for erasure requests handling
        erasure_requests = await self.redis.keys("erasure_request:*")
        evidence.append(f"Erasure requests processed: {len(erasure_requests)}")
        
        if issues:
            finding = {
                'control_id': 'GDPR.17',
                'issue': 'Data Erasure Issues',
                'description': '; '.join(issues),
                'severity': 'medium'
            }
            return ControlStatus.PARTIALLY_COMPLIANT, evidence, finding
        
        return ControlStatus.COMPLIANT, evidence, None
    
    async def _assess_data_security(self, start: datetime, end: datetime) -> Tuple[ControlStatus, List[str], Optional[Dict]]:
        """Assess security of processing."""
        evidence = []
        issues = []
        
        # Check for encryption implementation
        encryption_status = await self.redis.get("data_encryption_status")
        if encryption_status == "enabled":
            evidence.append("Data encryption implemented")
        else:
            issues.append("Data encryption not properly implemented")
        
        # Check for access controls
        access_controls = await self.redis.get("access_controls_status")
        if access_controls == "enabled":
            evidence.append("Access controls implemented")
        else:
            issues.append("Access controls not properly implemented")
        
        if issues:
            finding = {
                'control_id': 'GDPR.32',
                'issue': 'Data Security Issues',
                'description': '; '.join(issues),
                'severity': 'high'
            }
            return ControlStatus.NON_COMPLIANT, evidence, finding
        
        return ControlStatus.COMPLIANT, evidence, None
    
    async def _assess_breach_notification(self, start: datetime, end: datetime) -> Tuple[ControlStatus, List[str], Optional[Dict]]:
        """Assess breach notification procedures."""
        evidence = []
        issues = []
        
        # Check for breach notification procedures
        breach_procedures = await self.redis.get("breach_notification_procedures")
        if breach_procedures:
            evidence.append("Breach notification procedures exist")
        else:
            issues.append("Breach notification procedures not documented")
        
        # Check for breach incidents
        breach_incidents = await self.redis.keys("data_breach:*")
        evidence.append(f"Data breach incidents: {len(breach_incidents)}")
        
        if issues:
            finding = {
                'control_id': 'GDPR.33',
                'issue': 'Breach Notification Issues',
                'description': '; '.join(issues),
                'severity': 'critical'
            }
            return ControlStatus.NON_COMPLIANT, evidence, finding
        
        return ControlStatus.COMPLIANT, evidence, None
    
    def _generate_gdpr_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on GDPR findings."""
        recommendations = []
        
        for finding in findings:
            issue = finding.get('issue', '')
            
            if 'Lawful Processing' in issue:
                recommendations.append("Create and maintain a comprehensive data processing register")
                recommendations.append("Document legal basis for all data processing activities")
            elif 'Consent Management' in issue:
                recommendations.append("Implement granular consent management system")
                recommendations.append("Provide easy consent withdrawal mechanisms")
            elif 'Data Erasure' in issue:
                recommendations.append("Implement automated data deletion capabilities")
                recommendations.append("Establish procedures for handling erasure requests")
            elif 'Data Security' in issue:
                recommendations.append("Implement end-to-end encryption for personal data")
                recommendations.append("Strengthen access controls and authentication")
            elif 'Breach Notification' in issue:
                recommendations.append("Establish 72-hour breach notification procedures")
                recommendations.append("Implement automated breach detection and alerting")
        
        return list(set(recommendations))
    
    async def _save_report(self, report: ComplianceReport):
        """Save GDPR compliance report."""
        # Save to Redis
        report_key = f"compliance_report:{report.framework.value}:{report.id}"
        report_data = {
            'id': report.id,
            'framework': report.framework.value,
            'report_date': report.report_date.isoformat(),
            'overall_status': report.overall_status.value,
            'controls_assessed': report.controls_assessed,
            'controls_compliant': report.controls_compliant,
            'controls_non_compliant': report.controls_non_compliant,
            'risk_score': report.risk_score,
            'findings': json.dumps(report.findings),
            'recommendations': json.dumps(report.recommendations)
        }
        
        await self.redis.hset(report_key, mapping=report_data)
        await self.redis.expire(report_key, 86400 * 365)  # Keep for 1 year
        
        # Save to file
        reports_dir = Path("compliance_reports")
        reports_dir.mkdir(exist_ok=True)
        
        report_file = reports_dir / f"{report.framework.value}_report_{report.id}.json"
        
        with open(report_file, 'w') as f:
            json.dump({
                'id': report.id,
                'framework': report.framework.value,
                'report_date': report.report_date.isoformat(),
                'assessment_period_start': report.assessment_period_start.isoformat(),
                'assessment_period_end': report.assessment_period_end.isoformat(),
                'overall_status': report.overall_status.value,
                'controls_assessed': report.controls_assessed,
                'controls_compliant': report.controls_compliant,
                'controls_non_compliant': report.controls_non_compliant,
                'controls_partially_compliant': report.controls_partially_compliant,
                'risk_score': report.risk_score,
                'findings': report.findings,
                'recommendations': report.recommendations,
                'evidence_collected': report.evidence_collected
            }, f, indent=2)
        
        logger.info(f"GDPR compliance report saved: {report_file}")


class ComplianceReporter:
    """Main compliance reporting system."""
    
    def __init__(self, redis_client: aioredis.Redis, database_session: AsyncSession):
        self.redis = redis_client
        self.database_session = database_session
        self.soc2_reporter = SOC2Reporter(redis_client, database_session)
        self.gdpr_reporter = GDPRReporter(redis_client, database_session)
        
    async def generate_comprehensive_report(self) -> Dict[str, ComplianceReport]:
        """Generate comprehensive compliance report for all frameworks."""
        reports = {}
        
        logger.info("Generating comprehensive compliance report")
        
        # Generate SOC 2 report
        try:
            soc2_report = await self.soc2_reporter.assess_controls()
            reports['soc2'] = soc2_report
        except Exception as e:
            logger.error(f"Error generating SOC 2 report: {e}")
        
        # Generate GDPR report
        try:
            gdpr_report = await self.gdpr_reporter.assess_controls()
            reports['gdpr'] = gdpr_report
        except Exception as e:
            logger.error(f"Error generating GDPR report: {e}")
        
        return reports
    
    async def get_compliance_dashboard_data(self) -> Dict[str, Any]:
        """Get data for compliance dashboard."""
        dashboard_data = {
            'frameworks': {},
            'overall_status': 'unknown',
            'total_controls': 0,
            'compliant_controls': 0,
            'risk_score': 0.0,
            'recent_assessments': []
        }
        
        # Get recent reports
        report_keys = await self.redis.keys("compliance_report:*")
        
        for key in report_keys:
            report_data = await self.redis.hgetall(key)
            if report_data:
                framework = report_data.get('framework', '')
                dashboard_data['frameworks'][framework] = {
                    'status': report_data.get('overall_status', ''),
                    'controls_assessed': int(report_data.get('controls_assessed', 0)),
                    'controls_compliant': int(report_data.get('controls_compliant', 0)),
                    'risk_score': float(report_data.get('risk_score', 0)),
                    'report_date': report_data.get('report_date', '')
                }
        
        return dashboard_data
