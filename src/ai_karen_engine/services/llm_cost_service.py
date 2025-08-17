"""Utilities for aggregating LLM request costs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from sqlalchemy import func

from ai_karen_engine.database.client import get_db_session_context
from ai_karen_engine.database.models import LLMRequest


@dataclass
class ProviderCostSummary:
    """Aggregated cost information for a provider."""

    provider_name: str
    total_cost: float
    total_requests: int
    avg_latency_ms: float


def get_cost_summary(start: datetime, end: datetime) -> List[ProviderCostSummary]:
    """Return cost summaries per provider between start and end timestamps."""

    with get_db_session_context() as session:
        rows = (
            session.query(
                LLMRequest.provider_name,
                func.coalesce(func.sum(LLMRequest.cost), 0).label("total_cost"),
                func.count(LLMRequest.id).label("total_requests"),
                func.coalesce(func.avg(LLMRequest.latency_ms), 0).label(
                    "avg_latency_ms"
                ),
            )
            .filter(LLMRequest.created_at >= start, LLMRequest.created_at <= end)
            .group_by(LLMRequest.provider_name)
            .all()
        )

        return [ProviderCostSummary(*row) for row in rows]
