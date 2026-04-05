"""
Marketplace API Routes - REST endpoints for plugin marketplace.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from extensions.core.registry.marketplace_discovery import (
    get_discovery_service,
    SearchQuery,
    RegistrySource,
    RegistryConfig,
    RemotePlugin,
)

logger = logging.getLogger("kari.marketplace_routes")

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])


class SearchRequest(BaseModel):
    """Marketplace search request."""

    query: str = ""
    category: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    sort_by: str = Field(
        default="relevance", pattern="^(relevance|popularity|updated|name)$"
    )
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class RegistryAddRequest(BaseModel):
    """Request to add a registry."""

    source: str = Field(..., pattern="^(local|github|gitlab|npm|pypi|custom)$")
    name: str = Field(..., min_length=1, max_length=100)
    base_url: str = Field(..., min_length=1)
    priority: int = Field(default=0, ge=0, le=100)
    auth_token: Optional[str] = None


class PluginResponse(BaseModel):
    """Plugin response model."""

    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    source: str
    download_url: str
    homepage: Optional[str] = None
    license: Optional[str] = None
    category: str
    tags: List[str] = []
    rating: Optional[float] = None
    download_count: int = 0
    last_updated: Optional[str] = None
    verified: bool = False


class CategoryResponse(BaseModel):
    """Category response model."""

    category: str
    count: int


class RegistryResponse(BaseModel):
    """Registry response model."""

    name: str
    source: str
    base_url: str
    enabled: bool
    priority: int


@router.get("/search", response_model=Dict[str, Any])
async def search_plugins(
    q: str = Query("", description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    author: Optional[str] = Query(None, description="Filter by author"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    sort_by: str = Query("relevance", description="Sort order"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Search for plugins in the marketplace.

    Args:
        q: Search query string
        category: Filter by category
        author: Filter by author
        tags: Comma-separated tags
        sort_by: Sort order (relevance, popularity, updated, name)
        limit: Maximum results
        offset: Result offset

    Returns:
        Search results with pagination info
    """
    try:
        discovery = get_discovery_service()

        query = SearchQuery(
            query=q,
            category=category,
            author=author,
            tags=tags.split(",") if tags else [],
            sort_by=sort_by,
            limit=limit,
            offset=offset,
        )

        plugins = await discovery.search_plugins(query)

        # Convert to response format
        plugin_responses = [
            PluginResponse(
                plugin_id=p.plugin_id,
                name=p.name,
                version=p.version,
                description=p.description,
                author=p.author,
                source=p.source.value,
                download_url=p.download_url,
                homepage=p.homepage,
                license=p.license,
                category=p.category,
                tags=p.tags,
                rating=p.rating,
                download_count=p.download_count,
                last_updated=p.last_updated.isoformat() if p.last_updated else None,
                verified=p.verified,
            )
            for p in plugins
        ]

        return {
            "status": "success",
            "data": {
                "plugins": plugin_responses,
                "total": len(plugin_responses),
                "query": q,
                "category": category,
                "author": author,
                "offset": offset,
                "limit": limit,
            },
        }

    except Exception as e:
        logger.error(f"Failed to search plugins: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search plugins: {str(e)}",
        )


@router.get("/popular", response_model=Dict[str, Any])
async def get_popular_plugins(
    limit: int = Query(10, ge=1, le=50),
):
    """Get popular plugins by download count."""
    try:
        discovery = get_discovery_service()
        plugins = await discovery.get_popular_plugins(limit)

        plugin_responses = [
            PluginResponse(
                plugin_id=p.plugin_id,
                name=p.name,
                version=p.version,
                description=p.description,
                author=p.author,
                source=p.source.value,
                download_url=p.download_url,
                homepage=p.homepage,
                license=p.license,
                category=p.category,
                tags=p.tags,
                rating=p.rating,
                download_count=p.download_count,
                last_updated=p.last_updated.isoformat() if p.last_updated else None,
                verified=p.verified,
            )
            for p in plugins
        ]

        return {
            "status": "success",
            "data": {
                "plugins": plugin_responses,
                "total": len(plugin_responses),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get popular plugins: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get popular plugins: {str(e)}",
        )


@router.get("/recent", response_model=Dict[str, Any])
async def get_recently_updated(
    limit: int = Query(10, ge=1, le=50),
):
    """Get recently updated plugins."""
    try:
        discovery = get_discovery_service()
        plugins = await discovery.get_recently_updated(limit)

        plugin_responses = [
            PluginResponse(
                plugin_id=p.plugin_id,
                name=p.name,
                version=p.version,
                description=p.description,
                author=p.author,
                source=p.source.value,
                download_url=p.download_url,
                homepage=p.homepage,
                license=p.license,
                category=p.category,
                tags=p.tags,
                rating=p.rating,
                download_count=p.download_count,
                last_updated=p.last_updated.isoformat() if p.last_updated else None,
                verified=p.verified,
            )
            for p in plugins
        ]

        return {
            "status": "success",
            "data": {
                "plugins": plugin_responses,
                "total": len(plugin_responses),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get recently updated plugins: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recently updated plugins: {str(e)}",
        )


@router.get("/categories", response_model=Dict[str, Any])
async def get_categories():
    """Get all available plugin categories."""
    try:
        discovery = get_discovery_service()
        categories = await discovery.get_categories()

        category_responses = [
            CategoryResponse(category=cat, count=count)
            for cat, count in categories.items()
        ]

        return {
            "status": "success",
            "data": {
                "categories": category_responses,
                "total": len(category_responses),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get categories: {str(e)}",
        )


@router.get("/plugin/{plugin_id}", response_model=Dict[str, Any])
async def get_plugin_details(plugin_id: str):
    """Get detailed information about a specific plugin."""
    try:
        discovery = get_discovery_service()
        plugin = await discovery.get_plugin_details(plugin_id)

        if not plugin:
            raise HTTPException(
                status_code=404,
                detail=f"Plugin '{plugin_id}' not found",
            )

        return {
            "status": "success",
            "data": PluginResponse(
                plugin_id=plugin.plugin_id,
                name=plugin.name,
                version=plugin.version,
                description=plugin.description,
                author=plugin.author,
                source=plugin.source.value,
                download_url=plugin.download_url,
                homepage=plugin.homepage,
                license=plugin.license,
                category=plugin.category,
                tags=plugin.tags,
                rating=plugin.rating,
                download_count=plugin.download_count,
                last_updated=plugin.last_updated.isoformat()
                if plugin.last_updated
                else None,
                verified=plugin.verified,
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get plugin details for {plugin_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get plugin details: {str(e)}",
        )


@router.get("/registries", response_model=Dict[str, Any])
async def get_registries():
    """Get all configured registries."""
    try:
        discovery = get_discovery_service()
        registries = discovery.get_registries()

        registry_responses = [RegistryResponse(**r) for r in registries]

        return {
            "status": "success",
            "data": {
                "registries": registry_responses,
                "total": len(registry_responses),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get registries: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get registries: {str(e)}",
        )


@router.post("/registries", response_model=Dict[str, Any])
async def add_registry(request: RegistryAddRequest):
    """Add a new registry source."""
    try:
        discovery = get_discovery_service()

        config = RegistryConfig(
            source=RegistrySource(request.source),
            name=request.name,
            base_url=request.base_url,
            priority=request.priority,
            auth_token=request.auth_token,
        )

        discovery.add_registry(config)

        return {
            "status": "success",
            "message": f"Registry '{request.name}' added successfully",
            "data": RegistryResponse(
                name=config.name,
                source=config.source.value,
                base_url=config.base_url,
                enabled=config.enabled,
                priority=config.priority,
            ),
        }

    except Exception as e:
        logger.error(f"Failed to add registry: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add registry: {str(e)}",
        )


@router.delete("/registries/{registry_name}", response_model=Dict[str, Any])
async def remove_registry(registry_name: str):
    """Remove a registry source."""
    try:
        discovery = get_discovery_service()
        removed = discovery.remove_registry(registry_name)

        if not removed:
            raise HTTPException(
                status_code=404,
                detail=f"Registry '{registry_name}' not found",
            )

        return {
            "status": "success",
            "message": f"Registry '{registry_name}' removed successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove registry: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove registry: {str(e)}",
        )
