from typing import Any, Dict, List

from fastapi import APIRouter, Depends
try:
    from pydantic import BaseModel, ConfigDict
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, ConfigDict

from ai_karen_engine.core.dependencies import (
    get_current_tenant_id,
    get_current_user_context,
)
from ai_karen_engine.event_bus import get_event_bus

router = APIRouter()


# Alias core dependencies for convenience
get_current_user = get_current_user_context
get_current_tenant = get_current_tenant_id


class EventOut(BaseModel):
    id: str
    capsule: str
    event_type: str
    payload: dict
    risk: float


@router.get("/", response_model=List[EventOut])
async def consume_events(
    current_user: Dict[str, Any] = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
) -> List[EventOut]:
    bus = get_event_bus()
    events = bus.consume(current_user.get("roles", []), tenant_id=tenant_id)
    return [EventOut(**e.__dict__) for e in events]
