"""
Tools Service Helper

This module provides helper functionality for tools operations in KAREN AI system.
It handles tool management, tool execution, and other tool-related operations.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ToolsServiceHelper:
    """
    Helper service for tools operations.
    
    This service provides methods for managing tools, executing tools,
    and other tool-related operations in KAREN AI system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the tools service helper.
        
        Args:
            config: Configuration dictionary for the tools service
        """
        self.config = config
        self.tools_enabled = config.get("tools_enabled", True)
        self.max_tools = config.get("max_tools", 100)
        self.tool_timeout = config.get("tool_timeout", 30)  # 30 seconds
        self.tools = {}
        self.active_tools = {}
        self.tool_executions = []
        self._is_initialized = False
        self._is_running = False
        
    async def initialize(self) -> bool:
        """
        Initialize the tools service.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            logger.info("Initializing tools service")
            
            # Initialize tools
            if self.tools_enabled:
                await self._initialize_tools()
                
            self._is_initialized = True
            logger.info("Tools service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing tools service: {str(e)}")
            return False
    
    async def _initialize_tools(self) -> None:
        """Initialize tools."""
        # In a real implementation, this would set up tools
        logger.info("Initializing tools")
        
    async def start(self) -> bool:
        """
        Start the tools service.
        
        Returns:
            True if the service started successfully, False otherwise
        """
        try:
            logger.info("Starting tools service")
            
            # Start tools
            if self.tools_enabled:
                await self._start_tools()
                
            self._is_running = True
            logger.info("Tools service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting tools service: {str(e)}")
            return False
    
    async def _start_tools(self) -> None:
        """Start tools."""
        # In a real implementation, this would start tools
        logger.info("Starting tools")
        
    async def stop(self) -> bool:
        """
        Stop the tools service.
        
        Returns:
            True if the service stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping tools service")
            
            # Stop tools
            if self.tools_enabled:
                await self._stop_tools()
                
            self._is_running = False
            self._is_initialized = False
            logger.info("Tools service stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping tools service: {str(e)}")
            return False
    
    async def _stop_tools(self) -> None:
        """Stop tools."""
        # In a real implementation, this would stop tools
        logger.info("Stopping tools")
        
    async def health_check(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check the health of the tools service.
        
        Args:
            data: Optional data for the health check
            context: Optional context for the health check
            
        Returns:
            Dictionary containing health status information
        """
        try:
            if not self._is_initialized:
                return {"status": "unhealthy", "message": "Tools service is not initialized"}
                
            # Check tools health
            tools_health = {"status": "healthy", "message": "Tools are healthy"}
            if self.tools_enabled:
                tools_health = await self._health_check_tools()
                
            # Determine overall health
            overall_status = tools_health.get("status", "healthy")
            
            return {
                "status": overall_status,
                "message": f"Tools service is {overall_status}",
                "tools_health": tools_health,
                "tools_count": len(self.tools),
                "active_tools_count": len(self.active_tools),
                "tool_executions_count": len(self.tool_executions)
            }
            
        except Exception as e:
            logger.error(f"Error checking tools service health: {str(e)}")
            return {"status": "unhealthy", "message": str(e)}
    
    async def _health_check_tools(self) -> Dict[str, Any]:
        """Check tools health."""
        # In a real implementation, this would check tools health
        return {"status": "healthy", "message": "Tools are healthy"}
        
    async def create_tool(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a tool.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Tools service is not initialized"}
                
            # Check if tools are enabled
            if not self.tools_enabled:
                return {"status": "error", "message": "Tools are disabled"}
                
            # Get tool parameters
            name = data.get("name") if data else None
            description = data.get("description") if data else None
            tool_type = data.get("tool_type") if data else None
            parameters = data.get("parameters", []) if data else []
            code = data.get("code") if data else None
            metadata = data.get("metadata", {}) if data else {}
            
            # Validate name
            if not name:
                return {"status": "error", "message": "Name is required for tool"}
                
            # Validate tool type
            if not tool_type:
                return {"status": "error", "message": "Tool type is required for tool"}
                
            # Check if tool already exists
            if name in self.tools:
                return {"status": "error", "message": f"Tool {name} already exists"}
                
            # Check if we have reached the maximum number of tools
            if len(self.tools) >= self.max_tools:
                return {"status": "error", "message": "Maximum number of tools reached"}
                
            # Create tool
            tool_id = str(uuid.uuid4())
            tool = {
                "tool_id": tool_id,
                "name": name,
                "description": description,
                "tool_type": tool_type,
                "parameters": parameters,
                "code": code,
                "status": "inactive",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "metadata": metadata,
                "context": context or {}
            }
            
            # Add tool to tools
            self.tools[tool_id] = tool
            
            return {
                "status": "success",
                "message": "Tool created successfully",
                "tool_id": tool_id,
                "tool": tool
            }
            
        except Exception as e:
            logger.error(f"Error creating tool: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_tool(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get a tool.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Tools service is not initialized"}
                
            # Get tool parameters
            tool_id = data.get("tool_id") if data else None
            name = data.get("name") if data else None
            
            # Validate parameters
            if not tool_id and not name:
                return {"status": "error", "message": "Tool ID or name is required"}
                
            # Get tool
            tool = None
            if tool_id:
                if tool_id in self.tools:
                    tool = self.tools[tool_id]
                elif tool_id in self.active_tools:
                    tool = self.active_tools[tool_id]
            elif name:
                # Search for tool by name
                for t in self.tools.values():
                    if t["name"] == name:
                        tool = t
                        break
                if not tool:
                    for t in self.active_tools.values():
                        if t["name"] == name:
                            tool = t
                            break
                            
            if not tool:
                return {"status": "error", "message": "Tool not found"}
                
            return {
                "status": "success",
                "message": "Tool retrieved successfully",
                "tool_id": tool["tool_id"],
                "tool": tool
            }
            
        except Exception as e:
            logger.error(f"Error getting tool: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def update_tool(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update a tool.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Tools service is not initialized"}
                
            # Get tool parameters
            tool_id = data.get("tool_id") if data else None
            name = data.get("name") if data else None
            description = data.get("description") if data else None
            tool_type = data.get("tool_type") if data else None
            parameters = data.get("parameters") if data else None
            code = data.get("code") if data else None
            status = data.get("status") if data else None
            metadata = data.get("metadata") if data else None
            
            # Validate parameters
            if not tool_id:
                return {"status": "error", "message": "Tool ID is required"}
                
            # Get tool
            if tool_id in self.tools:
                tool = self.tools[tool_id]
            elif tool_id in self.active_tools:
                tool = self.active_tools[tool_id]
            else:
                return {"status": "error", "message": f"Tool {tool_id} not found"}
                
            # Update tool
            if name is not None:
                tool["name"] = name
            if description is not None:
                tool["description"] = description
            if tool_type is not None:
                tool["tool_type"] = tool_type
            if parameters is not None:
                tool["parameters"] = parameters
            if code is not None:
                tool["code"] = code
            if status is not None:
                tool["status"] = status
            if metadata is not None:
                tool["metadata"].update(metadata)
                
            # Update timestamp
            tool["updated_at"] = datetime.now().isoformat()
            
            return {
                "status": "success",
                "message": "Tool updated successfully",
                "tool_id": tool_id,
                "tool": tool
            }
            
        except Exception as e:
            logger.error(f"Error updating tool: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def delete_tool(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Delete a tool.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Tools service is not initialized"}
                
            # Get tool parameters
            tool_id = data.get("tool_id") if data else None
            
            # Validate parameters
            if not tool_id:
                return {"status": "error", "message": "Tool ID is required"}
                
            # Get tool
            if tool_id in self.tools:
                tool = self.tools.pop(tool_id)
            elif tool_id in self.active_tools:
                tool = self.active_tools.pop(tool_id)
            else:
                return {"status": "error", "message": f"Tool {tool_id} not found"}
                
            return {
                "status": "success",
                "message": "Tool deleted successfully",
                "tool_id": tool_id,
                "tool": tool
            }
            
        except Exception as e:
            logger.error(f"Error deleting tool: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def invoke_tool(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Invoke a tool.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Tools service is not initialized"}
                
            # Check if tools are enabled
            if not self.tools_enabled:
                return {"status": "error", "message": "Tools are disabled"}
                
            # Get tool parameters
            tool_id = data.get("tool_id") if data else None
            name = data.get("name") if data else None
            parameters = data.get("parameters", {}) if data else {}
            
            # Validate parameters
            if not tool_id and not name:
                return {"status": "error", "message": "Tool ID or name is required"}
                
            # Get tool
            tool = None
            if tool_id:
                if tool_id in self.tools:
                    tool = self.tools[tool_id]
                elif tool_id in self.active_tools:
                    tool = self.active_tools[tool_id]
            elif name:
                # Search for tool by name
                for t in self.tools.values():
                    if t["name"] == name:
                        tool = t
                        break
                if not tool:
                    for t in self.active_tools.values():
                        if t["name"] == name:
                            tool = t
                            break
                            
            if not tool:
                return {"status": "error", "message": "Tool not found"}
                
            # Create tool execution
            execution_id = str(uuid.uuid4())
            execution = {
                "execution_id": execution_id,
                "tool_id": tool["tool_id"],
                "tool_name": tool["name"],
                "parameters": parameters,
                "status": "queued",
                "created_at": datetime.now().isoformat(),
                "context": context or {}
            }
            
            # Add execution to tool executions
            self.tool_executions.append(execution)
            
            # Execute tool
            result = await self._execute_tool(tool, execution, context)
            
            # Update execution
            execution["status"] = "completed"
            execution["completed_at"] = datetime.now().isoformat()
            execution["result"] = result
            
            return {
                "status": "success",
                "message": "Tool invoked successfully",
                "execution_id": execution_id,
                "tool_id": tool["tool_id"],
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error invoking tool: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _execute_tool(self, tool: Dict[str, Any], execution: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a tool."""
        # In a real implementation, this would execute the tool
        logger.info(f"Executing tool {tool['tool_id']} with name: {tool['name']}")
        
        # Get tool details
        tool_id = tool["tool_id"]
        tool_name = tool["name"]
        tool_type = tool["tool_type"]
        parameters = execution["parameters"]
        
        # Simulate tool execution
        await asyncio.sleep(1)
        
        # Return tool result
        result = {
            "tool_id": tool_id,
            "tool_name": tool_name,
            "tool_type": tool_type,
            "parameters": parameters,
            "status": "success",
            "output": f"Output for tool {tool_name} with parameters {parameters}",
            "execution_time": 1.0
        }
        
        return result
    
    async def list_tools(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        List tools.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Tools service is not initialized"}
                
            # Get list parameters
            status = data.get("status") if data else None
            tool_type = data.get("tool_type") if data else None
            limit = data.get("limit", 100) if data else 100
            offset = data.get("offset", 0) if data else 0
            
            # Get all tools
            all_tools = list(self.tools.values()) + list(self.active_tools.values())
                
            # Filter tools based on parameters
            filtered_tools = []
            for tool in all_tools:
                if status and tool["status"] != status:
                    continue
                if tool_type and tool["tool_type"] != tool_type:
                    continue
                filtered_tools.append(tool)
                
            # Sort tools by creation time (newest first)
            filtered_tools.sort(key=lambda x: x["created_at"], reverse=True)
                
            # Apply pagination
            paginated_tools = filtered_tools[offset:offset+limit]
            
            return {
                "status": "success",
                "message": "Tools listed successfully",
                "total_count": len(filtered_tools),
                "limit": limit,
                "offset": offset,
                "tools": paginated_tools
            }
            
        except Exception as e:
            logger.error(f"Error listing tools: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def search_tools(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search tools.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Tools service is not initialized"}
                
            # Get search parameters
            query = data.get("query") if data else None
            tool_type = data.get("tool_type") if data else None
            status = data.get("status") if data else None
            start_time = data.get("start_time") if data else None
            end_time = data.get("end_time") if data else None
            limit = data.get("limit", 100) if data else 100
            offset = data.get("offset", 0) if data else 0
            
            if not query:
                return {"status": "error", "message": "Query is required for search"}
                
            # Get all tools
            all_tools = list(self.tools.values()) + list(self.active_tools.values())
                
            # Search tools based on query
            matched_tools = []
            for tool in all_tools:
                # Check if tool matches query
                tool_json = json.dumps(tool, default=str)
                if query.lower() in tool_json.lower():
                    # Check additional filters
                    if tool_type and tool["tool_type"] != tool_type:
                        continue
                    if status and tool["status"] != status:
                        continue
                    if start_time and tool["created_at"] < start_time:
                        continue
                    if end_time and tool["created_at"] > end_time:
                        continue
                    matched_tools.append(tool)
                    
            # Sort tools by creation time (newest first)
            matched_tools.sort(key=lambda x: x["created_at"], reverse=True)
                
            # Apply pagination
            paginated_tools = matched_tools[offset:offset+limit]
            
            return {
                "status": "success",
                "message": "Tools searched successfully",
                "query": query,
                "total_count": len(matched_tools),
                "limit": limit,
                "offset": offset,
                "tools": paginated_tools
            }
            
        except Exception as e:
            logger.error(f"Error searching tools: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def validate_tool(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate a tool.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Tools service is not initialized"}
                
            # Get validation parameters
            tool_id = data.get("tool_id") if data else None
            name = data.get("name") if data else None
            code = data.get("code") if data else None
            
            # If tool_id or name is provided, validate the specific tool
            if tool_id or name:
                # Get tool
                tool = None
                if tool_id:
                    if tool_id in self.tools:
                        tool = self.tools[tool_id]
                    elif tool_id in self.active_tools:
                        tool = self.active_tools[tool_id]
                elif name:
                    # Search for tool by name
                    for t in self.tools.values():
                        if t["name"] == name:
                            tool = t
                            break
                    if not tool:
                        for t in self.active_tools.values():
                            if t["name"] == name:
                                tool = t
                                break
                                
                if not tool:
                    return {"status": "error", "message": "Tool not found"}
                        
                # Validate tool
                validation_result = await self._validate_tool(tool, context)
                
                return {
                    "status": "success",
                    "message": "Tool validated successfully",
                    "tool_id": tool["tool_id"],
                    "validation_result": validation_result
                }
            else:
                # If tool_id and name are not provided, validate tool code
                if not code:
                    return {"status": "error", "message": "Tool code is required for validation"}
                    
                # Create a temporary tool for validation
                tool = {
                    "tool_id": str(uuid.uuid4()),
                    "name": "Temporary Tool",
                    "description": "Temporary tool for validation",
                    "tool_type": "validation",
                    "parameters": [],
                    "code": code,
                    "status": "validation",
                    "created_at": datetime.now().isoformat(),
                    "context": context or {}
                }
                
                # Validate tool
                validation_result = await self._validate_tool(tool, context)
                
                return {
                    "status": "success",
                    "message": "Tool validated successfully",
                    "validation_result": validation_result
                }
                
        except Exception as e:
            logger.error(f"Error validating tool: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _validate_tool(self, tool: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate a tool."""
        # In a real implementation, this would validate the tool
        logger.info(f"Validating tool {tool['tool_id']} with name: {tool['name']}")
        
        # Get tool details
        tool_id = tool["tool_id"]
        tool_name = tool["name"]
        tool_type = tool["tool_type"]
        code = tool["code"]
        
        # Simulate validation
        await asyncio.sleep(0.5)
        
        # Return validation result
        validation_result = {
            "tool_id": tool_id,
            "tool_name": tool_name,
            "tool_type": tool_type,
            "is_valid": True,
            "validation_issues": [],
            "validation_steps": [
                {
                    "step": 1,
                    "description": "Validated tool structure",
                    "result": "Tool structure is valid"
                },
                {
                    "step": 2,
                    "description": "Validated tool code",
                    "result": "Tool code is valid"
                },
                {
                    "step": 3,
                    "description": "Validated tool parameters",
                    "result": "Tool parameters are valid"
                }
            ]
        }
        
        return validation_result
        
    async def get_status(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get the status of the tools service.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the status information
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Tools service is not initialized"}
                
            status = {
                "tools_enabled": self.tools_enabled,
                "is_running": self._is_running,
                "tools_count": len(self.tools),
                "active_tools_count": len(self.active_tools),
                "tool_executions_count": len(self.tool_executions),
                "max_tools": self.max_tools,
                "tool_timeout": self.tool_timeout
            }
            
            return {
                "status": "success",
                "message": "Tools status retrieved successfully",
                "tools_status": status
            }
            
        except Exception as e:
            logger.error(f"Error getting tools status: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_stats(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get statistics for the tools service.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the statistics
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Tools service is not initialized"}
                
            # Get all tools
            all_tools = list(self.tools.values()) + list(self.active_tools.values())
                
            # Count by status
            status_counts = {}
            for tool in all_tools:
                status = tool["status"]
                if status not in status_counts:
                    status_counts[status] = 0
                status_counts[status] += 1
                
            # Count by tool type
            type_counts = {}
            for tool in all_tools:
                tool_type = tool["tool_type"]
                if tool_type not in type_counts:
                    type_counts[tool_type] = 0
                type_counts[tool_type] += 1
                
            # Calculate average execution time for completed tool executions
            completed_executions = [e for e in self.tool_executions if e["status"] == "completed"]
            total_execution_time = 0
            for execution in completed_executions:
                if "started_at" in execution and "completed_at" in execution:
                    start_time = datetime.fromisoformat(execution["started_at"])
                    end_time = datetime.fromisoformat(execution["completed_at"])
                    execution_time = (end_time - start_time).total_seconds()
                    total_execution_time += execution_time
                    
            average_execution_time = total_execution_time / len(completed_executions) if completed_executions else 0
            
            stats = {
                "tools_enabled": self.tools_enabled,
                "is_running": self._is_running,
                "total_tools": len(all_tools),
                "tools_count": len(self.tools),
                "active_tools_count": len(self.active_tools),
                "tool_executions_count": len(self.tool_executions),
                "completed_executions_count": len(completed_executions),
                "max_tools": self.max_tools,
                "tool_timeout": self.tool_timeout,
                "status_counts": status_counts,
                "type_counts": type_counts,
                "average_execution_time": average_execution_time
            }
            
            return {
                "status": "success",
                "message": "Tools statistics retrieved successfully",
                "tools_stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error getting tools statistics: {str(e)}")
            return {"status": "error", "message": str(e)}