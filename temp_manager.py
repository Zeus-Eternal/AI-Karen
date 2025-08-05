"""
Extension manager for discovery, loading, and lifecycle management.
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_karen_engine.plugins.router import PluginRouter

from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.hooks.hook_mixin import HookMixin
from ai_karen_engine.hooks.hook_types import HookTypes
from ai_karen_engine.extensions.models import (
    ExtensionContext, 
    ExtensionManifest, 
    ExtensionRecord, 
    ExtensionStatus
)
from ai_karen_engine.extensions.registry import ExtensionRegistry
from ai_karen_engine.extensions.validator import ExtensionValidator
from ai_karen_engine.extensions.dependency_resolver import DependencyResolver, DependencyError
from ai_karen_engine.extensions.resource_monitor import (
    ResourceMonitor,
    ExtensionHealthChecker,
    HealthStatus,
)
from ai_karen_engine.event_bus import get_event_bus
from ai_karen_engine.extensions.marketplace_client import MarketplaceClient


class ExtensionManager(HookMixin):
    """
    Manages extension discovery, loading, and lifecycle.
    
    This is the main class responsible for:
    - Discovering extensions in the extensions directory
    - Loading and initializing extensions
    - Managing extension lifecycle (start, stop, reload)
    - Providing access to loaded extensions
    """
    
    def __init__(
        self, 
        extension_root: Path, 
        plugin_router: PluginRouter,
        db_session: Any = None,
        app_instance: Any = None,
        marketplace_client: Optional[MarketplaceClient] = None,
    ):
        """
        Initialize the extension manager.
        
        Args:
            extension_root: Root directory containing extensions
            plugin_router: Plugin router instance for plugin orchestration
            db_session: Database session for data management
            app_instance: FastAPI app instance for API integration
            marketplace_client: Optional marketplace client for remote installs
        """
        super().__init__()
        self.extension_root = Path(extension_root)
        self.plugin_router = plugin_router
        self.db_session = db_session
        self.app_instance = app_instance
        self.marketplace_client = marketplace_client or MarketplaceClient()
        self.name = "extension_manager"
        
        self.registry = ExtensionRegistry()
        self.validator = ExtensionValidator()
        self.dependency_resolver = DependencyResolver()
        self.resource_monitor = ResourceMonitor()
        self.health_checker = ExtensionHealthChecker(self.resource_monitor)
        self.logger = logging.getLogger("extension.manager")
        
        # Ensure extension root exists
        self.extension_root.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Extension manager initialized with root: {self.extension_root}")
    
    async def discover_extensions(self) -> Dict[str, ExtensionManifest]:
        """
        Scan extension directory and load manifests from all categories.
        
        Returns:
            Dictionary mapping extension names to their manifests
        """
        manifests = {}
        
        self.logger.info(f"Discovering extensions in {self.extension_root}")
        
        try:
            # Scan both flat structure (for backward compatibility) and categorized structure
            await self._scan_directory_for_extensions(self.extension_root, manifests)
            
        except Exception as e:
            self.logger.error(f"Failed to scan extension directory: {e}")
        
        self.logger.info(f"Discovered {len(manifests)} extensions")
        return manifests
    
    async def _scan_directory_for_extensions(self, directory: Path, manifests: Dict[str, ExtensionManifest]) -> None:
        """
        Recursively scan a directory for extensions.
        
        Args:
            directory: Directory to scan
            manifests: Dictionary to store discovered manifests
        """
        try:
            for item in directory.iterdir():
                if not item.is_dir():
                    continue
                
                # Skip metadata directories
                if item.name.startswith('__') or item.name.startswith('.'):
                    continue
                
                # Look for extension manifest in this directory
                manifest_path = item / "extension.json"
                if manifest_path.exists():
                    await self._load_extension_manifest(item, manifest_path, manifests)
                else:
                    # If no manifest here, scan subdirectories (for category structure)
                    await self._scan_directory_for_extensions(item, manifests)
                    
        except Exception as e:
            self.logger.error(f"Failed to scan directory {directory}: {e}")
    
    async def _load_extension_manifest(
        self, 
        extension_dir: Path, 
        manifest_path: Path, 
        manifests: Dict[str, ExtensionManifest]
    ) -> None:
        """
        Load and validate an extension manifest.
        
        Args:
            extension_dir: Extension directory
            manifest_path: Path to manifest file
            manifests: Dictionary to store the manifest
        """
        try:
            # Load manifest
            manifest = ExtensionManifest.from_file(manifest_path)
            
            # Validate manifest
            is_valid, errors, warnings = self.validator.validate_manifest(manifest)
            
            if not is_valid:
                self.logger.error(f"Invalid manifest for {extension_dir.name}: {'; '.join(errors)}")
                return
            
            if warnings:
                self.logger.warning(f"Manifest warnings for {extension_dir.name}: {'; '.join(warnings)}")
            
            manifests[manifest.name] = manifest
            self.logger.info(
                f"Discovered extension: {manifest.name} v{manifest.version} at {extension_dir}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to load manifest from {manifest_path}: {e}")
    
    async def load_extension(self, name: str) -> ExtensionRecord:
        """
        Load and initialize an extension.
        
        Args:
            name: Extension name to load
            
        Returns:
            ExtensionRecord for the loaded extension
            
        Raises:
            RuntimeError: If extension loading fails
        """
        self.logger.info(f"Loading extension: {name}")
        
        try:
            # Find extension directory (search in all categories)
            extension_dir = await self._find_extension_directory(name)
            if not extension_dir:
                raise RuntimeError(f"Extension directory not found for: {name}")
            
            # Load manifest
            manifest_path = extension_dir / "extension.json"
            if not manifest_path.exists():
                raise RuntimeError(f"Extension manifest not found: {manifest_path}")
            
            manifest = ExtensionManifest.from_file(manifest_path)
            
            # Check dependencies
            dependency_status = self.registry.check_dependencies(manifest)
            missing_deps = [dep for dep, available in dependency_status.items() if not available]
            if missing_deps:
                raise RuntimeError(f"Missing dependencies: {missing_deps}")
            
            # Load extension module
            extension_instance = await self._load_extension_module(extension_dir, manifest)
            
            # Register extension
            record = self.registry.register_extension(manifest, extension_instance, str(extension_dir))
            
            # Create extension context (currently unused)
            ExtensionContext(
                plugin_router=self.plugin_router,
                db_session=self.db_session,
                app_instance=self.app_instance,
            )
            
            # Initialize extension
            try:
                await extension_instance.initialize()
                self.registry.update_status(name, ExtensionStatus.ACTIVE)

                # Register for resource monitoring
                self.resource_monitor.register_extension(record)

                # Trigger extension loaded hooks with enhanced context
                await self.trigger_hook_safe(
                    HookTypes.EXTENSION_LOADED,
                    {
                        "extension_name": name,
                        "extension_version": manifest.version,
                        "extension_manifest": manifest.dict(),
                        "extension_directory": str(extension_dir),
                        "extension_category": manifest.category,
                        "extension_capabilities": manifest.capabilities.dict() if hasattr(manifest, 'capabilities') else {},
                        "resource_usage": self.resource_monitor.get_extension_usage(name)
                    }
                )

                # Trigger extension activated hooks with enhanced context
                await self.trigger_hook_safe(
                    HookTypes.EXTENSION_ACTIVATED,
                    {
                        "extension_name": name,
                        "extension_version": manifest.version,
                        "extension_instance": extension_instance,
                        "extension_manifest": manifest.dict(),
                        "activation_timestamp": record.loaded_at.isoformat() if record.loaded_at else None,
                        "has_mcp_server": hasattr(extension_instance, '_mcp_server') and extension_instance._mcp_server is not None,
                        "has_api_router": hasattr(extension_instance, '_api_router') and extension_instance._api_router is not None
                    }
                )

                # Publish lifecycle event
                try:
                    bus = get_event_bus()
                    bus.publish(
                        "extensions",
                        "loaded",
                        {"name": name, "version": manifest.version},
                        roles=["admin"],
                    )
                except Exception as exc:  # pragma: no cover - optional
                    self.logger.debug("Event publish failed: %s", exc)

                self.logger.info(f"Extension {name} loaded and initialized successfully")
                
            except Exception as e:
                self.registry.update_status(name, ExtensionStatus.ERROR, str(e))
                raise RuntimeError(f"Extension initialization failed: {e}") from e
            
            return record
            
        except Exception as e:
            self.logger.error(f"Failed to load extension {name}: {e}")
            # Update status if extension was registered
            self.registry.update_status(name, ExtensionStatus.ERROR, str(e))
            raise
    
    async def unload_extension(self, name: str) -> None:
        """
        Safely unload an extension and cleanup resources.
        
        Args:
            name: Extension name to unload
            
        Raises:
            RuntimeError: If extension unloading fails
        """
        self.logger.info(f"Unloading extension: {name}")
        
        try:
            record = self.registry.get_extension(name)
            if not record:
                raise RuntimeError(f"Extension {name} not found in registry")
            
            # Update status to unloading
            self.registry.update_status(name, ExtensionStatus.UNLOADING)
            
            # Trigger extension deactivated hooks with enhanced context
            await self.trigger_hook_safe(
                HookTypes.EXTENSION_DEACTIVATED,
                {
                    "extension_name": name,
                    "extension_version": record.manifest.version,
                    "extension_instance": record.instance,
                    "extension_manifest": record.manifest.dict(),
                    "deactivation_reason": "manual_unload",
                    "resource_usage_final": self.resource_monitor.get_extension_usage(name),
                    "uptime_seconds": (record.loaded_at and (record.loaded_at - record.loaded_at).total_seconds()) or 0
                }
            )
            
            # Shutdown extension
            if record.instance and hasattr(record.instance, 'shutdown'):
                try:
                    await record.instance.shutdown()
                except Exception as e:
                    self.logger.error(f"Error during extension shutdown: {e}")
            
            # Unregister from resource monitoring
            self.resource_monitor.unregister_extension(name)

            # Trigger extension unloaded hooks with enhanced context
            await self.trigger_hook_safe(
                HookTypes.EXTENSION_UNLOADED,
                {
                    "extension_name": name,
                    "extension_version": record.manifest.version,
                    "extension_directory": str(record.directory),
                    "extension_manifest": record.manifest.dict(),
                    "unload_timestamp": record.loaded_at.isoformat() if record.loaded_at else None,
                    "cleanup_successful": True
                }
            )

            # Unregister extension
            self.registry.unregister_extension(name)

            try:
                bus = get_event_bus()
                bus.publish(
                    "extensions",
                    "unloaded",
                    {"name": name},
                    roles=["admin"],
                )
            except Exception as exc:  # pragma: no cover - optional
                self.logger.debug("Event publish failed: %s", exc)

            self.logger.info(f"Extension {name} unloaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to unload extension {name}: {e}")
            self.registry.update_status(name, ExtensionStatus.ERROR, str(e))
            raise
    
    async def reload_extension(self, name: str) -> ExtensionRecord:
        """
        Reload an extension (for development).
        
        Args:
            name: Extension name to reload
            
        Returns:
            ExtensionRecord for the reloaded extension
        """
        self.logger.info(f"Reloading extension: {name}")
        
        # Unload if currently loaded
        if self.registry.get_extension(name):
            await self.unload_extension(name)

        # Load again
        record = await self.load_extension(name)
        try:
            bus = get_event_bus()
            bus.publish(
                "extensions",
                "reloaded",
                {"name": name},
                roles=["admin"],
            )
        except Exception as exc:  # pragma: no cover - optional
            self.logger.debug("Event publish failed: %s", exc)
        return record
    
    def get_extension_status(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get current status and health of an extension.
        
        Args:
            name: Extension name
            
        Returns:
            Status dictionary or None if extension not found
        """
        record = self.registry.get_extension(name)
        if not record:
            return None
        
        status = {
            "name": record.manifest.name,
            "version": record.manifest.version,
            "status": record.status.value,
            "loaded_at": record.loaded_at,
            "error_message": record.error_message,
            "directory": str(record.directory)
        }
        
        # Add instance status if available
        if record.instance and hasattr(record.instance, 'get_status'):
            try:
                instance_status = record.instance.get_status()
                status.update(instance_status)
            except Exception as e:
                self.logger.error(f"Failed to get instance status for {name}: {e}")
        
        return status
    
    async def load_all_extensions(self) -> Dict[str, ExtensionRecord]:
        """
        Discover and load all available extensions with proper dependency resolution.
        
        Returns:
            Dictionary mapping extension names to their records
        """
        self.logger.info("Loading all extensions")
        
        # Discover available extensions
        manifests = await self.discover_extensions()
        
        if not manifests:
            self.logger.info("No extensions found to load")
            return {}
        
        loaded_extensions = {}
        
        try:
            # Resolve loading order based on dependencies
            loading_order = self.dependency_resolver.resolve_loading_order(manifests)
            
            # Check version compatibility
            compatibility_warnings = self.dependency_resolver.check_version_compatibility(manifests)
            for warning in compatibility_warnings:
                self.logger.warning(f"Version compatibility: {warning}")
            
            # Load extensions in dependency order
            for name in loading_order:
                if name not in manifests:
                    self.logger.warning(f"Extension {name} in loading order but not in manifests")
                    continue
                
                try:
                    self.logger.info(f"Loading extension {name} ({len(loaded_extensions) + 1}/{len(manifests)})")
                    record = await self.load_extension(name)
                    loaded_extensions[name] = record
                    
                except Exception as e:
                    self.logger.error(f"Failed to load extension {name}: {e}")
                    # Continue loading other extensions even if one fails
                    continue
        
        except DependencyError as e:
            self.logger.error(f"Dependency resolution failed: {e}")
            
            # Fallback: try to load extensions without dependency resolution
            self.logger.info("Attempting to load extensions without dependency resolution")
            for name, manifest in manifests.items():
                if name not in loaded_extensions:
                    try:
                        record = await self.load_extension(name)
                        loaded_extensions[name] = record
                    except Exception as load_error:
                        self.logger.error(f"Failed to load extension {name}: {load_error}")
                        continue
        
        self.logger.info(f"Loaded {len(loaded_extensions)} out of {len(manifests)} extensions")
        return loaded_extensions
    
    async def _load_extension_module(
        self, 
        extension_dir: Path, 
        manifest: ExtensionManifest
    ) -> BaseExtension:
        """
        Load the extension Python module and create instance.
        
        Args:
            extension_dir: Extension directory path
            manifest: Extension manifest
            
        Returns:
            Extension instance
            
        Raises:
            RuntimeError: If module loading fails
        """
        try:
            # Look for __init__.py in extension directory
            init_file = extension_dir / "__init__.py"
            if not init_file.exists():
                raise RuntimeError(f"Extension __init__.py not found: {init_file}")
            
            # Load module dynamically
            module_name = f"extension_{manifest.name}"
            spec = importlib.util.spec_from_file_location(module_name, init_file)
            if not spec or not spec.loader:
                raise RuntimeError(f"Failed to create module spec for {init_file}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for extension class
            # Convention: class should be named after the extension with "Extension" suffix
            # e.g., "AdvancedAnalyticsExtension" for "advanced-analytics"
            class_name = self._get_extension_class_name(manifest.name)
            
            if not hasattr(module, class_name):
                # Fallback: look for any class that inherits from BaseExtension
                extension_classes = [
                    getattr(module, attr) for attr in dir(module)
                    if (isinstance(getattr(module, attr), type) and 
                        issubclass(getattr(module, attr), BaseExtension) and
                        getattr(module, attr) != BaseExtension)
                ]
                
                if not extension_classes:
                    raise RuntimeError(f"No extension class found in {init_file}")
                
                extension_class = extension_classes[0]
            else:
                extension_class = getattr(module, class_name)
            
            # Create extension context
            context = ExtensionContext(
                plugin_router=self.plugin_router,
                db_session=self.db_session,
                app_instance=self.app_instance
            )
            
            # Create extension instance
            extension_instance = extension_class(manifest, context)
            
            return extension_instance
            
        except Exception as e:
            self.logger.error(f"Failed to load extension module: {e}")
            raise RuntimeError(f"Module loading failed: {e}") from e
    
    def _get_extension_class_name(self, extension_name: str) -> str:
        """
        Generate expected extension class name from extension name.
        
        Args:
            extension_name: Extension name (e.g., "advanced-analytics")
            
        Returns:
            Expected class name (e.g., "AdvancedAnalyticsExtension")
        """
        # Convert kebab-case to PascalCase and add "Extension" suffix
        words = extension_name.replace("-", "_").split("_")
        class_name = "".join(word.capitalize() for word in words) + "Extension"
        return class_name
    
    def get_registry(self) -> ExtensionRegistry:
        """Get the extension registry."""
        return self.registry
    
    def get_loaded_extensions(self) -> List[ExtensionRecord]:
        """Get all loaded extensions."""
        return self.registry.get_active_extensions()
    
    def get_extension_by_name(self, name: str) -> Optional[ExtensionRecord]:
        """Get extension by name."""
        return self.registry.get_extension(name)

    async def install_extension(
        self,
        extension_id: str,
        version: str,
        source: str = "local",
        path: Optional[str] = None,
    ) -> bool:
        """Install an extension from a local path or marketplace."""
        self.logger.info(f"Installing extension {extension_id} from {source}")

        try:
            if source == "local":
                if not path:
                    raise ValueError("path required for local install")
                src = Path(path)
                dest = self.extension_root / extension_id
                if dest.exists():
                    self.logger.warning("Extension already installed")
                    return False
                shutil.copytree(src, dest)
            else:
                await self.marketplace_client.download_extension(
                    extension_id, version, self.extension_root
                )
            return True
        except Exception as e:
            self.logger.error(f"Failed to install extension {extension_id}: {e}")
            return False

    async def update_extension(
        self,
        name: str,
        version: str,
        source: str = "local",
        path: Optional[str] = None,
    ) -> bool:
        """Update an installed extension."""
        await self.remove_extension(name)
        return await self.install_extension(name, version, source, path)

    async def enable_extension(self, name: str) -> Optional[ExtensionRecord]:
        """Enable and load an extension."""
        if self.registry.get_extension(name):
            return self.registry.get_extension(name)
        return await self.load_extension(name)

    async def disable_extension(self, name: str) -> None:
        """Disable an extension and unload it."""
        if self.registry.get_extension(name):
            await self.unload_extension(name)

    async def remove_extension(self, name: str) -> bool:
        """Remove an extension from disk and the registry."""
        try:
            if self.registry.get_extension(name):
                await self.unload_extension(name)
            ext_dir = await self._find_extension_directory(name)
            if ext_dir and ext_dir.exists():
                shutil.rmtree(ext_dir)
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove extension {name}: {e}")
            return False
    
    async def start_monitoring(self) -> None:
        """Start resource monitoring for all extensions."""
        await self.resource_monitor.start_monitoring()
        self.logger.info("Extension resource monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        await self.resource_monitor.stop_monitoring()
        self.logger.info("Extension resource monitoring stopped")
    
    async def check_extension_health(self, name: str) -> HealthStatus:
        """
        Check the health of a specific extension.
        
        Args:
            name: Extension name
            
        Returns:
            HealthStatus value
        """
        record = self.registry.get_extension(name)
        if not record:
            return HealthStatus.RED
        
        return await self.health_checker.check_extension_health(record)
    
    async def check_all_extensions_health(self) -> Dict[str, HealthStatus]:
        """
        Check health of all loaded extensions.
        
        Returns:
            Dictionary mapping extension names to health status
        """
        loaded_extensions = {
            name: record for name, record in 
            [(r.manifest.name, r) for r in self.registry.get_active_extensions()]
        }
        
        return await self.health_checker.check_all_extensions_health(loaded_extensions)
    
    def get_extension_resource_usage(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get resource usage for a specific extension.
        
        Args:
            name: Extension name
            
        Returns:
            Resource usage dictionary or None if not found
        """
        usage = self.resource_monitor.get_extension_usage(name)
        if not usage:
            return None
        
        return {
            "memory_mb": usage.memory_mb,
            "cpu_percent": usage.cpu_percent,
            "disk_mb": usage.disk_mb,
            "network_bytes_sent": usage.network_bytes_sent,
            "network_bytes_recv": usage.network_bytes_recv,
            "uptime_seconds": usage.uptime_seconds
        }
    
    def get_all_resource_usage(self) -> Dict[str, Dict[str, Any]]:
        """Get resource usage for all extensions."""
        all_usage = self.resource_monitor.get_all_usage()
        
        return {
            name: {
                "memory_mb": usage.memory_mb,
                "cpu_percent": usage.cpu_percent,
                "disk_mb": usage.disk_mb,
                "network_bytes_sent": usage.network_bytes_sent,
                "network_bytes_recv": usage.network_bytes_recv,
                "uptime_seconds": usage.uptime_seconds
            }
            for name, usage in all_usage.items()
        }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary of the extension system."""
        return self.health_checker.get_health_summary()
    
    async def get_extension_hook_stats(self, name: str) -> Dict[str, Any]:
        """
        Get hook statistics for a specific extension.
        
        Args:
            name: Extension name
            
        Returns:
            Hook statistics dictionary
        """
        record = self.registry.get_extension(name)
        if not record or not record.instance:
            return {"error": "Extension not found or not loaded"}
        
        # Get hook stats from the extension instance if it has hook capabilities
        if hasattr(record.instance, 'get_hook_stats'):
            try:
                return record.instance.get_hook_stats()
            except Exception as e:
                self.logger.error(f"Failed to get hook stats for {name}: {e}")
                return {"error": str(e)}
        
        return {"hooks_enabled": False, "message": "Extension does not support hooks"}
    
    async def get_all_extension_hook_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get hook statistics for all loaded extensions."""
        stats = {}
        for record in self.registry.get_active_extensions():
            stats[record.manifest.name] = await self.get_extension_hook_stats(record.manifest.name)
        return stats
    
    async def trigger_extension_hook(
        self, 
        extension_name: str, 
        hook_type: str, 
        data: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger a hook on a specific extension.
        
        Args:
            extension_name: Name of the extension
            hook_type: Type of hook to trigger
            data: Data to pass to the hook
            user_context: User context information
            
        Returns:
            Hook execution result
        """
        record = self.registry.get_extension(extension_name)
        if not record or not record.instance:
            return {"error": f"Extension {extension_name} not found or not loaded"}
        
        try:
            # Check if extension supports hook handling
            if hasattr(record.instance, 'handle_hook'):
                result = await record.instance.handle_hook(hook_type, data, user_context)
                
                # Trigger global extension hook event
                await self.trigger_hook_safe(
                    HookTypes.EXTENSION_ACTIVATED if hook_type == "activate" else hook_type,
                    {
                        "extension_name": extension_name,
                        "hook_type": hook_type,
                        "hook_data": data,
                        "hook_result": result,
                        "user_context": user_context
                    }
                )
                
                return {"success": True, "result": result}
            else:
                return {"error": f"Extension {extension_name} does not support hook handling"}
                
        except Exception as e:
            self.logger.error(f"Failed to trigger hook {hook_type} on extension {extension_name}: {e}")
            return {"error": str(e)}
    
    async def trigger_all_extension_hooks(
        self,
        hook_type: str,
        data: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None,
        filter_extensions: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Trigger a hook on all loaded extensions or a filtered subset.
        
        Args:
            hook_type: Type of hook to trigger
            data: Data to pass to hooks
            user_context: User context information
            filter_extensions: Optional list of extension names to filter
            
        Returns:
            Dictionary mapping extension names to their hook results
        """
        results = {}
        active_extensions = self.registry.get_active_extensions()
        
        for record in active_extensions:
            extension_name = record.manifest.name
            
            # Apply filter if provided
            if filter_extensions and extension_name not in filter_extensions:
                continue
            
            try:
                result = await self.trigger_extension_hook(
                    extension_name, hook_type, data, user_context
                )
                results[extension_name] = result
                
            except Exception as e:
                self.logger.error(f"Failed to trigger hook on extension {extension_name}: {e}")
                results[extension_name] = {"error": str(e)}
        
        return results
    
    async def register_extension_lifecycle_hooks(self) -> None:
        """
        Register standard lifecycle hooks for the extension manager.
        
        This method sets up hooks that are triggered during extension lifecycle events.
        """
        # Register hook for when extensions are loaded
        await self.register_hook(
            HookTypes.EXTENSION_LOADED,
            self._on_extension_loaded_hook,
            priority=25,  # High priority
            source_name="extension_manager_lifecycle"
        )
        
        # Register hook for when extensions are activated
        await self.register_hook(
            HookTypes.EXTENSION_ACTIVATED,
            self._on_extension_activated_hook,
            priority=25,
            source_name="extension_manager_lifecycle"
        )
        
        # Register hook for when extensions are deactivated
        await self.register_hook(
            HookTypes.EXTENSION_DEACTIVATED,
            self._on_extension_deactivated_hook,
            priority=25,
            source_name="extension_manager_lifecycle"
        )
        
        # Register hook for when extensions are unloaded
        await self.register_hook(
            HookTypes.EXTENSION_UNLOADED,
            self._on_extension_unloaded_hook,
            priority=25,
            source_name="extension_manager_lifecycle"
        )
        
        # Register hook for extension errors
        await self.register_hook(
            HookTypes.EXTENSION_ERROR,
            self._on_extension_error_hook,
            priority=10,  # Highest priority for error handling
            source_name="extension_manager_error_handler"
        )
        
        self.logger.info("Extension manager lifecycle hooks registered")
    
    async def _on_extension_loaded_hook(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle extension loaded hook."""
        extension_name = context.get("extension_name")
        
        # Update resource monitoring
        if extension_name:
            record = self.registry.get_extension(extension_name)
            if record:
                self.resource_monitor.register_extension(record)
        
        return {
            "manager": "extension_manager",
            "action": "extension_loaded",
            "extension_name": extension_name,
            "monitoring_enabled": True
        }
    
    async def _on_extension_activated_hook(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle extension activated hook."""
        extension_name = context.get("extension_name")
        
        # Start health monitoring
        if extension_name:
            try:
                health_status = await self.check_extension_health(extension_name)
                self.logger.info(f"Extension {extension_name} health status: {health_status}")
            except Exception as e:
                self.logger.warning(f"Failed to check health for {extension_name}: {e}")
        
        return {
            "manager": "extension_manager",
            "action": "extension_activated",
            "extension_name": extension_name,
            "health_check_performed": True
        }
    
    async def _on_extension_deactivated_hook(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle extension deactivated hook."""
        extension_name = context.get("extension_name")
        deactivation_reason = context.get("deactivation_reason", "unknown")
        
        # Log deactivation for audit trail
        self.logger.info(f"Extension {extension_name} deactivated: {deactivation_reason}")
        
        return {
            "manager": "extension_manager",
            "action": "extension_deactivated",
            "extension_name": extension_name,
            "reason": deactivation_reason,
            "audit_logged": True
        }
    
    async def _on_extension_unloaded_hook(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle extension unloaded hook."""
        extension_name = context.get("extension_name")
        
        # Clean up monitoring resources
        if extension_name:
            self.resource_monitor.unregister_extension(extension_name)
        
        return {
            "manager": "extension_manager",
            "action": "extension_unloaded",
            "extension_name": extension_name,
            "monitoring_cleaned": True
        }
    
    async def _on_extension_error_hook(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle extension error hook."""
        extension_name = context.get("extension_name")
        error_message = context.get("error", "Unknown error")
        
        # Update extension status
        if extension_name:
            self.registry.update_status(extension_name, ExtensionStatus.ERROR, error_message)
        
        # Publish error event
        try:
            bus = get_event_bus()
            bus.publish(
                "extensions",
                "error",
                {
                    "name": extension_name,
                    "error": error_message,
                    "timestamp": context.get("timestamp")
                },
                roles=["admin"]
            )
        except Exception as e:
            self.logger.debug(f"Failed to publish extension error event: {e}")
        
        return {
            "manager": "extension_manager",
            "action": "extension_error_handled",
            "extension_name": extension_name,
            "error_logged": True,
            "status_updated": True
        }
    
    async def setup_ai_powered_hooks(self) -> None:
        """
        Set up AI-powered hooks for intelligent extension management.
        
        These hooks use AI capabilities to provide intelligent insights
        and automation for extension management.
        """
        # Register AI-powered extension recommendation hook
        await self.register_hook(
            "ai_extension_recommendation",
            self._ai_recommend_extensions,
            priority=50,
            source_name="extension_manager_ai"
        )
        
        # Register AI-powered extension health analysis hook
        await self.register_hook(
            "ai_health_analysis",
            self._ai_analyze_extension_health,
            priority=50,
            source_name="extension_manager_ai"
        )
        
        # Register AI-powered extension optimization hook
        await self.register_hook(
            "ai_extension_optimization",
            self._ai_optimize_extensions,
            priority=50,
            source_name="extension_manager_ai"
        )
        
        self.logger.info("AI-powered extension hooks registered")
    
    async def _ai_recommend_extensions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered extension recommendation based on user behavior and context.
        
        Args:
            context: Context data including user preferences and usage patterns
            
        Returns:
            Extension recommendations
        """
        try:
            user_context = context.get("user_context", {})
            current_extensions = [r.manifest.name for r in self.registry.get_active_extensions()]
            
            # Simple AI recommendation logic (can be enhanced with ML models)
            recommendations = []
            
            # Analyze user's current extensions and suggest complementary ones
            if "analytics" in str(current_extensions).lower():
                recommendations.append({
                    "extension": "advanced-visualization",
                    "reason": "Complements analytics with advanced charts",
                    "confidence": 0.8
                })
            
            if "database" in str(current_extensions).lower():
                recommendations.append({
                    "extension": "query-optimizer",
                    "reason": "Optimizes database queries for better performance",
                    "confidence": 0.7
                })
            
            return {
                "recommendations": recommendations,
                "analysis_method": "rule_based_ai",
                "context_analyzed": len(user_context) > 0
            }
            
        except Exception as e:
            self.logger.error(f"AI extension recommendation failed: {e}")
            return {"error": str(e), "recommendations": []}
    
    async def _ai_analyze_extension_health(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered analysis of extension health and performance.
        
        Args:
            context: Context data including extension metrics
            
        Returns:
            Health analysis results
        """
        try:
            extension_name = context.get("extension_name")
            if not extension_name:
                return {"error": "Extension name required for health analysis"}
            
            # Get resource usage data
            usage_data = self.get_extension_resource_usage(extension_name)
            if not usage_data:
                return {"error": f"No usage data available for {extension_name}"}
            
            # AI-powered health analysis
            health_score = 100.0
            issues = []
            recommendations = []
            
            # Analyze memory usage
            if usage_data["memory_mb"] > 500:  # High memory usage
                health_score -= 20
                issues.append("High memory usage detected")
                recommendations.append("Consider optimizing memory usage or increasing system memory")
            
            # Analyze CPU usage
            if usage_data["cpu_percent"] > 80:  # High CPU usage
                health_score -= 25
                issues.append("High CPU usage detected")
                recommendations.append("Review extension algorithms for optimization opportunities")
            
            # Analyze uptime patterns
            if usage_data["uptime_seconds"] < 3600:  # Less than 1 hour uptime
                health_score -= 10
                issues.append("Frequent restarts detected")
                recommendations.append("Investigate stability issues and error logs")
            
            return {
                "extension_name": extension_name,
                "health_score": max(0, health_score),
                "issues": issues,
                "recommendations": recommendations,
                "analysis_timestamp": context.get("timestamp"),
                "ai_analysis": True
            }
            
        except Exception as e:
            self.logger.error(f"AI health analysis failed: {e}")
            return {"error": str(e)}
    
    async def _ai_optimize_extensions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered extension optimization suggestions.
        
        Args:
            context: Context data including system performance metrics
            
        Returns:
            Optimization suggestions
        """
        try:
            all_usage = self.get_all_resource_usage()
            optimizations = []
            
            # Analyze overall resource usage patterns
            total_memory = sum(usage["memory_mb"] for usage in all_usage.values())
            total_cpu = sum(usage["cpu_percent"] for usage in all_usage.values())
            
            if total_memory > 2000:  # High total memory usage
                # Find memory-heavy extensions
                memory_heavy = [
                    name for name, usage in all_usage.items()
                    if usage["memory_mb"] > 200
                ]
                
                optimizations.append({
                    "type": "memory_optimization",
                    "description": "High system memory usage detected",
                    "affected_extensions": memory_heavy,
                    "suggestion": "Consider disabling unused extensions or optimizing memory usage",
                    "priority": "high"
                })
            
            if total_cpu > 200:  # High total CPU usage
                # Find CPU-heavy extensions
                cpu_heavy = [
                    name for name, usage in all_usage.items()
                    if usage["cpu_percent"] > 50
                ]
                
                optimizations.append({
                    "type": "cpu_optimization",
                    "description": "High system CPU usage detected",
                    "affected_extensions": cpu_heavy,
                    "suggestion": "Review extension algorithms and consider load balancing",
                    "priority": "medium"
                })
            
            # Suggest extension consolidation if many similar extensions are loaded
            extension_categories = {}
            for record in self.registry.get_active_extensions():
                category = getattr(record.manifest, 'category', 'unknown')
                if category not in extension_categories:
                    extension_categories[category] = []
                extension_categories[category].append(record.manifest.name)
            
            for category, extensions in extension_categories.items():
                if len(extensions) > 3:  # Many extensions in same category
                    optimizations.append({
                        "type": "consolidation",
                        "description": f"Multiple {category} extensions detected",
                        "affected_extensions": extensions,
                        "suggestion": f"Consider consolidating {category} functionality",
                        "priority": "low"
                    })
            
            return {
                "optimizations": optimizations,
                "system_metrics": {
                    "total_memory_mb": total_memory,
                    "total_cpu_percent": total_cpu,
                    "active_extensions": len(all_usage)
                },
                "ai_analysis": True
            }
            
        except Exception as e:
            self.logger.error(f"AI optimization analysis failed: {e}")
            return {"error": str(e), "optimizations": []}
    
    async def enable_mcp_hooks(self) -> None:
        """
        Enable MCP-specific hooks for extensions with MCP capabilities.
        
        This method sets up hooks that integrate with the MCP system
        for AI-powered extension capabilities.
        """
        # Register MCP tool registration hook
        await self.register_hook(
            "mcp_tool_registered",
            self._on_mcp_tool_registered,
            priority=50,
            source_name="extension_manager_mcp"
        )
        
        # Register MCP tool call hook
        await self.register_hook(
            "mcp_tool_called",
            self._on_mcp_tool_called,
            priority=50,
            source_name="extension_manager_mcp"
        )
        
        # Register MCP service discovery hook
        await self.register_hook(
            "mcp_service_discovered",
            self._on_mcp_service_discovered,
            priority=50,
            source_name="extension_manager_mcp"
        )
        
        self.logger.info("MCP-specific extension hooks enabled")
    
    async def _on_mcp_tool_registered(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tool registration from extensions."""
        extension_name = context.get("extension_name")
        tool_name = context.get("tool_name")
        
        self.logger.info(f"MCP tool {tool_name} registered by extension {extension_name}")
        
        return {
            "manager": "extension_manager",
            "action": "mcp_tool_registered",
            "extension_name": extension_name,
            "tool_name": tool_name,
            "registered_successfully": True
        }
    
    async def _on_mcp_tool_called(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tool calls from extensions."""
        extension_name = context.get("extension_name")
        tool_name = context.get("tool_name")
        execution_time = context.get("execution_time_ms", 0)
        
        # Track tool usage statistics
        self.logger.debug(f"MCP tool {tool_name} called by {extension_name} in {execution_time}ms")
        
        return {
            "manager": "extension_manager",
            "action": "mcp_tool_called",
            "extension_name": extension_name,
            "tool_name": tool_name,
            "execution_time_ms": execution_time,
            "tracked": True
        }
    
    async def _on_mcp_service_discovered(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP service discovery events."""
        service_name = context.get("service_name")
        tools_count = len(context.get("tools", []))
        
        self.logger.info(f"MCP service {service_name} discovered with {tools_count} tools")
        
        return {
            "manager": "extension_manager",
            "action": "mcp_service_discovered",
            "service_name": service_name,
            "tools_count": tools_count,
            "discovery_successful": True
        }
    
    async def initialize_hook_system(self) -> None:
        """
        Initialize the complete hook system for the extension manager.
        
        This method sets up all hook capabilities including lifecycle hooks,
        AI-powered hooks, and MCP integration hooks.
        """
        try:
            # Register lifecycle hooks
            await self.register_extension_lifecycle_hooks()
            
            # Set up AI-powered hooks
            await self.setup_ai_powered_hooks()
            
            # Enable MCP hooks
            await self.enable_mcp_hooks()
            
            self.logger.info("Extension manager hook system initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize hook system: {e}")
            raise
    
    async def shutdown_hook_system(self) -> None:
        """
        Shutdown the hook system and clean up all registered hooks.
        """
        try:
            # Clear all hooks registered by this manager
            if self.hook_manager:
                cleared_count = await self.hook_manager.clear_hooks_by_source(
                    "extensionmanager", 
                    "extension_manager"
                )
                self.logger.info(f"Cleared {cleared_count} extension manager hooks")
            
        except Exception as e:
            self.logger.error(f"Failed to shutdown hook system: {e}")
    
    async def get_hook_integration_status(self) -> Dict[str, Any]:
        """
        Get the status of hook integration for the extension manager.
        
        Returns:
            Dictionary with hook integration status information
        """
        try:
            hook_stats = self.get_hook_stats()
            active_extensions = self.registry.get_active_extensions()
            
            # Count extensions with hook capabilities
            hook_enabled_extensions = 0
            for record in active_extensions:
                if hasattr(record.instance, 'handle_hook'):
                    hook_enabled_extensions += 1
            
            return {
                "hook_system_enabled": self.are_hooks_enabled(),
                "manager_hooks_registered": hook_stats.get("registered_hooks", 0),
                "manager_hook_types": hook_stats.get("hook_types", []),
                "total_extensions": len(active_extensions),
                "hook_enabled_extensions": hook_enabled_extensions,
                "hook_coverage_percent": (hook_enabled_extensions / len(active_extensions) * 100) if active_extensions else 0,
                "ai_hooks_available": "ai_extension_recommendation" in hook_stats.get("hook_types", []),
                "mcp_hooks_available": "mcp_tool_registered" in hook_stats.get("hook_types", [])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get hook integration status: {e}")
            return {"error": str(e)}
    
    async def _find_extension_directory(self, name: str) -> Optional[Path]:
        """
        record = self.registry.get_extension(extension_name)
        if not record or not record.instance:
            return {"error": "Extension not found or not loaded"}
        
        # Check if extension supports hooks
        if hasattr(record.instance, 'trigger_hooks'):
            try:
                summary = await record.instance.trigger_hooks(hook_type, data, user_context)
                return {
                    "success": True,
                    "hook_type": hook_type,
                    "total_hooks": summary.total_hooks,
                    "successful_hooks": summary.successful_hooks,
                    "failed_hooks": summary.failed_hooks,
                    "execution_time_ms": summary.total_execution_time_ms
                }
            except Exception as e:
                self.logger.error(f"Failed to trigger hook {hook_type} on {extension_name}: {e}")
                return {"error": str(e)}
        
        return {"error": "Extension does not support hooks"}
    
    def get_extension_monitoring_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive monitoring summary including hooks and resources.
        
        Returns:
            Monitoring summary dictionary
        """
        loaded_extensions = self.registry.get_active_extensions()
        
        summary = {
            "total_extensions": len(loaded_extensions),
            "health_summary": self.get_health_summary(),
            "resource_usage": self.get_all_resource_usage(),
            "hook_manager_stats": self.get_hook_stats(),
            "extensions": {}
        }
        
        for record in loaded_extensions:
            ext_name = record.manifest.name
            summary["extensions"][ext_name] = {
                "status": record.status.value,
                "version": record.manifest.version,
                "loaded_at": record.loaded_at.isoformat() if record.loaded_at else None,
                "has_hooks": hasattr(record.instance, 'trigger_hooks'),
                "has_mcp": hasattr(record.instance, '_mcp_server') and record.instance._mcp_server is not None
            }
        
        return summary
    
    def get_dependency_tree(self) -> Dict[str, Any]:
        """
        Get the dependency tree for all discovered extensions.
        
        Returns:
            Dictionary representing the dependency tree
        """
        # This requires discovering extensions first
        try:
            import asyncio
            manifests = asyncio.run(self.discover_extensions())
            return self.dependency_resolver.get_dependency_tree(manifests)
        except Exception as e:
            self.logger.error(f"Failed to get dependency tree: {e}")
            return {}
    
    async def _find_extension_directory(self, name: str) -> Optional[Path]:
        """
        Find the directory for an extension by name, searching all categories.
        
        Args:
            name: Extension name to find
            
        Returns:
            Path to extension directory or None if not found
        """
        # First try direct lookup (backward compatibility)
        direct_path = self.extension_root / name
        if direct_path.exists() and (direct_path / "extension.json").exists():
            return direct_path
        
        # Search in all category directories
        try:
            for category_dir in self.extension_root.iterdir():
                if not category_dir.is_dir() or category_dir.name.startswith('__'):
                    continue
                
                # Look for extension in this category
                extension_path = category_dir / name
                if extension_path.exists() and (extension_path / "extension.json").exists():
                    return extension_path
                
                # Also check if the directory name matches (for different naming patterns)
                for item in category_dir.iterdir():
                    if not item.is_dir():
                        continue
                    
                    manifest_path = item / "extension.json"
                    if manifest_path.exists():
                        try:
                            manifest = ExtensionManifest.from_file(manifest_path)
                            if manifest.name == name:
                                return item
                        except Exception:
                            continue
        
        except Exception as e:
            self.logger.error(f"Error searching for extension {name}: {e}")
        
        return None



# Global extension manager instance
_extension_manager: Optional[ExtensionManager] = None


def get_extension_manager() -> Optional[ExtensionManager]:
    """Get the global extension manager instance."""
    return _extension_manager


def initialize_extension_manager(
    extension_root: Path,
    plugin_router: PluginRouter,
    db_session: Any = None,
    app_instance: Any = None
) -> ExtensionManager:
    """
    Initialize the global extension manager.
    
    Args:
        extension_root: Root directory containing extensions
        plugin_router: Plugin router instance
        db_session: Database session
        app_instance: FastAPI app instance
        
    Returns:
        ExtensionManager instance
    """
    global _extension_manager
    _extension_manager = ExtensionManager(
        extension_root=extension_root,
        plugin_router=plugin_router,
        db_session=db_session,
        app_instance=app_instance
    )
    return _extension_manager


__all__ = [
    "ExtensionManager",
    "get_extension_manager",
    "initialize_extension_manager",
    "HealthStatus",
    "MarketplaceClient",
]