"""
Extension Tenant Access service for managing tenant-specific access to extensions.

This service provides capabilities for managing tenant-specific access to extensions,
including tenant isolation, access control, and resource management.
"""

from typing import Dict, List, Any, Optional, Set
import asyncio
import logging
import time
from datetime import datetime

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus, ServiceHealth


class ExtensionTenantAccess(BaseService):
    """
    Extension Tenant Access service for managing tenant-specific access to extensions.
    
    This service provides capabilities for managing tenant-specific access to extensions,
    including tenant isolation, access control, and resource management.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="extension_tenant_access"))
        self._initialized = False
        self._tenant_extensions: Dict[str, Set[str]] = {}  # tenant_id -> set of extension_ids
        self._extension_tenants: Dict[str, Set[str]] = {}  # extension_id -> set of tenant_ids
        self._tenant_access_policies: Dict[str, Dict[str, Any]] = {}  # tenant_id -> access_policy
        self._extension_resources: Dict[str, Dict[str, Any]] = {}  # extension_id -> resource_limits
        self._tenant_resource_usage: Dict[str, Dict[str, Any]] = {}  # tenant_id -> resource_usage
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize the Extension Tenant Access service."""
        if self._initialized:
            return
            
        try:
            self.logger.info("Initializing Extension Tenant Access service")
            
            # Initialize tenant-extension mappings
            self._tenant_extensions = {}
            self._extension_tenants = {}
            self._tenant_access_policies = {}
            self._extension_resources = {}
            self._tenant_resource_usage = {}
            
            self._initialized = True
            self._status = ServiceStatus.RUNNING
            self.logger.info("Extension Tenant Access service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Extension Tenant Access service: {str(e)}")
            self._status = ServiceStatus.ERROR
            raise
            
    async def grant_access(self, tenant_id: str, extension_id: str, access_policy: Optional[Dict[str, Any]] = None) -> None:
        """Grant access to an extension for a tenant."""
        async with self._lock:
            # Add tenant to extension's tenant set
            if extension_id not in self._extension_tenants:
                self._extension_tenants[extension_id] = set()
            self._extension_tenants[extension_id].add(tenant_id)
            
            # Add extension to tenant's extension set
            if tenant_id not in self._tenant_extensions:
                self._tenant_extensions[tenant_id] = set()
            self._tenant_extensions[tenant_id].add(extension_id)
            
            # Set access policy
            if access_policy:
                self._tenant_access_policies[f"{tenant_id}:{extension_id}"] = access_policy
            else:
                # Default access policy
                self._tenant_access_policies[f"{tenant_id}:{extension_id}"] = {
                    "read": True,
                    "write": True,
                    "execute": True,
                    "resource_limits": {
                        "cpu": "1",
                        "memory": "1Gi",
                        "storage": "1Gi"
                    }
                }
                
            # Initialize resource usage tracking
            if tenant_id not in self._tenant_resource_usage:
                self._tenant_resource_usage[tenant_id] = {}
                
            if extension_id not in self._tenant_resource_usage[tenant_id]:
                self._tenant_resource_usage[tenant_id][extension_id] = {
                    "cpu_usage": 0,
                    "memory_usage": 0,
                    "storage_usage": 0,
                    "request_count": 0
                }
                
        self.logger.info(f"Granted access to extension {extension_id} for tenant {tenant_id}")
        
    async def revoke_access(self, tenant_id: str, extension_id: str) -> None:
        """Revoke access to an extension for a tenant."""
        async with self._lock:
            # Remove tenant from extension's tenant set
            if extension_id in self._extension_tenants:
                self._extension_tenants[extension_id].discard(tenant_id)
                
            # Remove extension from tenant's extension set
            if tenant_id in self._tenant_extensions:
                self._tenant_extensions[tenant_id].discard(extension_id)
                
            # Remove access policy
            policy_key = f"{tenant_id}:{extension_id}"
            if policy_key in self._tenant_access_policies:
                del self._tenant_access_policies[policy_key]
                
            # Remove resource usage tracking
            if tenant_id in self._tenant_resource_usage and extension_id in self._tenant_resource_usage[tenant_id]:
                del self._tenant_resource_usage[tenant_id][extension_id]
                
        self.logger.info(f"Revoked access to extension {extension_id} for tenant {tenant_id}")
        
    async def check_access(self, tenant_id: str, extension_id: str, permission: str) -> bool:
        """Check if a tenant has a specific permission for an extension."""
        async with self._lock:
            policy_key = f"{tenant_id}:{extension_id}"
            policy = self._tenant_access_policies.get(policy_key, {})
            
            return policy.get(permission, False)
            
    async def get_tenant_extensions(self, tenant_id: str) -> Set[str]:
        """Get the set of extensions accessible to a tenant."""
        async with self._lock:
            return self._tenant_extensions.get(tenant_id, set()).copy()
            
    async def get_extension_tenants(self, extension_id: str) -> Set[str]:
        """Get the set of tenants that have access to an extension."""
        async with self._lock:
            return self._extension_tenants.get(extension_id, set()).copy()
            
    async def get_access_policy(self, tenant_id: str, extension_id: str) -> Dict[str, Any]:
        """Get the access policy for a tenant and extension."""
        async with self._lock:
            policy_key = f"{tenant_id}:{extension_id}"
            return self._tenant_access_policies.get(policy_key, {}).copy()
            
    async def update_access_policy(self, tenant_id: str, extension_id: str, policy: Dict[str, Any]) -> None:
        """Update the access policy for a tenant and extension."""
        async with self._lock:
            policy_key = f"{tenant_id}:{extension_id}"
            self._tenant_access_policies[policy_key] = policy
            
        self.logger.info(f"Updated access policy for extension {extension_id} and tenant {tenant_id}")
        
    async def set_extension_resources(self, extension_id: str, resources: Dict[str, Any]) -> None:
        """Set the resource limits for an extension."""
        async with self._lock:
            self._extension_resources[extension_id] = resources
            
        self.logger.info(f"Set resource limits for extension {extension_id}")
        
    async def get_extension_resources(self, extension_id: str) -> Dict[str, Any]:
        """Get the resource limits for an extension."""
        async with self._lock:
            return self._extension_resources.get(extension_id, {}).copy()
            
    async def update_resource_usage(self, tenant_id: str, extension_id: str, usage: Dict[str, Any]) -> None:
        """Update the resource usage for a tenant and extension."""
        async with self._lock:
            if tenant_id not in self._tenant_resource_usage:
                self._tenant_resource_usage[tenant_id] = {}
                
            if extension_id not in self._tenant_resource_usage[tenant_id]:
                self._tenant_resource_usage[tenant_id][extension_id] = {
                    "cpu_usage": 0,
                    "memory_usage": 0,
                    "storage_usage": 0,
                    "request_count": 0
                }
                
            # Update usage
            for key, value in usage.items():
                if key in self._tenant_resource_usage[tenant_id][extension_id]:
                    self._tenant_resource_usage[tenant_id][extension_id][key] += value
                else:
                    self._tenant_resource_usage[tenant_id][extension_id][key] = value
                    
    async def get_resource_usage(self, tenant_id: str, extension_id: str) -> Dict[str, Any]:
        """Get the resource usage for a tenant and extension."""
        async with self._lock:
            if tenant_id in self._tenant_resource_usage and extension_id in self._tenant_resource_usage[tenant_id]:
                return self._tenant_resource_usage[tenant_id][extension_id].copy()
            return {}
            
    async def check_resource_limits(self, tenant_id: str, extension_id: str) -> bool:
        """Check if a tenant is within resource limits for an extension."""
        async with self._lock:
            # Get resource limits
            policy_key = f"{tenant_id}:{extension_id}"
            policy = self._tenant_access_policies.get(policy_key, {})
            resource_limits = policy.get("resource_limits", {})
            
            # Get current usage
            if tenant_id not in self._tenant_resource_usage or extension_id not in self._tenant_resource_usage[tenant_id]:
                return True
                
            usage = self._tenant_resource_usage[tenant_id][extension_id]
            
            # Check each resource
            for resource, limit in resource_limits.items():
                if resource in usage and usage[resource] > limit:
                    return False
                    
            return True
            
    async def health_check(self) -> ServiceHealth:
        """Perform a health check of the service."""
        status = ServiceStatus.RUNNING if self._initialized else ServiceStatus.INITIALIZING
        
        return ServiceHealth(
            status=status,
            last_check=datetime.now(),
            details={
                "tenants": len(self._tenant_extensions),
                "extensions": len(self._extension_tenants),
                "access_policies": len(self._tenant_access_policies)
            }
        )
        
    async def shutdown(self) -> None:
        """Shutdown the service."""
        self.logger.info("Shutting down Extension Tenant Access service")
        
        self._tenant_extensions.clear()
        self._extension_tenants.clear()
        self._tenant_access_policies.clear()
        self._extension_resources.clear()
        self._tenant_resource_usage.clear()
        
        self._initialized = False
        self._status = ServiceStatus.SHUTDOWN
        self.logger.info("Extension Tenant Access service shutdown complete")