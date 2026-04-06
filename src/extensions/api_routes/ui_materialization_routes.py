"""
UI Materialization API Routes - Endpoints for UI artifact management.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks

from extensions.core.registry.ui_materialization import get_ui_pipeline

logger = logging.getLogger("kari.ui_materialization_routes")

router = APIRouter(prefix="/api/ui-materialization", tags=["ui-materialization"])


@router.get("/status", response_model=Dict[str, Any])
async def get_materialization_status():
    """
    Get the current status of UI materialization.

    Returns:
        Status of generated artifacts
    """
    try:
        pipeline = get_ui_pipeline()
        status = await pipeline.get_artifact_status()
        return {
            "status": "success",
            "data": status,
        }
    except Exception as e:
        logger.error(f"Failed to get materialization status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get materialization status: {str(e)}",
        )


@router.post("/discover", response_model=Dict[str, Any])
async def discover_ui_plugins():
    """
    Discover all plugins that declare UI capabilities.

    Returns:
        List of UI-capable plugins with their metadata
    """
    try:
        pipeline = get_ui_pipeline()
        plugins = await pipeline.discover_ui_plugins()
        return {
            "status": "success",
            "data": {
                "plugins": plugins,
                "total": len(plugins),
            },
        }
    except Exception as e:
        logger.error(f"Failed to discover UI plugins: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to discover UI plugins: {str(e)}",
        )


@router.post("/materialize", response_model=Dict[str, Any])
async def materialize_all_artifacts(background_tasks: BackgroundTasks):
    """
    Trigger full UI materialization for all plugins.

    This endpoint:
    1. Discovers all UI-capable plugins
    2. Generates/updates UI artifacts (icons, components, menus)
    3. Cleans up stale artifacts
    4. Generates the import map for frontend

    Returns:
        Materialization result summary
    """
    try:
        pipeline = get_ui_pipeline()
        result = await pipeline.materialize_all()
        return {
            "status": "success",
            "data": result,
        }
    except Exception as e:
        logger.error(f"Failed to materialize artifacts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to materialize artifacts: {str(e)}",
        )


@router.post("/materialize/{plugin_id}", response_model=Dict[str, Any])
async def materialize_plugin_artifacts(plugin_id: str):
    """
    Materialize UI artifacts for a specific plugin.

    Args:
        plugin_id: ID of the plugin to materialize

    Returns:
        Materialization result for the plugin
    """
    try:
        # Check if UI is already installed
        import os
        from pathlib import Path

        plugin_repo = Path("ui_launchers/Karen-AI-Theme/src/plugin_repo")
        plugin_dir = plugin_repo / plugin_id

        if plugin_dir.exists() and (plugin_dir / "manifest.json").exists():
            # UI is already installed
            return {
                "status": "success",
                "data": {
                    "message": "UI is already installed",
                    "plugin_id": plugin_id,
                    "state": "installed",
                },
            }

        # Try to install the UI
        from extensions.core.registry.ui_installer import get_ui_service

        ui_service = get_ui_service()
        category = "plugins"  # Default category

        result = ui_service.install_ui(plugin_id, category)

        if result.status == "success":
            return {
                "status": "success",
                "data": {
                    "message": result.message,
                    "plugin_id": plugin_id,
                    "state": result.state.value,
                },
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to install UI: {result.message}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to materialize artifacts for {plugin_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to materialize artifacts: {str(e)}",
        )


@router.post("/install/{plugin_id}", response_model=Dict[str, Any])
async def install_plugin_ui(plugin_id: str):
    """
    Install UI for a specific plugin.

    Args:
        plugin_id: ID of the plugin to install UI for

    Returns:
        Installation result
    """
    try:
        from extensions.core.registry.ui_installer import get_ui_service

        ui_service = get_ui_service()

        # Get plugin category - default to plugins
        category = "plugins"  # Could be made configurable

        result = ui_service.install_ui(plugin_id, category)

        return {
            "status": "success" if result.status == "success" else "error",
            "data": {
                "plugin_id": plugin_id,
                "install_status": result.status.value,
                "message": result.message,
                "state": result.state.value,
                "details": result.details,
            },
        }
    except Exception as e:
        logger.error(f"Failed to install UI for {plugin_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to install UI: {str(e)}",
        )


@router.get("/installed", response_model=Dict[str, Any])
async def list_installed_ui_plugins():
    """
    List all installed UI plugins from plugin_repo.

    Returns:
        List of installed UI plugins
    """
    try:
        from extensions.core.registry.ui_installer import get_ui_service

        ui_service = get_ui_service()
        installed = ui_service.list_installed_ui()

        # Convert to frontend-compatible format
        plugins = []
        for item in installed:
            try:
                # Read manifest to get plugin details
                import os
                from pathlib import Path
                import json

                manifest_path = Path(item["target_path"]) / "manifest.json"
                if manifest_path.exists():
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        manifest = json.load(f)

                    plugins.append(
                        {
                            "plugin_id": item["plugin_id"],
                            "name": manifest.get("id", item["plugin_id"]),
                            "display_name": manifest.get(
                                "display_name", manifest.get("name", item["plugin_id"])
                            ),
                            "description": manifest.get(
                                "description", "No description"
                            ),
                            "version": manifest.get("version", "1.0.0"),
                            "status": "active",  # Assume installed plugins are active
                            "capabilities": manifest.get("capabilities", {}),
                            "ui": manifest.get("ui", {}),
                            "rbac": manifest.get("rbac", {}),
                            "tags": manifest.get("tags", []),
                            "purpose": manifest.get("purpose"),
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to read manifest for {item['plugin_id']}: {e}")
                # Add basic info even if manifest can't be read
                plugins.append(
                    {
                        "plugin_id": item["plugin_id"],
                        "name": item["plugin_id"],
                        "display_name": item["plugin_id"],
                        "description": f"Installed plugin: {item['plugin_id']}",
                        "version": "1.0.0",
                        "status": "active",
                        "capabilities": {"provides_ui": True},
                        "ui": {"has_component": True},
                        "rbac": {"allowed_roles": ["user", "admin", "developer"]},
                        "tags": [],
                        "purpose": "Installed UI plugin",
                    }
                )

        return {
            "status": "success",
            "data": {
                "plugins": plugins,
                "total": len(plugins),
            },
        }
    except Exception as e:
        logger.error(f"Failed to list installed UI plugins: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list installed UI plugins: {str(e)}",
        )


@router.get("/import-map", response_model=Dict[str, Any])
async def get_import_map():
    """
    Get the generated PLUGIN_IMPORT_MAP for the frontend.

    Returns:
        Import map mapping plugin IDs to component import paths
    """
    try:
        pipeline = get_ui_pipeline()
        ui_plugins = await pipeline.discover_ui_plugins()
        import_map = await pipeline.generate_import_map(ui_plugins)

        return {
            "status": "success",
            "data": {
                "import_map": import_map,
                "total_entries": len(import_map),
            },
        }
    except Exception as e:
        logger.error(f"Failed to generate import map: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate import map: {str(e)}",
        )


@router.post("/cleanup", response_model=Dict[str, Any])
async def cleanup_stale_artifacts():
    """
    Clean up stale UI artifacts for inactive plugins.

    Returns:
        List of removed artifacts
    """
    try:
        pipeline = get_ui_pipeline()
        ui_plugins = await pipeline.discover_ui_plugins()
        removed = await pipeline.cleanup_stale_artifacts(ui_plugins)

        return {
            "status": "success",
            "data": {
                "removed_count": len(removed),
                "removed": removed,
            },
        }
    except Exception as e:
        logger.error(f"Failed to cleanup stale artifacts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup stale artifacts: {str(e)}",
        )


@router.get("/plugin/{plugin_id}", response_model=Dict[str, Any])
async def get_plugin_ui_status(plugin_id: str):
    """
    Get UI status for a specific plugin.

    Args:
        plugin_id: ID of the plugin

    Returns:
        UI status for the plugin
    """
    try:
        pipeline = get_ui_pipeline()
        ui_plugins = await pipeline.discover_ui_plugins()
        plugin_ui = next((p for p in ui_plugins if p["plugin_id"] == plugin_id), None)

        if not plugin_ui:
            raise HTTPException(
                status_code=404,
                detail=f"Plugin '{plugin_id}' not found or does not declare UI capabilities",
            )

        return {
            "status": "success",
            "data": plugin_ui,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get UI status for {plugin_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get UI status: {str(e)}",
        )


@router.get("/icons/{plugin_id}", response_model=Dict[str, Any])
async def get_plugin_icons(plugin_id: str):
    """
    Get all icons for a specific plugin.

    Args:
        plugin_id: ID of the plugin

    Returns:
        List of icons with their metadata
    """
    try:
        pipeline = get_ui_pipeline()
        ui_plugins = await pipeline.discover_ui_plugins()
        plugin_ui = next((p for p in ui_plugins if p["plugin_id"] == plugin_id), None)

        if not plugin_ui:
            raise HTTPException(
                status_code=404,
                detail=f"Plugin '{plugin_id}' not found or does not declare UI capabilities",
            )

        icons = plugin_ui.get("icons", [])

        return {
            "status": "success",
            "data": {
                "plugin_id": plugin_id,
                "icons": icons,
                "total": len(icons),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get icons for {plugin_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get icons: {str(e)}",
        )
