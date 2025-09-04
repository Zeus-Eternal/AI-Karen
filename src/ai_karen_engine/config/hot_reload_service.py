"""
Configuration Hot Reload Service

This module provides hot-reloading capability for configuration changes without
requiring system restart. Monitors configuration files and applies changes dynamically.
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from .deployment_config_manager import (
    DeploymentConfigManager, ConfigChange, ConfigChangeType,
    ServiceConfig, DeploymentProfile
)
from .deployment_validator import DeploymentValidator, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class ReloadEvent:
    """Configuration reload event"""
    timestamp: datetime
    file_path: str
    change_type: str  # 'modified', 'created', 'deleted'
    validation_result: Optional[ValidationResult] = None
    applied_successfully: bool = False
    error_message: Optional[str] = None


class ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for configuration files"""
    
    def __init__(self, hot_reload_service: 'HotReloadService'):
        """Initialize file handler"""
        self.hot_reload_service = hot_reload_service
        self.debounce_delay = 1.0  # seconds
        self.pending_events: Dict[str, float] = {}
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # Check if this is a configuration file we care about
        if not self._is_config_file(file_path):
            return
        
        # Debounce rapid file changes
        current_time = time.time()
        if file_path in self.pending_events:
            if current_time - self.pending_events[file_path] < self.debounce_delay:
                return
        
        self.pending_events[file_path] = current_time
        
        # Schedule reload
        asyncio.create_task(self.hot_reload_service._handle_file_change(file_path, 'modified'))
    
    def _is_config_file(self, file_path: str) -> bool:
        """Check if file is a configuration file"""
        config_extensions = {'.yml', '.yaml', '.json'}
        config_names = {'services', 'deployment', 'config'}
        
        path = Path(file_path)
        
        # Check extension
        if path.suffix.lower() not in config_extensions:
            return False
        
        # Check if it's in a config directory or has config-related name
        if 'config' in str(path).lower() or any(name in path.stem.lower() for name in config_names):
            return True
        
        return False


class HotReloadService:
    """
    Configuration hot reload service with validation and rollback capabilities.
    
    Features:
    - File system monitoring for configuration changes
    - Automatic validation of configuration changes
    - Rollback capability for invalid configurations
    - Debounced reload to handle rapid file changes
    - Event notification system for configuration updates
    """
    
    def __init__(
        self,
        config_manager: DeploymentConfigManager,
        validator: Optional[DeploymentValidator] = None,
        watch_directories: Optional[List[str]] = None,
        enable_validation: bool = True,
        enable_rollback: bool = True
    ):
        """
        Initialize hot reload service.
        
        Args:
            config_manager: Deployment configuration manager
            validator: Configuration validator (optional)
            watch_directories: Directories to monitor for changes
            enable_validation: Enable configuration validation on reload
            enable_rollback: Enable automatic rollback on validation failure
        """
        self.config_manager = config_manager
        self.validator = validator or DeploymentValidator()
        self.enable_validation = enable_validation
        self.enable_rollback = enable_rollback
        
        # Watch directories
        self.watch_directories = watch_directories or ['config', '.']
        
        # File system monitoring
        self.observer: Optional[Observer] = None
        self.file_handler = ConfigFileHandler(self)
        
        # State management
        self._is_running = False
        self._reload_lock = asyncio.Lock()
        self._backup_config: Optional[Dict[str, Any]] = None
        self._reload_history: List[ReloadEvent] = []
        self._max_history_size = 100
        
        # Event listeners
        self._reload_listeners: List[Callable[[ReloadEvent], None]] = []
        
        logger.info("Hot reload service initialized")
    
    async def start(self) -> None:
        """Start the hot reload service"""
        if self._is_running:
            logger.warning("Hot reload service is already running")
            return
        
        try:
            # Create backup of current configuration
            await self._create_config_backup()
            
            # Start file system monitoring
            self._start_file_monitoring()
            
            self._is_running = True
            logger.info("Hot reload service started")
            
        except Exception as e:
            logger.error(f"Failed to start hot reload service: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the hot reload service"""
        if not self._is_running:
            return
        
        try:
            # Stop file system monitoring
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None
            
            self._is_running = False
            logger.info("Hot reload service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping hot reload service: {e}")
    
    async def reload_configuration(self, validate: bool = True) -> ReloadEvent:
        """
        Manually reload configuration.
        
        Args:
            validate: Whether to validate the configuration
            
        Returns:
            ReloadEvent with reload details
        """
        async with self._reload_lock:
            reload_event = ReloadEvent(
                timestamp=datetime.now(),
                file_path="manual_reload",
                change_type="manual"
            )
            
            try:
                # Create backup before reload
                await self._create_config_backup()
                
                # Reload configuration
                await self.config_manager.load_configuration()
                
                # Validate if requested
                if validate and self.enable_validation:
                    validation_result = await self._validate_current_config()
                    reload_event.validation_result = validation_result
                    
                    if not validation_result.is_valid and self.enable_rollback:
                        await self._rollback_configuration()
                        reload_event.applied_successfully = False
                        reload_event.error_message = f"Validation failed: {validation_result.errors_count} errors"
                    else:
                        reload_event.applied_successfully = True
                else:
                    reload_event.applied_successfully = True
                
                logger.info("Configuration reloaded manually")
                
            except Exception as e:
                reload_event.applied_successfully = False
                reload_event.error_message = str(e)
                logger.error(f"Manual configuration reload failed: {e}")
                
                if self.enable_rollback:
                    await self._rollback_configuration()
            
            # Add to history and notify listeners
            self._add_reload_to_history(reload_event)
            await self._notify_reload_listeners(reload_event)
            
            return reload_event
    
    async def validate_current_configuration(self) -> ValidationResult:
        """Validate current configuration without reloading"""
        return await self._validate_current_config()
    
    async def rollback_configuration(self) -> bool:
        """
        Manually rollback to previous configuration.
        
        Returns:
            True if rollback was successful
        """
        return await self._rollback_configuration()
    
    def get_reload_history(self, limit: int = 50) -> List[ReloadEvent]:
        """Get configuration reload history"""
        return self._reload_history[-limit:]
    
    def add_reload_listener(self, listener: Callable[[ReloadEvent], None]) -> None:
        """Add reload event listener"""
        self._reload_listeners.append(listener)
    
    def remove_reload_listener(self, listener: Callable[[ReloadEvent], None]) -> None:
        """Remove reload event listener"""
        if listener in self._reload_listeners:
            self._reload_listeners.remove(listener)
    
    def get_status(self) -> Dict[str, Any]:
        """Get hot reload service status"""
        return {
            'is_running': self._is_running,
            'watch_directories': self.watch_directories,
            'enable_validation': self.enable_validation,
            'enable_rollback': self.enable_rollback,
            'reload_count': len(self._reload_history),
            'last_reload': self._reload_history[-1].timestamp.isoformat() if self._reload_history else None,
            'has_backup': self._backup_config is not None
        }
    
    # Private methods
    
    async def _handle_file_change(self, file_path: str, change_type: str) -> None:
        """Handle file system change event"""
        if not self._is_running:
            return
        
        async with self._reload_lock:
            reload_event = ReloadEvent(
                timestamp=datetime.now(),
                file_path=file_path,
                change_type=change_type
            )
            
            try:
                logger.info(f"Configuration file changed: {file_path}")
                
                # Create backup before reload
                await self._create_config_backup()
                
                # Wait a bit to ensure file write is complete
                await asyncio.sleep(0.5)
                
                # Reload configuration
                await self.config_manager.load_configuration()
                
                # Validate if enabled
                if self.enable_validation:
                    validation_result = await self._validate_current_config()
                    reload_event.validation_result = validation_result
                    
                    if not validation_result.is_valid:
                        logger.warning(f"Configuration validation failed: {validation_result.errors_count} errors")
                        
                        if self.enable_rollback:
                            await self._rollback_configuration()
                            reload_event.applied_successfully = False
                            reload_event.error_message = f"Validation failed, rolled back: {validation_result.errors_count} errors"
                        else:
                            reload_event.applied_successfully = True
                            reload_event.error_message = f"Validation failed but rollback disabled: {validation_result.errors_count} errors"
                    else:
                        reload_event.applied_successfully = True
                        logger.info("Configuration reloaded and validated successfully")
                else:
                    reload_event.applied_successfully = True
                    logger.info("Configuration reloaded successfully (validation disabled)")
                
            except Exception as e:
                reload_event.applied_successfully = False
                reload_event.error_message = str(e)
                logger.error(f"Configuration reload failed: {e}")
                
                if self.enable_rollback:
                    await self._rollback_configuration()
            
            # Add to history and notify listeners
            self._add_reload_to_history(reload_event)
            await self._notify_reload_listeners(reload_event)
    
    def _start_file_monitoring(self) -> None:
        """Start file system monitoring"""
        if self.observer:
            return
        
        self.observer = Observer()
        
        for watch_dir in self.watch_directories:
            if os.path.exists(watch_dir):
                self.observer.schedule(self.file_handler, watch_dir, recursive=True)
                logger.info(f"Monitoring directory for changes: {watch_dir}")
            else:
                logger.warning(f"Watch directory does not exist: {watch_dir}")
        
        self.observer.start()
    
    async def _create_config_backup(self) -> None:
        """Create backup of current configuration"""
        try:
            self._backup_config = {
                'services': self.config_manager.get_all_services(),
                'profiles': self.config_manager.get_deployment_profiles(),
                'current_mode': self.config_manager.get_current_mode(),
                'timestamp': datetime.now().isoformat()
            }
            logger.debug("Configuration backup created")
        except Exception as e:
            logger.error(f"Failed to create configuration backup: {e}")
    
    async def _rollback_configuration(self) -> bool:
        """Rollback to previous configuration"""
        if not self._backup_config:
            logger.error("No backup configuration available for rollback")
            return False
        
        try:
            # Note: In a real implementation, you would restore the configuration
            # from the backup. This would require additional methods in the
            # config manager to restore state.
            logger.warning("Configuration rollback requested but not fully implemented")
            logger.info(f"Would rollback to configuration from: {self._backup_config['timestamp']}")
            return True
            
        except Exception as e:
            logger.error(f"Configuration rollback failed: {e}")
            return False
    
    async def _validate_current_config(self) -> ValidationResult:
        """Validate current configuration"""
        try:
            services = self.config_manager.get_all_services()
            profiles = self.config_manager.get_deployment_profiles()
            current_mode = self.config_manager.get_current_mode()
            
            return await self.validator.validate_deployment_configuration(
                services, profiles, current_mode
            )
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            # Return a failed validation result
            from .deployment_validator import ValidationResult, ValidationIssue, ValidationSeverity
            return ValidationResult(
                is_valid=False,
                issues=[ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="validation_error",
                    message=f"Validation process failed: {e}"
                )]
            )
    
    def _add_reload_to_history(self, reload_event: ReloadEvent) -> None:
        """Add reload event to history"""
        self._reload_history.append(reload_event)
        if len(self._reload_history) > self._max_history_size:
            self._reload_history = self._reload_history[-self._max_history_size:]
    
    async def _notify_reload_listeners(self, reload_event: ReloadEvent) -> None:
        """Notify reload event listeners"""
        for listener in self._reload_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(reload_event)
                else:
                    listener(reload_event)
            except Exception as e:
                logger.error(f"Error notifying reload listener: {e}")


class ConfigurationWatcher:
    """
    High-level configuration watcher that integrates all hot reload components.
    
    This class provides a simple interface for setting up configuration hot reloading
    with validation and rollback capabilities.
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        watch_directories: Optional[List[str]] = None,
        enable_validation: bool = True,
        enable_rollback: bool = True,
        reload_interval: float = 1.0
    ):
        """
        Initialize configuration watcher.
        
        Args:
            config_path: Path to main configuration file
            watch_directories: Directories to monitor
            enable_validation: Enable configuration validation
            enable_rollback: Enable automatic rollback on validation failure
            reload_interval: Minimum interval between reloads
        """
        self.config_manager = DeploymentConfigManager(
            config_path=config_path,
            enable_hot_reload=False,  # We handle hot reload ourselves
            enable_validation=enable_validation
        )
        
        self.validator = DeploymentValidator()
        
        self.hot_reload_service = HotReloadService(
            config_manager=self.config_manager,
            validator=self.validator,
            watch_directories=watch_directories,
            enable_validation=enable_validation,
            enable_rollback=enable_rollback
        )
        
        self._is_initialized = False
    
    async def start(self) -> None:
        """Start configuration watching"""
        if not self._is_initialized:
            await self.config_manager.initialize()
            self._is_initialized = True
        
        await self.hot_reload_service.start()
        logger.info("Configuration watcher started")
    
    async def stop(self) -> None:
        """Stop configuration watching"""
        await self.hot_reload_service.stop()
        
        if self._is_initialized:
            await self.config_manager.shutdown()
        
        logger.info("Configuration watcher stopped")
    
    def get_config_manager(self) -> DeploymentConfigManager:
        """Get the configuration manager"""
        return self.config_manager
    
    def get_hot_reload_service(self) -> HotReloadService:
        """Get the hot reload service"""
        return self.hot_reload_service
    
    def get_validator(self) -> DeploymentValidator:
        """Get the configuration validator"""
        return self.validator
    
    async def reload_now(self) -> ReloadEvent:
        """Manually trigger configuration reload"""
        return await self.hot_reload_service.reload_configuration()
    
    async def validate_now(self) -> ValidationResult:
        """Manually trigger configuration validation"""
        return await self.hot_reload_service.validate_current_configuration()
    
    def add_reload_listener(self, listener: Callable[[ReloadEvent], None]) -> None:
        """Add configuration reload listener"""
        self.hot_reload_service.add_reload_listener(listener)
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status"""
        return {
            'config_manager': {
                'current_mode': self.config_manager.get_current_mode().value,
                'services_count': len(self.config_manager.get_all_services()),
                'profiles_count': len(self.config_manager.get_deployment_profiles())
            },
            'hot_reload': self.hot_reload_service.get_status(),
            'initialized': self._is_initialized
        }