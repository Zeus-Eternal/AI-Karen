"""
Extension audit logging and compliance reporting system
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from .models import (
    ExtensionAuditLog, AuditLogEntry, AuditLogResponse, 
    AuditEventType, ComplianceReport
)
from ..base.exceptions import ExtensionSecurityError


class ExtensionAuditLogger:
    """Handles audit logging for extension activities"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
    
    def log_event(
        self,
        extension_name: str,
        tenant_id: str,
        event_type: AuditEventType,
        event_data: Dict[str, Any],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        risk_score: int = 0
    ) -> int:
        """Log an audit event"""
        try:
            audit_entry = ExtensionAuditLog(
                extension_name=extension_name,
                tenant_id=tenant_id,
                user_id=user_id,
                event_type=event_type.value,
                event_data=event_data,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                risk_score=risk_score,
                timestamp=datetime.utcnow()
            )
            
            self.db_session.add(audit_entry)
            self.db_session.commit()
            self.db_session.refresh(audit_entry)
            
            # Log to application logger as well
            self.logger.info(
                f"Extension audit event: {event_type.value} for {extension_name} "
                f"by user {user_id} in tenant {tenant_id}"
            )
            
            return audit_entry.id
            
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"Failed to log audit event: {e}")
            raise ExtensionSecurityError(f"Failed to log audit event: {e}")
    
    def log_extension_install(
        self,
        extension_name: str,
        extension_version: str,
        tenant_id: str,
        user_id: str,
        source: str = "marketplace",
        **kwargs
    ) -> int:
        """Log extension installation"""
        event_data = {
            'extension_version': extension_version,
            'source': source,
            'action': 'install'
        }
        event_data.update(kwargs)
        
        return self.log_event(
            extension_name=extension_name,
            tenant_id=tenant_id,
            event_type=AuditEventType.EXTENSION_INSTALL,
            event_data=event_data,
            user_id=user_id,
            **{k: v for k, v in kwargs.items() if k in ['ip_address', 'user_agent', 'session_id']}
        )
    
    def log_extension_uninstall(
        self,
        extension_name: str,
        tenant_id: str,
        user_id: str,
        reason: Optional[str] = None,
        **kwargs
    ) -> int:
        """Log extension uninstallation"""
        event_data = {
            'action': 'uninstall',
            'reason': reason
        }
        event_data.update(kwargs)
        
        return self.log_event(
            extension_name=extension_name,
            tenant_id=tenant_id,
            event_type=AuditEventType.EXTENSION_UNINSTALL,
            event_data=event_data,
            user_id=user_id,
            **{k: v for k, v in kwargs.items() if k in ['ip_address', 'user_agent', 'session_id']}
        )
    
    def log_permission_change(
        self,
        extension_name: str,
        tenant_id: str,
        user_id: str,
        permission: str,
        action: str,  # 'grant' or 'revoke'
        target_user_id: Optional[str] = None,
        **kwargs
    ) -> int:
        """Log permission changes"""
        event_data = {
            'permission': permission,
            'action': action,
            'target_user_id': target_user_id
        }
        event_data.update(kwargs)
        
        event_type = AuditEventType.PERMISSION_GRANT if action == 'grant' else AuditEventType.PERMISSION_REVOKE
        
        return self.log_event(
            extension_name=extension_name,
            tenant_id=tenant_id,
            event_type=event_type,
            event_data=event_data,
            user_id=user_id,
            risk_score=5 if action == 'grant' else 3,
            **{k: v for k, v in kwargs.items() if k in ['ip_address', 'user_agent', 'session_id']}
        )
    
    def log_data_access(
        self,
        extension_name: str,
        tenant_id: str,
        user_id: str,
        resource: str,
        action: str,
        record_count: Optional[int] = None,
        **kwargs
    ) -> int:
        """Log data access events"""
        event_data = {
            'resource': resource,
            'action': action,
            'record_count': record_count
        }
        event_data.update(kwargs)
        
        # Calculate risk score based on action and record count
        risk_score = 1
        if action in ['delete', 'update']:
            risk_score = 3
        if record_count and record_count > 100:
            risk_score += 2
        
        return self.log_event(
            extension_name=extension_name,
            tenant_id=tenant_id,
            event_type=AuditEventType.DATA_ACCESS,
            event_data=event_data,
            user_id=user_id,
            risk_score=risk_score,
            **{k: v for k, v in kwargs.items() if k in ['ip_address', 'user_agent', 'session_id']}
        )
    
    def log_security_violation(
        self,
        extension_name: str,
        tenant_id: str,
        violation_type: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        **kwargs
    ) -> int:
        """Log security violations"""
        event_data = {
            'violation_type': violation_type,
            'details': details
        }
        event_data.update(kwargs)
        
        return self.log_event(
            extension_name=extension_name,
            tenant_id=tenant_id,
            event_type=AuditEventType.SECURITY_VIOLATION,
            event_data=event_data,
            user_id=user_id,
            risk_score=8,  # High risk score for security violations
            **{k: v for k, v in kwargs.items() if k in ['ip_address', 'user_agent', 'session_id']}
        )
    
    def get_audit_logs(
        self,
        tenant_id: Optional[str] = None,
        extension_name: Optional[str] = None,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_risk_score: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLogResponse]:
        """Retrieve audit logs with filtering"""
        try:
            query = self.db_session.query(ExtensionAuditLog)
            
            # Apply filters
            if tenant_id:
                query = query.filter(ExtensionAuditLog.tenant_id == tenant_id)
            
            if extension_name:
                query = query.filter(ExtensionAuditLog.extension_name == extension_name)
            
            if user_id:
                query = query.filter(ExtensionAuditLog.user_id == user_id)
            
            if event_type:
                query = query.filter(ExtensionAuditLog.event_type == event_type.value)
            
            if start_date:
                query = query.filter(ExtensionAuditLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(ExtensionAuditLog.timestamp <= end_date)
            
            if min_risk_score is not None:
                query = query.filter(ExtensionAuditLog.risk_score >= min_risk_score)
            
            # Order by timestamp descending
            query = query.order_by(desc(ExtensionAuditLog.timestamp))
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            logs = query.all()
            return [AuditLogResponse.from_orm(log) for log in logs]
            
        except Exception as e:
            raise ExtensionSecurityError(f"Failed to retrieve audit logs: {e}")
    
    def get_audit_summary(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get audit summary for a time period"""
        try:
            query = self.db_session.query(ExtensionAuditLog).filter(
                and_(
                    ExtensionAuditLog.tenant_id == tenant_id,
                    ExtensionAuditLog.timestamp >= start_date,
                    ExtensionAuditLog.timestamp <= end_date
                )
            )
            
            # Total events
            total_events = query.count()
            
            # Events by type
            events_by_type = {}
            type_counts = query.with_entities(
                ExtensionAuditLog.event_type,
                func.count(ExtensionAuditLog.id)
            ).group_by(ExtensionAuditLog.event_type).all()
            
            for event_type, count in type_counts:
                events_by_type[event_type] = count
            
            # High risk events
            high_risk_events = query.filter(ExtensionAuditLog.risk_score >= 5).count()
            
            # Most active extensions
            extension_activity = {}
            ext_counts = query.with_entities(
                ExtensionAuditLog.extension_name,
                func.count(ExtensionAuditLog.id)
            ).group_by(ExtensionAuditLog.extension_name).all()
            
            for ext_name, count in ext_counts:
                extension_activity[ext_name] = count
            
            # Most active users
            user_activity = {}
            user_counts = query.filter(
                ExtensionAuditLog.user_id.isnot(None)
            ).with_entities(
                ExtensionAuditLog.user_id,
                func.count(ExtensionAuditLog.id)
            ).group_by(ExtensionAuditLog.user_id).all()
            
            for user_id, count in user_counts:
                user_activity[user_id] = count
            
            return {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'total_events': total_events,
                'events_by_type': events_by_type,
                'high_risk_events': high_risk_events,
                'extension_activity': extension_activity,
                'user_activity': user_activity
            }
            
        except Exception as e:
            raise ExtensionSecurityError(f"Failed to generate audit summary: {e}")
    
    def cleanup_old_logs(self, retention_days: int = 90) -> int:
        """Clean up old audit logs"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            deleted_count = self.db_session.query(ExtensionAuditLog).filter(
                ExtensionAuditLog.timestamp < cutoff_date
            ).delete()
            
            self.db_session.commit()
            
            self.logger.info(f"Cleaned up {deleted_count} old audit log entries")
            return deleted_count
            
        except Exception as e:
            self.db_session.rollback()
            raise ExtensionSecurityError(f"Failed to cleanup old logs: {e}")


class ExtensionComplianceReporter:
    """Generates compliance reports for extensions"""
    
    def __init__(self, db_session: Session, audit_logger: ExtensionAuditLogger):
        self.db_session = db_session
        self.audit_logger = audit_logger
        self.logger = logging.getLogger(__name__)
    
    def generate_compliance_report(
        self,
        tenant_id: str,
        report_type: str,
        start_date: datetime,
        end_date: datetime,
        extensions: Optional[List[str]] = None
    ) -> ComplianceReport:
        """Generate a compliance report"""
        try:
            # Get audit summary
            audit_summary = self.audit_logger.get_audit_summary(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Get detailed logs for analysis
            logs = self.audit_logger.get_audit_logs(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date,
                limit=10000  # Large limit for comprehensive analysis
            )
            
            # Filter by extensions if specified
            if extensions:
                logs = [log for log in logs if log.extension_name in extensions]
                extensions_covered = extensions
            else:
                extensions_covered = list(set(log.extension_name for log in logs))
            
            # Analyze compliance based on report type
            findings = {}
            recommendations = []
            compliance_score = 100.0
            
            if report_type == "security":
                findings, recommendations, compliance_score = self._analyze_security_compliance(logs)
            elif report_type == "data_protection":
                findings, recommendations, compliance_score = self._analyze_data_protection_compliance(logs)
            elif report_type == "access_control":
                findings, recommendations, compliance_score = self._analyze_access_control_compliance(logs)
            else:
                findings, recommendations, compliance_score = self._analyze_general_compliance(logs)
            
            return ComplianceReport(
                tenant_id=tenant_id,
                report_type=report_type,
                period_start=start_date,
                period_end=end_date,
                extensions_covered=extensions_covered,
                findings=findings,
                recommendations=recommendations,
                compliance_score=compliance_score,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            raise ExtensionSecurityError(f"Failed to generate compliance report: {e}")
    
    def _analyze_security_compliance(self, logs: List[AuditLogResponse]) -> tuple:
        """Analyze security compliance"""
        findings = {}
        recommendations = []
        compliance_score = 100.0
        
        # Check for security violations
        security_violations = [log for log in logs if log.event_type == AuditEventType.SECURITY_VIOLATION.value]
        if security_violations:
            findings['security_violations'] = {
                'count': len(security_violations),
                'details': [log.event_data for log in security_violations[:10]]  # Top 10
            }
            compliance_score -= min(len(security_violations) * 5, 30)
            recommendations.append("Address security violations immediately")
        
        # Check for high-risk activities
        high_risk_events = [log for log in logs if log.risk_score >= 7]
        if high_risk_events:
            findings['high_risk_activities'] = {
                'count': len(high_risk_events),
                'types': list(set(log.event_type for log in high_risk_events))
            }
            compliance_score -= min(len(high_risk_events) * 2, 20)
            recommendations.append("Review and monitor high-risk activities")
        
        # Check for unusual access patterns
        failed_access_attempts = [log for log in logs if 'failed' in str(log.event_data).lower()]
        if len(failed_access_attempts) > 10:
            findings['unusual_access_patterns'] = {
                'failed_attempts': len(failed_access_attempts)
            }
            compliance_score -= 10
            recommendations.append("Investigate unusual access patterns")
        
        return findings, recommendations, max(compliance_score, 0)
    
    def _analyze_data_protection_compliance(self, logs: List[AuditLogResponse]) -> tuple:
        """Analyze data protection compliance"""
        findings = {}
        recommendations = []
        compliance_score = 100.0
        
        # Check data access events
        data_access_events = [log for log in logs if log.event_type == AuditEventType.DATA_ACCESS.value]
        
        # Check for bulk data operations
        bulk_operations = []
        for log in data_access_events:
            record_count = log.event_data.get('record_count', 0)
            if record_count and record_count > 1000:
                bulk_operations.append(log)
        
        if bulk_operations:
            findings['bulk_data_operations'] = {
                'count': len(bulk_operations),
                'max_records': max(log.event_data.get('record_count', 0) for log in bulk_operations)
            }
            compliance_score -= 15
            recommendations.append("Review bulk data operations for compliance")
        
        # Check for data deletion events
        deletion_events = [log for log in data_access_events if log.event_data.get('action') == 'delete']
        if deletion_events:
            findings['data_deletions'] = {
                'count': len(deletion_events),
                'extensions': list(set(log.extension_name for log in deletion_events))
            }
            recommendations.append("Ensure data deletion events are properly authorized")
        
        return findings, recommendations, max(compliance_score, 0)
    
    def _analyze_access_control_compliance(self, logs: List[AuditLogResponse]) -> tuple:
        """Analyze access control compliance"""
        findings = {}
        recommendations = []
        compliance_score = 100.0
        
        # Check permission changes
        permission_grants = [log for log in logs if log.event_type == AuditEventType.PERMISSION_GRANT.value]
        permission_revokes = [log for log in logs if log.event_type == AuditEventType.PERMISSION_REVOKE.value]
        
        if len(permission_grants) > len(permission_revokes) * 2:
            findings['permission_imbalance'] = {
                'grants': len(permission_grants),
                'revokes': len(permission_revokes)
            }
            compliance_score -= 10
            recommendations.append("Review permission grant/revoke balance")
        
        # Check for privilege escalation patterns
        admin_grants = [log for log in permission_grants if 'admin' in str(log.event_data).lower()]
        if admin_grants:
            findings['admin_privilege_grants'] = {
                'count': len(admin_grants),
                'users': list(set(log.event_data.get('target_user_id') for log in admin_grants if log.event_data.get('target_user_id')))
            }
            recommendations.append("Review administrative privilege grants")
        
        return findings, recommendations, max(compliance_score, 0)
    
    def _analyze_general_compliance(self, logs: List[AuditLogResponse]) -> tuple:
        """Analyze general compliance"""
        findings = {}
        recommendations = []
        compliance_score = 100.0
        
        # Basic activity analysis
        total_events = len(logs)
        findings['activity_summary'] = {
            'total_events': total_events,
            'event_types': list(set(log.event_type for log in logs)),
            'extensions': list(set(log.extension_name for log in logs))
        }
        
        if total_events == 0:
            compliance_score = 50  # No activity might indicate issues
            recommendations.append("No extension activity detected - verify monitoring")
        
        return findings, recommendations, max(compliance_score, 0)