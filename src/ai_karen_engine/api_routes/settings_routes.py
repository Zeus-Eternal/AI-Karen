from fastapi import APIRouter, Depends

from ai_karen_engine.core.user_prefs import UserPrefs, get_user_prefs

router = APIRouter(prefix="/api", tags=["settings"])

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
