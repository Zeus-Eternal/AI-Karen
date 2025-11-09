"""
Extension access control and policy management system
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .models import (
    ExtensionAccessPolicy, AccessPolicy, AccessPolicyRule, 
    AccessPolicyResponse
)
from .audit_logger import ExtensionAuditLogger, AuditEventType
from ..base.exceptions import ExtensionSecurityError, ExtensionPermissionError


class ExtensionAccessControlManager:
    """Manages access control policies for extensions"""
    
    def __init__(self, db_session: Session, audit_logger: Optional[ExtensionAuditLogger] = None):
        self.db_session = db_session
        self.audit_logger = audit_logger
        self._policy_cache = {}
    
    def create_policy(
        self,
        policy: AccessPolicy,
        created_by: str
    ) -> AccessPolicyResponse:
        """Create a new access control policy"""
        try:
            # Validate policy rules
            self._validate_policy_rules(policy.rules)
            
            # Create database record
            db_policy = ExtensionAccessPolicy(
                extension_name=policy.extension_name,
                tenant_id=policy.tenant_id,
                policy_name=policy.policy_name,
                policy_rules=[rule.dict() for rule in policy.rules],
                is_active=policy.is_active,
                created_by=created_by,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db_session.add(db_policy)
            self.db_session.commit()
            self.db_session.refresh(db_policy)
            
            # Clear cache for this extension
            self._clear_policy_cache(policy.extension_name, policy.tenant_id)
            
            # Log the policy creation
            if self.audit_logger:
                self.audit_logger.log_event(
                    extension_name=policy.extension_name,
                    tenant_id=policy.tenant_id or "global",
                    event_type=AuditEventType.PERMISSION_GRANT,
                    event_data={
                        'action': 'create_policy',
                        'policy_name': policy.policy_name,
                        'rules_count': len(policy.rules)
                    },
                    user_id=created_by,
                    risk_score=3
                )
            
            return AccessPolicyResponse.from_orm(db_policy)
            
        except Exception as e:
            self.db_session.rollback()
            raise ExtensionSecurityError(f"Failed to create access policy: {e}")
    
    def update_policy(
        self,
        policy_id: int,
        policy_updates: Dict[str, Any],
        updated_by: str
    ) -> AccessPolicyResponse:
        """Update an existing access control policy"""
        try:
            db_policy = self.db_session.query(ExtensionAccessPolicy).filter(
                ExtensionAccessPolicy.id == policy_id
            ).first()
            
            if not db_policy:
                raise ExtensionSecurityError(f"Policy {policy_id} not found")
            
            # Update fields
            for field, value in policy_updates.items():
                if field == 'rules' and value:
                    # Validate new rules
                    rules = [AccessPolicyRule(**rule) if isinstance(rule, dict) else rule for rule in value]
                    self._validate_policy_rules(rules)
                    setattr(db_policy, 'policy_rules', [rule.dict() if hasattr(rule, 'dict') else rule for rule in rules])
                elif hasattr(db_policy, field):
                    setattr(db_policy, field, value)
            
            db_policy.updated_at = datetime.utcnow()
            
            self.db_session.commit()
            self.db_session.refresh(db_policy)
            
            # Clear cache
            self._clear_policy_cache(db_policy.extension_name, db_policy.tenant_id)
            
            # Log the policy update
            if self.audit_logger:
                self.audit_logger.log_event(
                    extension_name=db_policy.extension_name,
                    tenant_id=db_policy.tenant_id or "global",
                    event_type=AuditEventType.PERMISSION_GRANT,
                    event_data={
                        'action': 'update_policy',
                        'policy_id': policy_id,
                        'policy_name': db_policy.policy_name,
                        'updated_fields': list(policy_updates.keys())
                    },
                    user_id=updated_by,
                    risk_score=4
                )
            
            return AccessPolicyResponse.from_orm(db_policy)
            
        except Exception as e:
            self.db_session.rollback()
            raise ExtensionSecurityError(f"Failed to update access policy: {e}")
    
    def delete_policy(self, policy_id: int, deleted_by: str) -> bool:
        """Delete an access control policy"""
        try:
            db_policy = self.db_session.query(ExtensionAccessPolicy).filter(
                ExtensionAccessPolicy.id == policy_id
            ).first()
            
            if not db_policy:
                return False
            
            extension_name = db_policy.extension_name
            tenant_id = db_policy.tenant_id
            policy_name = db_policy.policy_name
            
            self.db_session.delete(db_policy)
            self.db_session.commit()
            
            # Clear cache
            self._clear_policy_cache(extension_name, tenant_id)
            
            # Log the policy deletion
            if self.audit_logger:
                self.audit_logger.log_event(
                    extension_name=extension_name,
                    tenant_id=tenant_id or "global",
                    event_type=AuditEventType.PERMISSION_REVOKE,
                    event_data={
                        'action': 'delete_policy',
                        'policy_id': policy_id,
                        'policy_name': policy_name
                    },
                    user_id=deleted_by,
                    risk_score=5
                )
            
            return True
            
        except Exception as e:
            self.db_session.rollback()
            raise ExtensionSecurityError(f"Failed to delete access policy: {e}")
    
    def get_policy(self, policy_id: int) -> Optional[AccessPolicyResponse]:
        """Get a specific access control policy"""
        db_policy = self.db_session.query(ExtensionAccessPolicy).filter(
            ExtensionAccessPolicy.id == policy_id
        ).first()
        
        if db_policy:
            return AccessPolicyResponse.from_orm(db_policy)
        return None
    
    def list_policies(
        self,
        extension_name: Optional[str] = None,
        tenant_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[AccessPolicyResponse]:
        """List access control policies with filtering"""
        query = self.db_session.query(ExtensionAccessPolicy)
        
        if extension_name:
            query = query.filter(ExtensionAccessPolicy.extension_name == extension_name)
        
        if tenant_id:
            query = query.filter(ExtensionAccessPolicy.tenant_id == tenant_id)
        
        if is_active is not None:
            query = query.filter(ExtensionAccessPolicy.is_active == is_active)
        
        policies = query.all()
        return [AccessPolicyResponse.from_orm(policy) for policy in policies]
    
    def check_access(
        self,
        extension_name: str,
        tenant_id: str,
        user_id: str,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if access is allowed based on policies"""
        try:
            # Get applicable policies
            policies = self._get_applicable_policies(extension_name, tenant_id)
            
            if not policies:
                # No policies defined - default to deny
                return False
            
            # Evaluate policies
            for policy in policies:
                if not policy.is_active:
                    continue
                
                for rule_data in policy.policy_rules:
                    rule = AccessPolicyRule(**rule_data)
                    
                    # Check if rule applies to this resource and action
                    if self._rule_matches(rule, resource, action):
                        # Evaluate conditions
                        if self._evaluate_conditions(rule.conditions, user_id, context or {}):
                            # Log access decision
                            if self.audit_logger:
                                self.audit_logger.log_data_access(
                                    extension_name=extension_name,
                                    tenant_id=tenant_id,
                                    user_id=user_id,
                                    resource=resource,
                                    action=action,
                                    policy_decision=rule.effect
                                )
                            
                            return rule.effect == "allow"
            
            # No matching rules - default to deny
            return False
            
        except Exception as e:
            # Log security violation
            if self.audit_logger:
                self.audit_logger.log_security_violation(
                    extension_name=extension_name,
                    tenant_id=tenant_id,
                    violation_type="access_check_error",
                    details={'error': str(e), 'resource': resource, 'action': action},
                    user_id=user_id
                )
            raise ExtensionPermissionError(f"Access check failed: {e}")
    
    def enforce_access(
        self,
        extension_name: str,
        tenant_id: str,
        user_id: str,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Enforce access control - raises exception if access denied"""
        if not self.check_access(extension_name, tenant_id, user_id, resource, action, context):
            raise ExtensionPermissionError(
                f"Access denied: User {user_id} cannot {action} {resource} in extension {extension_name}"
            )
    
    def _get_applicable_policies(self, extension_name: str, tenant_id: str) -> List[ExtensionAccessPolicy]:
        """Get policies applicable to extension and tenant"""
        cache_key = f"{extension_name}:{tenant_id}"
        
        if cache_key in self._policy_cache:
            return self._policy_cache[cache_key]
        
        # Get tenant-specific and global policies
        policies = self.db_session.query(ExtensionAccessPolicy).filter(
            and_(
                ExtensionAccessPolicy.extension_name == extension_name,
                or_(
                    ExtensionAccessPolicy.tenant_id == tenant_id,
                    ExtensionAccessPolicy.tenant_id.is_(None)
                )
            )
        ).all()
        
        # Cache the result
        self._policy_cache[cache_key] = policies
        
        return policies
    
    def _rule_matches(self, rule: AccessPolicyRule, resource: str, action: str) -> bool:
        """Check if a rule matches the resource and action"""
        # Simple wildcard matching
        resource_match = (
            rule.resource == "*" or 
            rule.resource == resource or
            (rule.resource.endswith("*") and resource.startswith(rule.resource[:-1]))
        )
        
        action_match = (
            rule.action == "*" or
            rule.action == action or
            (rule.action.endswith("*") and action.startswith(rule.action[:-1]))
        )
        
        return resource_match and action_match
    
    def _evaluate_conditions(
        self, 
        conditions: Dict[str, Any], 
        user_id: str, 
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate rule conditions"""
        if not conditions:
            return True
        
        # User-based conditions
        if 'users' in conditions:
            if user_id not in conditions['users']:
                return False
        
        if 'user_roles' in conditions and 'user_role' in context:
            if context['user_role'] not in conditions['user_roles']:
                return False
        
        # Time-based conditions
        if 'time_range' in conditions:
            current_hour = datetime.utcnow().hour
            time_range = conditions['time_range']
            if not (time_range.get('start', 0) <= current_hour <= time_range.get('end', 23)):
                return False
        
        # IP-based conditions
        if 'allowed_ips' in conditions and 'ip_address' in context:
            if context['ip_address'] not in conditions['allowed_ips']:
                return False
        
        # Custom conditions
        if 'custom' in conditions:
            # This could be extended to support more complex condition evaluation
            pass
        
        return True
    
    def _validate_policy_rules(self, rules: List[AccessPolicyRule]) -> None:
        """Validate policy rules"""
        if not rules:
            raise ExtensionSecurityError("Policy must have at least one rule")
        
        for rule in rules:
            if not rule.resource:
                raise ExtensionSecurityError("Rule must specify a resource")
            
            if not rule.action:
                raise ExtensionSecurityError("Rule must specify an action")
            
            if rule.effect not in ["allow", "deny"]:
                raise ExtensionSecurityError("Rule effect must be 'allow' or 'deny'")
    
    def _clear_policy_cache(self, extension_name: str, tenant_id: Optional[str]) -> None:
        """Clear policy cache for extension and tenant"""
        keys_to_remove = []
        for key in self._policy_cache.keys():
            if key.startswith(f"{extension_name}:"):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._policy_cache[key]
    
    def create_default_policies(self, extension_name: str, tenant_id: str, created_by: str) -> List[AccessPolicyResponse]:
        """Create default access control policies for an extension"""
        default_policies = [
            AccessPolicy(
                extension_name=extension_name,
                tenant_id=tenant_id,
                policy_name="default_admin_policy",
                rules=[
                    AccessPolicyRule(
                        resource="*",
                        action="*",
                        conditions={"user_roles": ["admin", "super_admin"]},
                        effect="allow"
                    )
                ]
            ),
            AccessPolicy(
                extension_name=extension_name,
                tenant_id=tenant_id,
                policy_name="default_user_policy",
                rules=[
                    AccessPolicyRule(
                        resource="data/*",
                        action="read",
                        conditions={"user_roles": ["user", "admin", "super_admin"]},
                        effect="allow"
                    ),
                    AccessPolicyRule(
                        resource="api/public/*",
                        action="*",
                        conditions={"user_roles": ["user", "admin", "super_admin"]},
                        effect="allow"
                    )
                ]
            )
        ]
        
        created_policies = []
        for policy in default_policies:
            try:
                created_policy = self.create_policy(policy, created_by)
                created_policies.append(created_policy)
            except Exception as e:
                # Log error but continue with other policies
                if self.audit_logger:
                    self.audit_logger.log_security_violation(
                        extension_name=extension_name,
                        tenant_id=tenant_id,
                        violation_type="default_policy_creation_failed",
                        details={'error': str(e), 'policy_name': policy.policy_name}
                    )
        
        return created_policies