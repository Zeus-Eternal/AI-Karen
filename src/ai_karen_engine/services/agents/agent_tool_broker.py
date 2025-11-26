"""
Agent Tool Broker Service

This service manages the tools available to agents, including tool discovery,
execution, and result handling.
"""

from typing import Dict, List, Any, Optional, Union, Callable
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """Enumeration of tool statuses."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEPRECATED = "deprecated"
    MAINTENANCE = "maintenance"


@dataclass
class ToolParameter:
    """Represents a parameter for a tool."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ToolDefinition:
    """Represents a tool definition."""
    id: str
    name: str
    description: str
    parameters: List[ToolParameter]
    return_type: str
    status: ToolStatus
    execution_path: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ToolExecutionRequest:
    """Represents a request to execute a tool."""
    tool_id: str
    agent_id: str
    parameters: Dict[str, Any]
    execution_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ToolExecutionResult:
    """Represents the result of a tool execution."""
    execution_id: str
    tool_id: str
    agent_id: str
    success: bool
    output_data: Any
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentToolBroker:
    """
    Manages tools available to agents.
    
    This class is responsible for:
    - Registering and managing tools
    - Executing tools on behalf of agents
    - Handling tool execution results
    - Providing tool discovery and metadata
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._tool_executors: Dict[str, Callable] = {}
        self._execution_results: Dict[str, ToolExecutionResult] = {}
        
        # Callbacks for execution events
        self._on_execution_start: Optional[Callable[[ToolExecutionRequest], None]] = None
        self._on_execution_complete: Optional[Callable[[ToolExecutionResult], None]] = None
        self._on_execution_error: Optional[Callable[[ToolExecutionResult], None]] = None
    
    def register_tool(self, tool_def: ToolDefinition, executor: Callable) -> None:
        """
        Register a tool with the broker.
        
        Args:
            tool_def: Definition of the tool
            executor: Function that executes the tool
        """
        self._tools[tool_def.id] = tool_def
        self._tool_executors[tool_def.id] = executor
        logger.info(f"Registered tool: {tool_def.id} ({tool_def.name})")
    
    def unregister_tool(self, tool_id: str) -> bool:
        """
        Unregister a tool from the broker.
        
        Args:
            tool_id: ID of the tool to unregister
            
        Returns:
            True if tool was unregistered, False if not found
        """
        if tool_id in self._tools:
            del self._tools[tool_id]
            del self._tool_executors[tool_id]
            logger.info(f"Unregistered tool: {tool_id}")
            return True
        else:
            logger.warning(f"Attempted to unregister non-existent tool: {tool_id}")
            return False
    
    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        """Get a tool definition by ID."""
        return self._tools.get(tool_id)
    
    def get_all_tools(self) -> Dict[str, ToolDefinition]:
        """Get all tool definitions."""
        return self._tools.copy()
    
    def get_tools_by_status(self, status: ToolStatus) -> List[ToolDefinition]:
        """Get all tools with a specific status."""
        return [tool for tool in self._tools.values() if tool.status == status]
    
    def get_available_tools(self) -> List[ToolDefinition]:
        """Get all available tools."""
        return self.get_tools_by_status(ToolStatus.AVAILABLE)
    
    def search_tools(self, query: str) -> List[ToolDefinition]:
        """
        Search for tools by name or description.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching tools
        """
        query_lower = query.lower()
        matching_tools = []
        
        for tool in self._tools.values():
            if (query_lower in tool.name.lower() or
                query_lower in tool.description.lower()):
                matching_tools.append(tool)
        
        return matching_tools
    
    def update_tool_status(self, tool_id: str, status: ToolStatus) -> bool:
        """
        Update the status of a tool.
        
        Args:
            tool_id: ID of the tool to update
            status: New status for the tool
            
        Returns:
            True if tool status was updated, False if tool not found
        """
        tool = self._tools.get(tool_id)
        if tool:
            tool.status = status
            logger.info(f"Updated tool {tool_id} status to {status.value}")
            return True
        else:
            logger.warning(f"Attempted to update status of non-existent tool: {tool_id}")
            return False
    
    def validate_tool_parameters(self, tool_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parameters for a tool.
        
        Args:
            tool_id: ID of the tool
            parameters: Parameters to validate
            
        Returns:
            Dictionary of validation results
        """
        tool = self._tools.get(tool_id)
        if not tool:
            return {"valid": False, "error": f"Tool not found: {tool_id}"}
        
        if tool.status != ToolStatus.AVAILABLE:
            return {"valid": False, "error": f"Tool not available: {tool_id}"}
        
        errors = []
        validated_params = {}
        
        # Check required parameters
        for param in tool.parameters:
            if param.required and param.name not in parameters:
                errors.append(f"Missing required parameter: {param.name}")
            elif param.name in parameters:
                # Type validation would go here in a real implementation
                validated_params[param.name] = parameters[param.name]
            elif param.default is not None:
                validated_params[param.name] = param.default
        
        # Check for extra parameters
        for param_name in parameters:
            if param_name not in [p.name for p in tool.parameters]:
                errors.append(f"Unknown parameter: {param_name}")
        
        if errors:
            return {"valid": False, "errors": errors}
        else:
            return {"valid": True, "parameters": validated_params}
    
    def execute_tool(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """
        Execute a tool.
        
        Args:
            request: Tool execution request
            
        Returns:
            Execution result
        """
        import time
        start_time = time.time()
        
        # Generate execution ID if not provided
        if not request.execution_id:
            request.execution_id = f"{request.tool_id}_{request.agent_id}_{int(time.time() * 1000)}"
        
        # Call start callback if set
        if self._on_execution_start:
            self._on_execution_start(request)
        
        # Get tool definition
        tool = self._tools.get(request.tool_id)
        if not tool:
            result = ToolExecutionResult(
                execution_id=request.execution_id,
                tool_id=request.tool_id,
                agent_id=request.agent_id,
                success=False,
                output_data=None,
                error_message=f"Tool not found: {request.tool_id}",
                execution_time=time.time() - start_time,
                metadata=request.metadata
            )
            
            # Call error callback if set
            if self._on_execution_error:
                self._on_execution_error(result)
            
            return result
        
        # Check tool status
        if tool.status != ToolStatus.AVAILABLE:
            result = ToolExecutionResult(
                execution_id=request.execution_id,
                tool_id=request.tool_id,
                agent_id=request.agent_id,
                success=False,
                output_data=None,
                error_message=f"Tool not available: {request.tool_id}",
                execution_time=time.time() - start_time,
                metadata=request.metadata
            )
            
            # Call error callback if set
            if self._on_execution_error:
                self._on_execution_error(result)
            
            return result
        
        # Validate parameters
        validation = self.validate_tool_parameters(request.tool_id, request.parameters)
        if not validation["valid"]:
            result = ToolExecutionResult(
                execution_id=request.execution_id,
                tool_id=request.tool_id,
                agent_id=request.agent_id,
                success=False,
                output_data=None,
                error_message="; ".join(validation.get("errors", validation.get("error", "Invalid parameters"))),
                execution_time=time.time() - start_time,
                metadata=request.metadata
            )
            
            # Call error callback if set
            if self._on_execution_error:
                self._on_execution_error(result)
            
            return result
        
        # Get executor
        executor = self._tool_executors.get(request.tool_id)
        if not executor:
            result = ToolExecutionResult(
                execution_id=request.execution_id,
                tool_id=request.tool_id,
                agent_id=request.agent_id,
                success=False,
                output_data=None,
                error_message=f"Executor not found for tool: {request.tool_id}",
                execution_time=time.time() - start_time,
                metadata=request.metadata
            )
            
            # Call error callback if set
            if self._on_execution_error:
                self._on_execution_error(result)
            
            return result
        
        # Execute tool
        try:
            output_data = executor(validation["parameters"])
            
            execution_time = time.time() - start_time
            
            result = ToolExecutionResult(
                execution_id=request.execution_id,
                tool_id=request.tool_id,
                agent_id=request.agent_id,
                success=True,
                output_data=output_data,
                execution_time=execution_time,
                metadata=request.metadata
            )
            
            # Store result
            self._execution_results[request.execution_id] = result
            
            # Call completion callback if set
            if self._on_execution_complete:
                self._on_execution_complete(result)
            
            logger.info(f"Tool {request.tool_id} executed successfully for agent {request.agent_id}")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            result = ToolExecutionResult(
                execution_id=request.execution_id,
                tool_id=request.tool_id,
                agent_id=request.agent_id,
                success=False,
                output_data=None,
                error_message=str(e),
                execution_time=execution_time,
                metadata=request.metadata
            )
            
            # Store result
            self._execution_results[request.execution_id] = result
            
            # Call error callback if set
            if self._on_execution_error:
                self._on_execution_error(result)
            
            logger.error(f"Tool {request.tool_id} execution failed for agent {request.agent_id}: {str(e)}")
            return result
    
    def get_execution_result(self, execution_id: str) -> Optional[ToolExecutionResult]:
        """Get a tool execution result by ID."""
        return self._execution_results.get(execution_id)
    
    def get_execution_results_for_agent(self, agent_id: str) -> List[ToolExecutionResult]:
        """Get all tool execution results for an agent."""
        return [result for result in self._execution_results.values() if result.agent_id == agent_id]
    
    def get_execution_results_for_tool(self, tool_id: str) -> List[ToolExecutionResult]:
        """Get all tool execution results for a tool."""
        return [result for result in self._execution_results.values() if result.tool_id == tool_id]
    
    def clear_execution_results(self) -> None:
        """Clear all tool execution results."""
        self._execution_results.clear()
        logger.info("Cleared all tool execution results")
    
    def set_execution_callbacks(
        self,
        on_start: Optional[Callable[[ToolExecutionRequest], None]] = None,
        on_complete: Optional[Callable[[ToolExecutionResult], None]] = None,
        on_error: Optional[Callable[[ToolExecutionResult], None]] = None
    ) -> None:
        """Set callbacks for execution events."""
        self._on_execution_start = on_start
        self._on_execution_complete = on_complete
        self._on_execution_error = on_error
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about tools and executions.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_tools": len(self._tools),
            "tools_by_status": {},
            "total_executions": len(self._execution_results),
            "successful_executions": sum(1 for r in self._execution_results.values() if r.success),
            "failed_executions": sum(1 for r in self._execution_results.values() if not r.success),
            "average_execution_time": 0.0
        }
        
        # Count tools by status
        for status in ToolStatus:
            stats["tools_by_status"][status.value] = len(self.get_tools_by_status(status))
        
        # Calculate average execution time
        successful_results = [r for r in self._execution_results.values() if r.success and r.execution_time]
        if successful_results:
            stats["average_execution_time"] = sum(r.execution_time for r in successful_results if r.execution_time is not None) / len(successful_results)
        
        return stats