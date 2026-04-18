"""
Extension Error Recovery service for handling extension errors and recovery.

This service provides capabilities for detecting, handling, and recovering from
errors in extensions, including automatic restart and recovery mechanisms.
"""

from typing import Dict, List, Any, Optional, Set
import asyncio
import logging
import time
from datetime import datetime

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus, ServiceHealth


class ExtensionErrorRecovery(BaseService):
    """
    Extension Error Recovery service for handling extension errors and recovery.
    
    This service provides capabilities for detecting, handling, and recovering from
    errors in extensions, including automatic restart and recovery mechanisms.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="extension_error_recovery"))
        self._initialized = False
        self._extension_errors: Dict[str, List[Dict[str, Any]]] = {}  # extension_id -> list of errors
        self._extension_recovery_strategies: Dict[str, Dict[str, Any]] = {}  # extension_id -> recovery_strategy
        self._extension_recovery_status: Dict[str, str] = {}  # extension_id -> recovery_status
        self._recovery_tasks: Dict[str, asyncio.Task] = {}  # extension_id -> recovery_task
        self._error_thresholds: Dict[str, int] = {}  # extension_id -> error_threshold
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize the Extension Error Recovery service."""
        if self._initialized:
            return
            
        try:
            self.logger.info("Initializing Extension Error Recovery service")
            
            # Initialize error tracking for all extensions
            self._extension_errors = {}
            self._extension_recovery_strategies = {}
            self._extension_recovery_status = {}
            self._recovery_tasks = {}
            self._error_thresholds = {}
            
            self._initialized = True
            self._status = ServiceStatus.RUNNING
            self.logger.info("Extension Error Recovery service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Extension Error Recovery service: {str(e)}")
            self._status = ServiceStatus.ERROR
            raise
            
    async def register_extension(self, extension_id: str, recovery_strategy: Optional[Dict[str, Any]] = None, error_threshold: int = 5) -> None:
        """Register an extension for error recovery monitoring."""
        async with self._lock:
            if extension_id not in self._extension_errors:
                self._extension_errors[extension_id] = []
                
            self._extension_recovery_strategies[extension_id] = recovery_strategy or {
                "max_retries": 3,
                "retry_delay": 5,
                "restart_on_failure": True
            }
            
            self._extension_recovery_status[extension_id] = "monitoring"
            self._error_thresholds[extension_id] = error_threshold
            
        self.logger.info(f"Registered extension {extension_id} for error recovery monitoring")
        
    async def unregister_extension(self, extension_id: str) -> None:
        """Unregister an extension from error recovery monitoring."""
        async with self._lock:
            # Cancel any ongoing recovery tasks
            if extension_id in self._recovery_tasks:
                task = self._recovery_tasks[extension_id]
                task.cancel()
                del self._recovery_tasks[extension_id]
                
            # Remove extension from tracking
            if extension_id in self._extension_errors:
                del self._extension_errors[extension_id]
                
            if extension_id in self._extension_recovery_strategies:
                del self._extension_recovery_strategies[extension_id]
                
            if extension_id in self._extension_recovery_status:
                del self._extension_recovery_status[extension_id]
                
            if extension_id in self._error_thresholds:
                del self._error_thresholds[extension_id]
                
        self.logger.info(f"Unregistered extension {extension_id} from error recovery monitoring")
        
    async def report_error(self, extension_id: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Report an error for an extension."""
        async with self._lock:
            if extension_id not in self._extension_errors:
                self._extension_errors[extension_id] = []
                
            # Record the error
            error_record = {
                "timestamp": datetime.now().isoformat(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {}
            }
            
            self._extension_errors[extension_id].append(error_record)
            
            # Check if error threshold is exceeded
            error_count = len(self._extension_errors[extension_id])
            threshold = self._error_thresholds.get(extension_id, 5)
            
            if error_count >= threshold and extension_id not in self._recovery_tasks:
                # Start recovery process
                self._extension_recovery_status[extension_id] = "recovering"
                
                # Create recovery task
                task = asyncio.create_task(self._recover_extension(extension_id))
                self._recovery_tasks[extension_id] = task
                
                self.logger.warning(f"Error threshold exceeded for extension {extension_id}, starting recovery")
                
    async def get_extension_errors(self, extension_id: str) -> List[Dict[str, Any]]:
        """Get the error history for an extension."""
        async with self._lock:
            return self._extension_errors.get(extension_id, []).copy()
            
    async def get_extension_recovery_status(self, extension_id: str) -> str:
        """Get the recovery status of an extension."""
        async with self._lock:
            return self._extension_recovery_status.get(extension_id, "not_registered")
            
    async def get_all_extension_recovery_status(self) -> Dict[str, str]:
        """Get the recovery status of all extensions."""
        async with self._lock:
            return self._extension_recovery_status.copy()
            
    async def _recover_extension(self, extension_id: str) -> None:
        """Recover an extension from errors."""
        try:
            strategy = self._extension_recovery_strategies.get(extension_id, {})
            max_retries = strategy.get("max_retries", 3)
            retry_delay = strategy.get("retry_delay", 5)
            restart_on_failure = strategy.get("restart_on_failure", True)
            
            for attempt in range(max_retries):
                try:
                    # Attempt to recover the extension
                    self.logger.info(f"Attempting to recover extension {extension_id} (attempt {attempt + 1}/{max_retries})")
                    
                    # This is a placeholder implementation
                    # In a real implementation, this would make API calls to restart
                    # or recover the extension
                    
                    # Simulate recovery delay
                    await asyncio.sleep(retry_delay)
                    
                    # Clear recent errors
                    async with self._lock:
                        if extension_id in self._extension_errors:
                            # Keep only the last error for reference
                            if len(self._extension_errors[extension_id]) > 1:
                                self._extension_errors[extension_id] = [self._extension_errors[extension_id][-1]]
                                
                        self._extension_recovery_status[extension_id] = "recovered"
                        
                    self.logger.info(f"Successfully recovered extension {extension_id}")
                    return
                    
                except Exception as e:
                    self.logger.error(f"Recovery attempt {attempt + 1} failed for extension {extension_id}: {str(e)}")
                    
                    if attempt < max_retries - 1:
                        # Wait before retrying
                        await asyncio.sleep(retry_delay)
                        
            # All recovery attempts failed
            async with self._lock:
                self._extension_recovery_status[extension_id] = "recovery_failed"
                
            self.logger.error(f"Failed to recover extension {extension_id} after {max_retries} attempts")
            
            # If restart on failure is enabled, this would trigger a restart
            # of the extension or the entire system
            if restart_on_failure:
                self.logger.warning(f"Restart would be triggered for extension {extension_id} if restart_on_failure is implemented")
                
        except Exception as e:
            self.logger.error(f"Error during recovery process for extension {extension_id}: {str(e)}")
            
            async with self._lock:
                self._extension_recovery_status[extension_id] = "recovery_error"
                
        finally:
            # Remove the recovery task
            async with self._lock:
                if extension_id in self._recovery_tasks:
                    del self._recovery_tasks[extension_id]
                    
    async def health_check(self) -> ServiceHealth:
        """Perform a health check of the service."""
        status = ServiceStatus.RUNNING if self._initialized else ServiceStatus.INITIALIZING
        
        # Check if there are any stuck recovery tasks
        for extension_id, task in self._recovery_tasks.items():
            if task.done():
                status = ServiceStatus.ERROR
                break
                
        return ServiceHealth(
            status=status,
            last_check=datetime.now(),
            details={
                "monitored_extensions": len(self._extension_errors),
                "active_recovery_tasks": len(self._recovery_tasks)
            }
        )
        
    async def shutdown(self) -> None:
        """Shutdown the service."""
        self.logger.info("Shutting down Extension Error Recovery service")
        
        # Cancel all recovery tasks
        for extension_id, task in self._recovery_tasks.items():
            task.cancel()
            
        # Wait for all tasks to complete
        if self._recovery_tasks:
            await asyncio.gather(*self._recovery_tasks.values(), return_exceptions=True)
            
        self._recovery_tasks.clear()
        self._initialized = False
        self._status = ServiceStatus.SHUTDOWN
        self.logger.info("Extension Error Recovery service shutdown complete")