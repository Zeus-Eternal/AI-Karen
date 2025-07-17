from datetime import datetime
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

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
