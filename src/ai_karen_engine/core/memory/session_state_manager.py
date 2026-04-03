from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional

from ai_karen_engine.clients.database.redis_client import RedisClient


class SessionStateManager:
    """Redis-backed session continuity store for Stage 2 working memory."""

    def __init__(
        self,
        redis_client: Optional[RedisClient] = None,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        self.redis_client = redis_client
        self.ttl_seconds = ttl_seconds or int(
            os.getenv("KARI_SESSION_STATE_TTL_SECONDS", "3600")
        )

    @staticmethod
    def _normalize_scope_value(value: Optional[str], fallback: str) -> str:
        normalized = str(value or "").strip()
        return normalized or fallback

    async def get_session_state(
        self,
        tenant_id: str,
        user_id: str,
        session_id: str,
    ) -> Dict[str, Any]:
        if not self.redis_client:
            return {}
        tenant_scope = self._normalize_scope_value(tenant_id, "default")
        user_scope = self._normalize_scope_value(user_id, "anonymous")
        session_scope = self._normalize_scope_value(session_id, "default")
        state = self.redis_client.get_session(
            tenant_scope,
            user_scope,
            session_id=session_scope,
        )
        return state if isinstance(state, dict) else {}

    async def put_session_state(
        self,
        tenant_id: str,
        user_id: str,
        session_id: str,
        state: Dict[str, Any],
        ttl_seconds: Optional[int] = None,
    ) -> None:
        if not self.redis_client:
            return
        tenant_scope = self._normalize_scope_value(tenant_id, "default")
        user_scope = self._normalize_scope_value(user_id, "anonymous")
        session_scope = self._normalize_scope_value(session_id, "default")
        payload = dict(state or {})
        payload.setdefault("session_id", session_scope)
        payload.setdefault("updated_at", datetime.utcnow().isoformat())
        self.redis_client.set_session(
            tenant_scope,
            user_scope,
            payload,
            session_id=session_scope,
            ttl_seconds=ttl_seconds or self.ttl_seconds,
        )
