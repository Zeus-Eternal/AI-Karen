"""
Agent Registry Service

This service manages the registry of all available agents in the Kari system,
including their capabilities, metadata, and availability.
"""

from typing import Dict, List, Any, Optional, Union
import logging
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Enumeration of agent statuses."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"


@dataclass
class AgentCapability:
    """Represents a capability of an agent."""
    name: str
    description: str
    parameters: Dict[str, Any]
    return_type: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentMetadata:
    """Metadata about an agent."""
    name: str
    description: str
    version: str
    author: str
    tags: List[str]
    requirements: List[str]
    dependencies: List[str]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentDefinition:
    """Complete definition of an agent."""
    id: str
    type: str
    path: str
    status: AgentStatus
    capabilities: List[AgentCapability]
    metadata: AgentMetadata
    config: Dict[str, Any]
    last_updated: str
    metadata_ext: Optional[Dict[str, Any]] = None


class AgentRegistry:
    """
    Manages the registry of all available agents.
    
    This class is responsible for:
    - Registering and unregistering agents
    - Maintaining agent metadata and capabilities
    - Querying agents by various criteria
    - Persisting and loading agent definitions
    """
    
    def __init__(self, registry_path: Optional[Union[str, Path]] = None):
        self._agents: Dict[str, AgentDefinition] = {}
        self._registry_path = Path(registry_path) if registry_path else None
        
        # Load existing registry if path is provided
        if self._registry_path and self._registry_path.exists():
            self.load_registry()
    
    def register_agent(self, agent_def: AgentDefinition) -> None:
        """Register an agent with the registry."""
        self._agents[agent_def.id] = agent_def
        logger.info(f"Registered agent: {agent_def.id}")
        
        # Save registry if path is provided
        if self._registry_path:
            self.save_registry()
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the registry.
        
        Args:
            agent_id: ID of the agent to unregister
            
        Returns:
            True if agent was unregistered, False if not found
        """
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
            
            # Save registry if path is provided
            if self._registry_path:
                self.save_registry()
            
            return True
        else:
            logger.warning(f"Attempted to unregister non-existent agent: {agent_id}")
            return False
    
    def get_agent(self, agent_id: str) -> Optional[AgentDefinition]:
        """Get an agent by ID."""
        return self._agents.get(agent_id)
    
    def get_all_agents(self) -> Dict[str, AgentDefinition]:
        """Get all agents in the registry."""
        return self._agents.copy()
    
    def get_agents_by_type(self, agent_type: str) -> List[AgentDefinition]:
        """Get all agents of a specific type."""
        return [agent for agent in self._agents.values() if agent.type == agent_type]
    
    def get_agents_by_status(self, status: AgentStatus) -> List[AgentDefinition]:
        """Get all agents with a specific status."""
        return [agent for agent in self._agents.values() if agent.status == status]
    
    def get_agents_by_capability(self, capability_name: str) -> List[AgentDefinition]:
        """Get all agents that have a specific capability."""
        matching_agents = []
        
        for agent in self._agents.values():
            for capability in agent.capabilities:
                if capability.name == capability_name:
                    matching_agents.append(agent)
                    break
        
        return matching_agents
    
    def get_agents_by_tag(self, tag: str) -> List[AgentDefinition]:
        """Get all agents that have a specific tag."""
        return [agent for agent in self._agents.values() if tag in agent.metadata.tags]
    
    def search_agents(self, query: str) -> List[AgentDefinition]:
        """
        Search for agents by name, description, or capability.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching agents
        """
        query_lower = query.lower()
        matching_agents = []
        
        for agent in self._agents.values():
            # Check name, description, and author
            if (query_lower in agent.metadata.name.lower() or
                query_lower in agent.metadata.description.lower() or
                query_lower in agent.metadata.author.lower()):
                matching_agents.append(agent)
                continue
            
            # Check capabilities
            for capability in agent.capabilities:
                if (query_lower in capability.name.lower() or
                    query_lower in capability.description.lower()):
                    matching_agents.append(agent)
                    break
            
            # Check tags
            for tag in agent.metadata.tags:
                if query_lower in tag.lower():
                    matching_agents.append(agent)
                    break
        
        return matching_agents
    
    def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """
        Update the status of an agent.
        
        Args:
            agent_id: ID of the agent to update
            status: New status for the agent
            
        Returns:
            True if agent status was updated, False if agent not found
        """
        agent = self._agents.get(agent_id)
        if agent:
            agent.status = status
            logger.info(f"Updated agent {agent_id} status to {status.value}")
            
            # Save registry if path is provided
            if self._registry_path:
                self.save_registry()
            
            return True
        else:
            logger.warning(f"Attempted to update status of non-existent agent: {agent_id}")
            return False
    
    def update_agent_config(self, agent_id: str, config: Dict[str, Any]) -> bool:
        """
        Update the configuration of an agent.
        
        Args:
            agent_id: ID of the agent to update
            config: New configuration for the agent
            
        Returns:
            True if agent config was updated, False if agent not found
        """
        agent = self._agents.get(agent_id)
        if agent:
            agent.config = config
            logger.info(f"Updated agent {agent_id} configuration")
            
            # Save registry if path is provided
            if self._registry_path:
                self.save_registry()
            
            return True
        else:
            logger.warning(f"Attempted to update config of non-existent agent: {agent_id}")
            return False
    
    def add_agent_capability(self, agent_id: str, capability: AgentCapability) -> bool:
        """
        Add a capability to an agent.
        
        Args:
            agent_id: ID of the agent to update
            capability: Capability to add
            
        Returns:
            True if capability was added, False if agent not found
        """
        agent = self._agents.get(agent_id)
        if agent:
            agent.capabilities.append(capability)
            logger.info(f"Added capability {capability.name} to agent {agent_id}")
            
            # Save registry if path is provided
            if self._registry_path:
                self.save_registry()
            
            return True
        else:
            logger.warning(f"Attempted to add capability to non-existent agent: {agent_id}")
            return False
    
    def remove_agent_capability(self, agent_id: str, capability_name: str) -> bool:
        """
        Remove a capability from an agent.
        
        Args:
            agent_id: ID of the agent to update
            capability_name: Name of the capability to remove
            
        Returns:
            True if capability was removed, False if agent not found or capability not found
        """
        agent = self._agents.get(agent_id)
        if agent:
            for i, capability in enumerate(agent.capabilities):
                if capability.name == capability_name:
                    agent.capabilities.pop(i)
                    logger.info(f"Removed capability {capability_name} from agent {agent_id}")
                    
                    # Save registry if path is provided
                    if self._registry_path:
                        self.save_registry()
                    
                    return True
            
            logger.warning(f"Capability {capability_name} not found for agent {agent_id}")
            return False
        else:
            logger.warning(f"Attempted to remove capability from non-existent agent: {agent_id}")
            return False
    
    def save_registry(self) -> None:
        """Save the registry to disk."""
        if not self._registry_path:
            logger.warning("No registry path provided, cannot save registry")
            return
        
        # Create directory if it doesn't exist
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert dataclasses to dictionaries for JSON serialization
        agents_data = {agent_id: asdict(agent) for agent_id, agent in self._agents.items()}
        
        # Handle enum serialization
        for agent_data in agents_data.values():
            agent_data["status"] = agent_data["status"].value
        
        with open(self._registry_path, 'w') as f:
            json.dump(agents_data, f, indent=2)
        
        logger.info(f"Saved registry to {self._registry_path}")
    
    def load_registry(self) -> None:
        """Load the registry from disk."""
        if not self._registry_path or not self._registry_path.exists():
            logger.warning("No registry file found, cannot load registry")
            return
        
        with open(self._registry_path, 'r') as f:
            agents_data = json.load(f)
        
        # Convert dictionaries back to dataclasses
        self._agents = {}
        for agent_id, agent_data in agents_data.items():
            # Handle enum deserialization
            agent_data["status"] = AgentStatus(agent_data["status"])
            
            # Convert capability dictionaries back to dataclasses
            capabilities = []
            for cap_data in agent_data["capabilities"]:
                capabilities.append(AgentCapability(**cap_data))
            agent_data["capabilities"] = capabilities
            
            # Convert metadata dictionary back to dataclass
            agent_data["metadata"] = AgentMetadata(**agent_data["metadata"])
            
            # Create agent definition
            self._agents[agent_id] = AgentDefinition(**agent_data)
        
        logger.info(f"Loaded registry from {self._registry_path} with {len(self._agents)} agents")
    
    def validate_registry(self) -> Dict[str, List[str]]:
        """
        Validate the registry for consistency and completeness.
        
        Returns:
            Dictionary of validation errors by agent ID
        """
        errors = {}
        
        for agent_id, agent in self._agents.items():
            agent_errors = []
            
            # Check required fields
            if not agent.id:
                agent_errors.append("Missing agent ID")
            
            if not agent.type:
                agent_errors.append("Missing agent type")
            
            if not agent.path:
                agent_errors.append("Missing agent path")
            
            if not agent.capabilities:
                agent_errors.append("Agent has no capabilities")
            
            # Check metadata
            if not agent.metadata.name:
                agent_errors.append("Missing agent name in metadata")
            
            if not agent.metadata.description:
                agent_errors.append("Missing agent description in metadata")
            
            if not agent.metadata.version:
                agent_errors.append("Missing agent version in metadata")
            
            # Check if agent file exists
            agent_path = Path(agent.path)
            if not agent_path.exists():
                agent_errors.append(f"Agent file does not exist: {agent.path}")
            
            # Check capabilities
            for i, capability in enumerate(agent.capabilities):
                if not capability.name:
                    agent_errors.append(f"Capability {i} has no name")
                
                if not capability.description:
                    agent_errors.append(f"Capability {i} has no description")
                
                if not capability.return_type:
                    agent_errors.append(f"Capability {i} has no return type")
            
            if agent_errors:
                errors[agent_id] = agent_errors
        
        return errors
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the agent registry.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_agents": len(self._agents),
            "agents_by_status": {},
            "agents_by_type": {},
            "total_capabilities": 0,
            "capability_distribution": {}
        }
        
        # Count by status
        for status in AgentStatus:
            stats["agents_by_status"][status.value] = len(self.get_agents_by_status(status))
        
        # Count by type
        agent_types = set(agent.type for agent in self._agents.values())
        for agent_type in agent_types:
            stats["agents_by_type"][agent_type] = len(self.get_agents_by_type(agent_type))
        
        # Count capabilities
        for agent in self._agents.values():
            stats["total_capabilities"] += len(agent.capabilities)
            
            for capability in agent.capabilities:
                if capability.name not in stats["capability_distribution"]:
                    stats["capability_distribution"][capability.name] = 0
                stats["capability_distribution"][capability.name] += 1
        
        return stats