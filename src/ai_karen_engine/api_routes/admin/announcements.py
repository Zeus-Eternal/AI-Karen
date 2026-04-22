from datetime import datetime
from typing import List

try:
    from fastapi import APIRouter
except ImportError:
    from ai_karen_engine.fastapi_stub import APIRouter

from ai_karen_engine.utils.dependency_checks import import_pydantic

# Import Pydantic models
BaseModel, = import_pydantic("BaseModel")

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
