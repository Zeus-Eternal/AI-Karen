"""
Extension manager for discovery, loading, and lifecycle management.
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_karen_engine.plugins.router import PluginRouter

from .base import BaseExtension
from .models import (
    ExtensionContext, 
    ExtensionManifest, 
    ExtensionRecord, 
    ExtensionStatus
)
from .registry import ExtensionRegistry
from .validator import ExtensionValidator
from .dependency_resolver import DependencyResolver, DependencyError
from .resource_monitor import ResourceMonitor, ExtensionHealthChecker


class ExtensionManager:
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
        app_instance: Any = None
    ):
        """
        Initialize the extension manager.
        
        Args:
            extension_root: Root directory containing extensions
            plugin_router: Plugin router instance for plugin orchestration
            db_session: Database session for data management
            app_instance: FastAPI app instance for API integration
        """
        self.extension_root = Path(extension_root)
        self.plugin_router = plugin_router
        self.db_session = db_session
        self.app_instance = app_instance
        
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
            self.logger.debug(f"Discovered extension: {manifest.name} v{manifest.version} at {extension_dir}")
            
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
            
            # Shutdown extension
            if record.instance and hasattr(record.instance, 'shutdown'):
                try:
                    await record.instance.shutdown()
                except Exception as e:
                    self.logger.error(f"Error during extension shutdown: {e}")
            
            # Unregister from resource monitoring
            self.resource_monitor.unregister_extension(name)
            
            # Unregister extension
            self.registry.unregister_extension(name)
            
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
        return await self.load_extension(name)
    
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
    
    async def start_monitoring(self) -> None:
        """Start resource monitoring for all extensions."""
        await self.resource_monitor.start_monitoring()
        self.logger.info("Extension resource monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        await self.resource_monitor.stop_monitoring()
        self.logger.info("Extension resource monitoring stopped")
    
    async def check_extension_health(self, name: str) -> bool:
        """
        Check the health of a specific extension.
        
        Args:
            name: Extension name
            
        Returns:
            True if healthy, False otherwise
        """
        record = self.registry.get_extension(name)
        if not record:
            return False
        
        return await self.health_checker.check_extension_health(record)
    
    async def check_all_extensions_health(self) -> Dict[str, bool]:
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
]