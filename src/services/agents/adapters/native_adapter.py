"""
Native Adapter for Agent Architecture System.

This module provides native agent execution capabilities without relying on external frameworks
like LangChain or LangGraph. It implements a lightweight, efficient agent execution engine
that is optimized for the CoPilot architecture.
"""

import os
import logging
import json
import asyncio
import time
from typing import Any, Dict, List, Optional, Union, Type, Callable, Awaitable
from datetime import datetime
from enum import Enum

# Local application imports
from ..internal.agent_schemas import (
    AgentDefinition, AgentTask, AgentResponse, AgentTool, AgentMemory,
    AgentStatus, TaskStatus, MessageStatus
)
from ..internal.agent_validation import AgentValidation
from ..agent_memory import EnhancedAgentMemory
from ..agent_tool_broker import AgentToolBroker
from ..agent_reasoning import AgentReasoningEngine

logger = logging.getLogger(__name__)


class NativeExecutionMode(str, Enum):
    """Native execution mode enumeration."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ITERATIVE = "iterative"
    RECURSIVE = "recursive"


class NativeAdapter:
    """
    Adapter for native agent execution without external frameworks.
    
    This adapter provides functionality to:
    1. Execute agent tasks using native implementation
    2. Support different execution modes (sequential, parallel, iterative, recursive)
    3. Integrate with agent memory and tool systems
    4. Provide reasoning capabilities for complex tasks
    5. Handle task dependencies and workflows
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        agent_validation: Optional[AgentValidation] = None,
        agent_memory: Optional[EnhancedAgentMemory] = None,
        tool_broker: Optional[AgentToolBroker] = None,
        reasoning_engine: Optional[AgentReasoningEngine] = None
    ):
        """
        Initialize the Native adapter.
        
        Args:
            config: Configuration dictionary for the adapter
            agent_validation: Agent validation service instance
            agent_memory: Agent memory service instance
            tool_broker: Agent tool broker instance
            reasoning_engine: Agent reasoning engine instance
        """
        self.config = config or {}
        self.agent_validation = agent_validation
        self.agent_memory = agent_memory
        self.tool_broker = tool_broker
        self.reasoning_engine = reasoning_engine
        
        # Adapter configuration
        self._enable_error_handling = True
        self._max_execution_time = 300  # seconds
        self._verbose = self.config.get("verbose", False)
        self._default_execution_mode = self.config.get("default_execution_mode", NativeExecutionMode.SEQUENTIAL)
        self._enable_caching = self.config.get("enable_caching", True)
        self._cache_size = self.config.get("cache_size", 100)
        self._enable_parallelism = self.config.get("enable_parallelism", True)
        self._max_parallel_tasks = self.config.get("max_parallel_tasks", 5)
        
        # Task execution cache
        self._execution_cache: Dict[str, Any] = {}
        
        # Task registry
        self._task_registry: Dict[str, AgentTask] = {}
        self._task_functions: Dict[str, Callable] = {}
        
        logger.info("Native adapter initialized successfully")
    
    def register_task_function(
        self, 
        task_type: str, 
        function: Callable[[AgentTask], Awaitable[AgentResponse]]
    ) -> bool:
        """
        Register a task function for a specific task type.
        
        Args:
            task_type: Type of task to register
            function: Function to execute for this task type
            
        Returns:
            True if registration was successful, False otherwise
        """
        if not asyncio.iscoroutinefunction(function):
            logger.error(f"Function for task type {task_type} is not a coroutine function")
            return False
        
        self._task_functions[task_type] = function
        logger.info(f"Registered function for task type {task_type}")
        return True
    
    def unregister_task_function(self, task_type: str) -> bool:
        """
        Unregister a task function for a specific task type.
        
        Args:
            task_type: Type of task to unregister
            
        Returns:
            True if unregistration was successful, False otherwise
        """
        if task_type not in self._task_functions:
            logger.warning(f"No function registered for task type {task_type}")
            return False
        
        del self._task_functions[task_type]
        logger.info(f"Unregistered function for task type {task_type}")
        return True
    
    async def execute_task(
        self, 
        task: AgentTask, 
        execution_mode: Optional[NativeExecutionMode] = None
    ) -> AgentResponse:
        """
        Execute an agent task using the native implementation.
        
        Args:
            task: Task to execute
            execution_mode: Execution mode to use (if None, uses default)
            
        Returns:
            Agent response with execution results
        """
        # Validate task
        if self.agent_validation:
            is_valid, errors = await self.agent_validation.validate_task(task)
            if not is_valid:
                logger.error(f"Task validation failed: {errors}")
                return AgentResponse(
                    response_id=f"resp_{task.task_id}",
                    task_id=task.task_id,
                    agent_id=task.agent_id,
                    success=False,
                    data={},
                    error=f"Task validation failed: {errors}",
                    execution_time=0.0
                )
        
        # Set execution mode
        execution_mode = execution_mode or self._default_execution_mode
        
        # Check cache if enabled
        if self._enable_caching:
            cache_key = self._generate_cache_key(task, execution_mode)
            if cache_key in self._execution_cache:
                logger.info(f"Using cached result for task {task.task_id}")
                return self._execution_cache[cache_key]
        
        # Register task
        self._task_registry[task.task_id] = task
        
        # Execute task based on mode
        try:
            start_time = time.time()
            
            if execution_mode == NativeExecutionMode.SEQUENTIAL:
                result = await self._execute_sequential(task)
            elif execution_mode == NativeExecutionMode.PARALLEL:
                result = await self._execute_parallel(task)
            elif execution_mode == NativeExecutionMode.ITERATIVE:
                result = await self._execute_iterative(task)
            elif execution_mode == NativeExecutionMode.RECURSIVE:
                result = await self._execute_recursive(task)
            else:
                logger.error(f"Unknown execution mode: {execution_mode}")
                result = AgentResponse(
                    response_id=f"resp_{task.task_id}",
                    task_id=task.task_id,
                    agent_id=task.agent_id,
                    success=False,
                    data={},
                    error=f"Unknown execution mode: {execution_mode}",
                    execution_time=0.0
                )
            
            execution_time = time.time() - start_time
            
            # Update execution time
            result.execution_time = execution_time
            
            # Cache result if enabled and successful
            if self._enable_caching and result.success:
                self._execution_cache[cache_key] = result
                # Limit cache size
                if len(self._execution_cache) > self._cache_size:
                    # Remove oldest entry
                    oldest_key = next(iter(self._execution_cache))
                    del self._execution_cache[oldest_key]
            
            # Remove task from registry
            if task.task_id in self._task_registry:
                del self._task_registry[task.task_id]
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {e}")
            
            # Remove task from registry
            if task.task_id in self._task_registry:
                del self._task_registry[task.task_id]
            
            return AgentResponse(
                response_id=f"resp_{task.task_id}",
                task_id=task.task_id,
                agent_id=task.agent_id,
                success=False,
                data={},
                error=str(e),
                execution_time=0.0
            )
    
    def _generate_cache_key(self, task: AgentTask, execution_mode: NativeExecutionMode) -> str:
        """Generate a cache key for a task."""
        # Create a hash of the task and execution mode
        task_data = {
            "task_type": task.task_type,
            "description": task.description,
            "input_data": task.input_data,
            "execution_mode": execution_mode.value
        }
        task_str = json.dumps(task_data, sort_keys=True)
        return f"native_{hash(task_str)}"
    
    async def _execute_sequential(self, task: AgentTask) -> AgentResponse:
        """Execute a task in sequential mode."""
        logger.info(f"Executing task {task.task_id} in sequential mode")
        
        # Check if there's a registered function for this task type
        if task.task_type in self._task_functions:
            return await self._task_functions[task.task_type](task)
        
        # Default sequential execution
        result_data = {}
        
        # Execute reasoning step if available
        if self.reasoning_engine:
            reasoning_result = await self.reasoning_engine.reason(task)
            if reasoning_result.success:
                result_data["reasoning"] = reasoning_result.data
        
        # Execute tools if specified
        if task.tools and self.tool_broker:
            tool_results = await self.tool_broker.execute_tools(task.tools, task.input_data or {})
            if tool_results:
                result_data["tool_results"] = tool_results
        
        # Generate response
        response = self._generate_response(task, result_data)
        
        # Store in memory if available
        if self.agent_memory:
            await self.agent_memory.store_task_result(task, response)
        
        return response
    
    async def _execute_parallel(self, task: AgentTask) -> AgentResponse:
        """Execute a task in parallel mode."""
        logger.info(f"Executing task {task.task_id} in parallel mode")
        
        if not self._enable_parallelism:
            logger.warning("Parallelism is disabled, falling back to sequential execution")
            return await self._execute_sequential(task)
        
        # Check if there's a registered function for this task type
        if task.task_type in self._task_functions:
            return await self._task_functions[task.task_type](task)
        
        # Default parallel execution
        tasks = []
        
        # Add reasoning task if available
        if self.reasoning_engine:
            tasks.append(self.reasoning_engine.reason(task))
        
        # Add tool execution tasks if specified
        if task.tools and self.tool_broker:
            tasks.append(self.tool_broker.execute_tools(task.tools, task.input_data or {}))
        
        # Execute tasks in parallel
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            result_data = {}
            
            # Process reasoning result
            if self.reasoning_engine and len(results) > 0:
                reasoning_result = results[0]
                if isinstance(reasoning_result, Exception):
                    logger.error(f"Error in parallel reasoning: {reasoning_result}")
                elif reasoning_result.success:
                    result_data["reasoning"] = reasoning_result.data
            
            # Process tool results
            if task.tools and self.tool_broker and len(results) > 1:
                tool_results = results[1]
                if isinstance(tool_results, Exception):
                    logger.error(f"Error in parallel tool execution: {tool_results}")
                elif tool_results:
                    result_data["tool_results"] = tool_results
            
            # Generate response
            response = self._generate_response(task, result_data)
            
            # Store in memory if available
            if self.agent_memory:
                await self.agent_memory.store_task_result(task, response)
            
            return response
        else:
            # No parallel tasks, fall back to sequential
            return await self._execute_sequential(task)
    
    async def _execute_iterative(self, task: AgentTask) -> AgentResponse:
        """Execute a task in iterative mode."""
        logger.info(f"Executing task {task.task_id} in iterative mode")
        
        # Check if there's a registered function for this task type
        if task.task_type in self._task_functions:
            return await self._task_functions[task.task_type](task)
        
        # Default iterative execution
        result_data = {}
        max_iterations = self.config.get("max_iterations", 5)
        
        for iteration in range(1, max_iterations + 1):
            logger.info(f"Iteration {iteration}/{max_iterations} for task {task.task_id}")
            
            # Execute reasoning step if available
            if self.reasoning_engine:
                reasoning_result = await self.reasoning_engine.reason(task)
                if reasoning_result.success:
                    result_data["reasoning"] = reasoning_result.data
                    
                    # Check if reasoning suggests we should stop iterating
                    if reasoning_result.data.get("should_stop_iterating", False):
                        logger.info(f"Reasoning suggests stopping iteration at {iteration}")
                        break
            
            # Execute tools if specified
            if task.tools and self.tool_broker:
                tool_results = await self.tool_broker.execute_tools(task.tools, task.input_data or {})
                if tool_results:
                    result_data["tool_results"] = tool_results
                    
                    # Check if tool results suggest we should stop iterating
                    if tool_results.get("should_stop_iterating", False):
                        logger.info(f"Tool results suggest stopping iteration at {iteration}")
                        break
            
            # Check if we should continue iterating
            if iteration < max_iterations and self._should_continue_iterating(task, result_data, iteration):
                # Update task with intermediate results
                task.input_data = task.input_data or {}
                task.input_data["iteration"] = iteration
                task.input_data["intermediate_results"] = result_data
            else:
                break
        
        # Generate response
        response = self._generate_response(task, result_data)
        
        # Store in memory if available
        if self.agent_memory:
            await self.agent_memory.store_task_result(task, response)
        
        return response
    
    async def _execute_recursive(self, task: AgentTask) -> AgentResponse:
        """Execute a task in recursive mode."""
        logger.info(f"Executing task {task.task_id} in recursive mode")
        
        # Check if there's a registered function for this task type
        if task.task_type in self._task_functions:
            return await self._task_functions[task.task_type](task)
        
        # Default recursive execution
        return await self._execute_recursive_helper(task, 0)
    
    async def _execute_recursive_helper(
        self, 
        task: AgentTask, 
        depth: int
    ) -> AgentResponse:
        """Helper function for recursive execution."""
        max_depth = self.config.get("max_recursion_depth", 3)
        
        if depth > max_depth:
            logger.warning(f"Maximum recursion depth {max_depth} reached for task {task.task_id}")
            return AgentResponse(
                response_id=f"resp_{task.task_id}",
                task_id=task.task_id,
                agent_id=task.agent_id,
                success=False,
                data={},
                error=f"Maximum recursion depth {max_depth} reached",
                execution_time=0.0
            )
        
        logger.info(f"Recursion depth {depth}/{max_depth} for task {task.task_id}")
        
        # Execute reasoning step if available
        result_data = {}
        if self.reasoning_engine:
            reasoning_result = await self.reasoning_engine.reason(task)
            if reasoning_result.success:
                result_data["reasoning"] = reasoning_result.data
                
                # Check if reasoning suggests we should stop recursing
                if reasoning_result.data.get("should_stop_recursing", False):
                    logger.info(f"Reasoning suggests stopping recursion at depth {depth}")
                    return self._generate_response(task, result_data)
        
        # Execute tools if specified
        if task.tools and self.tool_broker:
            tool_results = await self.tool_broker.execute_tools(task.tools, task.input_data or {})
            if tool_results:
                result_data["tool_results"] = tool_results
                
                # Check if tool results suggest we should stop recursing
                if tool_results.get("should_stop_recursing", False):
                    logger.info(f"Tool results suggest stopping recursion at depth {depth}")
                    return self._generate_response(task, result_data)
        
        # Check if we should continue recursing
        if self._should_continue_recursing(task, result_data, depth):
            # Create subtasks for recursive execution
            subtasks = self._create_subtasks(task, result_data, depth)
            
            if subtasks:
                # Execute subtasks recursively
                subtask_results = []
                for subtask in subtasks:
                    subtask_result = await self._execute_recursive_helper(subtask, depth + 1)
                    subtask_results.append(subtask_result)
                
                # Aggregate subtask results
                result_data["subtask_results"] = subtask_results
        
        # Generate response
        response = self._generate_response(task, result_data)
        
        # Store in memory if available
        if self.agent_memory:
            await self.agent_memory.store_task_result(task, response)
        
        return response
    
    def _should_continue_iterating(
        self, 
        task: AgentTask, 
        result_data: Dict[str, Any], 
        iteration: int
    ) -> bool:
        """Determine if we should continue iterating."""
        # Check if iteration limit is reached
        max_iterations = self.config.get("max_iterations", 5)
        if iteration >= max_iterations:
            return False
        
        # Check if results suggest we should stop
        if result_data.get("should_stop_iterating", False):
            return False
        
        # Check if reasoning suggests we should stop
        reasoning = result_data.get("reasoning", {})
        if reasoning.get("should_stop_iterating", False):
            return False
        
        # Check if tool results suggest we should stop
        tool_results = result_data.get("tool_results", {})
        if tool_results.get("should_stop_iterating", False):
            return False
        
        # Default to continue
        return True
    
    def _should_continue_recursing(
        self, 
        task: AgentTask, 
        result_data: Dict[str, Any], 
        depth: int
    ) -> bool:
        """Determine if we should continue recursing."""
        # Check if depth limit is reached
        max_depth = self.config.get("max_recursion_depth", 3)
        if depth >= max_depth:
            return False
        
        # Check if results suggest we should stop
        if result_data.get("should_stop_recursing", False):
            return False
        
        # Check if reasoning suggests we should stop
        reasoning = result_data.get("reasoning", {})
        if reasoning.get("should_stop_recursing", False):
            return False
        
        # Check if tool results suggest we should stop
        tool_results = result_data.get("tool_results", {})
        if tool_results.get("should_stop_recursing", False):
            return False
        
        # Default to continue
        return True
    
    def _create_subtasks(
        self, 
        task: AgentTask, 
        result_data: Dict[str, Any], 
        depth: int
    ) -> List[AgentTask]:
        """Create subtasks for recursive execution."""
        # This is a placeholder for subtask creation
        # In a real implementation, this would analyze the task and results
        # to create appropriate subtasks
        
        # For now, we'll just return an empty list
        return []
    
    def _generate_response(
        self, 
        task: AgentTask, 
        result_data: Dict[str, Any]
    ) -> AgentResponse:
        """Generate an AgentResponse from task results."""
        # Create a simple response based on the task and results
        if result_data:
            message = "Task completed successfully"
        else:
            message = "Task completed (no results)"
        
        return AgentResponse(
            response_id=f"resp_{task.task_id}",
            task_id=task.task_id,
            agent_id=task.agent_id,
            success=True,
            data=result_data,
            message=message,
            execution_time=0.0  # Will be set by the caller
        )
    
    async def integrate_with_memory(self, agent_id: str) -> bool:
        """
        Integrate the native adapter with the agent memory system.
        
        Args:
            agent_id: ID of the agent to integrate
            
        Returns:
            True if integration was successful, False otherwise
        """
        if not self.agent_memory:
            logger.error("Agent memory service not available")
            return False
        
        try:
            # This is a placeholder for memory integration
            # In a real implementation, this would set up memory access
            logger.info(f"Integrated native adapter with memory system for agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to integrate native adapter with memory system: {e}")
            return False
    
    async def integrate_with_tools(self, agent_id: str) -> bool:
        """
        Integrate the native adapter with the agent tool system.
        
        Args:
            agent_id: ID of the agent to integrate
            
        Returns:
            True if integration was successful, False otherwise
        """
        if not self.tool_broker:
            logger.error("Agent tool broker not available")
            return False
        
        try:
            # This is a placeholder for tool integration
            # In a real implementation, this would set up tool access
            logger.info(f"Integrated native adapter with tool system for agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to integrate native adapter with tool system: {e}")
            return False
    
    async def integrate_with_reasoning(self, agent_id: str) -> bool:
        """
        Integrate the native adapter with the agent reasoning system.
        
        Args:
            agent_id: ID of the agent to integrate
            
        Returns:
            True if integration was successful, False otherwise
        """
        if not self.reasoning_engine:
            logger.error("Agent reasoning engine not available")
            return False
        
        try:
            # This is a placeholder for reasoning integration
            # In a real implementation, this would set up reasoning access
            logger.info(f"Integrated native adapter with reasoning system for agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to integrate native adapter with reasoning system: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Native adapter.
        
        Returns:
            Health status information
        """
        return {
            "service": "native_adapter",
            "timestamp": datetime.utcnow().isoformat(),
            "task_functions_count": len(self._task_functions),
            "task_registry_count": len(self._task_registry),
            "execution_cache_size": len(self._execution_cache),
            "enable_error_handling": self._enable_error_handling,
            "max_execution_time": self._max_execution_time,
            "default_execution_mode": self._default_execution_mode.value,
            "enable_caching": self._enable_caching,
            "cache_size": self._cache_size,
            "enable_parallelism": self._enable_parallelism,
            "max_parallel_tasks": self._max_parallel_tasks,
            "agent_validation_available": self.agent_validation is not None,
            "agent_memory_available": self.agent_memory is not None,
            "tool_broker_available": self.tool_broker is not None,
            "reasoning_engine_available": self.reasoning_engine is not None
        }