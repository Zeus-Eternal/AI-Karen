"""
Extension Executor Service

This service handles the execution of extensions in the AI Karen system,
providing a sandboxed environment for extension code to run in.
"""

import asyncio
import logging
import sys
from typing import Any, Dict, List, Optional, Union

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus


class ExtensionExecutor(BaseService):
    """
    Extension Executor service for handling execution of extensions.
    
    This service provides capabilities for executing extensions in a sandboxed
    environment, managing their lifecycle, and handling their outputs.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="extension_executor"))
        self._initialized = False
        self._running_executions: Dict[str, Dict[str, Any]] = {}
        self._execution_history: List[Dict[str, Any]] = []
        self._execution_results: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """Initialize the Extension Executor service."""
        try:
            self.logger.info("Initializing Extension Executor service")
            
            # Initialize execution environment
            await self._initialize_execution_environment()
            
            self._initialized = True
            self._status = ServiceStatus.RUNNING
            self.logger.info("Extension Executor service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Extension Executor service: {e}")
            self._status = ServiceStatus.ERROR
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown the Extension Executor service."""
        try:
            self.logger.info("Shutting down Extension Executor service")
            
            # Stop all running executions
            async with self._lock:
                for execution_id in list(self._running_executions.keys()):
                    await self.stop_execution(execution_id)
                
                self._running_executions.clear()
                self._execution_history.clear()
                self._execution_results.clear()
            
            self._initialized = False
            self._status = ServiceStatus.STOPPED
            self.logger.info("Extension Executor service shutdown successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to shutdown Extension Executor service: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check the health of the Extension Executor service."""
        return self._initialized and self._status == ServiceStatus.RUNNING
    
    async def execute_extension(
        self,
        extension_id: str,
        function_name: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> str:
        """
        Execute a function in an extension.
        
        Args:
            extension_id: The ID of the extension
            function_name: The name of the function to execute
            args: Optional list of arguments to pass to the function
            kwargs: Optional dictionary of keyword arguments to pass to the function
            timeout: Optional timeout in seconds
            
        Returns:
            The execution ID
        """
        if not self._initialized:
            raise RuntimeError("Extension Executor service is not initialized")
        
        execution_id = f"{extension_id}_{function_name}_{asyncio.get_event_loop().time()}"
        
        async with self._lock:
            self._running_executions[execution_id] = {
                "extension_id": extension_id,
                "function_name": function_name,
                "args": args or [],
                "kwargs": kwargs or {},
                "timeout": timeout,
                "start_time": asyncio.get_event_loop().time(),
                "status": "running"
            }
        
        # Start the execution in the background
        asyncio.create_task(self._execute_function(execution_id))
        
        return execution_id
    
    async def stop_execution(self, execution_id: str) -> bool:
        """
        Stop a running execution.
        
        Args:
            execution_id: The ID of the execution
            
        Returns:
            True if the execution was stopped successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Executor service is not initialized")
        
        async with self._lock:
            if execution_id not in self._running_executions:
                self.logger.warning(f"Execution {execution_id} is not running")
                return False
            
            # Mark the execution as stopped
            self._running_executions[execution_id]["status"] = "stopped"
            
            # Remove from running executions
            execution_info = self._running_executions.pop(execution_id)
            
            # Add to execution history
            self._execution_history.append({
                "execution_id": execution_id,
                "extension_id": execution_info["extension_id"],
                "function_name": execution_info["function_name"],
                "status": "stopped",
                "end_time": asyncio.get_event_loop().time()
            })
        
        self.logger.info(f"Execution {execution_id} stopped successfully")
        return True
    
    async def get_execution_status(self, execution_id: str) -> Optional[str]:
        """
        Get the status of an execution.
        
        Args:
            execution_id: The ID of the execution
            
        Returns:
            The status of the execution or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension Executor service is not initialized")
        
        async with self._lock:
            if execution_id in self._running_executions:
                return self._running_executions[execution_id]["status"]
            else:
                # Check execution history
                for execution in self._execution_history:
                    if execution["execution_id"] == execution_id:
                        return execution["status"]
                return None
    
    async def get_execution_result(self, execution_id: str) -> Optional[Any]:
        """
        Get the result of an execution.
        
        Args:
            execution_id: The ID of the execution
            
        Returns:
            The result of the execution or None if not found or not completed
        """
        if not self._initialized:
            raise RuntimeError("Extension Executor service is not initialized")
        
        async with self._lock:
            return self._execution_results.get(execution_id)
    
    async def get_running_executions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all running executions.
        
        Returns:
            Dictionary mapping execution IDs to execution information
        """
        if not self._initialized:
            raise RuntimeError("Extension Executor service is not initialized")
        
        async with self._lock:
            return self._running_executions.copy()
    
    async def get_execution_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get the execution history.
        
        Args:
            limit: Optional limit on the number of history items to return
            
        Returns:
            List of execution history items
        """
        if not self._initialized:
            raise RuntimeError("Extension Executor service is not initialized")
        
        async with self._lock:
            if limit is None:
                return self._execution_history.copy()
            else:
                return self._execution_history[-limit:]
    
    async def _execute_function(self, execution_id: str) -> None:
        """
        Execute a function in an extension.
        
        Args:
            execution_id: The ID of the execution
        """
        try:
            async with self._lock:
                if execution_id not in self._running_executions:
                    return
                
                execution_info = self._running_executions[execution_id]
                extension_id = execution_info["extension_id"]
                function_name = execution_info["function_name"]
                args = execution_info["args"]
                kwargs = execution_info["kwargs"]
                timeout = execution_info["timeout"]
            
            # Import the extension module
            try:
                # This is a placeholder for actual extension execution
                # In a real implementation, this would load and execute the extension function
                self.logger.info(f"Executing function {function_name} in extension {extension_id}")
                
                # Simulate function execution
                if timeout:
                    result = await asyncio.wait_for(
                        self._simulate_function_execution(extension_id, function_name, args, kwargs),
                        timeout=timeout
                    )
                else:
                    result = await self._simulate_function_execution(extension_id, function_name, args, kwargs)
                
                # Store the result
                async with self._lock:
                    if execution_id in self._running_executions:
                        self._execution_results[execution_id] = result
                        self._running_executions[execution_id]["status"] = "completed"
                        
                        # Add to execution history
                        self._execution_history.append({
                            "execution_id": execution_id,
                            "extension_id": extension_id,
                            "function_name": function_name,
                            "status": "completed",
                            "end_time": asyncio.get_event_loop().time()
                        })
                        
                        # Remove from running executions
                        self._running_executions.pop(execution_id)
                
                self.logger.info(f"Execution {execution_id} completed successfully")
            except asyncio.TimeoutError:
                async with self._lock:
                    if execution_id in self._running_executions:
                        self._running_executions[execution_id]["status"] = "timeout"
                        
                        # Add to execution history
                        self._execution_history.append({
                            "execution_id": execution_id,
                            "extension_id": extension_id,
                            "function_name": function_name,
                            "status": "timeout",
                            "end_time": asyncio.get_event_loop().time()
                        })
                        
                        # Remove from running executions
                        self._running_executions.pop(execution_id)
                
                self.logger.error(f"Execution {execution_id} timed out")
            except Exception as e:
                async with self._lock:
                    if execution_id in self._running_executions:
                        self._running_executions[execution_id]["status"] = "error"
                        
                        # Add to execution history
                        self._execution_history.append({
                            "execution_id": execution_id,
                            "extension_id": extension_id,
                            "function_name": function_name,
                            "status": "error",
                            "error": str(e),
                            "end_time": asyncio.get_event_loop().time()
                        })
                        
                        # Remove from running executions
                        self._running_executions.pop(execution_id)
                
                self.logger.error(f"Execution {execution_id} failed: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in execution {execution_id}: {e}")
    
    async def _simulate_function_execution(
        self,
        extension_id: str,
        function_name: str,
        args: List[Any],
        kwargs: Dict[str, Any]
    ) -> Any:
        """
        Simulate the execution of a function in an extension.
        
        Args:
            extension_id: The ID of the extension
            function_name: The name of the function to execute
            args: List of arguments to pass to the function
            kwargs: Dictionary of keyword arguments to pass to the function
            
        Returns:
            The result of the function execution
        """
        # This is a placeholder for actual function execution
        # In a real implementation, this would load and execute the extension function
        
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        # Return a dummy result
        return {
            "extension_id": extension_id,
            "function_name": function_name,
            "args": args,
            "kwargs": kwargs,
            "result": "Function executed successfully"
        }
    
    async def _initialize_execution_environment(self) -> None:
        """Initialize the execution environment."""
        # This is a placeholder for execution environment initialization
        # In a real implementation, this would set up the sandboxed environment
        pass