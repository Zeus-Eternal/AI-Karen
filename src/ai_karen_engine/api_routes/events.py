from typing import List, Dict
from fastapi import APIRouter, HTTPException, Request, status
from ai_karen_engine.event_bus import get_event_bus
from ai_karen_engine.utils.auth import validate_session

router = APIRouter(prefix="/api/events")

@router.get("/")
async def list_events(request: Request) -> List[Dict]:
    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = auth.split(None, 1)[1]
    ctx = validate_session(token, request.headers.get("user-agent", ""), request.client.host)
    if not ctx:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    roles = ctx.get("roles", [])
    tenant_id = ctx.get("tenant_id")
    events = [
        {
            "id": e.id,
            "capsule": e.capsule,
            "type": e.event_type,
            "payload": e.payload,
            "risk": e.risk,
        }
        for e in get_event_bus().consume(roles=roles, tenant_id=tenant_id)
    ]
    return events
