"""
Agent Integration Service for CoPilot Architecture.

This service provides integration between different agent execution modes:
1. Native mode - Direct execution using the agent orchestrator
2. DeepAgents mode - Execution using DeepAgents framework
3. LangGraph mode - Execution using LangGraph framework

The service handles:
- Mode selection and switching
- Task routing to appropriate execution modes
- Result aggregation and normalization
- Configuration management for different modes
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

from .internal.agent_schemas import AgentTask, AgentResponse, AgentDefinition
from .agent_orchestrator import AgentOrchestrator
from .adapters.deepagents_adapter import DeepAgentsAdapter
from .adapters.langgraph_adapter import LangGraphAdapter

logger = logging.getLogger(__name__)


class AgentExecutionMode(str, Enum):
    """Agent execution mode enumeration."""
    NATIVE = "native"
    DEEPAGENTS = "deepagents"
    LANGGRAPH = "langgraph"


class AgentIntegrationService:
    """
    Service for integrating different agent execution modes.
    
    This service provides a unified interface for executing agents using
    different execution modes while maintaining compatibility with the
    existing agent framework.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        agent_orchestrator: Optional[AgentOrchestrator] = None,
        deepagents_adapter: Optional[DeepAgentsAdapter] = None,
        langgraph_adapter: Optional[LangGraphAdapter] = None
    ):
        """
        Initialize the Agent Integration Service.
        
        Args:
            config: Configuration dictionary for the service
            agent_orchestrator: Agent orchestrator instance for native mode
            deepagents_adapter: DeepAgents adapter instance
            langchain_adapter: LangChain adapter instance
        """
        self.config = config or {}
        self.agent_orchestrator = agent_orchestrator
        self.deepagents_adapter = deepagents_adapter
        self.langgraph_adapter = langgraph_adapter
        
        # Default execution mode
        self._default_mode = AgentExecutionMode.NATIVE
        self._auto_mode_selection = self.config.get("auto_mode_selection", True)
        
        # Mode-specific configurations
        self._mode_configs = {
            AgentExecutionMode.NATIVE: self.config.get("native_config", {}),
            AgentExecutionMode.DEEPAGENTS: self.config.get("deepagents_config", {}),
            AgentExecutionMode.LANGGRAPH: self.config.get("langgraph_config", {})
        }
        
        # Mode selection criteria
        self._mode_selection_criteria = self.config.get("mode_selection_criteria", {
            "task_complexity_threshold": 0.7,
            "task_length_threshold": 1000,
            "reasoning_required_threshold": 0.8,
            "creativity_required_threshold": 0.6
        })
        
        # Performance metrics
        self._mode_performance_metrics = {
            AgentExecutionMode.NATIVE: {
                "execution_count": 0,
                "average_execution_time": 0.0,
                "success_rate": 0.0,
                "total_execution_time": 0.0
            },
            AgentExecutionMode.DEEPAGENTS: {
                "execution_count": 0,
                "average_execution_time": 0.0,
                "success_rate": 0.0,
                "total_execution_time": 0.0
            },
            AgentExecutionMode.LANGGRAPH: {
                "execution_count": 0,
                "average_execution_time": 0.0,
                "success_rate": 0.0,
                "total_execution_time": 0.0
            }
        }
        
        logger.info("Agent Integration Service initialized successfully")
    
    async def initialize(self) -> None:
        """Initialize the Agent Integration Service and its components."""
        logger.info("Initializing Agent Integration Service")
        
        # Initialize agent orchestrator if not provided
        if not self.agent_orchestrator:
            self.agent_orchestrator = AgentOrchestrator(
                config=self.config.get("orchestrator_config", {})
            )
            await self.agent_orchestrator.initialize()
        
        # Initialize DeepAgents adapter if not provided
        if not self.deepagents_adapter and self._mode_configs[AgentExecutionMode.DEEPAGENTS]:
            self.deepagents_adapter = DeepAgentsAdapter(
                config=self._mode_configs[AgentExecutionMode.DEEPAGENTS]
            )
        
        # Initialize LangGraph adapter if not provided
        if not self.langgraph_adapter and self._mode_configs[AgentExecutionMode.LANGGRAPH]:
            self.langgraph_adapter = LangGraphAdapter(
                config=self._mode_configs[AgentExecutionMode.LANGGRAPH]
            )
        
        logger.info("Agent Integration Service initialized successfully")
    
    async def execute_task(
        self,
        task: AgentTask,
        execution_mode: Optional[AgentExecutionMode] = None,
        agent_definition: Optional[AgentDefinition] = None
    ) -> AgentResponse:
        """
        Execute a task using the appropriate execution mode.
        
        Args:
            task: Task to execute
            execution_mode: Specific execution mode to use (if None, uses auto-selection)
            agent_definition: Agent definition for the task
            
        Returns:
            Agent response with execution results
        """
        # Select execution mode if not specified
        if not execution_mode:
            execution_mode = await self._select_execution_mode(task, agent_definition)
        
        logger.info(f"Executing task {task.task_id} using {execution_mode.value} mode")
        
        # Execute task using the selected mode
        try:
            start_time = datetime.utcnow()
            
            if execution_mode == AgentExecutionMode.NATIVE:
                response = await self._execute_native_mode(task, agent_definition)
            elif execution_mode == AgentExecutionMode.DEEPAGENTS:
                response = await self._execute_deepagents_mode(task, agent_definition)
            elif execution_mode == AgentExecutionMode.LANGGRAPH:
                response = await self._execute_langgraph_mode(task, agent_definition)
            else:
                raise ValueError(f"Unsupported execution mode: {execution_mode}")
            
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            # Update performance metrics
            await self._update_performance_metrics(execution_mode, response, execution_time)
            
            # Add execution metadata to response
            response.data["execution_metadata"] = {
                "execution_mode": execution_mode.value,
                "execution_time": execution_time,
                "timestamp": end_time.isoformat()
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error executing task {task.task_id} in {execution_mode.value} mode: {e}")
            return AgentResponse(
                response_id=f"resp_{task.task_id}",
                task_id=task.task_id,
                agent_id=task.agent_id,
                success=False,
                data={},
                error=str(e),
                execution_time=0.0
            )
    
    async def _select_execution_mode(
        self,
        task: AgentTask,
        agent_definition: Optional[AgentDefinition] = None
    ) -> AgentExecutionMode:
        """
        Select the appropriate execution mode for a task.
        
        Args:
            task: Task to analyze for mode selection
            agent_definition: Agent definition for the task
            
        Returns:
            Selected execution mode
        """
        if not self._auto_mode_selection:
            return self._default_mode
        
        # Analyze task characteristics
        task_characteristics = await self._analyze_task_characteristics(task, agent_definition)
        
        # Apply selection criteria
        criteria = self._mode_selection_criteria
        
        # Check if task requires DeepAgents mode
        if (task_characteristics.get("complexity", 0) > criteria["task_complexity_threshold"] or
            task_characteristics.get("reasoning_required", 0) > criteria["reasoning_required_threshold"] or
            task_characteristics.get("creativity_required", 0) > criteria["creativity_required_threshold"]):
            
            # Check if DeepAgents adapter is available
            if self.deepagents_adapter:
                logger.debug(f"Selected DeepAgents mode for task {task.task_id}")
                return AgentExecutionMode.DEEPAGENTS
        
        # Check if task requires LangGraph mode
        if (task_characteristics.get("requires_graph_execution", False) or
            task_characteristics.get("length", 0) > criteria["task_length_threshold"]):
            
            # Check if LangGraph adapter is available
            if self.langgraph_adapter:
                logger.debug(f"Selected LangGraph mode for task {task.task_id}")
                return AgentExecutionMode.LANGGRAPH
        
        # Default to native mode
        logger.debug(f"Selected native mode for task {task.task_id}")
        return AgentExecutionMode.NATIVE
    
    async def _analyze_task_characteristics(
        self,
        task: AgentTask,
        agent_definition: Optional[AgentDefinition] = None
    ) -> Dict[str, Any]:
        """
        Analyze task characteristics to determine the best execution mode.
        
        Args:
            task: Task to analyze
            agent_definition: Agent definition for the task
            
        Returns:
            Dictionary of task characteristics
        """
        characteristics = {
            "complexity": 0.5,  # Default medium complexity
            "length": len(task.description or ""),
            "reasoning_required": 0.5,  # Default medium reasoning requirement
            "creativity_required": 0.5,  # Default medium creativity requirement
            "requires_graph_execution": False
        }
        
        # Analyze task type
        if task.task_type in ["reasoning", "learning", "problem_solving"]:
            characteristics["reasoning_required"] = 0.8
            characteristics["complexity"] = 0.7
        
        if task.task_type in ["creative", "design", "generation"]:
            characteristics["creativity_required"] = 0.8
            characteristics["complexity"] = 0.6
        
        if task.task_type in ["planning", "coordination", "workflow"]:
            characteristics["requires_graph_execution"] = True
            characteristics["complexity"] = 0.9
        
        # Analyze task description for complexity indicators
        description = task.description or ""
        complexity_keywords = ["complex", "difficult", "challenging", "intricate", "sophisticated"]
        reasoning_keywords = ["analyze", "reason", "infer", "deduce", "logic", "think"]
        creative_keywords = ["create", "design", "imagine", "invent", "brainstorm", "innovate"]
        
        for keyword in complexity_keywords:
            if keyword in description.lower():
                characteristics["complexity"] = min(1.0, characteristics["complexity"] + 0.1)
        
        for keyword in reasoning_keywords:
            if keyword in description.lower():
                characteristics["reasoning_required"] = min(1.0, characteristics["reasoning_required"] + 0.1)
        
        for keyword in creative_keywords:
            if keyword in description.lower():
                characteristics["creativity_required"] = min(1.0, characteristics["creativity_required"] + 0.1)
        
        # Consider agent capabilities if available
        if agent_definition:
            # Check if agent has specific capabilities that might influence mode selection
            for capability in agent_definition.capabilities:
                if capability.name in ["reasoning", "complex_reasoning"]:
                    characteristics["reasoning_required"] = min(1.0, characteristics["reasoning_required"] + 0.1)
                elif capability.name in ["creative", "design"]:
                    characteristics["creativity_required"] = min(1.0, characteristics["creativity_required"] + 0.1)
                elif capability.name in ["graph_execution", "workflow"]:
                    characteristics["requires_graph_execution"] = True
        
        return characteristics
    
    async def _execute_native_mode(
        self,
        task: AgentTask,
        agent_definition: Optional[AgentDefinition] = None
    ) -> AgentResponse:
        """
        Execute a task using native mode.
        
        Args:
            task: Task to execute
            agent_definition: Agent definition for the task
            
        Returns:
            Agent response with execution results
        """
        if not self.agent_orchestrator:
            raise ValueError("Agent orchestrator not available for native mode execution")
        
        # Create agent if not already registered
        if agent_definition and task.agent_id:
            agent_exists = await self.agent_orchestrator.get_agent_status(task.agent_id)
            if not agent_exists:
                await self.agent_orchestrator.register_agent(
                    agent_id=task.agent_id,
                    agent_type=agent_definition.agent_type,
                    config=agent_definition.config
                )
        
        # Route task to agent
        result = await self.agent_orchestrator.route_task(
            task_type=task.task_type,
            task_data=task.input_data or {}
        )
        
        # Convert result to AgentResponse
        return AgentResponse(
            response_id=f"resp_{task.task_id}",
            task_id=task.task_id,
            agent_id=task.agent_id,
            success=result.get("status") == "completed",
            data=result.get("result", {}),
            message=result.get("error", "Task completed successfully"),
            execution_time=result.get("execution_time", 0.0)
        )
    
    async def _execute_deepagents_mode(
        self,
        task: AgentTask,
        agent_definition: Optional[AgentDefinition] = None
    ) -> AgentResponse:
        """
        Execute a task using DeepAgents mode.
        
        Args:
            task: Task to execute
            agent_definition: Agent definition for the task
            
        Returns:
            Agent response with execution results
        """
        if not self.deepagents_adapter:
            raise ValueError("DeepAgents adapter not available for DeepAgents mode execution")
        
        # Create agent if not already created
        if agent_definition and task.agent_id:
            agent_exists = self.deepagents_adapter.get_agent(task.agent_id)
            if not agent_exists:
                await self.deepagents_adapter.create_agent(
                    agent_id=task.agent_id,
                    agent_definition=agent_definition
                )
        
        # Execute task
        response = await self.deepagents_adapter.execute_task(
            agent_id=task.agent_id,
            task=task
        )
        
        return response
    
    async def _execute_langgraph_mode(
        self,
        task: AgentTask,
        agent_definition: Optional[AgentDefinition] = None
    ) -> AgentResponse:
        """
        Execute a task using LangGraph mode.
        
        Args:
            task: Task to execute
            agent_definition: Agent definition for the task
            
        Returns:
            Agent response with execution results
        """
        if not self.langgraph_adapter:
            raise ValueError("LangGraph adapter not available for LangGraph mode execution")
        
        # Create graph if not already created
        if agent_definition and task.agent_id:
            graph_exists = self.langgraph_adapter.get_graph(task.agent_id)
            if not graph_exists:
                await self.langgraph_adapter.create_graph(
                    graph_id=task.agent_id,
                    agent_definition=agent_definition
                )
        
        # Execute task
        response = await self.langgraph_adapter.execute_graph(
            graph_id=task.agent_id,
            task=task
        )
        
        return response
    
    async def _update_performance_metrics(
        self,
        execution_mode: AgentExecutionMode,
        response: AgentResponse,
        execution_time: float
    ) -> None:
        """
        Update performance metrics for an execution mode.
        
        Args:
            execution_mode: Execution mode that was used
            response: Response from the execution
            execution_time: Time taken for execution
        """
        metrics = self._mode_performance_metrics[execution_mode]
        
        # Update execution count
        metrics["execution_count"] += 1
        
        # Update total execution time
        metrics["total_execution_time"] += execution_time
        
        # Update average execution time
        if metrics["execution_count"] > 0:
            metrics["average_execution_time"] = (
                metrics["total_execution_time"] / metrics["execution_count"]
            )
        
        # Update success rate
        if metrics["execution_count"] > 0:
            success_count = sum(
                1 for m in [metrics] 
                if m.get("last_success", False)
            )
            metrics["success_rate"] = success_count / metrics["execution_count"]
        
        # Track last execution success
        metrics["last_success"] = response.success
        
        logger.debug(f"Updated performance metrics for {execution_mode.value} mode")
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for all execution modes.
        
        Returns:
            Dictionary of performance metrics
        """
        return {
            "modes": {
                mode.value: metrics.copy()
                for mode, metrics in self._mode_performance_metrics.items()
            },
            "auto_mode_selection": self._auto_mode_selection,
            "default_mode": self._default_mode.value,
            "mode_selection_criteria": self._mode_selection_criteria
        }
    
    async def set_default_mode(self, mode: AgentExecutionMode) -> None:
        """
        Set the default execution mode.
        
        Args:
            mode: Default execution mode to set
        """
        self._default_mode = mode
        logger.info(f"Set default execution mode to {mode.value}")
    
    async def enable_auto_mode_selection(self, enabled: bool) -> None:
        """
        Enable or disable automatic mode selection.
        
        Args:
            enabled: Whether to enable automatic mode selection
        """
        self._auto_mode_selection = enabled
        logger.info(f"{'Enabled' if enabled else 'Disabled'} automatic mode selection")
    
    async def update_mode_selection_criteria(self, criteria: Dict[str, float]) -> None:
        """
        Update the criteria for automatic mode selection.
        
        Args:
            criteria: New criteria for mode selection
        """
        self._mode_selection_criteria.update(criteria)
        logger.info(f"Updated mode selection criteria: {criteria}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Agent Integration Service.
        
        Returns:
            Health status information
        """
        health_status = {
            "service": "agent_integration_service",
            "timestamp": datetime.utcnow().isoformat(),
            "default_mode": self._default_mode.value,
            "auto_mode_selection": self._auto_mode_selection,
            "modes_available": {}
        }
        
        # Check native mode availability
        health_status["modes_available"]["native"] = self.agent_orchestrator is not None
        
        # Check DeepAgents mode availability
        if self.deepagents_adapter:
            deepagents_health = await self.deepagents_adapter.health_check()
            health_status["modes_available"]["deepagents"] = deepagents_health.get("deepagents_available", False)
        else:
            health_status["modes_available"]["deepagents"] = False
        
        # Check LangGraph mode availability
        if self.langgraph_adapter:
            langgraph_health = await self.langgraph_adapter.health_check()
            health_status["modes_available"]["langgraph"] = langgraph_health.get("langgraph_available", False)
        else:
            health_status["modes_available"]["langgraph"] = False
        
        return health_status