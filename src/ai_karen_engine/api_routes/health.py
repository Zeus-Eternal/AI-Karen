from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Basic health check for UIs."""
    return {"status": "ok"}
