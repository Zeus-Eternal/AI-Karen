"""
Agent registry and discovery.

This module provides functionality for loading and discovering agents.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import UUID


class AgentRegistry:
    """Registry for agent discovery and loading."""
    
    def __init__(self, agents_dir: Optional[Path] = None):
        """Initialize the agent registry.
        
        Args:
            agents_dir: Path to the agents directory. If None, uses default.
        """
        if agents_dir is None:
            agents_dir = Path(__file__).parent
        
        self.agents_dir = agents_dir
        self.agents: Dict[str, Dict[str, Any]] = {}
        self._load_agents()
    
    def _load_agents(self) -> None:
        """Load all agent manifests."""
        index_file = self.agents_dir / "index.json"
        
        if not index_file.exists():
            # Create empty index file
            with open(index_file, 'w') as f:
                json.dump({}, f)
            return
        
        try:
            with open(index_file, 'r') as f:
                index_data = json.load(f)
            
            for agent_id, agent_info in index_data.items():
                self.agents[agent_id] = agent_info
                
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading agent index: {e}")
    
    def load_agent_manifests(self) -> Dict[str, Dict[str, Any]]:
        """Load all agent manifests.
        
        Returns:
            Dictionary mapping agent IDs to agent information.
        """
        for agent_dir in self.agents_dir.iterdir():
            if agent_dir.is_dir() and not agent_dir.name.startswith('_'):
                manifest_file = agent_dir / "agent_manifest.json"
                
                if manifest_file.exists():
                    try:
                        with open(manifest_file, 'r') as f:
                            manifest_data = json.load(f)
                        
                        agent_id = manifest_data.get("id", agent_dir.name)
                        self.agents[agent_id] = {
                            "name": manifest_data.get("name", agent_dir.name),
                            "type": manifest_data.get("type", "worker"),
                            "version": manifest_data.get("version", "1.0.0"),
                            "description": manifest_data.get("description", ""),
                            "entry_point": manifest_data.get("entry_point", "handler.py"),
                            "path": str(agent_dir),
                            "manifest": manifest_data
                        }
                        
                    except (json.JSONDecodeError, FileNotFoundError) as e:
                        print(f"Error loading agent manifest from {manifest_file}: {e}")
        
        # Update index file
        index_file = self.agents_dir / "index.json"
        with open(index_file, 'w') as f:
            json.dump(self.agents, f, indent=2)
        
        return self.agents
    
    def get_agent_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information by ID.
        
        Args:
            agent_id: ID of the agent to retrieve.
            
        Returns:
            Agent information dictionary, or None if not found.
        """
        return self.agents.get(agent_id)
    
    def get_agents_by_type(self, agent_type: str) -> List[Dict[str, Any]]:
        """Get all agents of a specific type.
        
        Args:
            agent_type: Type of agents to retrieve.
            
        Returns:
            List of agent information dictionaries.
        """
        return [
            agent for agent in self.agents.values()
            if agent.get("type") == agent_type
        ]
    
    def get_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get all agents.
        
        Returns:
            Dictionary mapping agent IDs to agent information.
        """
        return self.agents
    
    def reload_agents(self) -> None:
        """Reload all agent manifests."""
        self.agents.clear()
        self._load_agents()


# Global registry instance
_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Get the global agent registry instance.
    
    Returns:
        Global AgentRegistry instance.
    """
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


def load_agent_manifests() -> Dict[str, Dict[str, Any]]:
    """Load all agent manifests.
    
    Returns:
        Dictionary mapping agent IDs to agent information.
    """
    return get_registry().load_agent_manifests()


def get_agent_by_id(agent_id: str) -> Optional[Dict[str, Any]]:
    """Get agent information by ID.
    
    Args:
        agent_id: ID of the agent to retrieve.
        
    Returns:
        Agent information dictionary, or None if not found.
    """
    return get_registry().get_agent_by_id(agent_id)


def get_agents_by_type(agent_type: str) -> List[Dict[str, Any]]:
    """Get all agents of a specific type.
    
    Args:
        agent_type: Type of agents to retrieve.
        
    Returns:
        List of agent information dictionaries.
    """
    return get_registry().get_agents_by_type(agent_type)