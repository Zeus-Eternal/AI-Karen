"""
Agent Task Router Service

This service is responsible for routing tasks to appropriate agents based on task type,
agent capabilities, and current system state.
"""

from typing import Dict, List, Any, Optional, Callable, Union
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Enumeration of task types that can be routed to agents."""
    ANALYSIS = "analysis"
    GENERATION = "generation"
    REASONING = "reasoning"
    PLANNING = "planning"
    EXECUTION = "execution"
    VALIDATION = "validation"
    MONITORING = "monitoring"
    LEARNING = "learning"
    COMMUNICATION = "communication"
    COORDINATION = "coordination"


class AgentType(Enum):
    """Enumeration of agent types."""
    WORKER = "worker"
    SPECIALIZED = "specialized"
    SYSTEM = "system"
    META = "meta"


@dataclass
class AgentCapability:
    """Represents a capability of an agent."""
    name: str
    task_types: List[TaskType]
    priority: int = 0
    max_concurrent_tasks: int = 1
    timeout: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentInfo:
    """Information about an agent."""
    id: str
    type: AgentType
    capabilities: List[AgentCapability]
    current_load: int = 0
    max_load: int = 10
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None


class AgentTaskRouter:
    """
    Routes tasks to appropriate agents based on capabilities and system state.
    
    This class is responsible for:
    - Maintaining a registry of agents and their capabilities
    - Selecting the most appropriate agent for a given task
    - Balancing load across agents
    - Handling agent failures and fallbacks
    """
    
    def __init__(self):
        self._agents: Dict[str, AgentInfo] = {}
        self._routing_strategies: Dict[TaskType, Callable] = {}
        self._fallback_agents: Dict[TaskType, List[str]] = {}
        
        # Register default routing strategies
        self._register_default_strategies()
    
    def register_agent(self, agent_info: AgentInfo) -> None:
        """Register an agent with the router."""
        self._agents[agent_info.id] = agent_info
        logger.info(f"Registered agent: {agent_info.id} of type {agent_info.type.value}")
        
        # Update fallback agents for each task type
        for capability in agent_info.capabilities:
            for task_type in capability.task_types:
                if task_type not in self._fallback_agents:
                    self._fallback_agents[task_type] = []
                self._fallback_agents[task_type].append(agent_info.id)
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the router."""
        if agent_id in self._agents:
            agent_info = self._agents[agent_id]
            del self._agents[agent_id]
            
            # Remove from fallback agents
            for capability in agent_info.capabilities:
                for task_type in capability.task_types:
                    if task_type in self._fallback_agents and agent_id in self._fallback_agents[task_type]:
                        self._fallback_agents[task_type].remove(agent_id)
                        if not self._fallback_agents[task_type]:
                            del self._fallback_agents[task_type]
            
            logger.info(f"Unregistered agent: {agent_id}")
        else:
            logger.warning(f"Attempted to unregister non-existent agent: {agent_id}")
    
    def register_routing_strategy(self, task_type: TaskType, strategy: Callable) -> None:
        """Register a custom routing strategy for a task type."""
        self._routing_strategies[task_type] = strategy
        logger.info(f"Registered routing strategy for task type: {task_type.value}")
    
    def route_task(self, task_type: TaskType, task_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Route a task to the most appropriate agent.
        
        Args:
            task_type: The type of task to route
            task_data: Additional data about the task
            
        Returns:
            The ID of the selected agent, or None if no suitable agent is found
        """
        if task_data is None:
            task_data = {}
        
        # Get agents that can handle this task type
        capable_agents = self._get_capable_agents(task_type)
        
        if not capable_agents:
            logger.warning(f"No agents capable of handling task type: {task_type.value}")
            return None
        
        # Apply routing strategy
        if task_type in self._routing_strategies:
            strategy = self._routing_strategies[task_type]
            try:
                agent_id = strategy(capable_agents, task_data)
                if agent_id in capable_agents:
                    return agent_id
            except Exception as e:
                logger.error(f"Routing strategy failed for task type {task_type.value}: {str(e)}")
        
        # Default to load-based routing
        return self._route_by_load(capable_agents, task_data)
    
    def route_task_with_fallback(self, task_type: TaskType, task_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Route a task to the most appropriate agent with fallback support.
        
        If the primary agent fails, this method will attempt to route to fallback agents.
        
        Args:
            task_type: The type of task to route
            task_data: Additional data about the task
            
        Returns:
            The ID of the selected agent, or None if no suitable agent is found
        """
        primary_agent = self.route_task(task_type, task_data)
        
        if primary_agent is None:
            return None
        
        # Check if primary agent is available
        agent_info = self._agents.get(primary_agent)
        if agent_info and agent_info.is_active and agent_info.current_load < agent_info.max_load:
            return primary_agent
        
        # Try fallback agents
        fallback_agents = self._fallback_agents.get(task_type, [])
        for agent_id in fallback_agents:
            if agent_id == primary_agent:
                continue  # Skip primary agent, already checked
                
            agent_info = self._agents.get(agent_id)
            if agent_info and agent_info.is_active and agent_info.current_load < agent_info.max_load:
                return agent_id
        
        # No available agents
        return None
    
    def get_agent_load(self, agent_id: str) -> float:
        """Get the current load of an agent as a percentage (0.0 to 1.0)."""
        agent_info = self._agents.get(agent_id)
        if agent_info is None:
            return 0.0
        
        if agent_info.max_load <= 0:
            return 1.0
        
        return min(1.0, agent_info.current_load / agent_info.max_load)
    
    def update_agent_load(self, agent_id: str, delta: int) -> None:
        """Update the load of an agent by the specified delta."""
        agent_info = self._agents.get(agent_id)
        if agent_info:
            agent_info.current_load = max(0, agent_info.current_load + delta)
            logger.debug(f"Updated agent {agent_id} load to {agent_info.current_load}")
        else:
            logger.warning(f"Attempted to update load of non-existent agent: {agent_id}")
    
    def set_agent_active_status(self, agent_id: str, is_active: bool) -> None:
        """Set the active status of an agent."""
        agent_info = self._agents.get(agent_id)
        if agent_info:
            agent_info.is_active = is_active
            logger.info(f"Set agent {agent_id} active status to {is_active}")
        else:
            logger.warning(f"Attempted to set active status of non-existent agent: {agent_id}")
    
    def get_agents_for_task_type(self, task_type: TaskType) -> List[str]:
        """Get all agents that can handle a specific task type."""
        capable_agents = self._get_capable_agents(task_type)
        return list(capable_agents.keys())
    
    def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """Get information about an agent."""
        return self._agents.get(agent_id)
    
    def get_all_agents(self) -> Dict[str, AgentInfo]:
        """Get information about all agents."""
        return self._agents.copy()
    
    def _get_capable_agents(self, task_type: TaskType) -> Dict[str, AgentInfo]:
        """Get all agents that can handle a specific task type."""
        capable_agents = {}
        
        for agent_id, agent_info in self._agents.items():
            if not agent_info.is_active:
                continue
                
            for capability in agent_info.capabilities:
                if task_type in capability.task_types:
                    capable_agents[agent_id] = agent_info
                    break
        
        return capable_agents
    
    def _route_by_load(self, capable_agents: Dict[str, AgentInfo], task_data: Dict[str, Any]) -> Optional[str]:
        """Route a task based on agent load."""
        if not capable_agents:
            return None
        
        # Find agent with lowest load
        best_agent_id = None
        best_load = float('inf')
        
        for agent_id, agent_info in capable_agents.items():
            load = self.get_agent_load(agent_id)
            if load < best_load:
                best_load = load
                best_agent_id = agent_id
        
        return best_agent_id
    
    def _route_by_priority(self, capable_agents: Dict[str, AgentInfo], task_data: Dict[str, Any]) -> Optional[str]:
        """Route a task based on agent priority."""
        if not capable_agents:
            return None
        
        # Find agent with highest priority (lower number = higher priority)
        best_agent_id = None
        best_priority = float('inf')
        
        for agent_id, agent_info in capable_agents.items():
            # Get highest priority (lowest number) among all capabilities
            agent_priority = min(cap.priority for cap in agent_info.capabilities)
            
            if agent_priority < best_priority:
                best_priority = agent_priority
                best_agent_id = agent_id
        
        return best_agent_id
    
    def _register_default_strategies(self) -> None:
        """Register default routing strategies."""
        self._routing_strategies[TaskType.ANALYSIS] = self._route_by_priority
        self._routing_strategies[TaskType.GENERATION] = self._route_by_load
        self._routing_strategies[TaskType.REASONING] = self._route_by_priority
        self._routing_strategies[TaskType.PLANNING] = self._route_by_priority
        self._routing_strategies[TaskType.EXECUTION] = self._route_by_load
        self._routing_strategies[TaskType.VALIDATION] = self._route_by_priority
        self._routing_strategies[TaskType.MONITORING] = self._route_by_load
        self._routing_strategies[TaskType.LEARNING] = self._route_by_priority
        self._routing_strategies[TaskType.COMMUNICATION] = self._route_by_load
        self._routing_strategies[TaskType.COORDINATION] = self._route_by_priority