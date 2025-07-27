from typing import Dict, Any

try:
    from fastapi import APIRouter, HTTPException
except Exception:  # pragma: no cover
    from ai_karen_engine.fastapi_stub import APIRouter, HTTPException

try:
    from pydantic import BaseModel
except Exception:
    from ai_karen_engine.pydantic_stub import BaseModel

from ai_karen_engine.clients.database.duckdb_client import DuckDBClient

router = APIRouter()

db = DuckDBClient()


class UserProfile(BaseModel):
    user_id: str
    name: str | None = None
    email: str | None = None
    preferences: Dict[str, Any] = {}


@router.get("/users/{user_id}/profile", response_model=UserProfile)
async def get_profile(user_id: str) -> UserProfile:
    profile = db.get_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return UserProfile(user_id=user_id, **profile)


@router.put("/users/{user_id}/profile", response_model=UserProfile)
async def save_profile(user_id: str, profile: UserProfile) -> UserProfile:
    data = profile.dict(exclude={"user_id"})
    db.save_profile(user_id, data)
    return UserProfile(user_id=user_id, **data)
