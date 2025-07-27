try:
    from fastapi import APIRouter
except Exception:  # pragma: no cover
    from ai_karen_engine.fastapi_stub import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Basic health check for UIs."""
    return {"status": "ok"}
