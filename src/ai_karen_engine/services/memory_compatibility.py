"""Transformation utilities for memory service compatibility with the web UI."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ai_karen_engine.models.web_ui_types import WebUIMemoryQuery, WebUIMemoryEntry
from ai_karen_engine.api_routes.memory_routes import QueryMemoryRequest
from ai_karen_engine.database.memory_manager import MemoryEntry
from ai_karen_engine.services.memory_service import UISource


def convert_datetime_to_js_timestamp(dt: datetime) -> int:
    """Convert ``datetime`` to JavaScript-compatible timestamp in milliseconds."""
    return int(dt.timestamp() * 1000)


def ensure_js_timestamp(value: Any) -> int:
    """Ensure the given timestamp-like value is a JS timestamp in milliseconds."""
    if isinstance(value, datetime):
        return convert_datetime_to_js_timestamp(value)
    if isinstance(value, (int, float)):
        # treat numbers > 1e12 as already in ms
        if value > 1e12:
            return int(value)
        return int(value * 1000)
    return convert_datetime_to_js_timestamp(datetime.utcnow())


def sanitize_metadata(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Ensure metadata is a dictionary and JSON serialisable."""
    if not isinstance(metadata, dict):
        return {}
    cleaned: Dict[str, Any] = {}
    for key, val in metadata.items():
        if not isinstance(key, str):
            continue
        cleaned[key] = val
    return cleaned


async def transform_web_ui_memory_query(web_ui_query: WebUIMemoryQuery) -> QueryMemoryRequest:
    """Transform a ``WebUIMemoryQuery`` to backend ``QueryMemoryRequest``."""
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    if web_ui_query.time_range:
        if len(web_ui_query.time_range) == 2:
            time_range_start, time_range_end = tuple(web_ui_query.time_range)
    return QueryMemoryRequest(
        text=web_ui_query.text,
        session_id=web_ui_query.session_id,
        conversation_id=None,
        ui_source=UISource.WEB,
        memory_types=[],
        tags=web_ui_query.tags or [],
        importance_range=None,
        only_user_confirmed=True,
        only_ai_generated=False,
        time_range_start=time_range_start,
        time_range_end=time_range_end,
        top_k=web_ui_query.top_k or 5,
        result_limit=None,
        similarity_threshold=web_ui_query.similarity_threshold or 0.7,
        include_embeddings=False,
    )


async def transform_memory_entries_to_web_ui(entries: List[MemoryEntry]) -> List[WebUIMemoryEntry]:
    """Convert a list of backend ``MemoryEntry`` objects to ``WebUIMemoryEntry``."""
    results: List[WebUIMemoryEntry] = []
    for entry in entries:
        results.append(
            WebUIMemoryEntry(
                id=str(entry.id),
                content=entry.content,
                metadata=sanitize_metadata(entry.metadata),
                timestamp=ensure_js_timestamp(entry.timestamp),
                similarity_score=entry.similarity_score,
                tags=[t.strip().lower() for t in entry.tags if isinstance(t, str) and t.strip()],
                user_id=entry.user_id,
                session_id=entry.session_id,
            )
        )
    return results
