from datetime import datetime
from typing import List

try:
    from fastapi import APIRouter
except Exception:  # pragma: no cover
    from ai_karen_engine.fastapi_stub import APIRouter

try:
    from pydantic import BaseModel
except Exception:
    from ai_karen_engine.pydantic_stub import BaseModel

router = APIRouter()


class Announcement(BaseModel):
    id: str
    title: str
    body: str
    created_at: datetime


ANNOUNCEMENTS: List[Announcement] = []


@router.get("/announcements", response_model=List[Announcement])
async def list_announcements(limit: int = 10) -> List[Announcement]:
    """Return recent announcements."""
    return ANNOUNCEMENTS[:limit]
