from datetime import datetime
from typing import List

from ai_karen_engine.fastapi_stub import APIRouter as _StubAPIRouter
from ai_karen_engine.pydantic_stub import BaseModel as _StubBaseModel

APIRouter = _StubAPIRouter
BaseModel = _StubBaseModel

try:
    from fastapi import APIRouter as FastAPIAPIRouter
except ImportError:
    pass
else:
    APIRouter = FastAPIAPIRouter

try:
    from pydantic import BaseModel as PydanticBaseModel
except ImportError:
    pass
else:
    BaseModel = PydanticBaseModel

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
