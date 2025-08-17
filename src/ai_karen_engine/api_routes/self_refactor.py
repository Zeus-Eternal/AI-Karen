from __future__ import annotations

import pathlib

from ai_karen_engine.self_refactor.engine import SelfRefactorEngine
from ai_karen_engine.utils.dependency_checks import import_fastapi, import_pydantic

APIRouter, HTTPException, Request = import_fastapi(
    "APIRouter", "HTTPException", "Request"
)
BaseModel = import_pydantic("BaseModel")

router = APIRouter()

ENGINE_ROOT = pathlib.Path(__file__).resolve().parents[2]


class ApproveRequest(BaseModel):
    review_id: str


@router.post("/self_refactor/approve")
def approve_review(req: ApproveRequest, request: Request) -> dict:
    """Apply a queued self-refactor review. Admin only."""
    roles = getattr(request.state, "roles", [])
    if "admin" not in roles:
        raise HTTPException(status_code=403, detail="Forbidden")
    engine = SelfRefactorEngine(repo_root=ENGINE_ROOT)
    engine.apply_review(req.review_id)
    return {"status": "applied", "review_id": req.review_id}
