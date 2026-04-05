"""Extension management API routes."""

from datetime import datetime
from pathlib import Path
import sys
from typing import Any, Dict, List
from fastapi.responses import FileResponse


def _ensure_src_on_path() -> None:
    current = Path(__file__).resolve()
    repo_root = current.parents[3]
    src_root = repo_root / "src"
    src_str = str(src_root)
    if src_root.is_dir() and src_str not in sys.path:
        sys.path.insert(0, src_str)


_ensure_src_on_path()

try:
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover - fallback only
    from ai_karen_engine.pydantic_stub import BaseModel, Field

try:
    from extensions.core.manager import get_extension_core_manager as get_extension_manager
    from ai_karen_engine.utils.dependency_checks import import_fastapi

    class ExtensionStatusAPI(BaseModel):
        name: str
        display_name: str | None = Field(default=None)
        description: str | None = Field(default=None)
        version: str
        status: str
        loaded_at: datetime | None = Field(default=None)
        error_message: str | None = Field(default=None)
except ImportError:
    # Fallback when extension host is unavailable; still use real FastAPI if installed
    from ai_karen_engine.utils.dependency_checks import import_fastapi

    class ExtensionStatusAPI(BaseModel):
        name: str
        display_name: str | None = Field(default=None)
        description: str | None = Field(default=None)
        version: str
        status: str
        loaded_at: datetime | None = Field(default=None)
        error_message: str | None = Field(default=None)

    def get_extension_manager():
        return None

APIRouter, Depends, HTTPException, Request = import_fastapi(
    "APIRouter", "Depends", "HTTPException", "Request"
)

router = APIRouter()

# Import authentication dependencies
try:
    from ai_karen_engine.auth.auth_middleware import AuthenticationError, get_current_user
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    AuthenticationError = Exception  # type: ignore[assignment]
    async def get_current_user():
        return None


async def get_optional_current_user(request: Request):
    """Best-effort auth dependency for routes that can be viewed anonymously."""
    if not AUTH_AVAILABLE:
        return None
    try:
        return await get_current_user(request)
    except AuthenticationError:
        return None


@router.get("/", response_model=Dict[str, Any])
async def list_extensions_root(current_user=Depends(get_optional_current_user) if AUTH_AVAILABLE else None):
    """List all extensions and their status (root endpoint)."""
    extension_manager = get_extension_manager()
    if not extension_manager:
        return {
            "extensions": {},
            "total": 0,
            "message": "Extension manager not initialized",
            "status": "unavailable"
        }

    try:
        records = extension_manager.list_extension_statuses()
        if not records:
            records = await extension_manager.discover_extensions()

        extensions = {}
        for record in records:
            ext_data = {
                "id": record["id"],
                "name": record["name"],
                "display_name": record["display_name"],
                "description": record["description"],
                "version": record["version"],
                "status": record["status"],
                "loaded_at": record["loaded_at"].isoformat() if record["loaded_at"] else None,
                "error_message": record["error_message"],
                "capabilities": record["capabilities"],
                "menu_contributions": record.get("menu_contributions", []),
            }
            extensions[record["name"]] = ext_data
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
        "message": "Extensions available" if extensions else "No extensions found",
        "status": "available" if extensions else "empty"
    }


@router.get("/list")
async def list_extensions(current_user=Depends(get_optional_current_user) if AUTH_AVAILABLE else None):
    """List all extensions and their status."""
    manager = get_extension_manager()
    if not manager:
        return []

    try:
        records = manager.list_extension_statuses()
        if not records:
            records = await manager.discover_extensions()

        extensions: List[Dict[str, Any]] = []
        for record in records:
            loaded_at = record.get("loaded_at")
            # Get category from registry if available
            category = "plugins"
            if manager.registry:
                metadata = manager.registry.get_metadata(record.get("name"))
                if metadata:
                    category = metadata.category

            extensions.append(
                {
                    "name": record.get("name"),
                    "display_name": record.get("display_name"),
                    "description": record.get("description"),
                    "version": record.get("version") or "unknown",
                    "status": record.get("status") or "unknown",
                    "category": category,
                    "loaded_at": loaded_at.isoformat() if hasattr(loaded_at, "isoformat") else loaded_at,
                    "error_message": record.get("error_message"),
                    "menu_contributions": record.get("menu_contributions", []),
                }
            )
    except Exception:
        return []

    return extensions


@router.get("/{extension_name}")
async def get_extension_status(extension_name: str, current_user=Depends(get_optional_current_user) if AUTH_AVAILABLE else None):
    """Get detailed status of a specific extension."""
    extension_manager = get_extension_manager()
    if not extension_manager:
        raise HTTPException(
            status_code=503,
            detail="Extension manager not initialized",
        )

    status = extension_manager.get_extension_status(extension_name)
    if not status:
        await extension_manager.refresh_registry()
        status = extension_manager.get_extension_status(extension_name)
    if not status:
        raise HTTPException(status_code=404, detail="Extension not found")

    return status


@router.get("/{extension_name}/assets/{asset_path:path}")
async def get_extension_asset(
    extension_name: str,
    asset_path: str,
    current_user=Depends(get_optional_current_user) if AUTH_AVAILABLE else None,
):
    """Serve a static asset from a discovered extension directory."""
    extension_manager = get_extension_manager()
    if not extension_manager:
        raise HTTPException(status_code=404, detail="Extension manager not initialized")

    metadata = extension_manager.registry.get_metadata(extension_name)
    if not metadata:
        await extension_manager.refresh_registry()
        metadata = extension_manager.registry.get_metadata(extension_name)
    if not metadata:
        raise HTTPException(status_code=404, detail="Extension not found")

    base_dir = metadata.directory.resolve()
    target = (base_dir / asset_path).resolve()
    try:
        target.relative_to(base_dir)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid asset path") from exc

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")

    return FileResponse(Path(target))


@router.post("/{extension_name}/load")
async def load_extension(extension_name: str, current_user=Depends(get_current_user) if AUTH_AVAILABLE else None):
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
async def unload_extension(extension_name: str, current_user=Depends(get_current_user) if AUTH_AVAILABLE else None):
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
async def reload_extension(extension_name: str, current_user=Depends(get_current_user) if AUTH_AVAILABLE else None):
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
async def discover_extensions(current_user=Depends(get_current_user) if AUTH_AVAILABLE else None):
    """Discover available extensions in the extensions directory."""
    extension_manager = get_extension_manager()
    if not extension_manager:
        raise HTTPException(
            status_code=503,
            detail="Extension manager not initialized",
        )

    try:
        items = await extension_manager.discover_extensions()
        return {
            "discovered": len(items),
            "extensions": [
                {
                    "name": m["name"],
                    "version": m["version"],
                    "display_name": m["display_name"],
                    "description": m["description"],
                    "status": m["status"],
                    "error_message": m["error_message"],
                }
                for m in items
            ],
        }
    except Exception as e:  # pragma: no cover - runtime errors
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/registry/summary")
async def get_registry_summary(current_user=Depends(get_current_user) if AUTH_AVAILABLE else None):
    """Get extension registry summary."""
    extension_manager = get_extension_manager()
    if not extension_manager:
        raise HTTPException(
            status_code=503,
            detail="Extension manager not initialized",
        )

    return extension_manager.registry.to_dict()


@router.get("/health")
async def get_extensions_health(current_user=Depends(get_current_user) if AUTH_AVAILABLE else None):
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
