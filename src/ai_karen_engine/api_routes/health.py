try:
    from fastapi import APIRouter
except ImportError as e:  # pragma: no cover - runtime dependency
    raise ImportError(
        "FastAPI is required for health routes. Install via `pip install fastapi`."
    ) from e

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Basic health check for UIs."""
    return {"status": "ok"}
