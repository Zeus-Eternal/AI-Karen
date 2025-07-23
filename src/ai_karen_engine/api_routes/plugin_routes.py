"""
FastAPI routes for Plugin service integration.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..services.plugin_service import PluginService
# Note: PluginInfo, PluginExecutionRequest, PluginExecutionResult, PluginStatus 
# classes need to be implemented in the plugin service
from ..core.dependencies import get_plugin_service
# Temporarily disable auth imports for web UI integration

router = APIRouter(prefix="/api/plugins", tags=["plugins"])


# Request/Response Models
class ExecutePluginRequest(BaseModel):
    """Request model for plugin execution."""
    plugin_name: str = Field(..., description="Name of plugin to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Plugin parameters")
    timeout: int = Field(30, ge=1, le=300, description="Execution timeout in seconds")
    session_id: Optional[str] = Field(None, description="Session ID")


class ValidatePluginRequest(BaseModel):
    """Request model for plugin validation."""
    plugin_name: str = Field(..., description="Name of plugin to validate")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Plugin parameters to validate")


class PluginInfoResponse(BaseModel):
    """Response model for plugin information."""
    name: str
    description: str
    version: str
    category: str
    status: str
    parameters: Dict[str, Any]
    author: str
    enabled: bool
    tags: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    last_executed: Optional[str] = None
    execution_count: int = 0
    success_rate: float = 0.0


class PluginExecutionResponse(BaseModel):
    """Response model for plugin execution."""
    success: bool
    result: Optional[Any] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    error: Optional[str] = None
    execution_time: float
    timestamp: str
    plugin_name: str
    session_id: Optional[str] = None


class PluginListResponse(BaseModel):
    """Response model for plugin list."""
    plugins: List[PluginInfoResponse]
    total_count: int
    enabled_count: int
    disabled_count: int


class PluginMetricsResponse(BaseModel):
    """Response model for plugin metrics."""
    total_plugins: int
    enabled_plugins: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_execution_time: float
    plugins_by_category: Dict[str, int]
    most_used_plugins: List[Dict[str, Any]]
    recent_executions: List[Dict[str, Any]]


@router.get("/", response_model=PluginListResponse)
async def list_plugins(
    category: Optional[str] = Query(None, description="Filter by category"),
    enabled_only: bool = Query(False, description="Only return enabled plugins"),
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """List all available plugins."""
    try:
        plugins = await plugin_service.list_plugins()
        
        # Apply filters
        if category:
            plugins = [p for p in plugins if p.category.lower() == category.lower()]
        
        if enabled_only:
            plugins = [p for p in plugins if p.enabled]
        
        # Convert to response format
        plugin_responses = []
        for plugin in plugins:
            plugin_responses.append(PluginInfoResponse(
                name=plugin.name,
                description=plugin.description,
                version=plugin.version,
                category=plugin.category,
                status=plugin.status.value,
                parameters=plugin.parameters,
                author=plugin.author,
                enabled=plugin.enabled,
                tags=getattr(plugin, 'tags', []),
                dependencies=getattr(plugin, 'dependencies', []),
                last_executed=getattr(plugin, 'last_executed', None),
                execution_count=getattr(plugin, 'execution_count', 0),
                success_rate=getattr(plugin, 'success_rate', 0.0)
            ))
        
        enabled_count = sum(1 for p in plugin_responses if p.enabled)
        disabled_count = len(plugin_responses) - enabled_count
        
        return PluginListResponse(
            plugins=plugin_responses,
            total_count=len(plugin_responses),
            enabled_count=enabled_count,
            disabled_count=disabled_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list plugins: {str(e)}")


@router.get("/{plugin_name}", response_model=PluginInfoResponse)
async def get_plugin_info(
    plugin_name: str,
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """Get detailed information about a specific plugin."""
    try:
        plugin = await plugin_service.get_plugin_info(plugin_name)
        
        if not plugin:
            raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} not found")
        
        return PluginInfoResponse(
            name=plugin.name,
            description=plugin.description,
            version=plugin.version,
            category=plugin.category,
            status=plugin.status.value,
            parameters=plugin.parameters,
            author=plugin.author,
            enabled=plugin.enabled,
            tags=getattr(plugin, 'tags', []),
            dependencies=getattr(plugin, 'dependencies', []),
            last_executed=getattr(plugin, 'last_executed', None),
            execution_count=getattr(plugin, 'execution_count', 0),
            success_rate=getattr(plugin, 'success_rate', 0.0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plugin info: {str(e)}")


@router.post("/{plugin_name}/execute", response_model=PluginExecutionResponse)
async def execute_plugin(
    plugin_name: str,
    request: ExecutePluginRequest,
    
    
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """Execute a plugin with given parameters."""
    try:
        # Create execution request
        execution_request = PluginExecutionRequest(
            plugin_name=plugin_name,
            parameters=request.parameters,
            user_id="anonymous",
            session_id=request.session_id,
            timeout=request.timeout
        )
        
        # Execute the plugin
        result = await plugin_service.execute_plugin(execution_request)
        
        return PluginExecutionResponse(
            success=result.success,
            result=result.result,
            stdout=result.stdout,
            stderr=result.stderr,
            error=result.error,
            execution_time=result.execution_time,
            timestamp=result.timestamp.isoformat(),
            plugin_name=plugin_name,
            session_id=request.session_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute plugin: {str(e)}")


@router.post("/{plugin_name}/validate")
async def validate_plugin_parameters(
    plugin_name: str,
    request: ValidatePluginRequest,
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """Validate plugin parameters."""
    try:
        is_valid = await plugin_service.validate_plugin(plugin_name, request.parameters)
        
        return {
            "valid": is_valid,
            "plugin_name": plugin_name,
            "message": "Parameters are valid" if is_valid else "Parameters are invalid"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate plugin: {str(e)}")


@router.post("/{plugin_name}/enable")
async def enable_plugin(
    plugin_name: str,
    
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """Enable a plugin."""
    try:
        # Check if user has admin privileges
        if "admin" not in current_user.get("roles", []):
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        success = await plugin_service.enable_plugin(plugin_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} not found")
        
        return {
            "success": True,
            "message": f"Plugin {plugin_name} enabled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enable plugin: {str(e)}")


@router.post("/{plugin_name}/disable")
async def disable_plugin(
    plugin_name: str,
    
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """Disable a plugin."""
    try:
        # Check if user has admin privileges
        if "admin" not in current_user.get("roles", []):
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        success = await plugin_service.disable_plugin(plugin_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} not found")
        
        return {
            "success": True,
            "message": f"Plugin {plugin_name} disabled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disable plugin: {str(e)}")


@router.get("/categories")
async def get_plugin_categories(
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """Get list of plugin categories."""
    try:
        plugins = await plugin_service.list_plugins()
        categories = list(set(plugin.category for plugin in plugins))
        categories.sort()
        
        category_counts = {}
        for plugin in plugins:
            category_counts[plugin.category] = category_counts.get(plugin.category, 0) + 1
        
        return {
            "categories": categories,
            "category_counts": category_counts,
            "total_categories": len(categories)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


@router.get("/metrics", response_model=PluginMetricsResponse)
async def get_plugin_metrics(
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """Get plugin execution metrics."""
    try:
        metrics = plugin_service.get_metrics()
        
        return PluginMetricsResponse(
            total_plugins=metrics.get("total_plugins", 0),
            enabled_plugins=metrics.get("enabled_plugins", 0),
            total_executions=metrics.get("total_executions", 0),
            successful_executions=metrics.get("successful_executions", 0),
            failed_executions=metrics.get("failed_executions", 0),
            average_execution_time=metrics.get("average_execution_time", 0.0),
            plugins_by_category=metrics.get("plugins_by_category", {}),
            most_used_plugins=metrics.get("most_used_plugins", []),
            recent_executions=metrics.get("recent_executions", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.post("/reload")
async def reload_plugins(
    
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """Reload all plugins from disk."""
    try:
        # Check if user has admin privileges
        if "admin" not in current_user.get("roles", []):
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        count = await plugin_service.reload_plugins()
        
        return {
            "success": True,
            "message": f"Reloaded {count} plugins successfully",
            "plugins_loaded": count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload plugins: {str(e)}")


@router.get("/health")
async def health_check(
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """Health check for plugin service."""
    try:
        if hasattr(plugin_service, 'health_check'):
            health_result = await plugin_service.health_check()
            return health_result
        else:
            return {
                "status": "healthy",
                "service": "plugin_service",
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "plugin_service",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }