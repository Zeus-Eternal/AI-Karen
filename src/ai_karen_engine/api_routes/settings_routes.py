from fastapi import APIRouter, Depends
from ai_karen_engine.integrations.llm_registry import get_registry
from ai_karen_engine.core.user_prefs import get_user_prefs, UserPrefs

router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/providers")
async def list_providers():
    reg = get_registry()
    return {
        "providers": [
            {
                "id": p.id,
                "models": [m.name for m in reg.models(p.id)],
                "enabled": getattr(p, "enabled", True),
            }
            for p in reg.providers()
        ]
    }

@router.get("/settings")
async def get_settings(user: UserPrefs = Depends(get_user_prefs)):
    return {
        "preferred_model": user.preferred_model,
        "degraded_banner": user.show_degraded_banner,
        "ui": user.ui,
    }
