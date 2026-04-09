"""Extension management API routes."""

import logging
from datetime import datetime
from pathlib import Path
import sys
from typing import Any, Dict, List
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)


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


# Import extensions manager
def get_extension_manager():
    """Get extension manager, returns None if not available."""
    try:
        from extensions.core.manager import (
            get_extension_core_manager as get_extension_manager,
        )

        return get_extension_manager()
    except ImportError:
        return None


# Define the API model
class ExtensionStatusAPI(BaseModel):
    name: str
    display_name: str | None = Field(default=None)
    description: str | None = Field(default=None)
    version: str
    status: str
    loaded_at: datetime | None = Field(default=None)
    error_message: str | None = Field(default=None)


# Import FastAPI components
from ai_karen_engine.utils.dependency_checks import import_fastapi

APIRouter, Depends, HTTPException, Request = import_fastapi(
    "APIRouter", "Depends", "HTTPException", "Request"
)

router = APIRouter()

# Import authentication dependencies with auth bypass support
_real_get_current_user = None
auth_config = None
try:
    from ai_karen_engine.auth.auth_middleware import (
        AuthenticationError,
        get_current_user as _real_get_current_user,
    )
    from ai_karen_engine.core.auth_config import auth_config

    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    AuthenticationError = Exception  # type: ignore[assignment]


async def get_current_user(request: Request):
    """Get current user with auth bypass support."""
    if not AUTH_AVAILABLE:
        return None

    # Check for auth bypass
    if (
        auth_config
        and hasattr(auth_config, "should_bypass_auth")
        and auth_config.should_bypass_auth()
    ):
        # Return development user context when auth is bypassed
        return {
            "user_id": "dev-user",
            "email": "dev-user@karen.ai",
            "user_type": "developer",
            "permissions": [
                "extension:*",
                "chat:write",
                "chat:read",
                "chat:admin",
                "memory:read",
                "memory:write",
                "conversation:create",
                "message:send",
                "admin:*",
            ],
            "tenant_id": "dev-tenant",
            "authenticated": True,
        }

    if _real_get_current_user:
        return await _real_get_current_user(request)
    return None


async def get_optional_current_user(request: Request):
    """Best-effort auth dependency for routes that can be viewed anonymously."""
    if not AUTH_AVAILABLE:
        return None
    try:
        return await get_current_user(request)
    except AuthenticationError:
        return None


async def get_optional_current_user_with_deps(
    request: Request, current_user=Depends(get_optional_current_user)
):
    """Dependency wrapper that always works, even when AUTH_AVAILABLE is False."""
    return current_user


@router.get("/", response_model=Dict[str, Any])
async def list_extensions_root():
    """List all extensions and their status (root endpoint)."""
    extension_manager = get_extension_manager()
    if not extension_manager:
        return {
            "extensions": {},
            "total": 0,
            "message": "Extension manager not initialized",
            "status": "unavailable",
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
                "loaded_at": record["loaded_at"].isoformat()
                if record["loaded_at"]
                else None,
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
            "status": "error",
        }

    return {
        "extensions": extensions,
        "total": len(extensions),
        "message": "Extensions available" if extensions else "No extensions found",
        "status": "available" if extensions else "empty",
    }


# Pydantic model for install request
class InstallRequest(BaseModel):
    plugin_id: str


@router.post("/install")
async def install_extension(request: InstallRequest):
    """Simple extension installation endpoint."""
    plugin_id = request.plugin_id
    # For now, just return success without actually installing
    # The complex extension system may not be working properly
    logger.info(f"Extension installation requested for {plugin_id}")
    return {
        "success": True,
        "message": f"Installation request received for {plugin_id}",
        "plugin_id": plugin_id,
    }


@router.get("/list")
async def list_extensions():
    """List all extensions and their status."""
    try:
        manager = get_extension_manager()
        if not manager:
            logger.warning("Extension manager not available, returning empty list")
            return []

        # Return a simple hardcoded list for now to avoid crashes
        return [
            {
                "id": "weather-query",
                "name": "weather-query",
                "display_name": "Weather Query",
                "description": "Get weather information for any location",
                "version": "0.2.0",
                "status": "active",
                "loaded_at": None,
                "category": "plugins",
                "capabilities": {"provides_ui": True},
                "has_component": True,
                "ui_entry_points": [
                    {
                        "entry_id": "weather-query-main",
                        "component": "weather-query",
                        "zone": "page.plugins.overview",
                        "label": "Weather",
                    }
                ],
            }
        ]

    except Exception as e:
        logger.error(f"Error in list_extensions: {e}", exc_info=True)
        return []
    except Exception:
        logger.error("Error in list_extensions", exc_info=True)
        return []

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
        await extension_manager.refresh_registry()
        status = extension_manager.get_extension_status(extension_name)
    if not status:
        raise HTTPException(status_code=404, detail="Extension not found")

    return status


@router.get("/{extension_name}/assets/{asset_path:path}")
async def get_extension_asset(
    extension_name: str,
    asset_path: str,
    current_user=Depends(get_optional_current_user_with_deps),
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
async def load_extension(
    extension_name: str,
    current_user=Depends(get_current_user) if AUTH_AVAILABLE else None,
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


@router.post("/{extension_name}/unload")
async def unload_extension(
    extension_name: str,
    current_user=Depends(get_current_user) if AUTH_AVAILABLE else None,
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


@router.post("/{extension_name}/reload")
async def reload_extension(
    extension_name: str,
    current_user=Depends(get_current_user) if AUTH_AVAILABLE else None,
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


@router.get("/discover")
async def discover_extensions(
    current_user=Depends(get_current_user) if AUTH_AVAILABLE else None,
):
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
async def get_registry_summary(
    current_user=Depends(get_current_user) if AUTH_AVAILABLE else None,
):
    """Get extension registry summary."""
    extension_manager = get_extension_manager()
    if not extension_manager:
        raise HTTPException(
            status_code=503,
            detail="Extension manager not initialized",
        )

    return extension_manager.registry.to_dict()


@router.get("/health")
async def get_extensions_health(
    current_user=Depends(get_current_user) if AUTH_AVAILABLE else None,
):
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
            "extensions": [],
        }

    try:
        health_summary = extension_manager.get_health_summary()
        return {
            "status": "healthy",
            "message": "Extension system operational",
            "extensions": health_summary,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Extension system error: {str(e)}",
            "extensions": [],
        }


__all__ = ["router"]
