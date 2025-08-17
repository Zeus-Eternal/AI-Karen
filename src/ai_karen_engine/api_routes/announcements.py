from datetime import datetime
from typing import List

from ai_karen_engine.utils.dependency_checks import import_fastapi, import_pydantic

APIRouter = import_fastapi("APIRouter")
BaseModel = import_pydantic("BaseModel")

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
