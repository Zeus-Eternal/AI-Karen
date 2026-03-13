"""
Extension Permissions Service

This service manages fine-grained permissions for extensions in the AI Karen system,
providing detailed access control to system resources and functionality.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, Union

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus


class ExtensionPermissions(BaseService):
    """
    Extension Permissions service for managing fine-grained extension permissions.
    
    This service provides capabilities for defining, managing, and enforcing
    fine-grained permissions for extensions in the AI Karen system.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="extension_permissions"))
        self._initialized = False
        self._permission_definitions: Dict[str, Dict[str, Any]] = {}  # permission_name -> definition
        self._permission_hierarchy: Dict[str, List[str]] = {}  # parent_permission -> child_permissions
        self._extension_permissions: Dict[str, Set[str]] = {}  # extension_id -> set of permissions
        self._permission_groups: Dict[str, Set[str]] = {}  # group_name -> set of permissions
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """Initialize the Extension Permissions service."""
        try:
            self.logger.info("Initializing Extension Permissions service")
            
            # Initialize default permissions
            await self._initialize_default_permissions()
            
            self._initialized = True
            self._status = ServiceStatus.RUNNING
            self.logger.info("Extension Permissions service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Extension Permissions service: {e}")
            self._status = ServiceStatus.ERROR
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown the Extension Permissions service."""
        try:
            self.logger.info("Shutting down Extension Permissions service")
            
            async with self._lock:
                self._permission_definitions.clear()
                self._permission_hierarchy.clear()
                self._extension_permissions.clear()
                self._permission_groups.clear()
            
            self._initialized = False
            self._status = ServiceStatus.STOPPED
            self.logger.info("Extension Permissions service shutdown successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to shutdown Extension Permissions service: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check the health of the Extension Permissions service."""
        return self._initialized and self._status == ServiceStatus.RUNNING
    
    async def define_permission(
        self,
        name: str,
        description: str,
        resource: str,
        action: str,
        parent: Optional[str] = None
    ) -> bool:
        """
        Define a new permission.
        
        Args:
            name: The name of the permission
            description: A description of the permission
            resource: The resource this permission applies to
            action: The action this permission allows
            parent: Optional parent permission
            
        Returns:
            True if the permission was defined successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Permissions service is not initialized")
        
        async with self._lock:
            if name in self._permission_definitions:
                self.logger.warning(f"Permission {name} is already defined")
                return False
            
            # Define the permission
            self._permission_definitions[name] = {
                "description": description,
                "resource": resource,
                "action": action,
                "parent": parent
            }
            
            # Add to hierarchy if it has a parent
            if parent:
                if parent not in self._permission_hierarchy:
                    self._permission_hierarchy[parent] = []
                self._permission_hierarchy[parent].append(name)
        
        self.logger.info(f"Permission {name} defined successfully")
        return True
    
    async def undefine_permission(self, name: str) -> bool:
        """
        Undefine a permission.
        
        Args:
            name: The name of the permission
            
        Returns:
            True if the permission was undefined successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Permissions service is not initialized")
        
        async with self._lock:
            if name not in self._permission_definitions:
                self.logger.warning(f"Permission {name} is not defined")
                return False
            
            # Check if any other permissions have this as a parent
            for parent, children in self._permission_hierarchy.items():
                if name in children:
                    self.logger.error(f"Cannot undefine permission {name}: it is a parent of other permissions")
                    return False
            
            # Remove from hierarchy if it has a parent
            parent = self._permission_definitions[name].get("parent")
            if parent and parent in self._permission_hierarchy:
                if name in self._permission_hierarchy[parent]:
                    self._permission_hierarchy[parent].remove(name)
            
            # Remove from all extensions
            for extension_id, permissions in self._extension_permissions.items():
                if name in permissions:
                    permissions.remove(name)
            
            # Remove from all groups
            for group_name, permissions in self._permission_groups.items():
                if name in permissions:
                    permissions.remove(name)
            
            # Undefine the permission
            del self._permission_definitions[name]
        
        self.logger.info(f"Permission {name} undefined successfully")
        return True
    
    async def get_permission_definition(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get the definition of a permission.
        
        Args:
            name: The name of the permission
            
        Returns:
            The permission definition or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension Permissions service is not initialized")
        
        async with self._lock:
            if name in self._permission_definitions:
                return self._permission_definitions[name].copy()
            else:
                return None
    
    async def get_all_permission_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all permission definitions.
        
        Returns:
            Dictionary mapping permission names to permission definitions
        """
        if not self._initialized:
            raise RuntimeError("Extension Permissions service is not initialized")
        
        async with self._lock:
            result = {}
            for name, definition in self._permission_definitions.items():
                result[name] = definition.copy()
            return result
    
    async def grant_permission(
        self,
        extension_id: str,
        permission: str
    ) -> bool:
        """
        Grant a permission to an extension.
        
        Args:
            extension_id: The ID of the extension
            permission: The name of the permission
            
        Returns:
            True if the permission was granted successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Permissions service is not initialized")
        
        async with self._lock:
            if permission not in self._permission_definitions:
                self.logger.error(f"Permission {permission} is not defined")
                return False
            
            if extension_id not in self._extension_permissions:
                self._extension_permissions[extension_id] = set()
            
            if permission in self._extension_permissions[extension_id]:
                self.logger.warning(f"Extension {extension_id} already has permission {permission}")
                return True
            
            # Grant the permission
            self._extension_permissions[extension_id].add(permission)
            
            # Also grant all child permissions
            if permission in self._permission_hierarchy:
                for child_permission in self._permission_hierarchy[permission]:
                    await self.grant_permission(extension_id, child_permission)
        
        self.logger.info(f"Permission {permission} granted to extension {extension_id}")
        return True
    
    async def revoke_permission(
        self,
        extension_id: str,
        permission: str
    ) -> bool:
        """
        Revoke a permission from an extension.
        
        Args:
            extension_id: The ID of the extension
            permission: The name of the permission
            
        Returns:
            True if the permission was revoked successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Permissions service is not initialized")
        
        async with self._lock:
            if extension_id not in self._extension_permissions:
                self.logger.warning(f"Extension {extension_id} has no permissions")
                return False
            
            if permission not in self._extension_permissions[extension_id]:
                self.logger.warning(f"Extension {extension_id} does not have permission {permission}")
                return True
            
            # Revoke the permission
            self._extension_permissions[extension_id].discard(permission)
            
            # Also revoke all child permissions
            if permission in self._permission_hierarchy:
                for child_permission in self._permission_hierarchy[permission]:
                    await self.revoke_permission(extension_id, child_permission)
        
        self.logger.info(f"Permission {permission} revoked from extension {extension_id}")
        return True
    
    async def check_permission(
        self,
        extension_id: str,
        permission: str
    ) -> bool:
        """
        Check if an extension has a permission.
        
        Args:
            extension_id: The ID of the extension
            permission: The name of the permission
            
        Returns:
            True if the extension has the permission, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Permissions service is not initialized")
        
        async with self._lock:
            if extension_id not in self._extension_permissions:
                return False
            
            return permission in self._extension_permissions[extension_id]
    
    async def get_extension_permissions(self, extension_id: str) -> Set[str]:
        """
        Get all permissions of an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            Set of permission names
        """
        if not self._initialized:
            raise RuntimeError("Extension Permissions service is not initialized")
        
        async with self._lock:
            if extension_id in self._extension_permissions:
                return self._extension_permissions[extension_id].copy()
            else:
                return set()
    
    async def create_permission_group(
        self,
        name: str,
        permissions: List[str]
    ) -> bool:
        """
        Create a permission group.
        
        Args:
            name: The name of the group
            permissions: List of permissions in the group
            
        Returns:
            True if the group was created successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Permissions service is not initialized")
        
        async with self._lock:
            if name in self._permission_groups:
                self.logger.warning(f"Permission group {name} already exists")
                return False
            
            # Validate that all permissions exist
            for permission in permissions:
                if permission not in self._permission_definitions:
                    self.logger.error(f"Permission {permission} is not defined")
                    return False
            
            # Create the group
            self._permission_groups[name] = set(permissions)
        
        self.logger.info(f"Permission group {name} created successfully")
        return True
    
    async def delete_permission_group(self, name: str) -> bool:
        """
        Delete a permission group.
        
        Args:
            name: The name of the group
            
        Returns:
            True if the group was deleted successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Permissions service is not initialized")
        
        async with self._lock:
            if name not in self._permission_groups:
                self.logger.warning(f"Permission group {name} does not exist")
                return False
            
            # Delete the group
            del self._permission_groups[name]
        
        self.logger.info(f"Permission group {name} deleted successfully")
        return True
    
    async def get_permission_group(self, name: str) -> Optional[Set[str]]:
        """
        Get a permission group.
        
        Args:
            name: The name of the group
            
        Returns:
            Set of permission names or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension Permissions service is not initialized")
        
        async with self._lock:
            if name in self._permission_groups:
                return self._permission_groups[name].copy()
            else:
                return None
    
    async def get_all_permission_groups(self) -> Dict[str, Set[str]]:
        """
        Get all permission groups.
        
        Returns:
            Dictionary mapping group names to sets of permission names
        """
        if not self._initialized:
            raise RuntimeError("Extension Permissions service is not initialized")
        
        async with self._lock:
            result = {}
            for name, permissions in self._permission_groups.items():
                result[name] = permissions.copy()
            return result
    
    async def grant_permission_group(
        self,
        extension_id: str,
        group_name: str
    ) -> bool:
        """
        Grant all permissions in a group to an extension.
        
        Args:
            extension_id: The ID of the extension
            group_name: The name of the permission group
            
        Returns:
            True if the permissions were granted successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Permissions service is not initialized")
        
        async with self._lock:
            if group_name not in self._permission_groups:
                self.logger.error(f"Permission group {group_name} does not exist")
                return False
            
            # Grant all permissions in the group
            for permission in self._permission_groups[group_name]:
                await self.grant_permission(extension_id, permission)
        
        self.logger.info(f"Permission group {group_name} granted to extension {extension_id}")
        return True
    
    async def revoke_permission_group(
        self,
        extension_id: str,
        group_name: str
    ) -> bool:
        """
        Revoke all permissions in a group from an extension.
        
        Args:
            extension_id: The ID of the extension
            group_name: The name of the permission group
            
        Returns:
            True if the permissions were revoked successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Permissions service is not initialized")
        
        async with self._lock:
            if group_name not in self._permission_groups:
                self.logger.error(f"Permission group {group_name} does not exist")
                return False
            
            # Revoke all permissions in the group
            for permission in self._permission_groups[group_name]:
                await self.revoke_permission(extension_id, permission)
        
        self.logger.info(f"Permission group {group_name} revoked from extension {extension_id}")
        return True
    
    async def _initialize_default_permissions(self) -> None:
        """Initialize default permissions and groups."""
        # Define default permissions
        default_permissions = [
            {
                "name": "extension.read",
                "description": "Read extension information",
                "resource": "extension",
                "action": "read"
            },
            {
                "name": "extension.write",
                "description": "Modify extension information",
                "resource": "extension",
                "action": "write",
                "parent": "extension.read"
            },
            {
                "name": "extension.execute",
                "description": "Execute extension functions",
                "resource": "extension",
                "action": "execute",
                "parent": "extension.read"
            },
            {
                "name": "config.read",
                "description": "Read configuration",
                "resource": "config",
                "action": "read"
            },
            {
                "name": "config.write",
                "description": "Modify configuration",
                "resource": "config",
                "action": "write",
                "parent": "config.read"
            },
            {
                "name": "system.read",
                "description": "Read system information",
                "resource": "system",
                "action": "read"
            },
            {
                "name": "system.write",
                "description": "Modify system information",
                "resource": "system",
                "action": "write",
                "parent": "system.read"
            }
        ]
        
        # Define default permissions
        for perm_def in default_permissions:
            await self.define_permission(
                perm_def["name"],
                perm_def["description"],
                perm_def["resource"],
                perm_def["action"],
                perm_def.get("parent")
            )
        
        # Define default permission groups
        default_groups = [
            {
                "name": "extension.basic",
                "permissions": ["extension.read"]
            },
            {
                "name": "extension.advanced",
                "permissions": ["extension.read", "extension.write", "extension.execute"]
            },
            {
                "name": "config.basic",
                "permissions": ["config.read"]
            },
            {
                "name": "config.advanced",
                "permissions": ["config.read", "config.write"]
            },
            {
                "name": "system.basic",
                "permissions": ["system.read"]
            },
            {
                "name": "system.advanced",
                "permissions": ["system.read", "system.write"]
            },
            {
                "name": "guest",
                "permissions": ["extension.read", "config.read", "system.read"]
            },
            {
                "name": "admin",
                "permissions": [
                    "extension.read", "extension.write", "extension.execute",
                    "config.read", "config.write",
                    "system.read", "system.write"
                ]
            }
        ]
        
        # Create default permission groups
        for group_def in default_groups:
            await self.create_permission_group(
                group_def["name"],
                group_def["permissions"]
            )