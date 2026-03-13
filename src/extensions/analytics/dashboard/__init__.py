"""
Analytics Dashboard Extension - Migrated from ui_logic/pages/analytics.py

This extension provides comprehensive analytics and data visualization capabilities,
including the auto-parser, chart builder, and data explorer components.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.hooks.hook_mixin import HookMixin

# Import the original analytics components
from ui_logic.components.analytics.auto_parser import render_auto_parser, AutoParserError
from ui_logic.components.analytics.chart_builder import render_chart_builder, ChartBuilderError
from ui_logic.components.analytics.data_explorer import render_data_explorer

logger = logging.getLogger(__name__)


class AnalyticsRequest(BaseModel):
    """Request model for analytics operations."""
    data: Any
    chart_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    query: Optional[str] = None
    mode: Optional[str] = "summary"


class AnalyticsDashboardExtension(BaseExtension, HookMixin):
    """Enhanced Analytics Dashboard Extension with migrated UI logic components."""
    
    async def _initialize(self) -> None:
        """Initialize the Analytics Dashboard Extension."""
        self.logger.info("Analytics Dashboard Extension initializing...")
        
        # Initialize analytics data storage
        self.parsed_datasets: Dict[str, Any] = {}
        self.chart_cache: Dict[str, Any] = {}
        self.exploration_history: List[Dict[str, Any]] = []
        
        # Set up MCP tools for AI integration
        await self._setup_mcp_tools()
        
        self.logger.info("Analytics Dashboard Extension initialized successfully")
    
    async def _setup_mcp_tools(self) -> None:
        """Set up MCP tools for AI-powered analytics."""
        mcp_server = self.create_mcp_server()
        if mcp_server:
            # Register analytics tools
            await self.register_mcp_tool(
                name="parse_data_file",
                handler=self._parse_data_file_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to data file"},
                        "max_rows": {"type": "integer", "default": 500000, "description": "Maximum rows to parse"},
                        "as_dict": {"type": "boolean", "default": True, "description": "Return as dictionary format"}
                    },
                    "required": ["file_path"]
                },
                description="Parse CSV, Excel, or TSV files with automatic type detection"
            )
            
            await self.register_mcp_tool(
                name="create_chart",
                handler=self._create_chart_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "data": {"type": "object", "description": "Data to visualize"},
                        "chart_type": {"type": "string", "enum": ["line", "bar", "scatter", "pie", "area", "histogram", "box", "violin", "heatmap"], "description": "Type of chart to create"},
                        "config": {"type": "object", "description": "Chart configuration options"}
                    },
                    "required": ["data", "chart_type"]
                },
                description="Create interactive charts from data"
            )
            
            await self.register_mcp_tool(
                name="explore_data",
                handler=self._explore_data_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "data": {"type": "object", "description": "Data to explore"},
                        "query": {"type": "string", "description": "Search query for semantic exploration"},
                        "mode": {"type": "string", "enum": ["summary", "semantic_search", "full"], "default": "summary", "description": "Exploration mode"}
                    },
                    "required": ["data"]
                },
                description="Explore and analyze data with AI-powered insights"
            )
    
    async def _parse_data_file_tool(self, file_path: str, max_rows: int = 500000, as_dict: bool = True) -> Dict[str, Any]:
        """MCP tool to parse data files."""
        try:
            # Use the original auto_parser component
            parsed_data = render_auto_parser(
                file_path=file_path,
                max_rows=max_rows,
                as_dict=as_dict
            )
            
            # Store parsed data for later use
            dataset_id = f"dataset_{len(self.parsed_datasets)}"
            self.parsed_datasets[dataset_id] = {
                "data": parsed_data,
                "file_path": file_path,
                "parsed_at": datetime.utcnow().isoformat(),
                "row_count": len(parsed_data) if isinstance(parsed_data, list) else sum(len(sheet) for sheet in parsed_data.values()) if isinstance(parsed_data, dict) else 0
            }
            
            return {
                "success": True,
                "dataset_id": dataset_id,
                "data": parsed_data,
                "message": f"Successfully parsed {file_path}"
            }
            
        except AutoParserError as e:
            self.logger.error(f"Auto parser error: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "AutoParserError"
            }
        except Exception as e:
            self.logger.error(f"Unexpected error parsing file: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "UnexpectedError"
            }
    
    async def _create_chart_tool(self, data: Any, chart_type: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """MCP tool to create charts."""
        try:
            # Use the original chart_builder component
            chart = render_chart_builder(
                data=data,
                chart_type=chart_type,
                config=config,
                fail_safe=True
            )
            
            # Cache the chart
            chart_id = f"chart_{len(self.chart_cache)}"
            self.chart_cache[chart_id] = {
                "chart": chart,
                "chart_type": chart_type,
                "config": config,
                "created_at": datetime.utcnow().isoformat()
            }
            
            return {
                "success": True,
                "chart_id": chart_id,
                "chart": chart,
                "message": f"Successfully created {chart_type} chart"
            }
            
        except ChartBuilderError as e:
            self.logger.error(f"Chart builder error: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "ChartBuilderError"
            }
        except Exception as e:
            self.logger.error(f"Unexpected error creating chart: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "UnexpectedError"
            }
    
    async def _explore_data_tool(self, data: Any, query: Optional[str] = None, mode: str = "summary") -> Dict[str, Any]:
        """MCP tool to explore data."""
        try:
            # Use the original data_explorer component
            exploration_result = render_data_explorer(
                data=data,
                query=query,
                mode=mode,
                user_roles=["user"],  # Default role
                config={"max_rows": 100000, "top_k": 10}
            )
            
            # Store exploration history
            exploration_record = {
                "result": exploration_result,
                "query": query,
                "mode": mode,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.exploration_history.append(exploration_record)
            
            # Keep only recent history (last 100 explorations)
            if len(self.exploration_history) > 100:
                self.exploration_history = self.exploration_history[-100:]
            
            return {
                "success": exploration_result.get("success", True),
                "result": exploration_result.get("result"),
                "meta": exploration_result.get("meta", {}),
                "error": exploration_result.get("error"),
                "message": "Data exploration completed"
            }
            
        except Exception as e:
            self.logger.error(f"Unexpected error exploring data: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "UnexpectedError"
            }
    
    def create_api_router(self) -> APIRouter:
        """Create API routes for the Analytics Dashboard Extension."""
        router = APIRouter(prefix=f"/api/extensions/{self.manifest.name}")
        
        @router.post("/parse")
        async def parse_data_file(file_path: str, max_rows: int = 500000, as_dict: bool = True):
            """Parse a data file using the auto-parser."""
            result = await self._parse_data_file_tool(file_path, max_rows, as_dict)
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        
        @router.post("/chart")
        async def create_chart(request: AnalyticsRequest):
            """Create a chart from data."""
            result = await self._create_chart_tool(request.data, request.chart_type, request.config)
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        
        @router.post("/explore")
        async def explore_data(request: AnalyticsRequest):
            """Explore data with AI-powered insights."""
            result = await self._explore_data_tool(request.data, request.query, request.mode)
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        
        @router.get("/datasets")
        async def list_datasets():
            """List all parsed datasets."""
            return {
                "datasets": [
                    {
                        "id": dataset_id,
                        "file_path": info["file_path"],
                        "parsed_at": info["parsed_at"],
                        "row_count": info["row_count"]
                    }
                    for dataset_id, info in self.parsed_datasets.items()
                ]
            }
        
        @router.get("/datasets/{dataset_id}")
        async def get_dataset(dataset_id: str):
            """Get a specific dataset."""
            if dataset_id not in self.parsed_datasets:
                raise HTTPException(status_code=404, detail="Dataset not found")
            return self.parsed_datasets[dataset_id]
        
        @router.get("/charts")
        async def list_charts():
            """List all created charts."""
            return {
                "charts": [
                    {
                        "id": chart_id,
                        "chart_type": info["chart_type"],
                        "created_at": info["created_at"]
                    }
                    for chart_id, info in self.chart_cache.items()
                ]
            }
        
        @router.get("/charts/{chart_id}")
        async def get_chart(chart_id: str):
            """Get a specific chart."""
            if chart_id not in self.chart_cache:
                raise HTTPException(status_code=404, detail="Chart not found")
            return self.chart_cache[chart_id]
        
        @router.get("/exploration-history")
        async def get_exploration_history(limit: int = Query(default=10, le=100)):
            """Get data exploration history."""
            return {
                "history": self.exploration_history[-limit:] if limit > 0 else self.exploration_history
            }
        
        return router
    
    def create_ui_components(self) -> Dict[str, Any]:
        """Create UI components for the Analytics Dashboard."""
        components = super().create_ui_components()
        
        # Add analytics dashboard data
        components["analytics_dashboard"] = {
            "title": "Analytics Dashboard",
            "description": "Comprehensive data analytics and visualization",
            "data": {
                "total_datasets": len(self.parsed_datasets),
                "total_charts": len(self.chart_cache),
                "exploration_count": len(self.exploration_history),
                "recent_activity": self.exploration_history[-5:] if self.exploration_history else []
            }
        }
        
        return components
    
    async def _shutdown(self) -> None:
        """Cleanup the Analytics Dashboard Extension."""
        self.logger.info("Analytics Dashboard Extension shutting down...")
        
        # Clear caches
        self.parsed_datasets.clear()
        self.chart_cache.clear()
        self.exploration_history.clear()
        
        self.logger.info("Analytics Dashboard Extension shut down successfully")


# Export the extension class
__all__ = ["AnalyticsDashboardExtension"]