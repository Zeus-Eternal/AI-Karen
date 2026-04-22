"""
Authorization Service for CoPilot Architecture.

This service provides comprehensive authorization functionality including
role-based access control, permission management, and policy enforcement.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from ai_karen_engine.core.services.base import BaseService, ServiceConfig
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.middleware.authorization_checker import (
    AuthorizationChecker, AuthorizationResult, Role, Resource, AccessRule,
    Permission, ResourceType
)

logger = get_logger(__name__)


class PolicyType(str, Enum):
    """Policy type enumeration."""
    RESOURCE_POLICY = "resource_policy"
    ACTION_POLICY = "action_policy"
    BEHAVIOR_POLICY = "behavior_policy"
    DATA_POLICY = "data_policy"


@dataclass
class Policy:
    """Policy data structure."""
    policy_id: str
    name: str
    description: str
    policy_type: PolicyType
    rules: List[str]
    conditions: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyEnforcementResult:
    """Policy enforcement result data structure."""
    policy_id: str
    policy_name: str
    is_violation: bool
    is_allowed: bool
    enforcement_action: str
    violation: Optional[Any] = None
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthorizationConfig(ServiceConfig):
    """Authorization configuration."""
    enable_rbac: bool = True
    enable_abac: bool = True  # Attribute-Based Access Control
    enable_policy_enforcement: bool = True
    default_role: str = "guest"
    admin_role: str = "admin"
    policy_cache_ttl: int = 300  # 5 minutes
    audit_logging: bool = True
    strict_mode: bool = False
    
    def __post_init__(self):
        """Initialize ServiceConfig fields."""
        if not hasattr(self, 'name') or not self.name:
            self.name = "authorization_service"
        if not hasattr(self, 'version') or not self.version:
            self.version = "1.0.0"


class AuthorizationService(BaseService):
    """
    Authorization Service for CoPilot Architecture.
    
    This service provides comprehensive authorization functionality including
    role-based access control, permission management, and policy enforcement.
    """
    
    def __init__(self, config: Optional[AuthorizationConfig] = None):
        """Initialize the Authorization Service."""
        super().__init__(config or AuthorizationConfig())
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Initialize authorization checker
        self._auth_checker = AuthorizationChecker(self.config.__dict__)
        
        # Import Request type for RBAC check
        from fastapi import Request
        self._Request = Request
        
        # Thread-safe data structures
        self._policies: Dict[str, Policy] = {}
        self._policy_cache: Dict[str, Tuple[Policy, float]] = {}
        self._user_permissions_cache: Dict[str, Tuple[Set[Permission], float]] = {}
        self._user_roles_cache: Dict[str, Tuple[List[str], float]] = {}
        
        # Load configuration from environment
        self._load_config_from_env()
    
    def _load_config_from_env(self) -> None:
        """Load configuration from environment variables."""
        import os
        
        if "AUTH_ENABLE_RBAC" in os.environ:
            self.config.enable_rbac = os.environ["AUTH_ENABLE_RBAC"].lower() == "true"
        
        if "AUTH_ENABLE_ABAC" in os.environ:
            self.config.enable_abac = os.environ["AUTH_ENABLE_ABAC"].lower() == "true"
        
        if "AUTH_ENABLE_POLICY_ENFORCEMENT" in os.environ:
            self.config.enable_policy_enforcement = os.environ["AUTH_ENABLE_POLICY_ENFORCEMENT"].lower() == "true"
        
        if "AUTH_DEFAULT_ROLE" in os.environ:
            self.config.default_role = os.environ["AUTH_DEFAULT_ROLE"]
        
        if "AUTH_ADMIN_ROLE" in os.environ:
            self.config.admin_role = os.environ["AUTH_ADMIN_ROLE"]
        
        if "AUTH_STRICT_MODE" in os.environ:
            self.config.strict_mode = os.environ["AUTH_STRICT_MODE"].lower() == "true"
    
    async def initialize(self) -> None:
        """Initialize the Authorization Service."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Load default policies
                await self._load_default_policies()
                
                self._initialized = True
                logger.info("Authorization Service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Authorization Service: {e}")
                raise RuntimeError(f"Authorization Service initialization failed: {e}")
    
    async def _load_default_policies(self) -> None:
        """Load default authorization policies."""
        default_policies = [
            Policy(
                policy_id="default_resource_policy",
                name="Default Resource Policy",
                description="Default policy for resource access",
                policy_type=PolicyType.RESOURCE_POLICY,
                rules=["allow_if_authorized"],
                conditions={"strict_mode": self.config.strict_mode}
            ),
            Policy(
                policy_id="default_action_policy",
                name="Default Action Policy",
                description="Default policy for action execution",
                policy_type=PolicyType.ACTION_POLICY,
                rules=["allow_safe_actions", "block_risky_actions"],
                conditions={"strict_mode": self.config.strict_mode}
            ),
            Policy(
                policy_id="default_data_policy",
                name="Default Data Policy",
                description="Default policy for data access",
                policy_type=PolicyType.DATA_POLICY,
                rules=["protect_sensitive_data", "allow_data_access"],
                conditions={"strict_mode": self.config.strict_mode}
            )
        ]
        
        for policy in default_policies:
            self._policies[policy.policy_id] = policy
    
    async def check_authorization(
        self,
        user_id: str,
        user_roles: List[str],
        resource_path: str,
        required_permissions: List[Permission]
    ) -> AuthorizationResult:
        """
        Check authorization for a user.
        
        Args:
            user_id: User ID
            user_roles: List of user roles
            resource_path: Path of the resource to access
            required_permissions: List of required permissions
            
        Returns:
            Authorization result
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Initialize results
            rbac_result = None
            abac_result = AuthorizationResult(
                is_authorized=True,  # Default to allow
                user_id=user_id,
                roles=user_roles,
                resource=resource_path,
                required_permissions=required_permissions,
                granted_permissions=required_permissions,
                denied_permissions=[]
            )
            
            # Check RBAC authorization
            if self.config.enable_rbac:
                rbac_result = await self._check_rbac_authorization(
                    user_id, user_roles, resource_path, required_permissions
                )
                
                # In strict mode, deny if RBAC check fails
                if self.config.strict_mode and not rbac_result.is_authorized:
                    return rbac_result
            
            # Check ABAC authorization
            if self.config.enable_abac:
                abac_result = await self._check_abac_authorization(
                    user_id, user_roles, resource_path, required_permissions
                )
            
            # Combine results
            if self.config.enable_rbac and self.config.enable_abac and rbac_result is not None:
                # Both RBAC and ABAC must pass
                is_authorized = rbac_result.is_authorized and abac_result.is_authorized
                granted_permissions = list(set(rbac_result.granted_permissions) & set(abac_result.granted_permissions))
                denied_permissions = list(set(rbac_result.denied_permissions) | set(abac_result.denied_permissions))
                
                reason = None
                if not is_authorized:
                    reasons = []
                    if not rbac_result.is_authorized and rbac_result.reason:
                        reasons.append(rbac_result.reason)
                    if not abac_result.is_authorized and abac_result.reason:
                        reasons.append(abac_result.reason)
                    reason = "; ".join(reasons)
                
                return AuthorizationResult(
                    is_authorized=is_authorized,
                    user_id=user_id,
                    roles=user_roles,
                    resource=resource_path,
                    required_permissions=required_permissions,
                    granted_permissions=granted_permissions,
                    denied_permissions=denied_permissions,
                    reason=reason
                )
            elif self.config.enable_rbac and rbac_result is not None:
                return rbac_result
            else:
                return abac_result
                
        except Exception as e:
            logger.error(f"Error checking authorization: {e}")
            return AuthorizationResult(
                is_authorized=False,
                user_id=user_id,
                roles=user_roles,
                resource=resource_path,
                required_permissions=required_permissions,
                granted_permissions=[],
                denied_permissions=required_permissions,
                reason="Authorization check failed"
            )
    
    async def _check_rbac_authorization(
        self,
        user_id: str,
        user_roles: List[str],
        resource_path: str,
        required_permissions: List[Permission]
    ) -> AuthorizationResult:
        """
        Check RBAC authorization.
        
        Args:
            user_id: User ID
            user_roles: List of user roles
            resource_path: Path of the resource to access
            required_permissions: List of required permissions
            
        Returns:
            Authorization result
        """
        # Use authorization checker for RBAC
        # We'll implement a simplified version of the authorization check
        # since we can't directly create a FastAPI Request object
        
        # Find the resource
        resource = None
        for r in self._auth_checker._resources.values():
            if resource_path.startswith(r.path):
                resource = r
                break
        
        if not resource:
            # Resource not found, deny access
            return AuthorizationResult(
                is_authorized=False,
                user_id=user_id,
                roles=user_roles,
                resource=resource_path,
                required_permissions=required_permissions,
                granted_permissions=[],
                denied_permissions=required_permissions,
                reason="Resource not found"
            )
        
        # Get required permissions for the resource
        resource_permissions = resource.required_permissions or required_permissions
        
        # Check access rules
        granted_permissions = []
        denied_permissions = []
        
        for role_name in user_roles:
            role = self._auth_checker.get_role(role_name)
            if not role:
                continue
            
            # Check role permissions for this resource type
            role_permissions = role.permissions.get(resource.type, [])
            
            for perm in resource_permissions:
                if perm in role_permissions:
                    if perm not in granted_permissions:
                        granted_permissions.append(perm)
                else:
                    if perm not in denied_permissions:
                        denied_permissions.append(perm)
        
        # Check if all required permissions are granted
        is_authorized = all(perm in granted_permissions for perm in resource_permissions)
        
        # Determine reason
        reason = None
        if not is_authorized:
            missing_perms = [perm for perm in resource_permissions if perm not in granted_permissions]
            reason = f"Missing required permissions: {', '.join(p.value for p in missing_perms)}"
        
        return AuthorizationResult(
            is_authorized=is_authorized,
            user_id=user_id,
            roles=user_roles,
            resource=resource_path,
            required_permissions=resource_permissions,
            granted_permissions=granted_permissions,
            denied_permissions=denied_permissions,
            reason=reason
        )
    
    async def _check_abac_authorization(
        self,
        user_id: str,
        user_roles: List[str],
        resource_path: str,
        required_permissions: List[Permission]
    ) -> AuthorizationResult:
        """
        Check ABAC authorization.
        
        Args:
            user_id: User ID
            user_roles: List of user roles
            resource_path: Path of the resource to access
            required_permissions: List of required permissions
            
        Returns:
            Authorization result
        """
        # For now, we'll implement a simple ABAC check
        # In a real implementation, this would consider user attributes,
        # resource attributes, and environmental conditions
        
        # Default to allow in non-strict mode
        is_authorized = True
        granted_permissions = required_permissions
        denied_permissions = []
        reason = None
        
        # In strict mode, implement some basic ABAC rules
        if self.config.strict_mode:
            # Example: Admin users always have access
            if self.config.admin_role in user_roles:
                is_authorized = True
                granted_permissions = required_permissions
                denied_permissions = []
            # Example: Users can only access their own resources
            elif user_id not in resource_path and "/user/" in resource_path:
                is_authorized = False
                granted_permissions = []
                denied_permissions = required_permissions
                reason = "Users can only access their own resources in strict mode"
        
        return AuthorizationResult(
            is_authorized=is_authorized,
            user_id=user_id,
            roles=user_roles,
            resource=resource_path,
            required_permissions=required_permissions,
            granted_permissions=granted_permissions,
            denied_permissions=denied_permissions,
            reason=reason
        )
    
    async def enforce_policy(
        self,
        policy_id: str,
        user_id: str,
        user_roles: List[str],
        context: Dict[str, Any]
    ) -> List[PolicyEnforcementResult]:
        """
        Enforce a policy for a user.
        
        Args:
            policy_id: ID of the policy to enforce
            user_id: User ID
            user_roles: List of user roles
            context: Context for policy enforcement
            
        Returns:
            List of policy enforcement results
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.config.enable_policy_enforcement:
            return []
        
        try:
            # Get policy
            policy = self._policies.get(policy_id)
            if not policy or not policy.is_active:
                return []
            
            results = []
            
            # Enforce each rule in the policy
            for rule in policy.rules:
                result = await self._enforce_policy_rule(
                    policy, rule, user_id, user_roles, context
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error enforcing policy: {e}")
            return []
    
    async def _enforce_policy_rule(
        self,
        policy: Policy,
        rule: str,
        user_id: str,
        user_roles: List[str],
        context: Dict[str, Any]
    ) -> PolicyEnforcementResult:
        """
        Enforce a single policy rule.
        
        Args:
            policy: Policy to enforce
            rule: Rule to enforce
            user_id: User ID
            user_roles: List of user roles
            context: Context for policy enforcement
            
        Returns:
            Policy enforcement result
        """
        # This would typically implement specific rule enforcement logic
        # For now, we'll implement some basic rules
        
        is_violation = False
        is_allowed = True
        enforcement_action = "allow"
        violation = None
        message = f"Rule '{rule}' evaluated successfully"
        
        # Example rules
        if rule == "allow_if_authorized":
            # Check if user is authorized for the resource
            resource_path = context.get("resource_path", "")
            required_permissions = context.get("required_permissions", [])
            
            auth_result = await self.check_authorization(
                user_id=user_id,
                user_roles=user_roles,
                resource_path=resource_path,
                required_permissions=required_permissions
            )
            
            is_violation = not auth_result.is_authorized
            is_allowed = auth_result.is_authorized
            enforcement_action = "allow" if is_allowed else "block"
            message = "Access allowed" if is_allowed else "Access denied"
            
        elif rule == "allow_safe_actions":
            # Check if action is safe
            action = context.get("action", "")
            is_safe = await self._is_action_safe(action, user_roles)
            
            is_violation = not is_safe
            is_allowed = is_safe
            enforcement_action = "allow" if is_safe else "block"
            message = "Action allowed" if is_safe else "Action blocked as unsafe"
            
        elif rule == "block_risky_actions":
            # Check if action is risky
            action = context.get("action", "")
            is_risky = await self._is_action_risky(action, user_roles)
            
            is_violation = is_risky
            is_allowed = not is_risky
            enforcement_action = "block" if is_risky else "allow"
            message = "Action allowed" if not is_risky else "Action blocked as risky"
            
        elif rule == "protect_sensitive_data":
            # Check if data access is appropriate
            data_type = context.get("data_type", "")
            is_protected = await self._is_data_protected(data_type, user_roles)
            
            is_violation = is_protected
            is_allowed = not is_protected
            enforcement_action = "block" if is_protected else "allow"
            message = "Data access allowed" if not is_protected else "Data access blocked"
            
        elif rule == "allow_data_access":
            # Allow data access
            is_violation = False
            is_allowed = True
            enforcement_action = "allow"
            message = "Data access allowed"
        
        return PolicyEnforcementResult(
            policy_id=policy.policy_id,
            policy_name=policy.name,
            is_violation=is_violation,
            is_allowed=is_allowed,
            enforcement_action=enforcement_action,
            violation=violation,
            message=message
        )
    
    async def _is_action_safe(self, action: str, user_roles: List[str]) -> bool:
        """
        Check if an action is safe.
        
        Args:
            action: Action to check
            user_roles: List of user roles
            
        Returns:
            True if action is safe, False otherwise
        """
        # Define safe actions
        safe_actions = [
            "read", "view", "list", "search", "get", "query"
        ]
        
        # Admin users can perform any safe action
        if self.config.admin_role in user_roles:
            return action.lower() in safe_actions
        
        # Non-admin users can only perform safe actions
        return action.lower() in safe_actions
    
    async def _is_action_risky(self, action: str, user_roles: List[str]) -> bool:
        """
        Check if an action is risky.
        
        Args:
            action: Action to check
            user_roles: List of user roles
            
        Returns:
            True if action is risky, False otherwise
        """
        # Define risky actions
        risky_actions = [
            "delete", "remove", "destroy", "purge",
            "modify", "change", "update", "edit",
            "create", "add", "insert", "new",
            "execute", "run", "start", "stop",
            "admin", "configure", "settings"
        ]
        
        # Admin users can perform risky actions
        if self.config.admin_role in user_roles:
            return False
        
        # Non-admin users cannot perform risky actions
        return action.lower() in risky_actions
    
    async def _is_data_protected(self, data_type: str, user_roles: List[str]) -> bool:
        """
        Check if data type is protected.
        
        Args:
            data_type: Data type to check
            user_roles: List of user roles
            
        Returns:
            True if data is protected, False otherwise
        """
        # Define protected data types
        protected_data_types = [
            "personal", "sensitive", "confidential", "restricted",
            "financial", "health", "security", "admin"
        ]
        
        # Admin users can access any data
        if self.config.admin_role in user_roles:
            return False
        
        # Non-admin users cannot access protected data
        return data_type.lower() in protected_data_types
    
    async def add_policy(self, policy: Policy) -> bool:
        """
        Add a new policy.
        
        Args:
            policy: Policy to add
            
        Returns:
            True if addition was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            self._policies[policy.policy_id] = policy
            logger.info(f"Added policy: {policy.name} ({policy.policy_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to add policy {policy.policy_id}: {e}")
            return False
    
    async def remove_policy(self, policy_id: str) -> bool:
        """
        Remove a policy.
        
        Args:
            policy_id: ID of the policy to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            if policy_id in self._policies:
                del self._policies[policy_id]
                logger.info(f"Removed policy: {policy_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove policy {policy_id}: {e}")
            return False
    
    async def get_policy(self, policy_id: str) -> Optional[Policy]:
        """
        Get a policy.
        
        Args:
            policy_id: ID of the policy to get
            
        Returns:
            Policy if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        return self._policies.get(policy_id)
    
    async def get_policies(self, policy_type: Optional[PolicyType] = None) -> List[Policy]:
        """
        Get policies.
        
        Args:
            policy_type: Optional policy type to filter by
            
        Returns:
            List of policies
        """
        if not self._initialized:
            await self.initialize()
        
        policies = list(self._policies.values())
        if policy_type:
            policies = [p for p in policies if p.policy_type == policy_type]
        
        return policies
    
    async def get_user_permissions(self, user_id: str, user_roles: List[str]) -> Set[Permission]:
        """
        Get all permissions for a user.
        
        Args:
            user_id: User ID
            user_roles: List of user roles
            
        Returns:
            Set of permissions
        """
        if not self._initialized:
            await self.initialize()
        
        # Check cache first
        current_time = asyncio.get_event_loop().time()
        if user_id in self._user_permissions_cache:
            cached_permissions, cache_time = self._user_permissions_cache[user_id]
            if current_time - cache_time < self.config.policy_cache_ttl:
                return cached_permissions
        
        # Get permissions from authorization checker
        permissions = set()
        for role_name in user_roles:
            role = self._auth_checker.get_role(role_name)
            if role:
                for resource_type, role_permissions in role.permissions.items():
                    permissions.update(role_permissions)
        
        # Cache the result
        self._user_permissions_cache[user_id] = (permissions, current_time)
        
        return permissions
    
    async def check_permission(
        self,
        user_id: str,
        user_roles: List[str],
        resource_type: ResourceType,
        permission: Permission
    ) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user_id: User ID
            user_roles: List of user roles
            resource_type: Type of resource
            permission: Permission to check
            
        Returns:
            True if permission is granted, False otherwise
        """
        user_permissions = await self.get_user_permissions(user_id, user_roles)
        
        # Use authorization checker to check permission
        return self._auth_checker.check_permission(user_roles, resource_type, permission)
    
    async def get_user_roles(self, user_id: str) -> List[str]:
        """
        Get roles for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of roles
        """
        if not self._initialized:
            await self.initialize()
        
        # Check cache first
        current_time = asyncio.get_event_loop().time()
        if user_id in self._user_roles_cache:
            cached_roles, cache_time = self._user_roles_cache[user_id]
            if current_time - cache_time < self.config.policy_cache_ttl:
                return cached_roles
        
        # For now, return default role
        # In a real implementation, this would query the database
        roles = [self.config.default_role]
        
        # Cache the result
        self._user_roles_cache[user_id] = (roles, current_time)
        
        return roles
    
    async def add_role(self, role: Role) -> bool:
        """
        Add a new role.
        
        Args:
            role: Role to add
            
        Returns:
            True if addition was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        return self._auth_checker.add_role(role)
    
    async def remove_role(self, role_name: str) -> bool:
        """
        Remove a role.
        
        Args:
            role_name: Name of the role to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        return self._auth_checker.remove_role(role_name)
    
    async def get_role(self, role_name: str) -> Optional[Role]:
        """
        Get a role.
        
        Args:
            role_name: Name of the role to get
            
        Returns:
            Role if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        return self._auth_checker.get_role(role_name)
    
    async def get_roles(self) -> List[Role]:
        """
        Get all roles.
        
        Returns:
            List of all roles
        """
        if not self._initialized:
            await self.initialize()
        
        return self._auth_checker.get_roles()
    
    async def add_resource(self, resource: Resource) -> bool:
        """
        Add a new resource.
        
        Args:
            resource: Resource to add
            
        Returns:
            True if addition was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        return self._auth_checker.add_resource(resource)
    
    async def remove_resource(self, resource_name: str) -> bool:
        """
        Remove a resource.
        
        Args:
            resource_name: Name of the resource to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        return self._auth_checker.remove_resource(resource_name)
    
    async def get_resource(self, resource_name: str) -> Optional[Resource]:
        """
        Get a resource.
        
        Args:
            resource_name: Name of the resource to get
            
        Returns:
            Resource if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        return self._auth_checker.get_resource(resource_name)
    
    async def get_resources(self) -> List[Resource]:
        """
        Get all resources.
        
        Returns:
            List of all resources
        """
        if not self._initialized:
            await self.initialize()
        
        return self._auth_checker.get_resources()
    
    async def add_access_rule(self, rule: AccessRule) -> bool:
        """
        Add a new access rule.
        
        Args:
            rule: Access rule to add
            
        Returns:
            True if addition was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        return self._auth_checker.add_access_rule(rule)
    
    async def remove_access_rule(self, rule_id: str) -> bool:
        """
        Remove an access rule.
        
        Args:
            rule_id: ID of the access rule to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        return self._auth_checker.remove_access_rule(rule_id)
    
    async def get_access_rule(self, rule_id: str) -> Optional[AccessRule]:
        """
        Get an access rule.
        
        Args:
            rule_id: ID of the access rule to get
            
        Returns:
            Access rule if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        return self._auth_checker.get_access_rule(rule_id)
    
    async def get_access_rules(self) -> List[AccessRule]:
        """
        Get all access rules.
        
        Returns:
            List of all access rules
        """
        if not self._initialized:
            await self.initialize()
        
        return self._auth_checker.get_access_rules()
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the authorization service.
        
        Returns:
            Dictionary with authorization service statistics
        """
        if not self._initialized:
            await self.initialize()
        
        # Get authorization checker statistics
        auth_checker_stats = self._auth_checker.get_statistics()
        
        # Add service-specific statistics
        service_stats = {
            "total_policies": len(self._policies),
            "active_policies": len([p for p in self._policies.values() if p.is_active]),
            "policy_types": {
                policy_type.value: len([p for p in self._policies.values() if p.policy_type == policy_type])
                for policy_type in PolicyType
            },
            "cache_size": {
                "policy_cache": len(self._policy_cache),
                "user_permissions_cache": len(self._user_permissions_cache),
                "user_roles_cache": len(self._user_roles_cache)
            },
            "config": {
                "enable_rbac": self.config.enable_rbac,
                "enable_abac": self.config.enable_abac,
                "enable_policy_enforcement": self.config.enable_policy_enforcement,
                "strict_mode": self.config.strict_mode
            }
        }
        
        # Combine statistics
        return {**auth_checker_stats, **service_stats}
    
    async def health_check(self) -> bool:
        """
        Check health of the Authorization Service.
        
        Returns:
            True if service is healthy, False otherwise
        """
        if not self._initialized:
            return False
        
        try:
            # Check if we can create and validate a policy
            test_policy = Policy(
                policy_id="test_policy",
                name="Test Policy",
                description="Policy for health check",
                policy_type=PolicyType.RESOURCE_POLICY,
                rules=["test_rule"]
            )
            
            # Add policy
            if not await self.add_policy(test_policy):
                return False
            
            # Get policy
            retrieved_policy = await self.get_policy("test_policy")
            if not retrieved_policy:
                return False
            
            # Remove policy
            if not await self.remove_policy("test_policy"):
                return False
            
            # Check authorization checker health
            # Since AuthorizationChecker doesn't have a health check method,
            # we'll just check if it's initialized
            return self._auth_checker is not None
        except Exception as e:
            logger.error(f"Authorization Service health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Authorization Service."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Authorization Service started successfully")
    
    async def stop(self) -> None:
        """Stop the Authorization Service."""
        if not self._initialized:
            return
        
        # Clear caches
        self._policy_cache.clear()
        self._user_permissions_cache.clear()
        self._user_roles_cache.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Authorization Service stopped successfully")