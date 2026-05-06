from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ai_karen_engine.services.user_prefs import UserPrefs, get_user_prefs
from ai_karen_engine.services.formatting.settings_manager import SettingsManager

router = APIRouter(prefix="/api", tags=["settings"])

class BehaviorSettings(BaseModel):
    memoryDepth: str
    personalityTone: str
    personalityVerbosity: str
    activeListenMode: bool

class NotificationSettings(BaseModel):
    enabled: bool
    alertOnNewInsights: bool
    alertOnSummaryReady: bool

@router.get("/settings")
async def get_settings(user: UserPrefs = Depends(get_user_prefs)):
    return {
        "preferred_provider": user.preferred_provider,
        "preferred_model": user.preferred_model,
        "degraded_banner": user.show_degraded_banner,
        "degraded_status": user.degraded_status,
        "ui": user.ui,
        "active_profile": user.active_profile,
        "available_profiles": user.available_profiles,
        "profile_assignments": user.profile_assignments,
    }

@router.get("/settings/behavior")
async def get_behavior_settings():
    """Get Karen's behavior settings."""
    try:
        settings_manager = SettingsManager()
        return {
            "memoryDepth": settings_manager.get_setting("behavior.memoryDepth", "medium"),
            "personalityTone": settings_manager.get_setting("behavior.personalityTone", "friendly"),
            "personalityVerbosity": settings_manager.get_setting("behavior.personalityVerbosity", "balanced"),
            "activeListenMode": settings_manager.get_setting("behavior.activeListenMode", False),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load behavior settings: {str(e)}")

@router.put("/settings/behavior")
async def update_behavior_settings(settings: BehaviorSettings):
    """Update Karen's behavior settings."""
    try:
        settings_manager = SettingsManager()
        settings_manager.set_setting("behavior.memoryDepth", settings.memoryDepth, save=False)
        settings_manager.set_setting("behavior.personalityTone", settings.personalityTone, save=False)
        settings_manager.set_setting("behavior.personalityVerbosity", settings.personalityVerbosity, save=False)
        settings_manager.set_setting("behavior.activeListenMode", settings.activeListenMode, save=True)
        
        return {
            "status": "success", 
            "message": "Behavior settings updated successfully",
            "behavior": settings.model_dump() if hasattr(settings, "model_dump") else settings.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save behavior settings: {str(e)}")

@router.get("/settings/notifications")
async def get_notification_settings():
    """Get user notification preferences."""
    try:
        settings_manager = SettingsManager()
        return {
            "enabled": settings_manager.get_setting("notifications.enabled", True),
            "alertOnNewInsights": settings_manager.get_setting("notifications.alertOnNewInsights", True),
            "alertOnSummaryReady": settings_manager.get_setting("notifications.alertOnSummaryReady", True),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load notification settings: {str(e)}")

@router.put("/settings/notifications")
async def update_notification_settings(settings: NotificationSettings):
    """Update user notification preferences."""
    try:
        settings_manager = SettingsManager()
        settings_manager.set_setting("notifications.enabled", settings.enabled, save=False)
        settings_manager.set_setting("notifications.alertOnNewInsights", settings.alertOnNewInsights, save=False)
        settings_manager.set_setting("notifications.alertOnSummaryReady", settings.alertOnSummaryReady, save=True)
        
        return {
            "status": "success",
            "message": "Notification settings updated successfully",
            "notifications": settings.model_dump() if hasattr(settings, "model_dump") else settings.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save notification settings: {str(e)}")
