from ai_karen_engine.utils.dependency_checks import import_fastapi

APIRouter = import_fastapi("APIRouter")

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Basic health check for UIs."""
    return {"status": "ok"}
