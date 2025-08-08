"""
Plugin Execution Service with Sandboxing.

This service provides secure plugin execution with input/output validation,
resource management, and timeout controls.
"""

import asyncio
import builtins
import logging
import os
import resource
import signal
import sys
import time
import traceback
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
import uuid
import importlib.util
import multiprocessing
import threading
import types
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, TimeoutError

from pydantic import BaseModel, ConfigDict, Field, validator

from ai_karen_engine.services.plugin_registry import (
    PluginRegistry,
    PluginMetadata,
    PluginStatus,
    get_plugin_registry,
)

logger = logging.getLogger(__name__)


class ExecutionMode(str, Enum):
    """Plugin execution mode."""
    DIRECT = "direct"
    THREAD = "thread"
    PROCESS = "process"
    SANDBOX = "sandbox"


class ExecutionStatus(str, Enum):
    """Plugin execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ResourceLimits:
    """Resource limits for plugin execution."""
    max_memory_mb: int = 128
    max_cpu_time_seconds: int = 30
    max_wall_time_seconds: int = 60
    max_file_descriptors: int = 64
    max_processes: int = 1
    max_threads: int = 4
    max_output_size_kb: int = 1024


@dataclass
class SecurityPolicy:
    """Security policy for plugin execution."""
    allow_network: bool = False
    allow_file_system: bool = False
    allow_subprocess: bool = False
    allow_imports: List[str] = field(default_factory=lambda: [
        "json", "re", "datetime", "math", "random", "uuid", "hashlib",
        "base64", "urllib.parse", "pathlib"
    ])
    blocked_imports: List[str] = field(default_factory=lambda: [
        "os", "sys", "subprocess", "socket", "urllib.request", 
        "requests", "http", "ftplib", "smtplib"
    ])
    allowed_builtins: List[str] = field(default_factory=lambda: [
        "len", "str", "int", "float", "bool", "list", "dict", "tuple",
        "set", "range", "enumerate", "zip", "map", "filter", "sorted",
        "min", "max", "sum", "abs", "round", "print"
    ])


class ExecutionRequest(BaseModel):
    """Plugin execution request."""
    model_config = ConfigDict(extra="allow")
    
    plugin_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    execution_mode: ExecutionMode = ExecutionMode.SANDBOX
    timeout_seconds: int = 30
    resource_limits: Optional[Dict[str, Any]] = None
    security_policy: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class ExecutionResult:
    """Plugin execution result."""
    request_id: str
    plugin_name: str
    status: ExecutionStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    memory_used_mb: float = 0.0
    output_size_bytes: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PluginSandbox:
    """Secure plugin execution sandbox."""

    def __init__(self, resource_limits: ResourceLimits, security_policy: SecurityPolicy):
        self.resource_limits = resource_limits
        self.security_policy = security_policy
        self.original_modules = {}
        self.allowed_builtins: Dict[str, Any] = {}
    
    def __enter__(self):
        """Enter sandbox context."""
        self._setup_resource_limits()
        self._setup_import_restrictions()
        self._setup_builtin_restrictions()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit sandbox context."""
        self._restore_environment()
    
    def _setup_resource_limits(self):
        """Set up resource limits."""
        try:
            # Memory limit
            if hasattr(resource, 'RLIMIT_AS'):
                memory_limit = self.resource_limits.max_memory_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
            
            # CPU time limit
            if hasattr(resource, 'RLIMIT_CPU'):
                cpu_limit = self.resource_limits.max_cpu_time_seconds
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
            
            # File descriptor limit
            if hasattr(resource, 'RLIMIT_NOFILE'):
                fd_limit = self.resource_limits.max_file_descriptors
                resource.setrlimit(resource.RLIMIT_NOFILE, (fd_limit, fd_limit))
            
            # Process limit
            if hasattr(resource, 'RLIMIT_NPROC'):
                proc_limit = self.resource_limits.max_processes
                resource.setrlimit(resource.RLIMIT_NPROC, (proc_limit, proc_limit))
                
        except Exception as e:
            logger.warning(f"Failed to set resource limits: {e}")
    
    def _setup_import_restrictions(self):
        """Set up import restrictions."""
        self.original_import = builtins.__import__

        def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
            """Restricted import function."""
            if name in self.security_policy.blocked_imports:
                raise ImportError(f"Import of '{name}' is not allowed in sandbox")

            if self.security_policy.allow_imports:
                allowed = False
                for allowed_pattern in self.security_policy.allow_imports:
                    if name.startswith(allowed_pattern):
                        allowed = True
                        break
                if not allowed:
                    raise ImportError(f"Import of '{name}' is not allowed in sandbox")

            return self.original_import(name, globals, locals, fromlist, level)

        self._restricted_import = restricted_import

    def _setup_builtin_restrictions(self):
        """Set up builtin function restrictions."""
        allowed = {}
        for name in self.security_policy.allowed_builtins:
            if hasattr(builtins, name):
                allowed[name] = getattr(builtins, name)

        if not self.security_policy.allow_file_system:
            allowed['open'] = self._restricted_open

        allowed['__import__'] = getattr(self, '_restricted_import', builtins.__import__)
        self.allowed_builtins = allowed
    
    def _restricted_open(self, *args, **kwargs):
        """Restricted open function."""
        raise PermissionError("File system access is not allowed in sandbox")

    def _restore_environment(self):
        """Restore original environment."""
        pass


class PluginExecutionEngine:
    """
    Plugin execution engine with sandboxing and resource management.
    """
    
    def __init__(self, registry: Optional[PluginRegistry] = None):
        """Initialize plugin execution engine."""
        self.registry = registry or get_plugin_registry()
        
        # Execution settings
        self.default_resource_limits = ResourceLimits()
        self.default_security_policy = SecurityPolicy()
        self.default_timeout = 30
        
        # Execution tracking
        self.active_executions: Dict[str, ExecutionResult] = {}
        self.execution_history: List[ExecutionResult] = []
        self.max_history_size = 1000
        
        # Thread/process pools
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.process_pool = ProcessPoolExecutor(max_workers=2)
        
        # Metrics
        self.metrics = {
            "executions_total": 0,
            "executions_successful": 0,
            "executions_failed": 0,
            "executions_timeout": 0,
            "average_execution_time": 0.0,
            "total_execution_time": 0.0
        }
    
    async def execute_plugin(self, request: ExecutionRequest) -> ExecutionResult:
        """
        Execute a plugin with the specified parameters.
        
        Args:
            request: Plugin execution request
            
        Returns:
            Execution result
        """
        # Create execution result
        result = ExecutionResult(
            request_id=request.request_id,
            plugin_name=request.plugin_name,
            status=ExecutionStatus.PENDING
        )
        
        # Track active execution
        self.active_executions[request.request_id] = result
        
        try:
            # Validate plugin exists and is registered
            plugin_metadata = self.registry.get_plugin(request.plugin_name)
            if not plugin_metadata:
                raise ValueError(f"Plugin '{request.plugin_name}' not found")
            
            if plugin_metadata.status not in [PluginStatus.REGISTERED, PluginStatus.LOADED, PluginStatus.ACTIVE]:
                raise ValueError(f"Plugin '{request.plugin_name}' is not available for execution")
            
            # Validate and sanitize input
            sanitized_params = await self._validate_and_sanitize_input(
                request.parameters, plugin_metadata
            )
            
            # Set up resource limits and security policy
            resource_limits = ResourceLimits(**(request.resource_limits or {}))
            security_policy = SecurityPolicy(**(request.security_policy or {}))
            
            # Execute plugin based on mode
            result.status = ExecutionStatus.RUNNING
            start_time = time.time()
            
            if request.execution_mode == ExecutionMode.DIRECT:
                plugin_result = await self._execute_direct(
                    plugin_metadata, sanitized_params, resource_limits, security_policy
                )
            elif request.execution_mode == ExecutionMode.THREAD:
                plugin_result = await self._execute_in_thread(
                    plugin_metadata, sanitized_params, resource_limits, security_policy, request.timeout_seconds
                )
            elif request.execution_mode == ExecutionMode.PROCESS:
                plugin_result = await self._execute_in_process(
                    plugin_metadata, sanitized_params, resource_limits, security_policy, request.timeout_seconds
                )
            else:  # SANDBOX mode
                plugin_result = await self._execute_in_sandbox(
                    plugin_metadata, sanitized_params, resource_limits, security_policy, request.timeout_seconds
                )
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Validate and sanitize output
            sanitized_result = await self._validate_and_sanitize_output(
                plugin_result, plugin_metadata, resource_limits
            )
            
            # Update result
            result.status = ExecutionStatus.COMPLETED
            result.result = sanitized_result
            result.execution_time = execution_time
            result.completed_at = datetime.utcnow()
            
            # Update metrics
            self.metrics["executions_successful"] += 1
            
        except TimeoutError:
            result.status = ExecutionStatus.TIMEOUT
            result.error = f"Plugin execution timed out after {request.timeout_seconds} seconds"
            self.metrics["executions_timeout"] += 1
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
            result.metadata["traceback"] = traceback.format_exc()
            self.metrics["executions_failed"] += 1
            logger.error(f"Plugin execution failed: {e}")
        
        finally:
            # Clean up active execution
            self.active_executions.pop(request.request_id, None)
            
            # Add to history
            self._add_to_history(result)
            
            # Update metrics
            self.metrics["executions_total"] += 1
            self.metrics["total_execution_time"] += result.execution_time
            if self.metrics["executions_total"] > 0:
                self.metrics["average_execution_time"] = (
                    self.metrics["total_execution_time"] / self.metrics["executions_total"]
                )
        
        return result
    
    async def _execute_direct(
        self, 
        plugin_metadata: PluginMetadata, 
        parameters: Dict[str, Any],
        resource_limits: ResourceLimits,
        security_policy: SecurityPolicy
    ) -> Any:
        """Execute plugin directly in current context."""
        # Load plugin module
        plugin_module = await self._load_plugin_module(plugin_metadata)
        
        # Get entry point function
        entry_point = getattr(plugin_module, plugin_metadata.manifest.entry_point)
        
        # Execute with sandbox
        with PluginSandbox(resource_limits, security_policy) as sandbox:
            func_globals = dict(entry_point.__globals__)
            func_globals['__builtins__'] = sandbox.allowed_builtins
            restricted = types.FunctionType(
                entry_point.__code__,
                func_globals,
                name=entry_point.__name__,
                argdefs=entry_point.__defaults__,
                closure=entry_point.__closure__,
            )
            if asyncio.iscoroutinefunction(entry_point):
                return await restricted(parameters)
            else:
                return restricted(parameters)
    
    async def _execute_in_thread(
        self,
        plugin_metadata: PluginMetadata,
        parameters: Dict[str, Any],
        resource_limits: ResourceLimits,
        security_policy: SecurityPolicy,
        timeout_seconds: int
    ) -> Any:
        """Execute plugin in a separate thread."""
        def thread_execution():
            # Load plugin module
            plugin_module = self._load_plugin_module_sync(plugin_metadata)
            entry_point = getattr(plugin_module, plugin_metadata.manifest.entry_point)
            
            # Execute with sandbox
            with PluginSandbox(resource_limits, security_policy) as sandbox:
                func_globals = dict(entry_point.__globals__)
                func_globals['__builtins__'] = sandbox.allowed_builtins
                restricted = types.FunctionType(
                    entry_point.__code__,
                    func_globals,
                    name=entry_point.__name__,
                    argdefs=entry_point.__defaults__,
                    closure=entry_point.__closure__,
                )
                return restricted(parameters)
        
        # Execute in thread pool with timeout
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(self.thread_pool, thread_execution)
        
        try:
            return await asyncio.wait_for(future, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Plugin execution timed out after {timeout_seconds} seconds")
    
    async def _execute_in_process(
        self,
        plugin_metadata: PluginMetadata,
        parameters: Dict[str, Any],
        resource_limits: ResourceLimits,
        security_policy: SecurityPolicy,
        timeout_seconds: int
    ) -> Any:
        """Execute plugin in a separate process."""
        def process_execution():
            try:
                # Load plugin module
                plugin_module = self._load_plugin_module_sync(plugin_metadata)
                entry_point = getattr(plugin_module, plugin_metadata.manifest.entry_point)
                
                # Execute with sandbox
                with PluginSandbox(resource_limits, security_policy) as sandbox:
                    func_globals = dict(entry_point.__globals__)
                    func_globals['__builtins__'] = sandbox.allowed_builtins
                    restricted = types.FunctionType(
                        entry_point.__code__,
                        func_globals,
                        name=entry_point.__name__,
                        argdefs=entry_point.__defaults__,
                        closure=entry_point.__closure__,
                    )
                    return restricted(parameters)
            except Exception as e:
                return {"error": str(e), "traceback": traceback.format_exc()}
        
        # Execute in process pool with timeout
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(self.process_pool, process_execution)
        
        try:
            result = await asyncio.wait_for(future, timeout=timeout_seconds)
            
            # Check if result contains error
            if isinstance(result, dict) and "error" in result:
                raise Exception(result["error"])
            
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(f"Plugin execution timed out after {timeout_seconds} seconds")
    
    async def _execute_in_sandbox(
        self,
        plugin_metadata: PluginMetadata,
        parameters: Dict[str, Any],
        resource_limits: ResourceLimits,
        security_policy: SecurityPolicy,
        timeout_seconds: int
    ) -> Any:
        """Execute plugin in enhanced sandbox mode."""
        # For now, use process execution as the sandbox
        # In a production environment, this could use containers or more advanced sandboxing
        return await self._execute_in_process(
            plugin_metadata, parameters, resource_limits, security_policy, timeout_seconds
        )
    
    async def _load_plugin_module(self, plugin_metadata: PluginMetadata):
        """Load plugin module asynchronously."""
        return self._load_plugin_module_sync(plugin_metadata)
    
    def _load_plugin_module_sync(self, plugin_metadata: PluginMetadata):
        """Load plugin module synchronously."""
        plugin_path = plugin_metadata.path
        handler_path = plugin_path / "handler.py"
        
        # Create module spec
        spec = importlib.util.spec_from_file_location(
            f"plugin_{plugin_metadata.manifest.name}",
            handler_path
        )
        
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load plugin module from {handler_path}")
        
        # Load and execute module
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return module
    
    async def _validate_and_sanitize_input(
        self, 
        parameters: Dict[str, Any], 
        plugin_metadata: PluginMetadata
    ) -> Dict[str, Any]:
        """Validate and sanitize plugin input parameters."""
        # Basic validation
        if not isinstance(parameters, dict):
            raise ValueError("Plugin parameters must be a dictionary")
        
        # Size limit check
        import json
        param_size = len(json.dumps(parameters, default=str))
        if param_size > 1024 * 1024:  # 1MB limit
            raise ValueError("Plugin parameters too large")
        
        # TODO: Add more sophisticated validation based on plugin manifest
        # For now, return parameters as-is
        return parameters
    
    async def _validate_and_sanitize_output(
        self,
        result: Any,
        plugin_metadata: PluginMetadata,
        resource_limits: ResourceLimits
    ) -> Any:
        """Validate and sanitize plugin output."""
        # Size limit check
        import json
        try:
            result_json = json.dumps(result, default=str)
            result_size = len(result_json)
            
            max_size = resource_limits.max_output_size_kb * 1024
            if result_size > max_size:
                raise ValueError(f"Plugin output too large: {result_size} bytes > {max_size} bytes")
            
        except (TypeError, ValueError) as e:
            if "too large" in str(e):
                raise
            # If result is not JSON serializable, convert to string
            result = str(result)
            if len(result) > resource_limits.max_output_size_kb * 1024:
                result = result[:resource_limits.max_output_size_kb * 1024] + "... [truncated]"
        
        return result
    
    def _add_to_history(self, result: ExecutionResult):
        """Add execution result to history."""
        self.execution_history.append(result)
        
        # Maintain history size limit
        if len(self.execution_history) > self.max_history_size:
            self.execution_history = self.execution_history[-self.max_history_size:]
    
    async def cancel_execution(self, request_id: str) -> bool:
        """
        Cancel an active plugin execution.
        
        Args:
            request_id: Request ID to cancel
            
        Returns:
            True if cancellation successful, False otherwise
        """
        if request_id not in self.active_executions:
            return False
        
        try:
            result = self.active_executions[request_id]
            result.status = ExecutionStatus.CANCELLED
            result.completed_at = datetime.utcnow()
            
            # TODO: Implement actual cancellation logic for threads/processes
            
            return True
        except Exception as e:
            logger.error(f"Failed to cancel execution {request_id}: {e}")
            return False
    
    def get_active_executions(self) -> List[ExecutionResult]:
        """Get list of active executions."""
        return list(self.active_executions.values())
    
    def get_execution_history(self, limit: int = 100) -> List[ExecutionResult]:
        """Get execution history."""
        return self.execution_history[-limit:]
    
    def get_execution_metrics(self) -> Dict[str, Any]:
        """Get execution metrics."""
        return self.metrics.copy()
    
    async def cleanup(self):
        """Clean up resources."""
        try:
            self.thread_pool.shutdown(wait=True)
            self.process_pool.shutdown(wait=True)
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Global execution engine instance
_execution_engine: Optional[PluginExecutionEngine] = None


def get_plugin_execution_engine() -> PluginExecutionEngine:
    """Get global plugin execution engine instance."""
    global _execution_engine
    if _execution_engine is None:
        _execution_engine = PluginExecutionEngine()
    return _execution_engine


async def initialize_plugin_execution_engine(
    registry: Optional[PluginRegistry] = None
) -> PluginExecutionEngine:
    """
    Initialize the plugin execution engine.
    
    Args:
        registry: Plugin registry to use
        
    Returns:
        Initialized plugin execution engine
    """
    global _execution_engine
    _execution_engine = PluginExecutionEngine(registry)
    return _execution_engine