from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class UserProfile(BaseModel):
    user_id: str
    name: str | None = None
    email: str | None = None
    preferences: Dict[str, Any] = {}


USER_PROFILES: Dict[str, UserProfile] = {}


@router.get("/users/{user_id}/profile", response_model=UserProfile)
async def get_profile(user_id: str) -> UserProfile:
    profile = USER_PROFILES.get(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
