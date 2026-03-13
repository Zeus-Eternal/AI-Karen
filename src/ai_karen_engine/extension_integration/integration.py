"""Extension Integration Layer - Integration of all extension system components.

This module provides the main integration layer that connects all extension system components:
- Lifecycle management
- Discovery and registration
- Sandbox and security
- Communication and messaging
- Versioning and updates
- Permissions and access control
- Metrics and monitoring
- Database persistence
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from pathlib import Path

from ai_karen_engine.extension_integration.lifecycle_manager import ExtensionLifecycleManager, ExtensionState
from ai_karen_engine.extension_integration.discovery_service import ExtensionDiscoveryService
from ai_karen_engine.extension_integration.sandbox_manager import ExtensionSandboxManager, SecurityLevel
from ai_karen_engine.extension_integration.communication_manager import ExtensionCommunicationManager
from ai_karen_engine.extension_integration.version_manager import ExtensionVersionManager, UpdateChannel
from ai_karen_engine.extension_integration.permissions_manager import ExtensionPermissionsManager
from ai_karen_engine.extension_integration.metrics_collector import ExtensionMetricsCollector
from ai_karen_engine.extension_integration.models import (
    ExtensionModel, ExtensionVersionModel, ExtensionMetricModel, 
    ExtensionEventModel, ExtensionConfigModel, create_extension_tables
)


class ExtensionIntegrationManager:
    """
    Main integration manager for the extension system.
    
    This class coordinates all extension system components and provides
    a unified interface for extension management.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        db_session_factory=None
    ):
        """
        Initialize the extension integration manager.
        
        Args:
            config: Configuration dictionary
            db_session_factory: Database session factory
        """
        self.config = config or {}
        self.db_session_factory = db_session_factory
        
        # Initialize components
        self.lifecycle_manager: Optional[ExtensionLifecycleManager] = None
        self.discovery_service: Optional[ExtensionDiscoveryService] = None
        self.sandbox_manager: Optional[ExtensionSandboxManager] = None
        self.communication_manager: Optional[ExtensionCommunicationManager] = None
        self.version_manager: Optional[ExtensionVersionManager] = None
        self.permissions_manager: Optional[ExtensionPermissionsManager] = None
        self.metrics_collector: Optional[ExtensionMetricsCollector] = None
        
        # Integration state
        self.initialized = False
        self.started = False
        
        self.logger = logging.getLogger("extension.integration_manager")
        
        self.logger.info("Extension integration manager initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize all extension system components.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Initializing extension system components")
            
            # Initialize database tables if session factory is available
            if self.db_session_factory:
                await self._initialize_database()
            
            # Initialize metrics collector first (other components may use it)
            self.metrics_collector = ExtensionMetricsCollector(
                collection_interval=self.config.get("metrics_collection_interval", 60),
                retention_period=self.config.get("metrics_retention_period", 7 * 24 * 60 * 60),
                max_samples=self.config.get("metrics_max_samples", 10000),
                enable_real_time=self.config.get("enable_real_time_metrics", True)
            )
            
            # Initialize permissions manager
            self.permissions_manager = ExtensionPermissionsManager(
                enable_audit=self.config.get("enable_permission_audit", True),
                default_policy=self.config.get("default_permission_policy", "default"),
                cache_ttl=self.config.get("permission_cache_ttl", 300)
            )
            
            # Initialize sandbox manager
            self.sandbox_manager = ExtensionSandboxManager(
                default_security_level=SecurityLevel(
                    self.config.get("default_security_level", "restricted")
                ),
                enable_monitoring=self.config.get("enable_sandbox_monitoring", True),
                resource_limits=self.config.get("default_resource_limits", {})
            )
            
            # Initialize communication manager
            self.communication_manager = ExtensionCommunicationManager(
                enable_message_queue=self.config.get("enable_message_queue", True),
                enable_event_bus=self.config.get("enable_event_bus", True),
                enable_service_discovery=self.config.get("enable_service_discovery", True)
            )
            
            # Initialize version manager
            self.version_manager = ExtensionVersionManager(
                update_channels=self.config.get("update_channels", {}),
                auto_update=self.config.get("auto_update_enabled", False),
                security_validation=self.config.get("enable_security_validation", True)
            )
            
            # Initialize discovery service
            self.discovery_service = ExtensionDiscoveryService(
                scan_paths=self.config.get("extension_scan_paths", ["src/extensions"]),
                recursive_scan=self.config.get("recursive_scan", True),
                cache_enabled=self.config.get("enable_discovery_cache", True)
            )
            
            # Initialize lifecycle manager (last, as it depends on other components)
            self.lifecycle_manager = ExtensionLifecycleManager(
                discovery_service=self.discovery_service,
                sandbox_manager=self.sandbox_manager,
                communication_manager=self.communication_manager,
                version_manager=self.version_manager,
                permissions_manager=self.permissions_manager,
                metrics_collector=self.metrics_collector,
                db_session_factory=self.db_session_factory
            )
            
            # Set up cross-component integration
            await self._setup_component_integration()
            
            self.initialized = True
            self.logger.info("Extension system components initialized successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize extension system: {e}")
            return False
    
    async def _initialize_database(self) -> None:
        """Initialize database tables."""
        try:
            # This would typically be done using the database engine
            # For now, just log that we would initialize tables
            self.logger.info("Database tables would be initialized here")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
    
    async def _setup_component_integration(self) -> None:
        """Set up integration between components."""
        try:
            # Connect metrics collector to lifecycle events
            if self.lifecycle_manager and self.metrics_collector:
                # Add metrics collector as lifecycle listener
                self.lifecycle_manager.add_lifecycle_listener(
                    self._on_lifecycle_event
                )
            
            # Connect communication manager to extension events
            if self.communication_manager and self.lifecycle_manager:
                # Set up event forwarding
                self.communication_manager.register_event_handler(
                    "extension.*",
                    self._on_extension_event
                )
            
            # Connect permissions manager to lifecycle events
            if self.permissions_manager and self.lifecycle_manager:
                # Set up permission checking for extension operations
                self.lifecycle_manager.set_permission_checker(
                    self.permissions_manager.check_permission
                )
            
            # Connect version manager to lifecycle events
            if self.version_manager and self.lifecycle_manager:
                # Set up update notifications
                self.version_manager.add_update_listener(
                    self._on_extension_update
                )
            
            self.logger.info("Component integration set up successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to set up component integration: {e}")
    
    async def _on_lifecycle_event(self, event: Dict[str, Any]) -> None:
        """Handle lifecycle events and record metrics."""
        try:
            if self.metrics_collector:
                # Record lifecycle event as metric
                self.metrics_collector.record_metric(
                    f"lifecycle_{event.get('event_type', 'unknown')}",
                    1,
                    tags={
                        "extension_id": event.get("extension_id", ""),
                        "from_state": event.get("from_state", ""),
                        "to_state": event.get("to_state", "")
                    },
                    extension_id=event.get("extension_id")
                )
            
        except Exception as e:
            self.logger.error(f"Failed to handle lifecycle event: {e}")
    
    async def _on_extension_event(self, event: Dict[str, Any]) -> None:
        """Handle extension events from communication manager."""
        try:
            # Forward event to lifecycle manager if needed
            if self.lifecycle_manager:
                await self.lifecycle_manager.handle_extension_event(event)
            
        except Exception as e:
            self.logger.error(f"Failed to handle extension event: {e}")
    
    async def _on_extension_update(self, update_info: Dict[str, Any]) -> None:
        """Handle extension update events."""
        try:
            # Notify lifecycle manager of update
            if self.lifecycle_manager:
                await self.lifecycle_manager.handle_extension_update(update_info)
            
        except Exception as e:
            self.logger.error(f"Failed to handle extension update: {e}")
    
    async def start(self) -> bool:
        """
        Start the extension system.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.initialized:
                if not await self.initialize():
                    return False
            
            self.logger.info("Starting extension system")
            
            # Start metrics collection
            if self.metrics_collector:
                self.metrics_collector.start_collection()
            
            # Start communication manager
            if self.communication_manager:
                await self.communication_manager.start()
            
            # Start version manager
            if self.version_manager:
                await self.version_manager.start()
            
            # Start discovery service
            if self.discovery_service:
                await self.discovery_service.start()
            
            # Start lifecycle manager
            if self.lifecycle_manager:
                await self.lifecycle_manager.start()
            
            self.started = True
            self.logger.info("Extension system started successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start extension system: {e}")
            return False
    
    async def stop(self) -> bool:
        """
        Stop the extension system.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.started:
                return True
            
            self.logger.info("Stopping extension system")
            
            # Stop lifecycle manager first
            if self.lifecycle_manager:
                await self.lifecycle_manager.stop()
            
            # Stop discovery service
            if self.discovery_service:
                await self.discovery_service.stop()
            
            # Stop version manager
            if self.version_manager:
                await self.version_manager.stop()
            
            # Stop communication manager
            if self.communication_manager:
                await self.communication_manager.stop()
            
            # Stop metrics collection
            if self.metrics_collector:
                self.metrics_collector.stop_collection()
            
            self.started = False
            self.logger.info("Extension system stopped successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop extension system: {e}")
            return False
    
    async def restart(self) -> bool:
        """
        Restart the extension system.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if await self.stop():
                return await self.start()
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to restart extension system: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the extension system.
        
        Returns:
            Status dictionary
        """
        try:
            status = {
                "initialized": self.initialized,
                "started": self.started,
                "components": {}
            }
            
            # Get component statuses
            if self.lifecycle_manager:
                status["components"]["lifecycle_manager"] = {
                    "initialized": True,
                    "extensions_count": len(self.lifecycle_manager.get_all_extensions()),
                    "active_extensions": len([
                        e for e in self.lifecycle_manager.get_all_extensions()
                        if e.state == ExtensionState.ACTIVE
                    ])
                }
            
            if self.discovery_service:
                status["components"]["discovery_service"] = {
                    "initialized": True,
                    "scan_paths": self.discovery_service.scan_paths,
                    "cache_enabled": self.discovery_service.cache_enabled
                }
            
            if self.sandbox_manager:
                status["components"]["sandbox_manager"] = {
                    "initialized": True,
                    "default_security_level": self.sandbox_manager.default_security_level.value,
                    "active_sandboxes": len(self.sandbox_manager.active_sandboxes)
                }
            
            if self.communication_manager:
                status["components"]["communication_manager"] = {
                    "initialized": True,
                    "message_queue_enabled": self.communication_manager.message_queue_enabled,
                    "event_bus_enabled": self.communication_manager.event_bus_enabled,
                    "registered_services": len(self.communication_manager.registered_services)
                }
            
            if self.version_manager:
                status["components"]["version_manager"] = {
                    "initialized": True,
                    "auto_update_enabled": self.version_manager.auto_update,
                    "update_channels": list(self.version_manager.update_channels.keys())
                }
            
            if self.permissions_manager:
                status["components"]["permissions_manager"] = {
                    "initialized": True,
                    "policies_count": len(self.permissions_manager.get_permission_policies()),
                    "roles_count": len(self.permissions_manager.get_roles()),
                    "permissions_count": len(self.permissions_manager.get_permissions())
                }
            
            if self.metrics_collector:
                status["components"]["metrics_collector"] = {
                    "initialized": True,
                    "collection_active": self.metrics_collector.collection_active,
                    "metrics_count": len(self.metrics_collector.metrics)
                }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get extension system status: {e}")
            return {"error": str(e)}
    
    # Convenience methods that delegate to appropriate components
    
    async def install_extension(
        self,
        extension_id: str,
        version: Optional[str] = None,
        update_channel: Optional[str] = None,
        auto_start: bool = True,
        configuration: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Install an extension."""
        if not self.lifecycle_manager:
            return False
        return await self.lifecycle_manager.install_extension(
            extension_id, version, update_channel, auto_start, configuration
        )
    
    async def uninstall_extension(self, extension_id: str) -> bool:
        """Uninstall an extension."""
        if not self.lifecycle_manager:
            return False
        return await self.lifecycle_manager.uninstall_extension(extension_id)
    
    async def start_extension(self, extension_id: str) -> bool:
        """Start an extension."""
        if not self.lifecycle_manager:
            return False
        return await self.lifecycle_manager.start_extension(extension_id)
    
    async def stop_extension(self, extension_id: str) -> bool:
        """Stop an extension."""
        if not self.lifecycle_manager:
            return False
        return await self.lifecycle_manager.stop_extension(extension_id)
    
    async def restart_extension(self, extension_id: str) -> bool:
        """Restart an extension."""
        if not self.lifecycle_manager:
            return False
        return await self.lifecycle_manager.restart_extension(extension_id)
    
    def get_extension(self, extension_id: str):
        """Get an extension by ID."""
        if not self.lifecycle_manager:
            return None
        return self.lifecycle_manager.get_extension(extension_id)
    
    def get_all_extensions(self) -> List:
        """Get all extensions."""
        if not self.lifecycle_manager:
            return []
        return self.lifecycle_manager.get_all_extensions()
    
    async def discover_extensions(self) -> List:
        """Discover extensions."""
        if not self.discovery_service:
            return []
        return await self.discovery_service.discover_extensions()
    
    def get_extension_metrics(
        self,
        extension_id: str,
        metric_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, List]:
        """Get extension metrics."""
        if not self.metrics_collector:
            return {}
        return self.metrics_collector.get_metrics(
            metric_name, extension_id, start_time, end_time
        )
    
    def get_extension_events(
        self,
        extension_id: str,
        event_type: Optional[str] = None,
        event_level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get extension events."""
        if not self.lifecycle_manager:
            return []
        return self.lifecycle_manager.get_extension_events(
            extension_id, event_type, event_level, start_time, end_time
        )


# Global instance for easy access
_integration_manager: Optional[ExtensionIntegrationManager] = None


def get_integration_manager() -> Optional[ExtensionIntegrationManager]:
    """Get the global extension integration manager instance."""
    return _integration_manager


def set_integration_manager(manager: ExtensionIntegrationManager) -> None:
    """Set the global extension integration manager instance."""
    global _integration_manager
    _integration_manager = manager


# Convenience functions for accessing components
def get_lifecycle_manager() -> Optional[ExtensionLifecycleManager]:
    """Get the extension lifecycle manager."""
    manager = get_integration_manager()
    return manager.lifecycle_manager if manager else None


def get_discovery_service() -> Optional[ExtensionDiscoveryService]:
    """Get the extension discovery service."""
    manager = get_integration_manager()
    return manager.discovery_service if manager else None


def get_sandbox_manager() -> Optional[ExtensionSandboxManager]:
    """Get the extension sandbox manager."""
    manager = get_integration_manager()
    return manager.sandbox_manager if manager else None


def get_communication_manager() -> Optional[ExtensionCommunicationManager]:
    """Get the extension communication manager."""
    manager = get_integration_manager()
    return manager.communication_manager if manager else None


def get_version_manager() -> Optional[ExtensionVersionManager]:
    """Get the extension version manager."""
    manager = get_integration_manager()
    return manager.version_manager if manager else None


def get_permissions_manager() -> Optional[ExtensionPermissionsManager]:
    """Get the extension permissions manager."""
    manager = get_integration_manager()
    return manager.permissions_manager if manager else None


def get_metrics_collector() -> Optional[ExtensionMetricsCollector]:
    """Get the extension metrics collector."""
    manager = get_integration_manager()
    return manager.metrics_collector if manager else None


__all__ = [
    "ExtensionIntegrationManager",
    "get_integration_manager",
    "set_integration_manager",
    "get_lifecycle_manager",
    "get_discovery_service",
    "get_sandbox_manager",
    "get_communication_manager",
    "get_version_manager",
    "get_permissions_manager",
    "get_metrics_collector",
]