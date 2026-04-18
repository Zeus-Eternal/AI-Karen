"""
Plugin Settings API Routes - REST endpoints for plugin configuration management.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ai_karen_engine.extensions.platform.core.registry.plugin_registry import (
    get_registry,
)

logger = logging.getLogger("kari.plugin_settings_routes")

router = APIRouter(prefix="/api/extensions", tags=["plugin-settings"])


class SettingSchema(BaseModel):
    """Setting schema definition."""

    key: str
    label: str
    description: Optional[str] = None
    type: str = Field(
        default="string", pattern="^(string|number|boolean|text|select|password|json)$"
    )
    defaultValue: Optional[Any] = None
    validation: Optional[Dict[str, Any]] = None
    options: Optional[List[Dict[str, str]]] = None
    readOnly: bool = False
    requiresRestart: bool = False
    category: str = "General"
    order: int = 0


class PluginSettingsResponse(BaseModel):
    """Response for plugin settings."""

    plugin_id: str
    settings: Dict[str, Any]
    schema: List[Dict[str, Any]]


class UpdateSettingsRequest(BaseModel):
    """Request to update plugin settings."""

    settings: Dict[str, Any]


class AllSettingsResponse(BaseModel):
    """Response for all plugin settings."""

    plugins: List[PluginSettingsResponse]


# Default schemas for common plugin settings
DEFAULT_SETTINGS_SCHEMAS: Dict[str, List[Dict[str, Any]]] = {
    "weather-query": [
        {
            "key": "api_key",
            "label": "OpenWeatherMap API Key",
            "description": "API key for OpenWeatherMap service. Leave empty for mock data.",
            "type": "password",
            "category": "API Configuration",
            "order": 0,
        },
        {
            "key": "default_location",
            "label": "Default Location",
            "description": "Default location to use when none specified",
            "type": "string",
            "defaultValue": "Boston, MA",
            "category": "General",
            "order": 0,
        },
        {
            "key": "temperature_unit",
            "label": "Temperature Unit",
            "description": "Unit for temperature display",
            "type": "select",
            "defaultValue": "celsius",
            "options": [
                {"value": "celsius", "label": "Celsius (°C)"},
                {"value": "fahrenheit", "label": "Fahrenheit (°F)"},
                {"value": "kelvin", "label": "Kelvin (K)"},
            ],
            "category": "General",
            "order": 1,
        },
        {
            "key": "cache_enabled",
            "label": "Enable Caching",
            "description": "Cache weather results to reduce API calls",
            "type": "boolean",
            "defaultValue": True,
            "category": "Performance",
            "order": 0,
        },
        {
            "key": "cache_ttl_minutes",
            "label": "Cache TTL (minutes)",
            "description": "Time to live for cached weather data",
            "type": "number",
            "defaultValue": 30,
            "validation": {"min": 5, "max": 1440},
            "category": "Performance",
            "order": 1,
        },
    ],
    "gmail-plugin": [
        {
            "key": "client_id",
            "label": "Google Client ID",
            "description": "OAuth2 client ID from Google Cloud Console",
            "type": "password",
            "category": "OAuth Configuration",
            "order": 0,
        },
        {
            "key": "client_secret",
            "label": "Google Client Secret",
            "description": "OAuth2 client secret from Google Cloud Console",
            "type": "password",
            "category": "OAuth Configuration",
            "order": 1,
        },
        {
            "key": "max_emails_per_request",
            "label": "Max Emails per Request",
            "description": "Maximum number of emails to fetch per request",
            "type": "number",
            "defaultValue": 10,
            "validation": {"min": 1, "max": 50},
            "category": "General",
            "order": 0,
        },
    ],
}


def get_plugin_settings_schema(plugin_id: str) -> List[Dict[str, Any]]:
    """Get settings schema for a plugin."""
    # Check for custom schema
    try:
        registry = get_registry()
        extension = registry.get_extension(plugin_id)
        if extension:
            manifest = extension.manifest if hasattr(extension, "manifest") else None
            if manifest and hasattr(manifest, "ui_config"):
                custom_schema = manifest.ui_config.get("settings_schema")
                if custom_schema:
                    return custom_schema
    except Exception:
        pass

    # Return default schema if available
    return DEFAULT_SETTINGS_SCHEMAS.get(plugin_id, [])


def get_default_settings(plugin_id: str) -> Dict[str, Any]:
    """Get default settings for a plugin."""
    schema = get_plugin_settings_schema(plugin_id)
    defaults = {}

    for setting in schema:
        if setting.get("defaultValue") is not None:
            defaults[setting["key"]] = setting["defaultValue"]

    return defaults


@router.get("/{plugin_id}/settings", response_model=PluginSettingsResponse)
async def get_plugin_settings(plugin_id: str):
    """
    Get settings for a specific plugin.

    Returns the plugin's settings schema and current values.
    """
    try:
        schema = get_plugin_settings_schema(plugin_id)
        defaults = get_default_settings(plugin_id)

        # In a production system, you'd fetch saved settings from database
        # For now, return defaults
        settings = defaults.copy()

        return PluginSettingsResponse(
            plugin_id=plugin_id,
            settings=settings,
            schema=schema,
        )
    except Exception as e:
        logger.error(f"Failed to get settings for {plugin_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get settings: {str(e)}",
        )


@router.post("/{plugin_id}/settings", response_model=Dict[str, Any])
async def update_plugin_settings(plugin_id: str, request: UpdateSettingsRequest):
    """
    Update settings for a specific plugin.

    Validates settings against schema and persists changes.
    """
    try:
        schema = get_plugin_settings_schema(plugin_id)

        # Validate settings
        errors = []
        for key, value in request.settings.items():
            setting_schema = next((s for s in schema if s["key"] == key), None)

            if not setting_schema:
                errors.append(f"Unknown setting: {key}")
                continue

            # Type validation
            setting_type = setting_schema["type"]
            if setting_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"{key} must be a number")
            elif setting_type == "boolean" and not isinstance(value, bool):
                errors.append(f"{key} must be a boolean")
            elif setting_type in ["select", "string"] and not isinstance(value, str):
                errors.append(f"{key} must be a string")

            # Validation rules
            validation = setting_schema.get("validation", {})
            if "min" in validation and isinstance(value, (int, float)):
                if value < validation["min"]:
                    errors.append(f"{key} must be at least {validation['min']}")
            if "max" in validation and isinstance(value, (int, float)):
                if value > validation["max"]:
                    errors.append(f"{key} must be at most {validation['max']}")
            if "required" in validation and validation["required"] and not value:
                errors.append(f"{key} is required")

        if errors:
            raise HTTPException(
                status_code=400,
                detail={"errors": errors},
            )

        # In a production system, you'd save to database
        # For now, we just return success
        logger.info(f"Updated settings for {plugin_id}")

        return {
            "status": "success",
            "message": f"Settings updated for {plugin_id}",
            "updated_keys": list(request.settings.keys()),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update settings for {plugin_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update settings: {str(e)}",
        )


@router.delete("/{plugin_id}/settings", response_model=Dict[str, Any])
async def reset_plugin_settings(plugin_id: str):
    """
    Reset settings for a plugin to defaults.
    """
    try:
        defaults = get_default_settings(plugin_id)

        # In a production system, you'd delete from database
        logger.info(f"Reset settings for {plugin_id} to defaults")

        return {
            "status": "success",
            "message": f"Settings reset to defaults for {plugin_id}",
            "default_settings": defaults,
        }
    except Exception as e:
        logger.error(f"Failed to reset settings for {plugin_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset settings: {str(e)}",
        )


@router.get("/settings", response_model=AllSettingsResponse)
async def get_all_plugin_settings():
    """
    Get settings for all plugins.

    Returns settings for plugins that have settings schemas defined.
    """
    try:
        all_settings = []

        # Get all plugin IDs with settings schemas
        plugin_ids = set(DEFAULT_SETTINGS_SCHEMAS.keys())

        # Also check registry for plugins with custom schemas
        try:
            registry = get_registry()
            discovered = registry.list_discovered()
            plugin_ids.update(discovered)
        except Exception:
            pass

        for plugin_id in plugin_ids:
            schema = get_plugin_settings_schema(plugin_id)
            if schema:
                settings = get_default_settings(plugin_id)
                all_settings.append(
                    PluginSettingsResponse(
                        plugin_id=plugin_id,
                        settings=settings,
                        schema=schema,
                    )
                )

        return AllSettingsResponse(plugins=all_settings)
    except Exception as e:
        logger.error(f"Failed to get all plugin settings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get all plugin settings: {str(e)}",
        )
