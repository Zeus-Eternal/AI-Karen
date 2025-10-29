"""
Extension Permission Management API.

This module provides REST API endpoints for managing extension permissions,
roles, and tenant access controls.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from .security import get_extension_auth_manager, require_extension_admin
from .extension_permissions import (
    ExtensionPermission, PermissionScope, get_extension_permission_manager
)
from .extension_rbac import (
    ExtensionRole, RoleAssignmentType, get_extension_rbac_manager
)
from .extension_tenant_access import (
    TenantAccessLevel, ExtensionVisibility, get_extension_tenant_access_manager
)

logger = logging.getLogger(__name__)


# Pydantic models for API requests and responses
class PermissionGrantRequest(BaseModel):
    """Request model for granting permissions."""
    user_id: str
    permission: str
    scope: str
    target: str
    tenant_id: Optional[str] = None
    expires_at: Optional[datetime] = None


class RoleAssignmentRequest(BaseModel):
    """Request model for role assignments."""
    user_id: str
    role: str
    tenant_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    assignment_type: str = "direct"


class TenantAccessRequest(BaseModel):
    """Request model for tenant access grants."""
    tenant_id: str
    extension_name: str
    access_level: str
    permissions: Optional[List[str]] = None
    restrictions: Optional[Dict[str, Any]] = None
    quota_limits: Optional[Dict[str, int]] = None
    expires_at: Optional[datetime] = None


class ExtensionPolicyRequest(BaseModel):
    """Request model for extension policies."""
    extension_name: str
    visibility: str
    default_access_level: str
    allowed_tenants: Optional[List[str]] = None
    blocked_tenants: Optional[List[str]] = None
    requires_approval: bool = False
    max_tenants: Optional[int] = None


class PermissionDelegationRequest(BaseModel):
    """Request model for permission delegation."""
    delegatee_user_id: str
    permission: str
    scope: str
    target: str
    expires_at: Optional[datetime] = None


def create_extension_permission_router() -> APIRouter:
    """Create the extension permission management router."""
    router = APIRouter(prefix="/api/extensions/permissions", tags=["extension-permissions"])
    
    # Get managers
    permission_manager = get_extension_permission_manager()
    rbac_manager = get_extension_rbac_manager()
    tenant_manager = get_extension_tenant_access_manager()
    
    @router.get("/user/{user_id}")
    async def get_user_permissions(
        user_id: str,
        extension_name: Optional[str] = Query(None),
        tenant_id: Optional[str] = Query(None),
        user_context: Dict[str, Any] = Depends(require_extension_admin)
    ) -> Dict[str, Any]:
        """Get all permissions for a specific user."""
        try:
            # Create user context for permission checking
            target_user_context = {
                'user_id': user_id,
                'tenant_id': tenant_id or user_context.get('tenant_id'),
                'roles': [],  # Will be populated by RBAC manager
                'permissions': []
            }
            
            # Get user roles
            user_roles = rbac_manager.get_user_roles(user_id, tenant_id)
            target_user_context['roles'] = [role.value for role in user_roles]
            
            # Get effective permissions
            effective_permissions = rbac_manager.get_effective_permissions(
                target_user_context, extension_name
            )
            
            # Get direct permission grants
            direct_permissions = permission_manager.get_user_permissions(
                target_user_context, extension_name
            )
            
            return {
                'user_id': user_id,
                'tenant_id': tenant_id,
                'extension_name': extension_name,
                'effective_permissions': effective_permissions,
                'direct_permissions': direct_permissions,
                'roles': [role.value for role in user_roles]
            }
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user permissions")
    
    @router.post("/grant")
    async def grant_permission(
        request: PermissionGrantRequest,
        user_context: Dict[str, Any] = Depends(require_extension_admin)
    ) -> Dict[str, Any]:
        """Grant a specific permission to a user."""
        try:
            # Validate permission and scope
            try:
                permission = ExtensionPermission(request.permission)
                scope = PermissionScope(request.scope)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid permission or scope: {e}")
            
            # Grant the permission
            success = permission_manager.grant_permission(
                user_id=request.user_id,
                permission=permission,
                scope=scope,
                target=request.target,
                tenant_id=request.tenant_id,
                expires_at=request.expires_at,
                granted_by=user_context.get('user_id')
            )
            
            if not success:
                raise HTTPException(status_code=400, detail="Failed to grant permission")
            
            return {
                'message': f'Permission {request.permission} granted to user {request.user_id}',
                'permission': request.permission,
                'scope': request.scope,
                'target': request.target,
                'granted_by': user_context.get('user_id')
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error granting permission: {e}")
            raise HTTPException(status_code=500, detail="Failed to grant permission")
    
    @router.delete("/revoke")
    async def revoke_permission(
        user_id: str,
        permission: str,
        scope: str,
        target: str,
        tenant_id: Optional[str] = None,
        user_context: Dict[str, Any] = Depends(require_extension_admin)
    ) -> Dict[str, Any]:
        """Revoke a specific permission from a user."""
        try:
            # Validate permission and scope
            try:
                permission_enum = ExtensionPermission(permission)
                scope_enum = PermissionScope(scope)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid permission or scope: {e}")
            
            # Revoke the permission
            success = permission_manager.revoke_permission(
                user_id=user_id,
                permission=permission_enum,
                scope=scope_enum,
                target=target,
                tenant_id=tenant_id
            )
            
            if not success:
                raise HTTPException(status_code=400, detail="Failed to revoke permission")
            
            return {
                'message': f'Permission {permission} revoked from user {user_id}',
                'permission': permission,
                'scope': scope,
                'target': target,
                'revoked_by': user_context.get('user_id')
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error revoking permission: {e}")
            raise HTTPException(status_code=500, detail="Failed to revoke permission")
    
    @router.post("/roles/assign")
    async def assign_role(
        request: RoleAssignmentRequest,
        user_context: Dict[str, Any] = Depends(require_extension_admin)
    ) -> Dict[str, Any]:
        """Assign a role to a user."""
        try:
            # Validate role and assignment type
            try:
                role = ExtensionRole(request.role)
                assignment_type = RoleAssignmentType(request.assignment_type)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid role or assignment type: {e}")
            
            # Assign the role
            success = rbac_manager.assign_role(
                user_id=request.user_id,
                role=role,
                tenant_id=request.tenant_id,
                assigned_by=user_context.get('user_id'),
                expires_at=request.expires_at,
                assignment_type=assignment_type
            )
            
            if not success:
                raise HTTPException(status_code=400, detail="Failed to assign role")
            
            return {
                'message': f'Role {request.role} assigned to user {request.user_id}',
                'role': request.role,
                'user_id': request.user_id,
                'tenant_id': request.tenant_id,
                'assigned_by': user_context.get('user_id')
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error assigning role: {e}")
            raise HTTPException(status_code=500, detail="Failed to assign role")
    
    @router.delete("/roles/revoke")
    async def revoke_role(
        user_id: str,
        role: str,
        tenant_id: Optional[str] = None,
        user_context: Dict[str, Any] = Depends(require_extension_admin)
    ) -> Dict[str, Any]:
        """Revoke a role from a user."""
        try:
            # Validate role
            try:
                role_enum = ExtensionRole(role)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid role: {e}")
            
            # Revoke the role
            success = rbac_manager.revoke_role(
                user_id=user_id,
                role=role_enum,
                tenant_id=tenant_id
            )
            
            if not success:
                raise HTTPException(status_code=400, detail="Failed to revoke role")
            
            return {
                'message': f'Role {role} revoked from user {user_id}',
                'role': role,
                'user_id': user_id,
                'tenant_id': tenant_id,
                'revoked_by': user_context.get('user_id')
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error revoking role: {e}")
            raise HTTPException(status_code=500, detail="Failed to revoke role")
    
    @router.get("/roles/{user_id}")
    async def get_user_roles(
        user_id: str,
        tenant_id: Optional[str] = Query(None),
        include_inherited: bool = Query(True),
        user_context: Dict[str, Any] = Depends(require_extension_admin)
    ) -> Dict[str, Any]:
        """Get all roles for a specific user."""
        try:
            user_roles = rbac_manager.get_user_roles(
                user_id=user_id,
                tenant_id=tenant_id,
                include_inherited=include_inherited
            )
            
            return {
                'user_id': user_id,
                'tenant_id': tenant_id,
                'roles': [role.value for role in user_roles],
                'include_inherited': include_inherited
            }
            
        except Exception as e:
            logger.error(f"Error getting user roles: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user roles")
    
    @router.post("/tenant/grant")
    async def grant_tenant_access(
        request: TenantAccessRequest,
        user_context: Dict[str, Any] = Depends(require_extension_admin)
    ) -> Dict[str, Any]:
        """Grant tenant access to an extension."""
        try:
            # Validate access level
            try:
                access_level = TenantAccessLevel(request.access_level)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid access level: {e}")
            
            # Convert permission strings to enums if provided
            permissions = None
            if request.permissions:
                try:
                    permissions = [ExtensionPermission(p) for p in request.permissions]
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=f"Invalid permission: {e}")
            
            # Grant tenant access
            success = tenant_manager.grant_tenant_access(
                tenant_id=request.tenant_id,
                extension_name=request.extension_name,
                access_level=access_level,
                permissions=permissions,
                restrictions=request.restrictions,
                quota_limits=request.quota_limits,
                granted_by=user_context.get('user_id'),
                expires_at=request.expires_at
            )
            
            if not success:
                raise HTTPException(status_code=400, detail="Failed to grant tenant access")
            
            return {
                'message': f'Tenant access granted to {request.tenant_id} for extension {request.extension_name}',
                'tenant_id': request.tenant_id,
                'extension_name': request.extension_name,
                'access_level': request.access_level,
                'granted_by': user_context.get('user_id')
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error granting tenant access: {e}")
            raise HTTPException(status_code=500, detail="Failed to grant tenant access")
    
    @router.delete("/tenant/revoke")
    async def revoke_tenant_access(
        tenant_id: str,
        extension_name: str,
        user_context: Dict[str, Any] = Depends(require_extension_admin)
    ) -> Dict[str, Any]:
        """Revoke tenant access to an extension."""
        try:
            success = tenant_manager.revoke_tenant_access(
                tenant_id=tenant_id,
                extension_name=extension_name
            )
            
            if not success:
                raise HTTPException(status_code=400, detail="Failed to revoke tenant access")
            
            return {
                'message': f'Tenant access revoked for {tenant_id} to extension {extension_name}',
                'tenant_id': tenant_id,
                'extension_name': extension_name,
                'revoked_by': user_context.get('user_id')
            }
            
        except Exception as e:
            logger.error(f"Error revoking tenant access: {e}")
            raise HTTPException(status_code=500, detail="Failed to revoke tenant access")
    
    @router.get("/tenant/{tenant_id}/extensions")
    async def get_tenant_extensions(
        tenant_id: str,
        include_disabled: bool = Query(False),
        user_context: Dict[str, Any] = Depends(require_extension_admin)
    ) -> Dict[str, Any]:
        """Get all extensions accessible to a tenant."""
        try:
            extensions = tenant_manager.get_tenant_extensions(
                tenant_id=tenant_id,
                include_disabled=include_disabled
            )
            
            # Convert to serializable format
            extension_data = {}
            for ext_name, access in extensions.items():
                extension_data[ext_name] = {
                    'extension_name': access.extension_name,
                    'access_level': access.access_level.value,
                    'permissions': [p.value for p in access.permissions],
                    'enabled': access.enabled,
                    'granted_at': access.granted_at.isoformat(),
                    'expires_at': access.expires_at.isoformat() if access.expires_at else None,
                    'restrictions': access.restrictions,
                    'quota_limits': access.quota_limits
                }
            
            return {
                'tenant_id': tenant_id,
                'extensions': extension_data,
                'total': len(extension_data),
                'include_disabled': include_disabled
            }
            
        except Exception as e:
            logger.error(f"Error getting tenant extensions: {e}")
            raise HTTPException(status_code=500, detail="Failed to get tenant extensions")
    
    @router.post("/extension/policy")
    async def set_extension_policy(
        request: ExtensionPolicyRequest,
        user_context: Dict[str, Any] = Depends(require_extension_admin)
    ) -> Dict[str, Any]:
        """Set tenant access policy for an extension."""
        try:
            # Validate enums
            try:
                visibility = ExtensionVisibility(request.visibility)
                default_access_level = TenantAccessLevel(request.default_access_level)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid visibility or access level: {e}")
            
            # Convert tenant lists to sets
            allowed_tenants = set(request.allowed_tenants) if request.allowed_tenants else None
            blocked_tenants = set(request.blocked_tenants) if request.blocked_tenants else None
            
            # Set the policy
            success = tenant_manager.set_extension_policy(
                extension_name=request.extension_name,
                visibility=visibility,
                default_access_level=default_access_level,
                allowed_tenants=allowed_tenants,
                blocked_tenants=blocked_tenants,
                requires_approval=request.requires_approval,
                max_tenants=request.max_tenants
            )
            
            if not success:
                raise HTTPException(status_code=400, detail="Failed to set extension policy")
            
            return {
                'message': f'Policy set for extension {request.extension_name}',
                'extension_name': request.extension_name,
                'visibility': request.visibility,
                'default_access_level': request.default_access_level,
                'set_by': user_context.get('user_id')
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error setting extension policy: {e}")
            raise HTTPException(status_code=500, detail="Failed to set extension policy")
    
    @router.post("/delegate")
    async def delegate_permission(
        request: PermissionDelegationRequest,
        user_context: Dict[str, Any] = Depends(require_extension_admin)
    ) -> Dict[str, Any]:
        """Delegate a permission from one user to another."""
        try:
            # Validate permission and scope
            try:
                permission = ExtensionPermission(request.permission)
                scope = PermissionScope(request.scope)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid permission or scope: {e}")
            
            # Delegate the permission
            success = permission_manager.delegate_permission(
                delegator_context=user_context,
                delegatee_user_id=request.delegatee_user_id,
                permission=permission,
                scope=scope,
                target=request.target,
                expires_at=request.expires_at
            )
            
            if not success:
                raise HTTPException(status_code=400, detail="Failed to delegate permission")
            
            return {
                'message': f'Permission {request.permission} delegated to user {request.delegatee_user_id}',
                'permission': request.permission,
                'scope': request.scope,
                'target': request.target,
                'delegator': user_context.get('user_id'),
                'delegatee': request.delegatee_user_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error delegating permission: {e}")
            raise HTTPException(status_code=500, detail="Failed to delegate permission")
    
    @router.post("/cleanup")
    async def cleanup_expired_permissions(
        user_context: Dict[str, Any] = Depends(require_extension_admin)
    ) -> Dict[str, Any]:
        """Clean up expired permissions and role assignments."""
        try:
            # Clean up expired permissions
            expired_permissions = permission_manager.cleanup_expired_permissions()
            
            # Clean up expired role assignments
            expired_roles = rbac_manager.cleanup_expired_assignments()
            
            # Clean up expired tenant access
            expired_tenant_access = tenant_manager.cleanup_expired_access()
            
            total_cleaned = expired_permissions + expired_roles + expired_tenant_access
            
            return {
                'message': f'Cleaned up {total_cleaned} expired items',
                'expired_permissions': expired_permissions,
                'expired_roles': expired_roles,
                'expired_tenant_access': expired_tenant_access,
                'total_cleaned': total_cleaned,
                'cleaned_by': user_context.get('user_id')
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up expired permissions: {e}")
            raise HTTPException(status_code=500, detail="Failed to clean up expired permissions")
    
    @router.get("/check")
    async def check_permission(
        user_id: str,
        permission: str,
        extension_name: Optional[str] = Query(None),
        tenant_id: Optional[str] = Query(None),
        user_context: Dict[str, Any] = Depends(require_extension_admin)
    ) -> Dict[str, Any]:
        """Check if a user has a specific permission."""
        try:
            # Create user context for permission checking
            target_user_context = {
                'user_id': user_id,
                'tenant_id': tenant_id or user_context.get('tenant_id'),
                'roles': [],
                'permissions': []
            }
            
            # Get user roles
            user_roles = rbac_manager.get_user_roles(user_id, tenant_id)
            target_user_context['roles'] = [role.value for role in user_roles]
            
            # Check permission using all systems
            from .extension_permissions import has_extension_permission, ExtensionPermission
            from .extension_rbac import check_extension_role_permission
            from .extension_tenant_access import check_tenant_extension_access
            
            try:
                permission_enum = ExtensionPermission(permission)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid permission: {permission}")
            
            # Check through different systems
            has_direct_permission = has_extension_permission(
                target_user_context, permission_enum, extension_name
            )
            
            has_role_permission = check_extension_role_permission(
                target_user_context, permission_enum, extension_name
            )
            
            has_tenant_access = False
            if extension_name:
                has_tenant_access = check_tenant_extension_access(
                    target_user_context, extension_name, permission_enum
                )
            
            has_permission = has_direct_permission or has_role_permission or has_tenant_access
            
            return {
                'user_id': user_id,
                'tenant_id': tenant_id,
                'permission': permission,
                'extension_name': extension_name,
                'has_permission': has_permission,
                'permission_sources': {
                    'direct_permission': has_direct_permission,
                    'role_permission': has_role_permission,
                    'tenant_access': has_tenant_access
                },
                'user_roles': [role.value for role in user_roles]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            raise HTTPException(status_code=500, detail="Failed to check permission")
    
    return router