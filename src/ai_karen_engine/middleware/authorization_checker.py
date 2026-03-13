"""
Authorization Checker for Safety Middleware.

This module provides authorization checking functionality, including
role-based access control, permission validation, and resource access control.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from fastapi import Request, HTTPException, status

from src.auth.auth_middleware import get_current_user

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """Enum representing different permissions."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"


class ResourceType(str, Enum):
    """Enum representing different resource types."""
    API_ENDPOINT = "api_endpoint"
    DATA = "data"
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    CONFIGURATION = "configuration"


@dataclass
class Role:
    """Data class for user roles."""
    
    name: str
    description: str
    permissions: Dict[ResourceType, List[Permission]]
    is_admin: bool = False
    priority: int = 0  # Higher priority roles override lower ones


@dataclass
class Resource:
    """Data class for resources."""
    
    name: str
    type: ResourceType
    path: str
    required_permissions: List[Permission]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessRule:
    """Data class for access rules."""
    
    rule_id: str
    name: str
    description: str
    roles: List[str]
    resources: List[str]
    permissions: List[Permission]
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthorizationResult:
    """Data class for authorization results."""
    
    is_authorized: bool
    user_id: Optional[str]
    roles: List[str]
    resource: str
    required_permissions: List[Permission]
    granted_permissions: List[Permission]
    denied_permissions: List[Permission]
    reason: Optional[str] = None


class AuthorizationChecker:
    """
    Authorization Checker for Safety Middleware.
    
    This class provides authorization checking functionality, including
    role-based access control, permission validation, and resource access control.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Authorization Checker."""
        self.config = config or {}
        
        # Initialize roles
        self._roles: Dict[str, Role] = {}
        self._load_default_roles()
        
        # Initialize resources
        self._resources: Dict[str, Resource] = {}
        self._load_default_resources()
        
        # Initialize access rules
        self._access_rules: Dict[str, AccessRule] = {}
        self._load_default_access_rules()
        
        # Load custom configuration
        self._load_custom_config()
        
        logger.info(f"Authorization Checker initialized with {len(self._roles)} roles, {len(self._resources)} resources, and {len(self._access_rules)} access rules")
    
    def _load_default_roles(self) -> None:
        """Load default roles."""
        default_roles = [
            Role(
                name="guest",
                description="Guest user with limited access",
                permissions={
                    ResourceType.API_ENDPOINT: [Permission.READ],
                    ResourceType.DATA: [Permission.READ],
                },
                priority=0
            ),
            Role(
                name="user",
                description="Regular user with standard access",
                permissions={
                    ResourceType.API_ENDPOINT: [Permission.READ, Permission.WRITE],
                    ResourceType.DATA: [Permission.READ, Permission.WRITE],
                    ResourceType.USER: [Permission.READ],
                },
                priority=1
            ),
            Role(
                name="admin",
                description="Administrator with full access",
                permissions={
                    ResourceType.API_ENDPOINT: [Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.DELETE],
                    ResourceType.DATA: [Permission.READ, Permission.WRITE, Permission.DELETE],
                    ResourceType.USER: [Permission.READ, Permission.WRITE, Permission.DELETE],
                    ResourceType.AGENT: [Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.DELETE],
                    ResourceType.SYSTEM: [Permission.READ, Permission.WRITE, Permission.EXECUTE],
                    ResourceType.CONFIGURATION: [Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.DELETE],
                },
                is_admin=True,
                priority=10
            ),
            Role(
                name="agent",
                description="System agent with limited operational access",
                permissions={
                    ResourceType.API_ENDPOINT: [Permission.READ, Permission.EXECUTE],
                    ResourceType.DATA: [Permission.READ],
                    ResourceType.AGENT: [Permission.READ, Permission.EXECUTE],
                },
                priority=5
            ),
            Role(
                name="security_officer",
                description="Security officer with security-related access",
                permissions={
                    ResourceType.API_ENDPOINT: [Permission.READ, Permission.WRITE],
                    ResourceType.DATA: [Permission.READ, Permission.WRITE],
                    ResourceType.USER: [Permission.READ],
                    ResourceType.SYSTEM: [Permission.READ, Permission.WRITE],
                },
                priority=8
            )
        ]
        
        for role in default_roles:
            self._roles[role.name] = role
    
    def _load_default_resources(self) -> None:
        """Load default resources."""
        default_resources = [
            Resource(
                name="public_api",
                type=ResourceType.API_ENDPOINT,
                path="/api/public/",
                required_permissions=[Permission.READ]
            ),
            Resource(
                name="user_api",
                type=ResourceType.API_ENDPOINT,
                path="/api/user/",
                required_permissions=[Permission.READ, Permission.WRITE]
            ),
            Resource(
                name="admin_api",
                type=ResourceType.API_ENDPOINT,
                path="/api/admin/",
                required_permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.DELETE]
            ),
            Resource(
                name="agent_api",
                type=ResourceType.API_ENDPOINT,
                path="/api/agent/",
                required_permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE]
            ),
            Resource(
                name="system_api",
                type=ResourceType.API_ENDPOINT,
                path="/api/system/",
                required_permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE]
            ),
            Resource(
                name="user_data",
                type=ResourceType.DATA,
                path="/data/user/",
                required_permissions=[Permission.READ, Permission.WRITE]
            ),
            Resource(
                name="system_data",
                type=ResourceType.DATA,
                path="/data/system/",
                required_permissions=[Permission.READ, Permission.WRITE, Permission.DELETE]
            ),
            Resource(
                name="user_management",
                type=ResourceType.USER,
                path="/user/",
                required_permissions=[Permission.READ, Permission.WRITE, Permission.DELETE]
            ),
            Resource(
                name="agent_management",
                type=ResourceType.AGENT,
                path="/agent/",
                required_permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.DELETE]
            ),
            Resource(
                name="system_config",
                type=ResourceType.CONFIGURATION,
                path="/config/",
                required_permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.DELETE]
            )
        ]
        
        for resource in default_resources:
            self._resources[resource.name] = resource
    
    def _load_default_access_rules(self) -> None:
        """Load default access rules."""
        default_access_rules = [
            AccessRule(
                rule_id="public_access",
                name="Public Access",
                description="Allow public access to public resources",
                roles=["guest", "user", "admin", "agent", "security_officer"],
                resources=["public_api"],
                permissions=[Permission.READ]
            ),
            AccessRule(
                rule_id="user_access",
                name="User Access",
                description="Allow users to access user resources",
                roles=["user", "admin", "security_officer"],
                resources=["user_api", "user_data"],
                permissions=[Permission.READ, Permission.WRITE]
            ),
            AccessRule(
                rule_id="admin_access",
                name="Admin Access",
                description="Allow administrators to access admin resources",
                roles=["admin"],
                resources=["admin_api", "system_data", "user_management", "agent_management", "system_config"],
                permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.DELETE]
            ),
            AccessRule(
                rule_id="agent_access",
                name="Agent Access",
                description="Allow agents to access agent resources",
                roles=["agent", "admin"],
                resources=["agent_api"],
                permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE]
            ),
            AccessRule(
                rule_id="system_access",
                name="System Access",
                description="Allow system access to authorized roles",
                roles=["admin", "security_officer"],
                resources=["system_api"],
                permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE]
            ),
            AccessRule(
                rule_id="security_access",
                name="Security Access",
                description="Allow security officers to access security-related resources",
                roles=["admin", "security_officer"],
                resources=["system_data"],
                permissions=[Permission.READ, Permission.WRITE]
            )
        ]
        
        for rule in default_access_rules:
            self._access_rules[rule.rule_id] = rule
    
    def _load_custom_config(self) -> None:
        """Load custom configuration."""
        # Load custom roles
        custom_roles = self.config.get("custom_roles", {})
        for role_name, role_data in custom_roles.items():
            try:
                permissions = {}
                for resource_type, perms in role_data.get("permissions", {}).items():
                    permissions[ResourceType(resource_type)] = [Permission(p) for p in perms]
                
                role = Role(
                    name=role_name,
                    description=role_data.get("description", ""),
                    permissions=permissions,
                    is_admin=role_data.get("is_admin", False),
                    priority=role_data.get("priority", 1)
                )
                self._roles[role_name] = role
            except Exception as e:
                logger.warning(f"Failed to load custom role {role_name}: {e}")
        
        # Load custom resources
        custom_resources = self.config.get("custom_resources", {})
        for resource_name, resource_data in custom_resources.items():
            try:
                resource = Resource(
                    name=resource_name,
                    type=ResourceType(resource_data.get("type", "api_endpoint")),
                    path=resource_data.get("path", ""),
                    required_permissions=[Permission(p) for p in resource_data.get("required_permissions", [])],
                    metadata=resource_data.get("metadata", {})
                )
                self._resources[resource_name] = resource
            except Exception as e:
                logger.warning(f"Failed to load custom resource {resource_name}: {e}")
        
        # Load custom access rules
        custom_rules = self.config.get("custom_access_rules", {})
        for rule_id, rule_data in custom_rules.items():
            try:
                rule = AccessRule(
                    rule_id=rule_id,
                    name=rule_data.get("name", rule_id),
                    description=rule_data.get("description", ""),
                    roles=rule_data.get("roles", []),
                    resources=rule_data.get("resources", []),
                    permissions=[Permission(p) for p in rule_data.get("permissions", [])],
                    conditions=rule_data.get("conditions", {})
                )
                self._access_rules[rule_id] = rule
            except Exception as e:
                logger.warning(f"Failed to load custom access rule {rule_id}: {e}")
    
    def add_role(self, role: Role) -> bool:
        """
        Add a new role.
        
        Args:
            role: Role to add
            
        Returns:
            True if addition was successful, False otherwise
        """
        try:
            self._roles[role.name] = role
            logger.info(f"Added role: {role.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add role {role.name}: {e}")
            return False
    
    def remove_role(self, role_name: str) -> bool:
        """
        Remove a role.
        
        Args:
            role_name: Name of the role to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        try:
            if role_name in self._roles:
                del self._roles[role_name]
                logger.info(f"Removed role: {role_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove role {role_name}: {e}")
            return False
    
    def get_role(self, role_name: str) -> Optional[Role]:
        """
        Get a role.
        
        Args:
            role_name: Name of the role to get
            
        Returns:
            Role if found, None otherwise
        """
        return self._roles.get(role_name)
    
    def get_roles(self) -> List[Role]:
        """
        Get all roles.
        
        Returns:
            List of all roles
        """
        return list(self._roles.values())
    
    def add_resource(self, resource: Resource) -> bool:
        """
        Add a new resource.
        
        Args:
            resource: Resource to add
            
        Returns:
            True if addition was successful, False otherwise
        """
        try:
            self._resources[resource.name] = resource
            logger.info(f"Added resource: {resource.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add resource {resource.name}: {e}")
            return False
    
    def remove_resource(self, resource_name: str) -> bool:
        """
        Remove a resource.
        
        Args:
            resource_name: Name of the resource to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        try:
            if resource_name in self._resources:
                del self._resources[resource_name]
                logger.info(f"Removed resource: {resource_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove resource {resource_name}: {e}")
            return False
    
    def get_resource(self, resource_name: str) -> Optional[Resource]:
        """
        Get a resource.
        
        Args:
            resource_name: Name of the resource to get
            
        Returns:
            Resource if found, None otherwise
        """
        return self._resources.get(resource_name)
    
    def get_resources(self) -> List[Resource]:
        """
        Get all resources.
        
        Returns:
            List of all resources
        """
        return list(self._resources.values())
    
    def add_access_rule(self, rule: AccessRule) -> bool:
        """
        Add a new access rule.
        
        Args:
            rule: Access rule to add
            
        Returns:
            True if addition was successful, False otherwise
        """
        try:
            self._access_rules[rule.rule_id] = rule
            logger.info(f"Added access rule: {rule.name} ({rule.rule_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to add access rule {rule.rule_id}: {e}")
            return False
    
    def remove_access_rule(self, rule_id: str) -> bool:
        """
        Remove an access rule.
        
        Args:
            rule_id: ID of the access rule to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        try:
            if rule_id in self._access_rules:
                del self._access_rules[rule_id]
                logger.info(f"Removed access rule: {rule_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove access rule {rule_id}: {e}")
            return False
    
    def get_access_rule(self, rule_id: str) -> Optional[AccessRule]:
        """
        Get an access rule.
        
        Args:
            rule_id: ID of the access rule to get
            
        Returns:
            Access rule if found, None otherwise
        """
        return self._access_rules.get(rule_id)
    
    def get_access_rules(self) -> List[AccessRule]:
        """
        Get all access rules.
        
        Returns:
            List of all access rules
        """
        return list(self._access_rules.values())
    
    async def check_authorization(
        self,
        request: Request,
        resource_path: str,
        required_permissions: List[Permission]
    ) -> AuthorizationResult:
        """
        Check authorization for a request.
        
        Args:
            request: FastAPI request object
            resource_path: Path of the resource to access
            required_permissions: List of required permissions
            
        Returns:
            Authorization result
        """
        try:
            # Get current user
            user = await get_current_user(request)
            user_id = user.get("id") if user else None
            user_roles = user.get("roles", []) if user else ["guest"]
            
            # Find the resource
            resource = None
            for r in self._resources.values():
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
                role = self._roles.get(role_name)
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
            
        except HTTPException:
            # Authentication failed
            return AuthorizationResult(
                is_authorized=False,
                user_id=None,
                roles=[],
                resource=resource_path,
                required_permissions=required_permissions,
                granted_permissions=[],
                denied_permissions=required_permissions,
                reason="Authentication required"
            )
        except Exception as e:
            logger.error(f"Error checking authorization: {e}")
            return AuthorizationResult(
                is_authorized=False,
                user_id=None,
                roles=[],
                resource=resource_path,
                required_permissions=required_permissions,
                granted_permissions=[],
                denied_permissions=required_permissions,
                reason="Authorization check failed"
            )
    
    def check_permission(
        self,
        user_roles: List[str],
        resource_type: ResourceType,
        permission: Permission
    ) -> bool:
        """
        Check if a user with the given roles has a specific permission.
        
        Args:
            user_roles: List of user roles
            resource_type: Type of resource
            permission: Permission to check
            
        Returns:
            True if permission is granted, False otherwise
        """
        for role_name in user_roles:
            role = self._roles.get(role_name)
            if not role:
                continue
            
            # Check role permissions for this resource type
            role_permissions = role.permissions.get(resource_type, [])
            if permission in role_permissions:
                return True
        
        return False
    
    def get_user_permissions(
        self,
        user_roles: List[str],
        resource_type: Optional[ResourceType] = None
    ) -> Dict[ResourceType, List[Permission]]:
        """
        Get all permissions for a user with the given roles.
        
        Args:
            user_roles: List of user roles
            resource_type: Optional resource type to filter by
            
        Returns:
            Dictionary mapping resource types to lists of permissions
        """
        permissions = {}
        
        for role_name in user_roles:
            role = self._roles.get(role_name)
            if not role:
                continue
            
            for rt, perms in role.permissions.items():
                if resource_type and rt != resource_type:
                    continue
                
                if rt not in permissions:
                    permissions[rt] = []
                
                for perm in perms:
                    if perm not in permissions[rt]:
                        permissions[rt].append(perm)
        
        return permissions
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the authorization checker.
        
        Returns:
            Dictionary with authorization checker statistics
        """
        # Count roles by priority
        roles_by_priority = {}
        for role in self._roles.values():
            priority = role.priority
            if priority not in roles_by_priority:
                roles_by_priority[priority] = []
            roles_by_priority[priority].append(role.name)
        
        # Count resources by type
        resources_by_type = {}
        for resource in self._resources.values():
            rt = resource.type.value
            if rt not in resources_by_type:
                resources_by_type[rt] = []
            resources_by_type[rt].append(resource.name)
        
        # Count access rules by role
        rules_by_role = {}
        for rule in self._access_rules.values():
            for role in rule.roles:
                if role not in rules_by_role:
                    rules_by_role[role] = []
                rules_by_role[role].append(rule.rule_id)
        
        return {
            "total_roles": len(self._roles),
            "total_resources": len(self._resources),
            "total_access_rules": len(self._access_rules),
            "admin_roles": [role.name for role in self._roles.values() if role.is_admin],
            "roles_by_priority": {
                priority: len(roles)
                for priority, roles in roles_by_priority.items()
            },
            "resources_by_type": {
                resource_type: len(resources)
                for resource_type, resources in resources_by_type.items()
            },
            "rules_by_role": {
                role: len(rules)
                for role, rules in rules_by_role.items()
            }
        }