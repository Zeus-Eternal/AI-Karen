from __future__ import annotations

import pathlib

try:
    from fastapi import APIRouter, HTTPException, Request
except ImportError as e:  # pragma: no cover - runtime dependency
    raise ImportError(
        "FastAPI is required for self-refactor routes. Install via `pip install fastapi`."
    ) from e

try:
    from pydantic import BaseModel
except ImportError as e:  # pragma: no cover - runtime dependency
    raise ImportError(
        "Pydantic is required for self-refactor routes. Install via `pip install pydantic`."
    ) from e

from ai_karen_engine.self_refactor.engine import SelfRefactorEngine

router = APIRouter()

ENGINE_ROOT = pathlib.Path(__file__).resolve().parents[2]


class ApproveRequest(BaseModel):
    review_id: str


@router.post("/self_refactor/approve")
def approve_review(
    req: ApproveRequest, request: Request
) -> dict:
    """Apply a queued self-refactor review. Admin only."""
    roles = getattr(request.state, "roles", [])
    if "admin" not in roles:
        raise HTTPException(status_code=403, detail="Forbidden")
    engine = SelfRefactorEngine(repo_root=ENGINE_ROOT)
    engine.apply_review(req.review_id)
    return {"status": "applied", "review_id": req.review_id}

