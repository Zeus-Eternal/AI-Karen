"""Extension management API routes."""

from typing import Any, Dict, List

from ai_karen_engine.core.dependencies import get_current_user_context
from ai_karen_engine.extensions import get_extension_manager
from ai_karen_engine.extensions.models import ExtensionStatusAPI
from ai_karen_engine.utils.dependency_checks import import_fastapi

APIRouter, Depends, HTTPException = import_fastapi(
    "APIRouter", "Depends", "HTTPException"
)

router = APIRouter()

# Alias core dependency for convenience
get_current_user = get_current_user_context


@router.get("/extensions", response_model=List[ExtensionStatusAPI])
async def list_extensions(user: Dict[str, Any] = Depends(get_current_user)):
    """List all extensions and their status."""
    extension_manager = get_extension_manager()
    if not extension_manager:
        raise HTTPException(
            status_code=503,
            detail="Extension manager not initialized",
        )

    extensions = []
    for record in extension_manager.registry.list_extensions():
        extensions.append(
            ExtensionStatusAPI(
                name=record.manifest.name,
                version=record.manifest.version,
                status=record.status.value,
                loaded_at=record.loaded_at,
                error_message=record.error_message,
            )
        )

    return extensions


@router.get("/extensions/{extension_name}")
async def get_extension_status(
    extension_name: str, user: Dict[str, Any] = Depends(get_current_user)
):
    """Get detailed status of a specific extension."""
    extension_manager = get_extension_manager()
    if not extension_manager:
        raise HTTPException(
            status_code=503,
            detail="Extension manager not initialized",
        )

    status = extension_manager.get_extension_status(extension_name)
    if not status:
        raise HTTPException(status_code=404, detail="Extension not found")

    return status


@router.post("/extensions/{extension_name}/load")
async def load_extension(
    extension_name: str, user: Dict[str, Any] = Depends(get_current_user)
):
    """Load an extension."""
    extension_manager = get_extension_manager()
    if not extension_manager:
        raise HTTPException(
            status_code=503,
            detail="Extension manager not initialized",
        )

    try:
        record = await extension_manager.load_extension(extension_name)
        return {
            "message": f"Extension {extension_name} loaded successfully",
            "status": record.status.value,
        }
    except Exception as e:  # pragma: no cover - runtime errors
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/extensions/{extension_name}/unload")
async def unload_extension(
    extension_name: str, user: Dict[str, Any] = Depends(get_current_user)
):
    """Unload an extension."""
    extension_manager = get_extension_manager()
    if not extension_manager:
        raise HTTPException(
            status_code=503,
            detail="Extension manager not initialized",
        )

    try:
        await extension_manager.unload_extension(extension_name)
        return {"message": f"Extension {extension_name} unloaded successfully"}
    except Exception as e:  # pragma: no cover - runtime errors
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/extensions/{extension_name}/reload")
async def reload_extension(
    extension_name: str, user: Dict[str, Any] = Depends(get_current_user)
):
    """Reload an extension (for development)."""
    extension_manager = get_extension_manager()
    if not extension_manager:
        raise HTTPException(
            status_code=503,
            detail="Extension manager not initialized",
        )

    try:
        record = await extension_manager.reload_extension(extension_name)
        return {
            "message": f"Extension {extension_name} reloaded successfully",
            "status": record.status.value,
        }
    except Exception as e:  # pragma: no cover - runtime errors
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/extensions/discover")
async def discover_extensions(user: Dict[str, Any] = Depends(get_current_user)):
    """Discover available extensions in the extensions directory."""
    extension_manager = get_extension_manager()
    if not extension_manager:
        raise HTTPException(
            status_code=503,
            detail="Extension manager not initialized",
        )

    try:
        manifests = await extension_manager.discover_extensions()
        return {
            "discovered": len(manifests),
            "extensions": [
                {
                    "name": manifest.name,
                    "version": manifest.version,
                    "display_name": manifest.display_name,
                    "description": manifest.description,
                    "category": manifest.category,
                    "author": manifest.author,
                }
                for manifest in manifests.values()
            ],
        }
    except Exception as e:  # pragma: no cover - runtime errors
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/extensions/registry/summary")
async def get_registry_summary(user: Dict[str, Any] = Depends(get_current_user)):
    """Get extension registry summary."""
    extension_manager = get_extension_manager()
    if not extension_manager:
        raise HTTPException(
            status_code=503,
            detail="Extension manager not initialized",
        )

    return extension_manager.registry.to_dict()


__all__ = ["router"]
