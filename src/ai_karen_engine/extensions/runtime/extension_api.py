"""
Extension API Service

This service provides an API for extensions to interact with the AI Karen system,
offering a standardized interface for extension functionality.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus


class ExtensionApi(BaseService):
    """
    Extension API service for providing API to extensions.
    
    This service provides capabilities for extensions to interact with the AI Karen system
    through a standardized API interface.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="extension_api"))
        self._initialized = False
        self._api_endpoints: Dict[str, Dict[str, Any]] = {}  # endpoint_name -> endpoint_info
        self._api_versions: Dict[str, Dict[str, Any]] = {}  # version -> version_info
        self._extension_handlers: Dict[str, Any] = {}  # extension_id -> handler
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """Initialize the Extension API service."""
        try:
            self.logger.info("Initializing Extension API service")
            
            # Initialize API endpoints
            await self._initialize_api_endpoints()
            
            # Initialize API versions
            await self._initialize_api_versions()
            
            self._initialized = True
            self._status = ServiceStatus.RUNNING
            self.logger.info("Extension API service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Extension API service: {e}")
            self._status = ServiceStatus.ERROR
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown the Extension API service."""
        try:
            self.logger.info("Shutting down Extension API service")
            
            async with self._lock:
                self._api_endpoints.clear()
                self._api_versions.clear()
                self._extension_handlers.clear()
            
            self._initialized = False
            self._status = ServiceStatus.STOPPED
            self.logger.info("Extension API service shutdown successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to shutdown Extension API service: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check the health of the Extension API service."""
        return self._initialized and self._status == ServiceStatus.RUNNING
    
    async def register_api_endpoint(
        self,
        extension_id: str,
        endpoint_name: str,
        handler: Any,
        methods: Optional[List[str]] = None,
        path: Optional[str] = None,
        version: str = "v1"
    ) -> bool:
        """
        Register an API endpoint for an extension.
        
        Args:
            extension_id: The ID of the extension
            endpoint_name: The name of the endpoint
            handler: The handler function for the endpoint
            methods: Optional list of HTTP methods (GET, POST, etc.)
            path: Optional path for the endpoint
            version: Optional API version
            
        Returns:
            True if the endpoint was registered successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension API service is not initialized")
        
        if methods is None:
            methods = ["GET"]
        
        if path is None:
            path = f"/api/extensions/{extension_id}/{endpoint_name}"
        
        endpoint_id = f"{extension_id}:{endpoint_name}:{version}"
        
        async with self._lock:
            if endpoint_id in self._api_endpoints:
                self.logger.warning(f"API endpoint {endpoint_id} is already registered")
                return False
            
            # Register the endpoint
            self._api_endpoints[endpoint_id] = {
                "extension_id": extension_id,
                "endpoint_name": endpoint_name,
                "handler": handler,
                "methods": methods,
                "path": path,
                "version": version,
                "registered_at": asyncio.get_event_loop().time()
            }
            
            # Store the extension handler
            self._extension_handlers[extension_id] = handler
        
        self.logger.info(f"API endpoint {endpoint_id} registered successfully")
        return True
    
    async def unregister_api_endpoint(
        self,
        extension_id: str,
        endpoint_name: str,
        version: str = "v1"
    ) -> bool:
        """
        Unregister an API endpoint for an extension.
        
        Args:
            extension_id: The ID of the extension
            endpoint_name: The name of the endpoint
            version: Optional API version
            
        Returns:
            True if the endpoint was unregistered successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension API service is not initialized")
        
        endpoint_id = f"{extension_id}:{endpoint_name}:{version}"
        
        async with self._lock:
            if endpoint_id not in self._api_endpoints:
                self.logger.warning(f"API endpoint {endpoint_id} is not registered")
                return False
            
            # Unregister the endpoint
            del self._api_endpoints[endpoint_id]
            
            # Remove the extension handler if no more endpoints
            has_other_endpoints = any(
                ep_id.startswith(f"{extension_id}:") and ep_id != endpoint_id
                for ep_id in self._api_endpoints
            )
            
            if not has_other_endpoints and extension_id in self._extension_handlers:
                del self._extension_handlers[extension_id]
        
        self.logger.info(f"API endpoint {endpoint_id} unregistered successfully")
        return True
    
    async def get_api_endpoints(
        self,
        extension_id: Optional[str] = None,
        version: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get API endpoints.
        
        Args:
            extension_id: Optional extension ID to filter by
            version: Optional API version to filter by
            
        Returns:
            Dictionary mapping endpoint IDs to endpoint information
        """
        if not self._initialized:
            raise RuntimeError("Extension API service is not initialized")
        
        async with self._lock:
            result = {}
            
            for ep_id, ep_info in self._api_endpoints.items():
                # Filter by extension ID
                if extension_id and ep_info.get("extension_id") != extension_id:
                    continue
                
                # Filter by version
                if version and ep_info.get("version") != version:
                    continue
                
                result[ep_id] = ep_info.copy()
            
            return result
    
    async def get_api_endpoint(
        self,
        extension_id: str,
        endpoint_name: str,
        version: str = "v1"
    ) -> Optional[Dict[str, Any]]:
        """
        Get an API endpoint.
        
        Args:
            extension_id: The ID of the extension
            endpoint_name: The name of the endpoint
            version: Optional API version
            
        Returns:
            The endpoint information or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension API service is not initialized")
        
        endpoint_id = f"{extension_id}:{endpoint_name}:{version}"
        
        async with self._lock:
            if endpoint_id in self._api_endpoints:
                return self._api_endpoints[endpoint_id].copy()
            else:
                return None
    
    async def call_api_endpoint(
        self,
        extension_id: str,
        endpoint_name: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        version: str = "v1"
    ) -> Any:
        """
        Call an API endpoint.
        
        Args:
            extension_id: The ID of the extension
            endpoint_name: The name of the endpoint
            method: The HTTP method to use
            data: Optional data to send with the request
            params: Optional query parameters
            version: Optional API version
            
        Returns:
            The result of the API call
        """
        if not self._initialized:
            raise RuntimeError("Extension API service is not initialized")
        
        endpoint_id = f"{extension_id}:{endpoint_name}:{version}"
        
        async with self._lock:
            if endpoint_id not in self._api_endpoints:
                raise ValueError(f"API endpoint {endpoint_id} is not registered")
            
            ep_info = self._api_endpoints[endpoint_id]
            
            # Check if the method is supported
            if method not in ep_info.get("methods", []):
                raise ValueError(f"Method {method} is not supported by endpoint {endpoint_id}")
            
            # Get the handler
            handler = ep_info.get("handler")
            if not handler:
                raise ValueError(f"No handler found for endpoint {endpoint_id}")
            
            # Call the handler
            try:
                if hasattr(handler, "__call__"):
                    # It's a callable function
                    if asyncio.iscoroutinefunction(handler):
                        # It's an async function
                        return await handler(method=method, data=data, params=params)
                    else:
                        # It's a sync function
                        return handler(method=method, data=data, params=params)
                else:
                    # It's not a callable, try to find a method matching the HTTP method
                    method_name = method.lower()
                    if hasattr(handler, method_name):
                        method_handler = getattr(handler, method_name)
                        if asyncio.iscoroutinefunction(method_handler):
                            return await method_handler(data=data, params=params)
                        else:
                            return method_handler(data=data, params=params)
                    else:
                        raise ValueError(f"Handler for endpoint {endpoint_id} does not support method {method}")
            except Exception as e:
                self.logger.error(f"Error calling API endpoint {endpoint_id}: {e}")
                raise
    
    async def get_api_versions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all API versions.
        
        Returns:
            Dictionary mapping version names to version information
        """
        if not self._initialized:
            raise RuntimeError("Extension API service is not initialized")
        
        async with self._lock:
            return self._api_versions.copy()
    
    async def get_api_version(self, version: str) -> Optional[Dict[str, Any]]:
        """
        Get an API version.
        
        Args:
            version: The version name
            
        Returns:
            The version information or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension API service is not initialized")
        
        async with self._lock:
            if version in self._api_versions:
                return self._api_versions[version].copy()
            else:
                return None
    
    async def add_api_version(
        self,
        version: str,
        description: str,
        status: str = "active"
    ) -> bool:
        """
        Add an API version.
        
        Args:
            version: The version name
            description: A description of the version
            status: The status of the version (active, deprecated, etc.)
            
        Returns:
            True if the version was added successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension API service is not initialized")
        
        async with self._lock:
            if version in self._api_versions:
                self.logger.warning(f"API version {version} already exists")
                return False
            
            # Add the version
            self._api_versions[version] = {
                "description": description,
                "status": status,
                "added_at": asyncio.get_event_loop().time()
            }
        
        self.logger.info(f"API version {version} added successfully")
        return True
    
    async def remove_api_version(self, version: str) -> bool:
        """
        Remove an API version.
        
        Args:
            version: The version name
            
        Returns:
            True if the version was removed successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension API service is not initialized")
        
        async with self._lock:
            if version not in self._api_versions:
                self.logger.warning(f"API version {version} does not exist")
                return False
            
            # Check if there are any endpoints using this version
            endpoints_with_version = [
                ep_id for ep_id, ep_info in self._api_endpoints.items()
                if ep_info.get("version") == version
            ]
            
            if endpoints_with_version:
                self.logger.error(f"Cannot remove API version {version}: it is being used by endpoints")
                return False
            
            # Remove the version
            del self._api_versions[version]
        
        self.logger.info(f"API version {version} removed successfully")
        return True
    
    async def _initialize_api_endpoints(self) -> None:
        """Initialize default API endpoints."""
        # This is a placeholder for initializing default API endpoints
        # In a real implementation, this would register default endpoints
        pass
    
    async def _initialize_api_versions(self) -> None:
        """Initialize default API versions."""
        # Add default API versions
        await self.add_api_version(
            "v1",
            "Initial version of the Extension API",
            "active"
        )