"""
Agent Executor Service

This service is responsible for executing agents, managing their lifecycle,
and handling the results of agent execution.
"""

from typing import Dict, List, Any, Optional, Union, Callable
import logging
import importlib.util
import sys
import os
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import time
import threading
from concurrent.futures import ThreadPoolExecutor, Future

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Enumeration of execution statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class ExecutionContext:
    """Context for agent execution."""
    agent_id: str
    agent_path: str
    agent_config: Dict[str, Any]
    execution_id: str
    input_data: Dict[str, Any]
    timeout: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionResult:
    """Result of agent execution."""
    execution_id: str
    agent_id: str
    status: ExecutionStatus
    output_data: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentExecutor:
    """
    Executes agents and manages their lifecycle.
    
    This class is responsible for:
    - Loading and executing agents
    - Managing agent execution context
    - Handling execution results
    - Managing concurrent execution
    """
    
    def __init__(self, max_workers: int = 4):
        self._max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running_executions: Dict[str, Future] = {}
        self._execution_results: Dict[str, ExecutionResult] = {}
        self._execution_lock = threading.Lock()
        
        # Callbacks for execution events
        self._on_execution_start: Optional[Callable[[ExecutionContext], None]] = None
        self._on_execution_complete: Optional[Callable[[ExecutionResult], None]] = None
        self._on_execution_error: Optional[Callable[[ExecutionResult], None]] = None
    
    def set_execution_callbacks(
        self,
        on_start: Optional[Callable[[ExecutionContext], None]] = None,
        on_complete: Optional[Callable[[ExecutionResult], None]] = None,
        on_error: Optional[Callable[[ExecutionResult], None]] = None
    ) -> None:
        """Set callbacks for execution events."""
        self._on_execution_start = on_start
        self._on_execution_complete = on_complete
        self._on_execution_error = on_error
    
    def execute_agent(self, context: ExecutionContext) -> str:
        """
        Execute an agent with the given context.
        
        Args:
            context: Execution context for the agent
            
        Returns:
            Execution ID
        """
        # Generate execution ID if not provided
        if not context.execution_id:
            context.execution_id = f"{context.agent_id}_{int(time.time() * 1000)}"
        
        # Call start callback if set
        if self._on_execution_start:
            self._on_execution_start(context)
        
        # Submit execution to thread pool
        future = self._executor.submit(self._execute_agent_internal, context)
        
        # Store future and add callback
        with self._execution_lock:
            self._running_executions[context.execution_id] = future
            future.add_done_callback(self._execution_done_callback)
        
        logger.info(f"Submitted execution {context.execution_id} for agent {context.agent_id}")
        return context.execution_id
    
    def execute_agent_sync(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute an agent synchronously.
        
        Args:
            context: Execution context for the agent
            
        Returns:
            Execution result
        """
        # Call start callback if set
        if self._on_execution_start:
            self._on_execution_start(context)
        
        # Execute agent
        result = self._execute_agent_internal(context)
        
        # Call completion callback if set
        if self._on_execution_complete and result.status == ExecutionStatus.COMPLETED:
            self._on_execution_complete(result)
        elif self._on_execution_error and result.status == ExecutionStatus.FAILED:
            self._on_execution_error(result)
        
        return result
    
    def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel a running execution.
        
        Args:
            execution_id: ID of the execution to cancel
            
        Returns:
            True if execution was cancelled, False if not found or already completed
        """
        with self._execution_lock:
            future = self._running_executions.get(execution_id)
            if future and not future.done():
                future.cancel()
                
                # Create cancelled result
                result = ExecutionResult(
                    execution_id=execution_id,
                    agent_id="",  # Will be filled in by callback
                    status=ExecutionStatus.CANCELLED,
                    output_data={},
                    error_message="Execution cancelled"
                )
                
                # Store result
                self._execution_results[execution_id] = result
                
                logger.info(f"Cancelled execution {execution_id}")
                return True
        
        return False
    
    def get_execution_status(self, execution_id: str) -> Optional[ExecutionStatus]:
        """
        Get the status of an execution.
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            Execution status or None if not found
        """
        # Check if execution is still running
        with self._execution_lock:
            if execution_id in self._running_executions:
                future = self._running_executions[execution_id]
                if future.done():
                    # Execution has completed, result should be in _execution_results
                    pass
                else:
                    return ExecutionStatus.RUNNING
            
            # Check if execution has completed
            if execution_id in self._execution_results:
                return self._execution_results[execution_id].status
        
        return None
    
    def get_execution_result(self, execution_id: str) -> Optional[ExecutionResult]:
        """
        Get the result of an execution.
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            Execution result or None if not found or not completed
        """
        with self._execution_lock:
            return self._execution_results.get(execution_id)
    
    def get_all_executions(self) -> Dict[str, ExecutionResult]:
        """Get all execution results."""
        with self._execution_lock:
            return self._execution_results.copy()
    
    def get_running_executions(self) -> List[str]:
        """Get IDs of all running executions."""
        with self._execution_lock:
            return [
                exec_id for exec_id, future in self._running_executions.items()
                if not future.done()
            ]
    
    def clear_execution_results(self) -> None:
        """Clear all execution results."""
        with self._execution_lock:
            self._execution_results.clear()
        logger.info("Cleared all execution results")
    
    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the executor.
        
        Args:
            wait: Whether to wait for pending executions to complete
        """
        self._executor.shutdown(wait=wait)
        logger.info("Agent executor shutdown")
    
    def _execute_agent_internal(self, context: ExecutionContext) -> ExecutionResult:
        """Internal method to execute an agent."""
        start_time = time.time()
        
        try:
            # Load agent module
            agent_module = self._load_agent_module(context.agent_path)
            
            # Get agent class
            agent_class = self._get_agent_class(agent_module)
            
            # Create agent instance
            agent_instance = agent_class(**context.agent_config)
            
            # Initialize agent if needed
            if hasattr(agent_instance, 'initialize'):
                agent_instance.initialize(context.metadata or {})
            
            # Execute agent
            result_data = self._call_agent_execute(agent_instance, context.input_data)
            
            # Finalize agent if needed
            if hasattr(agent_instance, 'finalize'):
                agent_instance.finalize(result_data)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Create result
            result = ExecutionResult(
                execution_id=context.execution_id,
                agent_id=context.agent_id,
                status=ExecutionStatus.COMPLETED,
                output_data=result_data,
                execution_time=execution_time,
                metadata=context.metadata
            )
            
            return result
            
        except Exception as e:
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Create error result
            result = ExecutionResult(
                execution_id=context.execution_id,
                agent_id=context.agent_id,
                status=ExecutionStatus.FAILED,
                output_data={},
                error_message=str(e),
                execution_time=execution_time,
                metadata=context.metadata
            )
            
            logger.error(f"Execution {context.execution_id} failed: {str(e)}")
            return result
    
    def _load_agent_module(self, agent_path: str):
        """Load an agent module from the given path."""
        agent_path_obj = Path(agent_path)
        
        if not agent_path_obj.exists():
            raise FileNotFoundError(f"Agent file not found: {agent_path}")
        
        # Add agent directory to Python path
        agent_dir = agent_path_obj.parent
        if str(agent_dir) not in sys.path:
            sys.path.insert(0, str(agent_dir))
        
        try:
            # Load module
            spec = importlib.util.spec_from_file_location("agent_module", agent_path_obj)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load spec for agent: {agent_path}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            return module
            
        except Exception as e:
            raise ImportError(f"Failed to load agent module from {agent_path}: {str(e)}")
    
    def _get_agent_class(self, agent_module):
        """Get the agent class from the agent module."""
        # Look for a class that implements the standard agent interface
        for name, obj in agent_module.__dict__.items():
            if (isinstance(obj, type) and 
                hasattr(obj, 'execute') and
                hasattr(obj, 'initialize')):
                return obj
        
        raise AttributeError("Agent module does not contain a valid agent class")
    
    def _call_agent_execute(self, agent_instance, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call the execute method of an agent instance."""
        if not hasattr(agent_instance, 'execute'):
            raise AttributeError("Agent instance does not have an execute method")
        
        # Call execute method
        result = agent_instance.execute(input_data)
        
        # Ensure result is a dictionary
        if not isinstance(result, dict):
            raise ValueError("Agent execute method must return a dictionary")
        
        return result
    
    def _execution_done_callback(self, future: Future) -> None:
        """Callback for when an execution is done."""
        # Get execution ID from future
        execution_id = None
        agent_id = None
        
        with self._execution_lock:
            # Find execution ID for this future
            for exec_id, f in self._running_executions.items():
                if f == future:
                    execution_id = exec_id
                    break
            
            # Remove from running executions
            if execution_id:
                self._running_executions.pop(execution_id, None)
        
        if not execution_id:
            logger.warning("Could not find execution ID for completed future")
            return
        
        # Get result
        try:
            result = future.result()
            
            # Store result
            with self._execution_lock:
                self._execution_results[execution_id] = result
            
            # Call completion callback if set
            if self._on_execution_complete and result.status == ExecutionStatus.COMPLETED:
                self._on_execution_complete(result)
            elif self._on_execution_error and result.status == ExecutionStatus.FAILED:
                self._on_execution_error(result)
            
            logger.info(f"Execution {execution_id} completed with status {result.status.value}")
            
        except Exception as e:
            # Create error result
            error_result = ExecutionResult(
                execution_id=execution_id,
                agent_id=agent_id or "unknown",
                status=ExecutionStatus.FAILED,
                output_data={},
                error_message=str(e)
            )
            
            # Store result
            with self._execution_lock:
                self._execution_results[execution_id] = error_result
            
            # Call error callback if set
            if self._on_execution_error:
                self._on_execution_error(error_result)
            
            logger.error(f"Execution {execution_id} failed with exception: {str(e)}")