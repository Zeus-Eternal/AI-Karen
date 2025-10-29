"""
Hot-reload system for extension configuration without service restart.
Provides real-time configuration updates with validation and rollback capabilities.

Requirements: 8.4, 8.5
"""

import os
import json
import yaml
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

from .extension_environment_config import (
    ExtensionEnvironmentConfig,
    ExtensionEnvironmentConfigManager,
    Environment,
    get_config_manager
)
from .extension_config_validator import (
    ExtensionConfigValidator,
    ValidationSeverity,
    validate_extension_config
)

logger = logging.getLogger(__name__)


class ReloadTrigger(str, Enum):
    """Types of reload triggers."""
    FILE_CHANGE = "file_change"
    API_REQUEST = "api_request"
    SCHEDULED = "scheduled"
    CREDENTIAL_ROTATION = "credential_rotation"
    HEALTH_CHECK = "health_check"


class ReloadStatus(str, Enum):
    """Status of a reload operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ReloadEvent:
    """Represents a configuration reload event."""
    id: str
    trigger: ReloadTrigger
    environment: Environment
    timestamp: datetime
    status: ReloadStatus
    duration_ms: float = 0.0
    changes: Dict[str, Any] = None
    error: Optional[str] = None
    rollback_reason: Optional[str] = None
    validation_issues: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.changes is None:
            self.changes = {}
        if self.validation_issues is None:
            self.validation_issues = []
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class ConfigurationSnapshot:
    """Represents a snapshot of configuration state for rollback purposes."""
    
    def __init__(self, config: ExtensionEnvironmentConfig, metadata: Dict[str, Any] = None):
        self.config = config
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        self.hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calculate hash of configuration for change detection."""
        config_dict = asdict(self.config)
        config_json = json.dumps(config_dict, sort_keys=True)
        return hashlib.sha256(config_json.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'config': asdict(self.config),
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'hash': self.hash
        }


class ExtensionConfigHotReloader:
    """Manages hot-reload of extension configuration without service restart."""
    
    def __init__(self, config_manager: ExtensionEnvironmentConfigManager):
        self.config_manager = config_manager
        self.validator = ExtensionConfigValidator()
        
        # Reload state
        self.reload_in_progress = False
        self.reload_lock = asyncio.Lock()
        self.reload_history: List[ReloadEvent] = []
        self.max_history_size = 100
        
        # Configuration snapshots for rollback
        self.snapshots: Dict[Environment, List[ConfigurationSnapshot]] = {}
        self.max_snapshots_per_env = 10
        
        # File watching
        self.file_observer: Optional[Observer] = None
        self.file_watcher: Optional['ConfigFileWatcher'] = None
        self.watched_files: Set[str] = set()
        self.file_checksums: Dict[str, str] = {}
        
        # Reload callbacks
        self.pre_reload_callbacks: List[Callable[[Environment, ExtensionEnvironmentConfig], bool]] = []
        self.post_reload_callbacks: List[Callable[[Environment, ExtensionEnvironmentConfig, bool], None]] = []
        self.rollback_callbacks: List[Callable[[Environment, ExtensionEnvironmentConfig], None]] = []
        
        # Debouncing
        self.debounce_delay = 2.0  # seconds
        self.pending_reloads: Dict[str, asyncio.Task] = {}
        
        # Thread pool for file operations
        self.thread_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="config-reload")
        
        # Initialize snapshots
        self._initialize_snapshots()
    
    def _initialize_snapshots(self):
        """Initialize configuration snapshots for all environments."""
        try:
            for environment in Environment:
                config = self.config_manager.get_config(environment)
                snapshot = ConfigurationSnapshot(
                    config,
                    {'source': 'initialization', 'auto_generated': True}
                )
                
                if environment not in self.snapshots:
                    self.snapshots[environment] = []
                
                self.snapshots[environment].append(snapshot)
                logger.debug(f"Created initial snapshot for {environment.value}")
                
        except Exception as e:
            logger.error(f"Failed to initialize configuration snapshots: {e}")
    
    def add_pre_reload_callback(self, callback: Callable[[Environment, ExtensionEnvironmentConfig], bool]):
        """Add a callback to be called before configuration reload.
        
        The callback should return True to allow the reload, False to prevent it.
        """
        self.pre_reload_callbacks.append(callback)
    
    def add_post_reload_callback(self, callback: Callable[[Environment, ExtensionEnvironmentConfig, bool], None]):
        """Add a callback to be called after configuration reload.
        
        The callback receives the environment, new config, and success status.
        """
        self.post_reload_callbacks.append(callback)
    
    def add_rollback_callback(self, callback: Callable[[Environment, ExtensionEnvironmentConfig], None]):
        """Add a callback to be called when configuration is rolled back."""
        self.rollback_callbacks.append(callback)
    
    async def reload_configuration(
        self,
        environment: Optional[Environment] = None,
        trigger: ReloadTrigger = ReloadTrigger.API_REQUEST,
        force: bool = False
    ) -> ReloadEvent:
        """Reload configuration for specified environment or current environment."""
        
        if environment is None:
            environment = self.config_manager.current_environment
        
        reload_id = f"{environment.value}_{int(time.time() * 1000)}"
        start_time = datetime.utcnow()
        
        reload_event = ReloadEvent(
            id=reload_id,
            trigger=trigger,
            environment=environment,
            timestamp=start_time,
            status=ReloadStatus.PENDING
        )
        
        try:
            async with self.reload_lock:
                if self.reload_in_progress and not force:
                    reload_event.status = ReloadStatus.FAILED
                    reload_event.error = "Another reload is already in progress"
                    self._add_to_history(reload_event)
                    return reload_event
                
                self.reload_in_progress = True
                reload_event.status = ReloadStatus.IN_PROGRESS
                
                logger.info(f"Starting configuration reload for {environment.value} (trigger: {trigger.value})")
                
                # Create snapshot of current configuration
                current_config = self.config_manager.get_config(environment)
                self._create_snapshot(environment, current_config, {
                    'source': 'pre_reload',
                    'trigger': trigger.value,
                    'reload_id': reload_id
                })
                
                # Run pre-reload callbacks
                if not await self._run_pre_reload_callbacks(environment, current_config):
                    reload_event.status = ReloadStatus.FAILED
                    reload_event.error = "Pre-reload callback prevented reload"
                    self._add_to_history(reload_event)
                    return reload_event
                
                # Load new configuration
                new_config = await self._load_new_configuration(environment)
                
                # Detect changes
                changes = self._detect_changes(current_config, new_config)
                reload_event.changes = changes
                
                if not changes and not force:
                    reload_event.status = ReloadStatus.SUCCESS
                    reload_event.error = "No changes detected"
                    logger.info(f"No configuration changes detected for {environment.value}")
                    self._add_to_history(reload_event)
                    return reload_event
                
                # Validate new configuration
                validation_result = await self._validate_configuration(new_config)
                reload_event.validation_issues = validation_result.get('issues', [])
                
                if not validation_result.get('valid', False):
                    reload_event.status = ReloadStatus.FAILED
                    reload_event.error = "Configuration validation failed"
                    logger.error(f"Configuration validation failed for {environment.value}")
                    self._add_to_history(reload_event)
                    return reload_event
                
                # Apply new configuration
                success = await self._apply_configuration(environment, new_config)
                
                if success:
                    reload_event.status = ReloadStatus.SUCCESS
                    
                    # Create snapshot of new configuration
                    self._create_snapshot(environment, new_config, {
                        'source': 'post_reload',
                        'trigger': trigger.value,
                        'reload_id': reload_id,
                        'changes': changes
                    })
                    
                    # Run post-reload callbacks
                    await self._run_post_reload_callbacks(environment, new_config, True)
                    
                    logger.info(f"Configuration reload successful for {environment.value}")
                else:
                    reload_event.status = ReloadStatus.FAILED
                    reload_event.error = "Failed to apply configuration"
                    
                    # Attempt rollback
                    rollback_success = await self._rollback_configuration(environment, reload_id)
                    if rollback_success:
                        reload_event.status = ReloadStatus.ROLLED_BACK
                        reload_event.rollback_reason = "Application failure"
                    
                    logger.error(f"Configuration reload failed for {environment.value}")
                
        except Exception as e:
            reload_event.status = ReloadStatus.FAILED
            reload_event.error = str(e)
            logger.error(f"Configuration reload error for {environment.value}: {e}")
            
            # Attempt rollback on error
            try:
                rollback_success = await self._rollback_configuration(environment, reload_id)
                if rollback_success:
                    reload_event.status = ReloadStatus.ROLLED_BACK
                    reload_event.rollback_reason = f"Exception: {e}"
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {rollback_error}")
        
        finally:
            self.reload_in_progress = False
            reload_event.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._add_to_history(reload_event)
        
        return reload_event
    
    async def _load_new_configuration(self, environment: Environment) -> ExtensionEnvironmentConfig:
        """Load new configuration from files."""
        try:
            # Force reload from files
            return await asyncio.get_event_loop().run_in_executor(
                self.thread_pool,
                self.config_manager._load_environment_config,
                environment
            )
        except Exception as e:
            logger.error(f"Failed to load new configuration for {environment.value}: {e}")
            raise
    
    def _detect_changes(
        self,
        old_config: ExtensionEnvironmentConfig,
        new_config: ExtensionEnvironmentConfig
    ) -> Dict[str, Any]:
        """Detect changes between old and new configuration."""
        try:
            old_dict = asdict(old_config)
            new_dict = asdict(new_config)
            
            changes = {}
            
            for key, new_value in new_dict.items():
                old_value = old_dict.get(key)
                if old_value != new_value:
                    changes[key] = {
                        'old': old_value,
                        'new': new_value
                    }
            
            # Check for removed keys
            for key in old_dict:
                if key not in new_dict:
                    changes[key] = {
                        'old': old_dict[key],
                        'new': None,
                        'removed': True
                    }
            
            return changes
            
        except Exception as e:
            logger.error(f"Failed to detect configuration changes: {e}")
            return {}
    
    async def _validate_configuration(self, config: ExtensionEnvironmentConfig) -> Dict[str, Any]:
        """Validate configuration asynchronously."""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                self.thread_pool,
                self._sync_validate_configuration,
                config
            )
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return {'valid': False, 'error': str(e)}
    
    def _sync_validate_configuration(self, config: ExtensionEnvironmentConfig) -> Dict[str, Any]:
        """Synchronous configuration validation."""
        issues = self.validator.validate_config(config)
        
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        error_issues = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        
        return {
            'valid': len(critical_issues) == 0 and len(error_issues) == 0,
            'issues': [issue.to_dict() for issue in issues],
            'critical_count': len(critical_issues),
            'error_count': len(error_issues)
        }
    
    async def _apply_configuration(self, environment: Environment, config: ExtensionEnvironmentConfig) -> bool:
        """Apply new configuration to the system."""
        try:
            # Update configuration in manager
            self.config_manager.configurations[environment] = config
            
            # If this is the current environment, trigger callbacks
            if environment == self.config_manager.current_environment:
                self.config_manager._trigger_reload_callbacks(config)
            
            logger.info(f"Applied new configuration for {environment.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply configuration for {environment.value}: {e}")
            return False
    
    async def _run_pre_reload_callbacks(
        self,
        environment: Environment,
        config: ExtensionEnvironmentConfig
    ) -> bool:
        """Run pre-reload callbacks and check if reload should proceed."""
        try:
            for callback in self.pre_reload_callbacks:
                try:
                    result = callback(environment, config)
                    if not result:
                        logger.warning(f"Pre-reload callback prevented reload for {environment.value}")
                        return False
                except Exception as e:
                    logger.error(f"Pre-reload callback error: {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to run pre-reload callbacks: {e}")
            return False
    
    async def _run_post_reload_callbacks(
        self,
        environment: Environment,
        config: ExtensionEnvironmentConfig,
        success: bool
    ):
        """Run post-reload callbacks."""
        try:
            for callback in self.post_reload_callbacks:
                try:
                    callback(environment, config, success)
                except Exception as e:
                    logger.error(f"Post-reload callback error: {e}")
        except Exception as e:
            logger.error(f"Failed to run post-reload callbacks: {e}")
    
    async def _rollback_configuration(self, environment: Environment, reload_id: str) -> bool:
        """Rollback configuration to previous snapshot."""
        try:
            snapshots = self.snapshots.get(environment, [])
            if len(snapshots) < 2:
                logger.error(f"No previous snapshot available for rollback in {environment.value}")
                return False
            
            # Get the snapshot before the current one
            previous_snapshot = snapshots[-2]
            
            logger.info(f"Rolling back configuration for {environment.value} to snapshot from {previous_snapshot.timestamp}")
            
            # Apply previous configuration
            success = await self._apply_configuration(environment, previous_snapshot.config)
            
            if success:
                # Run rollback callbacks
                for callback in self.rollback_callbacks:
                    try:
                        callback(environment, previous_snapshot.config)
                    except Exception as e:
                        logger.error(f"Rollback callback error: {e}")
                
                logger.info(f"Configuration rollback successful for {environment.value}")
                return True
            else:
                logger.error(f"Configuration rollback failed for {environment.value}")
                return False
                
        except Exception as e:
            logger.error(f"Configuration rollback error for {environment.value}: {e}")
            return False
    
    def _create_snapshot(
        self,
        environment: Environment,
        config: ExtensionEnvironmentConfig,
        metadata: Dict[str, Any]
    ):
        """Create a configuration snapshot."""
        try:
            snapshot = ConfigurationSnapshot(config, metadata)
            
            if environment not in self.snapshots:
                self.snapshots[environment] = []
            
            self.snapshots[environment].append(snapshot)
            
            # Limit number of snapshots
            if len(self.snapshots[environment]) > self.max_snapshots_per_env:
                self.snapshots[environment] = self.snapshots[environment][-self.max_snapshots_per_env:]
            
            logger.debug(f"Created configuration snapshot for {environment.value}")
            
        except Exception as e:
            logger.error(f"Failed to create configuration snapshot: {e}")
    
    def _add_to_history(self, reload_event: ReloadEvent):
        """Add reload event to history."""
        try:
            self.reload_history.append(reload_event)
            
            # Limit history size
            if len(self.reload_history) > self.max_history_size:
                self.reload_history = self.reload_history[-self.max_history_size:]
                
        except Exception as e:
            logger.error(f"Failed to add reload event to history: {e}")
    
    def start_file_watching(self):
        """Start watching configuration files for changes."""
        try:
            if self.file_observer:
                logger.warning("File watching is already active")
                return
            
            self.file_watcher = ConfigFileWatcher(self)
            self.file_observer = Observer()
            
            # Watch config directory
            self.file_observer.schedule(
                self.file_watcher,
                str(self.config_manager.config_dir),
                recursive=True
            )
            
            # Watch credentials directory
            self.file_observer.schedule(
                self.file_watcher,
                str(self.config_manager.credentials_manager.storage_path),
                recursive=True
            )
            
            self.file_observer.start()
            
            # Initialize file checksums
            self._update_file_checksums()
            
            logger.info("Started configuration file watching")
            
        except Exception as e:
            logger.error(f"Failed to start file watching: {e}")
    
    def stop_file_watching(self):
        """Stop watching configuration files."""
        try:
            if self.file_observer:
                self.file_observer.stop()
                self.file_observer.join(timeout=5)
                self.file_observer = None
                self.file_watcher = None
                logger.info("Stopped configuration file watching")
        except Exception as e:
            logger.error(f"Failed to stop file watching: {e}")
    
    def _update_file_checksums(self):
        """Update checksums for watched files."""
        try:
            config_files = list(self.config_manager.config_dir.glob("*.yaml")) + \
                          list(self.config_manager.config_dir.glob("*.yml")) + \
                          list(self.config_manager.config_dir.glob("*.json"))
            
            for file_path in config_files:
                if file_path.is_file():
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read()
                            checksum = hashlib.md5(content).hexdigest()
                            self.file_checksums[str(file_path)] = checksum
                            self.watched_files.add(str(file_path))
                    except Exception as e:
                        logger.error(f"Failed to calculate checksum for {file_path}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to update file checksums: {e}")
    
    async def _handle_file_change(self, file_path: str):
        """Handle configuration file change."""
        try:
            # Check if file actually changed
            if not os.path.exists(file_path):
                logger.debug(f"File no longer exists: {file_path}")
                return
            
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    new_checksum = hashlib.md5(content).hexdigest()
            except Exception as e:
                logger.error(f"Failed to read file {file_path}: {e}")
                return
            
            old_checksum = self.file_checksums.get(file_path)
            if old_checksum == new_checksum:
                logger.debug(f"File content unchanged: {file_path}")
                return
            
            self.file_checksums[file_path] = new_checksum
            
            logger.info(f"Configuration file changed: {file_path}")
            
            # Determine which environment(s) to reload
            file_name = Path(file_path).stem
            environments_to_reload = []
            
            for env in Environment:
                if file_name == env.value or file_name == "common":
                    environments_to_reload.append(env)
            
            if not environments_to_reload:
                # If we can't determine the environment, reload current environment
                environments_to_reload = [self.config_manager.current_environment]
            
            # Trigger reload for each environment
            for environment in environments_to_reload:
                await self._debounced_reload(environment, ReloadTrigger.FILE_CHANGE)
                
        except Exception as e:
            logger.error(f"Failed to handle file change for {file_path}: {e}")
    
    async def _debounced_reload(self, environment: Environment, trigger: ReloadTrigger):
        """Perform debounced configuration reload."""
        reload_key = f"{environment.value}_{trigger.value}"
        
        # Cancel existing pending reload
        if reload_key in self.pending_reloads:
            self.pending_reloads[reload_key].cancel()
        
        # Schedule new reload
        self.pending_reloads[reload_key] = asyncio.create_task(
            self._delayed_reload(environment, trigger, self.debounce_delay)
        )
    
    async def _delayed_reload(self, environment: Environment, trigger: ReloadTrigger, delay: float):
        """Perform reload after delay."""
        try:
            await asyncio.sleep(delay)
            await self.reload_configuration(environment, trigger)
        except asyncio.CancelledError:
            logger.debug(f"Delayed reload cancelled for {environment.value}")
        except Exception as e:
            logger.error(f"Delayed reload failed for {environment.value}: {e}")
        finally:
            reload_key = f"{environment.value}_{trigger.value}"
            self.pending_reloads.pop(reload_key, None)
    
    def get_reload_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get reload history."""
        try:
            recent_events = self.reload_history[-limit:] if limit > 0 else self.reload_history
            return [event.to_dict() for event in recent_events]
        except Exception as e:
            logger.error(f"Failed to get reload history: {e}")
            return []
    
    def get_snapshots(self, environment: Environment, limit: int = 10) -> List[Dict[str, Any]]:
        """Get configuration snapshots for an environment."""
        try:
            snapshots = self.snapshots.get(environment, [])
            recent_snapshots = snapshots[-limit:] if limit > 0 else snapshots
            return [snapshot.to_dict() for snapshot in recent_snapshots]
        except Exception as e:
            logger.error(f"Failed to get snapshots for {environment.value}: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get hot-reload system status."""
        try:
            return {
                'reload_in_progress': self.reload_in_progress,
                'file_watching_active': self.file_observer is not None and self.file_observer.is_alive(),
                'watched_files_count': len(self.watched_files),
                'pending_reloads_count': len(self.pending_reloads),
                'reload_history_count': len(self.reload_history),
                'snapshots_count': {env.value: len(snapshots) for env, snapshots in self.snapshots.items()},
                'debounce_delay_seconds': self.debounce_delay,
                'last_reload': self.reload_history[-1].to_dict() if self.reload_history else None
            }
        except Exception as e:
            logger.error(f"Failed to get hot-reload status: {e}")
            return {'error': str(e)}
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            # Stop file watching
            self.stop_file_watching()
            
            # Cancel pending reloads
            for task in self.pending_reloads.values():
                task.cancel()
            self.pending_reloads.clear()
            
            # Shutdown thread pool
            self.thread_pool.shutdown(wait=True)
            
            logger.info("Hot-reload system cleanup completed")
            
        except Exception as e:
            logger.error(f"Failed to cleanup hot-reload system: {e}")


class ConfigFileWatcher(FileSystemEventHandler):
    """Watches configuration files for changes."""
    
    def __init__(self, hot_reloader: ExtensionConfigHotReloader):
        self.hot_reloader = hot_reloader
        self.supported_extensions = {'.yaml', '.yml', '.json', '.env'}
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if file_path.suffix.lower() in self.supported_extensions:
            asyncio.create_task(self.hot_reloader._handle_file_change(str(file_path)))
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if file_path.suffix.lower() in self.supported_extensions:
            asyncio.create_task(self.hot_reloader._handle_file_change(str(file_path)))


# Global hot-reloader instance
hot_reloader: Optional[ExtensionConfigHotReloader] = None


def get_hot_reloader() -> ExtensionConfigHotReloader:
    """Get the global hot-reloader instance."""
    global hot_reloader
    if hot_reloader is None:
        config_manager = get_config_manager()
        hot_reloader = ExtensionConfigHotReloader(config_manager)
    return hot_reloader


async def initialize_hot_reload():
    """Initialize the hot-reload system."""
    try:
        reloader = get_hot_reloader()
        reloader.start_file_watching()
        logger.info("Extension configuration hot-reload system initialized")
    except Exception as e:
        logger.error(f"Failed to initialize hot-reload system: {e}")
        raise


def shutdown_hot_reload():
    """Shutdown the hot-reload system."""
    try:
        global hot_reloader
        if hot_reloader:
            hot_reloader.cleanup()
            hot_reloader = None
        logger.info("Extension configuration hot-reload system shutdown")
    except Exception as e:
        logger.error(f"Failed to shutdown hot-reload system: {e}")


async def reload_extension_config(
    environment: Optional[Environment] = None,
    force: bool = False
) -> Dict[str, Any]:
    """Reload extension configuration."""
    try:
        reloader = get_hot_reloader()
        reload_event = await reloader.reload_configuration(
            environment=environment,
            trigger=ReloadTrigger.API_REQUEST,
            force=force
        )
        return reload_event.to_dict()
    except Exception as e:
        logger.error(f"Failed to reload extension configuration: {e}")
        return {
            'status': ReloadStatus.FAILED.value,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }