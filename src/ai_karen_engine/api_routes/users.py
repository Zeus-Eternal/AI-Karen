from typing import Dict, Any

import asyncio

try:
    from fastapi import APIRouter, Depends, HTTPException
except ImportError as e:  # pragma: no cover - runtime dependency
    raise ImportError(
        "FastAPI is required for user routes. Install via `pip install fastapi`."
    ) from e

try:
    from pydantic import BaseModel
except ImportError as e:  # pragma: no cover - runtime dependency
    raise ImportError(
        "Pydantic is required for user routes. Install via `pip install pydantic`."
    ) from e

from ai_karen_engine.clients.database.duckdb_client import DuckDBClient
from ai_karen_engine.core.dependencies import get_current_user_context

router = APIRouter()

# Shared DuckDB client instance for dependency injection
_db_client = DuckDBClient()


def get_db() -> DuckDBClient:
    """Dependency that provides a DuckDB client instance."""
    return _db_client


class UserProfile(BaseModel):
    user_id: str
    name: str | None = None
    email: str | None = None
    preferences: Dict[str, Any] = {}


@router.get("/users/{user_id}/profile", response_model=UserProfile)
async def get_profile(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_context),
    db: DuckDBClient = Depends(get_db),
) -> UserProfile:
    # Only allow access to own profile or for admin roles
    if current_user.get("user_id") != user_id and "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not authorized to access this profile")

    profile = await asyncio.to_thread(db.get_profile, user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return UserProfile(user_id=user_id, **profile)


@router.put("/users/{user_id}/profile", response_model=UserProfile)
async def save_profile(
    user_id: str,
    profile: UserProfile,
    current_user: Dict[str, Any] = Depends(get_current_user_context),
    db: DuckDBClient = Depends(get_db),
) -> UserProfile:
    # Only allow modifications to own profile or for admin roles
    if current_user.get("user_id") != user_id and "admin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not authorized to modify this profile")

    data = profile.dict(exclude={"user_id"})
    await asyncio.to_thread(db.save_profile, user_id, data)
    return UserProfile(user_id=user_id, **data)
