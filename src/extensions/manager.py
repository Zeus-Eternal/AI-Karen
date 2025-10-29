"""
Extension Manager for the AI Karen Extensions System.

This module provides the ExtensionManager class that coordinates extension
discovery, loading, lifecycle management, and integration with the FastAPI application.
"""

import logging
import asyncio
import importlib.util
import sys
from typing import Dict, List, Optional, Any, Type
from pathlib import Path
from datetime import datetime, timezone
import json

from .models import (
    ExtensionManifest, 
    ExtensionRecord, 
    ExtensionStatus,
    ExtensionContext
)
from .base import BaseExtension
from .registry import ExtensionRegistry
from .api_integration import ExtensionAPIIntegration
from .background_tasks import BackgroundTaskManager
from .security import ExtensionSecurityManager
from .security_decorators import set_security_manager

logger = logging.getLogger(__name__)


class ExtensionManager:
    """
    Manages the lifecycle of extensions in the AI Karen platform.
    
    The ExtensionManager handles extension discovery, loading, initialization,
    API registration, and health monitoring.
    """
    
    def __init__(
        self, 
        extension_root: Path,
        app=None,
        db_session=None,
        plugin_router=None
    ):
        """
        Initialize the Extension Manager.
        
        Args:
            extension_root: Root directory for extensions
            app: FastAPI application instance
            db_session: Database session for persistence
            plugin_router: Plugin router for orchestration
        """
        self.extension_root = Path(extension_root)
        self.app = app
        self.db_session = db_session
        self.plugin_router = plugin_router
        
        # Core components
        self.registry = ExtensionRegistry(db_session)
        self.api_integration = ExtensionAPIIntegration(app) if app else None
        self.background_task_manager = BackgroundTaskManager(self)
        self.security_manager = ExtensionSecurityManager()
        
        # Set global security manager for decorators
        set_security_manager(self.security_manager)
        
        # Extension tracking
        self.loaded_extensions: Dict[str, ExtensionRecord] = {}
        self.extension_modules: Dict[str, Any] = {}
        
        # Monitoring
        self._monitoring_task: Optional[asyncio.Task] = None
        self._monitoring_enabled = False
        
        logger.info(f"Extension Manager initialized with root: {extension_root}")
    
    async def initialize(self) -> None:
        """Initialize the extension manager."""
        try:
            logger.info("Initializing Extension Manager")
            
            # Load registry from database if available
            if self.db_session:
                await self.registry.load_from_database()
            
            # Initialize background task manager
            await self.background_task_manager.initialize()
            
            # Start monitoring
            await self.start_monitoring()
            
            logger.info("Extension Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Extension Manager: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the extension manager."""
        try:
            logger.info("Shutting down Extension Manager")
            
            # Stop monitoring
            await self.stop_monitoring()
            
            # Shutdown background task manager
            await self.background_task_manager.shutdown()
            
            # Unload all extensions
            await self.unload_all_extensions()
            
            # Save registry to database
            if self.db_session:
                await self.registry.save_to_database()
            
            logger.info("Extension Manager shut down successfully")
            
        except Exception as e:
            logger.error(f"Error during Extension Manager shutdown: {e}")
    
    async def discover_extensions(self) -> Dict[str, ExtensionManifest]:
        """
        Discover extensions in the extension root directory.
        
        Returns:
            Dict[str, ExtensionManifest]: Discovered extension manifests
        """
        try:
            logger.info(f"Discovering extensions in {self.extension_root}")
            discovered = {}
            
            if not self.extension_root.exists():
                logger.warning(f"Extension root directory does not exist: {self.extension_root}")
                return discovered
            
            # Search for extension manifests
            for manifest_path in self.extension_root.rglob("extension.json"):
                try:
                    # Load and validate manifest
                    manifest = await self._load_manifest(manifest_path)
                    if manifest:
                        discovered[manifest.name] = manifest
                        logger.debug(f"Discovered extension: {manifest.name}")
                
                except Exception as e:
                    logger.error(f"Error loading manifest {manifest_path}: {e}")
                    continue
            
            logger.info(f"Discovered {len(discovered)} extensions")
            return discovered
            
        except Exception as e:
            logger.error(f"Extension discovery failed: {e}")
            return {}
    
    async def load_extension(self, extension_name: str) -> Optional[ExtensionRecord]:
        """
        Load a specific extension.
        
        Args:
            extension_name: Name of the extension to load
            
        Returns:
            Optional[ExtensionRecord]: Loaded extension record or None
        """
        try:
            logger.info(f"Loading extension: {extension_name}")
            
            # Check if already loaded
            if extension_name in self.loaded_extensions:
                logger.info(f"Extension {extension_name} already loaded")
                return self.loaded_extensions[extension_name]
            
            # Discover extensions if not already done
            discovered = await self.discover_extensions()
            if extension_name not in discovered:
                logger.error(f"Extension {extension_name} not found")
                return None
            
            manifest = discovered[extension_name]
            
            # Create extension record
            record = ExtensionRecord(
                manifest=manifest,
                status=ExtensionStatus.LOADING
            )
            
            # Register in registry
            await self.registry.register_extension(manifest)
            await self.registry.update_extension_status(extension_name, ExtensionStatus.LOADING)
            
            # Load extension module
            extension_instance = await self._load_extension_module(manifest)
            if not extension_instance:
                await self.registry.update_extension_status(
                    extension_name, 
                    ExtensionStatus.ERROR,
                    "Failed to load extension module"
                )
                return None
            
            # Update record with instance
            record.instance = extension_instance
            await self.registry.update_extension_instance(extension_name, extension_instance)
            
            # Initialize extension
            await extension_instance.initialize()
            
            # Register API if extension provides it
            if self.api_integration and manifest.capabilities.provides_api:
                api_success = await self.api_integration.register_extension_api(record)
                if not api_success:
                    logger.warning(f"Failed to register API for extension {extension_name}")
            
            # Register background tasks if extension provides them
            if manifest.capabilities.provides_background_tasks:
                self.background_task_manager.register_extension_tasks(record)
            
            # Update status to active
            record.status = ExtensionStatus.ACTIVE
            record.loaded_at = datetime.now(timezone.utc)
            await self.registry.update_extension_status(extension_name, ExtensionStatus.ACTIVE)
            
            # Track loaded extension
            self.loaded_extensions[extension_name] = record
            
            logger.info(f"Extension {extension_name} loaded successfully")
            return record
            
        except Exception as e:
            logger.error(f"Failed to load extension {extension_name}: {e}")
            
            # Update status to error
            await self.registry.update_extension_status(
                extension_name, 
                ExtensionStatus.ERROR,
                str(e)
            )
            
            return None
    
    async def unload_extension(self, extension_name: str) -> bool:
        """
        Unload a specific extension.
        
        Args:
            extension_name: Name of the extension to unload
            
        Returns:
            bool: True if unload successful
        """
        try:
            logger.info(f"Unloading extension: {extension_name}")
            
            # Check if extension is loaded
            if extension_name not in self.loaded_extensions:
                logger.warning(f"Extension {extension_name} not loaded")
                return True
            
            record = self.loaded_extensions[extension_name]
            
            # Update status to unloading
            await self.registry.update_extension_status(extension_name, ExtensionStatus.UNLOADING)
            
            # Unregister API
            if self.api_integration:
                await self.api_integration.unregister_extension_api(extension_name)
            
            # Unregister background tasks
            self.background_task_manager.unregister_extension_tasks(extension_name)
            
            # Stop security monitoring
            self.security_manager.stop_extension_monitoring(extension_name)
            
            # Shutdown extension instance
            if record.instance:
                try:
                    await record.instance.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down extension {extension_name}: {e}")
            
            # Cleanup security resources
            await self.security_manager.cleanup_extension_security(extension_name)
            
            # Remove from loaded extensions
            del self.loaded_extensions[extension_name]
            
            # Remove module from cache
            if extension_name in self.extension_modules:
                del self.extension_modules[extension_name]
            
            # Update status
            await self.registry.update_extension_status(extension_name, ExtensionStatus.NOT_LOADED)
            
            logger.info(f"Extension {extension_name} unloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload extension {extension_name}: {e}")
            return False
    
    async def reload_extension(self, extension_name: str) -> Optional[ExtensionRecord]:
        """
        Reload a specific extension.
        
        Args:
            extension_name: Name of the extension to reload
            
        Returns:
            Optional[ExtensionRecord]: Reloaded extension record or None
        """
        try:
            logger.info(f"Reloading extension: {extension_name}")
            
            # Unload if currently loaded
            if extension_name in self.loaded_extensions:
                await self.unload_extension(extension_name)
            
            # Load again
            return await self.load_extension(extension_name)
            
        except Exception as e:
            logger.error(f"Failed to reload extension {extension_name}: {e}")
            return None
    
    async def load_all_extensions(self) -> Dict[str, ExtensionRecord]:
        """
        Load all discovered extensions.
        
        Returns:
            Dict[str, ExtensionRecord]: Loaded extension records
        """
        try:
            logger.info("Loading all extensions")
            
            discovered = await self.discover_extensions()
            loaded = {}
            
            # Sort by dependencies (simple implementation)
            sorted_extensions = self._sort_extensions_by_dependencies(discovered)
            
            for extension_name in sorted_extensions:
                record = await self.load_extension(extension_name)
                if record:
                    loaded[extension_name] = record
            
            logger.info(f"Loaded {len(loaded)} out of {len(discovered)} extensions")
            return loaded
            
        except Exception as e:
            logger.error(f"Failed to load all extensions: {e}")
            return {}
    
    async def unload_all_extensions(self) -> bool:
        """
        Unload all loaded extensions.
        
        Returns:
            bool: True if all extensions unloaded successfully
        """
        try:
            logger.info("Unloading all extensions")
            
            success = True
            extension_names = list(self.loaded_extensions.keys())
            
            for extension_name in extension_names:
                if not await self.unload_extension(extension_name):
                    success = False
            
            logger.info("All extensions unloaded")
            return success
            
        except Exception as e:
            logger.error(f"Failed to unload all extensions: {e}")
            return False
    
    def get_extension_status(self, extension_name: str) -> Optional[Dict[str, Any]]:
        """
        Get status information for a specific extension.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            Optional[Dict[str, Any]]: Extension status or None
        """
        record = self.registry.get_extension(extension_name)
        if not record:
            return None
        
        status = {
            'name': extension_name,
            'version': record.manifest.version,
            'status': record.status.value,
            'loaded_at': record.loaded_at.isoformat() if record.loaded_at else None,
            'error': record.error,
            'capabilities': {
                'provides_ui': record.manifest.capabilities.provides_ui,
                'provides_api': record.manifest.capabilities.provides_api,
                'provides_background_tasks': record.manifest.capabilities.provides_background_tasks,
                'provides_webhooks': record.manifest.capabilities.provides_webhooks
            }
        }
        
        # Add instance status if available
        if record.instance:
            try:
                instance_status = record.instance.get_status()
                status.update(instance_status)
            except Exception as e:
                logger.error(f"Error getting instance status for {extension_name}: {e}")
        
        return status
    
    def get_loaded_extensions(self) -> List[ExtensionRecord]:
        """
        Get all loaded extension records.
        
        Returns:
            List[ExtensionRecord]: Loaded extension records
        """
        return list(self.loaded_extensions.values())
    
    def get_extension_by_name(self, extension_name: str) -> Optional[ExtensionRecord]:
        """
        Get extension record by name.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            Optional[ExtensionRecord]: Extension record or None
        """
        return self.loaded_extensions.get(extension_name)
    
    async def check_extension_health(self, extension_name: str) -> bool:
        """
        Check health of a specific extension.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            bool: True if extension is healthy
        """
        try:
            record = self.loaded_extensions.get(extension_name)
            if not record or not record.instance:
                return False
            
            # Check if extension is active
            if record.status != ExtensionStatus.ACTIVE:
                return False
            
            # Perform health check on instance
            health_result = await record.instance.health_check()
            is_healthy = health_result.get('healthy', False)
            
            # Update health information
            await self.registry.update_extension_health(extension_name, health_result)
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"Health check failed for extension {extension_name}: {e}")
            return False
    
    async def check_all_extensions_health(self) -> Dict[str, bool]:
        """
        Check health of all loaded extensions.
        
        Returns:
            Dict[str, bool]: Health status by extension name
        """
        health_status = {}
        
        for extension_name in self.loaded_extensions:
            health_status[extension_name] = await self.check_extension_health(extension_name)
        
        return health_status
    
    async def start_monitoring(self) -> None:
        """Start extension monitoring."""
        if self._monitoring_enabled:
            return
        
        self._monitoring_enabled = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Extension monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop extension monitoring."""
        self._monitoring_enabled = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
        
        logger.info("Extension monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Extension monitoring loop."""
        while self._monitoring_enabled:
            try:
                # Check health of all extensions
                await self.check_all_extensions_health()
                
                # Sleep for monitoring interval (30 seconds)
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Extension monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _load_manifest(self, manifest_path: Path) -> Optional[ExtensionManifest]:
        """Load and validate extension manifest."""
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
            
            # Validate manifest
            manifest = ExtensionManifest(**manifest_data)
            
            return manifest
            
        except Exception as e:
            logger.error(f"Failed to load manifest {manifest_path}: {e}")
            return None
    
    async def _load_extension_module(self, manifest: ExtensionManifest) -> Optional[BaseExtension]:
        """Load extension module and create instance."""
        try:
            extension_name = manifest.name
            
            # Find extension directory
            extension_dir = self._find_extension_directory(manifest)
            if not extension_dir:
                logger.error(f"Extension directory not found for {extension_name}")
                return None
            
            # Load extension module
            module_path = extension_dir / "__init__.py"
            if not module_path.exists():
                logger.error(f"Extension module not found: {module_path}")
                return None
            
            # Import module
            spec = importlib.util.spec_from_file_location(
                f"extension_{extension_name}", 
                module_path
            )
            if not spec or not spec.loader:
                logger.error(f"Failed to create module spec for {extension_name}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"extension_{extension_name}"] = module
            spec.loader.exec_module(module)
            
            # Cache module
            self.extension_modules[extension_name] = module
            
            # Find extension class
            extension_class = self._find_extension_class(module, manifest)
            if not extension_class:
                logger.error(f"Extension class not found in {extension_name}")
                return None
            
            # Create extension context
            context = ExtensionContext(
                extension_name=extension_name,
                resource_limits=manifest.resources
            )
            
            # Initialize security for extension
            security_policy = await self.security_manager.initialize_extension_security(
                extension_name, manifest, context
            )
            
            # Create extension instance
            instance = extension_class(manifest, context)
            
            # Inject services
            instance.plugin_orchestrator = self.plugin_router  # Will be proper orchestrator later
            instance.security_manager = self.security_manager
            # instance.data_manager = data_manager  # Will be injected later
            
            return instance
            
        except Exception as e:
            logger.error(f"Failed to load extension module for {manifest.name}: {e}")
            return None
    
    def _find_extension_directory(self, manifest: ExtensionManifest) -> Optional[Path]:
        """Find the directory containing the extension."""
        extension_name = manifest.name
        
        # Search in extension root and subdirectories
        for path in self.extension_root.rglob("extension.json"):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    if data.get('name') == extension_name:
                        return path.parent
            except Exception:
                continue
        
        return None
    
    def _find_extension_class(self, module: Any, manifest: ExtensionManifest) -> Optional[Type[BaseExtension]]:
        """Find the extension class in the module."""
        extension_name = manifest.name
        
        # Look for class that inherits from BaseExtension
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type) and
                issubclass(attr, BaseExtension) and
                attr != BaseExtension
            ):
                return attr
        
        # Look for specific naming patterns
        class_names = [
            f"{extension_name.replace('-', '_').title()}Extension",
            f"{extension_name.replace('-', '').title()}Extension",
            "Extension",
            "MainExtension"
        ]
        
        for class_name in class_names:
            if hasattr(module, class_name):
                attr = getattr(module, class_name)
                if isinstance(attr, type) and issubclass(attr, BaseExtension):
                    return attr
        
        return None
    
    def _sort_extensions_by_dependencies(self, extensions: Dict[str, ExtensionManifest]) -> List[str]:
        """Sort extensions by dependencies (simple topological sort)."""
        # Simple implementation - can be enhanced with proper dependency resolution
        sorted_names = []
        remaining = set(extensions.keys())
        
        while remaining:
            # Find extensions with no unresolved dependencies
            ready = []
            for name in remaining:
                manifest = extensions[name]
                deps = manifest.dependencies.extensions
                if all(dep not in remaining for dep in deps):
                    ready.append(name)
            
            if not ready:
                # Circular dependency or missing dependency - add remaining in arbitrary order
                ready = list(remaining)
            
            sorted_names.extend(ready)
            remaining -= set(ready)
        
        return sorted_names
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """Get extension manager statistics."""
        return {
            'loaded_extensions': len(self.loaded_extensions),
            'registry_stats': self.registry.get_registry_stats(),
            'monitoring_enabled': self._monitoring_enabled,
            'api_integration_enabled': self.api_integration is not None,
            'background_task_stats': self.background_task_manager.get_manager_stats()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Extension manager health check."""
        try:
            stats = self.get_manager_stats()
            registry_health = await self.registry.health_check()
            
            health_status = {
                'status': 'healthy',
                'loaded_extensions': stats['loaded_extensions'],
                'registry_healthy': registry_health['status'] == 'healthy',
                'monitoring_active': self._monitoring_enabled,
                'api_integration_active': self.api_integration is not None
            }
            
            # Check API integration health
            if self.api_integration:
                api_health = await self.api_integration.health_check()
                health_status['api_integration_healthy'] = api_health['status'] == 'healthy'
            
            # Check background task manager health
            task_health = await self.background_task_manager.health_check()
            health_status['background_tasks_healthy'] = task_health['status'] == 'healthy'
            health_status['background_task_stats'] = task_health
            
            # Check security manager health
            security_health = await self.security_manager.health_check()
            health_status['security_healthy'] = security_health['status'] == 'healthy'
            health_status['security_stats'] = security_health
            
            return health_status
            
        except Exception as e:
            logger.error(f"Extension manager health check error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    # Background task management methods
    async def execute_extension_task(
        self, 
        extension_name: str, 
        task_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute an extension background task manually."""
        return await self.background_task_manager.execute_task_manually(
            extension_name, task_name, parameters
        )
    
    async def emit_event(self, event_type: str, event_data: Dict[str, Any]) -> List[str]:
        """Emit an event that may trigger extension tasks."""
        return await self.background_task_manager.emit_event(event_type, event_data)
    
    def register_event_trigger(
        self, 
        event_type: str, 
        extension_name: str, 
        task_name: str,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register an event trigger for an extension task."""
        self.background_task_manager.register_event_trigger(
            event_type, extension_name, task_name, filter_conditions
        )
    
    def get_extension_tasks(self, extension_name: Optional[str] = None) -> List[Any]:
        """Get background tasks for an extension or all extensions."""
        tasks = self.background_task_manager.get_task_definitions()
        if extension_name:
            return [task for task in tasks if task.extension_name == extension_name]
        return tasks
    
    def get_task_execution_history(
        self, 
        extension_name: Optional[str] = None,
        task_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Any]:
        """Get task execution history."""
        return self.background_task_manager.get_execution_history(
            extension_name, task_name, limit
        )
    
    def get_active_task_executions(self) -> List[str]:
        """Get currently running task executions."""
        return self.background_task_manager.get_active_executions()
    
    async def cancel_task_execution(self, execution_id: str) -> bool:
        """Cancel a running task execution."""
        return await self.background_task_manager.cancel_task_execution(execution_id)