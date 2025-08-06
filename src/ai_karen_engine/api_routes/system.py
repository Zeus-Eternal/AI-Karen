from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_karen_engine.clients.database.duckdb_client import DuckDBClient
from ai_karen_engine.utils.dependency_checks import import_fastapi, import_pydantic

APIRouter, HTTPException = import_fastapi("APIRouter", "HTTPException")
BaseModel = import_pydantic("BaseModel")

router = APIRouter()

db = DuckDBClient()
ANNOUNCE_PATH = Path(__file__).resolve().parents[3] / "data" / "announcements.json"


class Announcement(BaseModel):
    id: str
    title: str
    body: Optional[str] = None
    created_at: Optional[str] = None


class UserProfile(BaseModel):
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    preferences: Dict[str, Any] = {}


@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@router.get("/announcements", response_model=List[Announcement])
def list_announcements(limit: int = 10) -> List[Announcement]:
    if ANNOUNCE_PATH.exists():
        data = json.loads(ANNOUNCE_PATH.read_text())
    else:
        data = []
    return [Announcement(**a) for a in data[:limit]]


@router.get("/users/{user_id}/profile", response_model=UserProfile)
def get_profile(user_id: str) -> UserProfile:
    profile = db.get_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return UserProfile(user_id=user_id, **profile)
