"""
API routes for manifest-driven plugin integration.

These endpoints provide RESTful access to the manifest integration service,
allowing the frontend to discover, install, and manage plugin UI components
based on their manifest configurations.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ...core.manager import ExtensionCore
from ...registry.ui_installer import UIInstallerService
from ...registry.manifest_integration import ManifestIntegrationService, PluginManifest

router = APIRouter(prefix="/api/ui-materialization", tags=["ui-materialization"])


class ImportMapResponse(BaseModel):
    """Response model for import map generation."""

    status: str
    import_map: Dict[str, str]
    total_entries: int
    timestamp: str


class IntegrationStatusResponse(BaseModel):
    """Response model for integration status."""

    plugin_name: str
    status: str
    has_manifest: bool
    has_ui: bool
    ui_installed: bool
    plugin_status: str
    last_updated: str


class SyncResponse(BaseModel):
    """Response model for synchronization operation."""

    status: str
    total_plugins: int
    successful: int
    failed: int
    skipped: int
    details: List[Dict[str, Any]]


# Global service instances (would be injected in real application)
_extension_core = None
_ui_installer = None
_manifest_integration_service = None


def get_manifest_integration_service():
    """Get the manifest integration service instance."""
    global _extension_core, _ui_installer, _manifest_integration_service

    if _manifest_integration_service is None:
        if _extension_core is None:
            _extension_core = ExtensionCore()
        if _ui_installer is None:
            _ui_installer = UIInstallerService(_extension_core)
        _manifest_integration_service = ManifestIntegrationService(
            _extension_core, _ui_installer
        )

    return _manifest_integration_service


@router.get("/discover", response_model=List[PluginManifest])
async def discover_plugins():
    """
    Discover all plugins with manifests and return their UI configuration.

    Returns:
        List of plugin manifests with UI configuration
    """
    try:
        service = get_manifest_integration_service()
        manifests = service.discover_plugins_with_manifests()
        return manifests
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to discover plugins: {str(e)}"
        )


@router.get("/import-map", response_model=ImportMapResponse)
async def get_import_map():
    """
    Generate and return the frontend import map based on plugin manifests.

    Returns:
        Import map configuration for frontend consumption
    """
    try:
        service = get_manifest_integration_service()
        import_map = service.generate_frontend_import_map()

        return ImportMapResponse(
            status="success",
            import_map=import_map,
            total_entries=len(import_map),
            timestamp="2024-01-01T00:00:00Z",  # Would use actual timestamp
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate import map: {str(e)}"
        )


@router.post("/install/{plugin_name}")
async def install_plugin_ui(plugin_name: str):
    """
    Install a plugin's UI component based on its manifest configuration.

    Args:
        plugin_name: Name of the plugin to install

    Returns:
        Success status and installation details
    """
    try:
        service = get_manifest_integration_service()
        success = service.install_plugin_ui_from_manifest(plugin_name)

        if success:
            return {
                "status": "success",
                "plugin": plugin_name,
                "message": "UI component installed successfully",
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to install UI for plugin: {plugin_name}",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error installing UI for plugin {plugin_name}: {str(e)}",
        )


@router.get("/status/{plugin_name}", response_model=IntegrationStatusResponse)
async def get_integration_status(plugin_name: str):
    """
    Get the integration status of a plugin based on its manifest.

    Args:
        plugin_name: Name of the plugin to check

    Returns:
        Integration status information
    """
    try:
        service = get_manifest_integration_service()
        status = service.get_manifest_integration_status(plugin_name)

        return IntegrationStatusResponse(
            plugin_name=plugin_name,
            status=status.get("status", "unknown"),
            has_manifest=status.get("has_manifest", False),
            has_ui=status.get("has_ui", False),
            ui_installed=status.get("ui_installed", False),
            plugin_status=status.get("plugin_status", "unknown"),
            last_updated=status.get("last_updated", "1970-01-01T00:00:00Z"),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting integration status for plugin {plugin_name}: {str(e)}",
        )


@router.post("/sync", response_model=SyncResponse)
async def sync_manifest_integrations():
    """
    Synchronize all manifest-based integrations.

    This ensures that all plugins with manifests have their UI components
    properly installed and configured.

    Returns:
        Summary of synchronization results
    """
    try:
        service = get_manifest_integration_service()
        results = service.sync_manifest_integrations()

        return SyncResponse(
            status="completed",
            total_plugins=results["total_plugins"],
            successful=results["successful"],
            failed=results["failed"],
            skipped=results["skipped"],
            details=results["details"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error synchronizing integrations: {str(e)}"
        )


@router.get("/health")
async def get_integration_health():
    """
    Get the health status of the manifest integration system.

    Returns:
        Health check results for the integration system
    """
    try:
        service = get_manifest_integration_service()

        # Check if we can discover plugins
        manifests = service.discover_plugins_with_manifests()

        # Check if we can generate import map
        import_map = service.generate_frontend_import_map()

        return {
            "status": "healthy",
            "manifests_found": len(manifests),
            "import_map_entries": len(import_map),
            "services_available": True,
            "timestamp": "2024-01-01T00:00:00Z",  # Would use actual timestamp
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "services_available": False,
            "timestamp": "2024-01-01T00:00:00Z",  # Would use actual timestamp
        }
