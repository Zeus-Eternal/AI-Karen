from datetime import datetime
from typing import List

try:
    from fastapi import APIRouter
except ImportError as e:  # pragma: no cover - runtime dependency
    raise ImportError(
        "FastAPI is required for announcement routes. Install via `pip install fastapi`."
    ) from e

try:
    from pydantic import BaseModel
except ImportError as e:  # pragma: no cover - runtime dependency
    raise ImportError(
        "Pydantic is required for announcement routes. Install via `pip install pydantic`."
    ) from e

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
