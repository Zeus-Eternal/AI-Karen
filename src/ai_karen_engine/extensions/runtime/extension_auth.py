"""
Extension Auth Service

This service handles authentication and authorization for extensions in the AI Karen system,
providing secure access control to extension functionality.
"""

import asyncio
import hashlib
import logging
import secrets
import time
from typing import Any, Dict, List, Optional, Union

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus


class ExtensionAuth(BaseService):
    """
    Extension Auth service for handling extension authentication and authorization.
    
    This service provides capabilities for authenticating extensions, managing
    their permissions, and enforcing access control.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="extension_auth"))
        self._initialized = False
        self._extension_tokens: Dict[str, str] = {}  # extension_id -> token
        self._extension_permissions: Dict[str, Dict[str, List[str]]] = {}  # extension_id -> {resource -> permissions}
        self._extension_roles: Dict[str, List[str]] = {}  # extension_id -> roles
        self._role_permissions: Dict[str, Dict[str, List[str]]] = {}  # role -> {resource -> permissions}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """Initialize the Extension Auth service."""
        try:
            self.logger.info("Initializing Extension Auth service")
            
            # Initialize default roles and permissions
            await self._initialize_roles_and_permissions()
            
            self._initialized = True
            self._status = ServiceStatus.RUNNING
            self.logger.info("Extension Auth service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Extension Auth service: {e}")
            self._status = ServiceStatus.ERROR
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown the Extension Auth service."""
        try:
            self.logger.info("Shutting down Extension Auth service")
            
            async with self._lock:
                self._extension_tokens.clear()
                self._extension_permissions.clear()
                self._extension_roles.clear()
                self._role_permissions.clear()
            
            self._initialized = False
            self._status = ServiceStatus.STOPPED
            self.logger.info("Extension Auth service shutdown successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to shutdown Extension Auth service: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check the health of the Extension Auth service."""
        return self._initialized and self._status == ServiceStatus.RUNNING
    
    async def register_extension(
        self,
        extension_id: str,
        roles: Optional[List[str]] = None,
        permissions: Optional[Dict[str, List[str]]] = None
    ) -> Optional[str]:
        """
        Register an extension and generate an authentication token for it.
        
        Args:
            extension_id: The ID of the extension
            roles: Optional list of roles to assign to the extension
            permissions: Optional dictionary of resource permissions to assign to the extension
            
        Returns:
            The authentication token or None if registration failed
        """
        if not self._initialized:
            raise RuntimeError("Extension Auth service is not initialized")
        
        async with self._lock:
            if extension_id in self._extension_tokens:
                self.logger.warning(f"Extension {extension_id} is already registered")
                return self._extension_tokens[extension_id]
            
            # Generate a secure token
            token = secrets.token_urlsafe(32)
            
            # Store the token
            self._extension_tokens[extension_id] = token
            
            # Assign default roles if none provided
            if roles is None:
                roles = ["extension"]
            
            # Assign the roles
            self._extension_roles[extension_id] = roles.copy()
            
            # Assign permissions
            if permissions is None:
                permissions = {}
            
            # Merge role permissions with direct permissions
            merged_permissions = permissions.copy()
            for role in roles:
                if role in self._role_permissions:
                    for resource, perms in self._role_permissions[role].items():
                        if resource not in merged_permissions:
                            merged_permissions[resource] = []
                        merged_permissions[resource].extend(perms)
                        # Remove duplicates
                        merged_permissions[resource] = list(set(merged_permissions[resource]))
            
            self._extension_permissions[extension_id] = merged_permissions
        
        self.logger.info(f"Extension {extension_id} registered successfully")
        return token
    
    async def unregister_extension(self, extension_id: str) -> bool:
        """
        Unregister an extension and revoke its authentication token.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            True if the extension was unregistered successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Auth service is not initialized")
        
        async with self._lock:
            if extension_id not in self._extension_tokens:
                self.logger.warning(f"Extension {extension_id} is not registered")
                return False
            
            # Remove the token, permissions, and roles
            del self._extension_tokens[extension_id]
            del self._extension_permissions[extension_id]
            del self._extension_roles[extension_id]
        
        self.logger.info(f"Extension {extension_id} unregistered successfully")
        return True
    
    async def authenticate_extension(self, extension_id: str, token: str) -> bool:
        """
        Authenticate an extension using its ID and token.
        
        Args:
            extension_id: The ID of the extension
            token: The authentication token
            
        Returns:
            True if the extension is authenticated, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Auth service is not initialized")
        
        async with self._lock:
            if extension_id not in self._extension_tokens:
                return False
            
            # Check if the token matches
            return self._extension_tokens[extension_id] == token
    
    async def check_permission(
        self,
        extension_id: str,
        resource: str,
        permission: str
    ) -> bool:
        """
        Check if an extension has a specific permission for a resource.
        
        Args:
            extension_id: The ID of the extension
            resource: The resource to check
            permission: The permission to check
            
        Returns:
            True if the extension has the permission, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Auth service is not initialized")
        
        async with self._lock:
            if extension_id not in self._extension_permissions:
                return False
            
            # Check if the extension has the permission for the resource
            if resource in self._extension_permissions[extension_id]:
                return permission in self._extension_permissions[extension_id][resource]
            
            return False
    
    async def get_extension_permissions(self, extension_id: str) -> Optional[Dict[str, List[str]]]:
        """
        Get the permissions of an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            The extension permissions or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension Auth service is not initialized")
        
        async with self._lock:
            if extension_id in self._extension_permissions:
                return self._extension_permissions[extension_id].copy()
            else:
                return None
    
    async def get_extension_roles(self, extension_id: str) -> Optional[List[str]]:
        """
        Get the roles of an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            The extension roles or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension Auth service is not initialized")
        
        async with self._lock:
            if extension_id in self._extension_roles:
                return self._extension_roles[extension_id].copy()
            else:
                return None
    
    async def add_extension_role(self, extension_id: str, role: str) -> bool:
        """
        Add a role to an extension.
        
        Args:
            extension_id: The ID of the extension
            role: The role to add
            
        Returns:
            True if the role was added successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Auth service is not initialized")
        
        async with self._lock:
            if extension_id not in self._extension_roles:
                self.logger.warning(f"Extension {extension_id} is not registered")
                return False
            
            if role not in self._role_permissions:
                self.logger.warning(f"Role {role} does not exist")
                return False
            
            if role not in self._extension_roles[extension_id]:
                self._extension_roles[extension_id].append(role)
                
                # Update permissions
                for resource, perms in self._role_permissions[role].items():
                    if resource not in self._extension_permissions[extension_id]:
                        self._extension_permissions[extension_id][resource] = []
                    self._extension_permissions[extension_id][resource].extend(perms)
                    # Remove duplicates
                    self._extension_permissions[extension_id][resource] = list(set(
                        self._extension_permissions[extension_id][resource]
                    ))
        
        self.logger.info(f"Role {role} added to extension {extension_id}")
        return True
    
    async def remove_extension_role(self, extension_id: str, role: str) -> bool:
        """
        Remove a role from an extension.
        
        Args:
            extension_id: The ID of the extension
            role: The role to remove
            
        Returns:
            True if the role was removed successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Auth service is not initialized")
        
        async with self._lock:
            if extension_id not in self._extension_roles:
                self.logger.warning(f"Extension {extension_id} is not registered")
                return False
            
            if role in self._extension_roles[extension_id]:
                self._extension_roles[extension_id].remove(role)
                
                # Update permissions
                for resource, perms in self._role_permissions[role].items():
                    if resource in self._extension_permissions[extension_id]:
                        # Remove permissions from this role
                        for perm in perms:
                            if perm in self._extension_permissions[extension_id][resource]:
                                self._extension_permissions[extension_id][resource].remove(perm)
                        
                        # Remove the resource if no permissions left
                        if not self._extension_permissions[extension_id][resource]:
                            del self._extension_permissions[extension_id][resource]
        
        self.logger.info(f"Role {role} removed from extension {extension_id}")
        return True
    
    async def add_extension_permission(
        self,
        extension_id: str,
        resource: str,
        permission: str
    ) -> bool:
        """
        Add a permission to an extension.
        
        Args:
            extension_id: The ID of the extension
            resource: The resource to add the permission for
            permission: The permission to add
            
        Returns:
            True if the permission was added successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Auth service is not initialized")
        
        async with self._lock:
            if extension_id not in self._extension_permissions:
                self.logger.warning(f"Extension {extension_id} is not registered")
                return False
            
            if resource not in self._extension_permissions[extension_id]:
                self._extension_permissions[extension_id][resource] = []
            
            if permission not in self._extension_permissions[extension_id][resource]:
                self._extension_permissions[extension_id][resource].append(permission)
        
        self.logger.info(f"Permission {permission} for resource {resource} added to extension {extension_id}")
        return True
    
    async def remove_extension_permission(
        self,
        extension_id: str,
        resource: str,
        permission: str
    ) -> bool:
        """
        Remove a permission from an extension.
        
        Args:
            extension_id: The ID of the extension
            resource: The resource to remove the permission for
            permission: The permission to remove
            
        Returns:
            True if the permission was removed successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Auth service is not initialized")
        
        async with self._lock:
            if extension_id not in self._extension_permissions:
                self.logger.warning(f"Extension {extension_id} is not registered")
                return False
            
            if resource in self._extension_permissions[extension_id]:
                if permission in self._extension_permissions[extension_id][resource]:
                    self._extension_permissions[extension_id][resource].remove(permission)
                    
                    # Remove the resource if no permissions left
                    if not self._extension_permissions[extension_id][resource]:
                        del self._extension_permissions[extension_id][resource]
        
        self.logger.info(f"Permission {permission} for resource {resource} removed from extension {extension_id}")
        return True
    
    async def create_role(
        self,
        role: str,
        permissions: Dict[str, List[str]]
    ) -> bool:
        """
        Create a new role with permissions.
        
        Args:
            role: The name of the role
            permissions: The permissions for the role
            
        Returns:
            True if the role was created successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Auth service is not initialized")
        
        async with self._lock:
            if role in self._role_permissions:
                self.logger.warning(f"Role {role} already exists")
                return False
            
            self._role_permissions[role] = permissions.copy()
        
        self.logger.info(f"Role {role} created successfully")
        return True
    
    async def delete_role(self, role: str) -> bool:
        """
        Delete a role.
        
        Args:
            role: The name of the role
            
        Returns:
            True if the role was deleted successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Auth service is not initialized")
        
        async with self._lock:
            if role not in self._role_permissions:
                self.logger.warning(f"Role {role} does not exist")
                return False
            
            # Remove the role from all extensions
            for extension_id, roles in self._extension_roles.items():
                if role in roles:
                    roles.remove(role)
            
            # Delete the role
            del self._role_permissions[role]
        
        self.logger.info(f"Role {role} deleted successfully")
        return True
    
    async def get_role_permissions(self, role: str) -> Optional[Dict[str, List[str]]]:
        """
        Get the permissions of a role.
        
        Args:
            role: The name of the role
            
        Returns:
            The role permissions or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension Auth service is not initialized")
        
        async with self._lock:
            if role in self._role_permissions:
                return self._role_permissions[role].copy()
            else:
                return None
    
    async def get_all_roles(self) -> List[str]:
        """
        Get all available roles.
        
        Returns:
            List of role names
        """
        if not self._initialized:
            raise RuntimeError("Extension Auth service is not initialized")
        
        async with self._lock:
            return list(self._role_permissions.keys())
    
    async def _initialize_roles_and_permissions(self) -> None:
        """Initialize default roles and permissions."""
        # Define default roles and their permissions
        default_roles = {
            "admin": {
                "extensions": ["create", "read", "update", "delete"],
                "config": ["read", "write"],
                "auth": ["manage"],
                "system": ["admin"]
            },
            "extension": {
                "extensions": ["read"],
                "config": ["read"],
                "system": ["basic"]
            },
            "guest": {
                "extensions": ["read"],
                "system": ["basic"]
            }
        }
        
        for role, permissions in default_roles.items():
            self._role_permissions[role] = permissions