"""
FastAPI routes for Tool service integration.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

try:
    from fastapi import APIRouter, HTTPException, Depends, Query
except ImportError as e:  # pragma: no cover - runtime dependency
    raise ImportError(
        "FastAPI is required for tool routes. Install via `pip install fastapi`."
    ) from e

try:
    from pydantic import BaseModel, Field
except ImportError as e:  # pragma: no cover - runtime dependency
    raise ImportError(
        "Pydantic is required for tool routes. Install via `pip install pydantic`."
    ) from e

from ai_karen_engine.services.tool_service import (
    ToolService,
    ToolInput,
    ToolOutput,
    BaseTool
)
from ai_karen_engine.core.dependencies import get_tool_service
# Temporarily disable auth imports for web UI integration

router = APIRouter(prefix="/api/tools", tags=["tools"])


# Request/Response Models
class ExecuteToolRequest(BaseModel):
    """Request model for tool execution."""
    tool_name: str = Field(..., description="Name of tool to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    user_context: Optional[Dict[str, Any]] = Field(None, description="User context data")


class ToolInfoResponse(BaseModel):
    """Response model for tool information."""
    name: str
    description: str
    category: str
    parameters: Dict[str, Any]
    return_type: str
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    version: str = "1.0.0"
    author: str = "AI Karen"
    enabled: bool = True


class ToolExecutionResponse(BaseModel):
    """Response model for tool execution."""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float
    metadata: Optional[Dict[str, Any]] = None
    tool_name: str
    timestamp: str


class ToolListResponse(BaseModel):
    """Response model for tool list."""
    tools: List[ToolInfoResponse]
    total_count: int
    categories: List[str]


class ToolSchemaResponse(BaseModel):
    """Response model for tool schema."""
    tool_name: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    description: str
    examples: List[Dict[str, Any]]


class ToolMetricsResponse(BaseModel):
    """Response model for tool metrics."""
    total_tools: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_execution_time: float
    tools_by_category: Dict[str, int]
    most_used_tools: List[Dict[str, Any]]
    recent_executions: List[Dict[str, Any]]


@router.get("/", response_model=ToolListResponse)
async def list_tools(
    category: Optional[str] = Query(None, description="Filter by category"),
    tool_service: ToolService = Depends(get_tool_service)
):
    """List all available tools."""
    try:
        tool_names = tool_service.list_tools()
        tools = []
        categories = set()
        
        for tool_name in tool_names:
            tool_info = await _get_tool_info(tool_service, tool_name)
            if tool_info:
                if not category or tool_info.category.lower() == category.lower():
                    tools.append(tool_info)
                categories.add(tool_info.category)
        
        return ToolListResponse(
            tools=tools,
            total_count=len(tools),
            categories=sorted(list(categories))
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")


@router.get("/{tool_name}", response_model=ToolInfoResponse)
async def get_tool_info(
    tool_name: str,
    tool_service: ToolService = Depends(get_tool_service)
):
    """Get detailed information about a specific tool."""
    try:
        tool_info = await _get_tool_info(tool_service, tool_name)
        
        if not tool_info:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
        
        return tool_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tool info: {str(e)}")


@router.post("/{tool_name}/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    tool_name: str,
    request: ExecuteToolRequest,
    
    
    tool_service: ToolService = Depends(get_tool_service)
):
    """Execute a tool with given parameters."""
    try:
        # Add user context
        user_context = request.user_context or {}
        user_context.update({
            "user_id": current_user["user_id"],
            "tenant_id": tenant_id,
            "roles": current_user.get("roles", [])
        })
        
        # Create tool input
        tool_input = ToolInput(
            tool_name=tool_name,
            parameters=request.parameters,
            user_context=user_context
        )
        
        # Execute the tool
        start_time = datetime.utcnow()
        result = await tool_service.execute_tool(tool_input)
        
        return ToolExecutionResponse(
            success=result.success,
            result=result.result,
            error=result.error,
            execution_time=result.execution_time,
            metadata=result.metadata,
            tool_name=tool_name,
            timestamp=start_time.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute tool: {str(e)}")


@router.get("/{tool_name}/schema", response_model=ToolSchemaResponse)
async def get_tool_schema(
    tool_name: str,
    tool_service: ToolService = Depends(get_tool_service)
):
    """Get input/output schema for a tool."""
    try:
        if tool_name not in tool_service.list_tools():
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
        
        # Get tool instance to extract schema information
        tool_instance = tool_service.tools.get(tool_name)
        if not tool_instance:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not available")
        
        # Extract schema information
        input_schema = _get_tool_input_schema(tool_instance)
        output_schema = _get_tool_output_schema(tool_instance)
        description = getattr(tool_instance, '__doc__', f"Tool: {tool_name}")
        examples = _get_tool_examples(tool_instance)
        
        return ToolSchemaResponse(
            tool_name=tool_name,
            input_schema=input_schema,
            output_schema=output_schema,
            description=description,
            examples=examples
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tool schema: {str(e)}")


@router.get("/categories")
async def get_tool_categories(
    tool_service: ToolService = Depends(get_tool_service)
):
    """Get list of tool categories."""
    try:
        tool_names = tool_service.list_tools()
        categories = {}
        
        for tool_name in tool_names:
            tool_info = await _get_tool_info(tool_service, tool_name)
            if tool_info:
                category = tool_info.category
                categories[category] = categories.get(category, 0) + 1
        
        return {
            "categories": list(categories.keys()),
            "category_counts": categories,
            "total_categories": len(categories)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


@router.get("/metrics", response_model=ToolMetricsResponse)
async def get_tool_metrics(
    tool_service: ToolService = Depends(get_tool_service)
):
    """Get tool execution metrics."""
    try:
        metrics = tool_service.get_metrics()
        
        return ToolMetricsResponse(
            total_tools=metrics.get("total_tools", 0),
            total_executions=metrics.get("total_executions", 0),
            successful_executions=metrics.get("successful_executions", 0),
            failed_executions=metrics.get("failed_executions", 0),
            average_execution_time=metrics.get("average_execution_time", 0.0),
            tools_by_category=metrics.get("tools_by_category", {}),
            most_used_tools=metrics.get("most_used_tools", []),
            recent_executions=metrics.get("recent_executions", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.post("/register")
async def register_tool(
    tool_name: str,
    tool_class: str,
    
    tool_service: ToolService = Depends(get_tool_service)
):
    """Register a new tool (admin only)."""
    try:
        # Check if user has admin privileges
        if "admin" not in current_user.get("roles", []):
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        # This would require dynamic class loading
        # For now, return a placeholder response
        return {
            "success": False,
            "message": "Dynamic tool registration not yet implemented",
            "tool_name": tool_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register tool: {str(e)}")


@router.get("/health")
async def health_check(
    tool_service: ToolService = Depends(get_tool_service)
):
    """Health check for tool service."""
    try:
        if hasattr(tool_service, 'health_check'):
            health_result = await tool_service.health_check()
            return health_result
        else:
            return {
                "status": "healthy",
                "service": "tool_service",
                "timestamp": datetime.utcnow().isoformat(),
                "tools_available": len(tool_service.list_tools())
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "tool_service",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


# Helper functions
async def _get_tool_info(tool_service: ToolService, tool_name: str) -> Optional[ToolInfoResponse]:
    """Get tool information."""
    try:
        if tool_name not in tool_service.list_tools():
            return None
        
        tool_instance = tool_service.tools.get(tool_name)
        if not tool_instance:
            return None
        
        # Extract tool information
        description = getattr(tool_instance, '__doc__', f"Tool: {tool_name}")
        category = getattr(tool_instance, 'category', 'general')
        parameters = _get_tool_input_schema(tool_instance)
        return_type = _get_tool_return_type(tool_instance)
        examples = _get_tool_examples(tool_instance)
        tags = getattr(tool_instance, 'tags', [])
        version = getattr(tool_instance, 'version', '1.0.0')
        author = getattr(tool_instance, 'author', 'AI Karen')
        
        return ToolInfoResponse(
            name=tool_name,
            description=description,
            category=category,
            parameters=parameters,
            return_type=return_type,
            examples=examples,
            tags=tags,
            version=version,
            author=author,
            enabled=True
        )
        
    except Exception:
        return None


def _get_tool_input_schema(tool_instance: BaseTool) -> Dict[str, Any]:
    """Extract input schema from tool instance."""
    # This would analyze the tool's execute method signature
    # For now, return a basic schema
    return {
        "type": "object",
        "properties": {
            "parameters": {
                "type": "object",
                "description": "Tool-specific parameters"
            }
        },
        "required": ["parameters"]
    }


def _get_tool_output_schema(tool_instance: BaseTool) -> Dict[str, Any]:
    """Extract output schema from tool instance."""
    return {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "result": {"type": "any"},
            "error": {"type": "string", "nullable": True}
        },
        "required": ["success", "result"]
    }


def _get_tool_return_type(tool_instance: BaseTool) -> str:
    """Get tool return type."""
    return getattr(tool_instance, 'return_type', 'any')


def _get_tool_examples(tool_instance: BaseTool) -> List[Dict[str, Any]]:
    """Get tool usage examples."""
    return getattr(tool_instance, 'examples', [])