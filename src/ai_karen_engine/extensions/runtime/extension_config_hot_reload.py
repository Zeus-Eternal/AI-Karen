"""
Extension Configuration Hot Reload service for managing hot reloading of extension configurations.

This service provides capabilities for hot reloading extension configurations without
restarting the service, including configuration change detection and validation.
"""

from typing import Dict, List, Any, Optional, Set, Callable
import asyncio
import logging
import os
import json
import time
from datetime import datetime
from pathlib import Path

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus, ServiceHealth


class ExtensionConfigHotReload(BaseService):
    """
    Extension Configuration Hot Reload service for managing hot reloading of extension configurations.
    
    This service provides capabilities for hot reloading extension configurations without
    restarting the service, including configuration change detection and validation.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="extension_config_hot_reload"))
        self._initialized = False
        self._watched_files: Dict[str, Dict[str, Any]] = {}  # file_path -> watch_info
        self._file_mod_times: Dict[str, float] = {}  # file_path -> modification_time
        self._reload_handlers: Dict[str, List[Callable]] = {}  # file_path -> list_of_handlers
        self._reload_tasks: Dict[str, asyncio.Task] = {}  # file_path -> reload_task
        self._reload_history: List[Dict[str, Any]] = []  # list of reload_events
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize the Extension Configuration Hot Reload service."""
        if self._initialized:
            return
            
        try:
            self.logger.info("Initializing Extension Configuration Hot Reload service")
            
            # Initialize watched files
            self._watched_files = {}
            self._file_mod_times = {}
            self._reload_handlers = {}
            self._reload_tasks = {}
            self._reload_history = []
            
            self._initialized = True
            self._status = ServiceStatus.RUNNING
            self.logger.info("Extension Configuration Hot Reload service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Extension Configuration Hot Reload service: {str(e)}")
            self._status = ServiceStatus.ERROR
            raise
            
    async def watch_file(self, file_path: str, handler: Optional[Callable] = None, 
                        check_interval: int = 5) -> None:
        """Start watching a configuration file for changes."""
        async with self._lock:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Configuration file not found: {file_path}")
                
            # Get current modification time
            mod_time = os.path.getmtime(file_path)
            
            # Initialize watch info
            self._watched_files[file_path] = {
                "check_interval": check_interval,
                "last_check": time.time(),
                "enabled": True
            }
            
            # Store modification time
            self._file_mod_times[file_path] = mod_time
            
            # Register handler if provided
            if handler:
                if file_path not in self._reload_handlers:
                    self._reload_handlers[file_path] = []
                self._reload_handlers[file_path].append(handler)
                
            # Start watching task if not already running
            if file_path not in self._reload_tasks:
                task = asyncio.create_task(self._watch_file_task(file_path))
                self._reload_tasks[file_path] = task
                
        self.logger.info(f"Started watching configuration file: {file_path}")
        
    async def unwatch_file(self, file_path: str) -> None:
        """Stop watching a configuration file."""
        async with self._lock:
            # Cancel watch task if running
            if file_path in self._reload_tasks:
                task = self._reload_tasks[file_path]
                task.cancel()
                del self._reload_tasks[file_path]
                
            # Remove from watched files
            if file_path in self._watched_files:
                del self._watched_files[file_path]
                
            # Remove modification time
            if file_path in self._file_mod_times:
                del self._file_mod_times[file_path]
                
            # Remove handlers
            if file_path in self._reload_handlers:
                del self._reload_handlers[file_path]
                
        self.logger.info(f"Stopped watching configuration file: {file_path}")
        
    async def add_reload_handler(self, file_path: str, handler: Callable) -> None:
        """Add a reload handler for a configuration file."""
        async with self._lock:
            if file_path not in self._reload_handlers:
                self._reload_handlers[file_path] = []
            self._reload_handlers[file_path].append(handler)
            
        self.logger.info(f"Added reload handler for configuration file: {file_path}")
        
    async def remove_reload_handler(self, file_path: str, handler: Callable) -> None:
        """Remove a reload handler for a configuration file."""
        async with self._lock:
            if file_path in self._reload_handlers and handler in self._reload_handlers[file_path]:
                self._reload_handlers[file_path].remove(handler)
                
        self.logger.info(f"Removed reload handler for configuration file: {file_path}")
        
    async def get_watched_files(self) -> List[str]:
        """Get the list of watched configuration files."""
        async with self._lock:
            return list(self._watched_files.keys())
            
    async def is_watched(self, file_path: str) -> bool:
        """Check if a configuration file is being watched."""
        async with self._lock:
            return file_path in self._watched_files
            
    async def get_reload_history(self, file_path: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the reload history for a configuration file or all files."""
        async with self._lock:
            if file_path:
                # Get history for specific file
                history = [event for event in self._reload_history if event.get("file_path") == file_path]
            else:
                # Get history for all files
                history = self._reload_history.copy()
                
            # Sort by timestamp (newest first)
            history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Limit results
            return history[:limit]
            
    async def force_reload(self, file_path: str) -> bool:
        """Force a reload of a configuration file."""
        if not await self.is_watched(file_path):
            raise ValueError(f"Configuration file is not being watched: {file_path}")
            
        try:
            # Load configuration
            config = await self._load_config(file_path)
            
            # Call reload handlers
            handlers = self._reload_handlers.get(file_path, [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(file_path, config)
                    else:
                        handler(file_path, config)
                except Exception as e:
                    self.logger.error(f"Error in reload handler for {file_path}: {str(e)}")
                    
            # Record reload event
            reload_event = {
                "file_path": file_path,
                "timestamp": datetime.now().isoformat(),
                "trigger": "manual",
                "success": True
            }
            
            async with self._lock:
                self._reload_history.append(reload_event)
                
            self.logger.info(f"Force reloaded configuration file: {file_path}")
            return True
            
        except Exception as e:
            # Record failed reload event
            reload_event = {
                "file_path": file_path,
                "timestamp": datetime.now().isoformat(),
                "trigger": "manual",
                "success": False,
                "error": str(e)
            }
            
            async with self._lock:
                self._reload_history.append(reload_event)
                
            self.logger.error(f"Failed to force reload configuration file {file_path}: {str(e)}")
            return False
            
    async def _watch_file_task(self, file_path: str) -> None:
        """Background task to watch a configuration file for changes."""
        try:
            while True:
                try:
                    # Get watch info
                    async with self._lock:
                        if file_path not in self._watched_files:
                            break
                            
                        watch_info = self._watched_files[file_path]
                        check_interval = watch_info["check_interval"]
                        enabled = watch_info["enabled"]
                        
                        # Update last check time
                        watch_info["last_check"] = time.time()
                        
                    # Skip if disabled
                    if not enabled:
                        await asyncio.sleep(check_interval)
                        continue
                        
                    # Check if file exists
                    if not os.path.exists(file_path):
                        self.logger.warning(f"Configuration file disappeared: {file_path}")
                        await asyncio.sleep(check_interval)
                        continue
                        
                    # Check if file has been modified
                    current_mod_time = os.path.getmtime(file_path)
                    last_mod_time = self._file_mod_times.get(file_path, 0)
                    
                    if current_mod_time > last_mod_time:
                        # Update modification time
                        async with self._lock:
                            self._file_mod_times[file_path] = current_mod_time
                            
                        # Reload configuration
                        try:
                            config = await self._load_config(file_path)
                            
                            # Call reload handlers
                            handlers = self._reload_handlers.get(file_path, [])
                            for handler in handlers:
                                try:
                                    if asyncio.iscoroutinefunction(handler):
                                        await handler(file_path, config)
                                    else:
                                        handler(file_path, config)
                                except Exception as e:
                                    self.logger.error(f"Error in reload handler for {file_path}: {str(e)}")
                                    
                            # Record successful reload event
                            reload_event = {
                                "file_path": file_path,
                                "timestamp": datetime.now().isoformat(),
                                "trigger": "file_change",
                                "success": True
                            }
                            
                            async with self._lock:
                                self._reload_history.append(reload_event)
                                
                            self.logger.info(f"Reloaded configuration file due to changes: {file_path}")
                            
                        except Exception as e:
                            # Record failed reload event
                            reload_event = {
                                "file_path": file_path,
                                "timestamp": datetime.now().isoformat(),
                                "trigger": "file_change",
                                "success": False,
                                "error": str(e)
                            }
                            
                            async with self._lock:
                                self._reload_history.append(reload_event)
                                
                            self.logger.error(f"Failed to reload configuration file {file_path}: {str(e)}")
                            
                except Exception as e:
                    self.logger.error(f"Error watching configuration file {file_path}: {str(e)}")
                    
                await asyncio.sleep(check_interval)
                
        except asyncio.CancelledError:
            # Task was cancelled
            pass
        except Exception as e:
            self.logger.error(f"Fatal error in watch task for configuration file {file_path}: {str(e)}")
            
    async def _load_config(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from a file."""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == ".json":
            with open(file_path, "r") as f:
                return json.load(f)
        elif file_ext in [".yaml", ".yml"]:
            import yaml
            with open(file_path, "r") as f:
                return yaml.safe_load(f)
        elif file_ext == ".toml":
            import toml
            with open(file_path, "r") as f:
                return toml.load(f)
        else:
            # Default to JSON
            with open(file_path, "r") as f:
                return json.load(f)
                
    async def health_check(self) -> ServiceHealth:
        """Perform a health check of the service."""
        status = ServiceStatus.RUNNING if self._initialized else ServiceStatus.INITIALIZING
        
        # Check if any watch tasks have failed
        for file_path, task in self._reload_tasks.items():
            if task.done():
                status = ServiceStatus.ERROR
                break
                
        return ServiceHealth(
            status=status,
            last_check=datetime.now(),
            details={
                "watched_files": len(self._watched_files),
                "reload_tasks": len(self._reload_tasks),
                "reload_history": len(self._reload_history)
            }
        )
        
    async def shutdown(self) -> None:
        """Shutdown the service."""
        self.logger.info("Shutting down Extension Configuration Hot Reload service")
        
        # Cancel all watch tasks
        for file_path, task in self._reload_tasks.items():
            task.cancel()
            
        # Wait for all tasks to complete
        if self._reload_tasks:
            await asyncio.gather(*self._reload_tasks.values(), return_exceptions=True)
            
        self._watched_files.clear()
        self._file_mod_times.clear()
        self._reload_handlers.clear()
        self._reload_tasks.clear()
        self._reload_history.clear()
        
        self._initialized = False
        self._status = ServiceStatus.SHUTDOWN
        self.logger.info("Extension Configuration Hot Reload service shutdown complete")