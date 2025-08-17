"""Utilities for dispatching registered webhooks."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_karen_engine.database import get_postgres_session
from ai_karen_engine.database.models import Webhook

logger = logging.getLogger(__name__)


async def dispatch_webhook(
    event: str,
    payload: Dict[str, Any],
    session: Optional[AsyncSession] = None,
    http_client: Optional[httpx.AsyncClient] = None,
) -> None:
    """Dispatch an event to all enabled webhooks subscribed to it."""
    close_client = False
    if http_client is None:
        http_client = httpx.AsyncClient()
        close_client = True

    async def _dispatch(db_session: AsyncSession) -> None:
        result = await db_session.execute(
            select(Webhook).where(Webhook.enabled.is_(True))
        )
        for hook in result.scalars():
            events = hook.events or []
            if event not in events:
                continue
            try:
                await http_client.post(hook.url, json={"event": event, "payload": payload})
            except Exception as exc:  # pragma: no cover - network issues
                logger.warning(
                    "Webhook dispatch failed", exc_info=True, extra={"webhook_id": hook.webhook_id}
                )

    try:
        if session is not None:
            await _dispatch(session)
        else:  # pragma: no cover - depends on external DB availability
            async with get_postgres_session() as db_session:
                await _dispatch(db_session)
    finally:
        if close_client:
            await http_client.aclose()
