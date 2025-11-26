"""Extension management API routes."""

from typing import Any, Dict, List

try:
    from ai_karen_engine.extension_host.__init__2 import get_extension_manager
    from ai_karen_engine.extension_host.models import ExtensionStatusAPI
    from ai_karen_engine.utils.dependency_checks import import_fastapi
except ImportError:
    # Define dummy classes if imports fail
    class ExtensionStatusAPI:
        def __init__(self, name, version, status, loaded_at=None, error_message=None):
            self.name = name
            self.version = version
            self.status = status
            self.loaded_at = loaded_at
            self.error_message = error_message
    
    def get_extension_manager():
        return None
    
    def import_fastapi(*args):
        # Return dummy objects if FastAPI is not available
        class Dummy:
            def __init__(self, *args, **kwargs):
                pass
        return tuple([Dummy() for _ in args])

APIRouter, Depends, HTTPException = import_fastapi(
    "APIRouter", "Depends", "HTTPException"
)

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def list_extensions_root():
    """List all extensions and their status (root endpoint)."""
    extension_manager = get_extension_manager()
    if not extension_manager:
        return {
            "extensions": {},
            "total": 0,
            "message": "Extension manager not initialized",
            "status": "unavailable"
        }

    extensions = {}
    extension_list = []
    try:
        for record in extension_manager.registry.list_extensions():
            ext_data = {
                "id": record.manifest.name,
                "name": record.manifest.name,
                "display_name": record.manifest.display_name or record.manifest.name,
                "description": record.manifest.description or "No description available",
                "version": record.manifest.version,
                "status": record.status.value,
                "loaded_at": record.loaded_at.isoformat() if record.loaded_at else None,
                "error_message": record.error_message,
                "capabilities": {
                    "provides_ui": getattr(record.manifest, 'provides_ui', False),
                    "provides_api": getattr(record.manifest, 'provides_api', False),
                    "provides_background_tasks": getattr(record.manifest, 'provides_background_tasks', False),
                    "provides_webhooks": getattr(record.manifest, 'provides_webhooks', False)
                }
            }
            extensions[record.manifest.name] = ext_data
            extension_list.append(ext_data)
    except Exception as e:
        return {
            "extensions": {},
            "total": 0,
            "message": f"Error loading extensions: {str(e)}",
            "status": "error"
        }

    return {
        "extensions": extensions,
        "total": len(extensions),
        "message": "Extensions loaded successfully" if extensions else "No extensions found",
        "status": "available" if extensions else "empty"
    }


@router.get("/list", response_model=List[ExtensionStatusAPI])
async def list_extensions():
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


@router.get("/{extension_name}")
async def get_extension_status(extension_name: str):
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


@router.post("/{extension_name}/load")
async def load_extension(extension_name: str):
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


@router.post("/{extension_name}/unload")
async def unload_extension(extension_name: str):
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


@router.post("/{extension_name}/reload")
async def reload_extension(extension_name: str):
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


@router.get("/discover")
async def discover_extensions():
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


@router.get("/registry/summary")
async def get_registry_summary():
    """Get extension registry summary."""
    extension_manager = get_extension_manager()
    if not extension_manager:
        raise HTTPException(
            status_code=503,
            detail="Extension manager not initialized",
        )

    return extension_manager.registry.to_dict()


@router.get("/health")
async def get_extensions_health():
    """Get overall health summary for extensions."""
    extension_manager = get_extension_manager()
    if not extension_manager:
        raise HTTPException(
            status_code=503,
            detail="Extension manager not initialized",
        )
    return extension_manager.get_health_summary()


@router.get("/system/health")
async def get_system_health():
    """Get system health for extensions (public endpoint)."""
    extension_manager = get_extension_manager()
    if not extension_manager:
        return {
            "status": "unavailable",
            "message": "Extension manager not initialized",
            "extensions": []
        }
    
    try:
        health_summary = extension_manager.get_health_summary()
        return {
            "status": "healthy",
            "message": "Extension system operational",
            "extensions": health_summary
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Extension system error: {str(e)}",
            "extensions": []
        }


__all__ = ["router"]
