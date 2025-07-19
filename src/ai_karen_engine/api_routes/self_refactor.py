from __future__ import annotations

import pathlib

try:
    from pydantic import BaseModel
except Exception:  # pragma: no cover - optional
    from ai_karen_engine.pydantic_stub import BaseModel

from ai_karen_engine.self_refactor.engine import SelfRefactorEngine

router = __import__("fastapi").APIRouter()

ENGINE_ROOT = pathlib.Path(__file__).resolve().parents[2]


class ApproveRequest(BaseModel):
    review_id: str


@router.post("/self_refactor/approve")
def approve_review(
    req: ApproveRequest, request: __import__("fastapi").Request
) -> dict:
    """Apply a queued self-refactor review. Admin only."""
    roles = getattr(request.state, "roles", [])
    if "admin" not in roles:
        raise (__import__("fastapi").HTTPException)(status_code=403, detail="Forbidden")
    engine = SelfRefactorEngine(repo_root=ENGINE_ROOT)
    engine.apply_review(req.review_id)
    return {"status": "applied", "review_id": req.review_id}

