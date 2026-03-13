"""
Extension Lifecycle Manager - Comprehensive extension lifecycle management for CoPilot system.

This module provides complete lifecycle management for extensions including:
- Extension discovery and registration
- Extension loading and unloading with dependency resolution
- Extension state management and transitions
- Extension health monitoring and error recovery
- Extension lifecycle event handling
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable, Union

from ai_karen_engine.extension_host import (
    ExtensionManager, 
    ExtensionLoader, 
    ExtensionRegistry, 
    ExtensionRunner,
    ExtensionManifest,
    ExtensionRecord,
    ExtensionStatus,
    ExtensionContext,
    HookPoint,
    HookContext,
    ExtensionHostConfig,
    ExtensionConfigManager
)
from ai_karen_engine.extension_host.dependency_resolver import DependencyResolver
from ai_karen_engine.extension_host.resource_monitor import ResourceMonitor, ExtensionHealthChecker
from ai_karen_engine.hooks.hook_types import HookTypes
from ai_karen_engine.database.client import get_db_session_context
from ai_karen_engine.database.models import Extension, ExtensionUsage, ExtensionHealth, ExtensionDependency


class ExtensionLifecycleState(Enum):
    """Extension lifecycle states."""
    
    DISCOVERED = "discovered"
    LOADING = "loading"
    LOADED = "loaded"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    DEACTIVATING = "deactivating"
    INACTIVE = "inactive"
    ERROR = "error"
    UNLOADING = "unloading"
    UNLOADED = "unloaded"


class ExtensionLifecycleEvent:
    """Extension lifecycle event data."""
    
    def __init__(
        self,
        extension_id: str,
        event_type: str,
        timestamp: datetime,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None
    ):
        self.extension_id = extension_id
        self.event_type = event_type
        self.timestamp = timestamp
        self.data = data or {}
        self.error = error


class ExtensionLifecycleManager:
    """
    Comprehensive extension lifecycle manager for CoPilot system.
    
    Provides complete lifecycle management including discovery, loading,
    dependency resolution, health monitoring, and error recovery.
    """
    
    def __init__(
        self,
        extensions_dir: Union[str, Path],
        config_manager: Optional[ExtensionConfigManager] = None,
        db_session: Optional[Any] = None,
        app_instance: Optional[Any] = None
    ):
        """
        Initialize the extension lifecycle manager.
        
        Args:
            extensions_dir: Directory containing extensions
            config_manager: Extension configuration manager
            db_session: Database session for persistence
            app_instance: FastAPI app instance
        """
        self.extensions_dir = Path(extensions_dir)
        self.config_manager = config_manager or ExtensionConfigManager()
        self.db_session = db_session
        self.app_instance = app_instance
        
        # Core components
        self.extension_manager = ExtensionManager(
            extension_root=self.extensions_dir,
            plugin_router=None,
            db_session=self.db_session,
            app_instance=self.app_instance,
            use_new_architecture=True
        )
        
        # State tracking
        self.extension_states: Dict[str, ExtensionLifecycleState] = {}
        self.extension_load_times: Dict[str, datetime] = {}
        self.extension_error_counts: Dict[str, int] = {}
        
        # Event handling
        self.lifecycle_listeners: List[Callable[[ExtensionLifecycleEvent], None]] = []
        self.lifecycle_events: List[ExtensionLifecycleEvent] = []
        
        # Health and recovery
        self.health_checker = ExtensionHealthChecker(
            resource_monitor=ResourceMonitor()
        )
        
        # Dependency management
        self.dependency_resolver = DependencyResolver()
        
        # Configuration
        self.config = self.config_manager.get_config()
        
        self.logger = logging.getLogger("extension.lifecycle_manager")
        self.logger.info(f"Extension lifecycle manager initialized for {self.extensions_dir}")
    
    async def initialize(self) -> None:
        """
        Initialize the extension lifecycle manager.
        
        Discovers extensions, resolves dependencies, and loads them
        in the correct order with proper error handling.
        """
        self.logger.info("Initializing extension lifecycle manager")
        
        try:
            # Start resource monitoring
            await self.health_checker.resource_monitor.start_monitoring()
            
            # Discover extensions
            await self.discover_extensions()
            
            # Load all extensions with dependency resolution
            await self.load_all_extensions()
            
            # Start health monitoring
            await self.start_health_monitoring()
            
            self.logger.info("Extension lifecycle manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize extension lifecycle manager: {e}")
            raise
    
    async def shutdown(self) -> None:
        """
        Shutdown the extension lifecycle manager.
        
        Unloads all extensions and stops monitoring.
        """
        self.logger.info("Shutting down extension lifecycle manager")
        
        try:
            # Stop health monitoring
            await self.stop_health_monitoring()
            
            # Unload all extensions
            await self.unload_all_extensions()
            
            # Stop resource monitoring
            await self.health_checker.resource_monitor.stop_monitoring()
            
            self.logger.info("Extension lifecycle manager shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during extension lifecycle manager shutdown: {e}")
    
    async def discover_extensions(self) -> Dict[str, ExtensionManifest]:
        """
        Discover all extensions in the extensions directory.
        
        Returns:
            Dictionary mapping extension names to their manifests
        """
        self.logger.info("Discovering extensions")
        
        try:
            manifests = await self.extension_manager.discover_extensions()
            
            # Update states and emit events
            for name, manifest in manifests.items():
                self.extension_states[name] = ExtensionLifecycleState.DISCOVERED
                await self._emit_lifecycle_event(
                    extension_id=name,
                    event_type="discovered",
                    data={"manifest": manifest.to_dict()}
                )
            
            self.logger.info(f"Discovered {len(manifests)} extensions")
            return manifests
            
        except Exception as e:
            self.logger.error(f"Failed to discover extensions: {e}")
            return {}
    
    async def load_all_extensions(self) -> Dict[str, ExtensionRecord]:
        """
        Load all discovered extensions with dependency resolution.
        
        Returns:
            Dictionary mapping extension names to their records
        """
        self.logger.info("Loading all extensions with dependency resolution")
        
        try:
            # Get discovered extensions
            manifests = await self.discover_extensions()
            
            if not manifests:
                self.logger.warning("No extensions discovered to load")
                return {}
            
            # Resolve loading order with dependencies
            loading_order = self.dependency_resolver.resolve_loading_order(manifests)
            
            # Load extensions in order
            loaded_extensions = {}
            failed_extensions = []
            
            for i, extension_name in enumerate(loading_order, 1):
                if extension_name not in manifests:
                    self.logger.warning(f"Extension {extension_name} in loading order but not discovered")
                    continue
                
                try:
                    self.logger.info(f"Loading extension {extension_name} ({i}/{len(loading_order)})")
                    
                    # Update state
                    self.extension_states[extension_name] = ExtensionLifecycleState.LOADING
                    await self._emit_lifecycle_event(
                        extension_id=extension_name,
                        event_type="loading_started"
                    )
                    
                    # Load the extension
                    record = await self.extension_manager.load_extension(extension_name)
                    
                    if record:
                        loaded_extensions[extension_name] = record
                        self.extension_states[extension_name] = ExtensionLifecycleState.LOADED
                        self.extension_load_times[extension_name] = datetime.now(timezone.utc)
                        
                        await self._emit_lifecycle_event(
                            extension_id=extension_name,
                            event_type="loaded",
                            data={"record": record.to_dict()}
                        )
                        
                        # Initialize the extension
                        await self._initialize_extension(extension_name, record)
                        
                    else:
                        failed_extensions.append(extension_name)
                        self.extension_states[extension_name] = ExtensionLifecycleState.ERROR
                        self.extension_error_counts[extension_name] = self.extension_error_counts.get(extension_name, 0) + 1
                        
                        await self._emit_lifecycle_event(
                            extension_id=extension_name,
                            event_type="load_failed",
                            error=Exception("Extension load returned None")
                        )
                
                except Exception as e:
                    failed_extensions.append(extension_name)
                    self.extension_states[extension_name] = ExtensionLifecycleState.ERROR
                    self.extension_error_counts[extension_name] = self.extension_error_counts.get(extension_name, 0) + 1
                    
                    self.logger.error(f"Failed to load extension {extension_name}: {e}")
                    
                    await self._emit_lifecycle_event(
                        extension_id=extension_name,
                        event_type="load_failed",
                        error=e,
                        data={"error_details": str(e)}
                    )
            
            # Log results
            self.logger.info(f"Loaded {len(loaded_extensions)}/{len(manifests)} extensions successfully")
            
            if failed_extensions:
                self.logger.warning(f"Failed to load {len(failed_extensions)} extensions: {failed_extensions}")
            
            # Persist loading results
            await self._persist_loading_results(loaded_extensions, failed_extensions)
            
            return loaded_extensions
            
        except Exception as e:
            self.logger.error(f"Failed to load all extensions: {e}")
            return {}
    
    async def load_extension(self, extension_name: str) -> Optional[ExtensionRecord]:
        """
        Load a specific extension by name.
        
        Args:
            extension_name: Name of the extension to load
            
        Returns:
            Extension record if successful, None otherwise
        """
        self.logger.info(f"Loading extension {extension_name}")
        
        try:
            # Check if already loaded
            if self.is_extension_loaded(extension_name):
                self.logger.warning(f"Extension {extension_name} is already loaded")
                return self.extension_manager.get_extension_by_name(extension_name)
            
            # Update state
            self.extension_states[extension_name] = ExtensionLifecycleState.LOADING
            await self._emit_lifecycle_event(
                extension_id=extension_name,
                event_type="loading_started"
            )
            
            # Load the extension
            record = await self.extension_manager.load_extension(extension_name)
            
            if record:
                self.extension_states[extension_name] = ExtensionLifecycleState.LOADED
                self.extension_load_times[extension_name] = datetime.now(timezone.utc)
                
                await self._emit_lifecycle_event(
                    extension_id=extension_name,
                    event_type="loaded",
                    data={"record": record.to_dict()}
                )
                
                # Initialize the extension
                await self._initialize_extension(extension_name, record)
                
                # Register for resource monitoring
                self.health_checker.resource_monitor.register_extension(record)
                
                # Persist to database
                await self._persist_extension_record(record)
                
                self.logger.info(f"Extension {extension_name} loaded successfully")
                return record
            else:
                self.extension_states[extension_name] = ExtensionLifecycleState.ERROR
                self.extension_error_counts[extension_name] = self.extension_error_counts.get(extension_name, 0) + 1
                
                await self._emit_lifecycle_event(
                    extension_id=extension_name,
                    event_type="load_failed",
                    error=Exception("Extension load returned None")
                )
                
                return None
                
        except Exception as e:
            self.extension_states[extension_name] = ExtensionLifecycleState.ERROR
            self.extension_error_counts[extension_name] = self.extension_error_counts.get(extension_name, 0) + 1
            
            self.logger.error(f"Failed to load extension {extension_name}: {e}")
            
            await self._emit_lifecycle_event(
                extension_id=extension_name,
                event_type="load_failed",
                error=e,
                data={"error_details": str(e)}
            )
            
            return None
    
    async def unload_extension(self, extension_name: str) -> bool:
        """
        Unload a specific extension by name.
        
        Args:
            extension_name: Name of the extension to unload
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Unloading extension {extension_name}")
        
        try:
            # Check if extension is loaded
            if not self.is_extension_loaded(extension_name):
                self.logger.warning(f"Extension {extension_name} is not loaded")
                return False
            
            # Update state
            self.extension_states[extension_name] = ExtensionLifecycleState.UNLOADING
            await self._emit_lifecycle_event(
                extension_id=extension_name,
                event_type="unloading_started"
            )
            
            # Get dependent extensions
            dependents = self.get_dependent_extensions(extension_name)
            if dependents:
                self.logger.warning(f"Extension {extension_name} has dependents: {dependents}")
                
                # Option 1: Unload dependents first
                for dependent in dependents:
                    if self.is_extension_loaded(dependent):
                        await self.unload_extension(dependent)
            
            # Unregister from resource monitoring
            self.health_checker.resource_monitor.unregister_extension(extension_name)
            
            # Unload the extension
            await self.extension_manager.unload_extension(extension_name)
            
            # Update state
            self.extension_states[extension_name] = ExtensionLifecycleState.UNLOADED
            
            await self._emit_lifecycle_event(
                extension_id=extension_name,
                event_type="unloaded"
            )
            
            # Update database
            await self._update_extension_status(extension_name, ExtensionStatus.INACTIVE)
            
            self.logger.info(f"Extension {extension_name} unloaded successfully")
            return True
            
        except Exception as e:
            self.extension_states[extension_name] = ExtensionLifecycleState.ERROR
            self.extension_error_counts[extension_name] = self.extension_error_counts.get(extension_name, 0) + 1
            
            self.logger.error(f"Failed to unload extension {extension_name}: {e}")
            
            await self._emit_lifecycle_event(
                extension_id=extension_name,
                event_type="unload_failed",
                error=e,
                data={"error_details": str(e)}
            )
            
            return False
    
    async def unload_all_extensions(self) -> None:
        """Unload all loaded extensions."""
        self.logger.info("Unloading all extensions")
        
        try:
            # Get all loaded extensions
            loaded_extensions = self.get_loaded_extensions()
            
            # Unload in reverse dependency order
            for extension_name in reversed(list(loaded_extensions.keys())):
                await self.unload_extension(extension_name)
            
            self.logger.info("All extensions unloaded")
            
        except Exception as e:
            self.logger.error(f"Failed to unload all extensions: {e}")
    
    async def reload_extension(self, extension_name: str) -> Optional[ExtensionRecord]:
        """
        Reload a specific extension by name.
        
        Args:
            extension_name: Name of the extension to reload
            
        Returns:
            Extension record if successful, None otherwise
        """
        self.logger.info(f"Reloading extension {extension_name}")
        
        try:
            # Unload first
            if await self.unload_extension(extension_name):
                # Load again
                return await self.load_extension(extension_name)
            else:
                self.logger.error(f"Failed to unload extension {extension_name} for reload")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to reload extension {extension_name}: {e}")
            return None
    
    async def _initialize_extension(self, extension_name: str, record: ExtensionRecord) -> None:
        """
        Initialize an extension and transition to active state.
        
        Args:
            extension_name: Name of the extension
            record: Extension record
        """
        try:
            # Update state
            self.extension_states[extension_name] = ExtensionLifecycleState.INITIALIZING
            await self._emit_lifecycle_event(
                extension_id=extension_name,
                event_type="initialization_started"
            )
            
            # Initialize the extension
            if record.instance and hasattr(record.instance, "initialize"):
                await record.instance.initialize()
            
            # Update state to active
            self.extension_states[extension_name] = ExtensionLifecycleState.ACTIVE
            
            await self._emit_lifecycle_event(
                extension_id=extension_name,
                event_type="activated"
            )
            
            # Update database
            await self._update_extension_status(extension_name, ExtensionStatus.ACTIVE)
            
            self.logger.info(f"Extension {extension_name} initialized and activated")
            
        except Exception as e:
            self.extension_states[extension_name] = ExtensionLifecycleState.ERROR
            self.extension_error_counts[extension_name] = self.extension_error_counts.get(extension_name, 0) + 1
            
            self.logger.error(f"Failed to initialize extension {extension_name}: {e}")
            
            await self._emit_lifecycle_event(
                extension_id=extension_name,
                event_type="activation_failed",
                error=e,
                data={"error_details": str(e)}
            )
    
    async def start_health_monitoring(self) -> None:
        """Start health monitoring for all loaded extensions."""
        self.logger.info("Starting extension health monitoring")
        
        try:
            # Get all loaded extensions
            loaded_extensions = self.get_loaded_extensions()
            
            # Start periodic health checks
            asyncio.create_task(self._health_monitoring_loop(loaded_extensions))
            
        except Exception as e:
            self.logger.error(f"Failed to start health monitoring: {e}")
    
    async def stop_health_monitoring(self) -> None:
        """Stop health monitoring for all extensions."""
        self.logger.info("Stopping extension health monitoring")
        
        try:
            # Health monitoring will be stopped by the resource monitor
            pass
            
        except Exception as e:
            self.logger.error(f"Failed to stop health monitoring: {e}")
    
    async def _health_monitoring_loop(self, extensions: Dict[str, ExtensionRecord]) -> None:
        """Main health monitoring loop."""
        while True:
            try:
                # Check health of all extensions
                for extension_name, record in extensions.items():
                    try:
                        health_status = await self.health_checker.check_extension_health(record)
                        
                        # Update state based on health
                        if health_status.value == "red":
                            if self.extension_states.get(extension_name) != ExtensionLifecycleState.ERROR:
                                self.extension_states[extension_name] = ExtensionLifecycleState.ERROR
                                self.extension_error_counts[extension_name] = self.extension_error_counts.get(extension_name, 0) + 1
                                
                                await self._emit_lifecycle_event(
                                    extension_id=extension_name,
                                    event_type="health_failed",
                                    data={"health_status": health_status.value}
                                )
                                
                                # Attempt recovery
                                await self._attempt_extension_recovery(extension_name, record)
                        
                        # Persist health status
                        await self._persist_extension_health(extension_name, health_status)
                        
                    except Exception as e:
                        self.logger.error(f"Health check failed for extension {extension_name}: {e}")
                
                # Sleep between checks
                await asyncio.sleep(self.config.health_check_interval or 60.0)
                
            except asyncio.CancelledError:
                self.logger.info("Health monitoring loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(10.0)  # Brief pause before retrying
    
    async def _attempt_extension_recovery(self, extension_name: str, record: ExtensionRecord) -> None:
        """
        Attempt to recover a failed extension.
        
        Args:
            extension_name: Name of the extension
            record: Extension record
        """
        self.logger.info(f"Attempting recovery for extension {extension_name}")
        
        try:
            # Check error count
            error_count = self.extension_error_counts.get(extension_name, 0)
            
            # Only attempt recovery if under threshold
            max_recovery_attempts = self.config.max_recovery_attempts or 3
            
            if error_count <= max_recovery_attempts:
                # Unload and reload
                if await self.unload_extension(extension_name):
                    await asyncio.sleep(5.0)  # Brief pause
                    await self.load_extension(extension_name)
                    
                    self.logger.info(f"Recovery attempt completed for extension {extension_name}")
            else:
                self.logger.warning(f"Too many recovery attempts for extension {extension_name}, giving up")
                
        except Exception as e:
            self.logger.error(f"Recovery failed for extension {extension_name}: {e}")
    
    def is_extension_loaded(self, extension_name: str) -> bool:
        """
        Check if an extension is currently loaded.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            True if loaded, False otherwise
        """
        state = self.extension_states.get(extension_name)
        return state in [ExtensionLifecycleState.LOADED, ExtensionLifecycleState.ACTIVE]
    
    def is_extension_active(self, extension_name: str) -> bool:
        """
        Check if an extension is currently active.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            True if active, False otherwise
        """
        return self.extension_states.get(extension_name) == ExtensionLifecycleState.ACTIVE
    
    def get_extension_state(self, extension_name: str) -> Optional[ExtensionLifecycleState]:
        """
        Get the current state of an extension.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            Current state or None if not found
        """
        return self.extension_states.get(extension_name)
    
    def get_loaded_extensions(self) -> Dict[str, ExtensionRecord]:
        """
        Get all currently loaded extensions.
        
        Returns:
            Dictionary mapping extension names to their records
        """
        loaded_extensions = {}
        
        for extension_name, state in self.extension_states.items():
            if state in [ExtensionLifecycleState.LOADED, ExtensionLifecycleState.ACTIVE]:
                record = self.extension_manager.get_extension_by_name(extension_name)
                if record:
                    loaded_extensions[extension_name] = record
        
        return loaded_extensions
    
    def get_active_extensions(self) -> Dict[str, ExtensionRecord]:
        """
        Get all currently active extensions.
        
        Returns:
            Dictionary mapping extension names to their records
        """
        active_extensions = {}
        
        for extension_name, state in self.extension_states.items():
            if state == ExtensionLifecycleState.ACTIVE:
                record = self.extension_manager.get_extension_by_name(extension_name)
                if record:
                    active_extensions[extension_name] = record
        
        return active_extensions
    
    def get_dependent_extensions(self, extension_name: str) -> List[str]:
        """
        Get extensions that depend on the specified extension.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            List of dependent extension names
        """
        try:
            # Get all manifests
            manifests = self.extension_manager.registry.extensions
            
            # Check dependencies
            dependents = []
            
            for name, manifest in manifests.items():
                if extension_name in manifest.dependencies.extensions:
                    dependents.append(name)
            
            return dependents
            
        except Exception as e:
            self.logger.error(f"Failed to get dependents for {extension_name}: {e}")
            return []
    
    def add_lifecycle_listener(self, listener: Callable[[ExtensionLifecycleEvent], None]) -> None:
        """
        Add a listener for extension lifecycle events.
        
        Args:
            listener: Callback function for lifecycle events
        """
        self.lifecycle_listeners.append(listener)
    
    def remove_lifecycle_listener(self, listener: Callable[[ExtensionLifecycleEvent], None]) -> bool:
        """
        Remove a listener for extension lifecycle events.
        
        Args:
            listener: Callback function to remove
            
        Returns:
            True if removed, False if not found
        """
        if listener in self.lifecycle_listeners:
            self.lifecycle_listeners.remove(listener)
            return True
        return False
    
    async def _emit_lifecycle_event(self, **kwargs) -> None:
        """
        Emit a lifecycle event to all listeners.
        
        Args:
            **kwargs: Arguments for ExtensionLifecycleEvent
        """
        try:
            event = ExtensionLifecycleEvent(**kwargs)
            self.lifecycle_events.append(event)
            
            # Notify all listeners
            for listener in self.lifecycle_listeners:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(event)
                    else:
                        listener(event)
                except Exception as e:
                    self.logger.error(f"Lifecycle listener error: {e}")
                    
        except Exception as e:
            self.logger.error(f"Failed to emit lifecycle event: {e}")
    
    def get_lifecycle_events(self, extension_name: Optional[str] = None) -> List[ExtensionLifecycleEvent]:
        """
        Get lifecycle events for an extension or all extensions.
        
        Args:
            extension_name: Optional extension name to filter by
            
        Returns:
            List of lifecycle events
        """
        if extension_name:
            return [event for event in self.lifecycle_events if event.extension_id == extension_name]
        else:
            return self.lifecycle_events.copy()
    
    def get_extension_metrics(self, extension_name: str) -> Dict[str, Any]:
        """
        Get metrics for a specific extension.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            Dictionary containing extension metrics
        """
        try:
            # Get basic metrics
            metrics = {
                "name": extension_name,
                "state": self.extension_states.get(extension_name, "unknown").value,
                "load_time": self.extension_load_times.get(extension_name),
                "error_count": self.extension_error_counts.get(extension_name, 0),
                "uptime_seconds": 0,
                "last_error": None
            }
            
            # Calculate uptime if loaded
            if extension_name in self.extension_load_times:
                load_time = self.extension_load_times[extension_name]
                if load_time:
                    metrics["uptime_seconds"] = (datetime.now(timezone.utc) - load_time).total_seconds()
            
            # Get resource usage
            resource_usage = self.health_checker.resource_monitor.get_extension_usage(extension_name)
            if resource_usage:
                metrics.update(resource_usage)
            
            # Get health status
            health_status = self.health_checker.get_extension_health(extension_name)
            if health_status:
                metrics["health_status"] = health_status.value
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get metrics for extension {extension_name}: {e}")
            return {"error": str(e)}
    
    def get_all_extension_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metrics for all extensions.
        
        Returns:
            Dictionary mapping extension names to their metrics
        """
        all_metrics = {}
        
        for extension_name in self.extension_states.keys():
            all_metrics[extension_name] = self.get_extension_metrics(extension_name)
        
        return all_metrics
    
    async def _persist_extension_record(self, record: ExtensionRecord) -> None:
        """Persist extension record to database."""
        try:
            if self.db_session:
                with get_db_session_context() as session:
                    # Check if extension already exists
                    existing = session.get(Extension, record.manifest.name)
                    
                    if existing:
                        # Update existing record
                        existing.version = record.manifest.version
                        existing.category = getattr(record.manifest, 'category', None)
                        existing.status = record.status.value
                        existing.directory = str(record.directory)
                        existing.loaded_at = datetime.utcnow()
                        existing.updated_at = datetime.utcnow()
                        session.commit()
                    else:
                        # Create new record
                        extension = Extension(
                            name=record.manifest.name,
                            version=record.manifest.version,
                            category=getattr(record.manifest, 'category', None),
                            status=record.status.value,
                            directory=str(record.directory),
                            loaded_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        session.add(extension)
                        session.commit()
                        
        except Exception as e:
            self.logger.error(f"Failed to persist extension record: {e}")
    
    async def _persist_loading_results(self, loaded_extensions: Dict[str, ExtensionRecord], failed_extensions: List[str]) -> None:
        """Persist loading results to database."""
        try:
            if self.db_session:
                with get_db_session_context() as session:
                    # Update status for loaded extensions
                    for extension_name, record in loaded_extensions.items():
                        existing = session.get(Extension, extension_name)
                        if existing:
                            existing.status = ExtensionStatus.ACTIVE.value
                            existing.loaded_at = datetime.utcnow()
                            existing.updated_at = datetime.utcnow()
                    
                    # Mark failed extensions as error
                    for extension_name in failed_extensions:
                        existing = session.get(Extension, extension_name)
                        if existing:
                            existing.status = ExtensionStatus.ERROR.value
                            existing.updated_at = datetime.utcnow()
                    
                    session.commit()
                    
        except Exception as e:
            self.logger.error(f"Failed to persist loading results: {e}")
    
    async def _update_extension_status(self, extension_name: str, status: ExtensionStatus) -> None:
        """Update extension status in database."""
        try:
            if self.db_session:
                with get_db_session_context() as session:
                    existing = session.get(Extension, extension_name)
                    if existing:
                        existing.status = status.value
                        existing.updated_at = datetime.utcnow()
                        session.commit()
                        
        except Exception as e:
            self.logger.error(f"Failed to update extension status: {e}")
    
    async def _persist_extension_health(self, extension_name: str, health_status) -> None:
        """Persist extension health status to database."""
        try:
            if self.db_session:
                with get_db_session_context() as session:
                    existing = session.get(Extension, extension_name)
                    if existing:
                        # Update or create health record
                        health_record = session.get(ExtensionHealth, extension_name)
                        
                        if health_record:
                            health_record.status = health_status.value
                            health_record.checked_at = datetime.utcnow()
                        else:
                            health_record = ExtensionHealth(
                                name=extension_name,
                                status=health_status.value,
                                checked_at=datetime.utcnow()
                            )
                            session.add(health_record)
                        
                        session.commit()
                        
        except Exception as e:
            self.logger.error(f"Failed to persist extension health: {e}")
    
    def get_lifecycle_summary(self) -> Dict[str, Any]:
        """
        Get a summary of extension lifecycle status.
        
        Returns:
            Dictionary containing lifecycle summary
        """
        try:
            total_extensions = len(self.extension_states)
            active_extensions = len(self.get_active_extensions())
            loaded_extensions = len(self.get_loaded_extensions())
            error_extensions = sum(1 for state in self.extension_states.values() if state == ExtensionLifecycleState.ERROR)
            
            return {
                "total_extensions": total_extensions,
                "active_extensions": active_extensions,
                "loaded_extensions": loaded_extensions,
                "error_extensions": error_extensions,
                "health_summary": self.health_checker.get_health_summary(),
                "recent_events": self.lifecycle_events[-10:] if self.lifecycle_events else [],
                "uptime_stats": self._get_uptime_stats()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get lifecycle summary: {e}")
            return {"error": str(e)}
    
    def _get_uptime_stats(self) -> Dict[str, Any]:
        """Get uptime statistics for all extensions."""
        try:
            now = datetime.now(timezone.utc)
            uptime_stats = {}
            
            for extension_name, load_time in self.extension_load_times.items():
                if load_time:
                    uptime_seconds = (now - load_time).total_seconds()
                    uptime_stats[extension_name] = {
                        "load_time": load_time.isoformat(),
                        "uptime_seconds": uptime_seconds,
                        "uptime_formatted": str(uptime_seconds)
                    }
            
            return uptime_stats
            
        except Exception as e:
            self.logger.error(f"Failed to get uptime stats: {e}")
            return {}


__all__ = [
    "ExtensionLifecycleManager",
    "ExtensionLifecycleState",
    "ExtensionLifecycleEvent",
]