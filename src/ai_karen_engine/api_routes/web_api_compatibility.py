"""Compatibility routes for the Kari web UI."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api", tags=["web-api-compatibility"], include_in_schema=False)

@router.get("/compat", response_class=JSONResponse)
async def compatibility_root() -> dict:
    """Simple endpoint to confirm compatibility layer is active."""
    return {"message": "Kari AI web API compatibility enabled"}

