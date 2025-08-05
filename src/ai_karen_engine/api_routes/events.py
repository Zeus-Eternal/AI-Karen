from typing import List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ai_karen_engine.event_bus import get_event_bus
from ai_karen_engine.utils.auth import validate_session

router = APIRouter()


class EventOut(BaseModel):
    id: str
    capsule: str
    event_type: str
    payload: dict
    risk: float


def _get_context(request: Request):
    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing token")
    token = auth.split(None, 1)[1]
    ctx = validate_session(token, request.headers.get("user-agent", ""), request.client.host)
    if not ctx:
        raise HTTPException(status_code=401, detail="invalid token")
    return ctx


@router.get("/", response_model=List[EventOut])
async def consume_events(request: Request) -> List[EventOut]:
    ctx = _get_context(request)
    bus = get_event_bus()
    events = bus.consume(ctx.get("roles", []), tenant_id=ctx.get("tenant_id"))
    return [EventOut(**e.__dict__) for e in events]
