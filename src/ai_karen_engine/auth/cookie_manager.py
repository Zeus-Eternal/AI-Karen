"""Cookie management helpers wrapping the simplified auth utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Response

from ai_karen_engine.services import auth_utils


@dataclass(frozen=True)
class CookieManagerConfig:
    """Configuration for session and refresh cookies."""

    session_cookie: str = auth_utils.COOKIE_NAME
    refresh_cookie: str = "refresh_token"


class CookieManager:
    """Facade used by legacy components to manage authentication cookies."""

    def __init__(self, config: Optional[CookieManagerConfig] = None) -> None:
        self.config = config or CookieManagerConfig()

    def set_session_cookie(self, response: Response, token: str, *, max_age: int = 86400) -> None:
        auth_utils.set_session_cookie(response, token, max_age=max_age)

    def set_refresh_cookie(self, response: Response, token: str) -> None:
        auth_utils.set_refresh_token_cookie(response, token)

    def clear_cookies(self, response: Response) -> None:
        auth_utils.clear_auth_cookies(response)

    def get_session_token(self, request) -> Optional[str]:  # pragma: no cover - simple proxy
        return auth_utils.get_session_token(request)

    def get_refresh_token(self, request) -> Optional[str]:  # pragma: no cover - simple proxy
        return auth_utils.get_refresh_token(request)

    def validate_security(self) -> dict:
        return auth_utils.validate_cookie_security()


_instance: CookieManager | None = None


def get_cookie_manager() -> CookieManager:
    """Return a shared :class:`CookieManager` instance."""

    global _instance
    if _instance is None:
        _instance = CookieManager()
    return _instance


__all__ = ["CookieManager", "CookieManagerConfig", "get_cookie_manager"]
