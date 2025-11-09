"""
Extension Marketplace API Routes

This module defines the FastAPI routes for the extension marketplace.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from .models import (
    ExtensionSearchRequest, ExtensionSearchResponse, ExtensionListingSchema,
    ExtensionVersionSchema, ExtensionInstallRequest, ExtensionInstallResponse,
    ExtensionUpdateRequest, ExtensionInstallationSchema, ExtensionReviewSchema
)
from .service import ExtensionMarketplaceService
from ..manager import ExtensionManager
from ..registry import ExtensionRegistry
from ...database import get_db_session
from ...auth import get_current_user, get_current_tenant

router = APIRouter(prefix="/api/extensions/marketplace", tags=["Extension Marketplace"])
security = HTTPBearer()


def get_marketplace_service(
    db: Session = Depends(get_db_session),
    extension_manager: ExtensionManager = Depends(),
    extension_registry: ExtensionRegistry = Depends()
) -> ExtensionMarketplaceService:
    """Get marketplace service instance."""
    return ExtensionMarketplaceService(db, extension_manager, extension_registry)


@router.get("/search", response_model=ExtensionSearchResponse)
async def search_extensions(
    query: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Extension category"),
    tags: Optional[List[str]] = Query(None, description="Extension tags"),
    price_filter: Optional[str] = Query("all", description="Price filter: free, paid, all"),
    sort_by: str = Query("popularity", description="Sort by: popularity, rating, newest, name"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    marketplace_service: ExtensionMarketplaceService = Depends(get_marketplace_service)
):
    """Search for extensions in the marketplace."""
    search_request = ExtensionSearchRequest(
        query=query,
        category=category,
        tags=tags or [],
        price_filter=price_filter,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )
    
    return await marketplace_service.search_extensions(search_request)


@router.get("/extensions/{extension_name}", response_model=ExtensionListingSchema)
async def get_extension_details(
    extension_name: str = Path(..., description="Extension name"),
    marketplace_service: ExtensionMarketplaceService = Depends(get_marketplace_service)
):
    """Get detailed information about a specific extension."""
    extension = await marketplace_service.get_extension_details(extension_name)
    
    if not extension:
        raise HTTPException(status_code=404, detail="Extension not found")
    
    return extension


@router.get("/extensions/{extension_name}/versions", response_model=List[ExtensionVersionSchema])
async def get_extension_versions(
    extension_name: str = Path(..., description="Extension name"),
    marketplace_service: ExtensionMarketplaceService = Depends(get_marketplace_service)
):
    """Get all versions of an extension."""
    versions = await marketplace_service.get_extension_versions(extension_name)
    return versions


@router.post("/install", response_model=ExtensionInstallResponse)
async def install_extension(
    install_request: ExtensionInstallRequest,
    current_user: dict = Depends(get_current_user),
    current_tenant: str = Depends(get_current_tenant),
    marketplace_service: ExtensionMarketplaceService = Depends(get_marketplace_service)
):
    """Install an extension for the current tenant."""
    return await marketplace_service.install_extension(
        install_request,
        current_tenant,
        current_user["user_id"]
    )


@router.post("/update", response_model=ExtensionInstallResponse)
async def update_extension(
    update_request: ExtensionUpdateRequest,
    current_user: dict = Depends(get_current_user),
    current_tenant: str = Depends(get_current_tenant),
    marketplace_service: ExtensionMarketplaceService = Depends(get_marketplace_service)
):
    """Update an installed extension."""
    return await marketplace_service.update_extension(
        update_request,
        current_tenant,
        current_user["user_id"]
    )


@router.delete("/uninstall/{extension_name}", response_model=ExtensionInstallResponse)
async def uninstall_extension(
    extension_name: str = Path(..., description="Extension name"),
    current_user: dict = Depends(get_current_user),
    current_tenant: str = Depends(get_current_tenant),
    marketplace_service: ExtensionMarketplaceService = Depends(get_marketplace_service)
):
    """Uninstall an extension."""
    return await marketplace_service.uninstall_extension(
        extension_name,
        current_tenant,
        current_user["user_id"]
    )


@router.get("/installations/{installation_id}", response_model=ExtensionInstallationSchema)
async def get_installation_status(
    installation_id: int = Path(..., description="Installation ID"),
    current_user: dict = Depends(get_current_user),
    marketplace_service: ExtensionMarketplaceService = Depends(get_marketplace_service)
):
    """Get the status of an installation."""
    installation = await marketplace_service.get_installation_status(installation_id)
    
    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")
    
    return installation


@router.get("/installed", response_model=List[ExtensionInstallationSchema])
async def get_installed_extensions(
    current_user: dict = Depends(get_current_user),
    current_tenant: str = Depends(get_current_tenant),
    marketplace_service: ExtensionMarketplaceService = Depends(get_marketplace_service)
):
    """Get all installed extensions for the current tenant."""
    return await marketplace_service.get_installed_extensions(current_tenant)


@router.get("/categories")
async def get_extension_categories(
    marketplace_service: ExtensionMarketplaceService = Depends(get_marketplace_service)
):
    """Get all available extension categories."""
    # This would query the database for distinct categories
    # For now, return a static list
    return [
        "analytics",
        "automation",
        "communication",
        "crm",
        "dashboard",
        "integration",
        "productivity",
        "reporting",
        "security",
        "workflow"
    ]


@router.get("/featured", response_model=List[ExtensionListingSchema])
async def get_featured_extensions(
    limit: int = Query(10, ge=1, le=50, description="Number of featured extensions"),
    marketplace_service: ExtensionMarketplaceService = Depends(get_marketplace_service)
):
    """Get featured extensions."""
    search_request = ExtensionSearchRequest(
        sort_by="rating",
        sort_order="desc",
        page=1,
        page_size=limit
    )
    
    result = await marketplace_service.search_extensions(search_request)
    return result.extensions


@router.get("/popular", response_model=List[ExtensionListingSchema])
async def get_popular_extensions(
    limit: int = Query(10, ge=1, le=50, description="Number of popular extensions"),
    marketplace_service: ExtensionMarketplaceService = Depends(get_marketplace_service)
):
    """Get popular extensions."""
    search_request = ExtensionSearchRequest(
        sort_by="popularity",
        sort_order="desc",
        page=1,
        page_size=limit
    )
    
    result = await marketplace_service.search_extensions(search_request)
    return result.extensions


@router.get("/recent", response_model=List[ExtensionListingSchema])
async def get_recent_extensions(
    limit: int = Query(10, ge=1, le=50, description="Number of recent extensions"),
    marketplace_service: ExtensionMarketplaceService = Depends(get_marketplace_service)
):
    """Get recently published extensions."""
    search_request = ExtensionSearchRequest(
        sort_by="newest",
        sort_order="desc",
        page=1,
        page_size=limit
    )
    
    result = await marketplace_service.search_extensions(search_request)
    return result.extensions


# Extension Reviews (placeholder for future implementation)

@router.post("/extensions/{extension_name}/reviews", response_model=ExtensionReviewSchema)
async def create_extension_review(
    extension_name: str = Path(..., description="Extension name"),
    review: ExtensionReviewSchema = ...,
    current_user: dict = Depends(get_current_user),
    marketplace_service: ExtensionMarketplaceService = Depends(get_marketplace_service)
):
    """Create a review for an extension."""
    # This would be implemented to create extension reviews
    raise HTTPException(status_code=501, detail="Reviews not yet implemented")


@router.get("/extensions/{extension_name}/reviews", response_model=List[ExtensionReviewSchema])
async def get_extension_reviews(
    extension_name: str = Path(..., description="Extension name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    marketplace_service: ExtensionMarketplaceService = Depends(get_marketplace_service)
):
    """Get reviews for an extension."""
    # This would be implemented to fetch extension reviews
    raise HTTPException(status_code=501, detail="Reviews not yet implemented")


# Admin endpoints (for marketplace management)

@router.post("/admin/extensions", response_model=ExtensionListingSchema)
async def create_extension_listing(
    extension: ExtensionListingSchema,
    current_user: dict = Depends(get_current_user),
    marketplace_service: ExtensionMarketplaceService = Depends(get_marketplace_service)
):
    """Create a new extension listing (admin only)."""
    # This would be implemented for admin users to create extension listings
    raise HTTPException(status_code=501, detail="Admin endpoints not yet implemented")


@router.put("/admin/extensions/{extension_name}", response_model=ExtensionListingSchema)
async def update_extension_listing(
    extension_name: str = Path(..., description="Extension name"),
    extension: ExtensionListingSchema = ...,
    current_user: dict = Depends(get_current_user),
    marketplace_service: ExtensionMarketplaceService = Depends(get_marketplace_service)
):
    """Update an extension listing (admin only)."""
    # This would be implemented for admin users to update extension listings
    raise HTTPException(status_code=501, detail="Admin endpoints not yet implemented")


@router.post("/admin/extensions/{extension_name}/versions", response_model=ExtensionVersionSchema)
async def create_extension_version(
    extension_name: str = Path(..., description="Extension name"),
    version: ExtensionVersionSchema = ...,
    current_user: dict = Depends(get_current_user),
    marketplace_service: ExtensionMarketplaceService = Depends(get_marketplace_service)
):
    """Create a new extension version (admin only)."""
    # This would be implemented for admin users to create extension versions
    raise HTTPException(status_code=501, detail="Admin endpoints not yet implemented")