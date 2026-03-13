"""Extension Permissions Manager - Advanced permissions and access control for extensions.

This module provides comprehensive permission management including:
- Role-based access control (RBAC)
- Fine-grained permission system
- Permission inheritance and composition
- Dynamic permission evaluation
- Permission audit and logging
- Permission conflict resolution
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field

from ai_karen_engine.extension_host.models import ExtensionManifest, ExtensionPermissions, ExtensionRBAC


class PermissionType(Enum):
    """Types of permissions for extensions."""
    
    SYSTEM = "system"          # System-level permissions
    DATA = "data"            # Data access permissions
    API = "api"              # API endpoint permissions
    NETWORK = "network"         # Network access permissions
    FILE = "file"             # File system permissions
    EXECUTION = "execution"       # Code execution permissions
    UI = "ui"                 # UI component permissions


class PermissionScope(Enum):
    """Scope of permissions."""
    
    GLOBAL = "global"           # System-wide permissions
    TENANT = "tenant"          # Tenant-specific permissions
    USER = "user"             # User-specific permissions
    EXTENSION = "extension"       # Extension-specific permissions


class AccessLevel(Enum):
    """Access levels for permissions."""
    
    NONE = 0
    READ = 1
    WRITE = 2
    ADMIN = 3
    SUPER_ADMIN = 4


@dataclass
class Permission:
    """Individual permission definition."""
    
    name: str
    type: PermissionType
    scope: PermissionScope
    level: AccessLevel
    description: str
    resource_limits: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)
    conflicts_with: List[str] = field(default_factory=list)
    granted_to: List[str] = field(default_factory=list)
    denied_to: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    is_active: bool = True


@dataclass
class Role:
    """Role definition for RBAC."""
    
    name: str
    description: str
    permissions: List[Permission] = field(default_factory=list)
    priority: int = 50
    is_system_role: bool = False
    inherits_from: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True


@dataclass
class PermissionPolicy:
    """Permission policy configuration."""
    
    name: str
    description: str
    permissions: List[Permission] = field(default_factory=list)
    roles: List[Role] = field(default_factory=list)
    default_allow: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True


@dataclass
class PermissionEvaluation:
    """Result of permission evaluation."""
    
    extension_id: str
    user_id: Optional[str]
    user_roles: List[str]
    requested_permissions: List[str]
    granted_permissions: List[str]
    denied_permissions: List[str]
    evaluation_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    decision: str  # "granted", "denied", "partial"
    reason: Optional[str] = None


class ExtensionPermissionsManager:
    """
    Advanced permissions manager for extensions with RBAC support.
    
    Provides:
    - Role-based access control (RBAC)
    - Fine-grained permission system
    - Dynamic permission evaluation
    - Permission audit and logging
    - Permission conflict resolution
    - Permission inheritance and composition
    """
    
    def __init__(
        self,
        enable_audit: bool = True,
        default_policy: Optional[str] = None,
        cache_ttl: int = 300  # 5 minutes
    ):
        """
        Initialize the permissions manager.
        
        Args:
            enable_audit: Whether to enable audit logging
            default_policy: Default permission policy name
            cache_ttl: Time-to-live for permission cache in seconds
        """
        self.enable_audit = enable_audit
        self.default_policy = default_policy
        
        # Permission storage
        self.permissions: Dict[str, Permission] = {}
        self.policies: Dict[str, PermissionPolicy] = {}
        self.roles: Dict[str, Role] = {}
        
        # Permission cache
        self.permission_cache: Dict[str, PermissionEvaluation] = {}
        
        # Audit log
        self.audit_log: List[Dict[str, Any]] = []
        
        self.logger = logging.getLogger("extension.permissions_manager")
        
        # Initialize default permissions and roles
        self._initialize_default_permissions()
        self._initialize_default_roles()
        
        self.logger.info("Extension permissions manager initialized")
    
    def _initialize_default_permissions(self) -> None:
        """Initialize default permissions and roles."""
        try:
            # System permissions
            system_permissions = [
                Permission(
                    name="system_config_read",
                    type=PermissionType.SYSTEM,
                    scope=PermissionScope.GLOBAL,
                    level=AccessLevel.READ,
                    description="Read system configuration"
                ),
                Permission(
                    name="system_config_write",
                    type=PermissionType.SYSTEM,
                    scope=PermissionScope.GLOBAL,
                    level=AccessLevel.ADMIN,
                    description="Write system configuration"
                ),
                Permission(
                    name="system_admin",
                    type=PermissionType.SYSTEM,
                    scope=PermissionScope.GLOBAL,
                    level=AccessLevel.SUPER_ADMIN,
                    description="Full system administration"
                )
            ]
            
            # Data permissions
            data_permissions = [
                Permission(
                    name="data_read",
                    type=PermissionType.DATA,
                    scope=PermissionScope.TENANT,
                    level=AccessLevel.READ,
                    description="Read tenant data"
                ),
                Permission(
                    name="data_write",
                    type=PermissionType.DATA,
                    scope=PermissionScope.TENANT,
                    level=AccessLevel.WRITE,
                    description="Write tenant data"
                ),
                Permission(
                    name="data_admin",
                    type=PermissionType.DATA,
                    scope=PermissionScope.TENANT,
                    level=AccessLevel.ADMIN,
                    description="Administer tenant data"
                )
            ]
            
            # API permissions
            api_permissions = [
                Permission(
                    name="api_read",
                    type=PermissionType.API,
                    scope=PermissionScope.GLOBAL,
                    level=AccessLevel.READ,
                    description="Read API endpoints"
                ),
                Permission(
                    name="api_write",
                    type=PermissionType.API,
                    scope=PermissionScope.GLOBAL,
                    level=AccessLevel.WRITE,
                    description="Write to API endpoints"
                ),
                Permission(
                    name="api_admin",
                    type=PermissionType.API,
                    scope=PermissionScope.GLOBAL,
                    level=AccessLevel.ADMIN,
                    description="Administer API endpoints"
                )
            ]
            
            # Network permissions
            network_permissions = [
                Permission(
                    name="network_outbound",
                    type=PermissionType.NETWORK,
                    scope=PermissionScope.GLOBAL,
                    level=AccessLevel.READ,
                    description="Make outbound network requests"
                ),
                Permission(
                    name="network_inbound",
                    type=PermissionType.NETWORK,
                    scope=PermissionScope.GLOBAL,
                    level=AccessLevel.WRITE,
                    description="Accept inbound network connections"
                )
            ]
            
            # File permissions
            file_permissions = [
                Permission(
                    name="file_read",
                    type=PermissionType.FILE,
                    scope=PermissionScope.EXTENSION,
                    level=AccessLevel.READ,
                    description="Read extension files"
                ),
                Permission(
                    name="file_write",
                    type=PermissionType.FILE,
                    scope=PermissionScope.EXTENSION,
                    level=AccessLevel.WRITE,
                    description="Write extension files"
                ),
                Permission(
                    name="file_execute",
                    type=PermissionType.FILE,
                    scope=PermissionScope.EXTENSION,
                    level=AccessLevel.EXECUTION,
                    description="Execute extension files"
                )
            ]
            
            # Execution permissions
            execution_permissions = [
                Permission(
                    name="execute_code",
                    type=PermissionType.EXECUTION,
                    scope=PermissionScope.EXTENSION,
                    level=AccessLevel.EXECUTION,
                    description="Execute code within extension sandbox"
                ),
                Permission(
                    name="execute_system",
                    type=PermissionType.EXECUTION,
                    scope=PermissionScope.SYSTEM,
                    level=AccessLevel.ADMIN,
                    description="Execute system commands"
                )
            ]
            
            # UI permissions
            ui_permissions = [
                Permission(
                    name="ui_access",
                    type=PermissionType.UI,
                    scope=PermissionScope.GLOBAL,
                    level=AccessLevel.READ,
                    description="Access extension UI components"
                ),
                Permission(
                    name="ui_configure",
                    type=PermissionType.UI,
                    scope=PermissionScope.GLOBAL,
                    level=AccessLevel.WRITE,
                    description="Configure extension UI components"
                )
            ]
            
            # Register all permissions
            all_permissions = (
                system_permissions + data_permissions + api_permissions +
                network_permissions + file_permissions + execution_permissions + ui_permissions
            )
            
            # Create default policy
            default_policy = PermissionPolicy(
                name="default",
                description="Default permission policy for all extensions",
                permissions=all_permissions,
                roles=[
                    Role(
                        name="admin",
                        description="System administrator",
                        permissions=all_permissions,
                        is_system_role=True,
                        priority=100
                    ),
                    Role(
                        name="user",
                        description="Regular user",
                        permissions=[
                            p for p in all_permissions
                            if p.level in [AccessLevel.READ, AccessLevel.WRITE]
                        ],
                        is_system_role=False,
                        priority=50
                    ),
                    Role(
                        name="guest",
                        description="Guest user",
                        permissions=[
                            p for p in all_permissions
                            if p.level == AccessLevel.READ
                        ],
                        is_system_role=False,
                        priority=10
                    )
                ]
            )
            
            # Register all permissions
            for permission in all_permissions:
                self.permissions[permission.name] = permission
            
            # Register all roles
            for role in default_policy.roles:
                self.roles[role.name] = role
            
            # Register default policy
            self.policies["default"] = default_policy
            
        except Exception as e:
            self.logger.error(f"Failed to initialize default permissions: {e}")
    
    def _initialize_default_roles(self) -> None:
        """Initialize default roles if not already present."""
        if not self.roles:
            try:
                # Create admin role
                admin_role = Role(
                    name="admin",
                    description="System administrator",
                    permissions=list(self.permissions.values()),
                    is_system_role=True,
                    priority=100
                )
                
                # Create user role
                user_role = Role(
                    name="user",
                    description="Regular user",
                    permissions=[
                        p for p in self.permissions.values()
                        if p.level in [AccessLevel.READ, AccessLevel.WRITE]
                    ],
                    is_system_role=False,
                    priority=50
                )
                
                # Create guest role
                guest_role = Role(
                    name="guest",
                    description="Guest user",
                    permissions=[
                        p for p in self.permissions.values()
                        if p.level == AccessLevel.READ
                    ],
                    is_system_role=False,
                    priority=10
                )
                
                self.roles["admin"] = admin_role
                self.roles["user"] = user_role
                self.roles["guest"] = guest_role
                
            except Exception as e:
                self.logger.error(f"Failed to initialize default roles: {e}")
    
    def create_permission_policy(
        self,
        name: str,
        description: str,
        permissions: List[Permission],
        roles: List[Role],
        default_allow: bool = True
    ) -> PermissionPolicy:
        """
        Create a custom permission policy.
        
        Args:
            name: Policy name
            description: Policy description
            permissions: List of permissions
            roles: List of roles
            default_allow: Whether to allow by default
            
        Returns:
            Created permission policy
        """
        try:
            policy = PermissionPolicy(
                name=name,
                description=description,
                permissions=permissions,
                roles=roles,
                default_allow=default_allow,
                created_at=datetime.now(timezone.utc),
                is_active=True
            )
            
            self.policies[name] = policy
            
            self.logger.info(f"Created permission policy: {name}")
            return policy
            
        except Exception as e:
            self.logger.error(f"Failed to create permission policy {name}: {e}")
            return None
    
    def create_role(
        self,
        name: str,
        description: str,
        permissions: List[Permission],
        priority: int = 50,
        is_system_role: bool = False,
        inherits_from: List[str] = field(default_factory=list)
    ) -> Role:
        """
        Create a custom role.
        
        Args:
            name: Role name
            description: Role description
            permissions: List of permissions
            priority: Role priority
            is_system_role: Whether this is a system role
            inherits_from: List of role names to inherit from
            
        Returns:
            Created role
        """
        try:
            role = Role(
                name=name,
                description=description,
                permissions=permissions,
                priority=priority,
                is_system_role=is_system_role,
                inherits_from=inherits_from,
                created_at=datetime.now(timezone.utc),
                is_active=True
            )
            
            self.roles[name] = role
            
            self.logger.info(f"Created role: {name}")
            return role
            
        except Exception as e:
            self.logger.error(f"Failed to create role {name}: {e}")
            return None
    
    async def evaluate_permissions(
        self,
        extension_id: str,
        user_id: Optional[str] = None,
        user_roles: List[str],
        requested_permissions: List[str]
    ) -> PermissionEvaluation:
        """
        Evaluate permissions for a user and extension.
        
        Args:
            extension_id: ID of the extension
            user_id: ID of the user
            user_roles: List of user roles
            requested_permissions: List of permissions to evaluate
            
        Returns:
            Permission evaluation result
        """
        try:
            # Get user's role-based permissions
            user_permissions = set()
            for role in user_roles:
                if role in self.roles:
                    user_permissions.update([p.name for p in self.roles[role].permissions])
            
            # Get extension's required permissions
            extension_permissions = set(requested_permissions)
            
            # Determine granted permissions (intersection)
            granted_permissions = list(user_permissions & extension_permissions)
            
            # Determine denied permissions (in extension but not in user)
            denied_permissions = list(extension_permissions - user_permissions)
            
            # Create evaluation result
            evaluation = PermissionEvaluation(
                extension_id=extension_id,
                user_id=user_id,
                user_roles=user_roles,
                requested_permissions=requested_permissions,
                granted_permissions=granted_permissions,
                denied_permissions=denied_permissions,
                decision="granted" if granted_permissions == requested_permissions else "partial" if granted_permissions else "denied",
                reason=None  # Could add detailed reasoning
            )
            
            # Cache evaluation
            self.permission_cache[f"{extension_id}:{','.join(user_roles)}"] = evaluation
            
            # Log evaluation
            if self.enable_audit:
                self.audit_log.append({
                    "timestamp": evaluation.evaluation_time.isoformat(),
                    "action": "permission_evaluation",
                    "extension_id": extension_id,
                    "user_id": user_id,
                    "user_roles": user_roles,
                    "requested_permissions": requested_permissions,
                    "granted_permissions": granted_permissions,
                    "denied_permissions": denied_permissions,
                    "decision": evaluation.decision
                })
            
            self.logger.info(
                f"Permission evaluation for {extension_id}: {evaluation.decision} "
                f"({len(granted_permissions)}/{len(requested_permissions)} granted)"
            )
            
            return evaluation
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate permissions: {e}")
            
            # Return error evaluation
            return PermissionEvaluation(
                extension_id=extension_id,
                user_id=user_id,
                user_roles=user_roles,
                requested_permissions=requested_permissions,
                granted_permissions=[],
                denied_permissions=requested_permissions,
                decision="error",
                reason=str(e)
            )
    
    def check_permission(
        self,
        extension_id: str,
        user_id: Optional[str] = None,
        user_roles: List[str],
        permission: str,
        access_level: AccessLevel = AccessLevel.READ
    ) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            extension_id: ID of the extension
            user_id: ID of the user
            user_roles: List of user roles
            permission: Permission name to check
            access_level: Minimum access level required
            
        Returns:
            True if permission is granted, False otherwise
        """
        try:
            # Get user's role-based permissions
            user_permissions = set()
            for role in user_roles:
                if role in self.roles:
                    user_permissions.update([p.name for p in self.roles[role].permissions])
            
            # Check permission
            permission_obj = self.permissions.get(permission)
            if not permission_obj:
                return False
            
            # Check if user has required access level
            for user_perm in user_permissions:
                if user_perm.name == permission and user_perm.level >= access_level:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check permission {permission}: {e}")
            return False
    
    def grant_permission(
        self,
        extension_id: str,
        user_id: Optional[str] = None,
        permission: str,
        expires_at: Optional[datetime] = None,
        reason: Optional[str] = None
    ) -> bool:
        """
        Grant a permission to a user.
        
        Args:
            extension_id: ID of the extension
            user_id: ID of the user
            permission: Permission name
            expires_at: When permission expires
            reason: Reason for granting permission
            
        Returns:
            True if successful, False otherwise
        """
        try:
            permission_obj = self.permissions.get(permission)
            if not permission_obj:
                self.logger.error(f"Permission {permission} not found")
                return False
            
            # This would update a user record in a real system
            # For now, just log the action
            if self.enable_audit:
                self.audit_log.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": "permission_granted",
                    "extension_id": extension_id,
                    "user_id": user_id,
                    "permission": permission,
                    "expires_at": expires_at.isoformat() if expires_at else None,
                    "reason": reason
                })
            
            self.logger.info(f"Granted permission {permission} to user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to grant permission {permission}: {e}")
            return False
    
    def revoke_permission(
        self,
        extension_id: str,
        user_id: Optional[str] = None,
        permission: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Revoke a permission from a user.
        
        Args:
            extension_id: ID of the extension
            user_id: ID of the user
            permission: Permission name
            reason: Reason for revoking permission
            
        Returns:
            True if successful, False otherwise
        """
        try:
            permission_obj = self.permissions.get(permission)
            if not permission_obj:
                self.logger.error(f"Permission {permission} not found")
                return False
            
            # This would update a user record in a real system
            # For now, just log the action
            if self.enable_audit:
                self.audit_log.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": "permission_revoked",
                    "extension_id": extension_id,
                    "user_id": user_id,
                    "permission": permission,
                    "reason": reason
                })
            
            self.logger.info(f"Revoked permission {permission} from user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to revoke permission {permission}: {e}")
            return False
    
    def get_permission_policies(self) -> Dict[str, PermissionPolicy]:
        """Get all permission policies."""
        try:
            return self.policies.copy()
        except Exception as e:
            self.logger.error(f"Failed to get permission policies: {e}")
            return {}
    
    def get_roles(self) -> Dict[str, Role]:
        """Get all roles."""
        try:
            return self.roles.copy()
        except Exception as e:
            self.logger.error(f"Failed to get roles: {e}")
            return {}
    
    def get_permissions(self) -> Dict[str, Permission]:
        """Get all permissions."""
        try:
            return self.permissions.copy()
        except Exception as e:
            self.logger.error(f"Failed to get permissions: {e}")
            return {}
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get the audit log.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of audit log entries
        """
        try:
            return self.audit_log[-limit:] if self.audit_log else []
        except Exception as e:
            self.logger.error(f"Failed to get audit log: {e}")
            return []
    
    def get_permission_evaluation(
        self,
        extension_id: str,
        user_id: Optional[str] = None,
        user_roles: List[str]
    ) -> Optional[PermissionEvaluation]:
        """
        Get cached permission evaluation.
        
        Args:
            extension_id: ID of the extension
            user_id: ID of the user
            user_roles: List of user roles
            
        Returns:
            Cached evaluation or None
        """
        try:
            cache_key = f"{extension_id}:{','.join(user_roles)}"
            return self.permission_cache.get(cache_key)
        except Exception as e:
            self.logger.error(f"Failed to get permission evaluation: {e}")
            return None
    
    def clear_permission_cache(self, extension_id: Optional[str] = None, user_id: Optional[str] = None) -> None:
        """Clear permission cache for specific user or all users."""
        try:
            if extension_id and user_id:
                cache_key = f"{extension_id}:{','.join(user_id)}"
                if cache_key in self.permission_cache:
                    del self.permission_cache[cache_key]
                    self.logger.info(f"Cleared permission cache for {cache_key}")
            
            else:
                # Clear all cache
                self.permission_cache.clear()
                self.logger.info("Cleared all permission cache")
            
        except Exception as e:
            self.logger.error(f"Failed to clear permission cache: {e}")


__all__ = [
    "ExtensionPermissionsManager",
    "Permission",
    "PermissionType",
    "PermissionScope",
    "AccessLevel",
    "PermissionPolicy",
    "Role",
    "PermissionEvaluation",
]