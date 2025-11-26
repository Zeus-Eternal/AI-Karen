"""
Agent Service Helper

This module provides helper functionality for agent operations in KAREN AI system.
It handles agent management, agent execution, and other agent-related operations.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class AgentServiceHelper:
    """
    Helper service for agent operations.
    
    This service provides methods for managing agents, executing agents,
    and other agent-related operations in KAREN AI system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the agent service helper.
        
        Args:
            config: Configuration dictionary for the agent service
        """
        self.config = config
        self.agents_enabled = config.get("agents_enabled", True)
        self.max_agents = config.get("max_agents", 100)
        self.agent_timeout = config.get("agent_timeout", 300)  # 5 minutes
        self.agents = {}
        self.agent_executions = []
        self._is_initialized = False
        self._is_running = False
        
    async def initialize(self) -> bool:
        """
        Initialize the agent service.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            logger.info("Initializing agent service")
            
            # Initialize agents
            if self.agents_enabled:
                await self._initialize_agents()
                
            self._is_initialized = True
            logger.info("Agent service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing agent service: {str(e)}")
            return False
    
    async def _initialize_agents(self) -> None:
        """Initialize agents."""
        # In a real implementation, this would set up agents
        logger.info("Initializing agents")
        
    async def start(self) -> bool:
        """
        Start the agent service.
        
        Returns:
            True if the service started successfully, False otherwise
        """
        try:
            logger.info("Starting agent service")
            
            # Start agents
            if self.agents_enabled:
                await self._start_agents()
                
            self._is_running = True
            logger.info("Agent service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting agent service: {str(e)}")
            return False
    
    async def _start_agents(self) -> None:
        """Start agents."""
        # In a real implementation, this would start agents
        logger.info("Starting agents")
        
    async def stop(self) -> bool:
        """
        Stop the agent service.
        
        Returns:
            True if the service stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping agent service")
            
            # Stop agents
            if self.agents_enabled:
                await self._stop_agents()
                
            self._is_running = False
            self._is_initialized = False
            logger.info("Agent service stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping agent service: {str(e)}")
            return False
    
    async def _stop_agents(self) -> None:
        """Stop agents."""
        # In a real implementation, this would stop agents
        logger.info("Stopping agents")
        
    async def health_check(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check the health of the agent service.
        
        Args:
            data: Optional data for the health check
            context: Optional context for the health check
            
        Returns:
            Dictionary containing health status information
        """
        try:
            if not self._is_initialized:
                return {"status": "unhealthy", "message": "Agent service is not initialized"}
                
            # Check agents health
            agents_health = {"status": "healthy", "message": "Agents are healthy"}
            if self.agents_enabled:
                agents_health = await self._health_check_agents()
                
            # Determine overall health
            overall_status = agents_health.get("status", "healthy")
            
            return {
                "status": overall_status,
                "message": f"Agent service is {overall_status}",
                "agents_health": agents_health,
                "agents_count": len(self.agents),
                "agent_executions_count": len(self.agent_executions)
            }
            
        except Exception as e:
            logger.error(f"Error checking agent service health: {str(e)}")
            return {"status": "unhealthy", "message": str(e)}
    
    async def _health_check_agents(self) -> Dict[str, Any]:
        """Check agents health."""
        # In a real implementation, this would check agents health
        return {"status": "healthy", "message": "Agents are healthy"}
        
    async def create_agent(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create an agent.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Agent service is not initialized"}
                
            # Check if agents are enabled
            if not self.agents_enabled:
                return {"status": "error", "message": "Agents are disabled"}
                
            # Get agent parameters
            name = data.get("name") if data else None
            description = data.get("description") if data else None
            agent_type = data.get("agent_type") if data else None
            version = data.get("version") if data else None
            author = data.get("author") if data else None
            capabilities = data.get("capabilities", []) if data else []
            code = data.get("code") if data else None
            metadata = data.get("metadata", {}) if data else {}
            
            # Validate name
            if not name:
                return {"status": "error", "message": "Name is required for agent"}
                
            # Validate agent type
            if not agent_type:
                return {"status": "error", "message": "Agent type is required for agent"}
                
            # Validate version
            if not version:
                return {"status": "error", "message": "Version is required for agent"}
                
            # Check if agent already exists
            if name in self.agents:
                return {"status": "error", "message": f"Agent {name} already exists"}
                
            # Check if we have reached the maximum number of agents
            if len(self.agents) >= self.max_agents:
                return {"status": "error", "message": "Maximum number of agents reached"}
                
            # Create agent
            agent_id = str(uuid.uuid4())
            agent = {
                "agent_id": agent_id,
                "name": name,
                "description": description,
                "agent_type": agent_type,
                "version": version,
                "author": author,
                "capabilities": capabilities,
                "code": code,
                "status": "created",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "metadata": metadata,
                "context": context or {}
            }
            
            # Add agent to agents
            self.agents[agent_id] = agent
            
            return {
                "status": "success",
                "message": "Agent created successfully",
                "agent_id": agent_id,
                "agent": agent
            }
            
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_agent(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get an agent.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Agent service is not initialized"}
                
            # Get agent parameters
            agent_id = data.get("agent_id") if data else None
            name = data.get("name") if data else None
            
            # Validate parameters
            if not agent_id and not name:
                return {"status": "error", "message": "Agent ID or name is required"}
                
            # Get agent
            agent = None
            if agent_id:
                if agent_id in self.agents:
                    agent = self.agents[agent_id]
            elif name:
                # Search for agent by name
                for a in self.agents.values():
                    if a["name"] == name:
                        agent = a
                        break
                            
            if not agent:
                return {"status": "error", "message": "Agent not found"}
                
            return {
                "status": "success",
                "message": "Agent retrieved successfully",
                "agent_id": agent["agent_id"],
                "agent": agent
            }
            
        except Exception as e:
            logger.error(f"Error getting agent: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def update_agent(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update an agent.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Agent service is not initialized"}
                
            # Get agent parameters
            agent_id = data.get("agent_id") if data else None
            name = data.get("name") if data else None
            description = data.get("description") if data else None
            agent_type = data.get("agent_type") if data else None
            version = data.get("version") if data else None
            author = data.get("author") if data else None
            capabilities = data.get("capabilities") if data else None
            code = data.get("code") if data else None
            status = data.get("status") if data else None
            metadata = data.get("metadata") if data else None
            
            # Validate agent_id
            if not agent_id:
                return {"status": "error", "message": "Agent ID is required"}
                
            # Get agent
            if agent_id not in self.agents:
                return {"status": "error", "message": f"Agent {agent_id} not found"}
                
            agent = self.agents[agent_id]
                
            # Update agent
            if name is not None:
                agent["name"] = name
            if description is not None:
                agent["description"] = description
            if agent_type is not None:
                agent["agent_type"] = agent_type
            if version is not None:
                agent["version"] = version
            if author is not None:
                agent["author"] = author
            if capabilities is not None:
                agent["capabilities"] = capabilities
            if code is not None:
                agent["code"] = code
            if status is not None:
                agent["status"] = status
            if metadata is not None:
                agent["metadata"].update(metadata)
                
            # Update timestamp
            agent["updated_at"] = datetime.now().isoformat()
            
            return {
                "status": "success",
                "message": "Agent updated successfully",
                "agent_id": agent_id,
                "agent": agent
            }
            
        except Exception as e:
            logger.error(f"Error updating agent: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def delete_agent(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Delete an agent.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Agent service is not initialized"}
                
            # Get agent parameters
            agent_id = data.get("agent_id") if data else None
            
            # Validate agent_id
            if not agent_id:
                return {"status": "error", "message": "Agent ID is required"}
                
            # Get agent
            if agent_id not in self.agents:
                return {"status": "error", "message": f"Agent {agent_id} not found"}
                
            agent = self.agents.pop(agent_id)
                
            return {
                "status": "success",
                "message": "Agent deleted successfully",
                "agent_id": agent_id,
                "agent": agent
            }
            
        except Exception as e:
            logger.error(f"Error deleting agent: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def execute_agent(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute an agent.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Agent service is not initialized"}
                
            # Check if agents are enabled
            if not self.agents_enabled:
                return {"status": "error", "message": "Agents are disabled"}
                
            # Get agent parameters
            agent_id = data.get("agent_id") if data else None
            name = data.get("name") if data else None
            input_data = data.get("input_data", {}) if data else {}
            
            # Validate parameters
            if not agent_id and not name:
                return {"status": "error", "message": "Agent ID or name is required"}
                
            # Get agent
            agent = None
            if agent_id:
                if agent_id in self.agents:
                    agent = self.agents[agent_id]
            elif name:
                # Search for agent by name
                for a in self.agents.values():
                    if a["name"] == name:
                        agent = a
                        break
                            
            if not agent:
                return {"status": "error", "message": "Agent not found"}
                
            # Create agent execution
            execution_id = str(uuid.uuid4())
            agent_execution = {
                "execution_id": execution_id,
                "agent_id": agent["agent_id"],
                "agent_name": agent["name"],
                "status": "running",
                "input_data": input_data,
                "output_data": {},
                "created_at": datetime.now().isoformat(),
                "context": context or {}
            }
            
            # Add agent execution to agent executions
            self.agent_executions.append(agent_execution)
            
            # Execute agent
            result = await self._execute_agent(agent, agent_execution, input_data, context)
            
            # Update agent execution
            agent_execution["status"] = result.get("status", "completed")
            agent_execution["output_data"] = result.get("output_data", {})
            agent_execution["completed_at"] = datetime.now().isoformat()
            agent_execution["result"] = result
            
            return {
                "status": "success",
                "message": "Agent executed successfully",
                "execution_id": execution_id,
                "agent_id": agent["agent_id"],
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error executing agent: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _execute_agent(self, agent: Dict[str, Any], agent_execution: Dict[str, Any], input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute an agent."""
        # In a real implementation, this would execute an agent
        logger.info(f"Executing agent {agent['agent_id']} with name: {agent['name']}")
        
        # Get agent details
        agent_id = agent["agent_id"]
        agent_name = agent["name"]
        agent_type = agent["agent_type"]
        capabilities = agent["capabilities"]
        
        # Simulate agent execution
        await asyncio.sleep(2)
        
        # Return agent execution result
        result = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "agent_type": agent_type,
            "capabilities": capabilities,
            "status": "completed",
            "message": f"Agent {agent_name} executed successfully",
            "output_data": {
                "agent_output": f"Output from agent {agent_name}",
                "timestamp": datetime.now().isoformat()
            },
            "execution_time": 2.0  # Simulated execution time
        }
        
        return result
    
    async def list_agents(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        List agents.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Agent service is not initialized"}
                
            # Get list parameters
            status = data.get("status") if data else None
            agent_type = data.get("agent_type") if data else None
            limit = data.get("limit", 100) if data else 100
            offset = data.get("offset", 0) if data else 0
            
            # Get all agents
            all_agents = list(self.agents.values())
                
            # Filter agents based on parameters
            filtered_agents = []
            for agent in all_agents:
                if status and agent["status"] != status:
                    continue
                if agent_type and agent["agent_type"] != agent_type:
                    continue
                filtered_agents.append(agent)
                
            # Sort agents by creation time (newest first)
            filtered_agents.sort(key=lambda x: x["created_at"], reverse=True)
                
            # Apply pagination
            paginated_agents = filtered_agents[offset:offset+limit]
            
            return {
                "status": "success",
                "message": "Agents listed successfully",
                "total_count": len(filtered_agents),
                "limit": limit,
                "offset": offset,
                "agents": paginated_agents
            }
            
        except Exception as e:
            logger.error(f"Error listing agents: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def list_agent_executions(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        List agent executions.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Agent service is not initialized"}
                
            # Get list parameters
            agent_id = data.get("agent_id") if data else None
            status = data.get("status") if data else None
            limit = data.get("limit", 100) if data else 100
            offset = data.get("offset", 0) if data else 0
            
            # Get all agent executions
            all_executions = self.agent_executions
                
            # Filter agent executions based on parameters
            filtered_executions = []
            for execution in all_executions:
                if agent_id and execution["agent_id"] != agent_id:
                    continue
                if status and execution["status"] != status:
                    continue
                filtered_executions.append(execution)
                
            # Sort agent executions by creation time (newest first)
            filtered_executions.sort(key=lambda x: x["created_at"], reverse=True)
                
            # Apply pagination
            paginated_executions = filtered_executions[offset:offset+limit]
            
            return {
                "status": "success",
                "message": "Agent executions listed successfully",
                "total_count": len(filtered_executions),
                "limit": limit,
                "offset": offset,
                "agent_executions": paginated_executions
            }
            
        except Exception as e:
            logger.error(f"Error listing agent executions: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def search_agents(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search agents.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Agent service is not initialized"}
                
            # Get search parameters
            query = data.get("query") if data else None
            agent_type = data.get("agent_type") if data else None
            status = data.get("status") if data else None
            start_time = data.get("start_time") if data else None
            end_time = data.get("end_time") if data else None
            limit = data.get("limit", 100) if data else 100
            offset = data.get("offset", 0) if data else 0
            
            if not query:
                return {"status": "error", "message": "Query is required for search"}
                
            # Get all agents
            all_agents = list(self.agents.values())
                
            # Search agents based on query
            matched_agents = []
            for agent in all_agents:
                # Check if agent matches query
                agent_json = json.dumps(agent, default=str)
                if query.lower() in agent_json.lower():
                    # Check additional filters
                    if agent_type and agent["agent_type"] != agent_type:
                        continue
                    if status and agent["status"] != status:
                        continue
                    if start_time and agent["created_at"] < start_time:
                        continue
                    if end_time and agent["created_at"] > end_time:
                        continue
                    matched_agents.append(agent)
                    
            # Sort agents by creation time (newest first)
            matched_agents.sort(key=lambda x: x["created_at"], reverse=True)
                
            # Apply pagination
            paginated_agents = matched_agents[offset:offset+limit]
            
            return {
                "status": "success",
                "message": "Agents searched successfully",
                "query": query,
                "total_count": len(matched_agents),
                "limit": limit,
                "offset": offset,
                "agents": paginated_agents
            }
            
        except Exception as e:
            logger.error(f"Error searching agents: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_agent_execution(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get an agent execution.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Agent service is not initialized"}
                
            # Get execution parameters
            execution_id = data.get("execution_id") if data else None
            
            # Validate execution_id
            if not execution_id:
                return {"status": "error", "message": "Execution ID is required"}
                
            # Get agent execution
            agent_execution = None
            for execution in self.agent_executions:
                if execution["execution_id"] == execution_id:
                    agent_execution = execution
                    break
                    
            if not agent_execution:
                return {"status": "error", "message": f"Agent execution {execution_id} not found"}
                
            return {
                "status": "success",
                "message": "Agent execution retrieved successfully",
                "execution_id": execution_id,
                "agent_execution": agent_execution
            }
            
        except Exception as e:
            logger.error(f"Error getting agent execution: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_status(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get the status of the agent service.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the status information
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Agent service is not initialized"}
                
            status = {
                "agents_enabled": self.agents_enabled,
                "is_running": self._is_running,
                "agents_count": len(self.agents),
                "agent_executions_count": len(self.agent_executions),
                "max_agents": self.max_agents,
                "agent_timeout": self.agent_timeout
            }
            
            return {
                "status": "success",
                "message": "Agent status retrieved successfully",
                "agent_status": status
            }
            
        except Exception as e:
            logger.error(f"Error getting agent status: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_stats(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get statistics for the agent service.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the statistics
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Agent service is not initialized"}
                
            # Get all agents
            all_agents = list(self.agents.values())
                
            # Count by status
            status_counts = {}
            for agent in all_agents:
                status = agent["status"]
                if status not in status_counts:
                    status_counts[status] = 0
                status_counts[status] += 1
                
            # Count by agent type
            type_counts = {}
            for agent in all_agents:
                agent_type = agent["agent_type"]
                if agent_type not in type_counts:
                    type_counts[agent_type] = 0
                type_counts[agent_type] += 1
                
            # Get all agent executions
            all_executions = self.agent_executions
                
            # Count executions by status
            execution_status_counts = {}
            for execution in all_executions:
                status = execution["status"]
                if status not in execution_status_counts:
                    execution_status_counts[status] = 0
                execution_status_counts[status] += 1
                
            # Calculate average execution time for completed agent executions
            completed_executions = [e for e in all_executions if e["status"] == "completed"]
            total_execution_time = 0
            for execution in completed_executions:
                if "created_at" in execution and "completed_at" in execution:
                    start_time = datetime.fromisoformat(execution["created_at"])
                    end_time = datetime.fromisoformat(execution["completed_at"])
                    execution_time = (end_time - start_time).total_seconds()
                    total_execution_time += execution_time
                    
            average_execution_time = total_execution_time / len(completed_executions) if completed_executions else 0
            
            stats = {
                "agents_enabled": self.agents_enabled,
                "is_running": self._is_running,
                "total_agents": len(all_agents),
                "agent_executions_count": len(all_executions),
                "completed_executions_count": len(completed_executions),
                "max_agents": self.max_agents,
                "agent_timeout": self.agent_timeout,
                "status_counts": status_counts,
                "type_counts": type_counts,
                "execution_status_counts": execution_status_counts,
                "average_execution_time": average_execution_time
            }
            
            return {
                "status": "success",
                "message": "Agent statistics retrieved successfully",
                "agent_stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error getting agent statistics: {str(e)}")
            return {"status": "error", "message": str(e)}