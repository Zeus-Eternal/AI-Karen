"""
Extension RBAC Service

This service implements Role-Based Access Control (RBAC) for extensions in the AI Karen system,
providing a comprehensive framework for managing extension access through roles and permissions.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, Union

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus


class ExtensionRBAC(BaseService):
    """
    Extension RBAC service for implementing Role-Based Access Control.
    
    This service provides capabilities for defining roles, assigning permissions
    to roles, and managing role assignments for extensions.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="extension_rbac"))
        self._initialized = False
        self._roles: Dict[str, Dict[str, Any]] = {}  # role_name -> role_definition
        self._role_permissions: Dict[str, Set[str]] = {}  # role_name -> set of permissions
        self._role_hierarchy: Dict[str, List[str]] = {}  # parent_role -> child_roles
        self._extension_roles: Dict[str, Set[str]] = {}  # extension_id -> set of roles
        self._extension_permissions: Dict[str, Set[str]] = {}  # extension_id -> set of permissions
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """Initialize the Extension RBAC service."""
        try:
            self.logger.info("Initializing Extension RBAC service")
            
            # Initialize default roles and permissions
            await self._initialize_default_roles()
            
            self._initialized = True
            self._status = ServiceStatus.RUNNING
            self.logger.info("Extension RBAC service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Extension RBAC service: {e}")
            self._status = ServiceStatus.ERROR
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown the Extension RBAC service."""
        try:
            self.logger.info("Shutting down Extension RBAC service")
            
            async with self._lock:
                self._roles.clear()
                self._role_permissions.clear()
                self._role_hierarchy.clear()
                self._extension_roles.clear()
                self._extension_permissions.clear()
            
            self._initialized = False
            self._status = ServiceStatus.STOPPED
            self.logger.info("Extension RBAC service shutdown successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to shutdown Extension RBAC service: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check the health of the Extension RBAC service."""
        return self._initialized and self._status == ServiceStatus.RUNNING
    
    async def create_role(
        self,
        name: str,
        description: str,
        permissions: Optional[List[str]] = None,
        parent_roles: Optional[List[str]] = None
    ) -> bool:
        """
        Create a new role.
        
        Args:
            name: The name of the role
            description: A description of the role
            permissions: Optional list of permissions to assign to the role
            parent_roles: Optional list of parent roles
            
        Returns:
            True if the role was created successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension RBAC service is not initialized")
        
        async with self._lock:
            if name in self._roles:
                self.logger.warning(f"Role {name} already exists")
                return False
            
            # Create the role
            self._roles[name] = {
                "description": description,
                "permissions": permissions or [],
                "parent_roles": parent_roles or []
            }
            
            # Initialize role permissions
            self._role_permissions[name] = set(permissions or [])
            
            # Add to hierarchy if it has parent roles
            if parent_roles:
                for parent_role in parent_roles:
                    if parent_role not in self._role_hierarchy:
                        self._role_hierarchy[parent_role] = []
                    self._role_hierarchy[parent_role].append(name)
        
        self.logger.info(f"Role {name} created successfully")
        return True
    
    async def delete_role(self, name: str) -> bool:
        """
        Delete a role.
        
        Args:
            name: The name of the role
            
        Returns:
            True if the role was deleted successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension RBAC service is not initialized")
        
        async with self._lock:
            if name not in self._roles:
                self.logger.warning(f"Role {name} does not exist")
                return False
            
            # Check if any other roles have this as a parent
            for parent, children in self._role_hierarchy.items():
                if name in children:
                    self.logger.error(f"Cannot delete role {name}: it is a parent of other roles")
                    return False
            
            # Remove from hierarchy if it has parent roles
            parent_roles = self._roles[name].get("parent_roles", [])
            for parent_role in parent_roles:
                if parent_role in self._role_hierarchy and name in self._role_hierarchy[parent_role]:
                    self._role_hierarchy[parent_role].remove(name)
            
            # Remove from all extensions
            for extension_id, roles in self._extension_roles.items():
                if name in roles:
                    roles.remove(name)
                    # Recalculate permissions for the extension
                    await self._recalculate_extension_permissions(extension_id)
            
            # Delete the role
            del self._roles[name]
            del self._role_permissions[name]
        
        self.logger.info(f"Role {name} deleted successfully")
        return True
    
    async def get_role(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a role definition.
        
        Args:
            name: The name of the role
            
        Returns:
            The role definition or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension RBAC service is not initialized")
        
        async with self._lock:
            if name in self._roles:
                role_info = self._roles[name].copy()
                role_info["permissions"] = list(self._role_permissions[name])
                return role_info
            else:
                return None
    
    async def get_all_roles(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all role definitions.
        
        Returns:
            Dictionary mapping role names to role definitions
        """
        if not self._initialized:
            raise RuntimeError("Extension RBAC service is not initialized")
        
        async with self._lock:
            result = {}
            for name, role_info in self._roles.items():
                role_copy = role_info.copy()
                role_copy["permissions"] = list(self._role_permissions[name])
                result[name] = role_copy
            return result
    
    async def add_permission_to_role(self, role_name: str, permission: str) -> bool:
        """
        Add a permission to a role.
        
        Args:
            role_name: The name of the role
            permission: The permission to add
            
        Returns:
            True if the permission was added successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension RBAC service is not initialized")
        
        async with self._lock:
            if role_name not in self._roles:
                self.logger.warning(f"Role {role_name} does not exist")
                return False
            
            # Add the permission
            self._role_permissions[role_name].add(permission)
            
            # Update all extensions with this role
            for extension_id, roles in self._extension_roles.items():
                if role_name in roles:
                    # Add the permission to the extension
                    if extension_id not in self._extension_permissions:
                        self._extension_permissions[extension_id] = set()
                    self._extension_permissions[extension_id].add(permission)
        
        self.logger.info(f"Permission {permission} added to role {role_name}")
        return True
    
    async def remove_permission_from_role(self, role_name: str, permission: str) -> bool:
        """
        Remove a permission from a role.
        
        Args:
            role_name: The name of the role
            permission: The permission to remove
            
        Returns:
            True if the permission was removed successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension RBAC service is not initialized")
        
        async with self._lock:
            if role_name not in self._roles:
                self.logger.warning(f"Role {role_name} does not exist")
                return False
            
            # Remove the permission
            self._role_permissions[role_name].discard(permission)
            
            # Update all extensions with this role
            for extension_id, roles in self._extension_roles.items():
                if role_name in roles:
                    # Recalculate permissions for the extension
                    await self._recalculate_extension_permissions(extension_id)
        
        self.logger.info(f"Permission {permission} removed from role {role_name}")
        return True
    
    async def assign_role_to_extension(self, extension_id: str, role_name: str) -> bool:
        """
        Assign a role to an extension.
        
        Args:
            extension_id: The ID of the extension
            role_name: The name of the role
            
        Returns:
            True if the role was assigned successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension RBAC service is not initialized")
        
        async with self._lock:
            if role_name not in self._roles:
                self.logger.warning(f"Role {role_name} does not exist")
                return False
            
            if extension_id not in self._extension_roles:
                self._extension_roles[extension_id] = set()
            
            # Assign the role
            if role_name not in self._extension_roles[extension_id]:
                self._extension_roles[extension_id].add(role_name)
                
                # Recalculate permissions for the extension
                await self._recalculate_extension_permissions(extension_id)
        
        self.logger.info(f"Role {role_name} assigned to extension {extension_id}")
        return True
    
    async def unassign_role_from_extension(self, extension_id: str, role_name: str) -> bool:
        """
        Unassign a role from an extension.
        
        Args:
            extension_id: The ID of the extension
            role_name: The name of the role
            
        Returns:
            True if the role was unassigned successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension RBAC service is not initialized")
        
        async with self._lock:
            if extension_id not in self._extension_roles:
                self.logger.warning(f"Extension {extension_id} has no roles")
                return False
            
            if role_name in self._extension_roles[extension_id]:
                # Unassign the role
                self._extension_roles[extension_id].discard(role_name)
                
                # Recalculate permissions for the extension
                await self._recalculate_extension_permissions(extension_id)
        
        self.logger.info(f"Role {role_name} unassigned from extension {extension_id}")
        return True
    
    async def get_extension_roles(self, extension_id: str) -> Set[str]:
        """
        Get the roles of an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            Set of role names
        """
        if not self._initialized:
            raise RuntimeError("Extension RBAC service is not initialized")
        
        async with self._lock:
            if extension_id in self._extension_roles:
                return self._extension_roles[extension_id].copy()
            else:
                return set()
    
    async def get_extension_permissions(self, extension_id: str) -> Set[str]:
        """
        Get the permissions of an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            Set of permission names
        """
        if not self._initialized:
            raise RuntimeError("Extension RBAC service is not initialized")
        
        async with self._lock:
            if extension_id in self._extension_permissions:
                return self._extension_permissions[extension_id].copy()
            else:
                return set()
    
    async def check_extension_permission(self, extension_id: str, permission: str) -> bool:
        """
        Check if an extension has a specific permission.
        
        Args:
            extension_id: The ID of the extension
            permission: The permission to check
            
        Returns:
            True if the extension has the permission, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension RBAC service is not initialized")
        
        async with self._lock:
            if extension_id in self._extension_permissions:
                return permission in self._extension_permissions[extension_id]
            else:
                return False
    
    async def _recalculate_extension_permissions(self, extension_id: str) -> None:
        """
        Recalculate the permissions for an extension based on its roles.
        
        Args:
            extension_id: The ID of the extension
        """
        if extension_id not in self._extension_roles:
            self._extension_permissions[extension_id] = set()
            return
        
        # Get all roles for the extension
        roles = self._extension_roles[extension_id].copy()
        
        # Get all permissions from all roles, including parent roles
        permissions = set()
        processed_roles = set()
        
        async def collect_role_permissions(role_name: str) -> None:
            if role_name in processed_roles:
                return
            
            processed_roles.add(role_name)
            
            if role_name in self._role_permissions:
                permissions.update(self._role_permissions[role_name])
            
            # Process parent roles
            if role_name in self._roles:
                for parent_role in self._roles[role_name].get("parent_roles", []):
                    await collect_role_permissions(parent_role)
        
        # Collect permissions from all roles
        for role in roles:
            await collect_role_permissions(role)
        
        # Update the extension's permissions
        self._extension_permissions[extension_id] = permissions
    
    async def _initialize_default_roles(self) -> None:
        """Initialize default roles and permissions."""
        # Define default roles
        default_roles = [
            {
                "name": "admin",
                "description": "Administrator with full access",
                "permissions": [
                    "system.read", "system.write", "system.admin",
                    "extension.read", "extension.write", "extension.execute", "extension.admin",
                    "config.read", "config.write", "config.admin"
                ]
            },
            {
                "name": "extension_manager",
                "description": "Manager of extensions",
                "permissions": [
                    "extension.read", "extension.write", "extension.execute",
                    "config.read", "config.write"
                ],
                "parent_roles": ["extension_user"]
            },
            {
                "name": "extension_user",
                "description": "User of extensions",
                "permissions": [
                    "extension.read", "extension.execute",
                    "config.read"
                ]
            },
            {
                "name": "config_manager",
                "description": "Manager of configuration",
                "permissions": [
                    "config.read", "config.write"
                ],
                "parent_roles": ["config_user"]
            },
            {
                "name": "config_user",
                "description": "User of configuration",
                "permissions": [
                    "config.read"
                ]
            },
            {
                "name": "guest",
                "description": "Guest with read-only access",
                "permissions": [
                    "extension.read", "config.read"
                ]
            }
        ]
        
        # Create default roles
        for role_def in default_roles:
            await self.create_role(
                role_def["name"],
                role_def["description"],
                role_def.get("permissions", []),
                role_def.get("parent_roles", [])
            )