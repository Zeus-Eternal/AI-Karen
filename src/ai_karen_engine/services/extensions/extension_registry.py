"""
Extension Registry Service

This service provides a registry for all extensions in the system,
allowing for discovery, management, and execution of extensions.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable
import logging
import uuid
import json
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import os
import importlib.util
from pathlib import Path

logger = logging.getLogger(__name__)


class ExtensionType(Enum):
    """Enumeration of extension types."""
    AGENT = "agent"
    TOOL = "tool"
    UI_COMPONENT = "ui_component"
    DATA_SOURCE = "data_source"
    INTEGRATION = "integration"
    CUSTOM = "custom"


class ExtensionStatus(Enum):
    """Enumeration of extension statuses."""
    LOADED = "loaded"
    UNLOADED = "unloaded"
    ERROR = "error"
    DISABLED = "disabled"
    UPDATING = "updating"


@dataclass
class ExtensionMetadata:
    """Metadata for an extension."""
    name: str
    version: str
    description: str
    author: str
    license: str
    homepage: Optional[str] = None
    repository: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    api_version: str = "1.0"
    min_kari_version: str = "1.0.0"
    max_kari_version: Optional[str] = None


@dataclass
class ExtensionConfig:
    """Configuration for an extension."""
    enabled: bool = True
    auto_update: bool = False
    settings: Dict[str, Any] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    resource_limits: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Extension:
    """An extension."""
    id: str
    path: str
    type: ExtensionType
    metadata: ExtensionMetadata
    config: ExtensionConfig
    main_module: Optional[str] = None
    entry_point: Optional[str] = None
    status: ExtensionStatus = ExtensionStatus.UNLOADED
    loaded_at: Optional[datetime] = None
    error_message: Optional[str] = None
    instance: Optional[Any] = None


@dataclass
class ExtensionEvent:
    """An event related to an extension."""
    id: str
    extension_id: str
    event_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class ExtensionRegistry:
    """
    Provides a registry for all extensions in the system.
    
    This class is responsible for:
    - Discovering and loading extensions
    - Managing extension lifecycle
    - Providing extension metadata and configuration
    - Handling extension events
    - Validating extension compatibility
    """
    
    def __init__(self, extensions_dir: str = "extensions"):
        self._extensions_dir = Path(extensions_dir)
        self._extensions: Dict[str, Extension] = {}
        self._events: List[ExtensionEvent] = []
        self._type_index: Dict[ExtensionType, Set[str]] = {t: set() for t in ExtensionType}
        self._tag_index: Dict[str, Set[str]] = {}
        
        # Callbacks for extension events
        self._on_extension_loaded: Optional[Callable[[Extension], None]] = None
        self._on_extension_unloaded: Optional[Callable[[Extension], None]] = None
        self._on_extension_error: Optional[Callable[[Extension, str], None]] = None
        self._on_extension_event: Optional[Callable[[ExtensionEvent], None]] = None
    
    def initialize(self) -> None:
        """Initialize the extension registry."""
        # Create extensions directory if it doesn't exist
        self._extensions_dir.mkdir(exist_ok=True)
        
        # Discover extensions
        self._discover_extensions()
        
        logger.info(f"Initialized extension registry with {len(self._extensions)} extensions")
    
    def get_extension(self, extension_id: str) -> Optional[Extension]:
        """Get an extension by ID."""
        return self._extensions.get(extension_id)
    
    def get_extensions(self, extension_type: Optional[ExtensionType] = None, tag: Optional[str] = None) -> List[Extension]:
        """
        Get extensions, optionally filtered by type or tag.
        
        Args:
            extension_type: Type of extensions to get
            tag: Tag to filter by
            
        Returns:
            List of extensions
        """
        extensions = list(self._extensions.values())
        
        # Filter by type
        if extension_type:
            extension_ids = self._type_index.get(extension_type, set())
            extensions = [e for e in extensions if e.id in extension_ids]
        
        # Filter by tag
        if tag:
            extension_ids = self._tag_index.get(tag, set())
            extensions = [e for e in extensions if e.id in extension_ids]
        
        return extensions
    
    def get_enabled_extensions(self, extension_type: Optional[ExtensionType] = None) -> List[Extension]:
        """
        Get enabled extensions, optionally filtered by type.
        
        Args:
            extension_type: Type of extensions to get
            
        Returns:
            List of enabled extensions
        """
        extensions = self.get_extensions(extension_type)
        return [e for e in extensions if e.config.enabled]
    
    def load_extension(self, extension_id: str) -> bool:
        """
        Load an extension.
        
        Args:
            extension_id: ID of the extension
            
        Returns:
            True if extension was loaded, False otherwise
        """
        extension = self._extensions.get(extension_id)
        if not extension:
            logger.error(f"Extension not found: {extension_id}")
            return False
        
        if extension.status == ExtensionStatus.LOADED:
            logger.warning(f"Extension already loaded: {extension_id}")
            return True
        
        if not extension.config.enabled:
            logger.warning(f"Extension is disabled: {extension_id}")
            return False
        
        try:
            # Load the extension
            if extension.main_module:
                # Load as a Python module
                module_path = Path(extension.path) / extension.main_module
                if not module_path.exists():
                    raise Exception(f"Main module not found: {module_path}")
                
                spec = importlib.util.spec_from_file_location(
                    f"extension_{extension_id}",
                    module_path
                )
                if not spec or not spec.loader:
                    raise Exception(f"Failed to load module spec: {module_path}")
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Create extension instance
                if hasattr(module, "create_extension"):
                    extension.instance = module.create_extension()
                elif hasattr(module, "Extension"):
                    extension.instance = module.Extension()
                else:
                    raise Exception("Extension module has no entry point")
            
            elif extension.entry_point:
                # Load as a function
                module_path = Path(extension.path) / "main.py"
                if not module_path.exists():
                    raise Exception(f"Main module not found: {module_path}")
                
                spec = importlib.util.spec_from_file_location(
                    f"extension_{extension_id}",
                    module_path
                )
                if not spec or not spec.loader:
                    raise Exception(f"Failed to load module spec: {module_path}")
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Get entry point function
                if not hasattr(module, extension.entry_point):
                    raise Exception(f"Entry point not found: {extension.entry_point}")
                
                extension.instance = getattr(module, extension.entry_point)
            
            else:
                raise Exception("Extension has no main module or entry point")
            
            # Update extension status
            extension.status = ExtensionStatus.LOADED
            extension.loaded_at = datetime.now()
            extension.error_message = None
            
            # Record event
            self._record_event(extension_id, "loaded", {
                "loaded_at": extension.loaded_at.isoformat()
            })
            
            # Call extension loaded callback if set
            if self._on_extension_loaded:
                self._on_extension_loaded(extension)
            
            logger.info(f"Loaded extension: {extension_id}")
            return True
            
        except Exception as e:
            # Update extension status
            extension.status = ExtensionStatus.ERROR
            extension.error_message = str(e)
            
            # Record event
            self._record_event(extension_id, "error", {
                "error": str(e)
            })
            
            # Call extension error callback if set
            if self._on_extension_error:
                self._on_extension_error(extension, str(e))
            
            logger.error(f"Failed to load extension {extension_id}: {str(e)}")
            return False
    
    def unload_extension(self, extension_id: str) -> bool:
        """
        Unload an extension.
        
        Args:
            extension_id: ID of the extension
            
        Returns:
            True if extension was unloaded, False otherwise
        """
        extension = self._extensions.get(extension_id)
        if not extension:
            logger.error(f"Extension not found: {extension_id}")
            return False
        
        if extension.status != ExtensionStatus.LOADED:
            logger.warning(f"Extension not loaded: {extension_id}")
            return True
        
        try:
            # Check if extension has cleanup method
            if extension.instance and hasattr(extension.instance, "cleanup"):
                extension.instance.cleanup()
            
            # Update extension status
            extension.status = ExtensionStatus.UNLOADED
            extension.instance = None
            
            # Record event
            self._record_event(extension_id, "unloaded")
            
            # Call extension unloaded callback if set
            if self._on_extension_unloaded:
                self._on_extension_unloaded(extension)
            
            logger.info(f"Unloaded extension: {extension_id}")
            return True
            
        except Exception as e:
            # Update extension status
            extension.status = ExtensionStatus.ERROR
            extension.error_message = str(e)
            
            # Record event
            self._record_event(extension_id, "error", {
                "error": str(e)
            })
            
            # Call extension error callback if set
            if self._on_extension_error:
                self._on_extension_error(extension, str(e))
            
            logger.error(f"Failed to unload extension {extension_id}: {str(e)}")
            return False
    
    def enable_extension(self, extension_id: str) -> bool:
        """
        Enable an extension.
        
        Args:
            extension_id: ID of the extension
            
        Returns:
            True if extension was enabled, False otherwise
        """
        extension = self._extensions.get(extension_id)
        if not extension:
            logger.error(f"Extension not found: {extension_id}")
            return False
        
        if extension.config.enabled:
            logger.warning(f"Extension already enabled: {extension_id}")
            return True
        
        extension.config.enabled = True
        
        # Record event
        self._record_event(extension_id, "enabled")
        
        logger.info(f"Enabled extension: {extension_id}")
        return True
    
    def disable_extension(self, extension_id: str) -> bool:
        """
        Disable an extension.
        
        Args:
            extension_id: ID of the extension
            
        Returns:
            True if extension was disabled, False otherwise
        """
        extension = self._extensions.get(extension_id)
        if not extension:
            logger.error(f"Extension not found: {extension_id}")
            return False
        
        if not extension.config.enabled:
            logger.warning(f"Extension already disabled: {extension_id}")
            return True
        
        # Unload extension if loaded
        if extension.status == ExtensionStatus.LOADED:
            self.unload_extension(extension_id)
        
        extension.config.enabled = False
        
        # Record event
        self._record_event(extension_id, "disabled")
        
        logger.info(f"Disabled extension: {extension_id}")
        return True
    
    def update_extension_config(self, extension_id: str, config: Dict[str, Any]) -> bool:
        """
        Update an extension's configuration.
        
        Args:
            extension_id: ID of the extension
            config: New configuration
            
        Returns:
            True if configuration was updated, False otherwise
        """
        extension = self._extensions.get(extension_id)
        if not extension:
            logger.error(f"Extension not found: {extension_id}")
            return False
        
        # Update configuration
        if "enabled" in config:
            extension.config.enabled = config["enabled"]
        
        if "auto_update" in config:
            extension.config.auto_update = config["auto_update"]
        
        if "settings" in config:
            extension.config.settings.update(config["settings"])
        
        if "permissions" in config:
            extension.config.permissions = config["permissions"]
        
        if "environment" in config:
            extension.config.environment.update(config["environment"])
        
        if "resource_limits" in config:
            extension.config.resource_limits.update(config["resource_limits"])
        
        # Record event
        self._record_event(extension_id, "config_updated", {
            "config": config
        })
        
        logger.info(f"Updated configuration for extension: {extension_id}")
        return True
    
    def get_events(
        self,
        extension_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[ExtensionEvent]:
        """
        Get extension events.
        
        Args:
            extension_id: ID of the extension
            event_type: Type of event
            limit: Maximum number of events to return
            
        Returns:
            List of extension events
        """
        events = self._events
        
        # Filter by extension_id
        if extension_id:
            events = [e for e in events if e.extension_id == extension_id]
        
        # Filter by event_type
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Sort by timestamp (newest first)
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        # Apply limit
        return events[:limit]
    
    def set_extension_callbacks(
        self,
        on_extension_loaded: Optional[Callable[[Extension], None]] = None,
        on_extension_unloaded: Optional[Callable[[Extension], None]] = None,
        on_extension_error: Optional[Callable[[Extension, str], None]] = None,
        on_extension_event: Optional[Callable[[ExtensionEvent], None]] = None
    ) -> None:
        """Set callbacks for extension events."""
        self._on_extension_loaded = on_extension_loaded
        self._on_extension_unloaded = on_extension_unloaded
        self._on_extension_error = on_extension_error
        self._on_extension_event = on_extension_event
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about extensions.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_extensions": len(self._extensions),
            "loaded_extensions": sum(1 for e in self._extensions.values() if e.status == ExtensionStatus.LOADED),
            "enabled_extensions": sum(1 for e in self._extensions.values() if e.config.enabled),
            "disabled_extensions": sum(1 for e in self._extensions.values() if not e.config.enabled),
            "error_extensions": sum(1 for e in self._extensions.values() if e.status == ExtensionStatus.ERROR),
            "extensions_by_type": {},
            "extensions_by_status": {},
            "extensions_by_tag": {},
            "total_events": len(self._events)
        }
        
        # Count extensions by type
        for extension_type, extension_ids in self._type_index.items():
            stats["extensions_by_type"][extension_type.value] = len(extension_ids)
        
        # Count extensions by status
        for extension in self._extensions.values():
            status = extension.status.value
            if status not in stats["extensions_by_status"]:
                stats["extensions_by_status"][status] = 0
            stats["extensions_by_status"][status] += 1
        
        # Count extensions by tag
        for tag, extension_ids in self._tag_index.items():
            stats["extensions_by_tag"][tag] = len(extension_ids)
        
        return stats
    
    def _discover_extensions(self) -> None:
        """Discover extensions in the extensions directory."""
        if not self._extensions_dir.exists():
            logger.warning(f"Extensions directory not found: {self._extensions_dir}")
            return
        
        # Look for extension directories
        for item in self._extensions_dir.iterdir():
            if not item.is_dir():
                continue
            
            # Check for manifest file
            manifest_path = item / "extension_manifest.json"
            if not manifest_path.exists():
                continue
            
            try:
                # Load manifest
                with open(manifest_path, "r") as f:
                    manifest_data = json.load(f)
                
                # Parse metadata
                metadata_data = manifest_data.get("metadata", {})
                metadata = ExtensionMetadata(
                    name=metadata_data.get("name", ""),
                    version=metadata_data.get("version", "1.0.0"),
                    description=metadata_data.get("description", ""),
                    author=metadata_data.get("author", ""),
                    license=metadata_data.get("license", "MIT"),
                    homepage=metadata_data.get("homepage"),
                    repository=metadata_data.get("repository"),
                    tags=metadata_data.get("tags", []),
                    dependencies=metadata_data.get("dependencies", []),
                    api_version=metadata_data.get("api_version", "1.0"),
                    min_kari_version=metadata_data.get("min_kari_version", "1.0.0"),
                    max_kari_version=metadata_data.get("max_kari_version")
                )
                
                # Parse configuration
                config_data = manifest_data.get("config", {})
                config = ExtensionConfig(
                    enabled=config_data.get("enabled", True),
                    auto_update=config_data.get("auto_update", False),
                    settings=config_data.get("settings", {}),
                    permissions=config_data.get("permissions", []),
                    environment=config_data.get("environment", {}),
                    resource_limits=config_data.get("resource_limits", {})
                )
                
                # Create extension
                extension = Extension(
                    id=manifest_data.get("id", item.name),
                    path=str(item),
                    type=ExtensionType(manifest_data.get("type", "custom")),
                    metadata=metadata,
                    config=config,
                    main_module=manifest_data.get("main_module"),
                    entry_point=manifest_data.get("entry_point")
                )
                
                # Add to registry
                self._extensions[extension.id] = extension
                
                # Update type index
                self._type_index[extension.type].add(extension.id)
                
                # Update tag index
                for tag in metadata.tags:
                    if tag not in self._tag_index:
                        self._tag_index[tag] = set()
                    self._tag_index[tag].add(extension.id)
                
                logger.debug(f"Discovered extension: {extension.id}")
                
            except Exception as e:
                logger.error(f"Failed to load extension manifest from {manifest_path}: {str(e)}")
    
    def _record_event(self, extension_id: str, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Record an extension event."""
        event = ExtensionEvent(
            id=str(uuid.uuid4()),
            extension_id=extension_id,
            event_type=event_type,
            data=data or {}
        )
        
        self._events.append(event)
        
        # Call extension event callback if set
        if self._on_extension_event:
            self._on_extension_event(event)