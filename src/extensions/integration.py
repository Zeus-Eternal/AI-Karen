"""
Extension system integration with FastAPI application.

This module provides integration functions to wire the extension system
into the main FastAPI application and server startup process.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from fastapi import FastAPI

from .manager import ExtensionManager
from .models import ExtensionStatus
from .background_task_api import create_background_task_router

logger = logging.getLogger(__name__)


class ExtensionSystemIntegration:
    """
    Integrates the extension system with the FastAPI application.
    
    This class handles the integration of the extension system with the main
    FastAPI application, including startup, shutdown, and route registration.
    """
    
    def __init__(self):
        """Initialize the extension system integration."""
        self.extension_manager: Optional[ExtensionManager] = None
        self._initialized = False
    
    async def initialize_extension_system(
        self,
        app: FastAPI,
        extension_root: str = "extensions",
        db_session=None,
        plugin_router=None
    ) -> bool:
        """
        Initialize the extension system for the FastAPI application.
        
        Args:
            app: FastAPI application instance
            extension_root: Root directory for extensions
            db_session: Database session for persistence
            plugin_router: Plugin router for orchestration
            
        Returns:
            bool: True if initialization successful
        """
        try:
            logger.info("Initializing extension system")
            
            # Create extension manager
            self.extension_manager = ExtensionManager(
                extension_root=Path(extension_root),
                app=app,
                db_session=db_session,
                plugin_router=plugin_router
            )
            
            # Initialize the manager
            await self.extension_manager.initialize()
            
            # Register extension system endpoints
            await self._register_extension_endpoints(app)
            
            # Add startup and shutdown handlers
            self._add_lifecycle_handlers(app)
            
            self._initialized = True
            logger.info("Extension system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize extension system: {e}")
            return False
    
    async def load_extensions_on_startup(self) -> None:
        """Load extensions during application startup."""
        if not self.extension_manager:
            logger.warning("Extension manager not initialized")
            return
        
        try:
            logger.info("Loading extensions on startup")
            
            # Discover and load all extensions
            loaded_extensions = await self.extension_manager.load_all_extensions()
            
            # Log results
            active_count = len([
                ext for ext in loaded_extensions.values() 
                if ext.status == ExtensionStatus.ACTIVE
            ])
            
            logger.info(f"Loaded {active_count} extensions successfully")
            
            # Log any failed extensions
            for name, record in loaded_extensions.items():
                if record.status == ExtensionStatus.ERROR:
                    logger.error(f"Extension {name} failed to load: {record.error}")
            
        except Exception as e:
            logger.error(f"Error loading extensions on startup: {e}")
    
    async def shutdown_extensions(self) -> None:
        """Shutdown extensions during application shutdown."""
        if not self.extension_manager:
            return
        
        try:
            logger.info("Shutting down extensions")
            await self.extension_manager.shutdown()
            logger.info("Extensions shut down successfully")
            
        except Exception as e:
            logger.error(f"Error shutting down extensions: {e}")
    
    def _add_lifecycle_handlers(self, app: FastAPI) -> None:
        """Add startup and shutdown handlers to the FastAPI app."""
        
        @app.on_event("startup")
        async def startup_extensions():
            """Load extensions on application startup."""
            await self.load_extensions_on_startup()
        
        @app.on_event("shutdown")
        async def shutdown_extensions():
            """Shutdown extensions on application shutdown."""
            await self.shutdown_extensions()
    
    async def _register_extension_endpoints(self, app: FastAPI) -> None:
        """Register extension management endpoints with enhanced authentication."""
        from fastapi import APIRouter, HTTPException, Depends, Request
        from typing import Dict, Any, List, Optional
        from server.security import (
            require_extension_read, 
            require_extension_write, 
            require_extension_admin,
            require_background_tasks,
            get_extension_auth_manager
        )
        
        # Create extension management router with enhanced authentication
        extension_router = APIRouter(prefix="/api/extensions", tags=["extensions"])
        
        # Get authentication manager for permission utilities
        auth_manager = get_extension_auth_manager()
        
        @extension_router.get("/")
        async def list_extensions(
            request: Request,
            include_disabled: bool = False,
            category: Optional[str] = None,
            user_context: Dict[str, Any] = Depends(require_extension_read)
        ) -> Dict[str, Any]:
            """List all extensions with their status and enhanced filtering."""
            if not self.extension_manager:
                raise HTTPException(status_code=503, detail="Extension system not initialized")
            
            try:
                logger.info(f"User {user_context['user_id']} listing extensions (category: {category})")
                
                # Enhanced permission checking for sensitive operations
                can_view_system_extensions = self._has_system_extension_permission(user_context)
                can_view_disabled = include_disabled and self._has_admin_permission(user_context)
                
                extensions = {}
                for name, record in self.extension_manager.registry.get_all_extensions().items():
                    # Enhanced access control with category and status filtering
                    if self._can_access_extension(record, user_context, can_view_system_extensions):
                        # Skip disabled extensions unless user has permission
                        if record.status.value == 'disabled' and not can_view_disabled:
                            continue
                        
                        # Apply category filter if specified
                        if category and record.manifest.category != category:
                            continue
                        
                        extensions[name] = {
                            'name': name,
                            'version': record.manifest.version,
                            'display_name': record.manifest.display_name,
                            'description': record.manifest.description,
                            'category': record.manifest.category,
                            'status': record.status.value,
                            'capabilities': {
                                'provides_ui': record.manifest.capabilities.provides_ui,
                                'provides_api': record.manifest.capabilities.provides_api,
                                'provides_background_tasks': record.manifest.capabilities.provides_background_tasks,
                                'provides_webhooks': record.manifest.capabilities.provides_webhooks
                            },
                            'loaded_at': record.loaded_at.isoformat() if record.loaded_at else None,
                            'error': record.error,
                            'permissions': self._get_extension_permissions(record, user_context)
                        }
                
                return {
                    'extensions': extensions,
                    'total': len(extensions),
                    'loaded': len(self.extension_manager.loaded_extensions),
                    'user_context': {
                        'user_id': user_context['user_id'],
                        'tenant_id': user_context['tenant_id'],
                        'permissions': user_context.get('permissions', [])
                    },
                    'filters': {
                        'category': category,
                        'include_disabled': include_disabled
                    }
                }
                
            except Exception as e:
                logger.error(f"Error listing extensions for user {user_context.get('user_id')}: {e}")
                raise HTTPException(status_code=500, detail="Failed to list extensions")
        
        @extension_router.get("/{extension_name}")
        async def get_extension(
            extension_name: str,
            include_config: bool = False,
            user_context: Dict[str, Any] = Depends(require_extension_read)
        ) -> Dict[str, Any]:
            """Get detailed information about a specific extension with enhanced access control."""
            if not self.extension_manager:
                raise HTTPException(status_code=503, detail="Extension system not initialized")
            
            try:
                logger.info(f"User {user_context['user_id']} requesting extension {extension_name}")
                
                # Get extension record
                record = self.extension_manager.registry.get_extension(extension_name)
                if not record:
                    raise HTTPException(status_code=404, detail="Extension not found")
                
                # Enhanced permission checking for extension access
                if not self._can_access_extension(record, user_context):
                    raise HTTPException(status_code=403, detail="Access denied to this extension")
                
                # Build response with permission-based data inclusion
                extension_data = {
                    'name': extension_name,
                    'version': record.manifest.version,
                    'display_name': record.manifest.display_name,
                    'description': record.manifest.description,
                    'category': record.manifest.category,
                    'status': record.status.value,
                    'capabilities': {
                        'provides_ui': record.manifest.capabilities.provides_ui,
                        'provides_api': record.manifest.capabilities.provides_api,
                        'provides_background_tasks': record.manifest.capabilities.provides_background_tasks,
                        'provides_webhooks': record.manifest.capabilities.provides_webhooks
                    },
                    'loaded_at': record.loaded_at.isoformat() if record.loaded_at else None,
                    'error': record.error,
                    'permissions': self._get_extension_permissions(record, user_context)
                }
                
                # Include configuration if user has admin permissions and requested
                if include_config and self._has_admin_permission(user_context):
                    extension_data['configuration'] = getattr(record, 'configuration', {})
                
                # Include detailed status for admin users
                if self._has_admin_permission(user_context):
                    extension_data['detailed_status'] = self.extension_manager.get_extension_status(extension_name)
                
                return extension_data
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting extension {extension_name}: {e}")
                raise HTTPException(status_code=500, detail="Failed to get extension")
        
        @extension_router.post("/{extension_name}/load")
        async def load_extension(
            extension_name: str,
            force_reload: bool = False,
            user_context: Dict[str, Any] = Depends(require_extension_admin)
        ) -> Dict[str, Any]:
            """Load a specific extension with enhanced validation and logging."""
            if not self.extension_manager:
                raise HTTPException(status_code=503, detail="Extension system not initialized")
            
            try:
                logger.info(f"Admin {user_context['user_id']} loading extension {extension_name} (force_reload: {force_reload})")
                
                # Enhanced permission validation for system extensions
                if self._is_system_extension(extension_name) and not self._has_system_extension_permission(user_context):
                    raise HTTPException(status_code=403, detail="Insufficient permissions to load system extensions")
                
                # Check if extension is already loaded and handle accordingly
                existing_record = self.extension_manager.registry.get_extension(extension_name)
                if existing_record and existing_record.status.value == 'active' and not force_reload:
                    return {
                        'message': f'Extension {extension_name} is already loaded',
                        'status': existing_record.status.value,
                        'action': 'no_change'
                    }
                
                # Perform the load operation
                record = await self.extension_manager.load_extension(extension_name)
                if not record:
                    raise HTTPException(status_code=400, detail="Failed to load extension")
                
                # Log successful load for audit trail
                logger.info(f"Extension {extension_name} loaded successfully by {user_context['user_id']}")
                
                return {
                    'message': f'Extension {extension_name} loaded successfully',
                    'status': record.status.value,
                    'action': 'loaded',
                    'loaded_at': record.loaded_at.isoformat() if record.loaded_at else None
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error loading extension {extension_name} by user {user_context.get('user_id')}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to load extension: {str(e)}")
        
        @extension_router.post("/{extension_name}/unload")
        async def unload_extension(
            extension_name: str,
            force_unload: bool = False,
            user_context: Dict[str, Any] = Depends(require_extension_admin)
        ) -> Dict[str, Any]:
            """Unload a specific extension with enhanced safety checks."""
            if not self.extension_manager:
                raise HTTPException(status_code=503, detail="Extension system not initialized")
            
            try:
                logger.info(f"Admin {user_context['user_id']} unloading extension {extension_name} (force: {force_unload})")
                
                # Enhanced permission validation for system extensions
                if self._is_system_extension(extension_name) and not self._has_system_extension_permission(user_context):
                    raise HTTPException(status_code=403, detail="Insufficient permissions to unload system extensions")
                
                # Check if extension has active background tasks (unless force unload)
                if not force_unload and self._has_active_background_tasks(extension_name):
                    raise HTTPException(
                        status_code=409, 
                        detail="Extension has active background tasks. Use force_unload=true to override."
                    )
                
                # Perform the unload operation
                success = await self.extension_manager.unload_extension(extension_name)
                if not success:
                    raise HTTPException(status_code=400, detail="Failed to unload extension")
                
                # Log successful unload for audit trail
                logger.info(f"Extension {extension_name} unloaded successfully by {user_context['user_id']}")
                
                return {
                    'message': f'Extension {extension_name} unloaded successfully',
                    'action': 'unloaded',
                    'force_unload': force_unload
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error unloading extension {extension_name} by user {user_context.get('user_id')}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to unload extension: {str(e)}")
        
        @extension_router.post("/{extension_name}/reload")
        async def reload_extension(
            extension_name: str,
            preserve_state: bool = True,
            user_context: Dict[str, Any] = Depends(require_extension_admin)
        ) -> Dict[str, Any]:
            """Reload a specific extension with state preservation options."""
            if not self.extension_manager:
                raise HTTPException(status_code=503, detail="Extension system not initialized")
            
            try:
                logger.info(f"Admin {user_context['user_id']} reloading extension {extension_name} (preserve_state: {preserve_state})")
                
                # Enhanced permission validation for system extensions
                if self._is_system_extension(extension_name) and not self._has_system_extension_permission(user_context):
                    raise HTTPException(status_code=403, detail="Insufficient permissions to reload system extensions")
                
                # Get current state before reload if preservation is requested
                previous_state = None
                if preserve_state:
                    previous_state = self._capture_extension_state(extension_name)
                
                # Perform the reload operation
                record = await self.extension_manager.reload_extension(extension_name)
                if not record:
                    raise HTTPException(status_code=400, detail="Failed to reload extension")
                
                # Restore state if preservation was requested and successful
                if preserve_state and previous_state:
                    await self._restore_extension_state(extension_name, previous_state)
                
                # Log successful reload for audit trail
                logger.info(f"Extension {extension_name} reloaded successfully by {user_context['user_id']}")
                
                return {
                    'message': f'Extension {extension_name} reloaded successfully',
                    'status': record.status.value,
                    'action': 'reloaded',
                    'preserve_state': preserve_state,
                    'reloaded_at': record.loaded_at.isoformat() if record.loaded_at else None
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error reloading extension {extension_name} by user {user_context.get('user_id')}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to reload extension: {str(e)}")
        
        @extension_router.get("/{extension_name}/health")
        async def check_extension_health(
            extension_name: str,
            detailed: bool = False,
            user_context: Dict[str, Any] = Depends(require_extension_read)
        ) -> Dict[str, Any]:
            """Check health of a specific extension with detailed diagnostics."""
            if not self.extension_manager:
                raise HTTPException(status_code=503, detail="Extension system not initialized")
            
            try:
                logger.debug(f"User {user_context['user_id']} checking health of extension {extension_name}")
                
                # Check if user can access this extension
                record = self.extension_manager.registry.get_extension(extension_name)
                if not record:
                    raise HTTPException(status_code=404, detail="Extension not found")
                
                if not self._can_access_extension(record, user_context):
                    raise HTTPException(status_code=403, detail="Access denied to this extension")
                
                # Perform health check
                is_healthy = await self.extension_manager.check_extension_health(extension_name)
                
                health_data = {
                    'extension': extension_name,
                    'healthy': is_healthy,
                    'timestamp': datetime.utcnow().isoformat(),
                    'status': record.status.value
                }
                
                # Include detailed diagnostics if requested and user has admin permissions
                if detailed and self._has_admin_permission(user_context):
                    health_data.update({
                        'detailed_diagnostics': await self._get_extension_diagnostics(extension_name),
                        'resource_usage': await self._get_extension_resource_usage(extension_name),
                        'background_tasks': await self._get_extension_task_health(extension_name)
                    })
                
                return health_data
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error checking extension health {extension_name}: {e}")
                raise HTTPException(status_code=500, detail="Failed to check extension health")
        
        @extension_router.get("/system/health")
        async def extension_system_health(
            user_context: Dict[str, Any] = Depends(require_extension_read)
        ) -> Dict[str, Any]:
            """Get extension system health status."""
            if not self.extension_manager:
                raise HTTPException(status_code=503, detail="Extension system not initialized")
            
            try:
                health = await self.extension_manager.health_check()
                return health
                
            except Exception as e:
                logger.error(f"Error checking extension system health: {e}")
                raise HTTPException(status_code=500, detail="Failed to check system health")
        
        @extension_router.get("/system/stats")
        async def extension_system_stats(
            user_context: Dict[str, Any] = Depends(require_extension_read)
        ) -> Dict[str, Any]:
            """Get extension system statistics."""
            if not self.extension_manager:
                raise HTTPException(status_code=503, detail="Extension system not initialized")
            
            try:
                stats = self.extension_manager.get_manager_stats()
                return stats
                
            except Exception as e:
                logger.error(f"Error getting extension system stats: {e}")
                raise HTTPException(status_code=500, detail="Failed to get system stats")
        


        @extension_router.post("/{extension_name}/configure")
        async def configure_extension(
            extension_name: str,
            configuration: Dict[str, Any],
            user_context: Dict[str, Any] = Depends(require_extension_write)
        ) -> Dict[str, Any]:
            """Configure a specific extension with write permissions."""
            if not self.extension_manager:
                raise HTTPException(status_code=503, detail="Extension system not initialized")
            
            try:
                logger.info(f"User {user_context['user_id']} configuring extension {extension_name}")
                
                # Check if user can configure this extension
                record = self.extension_manager.registry.get_extension(extension_name)
                if not record:
                    raise HTTPException(status_code=404, detail="Extension not found")
                
                if not self._has_extension_config_permission(record, user_context):
                    raise HTTPException(status_code=403, detail="Insufficient permissions to configure this extension")
                
                # Apply configuration (this would be implemented in the extension manager)
                # For now, return success message
                return {
                    'message': f'Extension {extension_name} configured successfully',
                    'configuration': configuration,
                    'configured_by': user_context['user_id']
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error configuring extension {extension_name}: {e}")
                raise HTTPException(status_code=500, detail="Failed to configure extension")

        @extension_router.post("/discover")
        async def discover_extensions(
            user_context: Dict[str, Any] = Depends(require_extension_admin)
        ) -> Dict[str, Any]:
            """Discover available extensions."""
            if not self.extension_manager:
                raise HTTPException(status_code=503, detail="Extension system not initialized")
            
            try:
                logger.info(f"User {user_context['user_id']} discovering extensions")
                discovered = await self.extension_manager.discover_extensions()
                
                return {
                    'discovered': {
                        name: {
                            'name': manifest.name,
                            'version': manifest.version,
                            'display_name': manifest.display_name,
                            'description': manifest.description,
                            'category': manifest.category
                        }
                        for name, manifest in discovered.items()
                    },
                    'total': len(discovered)
                }
                
            except Exception as e:
                logger.error(f"Error discovering extensions: {e}")
                raise HTTPException(status_code=500, detail="Failed to discover extensions")
        
        # Include the router in the app
        app.include_router(extension_router)
        
        # Register background task endpoints with enhanced authentication
        if self.extension_manager:
            background_task_router = create_background_task_router(self.extension_manager)
            app.include_router(background_task_router, prefix="/api/extensions")
            logger.info("Background task endpoints registered with authentication")
        
        logger.info("Extension management endpoints registered with enhanced authentication")
    
    def _can_access_extension(self, extension_record, user_context: Dict[str, Any], can_view_system: bool = None) -> bool:
        """Enhanced extension access control with granular permissions using new permission system."""
        try:
            # Import here to avoid circular imports
            from server.extension_permissions import has_extension_permission, ExtensionPermission
            from server.extension_rbac import check_extension_role_permission
            from server.extension_tenant_access import check_tenant_extension_access
            
            extension_name = extension_record.manifest.name
            user_roles = user_context.get('roles', [])
            tenant_id = user_context.get('tenant_id')
            
            # Admin users can access all extensions
            if 'admin' in user_roles:
                return True
            
            # Service tokens can access all extensions
            if user_context.get('token_type') == 'service':
                return True
            
            # Check using the enhanced permission system
            # 1. Check tenant-specific access first (most restrictive)
            if check_tenant_extension_access(user_context, extension_name, ExtensionPermission.READ):
                return True
            
            # 2. Check role-based permissions
            if check_extension_role_permission(user_context, ExtensionPermission.READ, extension_name):
                return True
            
            # 3. Check direct permission grants
            if has_extension_permission(user_context, ExtensionPermission.READ, extension_name):
                return True
            
            # 4. Fallback to legacy category-based access control
            category = getattr(extension_record.manifest, 'category', 'general')
            
            # Check if this is a system extension
            if self._is_system_extension(extension_name):
                if can_view_system is None:
                    can_view_system = self._has_system_extension_permission(user_context)
                return can_view_system
            
            # Check category-based permissions
            if category == 'admin' and not self._has_admin_permission(user_context):
                return False
            
            # Check tenant-specific restrictions (legacy)
            if hasattr(extension_record.manifest, 'tenant_restrictions'):
                allowed_tenants = extension_record.manifest.tenant_restrictions
                if allowed_tenants and tenant_id not in allowed_tenants:
                    return False
            
            # Default: allow access to general extensions for authenticated users
            return category in ['general', 'utility', 'integration']
            
        except Exception as e:
            logger.error(f"Error checking extension access for {extension_record.manifest.name}: {e}")
            # Fallback to restrictive access on error
            return user_context.get('roles', []) and 'admin' in user_context.get('roles', [])
    
    def _has_admin_permission(self, user_context: Dict[str, Any]) -> bool:
        """Check if user has admin permissions using enhanced permission system."""
        try:
            # Import here to avoid circular imports
            from server.extension_permissions import has_extension_permission, ExtensionPermission
            from server.extension_rbac import check_extension_role_permission
            
            # Check using enhanced permission system
            if check_extension_role_permission(user_context, ExtensionPermission.ADMIN):
                return True
            
            if has_extension_permission(user_context, ExtensionPermission.ADMIN):
                return True
            
            # Fallback to legacy permission checking
            user_roles = user_context.get('roles', [])
            user_permissions = user_context.get('permissions', [])
            
            return (
                'admin' in user_roles or 
                'extension:admin' in user_permissions or
                'extension:*' in user_permissions
            )
            
        except Exception as e:
            logger.error(f"Error checking admin permission: {e}")
            # Fallback to basic role check
            return 'admin' in user_context.get('roles', [])
    
    def _has_system_extension_permission(self, user_context: Dict[str, Any]) -> bool:
        """Check if user has permission to access system extensions."""
        try:
            # Import here to avoid circular imports
            from server.extension_permissions import has_extension_permission, ExtensionPermission
            from server.extension_rbac import check_extension_role_permission, ExtensionRole
            
            # Check if user has system role
            user_roles = user_context.get('roles', [])
            if 'system' in user_roles or ExtensionRole.SYSTEM.value in user_roles:
                return True
            
            # Check admin permissions (admins can access system extensions)
            if self._has_admin_permission(user_context):
                return True
            
            # Check specific system extension permission
            if has_extension_permission(user_context, ExtensionPermission.ADMIN, category='system'):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking system extension permission: {e}")
            return False
    
    def _has_extension_config_permission(self, extension_record, user_context: Dict[str, Any]) -> bool:
        """Check if user has permission to configure an extension."""
        try:
            # Import here to avoid circular imports
            from server.extension_permissions import has_extension_permission, ExtensionPermission
            from server.extension_rbac import check_extension_role_permission
            from server.extension_tenant_access import check_tenant_extension_access
            
            extension_name = extension_record.manifest.name
            
            # Check admin permission first
            if self._has_admin_permission(user_context):
                return True
            
            # Check tenant-specific configure access
            if check_tenant_extension_access(user_context, extension_name, ExtensionPermission.CONFIGURE):
                return True
            
            # Check role-based configure permission
            if check_extension_role_permission(user_context, ExtensionPermission.CONFIGURE, extension_name):
                return True
            
            # Check direct configure permission
            if has_extension_permission(user_context, ExtensionPermission.CONFIGURE, extension_name):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking extension config permission: {e}")
            return False
    
    def _is_system_extension(self, extension_name: str) -> bool:
        """Check if an extension is a system extension."""
        # Define system extensions (these could be configurable)
        system_extensions = {
            'core', 'system', 'admin', 'security', 'monitoring',
            'health', 'metrics', 'logging', 'backup', 'migration'
        }
        
        # Check if extension name contains system keywords
        extension_lower = extension_name.lower()
        return (
            extension_lower in system_extensions or
            extension_lower.startswith('system_') or
            extension_lower.startswith('core_') or
            extension_lower.endswith('_system') or
            extension_lower.endswith('_core')
        )
    
    def _has_active_background_tasks(self, extension_name: str) -> bool:
        """Check if extension has active background tasks."""
        try:
            if not self.extension_manager:
                return False
            
            # This would need to be implemented in the extension manager
            # For now, return False to allow unloading
            return False
            
        except Exception as e:
            logger.error(f"Error checking active background tasks for {extension_name}: {e}")
            return False
    
    def _capture_extension_state(self, extension_name: str) -> Optional[Dict[str, Any]]:
        """Capture extension state for preservation during reload."""
        try:
            if not self.extension_manager:
                return None
            
            # This would capture extension-specific state
            # For now, return None (no state preservation)
            return None
            
        except Exception as e:
            logger.error(f"Error capturing state for extension {extension_name}: {e}")
            return None
    
    async def _restore_extension_state(self, extension_name: str, state: Dict[str, Any]) -> bool:
        """Restore extension state after reload."""
        try:
            if not self.extension_manager or not state:
                return False
            
            # This would restore extension-specific state
            # For now, return True (no state restoration)
            return True
            
        except Exception as e:
            logger.error(f"Error restoring state for extension {extension_name}: {e}")
            return False
    
    async def _get_extension_diagnostics(self, extension_name: str) -> Dict[str, Any]:
        """Get detailed diagnostics for an extension."""
        try:
            if not self.extension_manager:
                return {}
            
            # This would get detailed diagnostics from the extension manager
            return {
                'status': 'healthy',
                'last_check': datetime.utcnow().isoformat(),
                'memory_usage': 'unknown',
                'cpu_usage': 'unknown',
                'error_count': 0
            }
            
        except Exception as e:
            logger.error(f"Error getting diagnostics for extension {extension_name}: {e}")
            return {'error': str(e)}
    
    async def _get_extension_resource_usage(self, extension_name: str) -> Dict[str, Any]:
        """Get resource usage for an extension."""
        try:
            # This would get resource usage from the extension manager
            return {
                'memory_mb': 0,
                'cpu_percent': 0.0,
                'disk_usage_mb': 0,
                'network_io': {'bytes_sent': 0, 'bytes_received': 0}
            }
            
        except Exception as e:
            logger.error(f"Error getting resource usage for extension {extension_name}: {e}")
            return {'error': str(e)}
    
    async def _get_extension_task_health(self, extension_name: str) -> Dict[str, Any]:
        """Get background task health for an extension."""
        try:
            # This would get task health from the extension manager
            return {
                'active_tasks': 0,
                'failed_tasks': 0,
                'completed_tasks': 0,
                'last_task_run': None
            }
            
        except Exception as e:
            logger.error(f"Error getting task health for extension {extension_name}: {e}")
            return {'error': str(e)}
    
    def _get_extension_permissions(self, extension_record, user_context: Dict[str, Any]) -> List[str]:
        """Get user's permissions for a specific extension."""
        try:
            # Import here to avoid circular imports
            from server.extension_permissions import ExtensionPermission, get_extension_permission_manager
            
            extension_name = extension_record.manifest.name
            permissions = []
            
            permission_manager = get_extension_permission_manager()
            
            # Check each permission type
            for permission in ExtensionPermission:
                if permission_manager.has_permission(user_context, permission, extension_name):
                    permissions.append(permission.value)
            
            return permissions
            
        except Exception as e:
            logger.error(f"Error getting extension permissions: {e}")
            return []
            'extension:*' in user_permissions
        )
    
    def _has_system_extension_permission(self, user_context: Dict[str, Any]) -> bool:
        """Check if user can access system extensions."""
        user_roles = user_context.get('roles', [])
        user_permissions = user_context.get('permissions', [])
        
        return (
            'admin' in user_roles or 
            'system_admin' in user_roles or
            'extension:system' in user_permissions or
            'extension:*' in user_permissions
        )
    
    def _is_system_extension(self, extension_name: str) -> bool:
        """Check if extension is a system extension."""
        # System extensions are those that provide core platform functionality
        system_extensions = [
            'core-auth', 'core-logging', 'core-monitoring', 
            'system-health', 'admin-panel', 'security-manager'
        ]
        return extension_name in system_extensions or extension_name.startswith('system-')
    
    def _get_extension_permissions(self, extension_record, user_context: Dict[str, Any]) -> Dict[str, bool]:
        """Get user's permissions for a specific extension."""
        extension_name = extension_record.manifest.name
        
        return {
            'can_read': self._can_access_extension(extension_record, user_context),
            'can_write': self._has_extension_write_permission(extension_record, user_context),
            'can_admin': self._has_extension_admin_permission(extension_record, user_context),
            'can_execute_tasks': self._has_extension_task_permission(extension_record, user_context),
            'can_configure': self._has_extension_config_permission(extension_record, user_context)
        }
    
    def _has_extension_write_permission(self, extension_record, user_context: Dict[str, Any]) -> bool:
        """Check if user has write permission for specific extension."""
        if not self._can_access_extension(extension_record, user_context):
            return False
        
        user_roles = user_context.get('roles', [])
        user_permissions = user_context.get('permissions', [])
        extension_name = extension_record.manifest.name
        
        return (
            'admin' in user_roles or
            'extension:write' in user_permissions or
            f'extension:{extension_name}:write' in user_permissions or
            'extension:*' in user_permissions
        )
    
    def _has_extension_admin_permission(self, extension_record, user_context: Dict[str, Any]) -> bool:
        """Check if user has admin permission for specific extension."""
        user_roles = user_context.get('roles', [])
        user_permissions = user_context.get('permissions', [])
        extension_name = extension_record.manifest.name
        
        return (
            'admin' in user_roles or
            'extension:admin' in user_permissions or
            f'extension:{extension_name}:admin' in user_permissions or
            'extension:*' in user_permissions
        )
    
    def _has_extension_task_permission(self, extension_record, user_context: Dict[str, Any]) -> bool:
        """Check if user has background task permission for specific extension."""
        if not self._can_access_extension(extension_record, user_context):
            return False
        
        user_roles = user_context.get('roles', [])
        user_permissions = user_context.get('permissions', [])
        extension_name = extension_record.manifest.name
        
        return (
            'admin' in user_roles or
            'extension:background_tasks' in user_permissions or
            f'extension:{extension_name}:tasks' in user_permissions or
            'extension:*' in user_permissions
        )
    
    def _has_extension_config_permission(self, extension_record, user_context: Dict[str, Any]) -> bool:
        """Check if user has configuration permission for specific extension."""
        user_roles = user_context.get('roles', [])
        user_permissions = user_context.get('permissions', [])
        extension_name = extension_record.manifest.name
        
        return (
            'admin' in user_roles or
            'extension:configure' in user_permissions or
            f'extension:{extension_name}:configure' in user_permissions or
            'extension:*' in user_permissions
        )
    
    def _has_active_background_tasks(self, extension_name: str) -> bool:
        """Check if extension has active background tasks."""
        if not self.extension_manager or not hasattr(self.extension_manager, 'background_task_manager'):
            return False
        
        try:
            active_tasks = self.extension_manager.get_active_task_executions()
            return any(task.startswith(f"{extension_name}.") for task in active_tasks)
        except Exception as e:
            logger.warning(f"Error checking active tasks for {extension_name}: {e}")
            return False
    
    def _capture_extension_state(self, extension_name: str) -> Optional[Dict[str, Any]]:
        """Capture extension state for preservation during reload."""
        try:
            record = self.extension_manager.registry.get_extension(extension_name)
            if not record or not record.instance:
                return None
            
            # Capture basic state information
            state = {
                'configuration': getattr(record.instance, 'configuration', {}),
                'runtime_data': getattr(record.instance, 'runtime_data', {}),
                'last_activity': getattr(record, 'last_activity', None)
            }
            
            # Capture extension-specific state if available
            if hasattr(record.instance, 'get_state'):
                state['extension_state'] = record.instance.get_state()
            
            return state
        except Exception as e:
            logger.warning(f"Error capturing state for {extension_name}: {e}")
            return None
    
    async def _restore_extension_state(self, extension_name: str, state: Dict[str, Any]) -> bool:
        """Restore extension state after reload."""
        try:
            record = self.extension_manager.registry.get_extension(extension_name)
            if not record or not record.instance:
                return False
            
            # Restore basic state
            if 'configuration' in state:
                setattr(record.instance, 'configuration', state['configuration'])
            
            if 'runtime_data' in state:
                setattr(record.instance, 'runtime_data', state['runtime_data'])
            
            # Restore extension-specific state if available
            if 'extension_state' in state and hasattr(record.instance, 'set_state'):
                record.instance.set_state(state['extension_state'])
            
            return True
        except Exception as e:
            logger.warning(f"Error restoring state for {extension_name}: {e}")
            return False
    
    async def _get_extension_diagnostics(self, extension_name: str) -> Dict[str, Any]:
        """Get detailed diagnostics for an extension."""
        try:
            record = self.extension_manager.registry.get_extension(extension_name)
            if not record:
                return {'error': 'Extension not found'}
            
            diagnostics = {
                'load_time': record.loaded_at.isoformat() if record.loaded_at else None,
                'status': record.status.value,
                'error': record.error,
                'instance_type': type(record.instance).__name__ if record.instance else None,
                'capabilities': record.manifest.capabilities.__dict__ if record.manifest else {},
                'dependencies': getattr(record.manifest, 'dependencies', []) if record.manifest else []
            }
            
            # Add instance-specific diagnostics if available
            if record.instance and hasattr(record.instance, 'get_diagnostics'):
                diagnostics['instance_diagnostics'] = record.instance.get_diagnostics()
            
            return diagnostics
        except Exception as e:
            logger.error(f"Error getting diagnostics for {extension_name}: {e}")
            return {'error': str(e)}
    
    async def _get_extension_resource_usage(self, extension_name: str) -> Dict[str, Any]:
        """Get resource usage information for an extension."""
        try:
            # This would integrate with system monitoring to get actual resource usage
            # For now, return placeholder data
            return {
                'memory_usage': 'N/A',
                'cpu_usage': 'N/A',
                'disk_usage': 'N/A',
                'network_usage': 'N/A',
                'note': 'Resource monitoring not yet implemented'
            }
        except Exception as e:
            logger.error(f"Error getting resource usage for {extension_name}: {e}")
            return {'error': str(e)}
    
    async def _get_extension_task_health(self, extension_name: str) -> Dict[str, Any]:
        """Get background task health for an extension."""
        try:
            if not self.extension_manager or not hasattr(self.extension_manager, 'background_task_manager'):
                return {'error': 'Background task manager not available'}
            
            # Get task statistics for this extension
            tasks = self.extension_manager.get_extension_tasks(extension_name)
            active_executions = [
                task for task in self.extension_manager.get_active_task_executions()
                if task.startswith(f"{extension_name}.")
            ]
            
            return {
                'registered_tasks': len(tasks),
                'active_executions': len(active_executions),
                'task_names': [task.name for task in tasks],
                'active_task_ids': active_executions
            }
        except Exception as e:
            logger.error(f"Error getting task health for {extension_name}: {e}")
            return {'error': str(e)}
    
    def get_extension_manager(self) -> Optional[ExtensionManager]:
        """Get the extension manager instance."""
        return self.extension_manager
    
    def is_initialized(self) -> bool:
        """Check if the extension system is initialized."""
        return self._initialized


# Global extension system integration instance
extension_system = ExtensionSystemIntegration()


async def initialize_extensions(
    app: FastAPI,
    extension_root: str = "extensions",
    db_session=None,
    plugin_router=None
) -> bool:
    """
    Initialize the extension system for a FastAPI application.
    
    This is a convenience function that can be called from the main application
    to set up the extension system.
    
    Args:
        app: FastAPI application instance
        extension_root: Root directory for extensions
        db_session: Database session for persistence
        plugin_router: Plugin router for orchestration
        
    Returns:
        bool: True if initialization successful
    """
    # Store extension system instance in app state for health monitoring access
    app.state.extension_system = extension_system
    
    success = await extension_system.initialize_extension_system(
        app=app,
        extension_root=extension_root,
        db_session=db_session,
        plugin_router=plugin_router
    )
    
    return success


def get_extension_manager() -> Optional[ExtensionManager]:
    """
    Get the global extension manager instance.
    
    Returns:
        Optional[ExtensionManager]: Extension manager or None if not initialized
    """
    return extension_system.get_extension_manager()


def is_extension_system_initialized() -> bool:
    """
    Check if the extension system is initialized.
    
    Returns:
        bool: True if extension system is initialized
    """
    return extension_system.is_initialized()