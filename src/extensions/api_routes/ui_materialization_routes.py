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
        pipeline = get_ui_pipeline()

        # Discover plugins to get the specific plugin's metadata
        ui_plugins = await pipeline.discover_ui_plugins()
        plugin_ui = next((p for p in ui_plugins if p["plugin_id"] == plugin_id), None)

        if not plugin_ui:
            raise HTTPException(
                status_code=404,
                detail=f"Plugin '{plugin_id}' not found or does not declare UI capabilities",
            )

        # Materialize artifacts for the plugin
        result = await pipeline.materialize_plugin(plugin_ui)

        return {
            "status": "success",
            "data": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to materialize artifacts for {plugin_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to materialize artifacts: {str(e)}",
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
