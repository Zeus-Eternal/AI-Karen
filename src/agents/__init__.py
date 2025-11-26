"""
Agents Package

This package contains the agent system for the Kari platform.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Registry for managing agents.
    
    This class provides functionality to discover, load, and manage agents
    within the Kari platform.
    """
    
    def __init__(self):
        """Initialize the agent registry."""
        self.agents = {}
        self.index_path = os.path.join(os.path.dirname(__file__), 'index.json')
        self._load_index()
    
    def _load_index(self) -> None:
        """Load the agent index."""
        if os.path.exists(self.index_path):
            with open(self.index_path, 'r') as f:
                self.agents = json.load(f)
        else:
            self.agents = {}
    
    def get_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all registered agents.
        
        Returns:
            Dictionary of all registered agents
        """
        return self.agents
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific agent by ID.
        
        Args:
            agent_id: ID of the agent to get
            
        Returns:
            Agent information or None if not found
        """
        return self.agents.get(agent_id)
    
    def register_agent(self, agent_id: str, agent_info: Dict[str, Any]) -> None:
        """
        Register an agent.
        
        Args:
            agent_id: ID of the agent to register
            agent_info: Information about the agent
        """
        self.agents[agent_id] = agent_info
        self._save_index()
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent.
        
        Args:
            agent_id: ID of the agent to unregister
            
        Returns:
            True if the agent was unregistered, False if it wasn't found
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            self._save_index()
            return True
        return False
    
    def _save_index(self) -> None:
        """Save the agent index."""
        with open(self.index_path, 'w') as f:
            json.dump(self.agents, f, indent=2)


# Global registry instance
_registry = None


def get_registry() -> AgentRegistry:
    """
    Get the global agent registry instance.
    
    Returns:
        The global agent registry instance
    """
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


def get_agents() -> Dict[str, Dict[str, Any]]:
    """
    Get all registered agents.
    
    Returns:
        Dictionary of all registered agents
    """
    return get_registry().get_agents()


def get_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific agent by ID.
    
    Args:
        agent_id: ID of the agent to get
        
    Returns:
        Agent information or None if not found
    """
    return get_registry().get_agent(agent_id)


def register_agent(agent_id: str, agent_info: Dict[str, Any]) -> None:
    """
    Register an agent.
    
    Args:
        agent_id: ID of the agent to register
        agent_info: Information about the agent
    """
    get_registry().register_agent(agent_id, agent_info)


def unregister_agent(agent_id: str) -> bool:
    """
    Unregister an agent.
    
    Args:
        agent_id: ID of the agent to unregister
        
    Returns:
        True if the agent was unregistered, False if it wasn't found
    """
    return get_registry().unregister_agent(agent_id)