"""
Role-Based Access Control (RBAC) Middleware for Response Core Orchestrator

This module provides comprehensive RBAC functionality for securing training operations,
model management, and administrative features. Integrates with existing authentication
and audit logging systems.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
"""

import logging
import time
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from typing import Any, Dict, List, Optional, Set, Callable, Union
from dataclasses import dataclass, field

from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ai_karen_engine.auth.models import UserData
from ai_karen_engine.auth.tokens import EnhancedTokenManager
from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.services.audit_logging import get_audit_logger
from ai_karen_engine.core.logging import get_logger

logger = get_logger(__name__)
security = HTTPBearer()


class Permission(str, Enum):
    """System permissions for RBAC."""
    # Training and model management permissions
    TRAINING_READ = "training:read"
    TRAINING_WRITE = "training:write"
    TRAINING_DELETE = "training:delete"
    TRAINING_EXECUTE = "training:execute"
    
    # Model management permissions
    MODEL_READ = "model:read"
    MODEL_WRITE = "model:write"
    MODEL_DELETE = "model:delete"
    MODEL_DEPLOY = "model:deploy"
    
    # Data management permissions
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    DATA_DELETE = "data:delete"
    DATA_EXPORT = "data:export"
    
    # Scheduler permissions
    SCHEDULER_READ = "scheduler:read"
    SCHEDULER_WRITE = "scheduler:write"
    SCHEDULER_EXECUTE = "scheduler:execute"
    
    # System administration permissions
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    ADMIN_SYSTEM = "admin:system"
    
    # Audit and security permissions
    AUDIT_READ = "audit:read"
    SECURITY_READ = "security:read"
    SECURITY_WRITE = "security:write"


class Role(str, Enum):
    """System roles with associated permissions."""
    ADMIN = "admin"
    TRAINER = "trainer"
    ANALYST = "analyst"
    USER = "user"
    READONLY = "readonly"


@dataclass
class RolePermissions:
    """Role to permissions mapping."""
    role: Role
    permissions: Set[Permission]
    description: str
    inherits_from: Optional[Role] = None


# Define role hierarchy and permissions
ROLE_PERMISSIONS = {
    Role.ADMIN: RolePermissions(
        role=Role.ADMIN,
        permissions={
            # All permissions for admin
            Permission.TRAINING_READ, Permission.TRAINING_WRITE, Permission.TRAINING_DELETE, Permission.TRAINING_EXECUTE,
            Permission.MODEL_READ, Permission.MODEL_WRITE, Permission.MODEL_DELETE, Permission.MODEL_DEPLOY,
            Permission.DATA_READ, Permission.DATA_WRITE, Permission.DATA_DELETE, Permission.DATA_EXPORT,
            Permission.SCHEDULER_READ, Permission.SCHEDULER_WRITE, Permission.SCHEDULER_EXECUTE,
            Permission.ADMIN_READ, Permission.ADMIN_WRITE, Permission.ADMIN_SYSTEM,
            Permission.AUDIT_READ, Permission.SECURITY_READ, Permission.SECURITY_WRITE,
        },
        description="Full system administrator with all permissions"
    ),
    
    Role.TRAINER: RolePermissions(
        role=Role.TRAINER,
        permissions={
            Permission.TRAINING_READ, Permission.TRAINING_WRITE, Permission.TRAINING_EXECUTE,
            Permission.MODEL_READ, Permission.MODEL_WRITE, Permission.MODEL_DEPLOY,
            Permission.DATA_READ, Permission.DATA_WRITE, Permission.DATA_EXPORT,
            Permission.SCHEDULER_READ, Permission.SCHEDULER_WRITE,
        },
        description="Training specialist with model and data management permissions"
    ),
    
    Role.ANALYST: RolePermissions(
        role=Role.ANALYST,
        permissions={
            Permission.TRAINING_READ,
            Permission.MODEL_READ,
            Permission.DATA_READ, Permission.DATA_EXPORT,
            Permission.SCHEDULER_READ,
            Permission.AUDIT_READ,
        },
        description="Data analyst with read access and export capabilities"
    ),
    
    Role.USER: RolePermissions(
        role=Role.USER,
        permissions={
            Permission.TRAINING_READ,
            Permission.MODEL_READ,
            Permission.DATA_READ,
        },
        description="Regular user with basic read access"
    ),
    
    Role.READONLY: RolePermissions(
        role=Role.READONLY,
        permissions={
            Permission.TRAINING_READ,
            Permission.MODEL_READ,
        },
        description="Read-only access to training and model information"
    ),
}


class RBACManager:
    """Role-Based Access Control manager."""
    
    def __init__(self, config: Optional[AuthConfig] = None):
        """Initialize RBAC manager."""
        self.config = config or AuthConfig.from_env()
        self.token_manager = EnhancedTokenManager(self.config.jwt)
        self.audit_logger = get_audit_logger()
        
        # Cache for user permissions
        self._user_permissions_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 minutes
    
    def get_user_permissions(self, user_data: UserData) -> Set[Permission]:
        """Get all permissions for a user based on their roles."""
        permissions = set()
        
        for role_name in user_data.roles:
            try:
                role = Role(role_name)
                role_perms = ROLE_PERMISSIONS.get(role)
                if role_perms:
                    permissions.update(role_perms.permissions)
            except ValueError:
                logger.warning(f"Unknown role: {role_name} for user {user_data.user_id}")
                continue
        
        return permissions
    
    def has_permission(self, user_data: UserData, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        user_permissions = self.get_user_permissions(user_data)
        return permission in user_permissions
    
    def has_any_permission(self, user_data: UserData, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        user_permissions = self.get_user_permissions(user_data)
        return any(perm in user_permissions for perm in permissions)
    
    def has_all_permissions(self, user_data: UserData, permissions: List[Permission]) -> bool:
        """Check if user has all of the specified permissions."""
        user_permissions = self.get_user_permissions(user_data)
        return all(perm in user_permissions for perm in permissions)
    
    def has_role(self, user_data: UserData, role: Role) -> bool:
        """Check if user has a specific role."""
        return role.value in user_data.roles
    
    def has_admin_role(self, user_data: UserData) -> bool:
        """Check if user has admin role."""
        return self.has_role(user_data, Role.ADMIN)
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials) -> UserData:
        """Extract and validate user from JWT token."""
        try:
            token = credentials.credentials
            payload = await self.token_manager.validate_access_token(token)
            
            # Create UserData from token payload
            user_data = UserData(
                user_id=payload.get("sub", ""),
                email=payload.get("email", ""),
                full_name=payload.get("full_name"),
                roles=payload.get("roles", ["user"]),
                tenant_id=payload.get("tenant_id", "default"),
                is_verified=payload.get("is_verified", True),
                is_active=payload.get("is_active", True),
            )
            
            return user_data
            
        except Exception as e:
            logger.error(f"Failed to validate user token: {e}")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )
    
    def audit_access_attempt(
        self,
        user_data: UserData,
        permission: Permission,
        resource: str,
        granted: bool,
        request: Optional[Request] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Audit access control decisions."""
        try:
            ip_address = "unknown"
            user_agent = ""
            
            if request:
                ip_address = request.client.host if request.client else "unknown"
                user_agent = request.headers.get("user-agent", "")
            
            context = {
                "permission": permission.value,
                "resource": resource,
                "granted": granted,
                "user_roles": user_data.roles,
                "tenant_id": user_data.tenant_id,
            }
            
            if additional_context:
                context.update(additional_context)
            
            # Log to audit system using the base audit logger's method signature
            try:
                from ai_karen_engine.services.audit_logging import AuditEvent, AuditEventType, AuditSeverity
                
                event_type = AuditEventType.LOGIN_SUCCESS if granted else AuditEventType.LOGIN_FAILURE
                severity = AuditSeverity.INFO if granted else AuditSeverity.WARNING
                
                audit_event = AuditEvent(
                    event_type=event_type,
                    severity=severity,
                    message=f"Access {'granted' if granted else 'denied'} to {permission.value} for resource {resource}",
                    user_id=user_data.user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata=context
                )
                
                self.audit_logger.log_audit_event(audit_event)
                
            except ImportError:
                # Fallback to simple logging if audit system not available
                logger.info(f"RBAC: Access {'granted' if granted else 'denied'} to {permission.value} for resource {resource} by user {user_data.user_id}")
                
        except Exception as e:
            logger.error(f"Failed to audit access attempt: {e}")


# Global RBAC manager instance
_rbac_manager: Optional[RBACManager] = None


def get_rbac_manager() -> RBACManager:
    """Get or create global RBAC manager instance."""
    global _rbac_manager
    if _rbac_manager is None:
        _rbac_manager = RBACManager()
    return _rbac_manager


# Dependency functions for FastAPI

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserData:
    """FastAPI dependency to get current authenticated user."""
    rbac_manager = get_rbac_manager()
    return await rbac_manager.get_current_user(credentials)


async def get_current_admin_user(
    current_user: UserData = Depends(get_current_user)
) -> UserData:
    """FastAPI dependency to get current user and verify admin role."""
    rbac_manager = get_rbac_manager()
    
    if not rbac_manager.has_admin_role(current_user):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    
    return current_user


def require_permission(permission: Permission, resource: str = "unknown"):
    """Decorator to require specific permission for endpoint access."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and current_user from kwargs
            request = kwargs.get('request')
            current_user = None
            
            # Try to find current_user in kwargs
            for key, value in kwargs.items():
                if isinstance(value, UserData):
                    current_user = value
                    break
            
            if not current_user:
                # If no user found in kwargs, try to get from dependencies
                try:
                    # This assumes the endpoint has current_user as a dependency
                    credentials = kwargs.get('credentials')
                    if credentials:
                        rbac_manager = get_rbac_manager()
                        current_user = await rbac_manager.get_current_user(credentials)
                except Exception:
                    raise HTTPException(
                        status_code=401,
                        detail="Authentication required"
                    )
            
            if not current_user:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            rbac_manager = get_rbac_manager()
            
            # Check permission
            has_permission = rbac_manager.has_permission(current_user, permission)
            
            # Audit the access attempt
            rbac_manager.audit_access_attempt(
                user_data=current_user,
                permission=permission,
                resource=resource,
                granted=has_permission,
                request=request
            )
            
            if not has_permission:
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission {permission.value} required for {resource}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(role: Role):
    """Decorator to require specific role for endpoint access."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, UserData):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            rbac_manager = get_rbac_manager()
            
            if not rbac_manager.has_role(current_user, role):
                raise HTTPException(
                    status_code=403,
                    detail=f"Role {role.value} required"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_admin(func: Callable) -> Callable:
    """Decorator to require admin role for endpoint access."""
    return require_role(Role.ADMIN)(func)


# Permission checking functions for use in endpoints

def check_training_access(user: UserData, operation: str = "read") -> bool:
    """Check if user has training access."""
    rbac_manager = get_rbac_manager()
    
    if operation == "read":
        return rbac_manager.has_permission(user, Permission.TRAINING_READ)
    elif operation == "write":
        return rbac_manager.has_permission(user, Permission.TRAINING_WRITE)
    elif operation == "delete":
        return rbac_manager.has_permission(user, Permission.TRAINING_DELETE)
    elif operation == "execute":
        return rbac_manager.has_permission(user, Permission.TRAINING_EXECUTE)
    
    return False


def check_model_access(user: UserData, operation: str = "read") -> bool:
    """Check if user has model access."""
    rbac_manager = get_rbac_manager()
    
    if operation == "read":
        return rbac_manager.has_permission(user, Permission.MODEL_READ)
    elif operation == "write":
        return rbac_manager.has_permission(user, Permission.MODEL_WRITE)
    elif operation == "delete":
        return rbac_manager.has_permission(user, Permission.MODEL_DELETE)
    elif operation == "deploy":
        return rbac_manager.has_permission(user, Permission.MODEL_DEPLOY)
    
    return False


def check_data_access(user: UserData, operation: str = "read") -> bool:
    """Check if user has data access."""
    rbac_manager = get_rbac_manager()
    
    if operation == "read":
        return rbac_manager.has_permission(user, Permission.DATA_READ)
    elif operation == "write":
        return rbac_manager.has_permission(user, Permission.DATA_WRITE)
    elif operation == "delete":
        return rbac_manager.has_permission(user, Permission.DATA_DELETE)
    elif operation == "export":
        return rbac_manager.has_permission(user, Permission.DATA_EXPORT)
    
    return False


def check_scheduler_access(user: UserData, operation: str = "read") -> bool:
    """Check if user has scheduler access."""
    rbac_manager = get_rbac_manager()
    
    if operation == "read":
        return rbac_manager.has_permission(user, Permission.SCHEDULER_READ)
    elif operation == "write":
        return rbac_manager.has_permission(user, Permission.SCHEDULER_WRITE)
    elif operation == "execute":
        return rbac_manager.has_permission(user, Permission.SCHEDULER_EXECUTE)
    
    return False


def check_admin_access(user: UserData, operation: str = "read") -> bool:
    """Check if user has admin access."""
    rbac_manager = get_rbac_manager()
    
    if operation == "read":
        return rbac_manager.has_permission(user, Permission.ADMIN_READ)
    elif operation == "write":
        return rbac_manager.has_permission(user, Permission.ADMIN_WRITE)
    elif operation == "system":
        return rbac_manager.has_permission(user, Permission.ADMIN_SYSTEM)
    
    return False