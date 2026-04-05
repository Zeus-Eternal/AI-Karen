"""
Mock Plugin Store API Routes for Development

This provides a temporary implementation of the plugin store endpoints
while the full backend is being developed.
"""

from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/store", tags=["plugin-store"])


class PluginSearchParams(BaseModel):
    query: Optional[str] = Field(None, description="Search query string")
    category: Optional[str] = Field(None, description="Filter by category")
    sort_by: Optional[str] = Field("popularity", description="Sort order")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")


class PluginInstallRequest(BaseModel):
    plugin_id: str = Field(..., description="Plugin identifier")
    version: Optional[str] = Field(None, description="Specific version to install")


class PluginRatingRequest(BaseModel):
    plugin_id: str = Field(..., description="Plugin identifier")
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5)")
    review: str = Field(..., min_length=10, max_length=1000, description="Review text")


# Mock data for development
MOCK_PLUGINS = [
    {
        "id": "weather-plugin",
        "name": "Weather Plugin",
        "description": "Get weather information for any location",
        "version": "1.0.0",
        "author": "Karen AI Team",
        "category": "utilities",
        "rating": 4.5,
        "downloads": 1250,
        "status": "active",
        "price": 0.0,
        "tags": ["weather", "forecast", "utilities"],
    },
    {
        "id": "gmail-plugin",
        "name": "Gmail Integration",
        "description": "Connect and manage your Gmail account",
        "version": "2.1.0",
        "author": "Karen AI Team",
        "category": "communication",
        "rating": 4.2,
        "downloads": 890,
        "status": "active",
        "price": 0.0,
        "tags": ["gmail", "email", "communication"],
    },
    {
        "id": "data-connector",
        "name": "Data Connector",
        "description": "Connect to various data sources and databases",
        "version": "1.2.0",
        "author": "Karen AI Team",
        "category": "integration",
        "rating": 4.7,
        "downloads": 2100,
        "status": "active",
        "price": 0.0,
        "tags": ["data", "database", "integration"],
    },
]

MOCK_CATEGORIES = [
    {"name": "utilities", "display_name": "Utilities", "plugin_count": 1},
    {"name": "communication", "display_name": "Communication", "plugin_count": 1},
    {"name": "integration", "display_name": "Integration", "plugin_count": 1},
    {"name": "productivity", "display_name": "Productivity", "plugin_count": 0},
    {"name": "development", "display_name": "Development", "plugin_count": 0},
]


@router.get("/search", response_model=Dict[str, Any])
async def search_plugins(params: PluginSearchParams = PluginSearchParams()):
    """Search for plugins."""
    # Filter mock plugins based on search params
    filtered_plugins = MOCK_PLUGINS.copy()

    if params.query:
        query_lower = params.query.lower()
        filtered_plugins = [
            p
            for p in filtered_plugins
            if query_lower in p["name"].lower()
            or query_lower in p["description"].lower()
        ]

    if params.category:
        filtered_plugins = [
            p for p in filtered_plugins if p["category"] == params.category
        ]

    # Apply pagination
    offset = (params.page - 1) * params.per_page
    paginated_plugins = filtered_plugins[offset : offset + params.per_page]

    return {
        "plugins": paginated_plugins,
        "total": len(filtered_plugins),
        "page": params.page,
        "per_page": params.per_page,
        "total_pages": (len(filtered_plugins) + params.per_page - 1) // params.per_page,
        "has_next": offset + params.per_page < len(filtered_plugins),
    }


@router.get("/plugins/{plugin_id}", response_model=Dict[str, Any])
async def get_plugin_details(plugin_id: str):
    """Get plugin details."""
    plugin = next((p for p in MOCK_PLUGINS if p["id"] == plugin_id), None)

    if not plugin:
        return {"error": "Plugin not found", "plugin_id": plugin_id}

    return {
        "plugin": plugin,
        "marketplace_info": {
            "repository": "https://github.com/karen-ai/plugins",
            "documentation": f"https://docs.karen.ai/plugins/{plugin_id}",
            "changelog": f"https://github.com/karen-ai/plugins/{plugin_id}/CHANGELOG.md",
        },
        "analytics": {
            "downloads": plugin["downloads"],
            "rating": plugin["rating"],
            "installations": plugin["downloads"] * 0.8,  # Mock installation count
        },
        "installed": False,
        "update_available": False,
    }


@router.post("/install", response_model=Dict[str, Any])
async def install_plugin(request: PluginInstallRequest):
    """Install plugin from store."""
    plugin = next((p for p in MOCK_PLUGINS if p["id"] == request.plugin_id), None)

    if not plugin:
        return {
            "success": False,
            "error": "Plugin not found",
            "plugin_id": request.plugin_id,
        }

    return {
        "success": True,
        "message": f"Plugin '{plugin['name']}' installed successfully",
        "plugin_id": request.plugin_id,
        "version": request.version or plugin["version"],
    }


@router.post("/rate", response_model=Dict[str, Any])
async def rate_plugin(request: PluginRatingRequest):
    """Rate a plugin."""
    plugin = next((p for p in MOCK_PLUGINS if p["id"] == request.plugin_id), None)

    if not plugin:
        return {
            "success": False,
            "error": "Plugin not found",
            "plugin_id": request.plugin_id,
        }

    return {
        "success": True,
        "message": "Rating saved successfully",
        "plugin_id": request.plugin_id,
        "rating": request.rating,
    }


@router.get("/statistics", response_model=Dict[str, Any])
async def get_statistics():
    """Get store statistics."""
    return {
        "total_plugins": len(MOCK_PLUGINS),
        "active_plugins": len([p for p in MOCK_PLUGINS if p["status"] == "active"]),
        "total_downloads": sum(p["downloads"] for p in MOCK_PLUGINS),
        "total_ratings": len(MOCK_PLUGINS) * 50,  # Mock rating count
        "recent_updates": 1,
    }


@router.get("/categories", response_model=List[Dict[str, Any]])
async def get_categories():
    """Get plugin categories."""
    return MOCK_CATEGORIES


@router.get("/trending", response_model=List[Dict[str, Any]])
async def get_trending(limit: int = Query(10, ge=1, le=50)):
    """Get trending plugins."""
    # Return mock plugins sorted by downloads
    trending = sorted(MOCK_PLUGINS, key=lambda p: p["downloads"], reverse=True)
    return trending[:limit]


@router.get("/updates", response_model=List[Dict[str, Any]])
async def get_updates():
    """Get available updates for installed plugins."""
    return []  # No updates available in mock
