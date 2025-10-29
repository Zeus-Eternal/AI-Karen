"""
FastAPI integration for extensions.

This module provides the core FastAPI integration functionality for the extension system,
including router registration, endpoint discovery, authentication, and documentation generation.
"""

import logging
from typing import Dict, List, Optional, Any, Callable, Set
from pathlib import Path
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.models import OpenAPI
import inspect
import asyncio

from .models import (
    ExtensionManifest, 
    ExtensionRecord, 
    ExtensionAPIRoute, 
    ExtensionAPIEndpoint,
    ExtensionStatus
)

logger = logging.getLogger(__name__)


class ExtensionAPIIntegration:
    """
    Manages FastAPI integration for extensions.
    
    Handles router registration, endpoint discovery, authentication,
    and API documentation generation for extension endpoints.
    """
    
    def __init__(self, app: FastAPI):
        """Initialize the extension API integration."""
        self.app = app
        self.registered_routes: Dict[str, List[ExtensionAPIRoute]] = {}
        self.extension_routers: Dict[str, APIRouter] = {}
        self.auth_dependencies: Dict[str, Callable] = {}
        self.security = HTTPBearer(auto_error=False)
        
        # Track registered extensions for documentation
        self.registered_extensions: Dict[str, ExtensionRecord] = {}
        
        logger.info("Extension API integration initialized")
    
    async def register_extension_api(
        self, 
        extension_record: ExtensionRecord
    ) -> bool:
        """
        Register an extension's API endpoints with FastAPI.
        
        Args:
            extension_record: The extension record containing manifest and instance
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            extension_name = extension_record.manifest.name
            logger.info(f"Registering API for extension: {extension_name}")
            
            # Check if extension provides API
            if not extension_record.manifest.capabilities.provides_api:
                logger.debug(f"Extension {extension_name} does not provide API")
                return True
            
            # Get the extension instance
            if not extension_record.instance:
                logger.error(f"Extension {extension_name} has no instance")
                return False
            
            # Get the API router from the extension
            router = await self._get_extension_router(extension_record)
            if not router:
                logger.warning(f"Extension {extension_name} did not provide API router")
                return True
            
            # Configure router with extension-specific settings
            await self._configure_extension_router(extension_record, router)
            
            # Register the router with FastAPI
            await self._mount_extension_router(extension_record, router)
            
            # Update documentation
            await self._update_api_documentation(extension_record)
            
            # Track the registration
            self.registered_extensions[extension_name] = extension_record
            
            logger.info(f"Successfully registered API for extension: {extension_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register API for extension {extension_record.manifest.name}: {e}")
            return False
    
    async def unregister_extension_api(self, extension_name: str) -> bool:
        """
        Unregister an extension's API endpoints.
        
        Args:
            extension_name: Name of the extension to unregister
            
        Returns:
            bool: True if unregistration successful, False otherwise
        """
        try:
            logger.info(f"Unregistering API for extension: {extension_name}")
            
            # Remove from registered routes
            if extension_name in self.registered_routes:
                del self.registered_routes[extension_name]
            
            # Remove router
            if extension_name in self.extension_routers:
                del self.extension_routers[extension_name]
            
            # Remove from registered extensions
            if extension_name in self.registered_extensions:
                del self.registered_extensions[extension_name]
            
            # Update documentation
            await self._regenerate_api_documentation()
            
            logger.info(f"Successfully unregistered API for extension: {extension_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister API for extension {extension_name}: {e}")
            return False
    
    async def _get_extension_router(self, extension_record: ExtensionRecord) -> Optional[APIRouter]:
        """Get the API router from an extension instance."""
        try:
            instance = extension_record.instance
            
            # Try to get router from extension
            if hasattr(instance, 'create_api_router'):
                router = instance.create_api_router()
                if router and isinstance(router, APIRouter):
                    return router
            
            # Try alternative method names
            for method_name in ['get_api_router', 'get_router', 'create_router']:
                if hasattr(instance, method_name):
                    method = getattr(instance, method_name)
                    if callable(method):
                        router = method()
                        if router and isinstance(router, APIRouter):
                            return router
            
            logger.debug(f"Extension {extension_record.manifest.name} has no API router method")
            return None
            
        except Exception as e:
            logger.error(f"Error getting router from extension {extension_record.manifest.name}: {e}")
            return None
    
    async def _configure_extension_router(
        self, 
        extension_record: ExtensionRecord, 
        router: APIRouter
    ) -> None:
        """Configure an extension router with authentication and metadata."""
        try:
            manifest = extension_record.manifest
            extension_name = manifest.name
            
            # Set router prefix if not already set
            if not router.prefix:
                api_prefix = manifest.api.prefix or f"/api/extensions/{extension_name}"
                router.prefix = api_prefix
            
            # Add extension tags if not already set
            if not router.tags:
                router.tags = manifest.api.tags or [f"extension-{extension_name}"]
            
            # Add authentication dependencies to routes that need them
            await self._add_authentication_to_routes(extension_record, router)
            
            # Validate routes against manifest
            await self._validate_routes_against_manifest(extension_record, router)
            
        except Exception as e:
            logger.error(f"Error configuring router for extension {extension_record.manifest.name}: {e}")
            raise
    
    async def _add_authentication_to_routes(
        self, 
        extension_record: ExtensionRecord, 
        router: APIRouter
    ) -> None:
        """Add authentication dependencies to extension routes."""
        try:
            manifest = extension_record.manifest
            extension_name = manifest.name
            
            # Create extension-specific auth dependency
            auth_dependency = self._create_extension_auth_dependency(extension_record)
            
            # Add auth to routes that require permissions
            for route in router.routes:
                if hasattr(route, 'endpoint') and hasattr(route, 'path'):
                    # Find matching endpoint in manifest
                    endpoint_config = self._find_endpoint_config(manifest, route.path, route.methods)
                    
                    if endpoint_config and endpoint_config.permissions:
                        # Add auth dependency to route
                        if hasattr(route, 'dependencies'):
                            route.dependencies.append(Depends(auth_dependency))
                        else:
                            # For routes without existing dependencies
                            original_endpoint = route.endpoint
                            
                            async def authenticated_endpoint(*args, **kwargs):
                                # Auth dependency will be called automatically by FastAPI
                                return await original_endpoint(*args, **kwargs)
                            
                            route.endpoint = authenticated_endpoint
            
            logger.debug(f"Added authentication to routes for extension: {extension_name}")
            
        except Exception as e:
            logger.error(f"Error adding authentication to extension {extension_record.manifest.name}: {e}")
            raise
    
    def _create_extension_auth_dependency(self, extension_record: ExtensionRecord) -> Callable:
        """Create an authentication dependency for an extension."""
        manifest = extension_record.manifest
        extension_name = manifest.name
        required_permissions = manifest.permissions
        
        async def extension_auth_dependency(
            request: Request,
            credentials: Optional[HTTPAuthorizationCredentials] = Depends(self.security)
        ) -> Dict[str, Any]:
            """Authentication dependency for extension endpoints."""
            try:
                # Try to get user from request state (set by global auth middleware)
                user_data = getattr(request.state, 'user', None)
                
                if not user_data:
                    # Try to authenticate using credentials
                    if credentials:
                        user_data = await self._authenticate_with_token(credentials.credentials)
                    
                    if not user_data:
                        raise HTTPException(
                            status_code=401,
                            detail=f"Authentication required for extension {extension_name}"
                        )
                
                # Check extension-specific permissions
                await self._check_extension_permissions(
                    user_data, 
                    extension_name, 
                    required_permissions
                )
                
                return user_data
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Authentication error for extension {extension_name}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Authentication service error"
                )
        
        return extension_auth_dependency
    
    async def _authenticate_with_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user with a token."""
        try:
            # Try to import and use the auth service
            try:
                from src.auth.auth_service import AuthService
                auth_service = AuthService()
                user_data = await auth_service.verify_token(token)
                return user_data
            except ImportError:
                logger.warning("Auth service not available for token authentication")
                return None
                
        except Exception as e:
            logger.error(f"Token authentication error: {e}")
            return None
    
    async def _check_extension_permissions(
        self, 
        user_data: Dict[str, Any], 
        extension_name: str,
        required_permissions: Any
    ) -> None:
        """Check if user has required permissions for extension."""
        try:
            # Basic permission checking - can be extended
            user_roles = user_data.get('roles', [])
            
            # Admin users have access to all extensions
            if 'admin' in user_roles:
                return
            
            # Check specific permissions if needed
            # This is a simplified implementation - extend as needed
            if hasattr(required_permissions, 'data_access'):
                if 'admin' in required_permissions.data_access and 'admin' not in user_roles:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Admin access required for extension {extension_name}"
                    )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Permission check error for extension {extension_name}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Permission check error"
            )
    
    def _find_endpoint_config(
        self, 
        manifest: ExtensionManifest, 
        path: str, 
        methods: Set[str]
    ) -> Optional[ExtensionAPIEndpoint]:
        """Find endpoint configuration in manifest."""
        try:
            for endpoint in manifest.api.endpoints:
                if endpoint.path in path and any(method.upper() in methods for method in endpoint.methods):
                    return endpoint
            return None
        except Exception:
            return None
    
    async def _validate_routes_against_manifest(
        self, 
        extension_record: ExtensionRecord, 
        router: APIRouter
    ) -> None:
        """Validate that router routes match manifest declarations."""
        try:
            manifest = extension_record.manifest
            extension_name = manifest.name
            
            # Get declared endpoints from manifest
            declared_endpoints = {ep.path: ep for ep in manifest.api.endpoints}
            
            # Get actual routes from router
            actual_routes = []
            for route in router.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    actual_routes.append({
                        'path': route.path,
                        'methods': route.methods
                    })
            
            # Log validation results
            logger.debug(f"Extension {extension_name} declared {len(declared_endpoints)} endpoints")
            logger.debug(f"Extension {extension_name} router has {len(actual_routes)} routes")
            
            # Store route information for tracking
            extension_routes = []
            for route in router.routes:
                if hasattr(route, 'path') and hasattr(route, 'endpoint'):
                    extension_route = ExtensionAPIRoute(
                        extension_name=extension_name,
                        path=route.path,
                        methods=list(route.methods) if hasattr(route, 'methods') else ['GET'],
                        handler=route.endpoint,
                        permissions=[],  # Will be populated from manifest
                        description=getattr(route, 'description', None),
                        tags=router.tags or []
                    )
                    extension_routes.append(extension_route)
            
            self.registered_routes[extension_name] = extension_routes
            
        except Exception as e:
            logger.error(f"Route validation error for extension {extension_record.manifest.name}: {e}")
            # Don't raise - validation errors shouldn't prevent registration
    
    async def _mount_extension_router(
        self, 
        extension_record: ExtensionRecord, 
        router: APIRouter
    ) -> None:
        """Mount the extension router to the FastAPI app."""
        try:
            extension_name = extension_record.manifest.name
            
            # Include the router in the FastAPI app
            self.app.include_router(
                router,
                tags=router.tags or [f"extension-{extension_name}"]
            )
            
            # Store the router for later reference
            self.extension_routers[extension_name] = router
            
            logger.info(f"Mounted router for extension {extension_name} with prefix {router.prefix}")
            
        except Exception as e:
            logger.error(f"Error mounting router for extension {extension_record.manifest.name}: {e}")
            raise
    
    async def _update_api_documentation(self, extension_record: ExtensionRecord) -> None:
        """Update API documentation to include extension endpoints."""
        try:
            extension_name = extension_record.manifest.name
            
            # The OpenAPI schema will be automatically updated by FastAPI
            # when we include the router. We can add custom metadata here.
            
            # Add extension information to app metadata
            if not hasattr(self.app, 'extension_metadata'):
                self.app.extension_metadata = {}
            
            self.app.extension_metadata[extension_name] = {
                'display_name': extension_record.manifest.display_name,
                'description': extension_record.manifest.description,
                'version': extension_record.manifest.version,
                'author': extension_record.manifest.author,
                'category': extension_record.manifest.category,
                'endpoints': len(extension_record.manifest.api.endpoints)
            }
            
            logger.debug(f"Updated API documentation for extension: {extension_name}")
            
        except Exception as e:
            logger.error(f"Error updating documentation for extension {extension_record.manifest.name}: {e}")
            # Don't raise - documentation errors shouldn't prevent registration
    
    async def _regenerate_api_documentation(self) -> None:
        """Regenerate API documentation after extension changes."""
        try:
            # FastAPI automatically regenerates OpenAPI schema
            # We just need to clean up our metadata
            
            if hasattr(self.app, 'extension_metadata'):
                # Remove metadata for unregistered extensions
                registered_names = set(self.registered_extensions.keys())
                metadata_names = set(self.app.extension_metadata.keys())
                
                for name in metadata_names - registered_names:
                    del self.app.extension_metadata[name]
            
            logger.debug("Regenerated API documentation")
            
        except Exception as e:
            logger.error(f"Error regenerating API documentation: {e}")
    
    def get_extension_routes(self, extension_name: str) -> List[ExtensionAPIRoute]:
        """Get registered routes for an extension."""
        return self.registered_routes.get(extension_name, [])
    
    def get_all_extension_routes(self) -> Dict[str, List[ExtensionAPIRoute]]:
        """Get all registered extension routes."""
        return self.registered_routes.copy()
    
    def get_extension_router(self, extension_name: str) -> Optional[APIRouter]:
        """Get the router for a specific extension."""
        return self.extension_routers.get(extension_name)
    
    def is_extension_registered(self, extension_name: str) -> bool:
        """Check if an extension's API is registered."""
        return extension_name in self.registered_extensions
    
    def get_registered_extensions(self) -> Dict[str, ExtensionRecord]:
        """Get all registered extensions."""
        return self.registered_extensions.copy()
    
    async def generate_extension_openapi_schema(self) -> Dict[str, Any]:
        """Generate OpenAPI schema including extension endpoints."""
        try:
            # Get the base OpenAPI schema
            openapi_schema = get_openapi(
                title=self.app.title,
                version=self.app.version,
                description=self.app.description,
                routes=self.app.routes,
            )
            
            # Add extension metadata
            if hasattr(self.app, 'extension_metadata'):
                openapi_schema['x-extensions'] = self.app.extension_metadata
            
            return openapi_schema
            
        except Exception as e:
            logger.error(f"Error generating extension OpenAPI schema: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the API integration system."""
        try:
            return {
                'status': 'healthy',
                'registered_extensions': len(self.registered_extensions),
                'total_routes': sum(len(routes) for routes in self.registered_routes.values()),
                'active_routers': len(self.extension_routers)
            }
        except Exception as e:
            logger.error(f"API integration health check error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }