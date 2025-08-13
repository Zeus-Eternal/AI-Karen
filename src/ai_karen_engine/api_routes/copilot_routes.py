from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter(tags=["copilot"])


class ContextHit(BaseModel):
    id: str
    text: str
    preview: Optional[str] = None
    score: float
    tags: List[str] = Field(default_factory=list)
    recency: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    importance: int = Field(5, ge=1, le=10)
    decay_tier: str = Field("short")
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: str
    org_id: Optional[str] = None


class SuggestedAction(BaseModel):
    type: str = Field(
        ..., examples=["add_task", "pin_memory", "open_doc", "export_note"]
    )
    params: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(0.8, ge=0.0, le=1.0)
    description: Optional[str] = None


class AssistRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    org_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=8000)
    top_k: int = Field(6, ge=1, le=50)
    context: Dict[str, Any] = Field(default_factory=dict)


class AssistResponse(BaseModel):
    answer: str
    context: List[ContextHit] = Field(default_factory=list)
    actions: List[SuggestedAction] = Field(default_factory=list)
    timings: Dict[str, float]
    correlation_id: str


def get_correlation_id(request: Request) -> str:
    return request.headers.get("X-Correlation-Id", "")


@router.post("/assist", response_model=AssistResponse)
async def copilot_assist(
    request: AssistRequest, http_request: Request
) -> AssistResponse:
    correlation_id = get_correlation_id(http_request)
    return AssistResponse(
        answer="Copilot assist is not fully implemented.",
        context=[],
        actions=[],
        timings={"total_ms": 0.0},
        correlation_id=correlation_id,
    )


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "copilot",
        "timestamp": datetime.utcnow().isoformat(),
    }


__all__ = ["router"]
