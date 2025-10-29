"""
Tenant-specific access controls for extensions.

This module provides tenant isolation and access control for extension operations,
ensuring proper multi-tenancy support and data isolation.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from .extension_permissions import ExtensionPermission, PermissionScope
from .extension_rbac import ExtensionRole, get_extension_rbac_manager

logger = logging.getLogger(__name__)


class TenantAccessLevel(str, Enum):
    """Tenant access levels for extensions."""
    NONE = "none"           # No access
    READ_ONLY = "read_only" # Read-only access
    LIMITED = "limited"     # Limited functionality
    STANDARD = "standard"   # Standard access
    PREMIUM = "premium"     # Premium features
    ADMIN = "admin"         # Administrative access


class ExtensionVisibility(str, Enum):
    """Extension visibility levels."""
    PUBLIC = "public"       # Visible to all tenants
    PRIVATE = "private"     # Visible only to specific tenants
    INTERNAL = "internal"   # Internal system extensions
    BETA = "beta"          # Beta extensions for selected tenants


@dataclass
class TenantExtensionAccess:
    """Defines tenant access to a specific extension."""
    tenant_id: str
    extension_name: str
    access_level: TenantAccessLevel
    permissions: List[ExtensionPermission] = field(default_factory=list)
    restrictions: Dict[str, Any] = field(default_factory=dict)
    quota_limits: Dict[str, int] = field(default_factory=dict)
    enabled: bool = True
    granted_at: datetime = field(default_factory=datetime.utcnow)
    granted_by: Optional[str] = None
    expires_at: Optional[datetime] = None


@dataclass
class ExtensionTenantPolicy:
    """Defines tenant policy for an extension."""
    extension_name: str
    visibility: ExtensionVisibility
    default_access_level: TenantAccessLevel
    allowed_tenants: Optional[Set[str]] = None
    blocked_tenants: Optional[Set[str]] = None
    tenant_specific_access: Dict[str, TenantExtensionAccess] = field(default_factory=dict)
    requires_approval: bool = False
    max_tenants: Optional[int] = None


class ExtensionTenantAccessManager:
    """Manages tenant-specific access controls for extensions."""
    
    def __init__(self):
        """Initialize the tenant access manager."""
        self.tenant_access: Dict[str, Dict[str, TenantExtensionAccess]] = {}
        self.extension_policies: Dict[str, ExtensionTenantPolicy] = {}
        self.tenant_quotas: Dict[str, Dict[str, int]] = {}
        self.access_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(minutes=10)
        self._initialize_default_policies()
    
    def _initialize_default_policies(self):
        """Initialize default tenant access policies."""
        # Default policy for general extensions
        self.extension_policies["*"] = ExtensionTenantPolicy(
            extension_name="*",
            visibility=ExtensionVisibility.PUBLIC,
            default_access_level=TenantAccessLevel.STANDARD,
            requires_approval=False
        )
        
        logger.info("Default tenant access policies initialized")
    
    def set_extension_policy(
        self,
        extension_name: str,
        visibility: ExtensionVisibility,
        default_access_level: TenantAccessLevel,
        allowed_tenants: Optional[Set[str]] = None,
        blocked_tenants: Optional[Set[str]] = None,
        requires_approval: bool = False,
        max_tenants: Optional[int] = None
    ) -> bool:
        """Set tenant access policy for an extension."""
        try:
            policy = ExtensionTenantPolicy(
                extension_name=extension_name,
                visibility=visibility,
                default_access_level=default_access_level,
                allowed_tenants=allowed_tenants,
                blocked_tenants=blocked_tenants,
                requires_approval=requires_approval,
                max_tenants=max_tenants
            )
            
            self.extension_policies[extension_name] = policy
            
            # Clear cache for this extension
            self._clear_extension_cache(extension_name)
            
            logger.info(f"Set tenant policy for extension {extension_name}: {visibility.value}, {default_access_level.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting extension policy for {extension_name}: {e}")
            return False
    
    def grant_tenant_access(
        self,
        tenant_id: str,
        extension_name: str,
        access_level: TenantAccessLevel,
        permissions: Optional[List[ExtensionPermission]] = None,
        restrictions: Optional[Dict[str, Any]] = None,
        quota_limits: Optional[Dict[str, int]] = None,
        granted_by: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Grant specific access to an extension for a tenant."""
        try:
            # Check if extension policy allows this tenant
            if not self._validate_tenant_access_grant(tenant_id, extension_name, access_level):
                return False
            
            access = TenantExtensionAccess(
                tenant_id=tenant_id,
                extension_name=extension_name,
                access_level=access_level,
                permissions=permissions or self._get_default_permissions(access_level),
                restrictions=restrictions or {},
                quota_limits=quota_limits or {},
                granted_by=granted_by,
                expires_at=expires_at
            )
            
            if tenant_id not in self.tenant_access:
                self.tenant_access[tenant_id] = {}
            
            self.tenant_access[tenant_id][extension_name] = access
            
            # Update extension policy with tenant-specific access
            if extension_name in self.extension_policies:
                self.extension_policies[extension_name].tenant_specific_access[tenant_id] = access
            
            # Clear cache for this tenant and extension
            self._clear_tenant_extension_cache(tenant_id, extension_name)
            
            logger.info(f"Granted {access_level.value} access to extension {extension_name} for tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error granting tenant access: {e}")
            return False
    
    def revoke_tenant_access(
        self,
        tenant_id: str,
        extension_name: str
    ) -> bool:
        """Revoke tenant access to an extension."""
        try:
            # Remove from tenant access
            if tenant_id in self.tenant_access and extension_name in self.tenant_access[tenant_id]:
                del self.tenant_access[tenant_id][extension_name]
                
                # Clean up empty tenant entries
                if not self.tenant_access[tenant_id]:
                    del self.tenant_access[tenant_id]
            
            # Remove from extension policy
            if (extension_name in self.extension_policies and
                tenant_id in self.extension_policies[extension_name].tenant_specific_access):
                del self.extension_policies[extension_name].tenant_specific_access[tenant_id]
            
            # Clear cache
            self._clear_tenant_extension_cache(tenant_id, extension_name)
            
            logger.info(f"Revoked access to extension {extension_name} for tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking tenant access: {e}")
            return False
    
    def check_tenant_access(
        self,
        user_context: Dict[str, Any],
        extension_name: str,
        required_permission: Optional[ExtensionPermission] = None
    ) -> bool:
        """Check if a tenant has access to an extension."""
        try:
            tenant_id = user_context.get('tenant_id')
            if not tenant_id:
                return False
            
            # Check cache first
            cache_key = f"{tenant_id}:{extension_name}:{required_permission}"
            if cache_key in self.access_cache:
                cache_entry = self.access_cache[cache_key]
                if datetime.utcnow() - cache_entry['timestamp'] < self.cache_ttl:
                    return cache_entry['result']
            
            # Get extension policy
            policy = self.extension_policies.get(extension_name, self.extension_policies.get("*"))
            if not policy:
                return False
            
            # Check if tenant is blocked
            if policy.blocked_tenants and tenant_id in policy.blocked_tenants:
                self._cache_access_result(cache_key, False)
                return False
            
            # Check visibility restrictions
            if policy.visibility == ExtensionVisibility.PRIVATE:
                if not policy.allowed_tenants or tenant_id not in policy.allowed_tenants:
                    self._cache_access_result(cache_key, False)
                    return False
            
            # Get tenant-specific access
            access = self._get_tenant_access(tenant_id, extension_name)
            if not access or not access.enabled:
                # Check if default access is allowed
                if policy.default_access_level == TenantAccessLevel.NONE:
                    self._cache_access_result(cache_key, False)
                    return False
                
                # Create default access
                access = TenantExtensionAccess(
                    tenant_id=tenant_id,
                    extension_name=extension_name,
                    access_level=policy.default_access_level,
                    permissions=self._get_default_permissions(policy.default_access_level)
                )
            
            # Check if access has expired
            if access.expires_at and datetime.utcnow() > access.expires_at:
                self._cache_access_result(cache_key, False)
                return False
            
            # Check specific permission if required
            if required_permission and required_permission not in access.permissions:
                # Check if access level grants the permission
                if not self._access_level_grants_permission(access.access_level, required_permission):
                    self._cache_access_result(cache_key, False)
                    return False
            
            # Check quota limits
            if not self._check_quota_limits(tenant_id, extension_name, access):
                self._cache_access_result(cache_key, False)
                return False
            
            # Check additional restrictions
            if not self._check_access_restrictions(user_context, access):
                self._cache_access_result(cache_key, False)
                return False
            
            self._cache_access_result(cache_key, True)
            return True
            
        except Exception as e:
            logger.error(f"Error checking tenant access: {e}")
            return False
    
    def get_tenant_extensions(
        self,
        tenant_id: str,
        include_disabled: bool = False
    ) -> Dict[str, TenantExtensionAccess]:
        """Get all extensions accessible to a tenant."""
        try:
            accessible_extensions = {}
            
            # Get explicitly granted extensions
            if tenant_id in self.tenant_access:
                for ext_name, access in self.tenant_access[tenant_id].items():
                    if access.enabled or include_disabled:
                        if not access.expires_at or datetime.utcnow() <= access.expires_at:
                            accessible_extensions[ext_name] = access
            
            # Add extensions with default access
            for ext_name, policy in self.extension_policies.items():
                if ext_name == "*":
                    continue
                
                if ext_name not in accessible_extensions:
                    # Check if tenant can access with default policy
                    if self._can_access_with_default_policy(tenant_id, policy):
                        accessible_extensions[ext_name] = TenantExtensionAccess(
                            tenant_id=tenant_id,
                            extension_name=ext_name,
                            access_level=policy.default_access_level,
                            permissions=self._get_default_permissions(policy.default_access_level)
                        )
            
            return accessible_extensions
            
        except Exception as e:
            logger.error(f"Error getting tenant extensions: {e}")
            return {}
    
    def get_extension_tenants(
        self,
        extension_name: str,
        access_level: Optional[TenantAccessLevel] = None
    ) -> List[str]:
        """Get all tenants with access to an extension."""
        try:
            tenants = set()
            
            # Get tenants with explicit access
            for tenant_id, extensions in self.tenant_access.items():
                if extension_name in extensions:
                    access = extensions[extension_name]
                    if (access.enabled and
                        (not access.expires_at or datetime.utcnow() <= access.expires_at) and
                        (not access_level or access.access_level == access_level)):
                        tenants.add(tenant_id)
            
            # Add tenants with default access
            policy = self.extension_policies.get(extension_name)
            if policy and policy.default_access_level != TenantAccessLevel.NONE:
                if not access_level or policy.default_access_level == access_level:
                    # This would require a tenant registry to enumerate all tenants
                    # For now, we only return explicitly granted tenants
                    pass
            
            return list(tenants)
            
        except Exception as e:
            logger.error(f"Error getting extension tenants: {e}")
            return []
    
    def update_tenant_quota(
        self,
        tenant_id: str,
        extension_name: str,
        quota_type: str,
        used_amount: int
    ) -> bool:
        """Update quota usage for a tenant and extension."""
        try:
            if tenant_id not in self.tenant_quotas:
                self.tenant_quotas[tenant_id] = {}
            
            if extension_name not in self.tenant_quotas[tenant_id]:
                self.tenant_quotas[tenant_id][extension_name] = {}
            
            self.tenant_quotas[tenant_id][extension_name][quota_type] = used_amount
            
            logger.debug(f"Updated quota {quota_type} for tenant {tenant_id}, extension {extension_name}: {used_amount}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating tenant quota: {e}")
            return False
    
    def _validate_tenant_access_grant(
        self,
        tenant_id: str,
        extension_name: str,
        access_level: TenantAccessLevel
    ) -> bool:
        """Validate if tenant access can be granted."""
        policy = self.extension_policies.get(extension_name, self.extension_policies.get("*"))
        if not policy:
            return False
        
        # Check if tenant is blocked
        if policy.blocked_tenants and tenant_id in policy.blocked_tenants:
            return False
        
        # Check if extension is private and tenant is not allowed
        if (policy.visibility == ExtensionVisibility.PRIVATE and
            policy.allowed_tenants and tenant_id not in policy.allowed_tenants):
            return False
        
        # Check max tenants limit
        if policy.max_tenants:
            current_tenant_count = len(self.get_extension_tenants(extension_name))
            if current_tenant_count >= policy.max_tenants:
                return False
        
        return True
    
    def _get_tenant_access(
        self,
        tenant_id: str,
        extension_name: str
    ) -> Optional[TenantExtensionAccess]:
        """Get tenant access configuration for an extension."""
        if tenant_id in self.tenant_access and extension_name in self.tenant_access[tenant_id]:
            return self.tenant_access[tenant_id][extension_name]
        return None
    
    def _get_default_permissions(self, access_level: TenantAccessLevel) -> List[ExtensionPermission]:
        """Get default permissions for an access level."""
        permission_map = {
            TenantAccessLevel.NONE: [],
            TenantAccessLevel.READ_ONLY: [ExtensionPermission.READ, ExtensionPermission.HEALTH],
            TenantAccessLevel.LIMITED: [
                ExtensionPermission.READ, ExtensionPermission.HEALTH, ExtensionPermission.WRITE
            ],
            TenantAccessLevel.STANDARD: [
                ExtensionPermission.READ, ExtensionPermission.WRITE, 
                ExtensionPermission.CONFIGURE, ExtensionPermission.HEALTH
            ],
            TenantAccessLevel.PREMIUM: [
                ExtensionPermission.READ, ExtensionPermission.WRITE,
                ExtensionPermission.CONFIGURE, ExtensionPermission.BACKGROUND_TASKS,
                ExtensionPermission.HEALTH, ExtensionPermission.METRICS
            ],
            TenantAccessLevel.ADMIN: [perm for perm in ExtensionPermission]
        }
        
        return permission_map.get(access_level, [])
    
    def _access_level_grants_permission(
        self,
        access_level: TenantAccessLevel,
        permission: ExtensionPermission
    ) -> bool:
        """Check if an access level grants a specific permission."""
        default_permissions = self._get_default_permissions(access_level)
        return permission in default_permissions
    
    def _check_quota_limits(
        self,
        tenant_id: str,
        extension_name: str,
        access: TenantExtensionAccess
    ) -> bool:
        """Check if tenant is within quota limits."""
        if not access.quota_limits:
            return True
        
        current_usage = self.tenant_quotas.get(tenant_id, {}).get(extension_name, {})
        
        for quota_type, limit in access.quota_limits.items():
            used = current_usage.get(quota_type, 0)
            if used >= limit:
                logger.warning(f"Tenant {tenant_id} exceeded quota {quota_type} for extension {extension_name}: {used}/{limit}")
                return False
        
        return True
    
    def _check_access_restrictions(
        self,
        user_context: Dict[str, Any],
        access: TenantExtensionAccess
    ) -> bool:
        """Check additional access restrictions."""
        if not access.restrictions:
            return True
        
        # Check time-based restrictions
        if 'allowed_hours' in access.restrictions:
            current_hour = datetime.utcnow().hour
            if current_hour not in access.restrictions['allowed_hours']:
                return False
        
        # Check IP-based restrictions
        if 'allowed_ips' in access.restrictions and 'client_ip' in user_context:
            client_ip = user_context['client_ip']
            if client_ip not in access.restrictions['allowed_ips']:
                return False
        
        # Check user role restrictions
        if 'required_roles' in access.restrictions:
            user_roles = set(user_context.get('roles', []))
            required_roles = set(access.restrictions['required_roles'])
            if not user_roles.intersection(required_roles):
                return False
        
        return True
    
    def _can_access_with_default_policy(
        self,
        tenant_id: str,
        policy: ExtensionTenantPolicy
    ) -> bool:
        """Check if tenant can access extension with default policy."""
        if policy.default_access_level == TenantAccessLevel.NONE:
            return False
        
        if policy.blocked_tenants and tenant_id in policy.blocked_tenants:
            return False
        
        if (policy.visibility == ExtensionVisibility.PRIVATE and
            policy.allowed_tenants and tenant_id not in policy.allowed_tenants):
            return False
        
        return True
    
    def _cache_access_result(self, cache_key: str, result: bool):
        """Cache access check result."""
        self.access_cache[cache_key] = {
            'result': result,
            'timestamp': datetime.utcnow()
        }
    
    def _clear_extension_cache(self, extension_name: str):
        """Clear cache for a specific extension."""
        keys_to_remove = [key for key in self.access_cache.keys() if f":{extension_name}:" in key]
        for key in keys_to_remove:
            del self.access_cache[key]
    
    def _clear_tenant_extension_cache(self, tenant_id: str, extension_name: str):
        """Clear cache for a specific tenant and extension."""
        keys_to_remove = [key for key in self.access_cache.keys() if key.startswith(f"{tenant_id}:{extension_name}:")]
        for key in keys_to_remove:
            del self.access_cache[key]
    
    def cleanup_expired_access(self) -> int:
        """Clean up expired tenant access grants."""
        try:
            removed_count = 0
            current_time = datetime.utcnow()
            
            for tenant_id in list(self.tenant_access.keys()):
                for ext_name in list(self.tenant_access[tenant_id].keys()):
                    access = self.tenant_access[tenant_id][ext_name]
                    if access.expires_at and access.expires_at <= current_time:
                        del self.tenant_access[tenant_id][ext_name]
                        removed_count += 1
                
                # Clean up empty tenant entries
                if not self.tenant_access[tenant_id]:
                    del self.tenant_access[tenant_id]
            
            # Clean up extension policies
            for ext_name in self.extension_policies:
                policy = self.extension_policies[ext_name]
                expired_tenants = []
                for tenant_id, access in policy.tenant_specific_access.items():
                    if access.expires_at and access.expires_at <= current_time:
                        expired_tenants.append(tenant_id)
                
                for tenant_id in expired_tenants:
                    del policy.tenant_specific_access[tenant_id]
                    removed_count += 1
            
            # Clean up cache
            self._cleanup_access_cache()
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} expired tenant access grants")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired access: {e}")
            return 0
    
    def _cleanup_access_cache(self):
        """Clean up expired cache entries."""
        current_time = datetime.utcnow()
        keys_to_remove = []
        
        for key, entry in self.access_cache.items():
            if current_time - entry['timestamp'] >= self.cache_ttl:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.access_cache[key]


# Global tenant access manager instance
_tenant_access_manager: Optional[ExtensionTenantAccessManager] = None


def get_extension_tenant_access_manager() -> ExtensionTenantAccessManager:
    """Get or create the global extension tenant access manager."""
    global _tenant_access_manager
    if _tenant_access_manager is None:
        _tenant_access_manager = ExtensionTenantAccessManager()
    return _tenant_access_manager


def check_tenant_extension_access(
    user_context: Dict[str, Any],
    extension_name: str,
    required_permission: Optional[ExtensionPermission] = None
) -> bool:
    """Convenience function to check tenant extension access."""
    manager = get_extension_tenant_access_manager()
    return manager.check_tenant_access(user_context, extension_name, required_permission)