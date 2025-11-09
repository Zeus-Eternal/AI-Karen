"""
User preferences API routes for model selection.
Handles user-specific model preferences like last selected model and default model.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ai_karen_engine.core.user_prefs import get_user_prefs, UserPrefs
from ai_karen_engine.services.settings_manager import SettingsManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user-preferences"])

# Pydantic models for request/response
class ModelSelectionPreferences(BaseModel):
    lastSelectedModel: Optional[str] = None
    defaultModel: Optional[str] = None

class UpdatePreferencesRequest(BaseModel):
    lastSelectedModel: Optional[str] = None
    defaultModel: Optional[str] = None

@router.get("/preferences/models", response_model=ModelSelectionPreferences)
async def get_user_model_preferences() -> ModelSelectionPreferences:
    """Get user model selection preferences"""
    try:
        # Try to get user preferences, but handle read-only filesystem gracefully
        try:
            user_prefs = get_user_prefs()
            default_model = user_prefs.preferred_model
        except (OSError, PermissionError) as e:
            logger.warning(f"Could not access user preferences due to filesystem restrictions: {e}")
            # Fallback to basic defaults
            default_model = "llama3.2:latest"
        
        # Try to get settings manager for persistent storage
        try:
            settings_manager = SettingsManager()
            last_selected = settings_manager.get_setting("last_selected_model")
            stored_default = settings_manager.get_setting("default_model")
            if stored_default:
                default_model = stored_default
        except (OSError, PermissionError) as e:
            logger.warning(f"Could not access settings due to filesystem restrictions: {e}")
            last_selected = None
        
        return ModelSelectionPreferences(
            lastSelectedModel=last_selected,
            defaultModel=default_model
        )
    except Exception as e:
        logger.error(f"Failed to get user model preferences: {e}")
        # Return basic defaults instead of failing
        return ModelSelectionPreferences(
            lastSelectedModel=None,
            defaultModel="llama3.2:latest"
        )

@router.put("/preferences/models")
async def update_user_model_preferences(request: UpdatePreferencesRequest) -> Dict[str, str]:
    """Update user model selection preferences"""
    try:
        # Try to get settings manager for persistent storage
        try:
            settings_manager = SettingsManager()
            
            # Update last selected model if provided
            if request.lastSelectedModel is not None:
                settings_manager.set_setting("last_selected_model", request.lastSelectedModel, save=True)
                logger.info(f"Updated last selected model to: {request.lastSelectedModel}")
            
            # Update default model if provided
            if request.defaultModel is not None:
                settings_manager.set_setting("default_model", request.defaultModel, save=True)
                # Also update the main model setting for consistency
                settings_manager.set_setting("model", request.defaultModel, save=True)
                logger.info(f"Updated default model to: {request.defaultModel}")
            
            return {"status": "success", "message": "Preferences updated successfully"}
            
        except (OSError, PermissionError) as e:
            logger.warning(f"Could not save preferences due to filesystem restrictions: {e}")
            # In read-only environments, we can't persist settings but we can acknowledge the request
            return {"status": "acknowledged", "message": "Preferences received but could not be persisted due to read-only filesystem"}
        
    except Exception as e:
        logger.error(f"Failed to update user model preferences: {e}")
        return {"status": "error", "message": f"Failed to update preferences: {str(e)}"}