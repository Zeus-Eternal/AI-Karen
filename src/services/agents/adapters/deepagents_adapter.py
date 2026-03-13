"""
DeepAgents Adapter for Agent Architecture System.

This module provides integration between DeepAgents and the agent architecture system,
enabling agents to leverage DeepAgents' capabilities while maintaining compatibility
with the existing agent framework.
"""

import os
import logging
import json
import asyncio
from typing import Any, Dict, List, Optional, Union, Type
from datetime import datetime
from enum import Enum

# DeepAgents imports
try:
    from deepagents import Agent as DeepAgent
    from deepagents import Environment as DeepEnvironment
    from deepagents import Task as DeepTask
    from deepagents import Memory as DeepMemory
    from deepagents import Tool as DeepTool
    from deepagents import ReasoningEngine as DeepReasoningEngine
    from deepagents import AgentConfig as DeepAgentConfig
    from deepagents import TaskConfig as DeepTaskConfig
    from deepagents import ToolConfig as DeepToolConfig
    from deepagents import MemoryConfig as DeepMemoryConfig
    from deepagents import ReasoningConfig as DeepReasoningConfig
    
    HAS_DEEPAGENTS = True
except ImportError:
    HAS_DEEPAGENTS = False
    # Create placeholder classes for type hints if DeepAgents is not available
    class DeepAgent:
        def __init__(self, *args, **kwargs):
            pass
        
        async def execute(self, *args, **kwargs):
            return {}
    
    class DeepEnvironment:
        def __init__(self, *args, **kwargs):
            pass
        
        async def step(self, *args, **kwargs):
            return {}
    
    class DeepTask:
        def __init__(self, *args, **kwargs):
            pass
    
    class DeepMemory:
        def __init__(self, *args, **kwargs):
            pass
        
        async def store(self, *args, **kwargs):
            return {}
        
        async def retrieve(self, *args, **kwargs):
            return {}
    
    class DeepTool:
        def __init__(self, *args, **kwargs):
            pass
        
        async def execute(self, *args, **kwargs):
            return {}
    
    class DeepReasoningEngine:
        def __init__(self, *args, **kwargs):
            pass
        
        async def reason(self, *args, **kwargs):
            return {}
    
    class DeepAgentConfig:
        def __init__(self, *args, **kwargs):
            pass
    
    class DeepTaskConfig:
        def __init__(self, *args, **kwargs):
            pass
    
    class DeepToolConfig:
        def __init__(self, *args, **kwargs):
            pass
    
    class DeepMemoryConfig:
        def __init__(self, *args, **kwargs):
            pass
    
    class DeepReasoningConfig:
        def __init__(self, *args, **kwargs):
            pass

# Local application imports
from ..internal.agent_schemas import (
    AgentDefinition, AgentTask, AgentResponse, AgentTool, AgentMemory,
    AgentStatus, TaskStatus, MessageStatus
)
from ..internal.agent_validation import AgentValidation
from ..agent_memory import EnhancedAgentMemory
from ..agent_tool_broker import AgentToolBroker
from ..agent_reasoning import AgentReasoning

logger = logging.getLogger(__name__)


class DeepAgentsExecutionMode(str, Enum):
    """DeepAgents execution mode enumeration."""
    REACTIVE = "reactive"
    PLANNING = "planning"
    HIERARCHICAL = "hierarchical"
    MULTI_AGENT = "multi_agent"


class DeepAgentsAgentType(str, Enum):
    """DeepAgents agent type enumeration."""
    CONVERSATIONAL = "conversational"
    TASK_ORIENTED = "task-oriented"
    REASONING = "reasoning"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    ASSISTANT = "assistant"


class DeepAgentsAdapter:
    """
    Adapter for integrating DeepAgents with the agent architecture system.
    
    This adapter provides functionality to:
    1. Create and manage DeepAgents
    2. Convert between DeepAgents and agent architecture data structures
    3. Execute DeepAgents with proper error handling
    4. Integrate with the agent memory system
    5. Integrate with the agent tool system
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        agent_validation: Optional[AgentValidation] = None,
        agent_memory: Optional[EnhancedAgentMemory] = None,
        tool_broker: Optional[AgentToolBroker] = None,
        reasoning_engine: Optional[AgentReasoning] = None
    ):
        """
        Initialize the DeepAgents adapter.
        
        Args:
            config: Configuration dictionary for the adapter
            agent_validation: Agent validation service instance
            agent_memory: Agent memory service instance
            tool_broker: Agent tool broker instance
            reasoning_engine: Agent reasoning engine instance
        """
        if not HAS_DEEPAGENTS:
            logger.error("DeepAgents is not installed. Please install it to use this adapter.")
            raise ImportError("DeepAgents is required but not installed")
        
        self.config = config or {}
        self.agent_validation = agent_validation
        self.agent_memory = agent_memory
        self.tool_broker = tool_broker
        self.reasoning_engine = reasoning_engine
        
        # DeepAgents components
        self._agents: Dict[str, DeepAgent] = {}
        self._environments: Dict[str, DeepEnvironment] = {}
        self._tasks: Dict[str, DeepTask] = {}
        self._memories: Dict[str, DeepMemory] = {}
        self._tools: Dict[str, DeepTool] = {}
        self._reasoning_engines: Dict[str, DeepReasoningEngine] = {}
        
        # Adapter configuration
        self._enable_error_handling = True
        self._max_execution_time = 300  # seconds
        self._verbose = self.config.get("verbose", False)
        self._default_execution_mode = self.config.get("default_execution_mode", DeepAgentsExecutionMode.REACTIVE)
        self._enable_environment = self.config.get("enable_environment", True)
        self._enable_multi_agent = self.config.get("enable_multi_agent", True)
        self._max_agents = self.config.get("max_agents", 10)
        
        logger.info("DeepAgents adapter initialized successfully")
    
    async def create_agent(
        self,
        agent_id: str,
        agent_definition: AgentDefinition,
        execution_mode: Optional[DeepAgentsExecutionMode] = None,
        agent_type: Optional[DeepAgentsAgentType] = None,
        agent_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a DeepAgent from an agent definition.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_definition: Agent definition to convert to DeepAgent
            execution_mode: Execution mode for the agent
            agent_config: Configuration for the DeepAgent
            
        Returns:
            True if agent creation was successful, False otherwise
        """
        if not HAS_DEEPAGENTS:
            logger.error("DeepAgents is not available")
            return False
        
        # Validate agent definition
        if self.agent_validation:
            is_valid, errors = await self.agent_validation.validate_agent_definition(agent_definition)
            if not is_valid:
                logger.error(f"Agent definition validation failed: {errors}")
                return False
        
        # Check if we've reached the maximum number of agents
        if len(self._agents) >= self._max_agents:
            logger.error(f"Maximum number of agents ({self._max_agents}) reached")
            return False
        
        # Set execution mode
        execution_mode = execution_mode or self._default_execution_mode
        
        # Create DeepAgent configuration
        deep_agent_config = self._create_deep_agent_config(agent_definition, execution_mode, agent_type, agent_config)
        
        # Create memory if available
        deep_memory = None
        if self.agent_memory:
            deep_memory = self._create_deep_memory(agent_id)
            self._memories[agent_id] = deep_memory
        
        # Create reasoning engine if available
        deep_reasoning = None
        if self.reasoning_engine:
            deep_reasoning = self._create_deep_reasoning_engine(agent_id)
            self._reasoning_engines[agent_id] = deep_reasoning
        
        try:
            # Create the DeepAgent
            deep_agent = DeepAgent(
                config=deep_agent_config,
                memory=deep_memory,
                reasoning_engine=deep_reasoning
            )
            
            # Store the agent
            self._agents[agent_id] = deep_agent
            
            # Create environment if enabled
            if self._enable_environment:
                deep_environment = self._create_deep_environment(agent_id)
                self._environments[agent_id] = deep_environment
            
            logger.info(f"Created DeepAgent {agent_id} with execution mode {execution_mode}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create DeepAgent: {e}")
            return False
    
    def _create_deep_agent_config(
        self,
        agent_definition: AgentDefinition,
        execution_mode: DeepAgentsExecutionMode,
        agent_type: Optional[DeepAgentsAgentType] = None,
        agent_config: Optional[Dict[str, Any]] = None
    ) -> DeepAgentConfig:
        """Create a DeepAgent configuration from an agent definition."""
        # Convert agent definition to DeepAgentConfig
        config_dict = {
            "name": agent_definition.name,
            "description": agent_definition.description,
            "execution_mode": execution_mode.value,
            "capabilities": agent_definition.capabilities,
            "model": agent_definition.model,
            "parameters": agent_definition.parameters
        }
        
        # Add agent type if provided
        if agent_type:
            config_dict["agent_type"] = agent_type.value
        
        # Add any additional configuration
        if agent_config:
            config_dict.update(agent_config)
        
        return DeepAgentConfig(**config_dict)
    
    def _create_deep_memory(self, agent_id: str) -> DeepMemory:
        """Create a DeepMemory instance for an agent."""
        # Create memory configuration
        memory_config = DeepMemoryConfig(
            agent_id=agent_id,
            max_size=self.config.get("memory_max_size", 1000),
            retention_policy=self.config.get("memory_retention_policy", "lru")
        )
        
        # Create memory
        return DeepMemory(config=memory_config)
    
    def _create_deep_reasoning_engine(self, agent_id: str) -> DeepReasoningEngine:
        """Create a DeepReasoningEngine instance for an agent."""
        # Create reasoning configuration
        reasoning_config = DeepReasoningConfig(
            agent_id=agent_id,
            reasoning_type=self.config.get("reasoning_type", "logical"),
            max_depth=self.config.get("reasoning_max_depth", 5),
            timeout=self.config.get("reasoning_timeout", 30)
        )
        
        # Create reasoning engine
        return DeepReasoningEngine(config=reasoning_config)
    
    def _create_deep_environment(self, agent_id: str) -> DeepEnvironment:
        """Create a DeepEnvironment instance for an agent."""
        # Create environment configuration
        env_config = {
            "agent_id": agent_id,
            "max_steps": self.config.get("environment_max_steps", 100),
            "reward_function": self.config.get("environment_reward_function", "default"),
            "observation_space": self.config.get("environment_observation_space", "default"),
            "action_space": self.config.get("environment_action_space", "default")
        }
        
        # Create environment
        return DeepEnvironment(config=env_config)
    
    async def register_tool(self, tool_id: str, tool: AgentTool) -> bool:
        """
        Register a tool with the adapter.
        
        Args:
            tool_id: Unique identifier for the tool
            tool: The AgentTool instance to register
            
        Returns:
            True if registration was successful, False otherwise
        """
        if not HAS_DEEPAGENTS:
            logger.error("DeepAgents is not available")
            return False
        
        try:
            # Convert AgentTool to DeepTool
            deep_tool_config = DeepToolConfig(
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters,
                function=tool.function
            )
            
            deep_tool = DeepTool(config=deep_tool_config)
            
            # Store the tool
            self._tools[tool_id] = deep_tool
            
            logger.info(f"Registered tool {tool_id} with DeepAgents adapter")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register tool {tool_id}: {e}")
            return False
    
    def unregister_tool(self, tool_id: str) -> bool:
        """
        Unregister a tool from the adapter.
        
        Args:
            tool_id: Unique identifier of the tool to unregister
            
        Returns:
            True if unregistration was successful, False otherwise
        """
        if tool_id not in self._tools:
            logger.warning(f"Tool {tool_id} not found in adapter")
            return False
        
        del self._tools[tool_id]
        logger.info(f"Unregistered tool {tool_id} from DeepAgents adapter")
        return True
    
    async def execute_task(
        self, 
        agent_id: str, 
        task: AgentTask
    ) -> AgentResponse:
        """
        Execute a task using a DeepAgent.
        
        Args:
            agent_id: ID of the agent to execute the task
            task: Task to execute
            
        Returns:
            Agent response with execution results
        """
        if agent_id not in self._agents:
            return AgentResponse(
                response_id=f"resp_{task.task_id}",
                task_id=task.task_id,
                agent_id=task.agent_id,
                success=False,
                data={},
                error=f"Agent {agent_id} not found",
                execution_time=0.0
            )
        
        agent = self._agents[agent_id]
        
        # Convert task to DeepTask
        deep_task = await self._convert_task_to_deep_task(task)
        
        try:
            # Execute the task
            start_time = datetime.utcnow()
            
            # Try to use execute method first, fallback to other methods if not available
            if hasattr(agent, 'execute'):
                if self._enable_environment and agent_id in self._environments:
                    # Execute with environment
                    environment = self._environments[agent_id]
                    result = await agent.execute(deep_task, environment)
                else:
                    # Execute without environment
                    result = await agent.execute(deep_task)
            elif hasattr(agent, 'run'):
                result = await agent.run(deep_task)
            else:
                raise AttributeError("DeepAgent has no execute or run method")
                
            end_time = datetime.utcnow()
            
            # Calculate execution time
            execution_time = (end_time - start_time).total_seconds()
            
            # Convert result to AgentResponse
            response = await self._convert_deep_task_result_to_agent_response(
                result, task, agent_id, execution_time
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error executing task {task.task_id} with agent {agent_id}: {e}")
            return AgentResponse(
                response_id=f"resp_{task.task_id}",
                task_id=task.task_id,
                agent_id=task.agent_id,
                success=False,
                data={},
                error=str(e),
                execution_time=0.0
            )

    async def execute_agent(
        self,
        agent_id: str,
        task: AgentTask
    ) -> AgentResponse:
        """
        Alias for executing a task under the agent API.
        """
        return await self.execute_task(agent_id, task)
    
    async def _convert_task_to_deep_task(self, task: AgentTask) -> DeepTask:
        """Convert an AgentTask to DeepTask format."""
        # Create task configuration
        task_config = DeepTaskConfig(
            task_id=task.task_id,
            task_type=task.task_type,
            description=task.description,
            input_data=task.input_data or {},
            tools=task.tools or [],
            priority=task.priority,
            deadline=task.deadline
        )
        
        # Create DeepTask
        return DeepTask(config=task_config)
    
    async def _convert_deep_task_result_to_agent_response(
        self, 
        result: Any, 
        task: AgentTask, 
        agent_id: str,
        execution_time: float
    ) -> AgentResponse:
        """Convert DeepTask result to AgentResponse format."""
        # Parse the result
        if isinstance(result, str):
            data = {"output": result}
        elif isinstance(result, dict):
            data = result
        else:
            data = {"output": str(result)}
        
        return AgentResponse(
            response_id=f"resp_{task.task_id}",
            task_id=task.task_id,
            agent_id=task.agent_id,
            success=True,
            data=data,
            message="Task completed successfully",
            execution_time=execution_time
        )
    
    async def integrate_with_memory(self, agent_id: str) -> bool:
        """
        Integrate a DeepAgent with the agent memory system.
        
        Args:
            agent_id: ID of the agent to integrate
            
        Returns:
            True if integration was successful, False otherwise
        """
        if agent_id not in self._agents:
            logger.error(f"Agent {agent_id} not found")
            return False
        
        if not self.agent_memory:
            logger.error("Agent memory service not available")
            return False
        
        try:
            # Get the agent and memory
            agent = self._agents[agent_id]
            deep_memory = self._memories.get(agent_id)
            
            if not deep_memory:
                logger.warning(f"No DeepMemory found for agent {agent_id}")
                return False
            
            # This is a placeholder for memory integration
            # In a real implementation, this would set up bidirectional memory access
            logger.info(f"Integrated DeepAgent {agent_id} with memory system")
            return True
            
        except Exception as e:
            logger.error(f"Failed to integrate DeepAgent {agent_id} with memory system: {e}")
            return False
    
    async def integrate_with_tools(self, agent_id: str) -> bool:
        """
        Integrate a DeepAgent with the agent tool system.
        
        Args:
            agent_id: ID of the agent to integrate
            
        Returns:
            True if integration was successful, False otherwise
        """
        if agent_id not in self._agents:
            logger.error(f"Agent {agent_id} not found")
            return False
        
        if not self.tool_broker:
            logger.error("Agent tool broker not available")
            return False
        
        try:
            # Get the agent
            agent = self._agents[agent_id]
            
            # This is a placeholder for tool integration
            # In a real implementation, this would register tools with the agent
            logger.info(f"Integrated DeepAgent {agent_id} with tool system")
            return True
            
        except Exception as e:
            logger.error(f"Failed to integrate DeepAgent {agent_id} with tool system: {e}")
            return False
    
    async def integrate_with_reasoning(self, agent_id: str) -> bool:
        """
        Integrate a DeepAgent with the agent reasoning system.
        
        Args:
            agent_id: ID of the agent to integrate
            
        Returns:
            True if integration was successful, False otherwise
        """
        if agent_id not in self._agents:
            logger.error(f"Agent {agent_id} not found")
            return False
        
        if not self.reasoning_engine:
            logger.error("Agent reasoning engine not available")
            return False
        
        try:
            # Get the agent and reasoning engine
            agent = self._agents[agent_id]
            deep_reasoning = self._reasoning_engines.get(agent_id)
            
            if not deep_reasoning:
                logger.warning(f"No DeepReasoningEngine found for agent {agent_id}")
                return False
            
            # This is a placeholder for reasoning integration
            # In a real implementation, this would set up bidirectional reasoning access
            logger.info(f"Integrated DeepAgent {agent_id} with reasoning system")
            return True
            
        except Exception as e:
            logger.error(f"Failed to integrate DeepAgent {agent_id} with reasoning system: {e}")
            return False
    
    def get_agent(self, agent_id: str) -> Optional[DeepAgent]:
        """
        Get a DeepAgent by ID.
        
        Args:
            agent_id: ID of the agent to retrieve
            
        Returns:
            DeepAgent instance if found, None otherwise
        """
        return self._agents.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """
        List all agent IDs in the adapter.
        
        Returns:
            List of agent IDs
        """
        return list(self._agents.keys())
    
    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove a DeepAgent from the adapter.
        
        Args:
            agent_id: ID of the agent to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        if agent_id not in self._agents:
            logger.warning(f"Agent {agent_id} not found")
            return False
        
        del self._agents[agent_id]
        if agent_id in self._environments:
            del self._environments[agent_id]
        if agent_id in self._memories:
            del self._memories[agent_id]
        if agent_id in self._reasoning_engines:
            del self._reasoning_engines[agent_id]
        
        logger.info(f"Removed agent {agent_id} from DeepAgents adapter")
        return True
    
    async def create_multi_agent_system(
        self, 
        system_id: str, 
        agent_ids: List[str],
        system_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a multi-agent system using DeepAgents.
        
        Args:
            system_id: Unique identifier for the multi-agent system
            agent_ids: List of agent IDs to include in the system
            system_config: Configuration for the multi-agent system
            
        Returns:
            True if system creation was successful, False otherwise
        """
        if not self._enable_multi_agent:
            logger.error("Multi-agent functionality is disabled")
            return False
        
        # Check if all agents exist
        missing_agents = [aid for aid in agent_ids if aid not in self._agents]
        if missing_agents:
            logger.error(f"Agents not found: {missing_agents}")
            return False
        
        try:
            # This is a placeholder for multi-agent system creation
            # In a real implementation, this would create a multi-agent system
            logger.info(f"Created multi-agent system {system_id} with agents {agent_ids}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create multi-agent system {system_id}: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the DeepAgents adapter.
        
        Returns:
            Health status information
        """
        return {
            "service": "deepagents_adapter",
            "timestamp": datetime.utcnow().isoformat(),
            "deepagents_available": HAS_DEEPAGENTS,
            "agents_count": len(self._agents),
            "environments_count": len(self._environments),
            "tasks_count": len(self._tasks),
            "memories_count": len(self._memories),
            "tools_count": len(self._tools),
            "reasoning_engines_count": len(self._reasoning_engines),
            "enable_error_handling": self._enable_error_handling,
            "max_execution_time": self._max_execution_time,
            "default_execution_mode": self._default_execution_mode.value,
            "enable_environment": self._enable_environment,
            "enable_multi_agent": self._enable_multi_agent,
            "max_agents": self._max_agents,
            "agent_validation_available": self.agent_validation is not None,
            "agent_memory_available": self.agent_memory is not None,
            "tool_broker_available": self.tool_broker is not None,
            "reasoning_engine_available": self.reasoning_engine is not None
        }
