"""
Kari UI Auth Hook - Enterprise-Grade Auth & Session Management
- JWT & session-cookie auth (local or remote)
- RBAC role checking & fast permission hooks
- Device binding and session expiration
- Secure context loader for UI
- Abstract backend for custom API, FastAPI, or SSO
"""

import os
import time
import hashlib
from typing import Optional, Dict, Any, List, Callable
import requests

try:
    import streamlit as st  # pragma: no cover - optional UI dependency
except ModuleNotFoundError:  # pragma: no cover - fallback when Streamlit absent

    class _DummyStreamlit:
        def __init__(self) -> None:
            self.session_state: Dict[str, Any] = {}

    st = _DummyStreamlit()

_CURRENT_USER_CALLBACK: Optional[Callable[[], Optional[Dict[str, Any]]]] = None


def register_current_user_callback(cb: Callable[[], Optional[Dict[str, Any]]]) -> None:
    """Register a callback used by :func:`get_current_user`."""

    global _CURRENT_USER_CALLBACK
    _CURRENT_USER_CALLBACK = cb


# === Security Constants ===
AUTH_SIGNING_KEY = os.getenv("KARI_AUTH_SIGNING_KEY", "change-me-in-prod")
SESSION_DURATION = int(os.getenv("KARI_SESSION_DURATION", "3600"))  # 1 hour
COOKIE_NAME = "kari_session"
JWT_ALGORITHM = "HS256"
API_BASE_URL = os.getenv("KARI_API_BASE_URL", "http://localhost:8000")


# === Device/Browser Fingerprinting ===
def _device_fingerprint(user_agent: str, ip: str) -> str:
    """Hash user agent + IP for device-bound session."""
    data = f"{user_agent}:{ip}".encode()
    return hashlib.sha256(data).hexdigest()


# === JWT/Session Token Management ===
def _sign_token(payload: dict) -> str:
    """HMAC-signed JWT or fallback."""
    import jwt

    return jwt.encode(payload, AUTH_SIGNING_KEY, algorithm=JWT_ALGORITHM)


def _verify_token(token: str) -> Optional[dict]:
    """Verify JWT signature and expiration."""
    import jwt

    try:
        decoded = jwt.decode(token, AUTH_SIGNING_KEY, algorithms=[JWT_ALGORITHM])
        if decoded.get("exp", 0) < time.time():
            return None
        return decoded
    except Exception:
        return None


def create_session(
    user_id: str, roles: List[str], user_agent: str, ip: str, tenant_id: str
) -> str:
    """Create a session JWT token (device-bound, time-limited)."""
    now = int(time.time())
    payload = {
        "sub": user_id,
        "roles": roles,
        "exp": now + SESSION_DURATION,
        "iat": now,
        "device": _device_fingerprint(user_agent, ip),
        "tenant_id": tenant_id,
    }
    return _sign_token(payload)


def validate_session(token: str, user_agent: str, ip: str) -> Optional[dict]:
    """Validate session: signature, expiry, device match."""
    decoded = _verify_token(token)
    if not decoded:
        return None
    if decoded.get("device") != _device_fingerprint(user_agent, ip):
        return None
    return decoded


def token_has_role(token: str, required: List[str], user_agent: str, ip: str) -> bool:
    """Check roles embedded in a session token."""
    ctx = validate_session(token, user_agent, ip)
    if not ctx:
        return False
    return bool(set(ctx.get("roles", [])) & set(required))


# === RBAC Fast Check ===
def has_role(user_ctx: dict, role: str) -> bool:
    """Check if user_ctx has at least one matching role."""
    return role in user_ctx.get("roles", [])


def check_permission(user_ctx: dict, required: List[str]) -> bool:
    """Check if user_ctx covers all required roles."""
    roles = set(user_ctx.get("roles", []))
    return roles.issuperset(required)


# === Auth API Integration ===
def api_authenticate(email: str, password: str) -> Optional[dict]:
    """Authenticate user via backend API; returns user_ctx or None."""
    url = f"{API_BASE_URL}/api/auth/login"
    try:
        # Backend expects an email field rather than username
        resp = requests.post(url, json={"email": email, "password": password})
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def api_get_user(token: str) -> Optional[dict]:
    """Get user profile/context for current session token."""
    url = f"{API_BASE_URL}/api/auth/me"
    try:
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def get_current_user() -> Dict[str, Any]:
    """Return the active user context.

    Priority:
    1. Callback registered via :func:`register_current_user_callback`.
    2. ``st.session_state['user_ctx']`` if present (Streamlit).
    3. Anonymous guest context.
    """

    if _CURRENT_USER_CALLBACK is not None:
        try:
            ctx = _CURRENT_USER_CALLBACK()
            if ctx:
                return ctx
        except Exception:
            pass

    if hasattr(st, "session_state") and "user_ctx" in st.session_state:
        return st.session_state["user_ctx"]

    return {"user_id": "anonymous", "name": "Anonymous", "roles": ["guest"]}


# === Secure Context Loader ===
def get_user_context(cookie: str, user_agent: str, ip: str) -> Optional[dict]:
    """Load validated user context from cookie/token."""
    token = cookie
    ctx = validate_session(token, user_agent, ip)
    if ctx:
        return ctx
    # Fallback to remote API if needed
    profile = api_get_user(token)
    if profile:
        return profile
    return None


# === Session Cookie (for Streamlit/FastAPI) ===
def set_session_cookie(response, token: str):
    """Set a secure session cookie on response (Streamlit or FastAPI)."""
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=SESSION_DURATION,
        httponly=True,
        secure=True,
        samesite="Lax",
    )


def clear_session_cookie(response):
    """Remove session cookie."""
    response.delete_cookie(COOKIE_NAME)


# === Public API ===
__all__ = [
    "create_session",
    "validate_session",
    "get_current_user",
    "get_user_context",
    "has_role",
    "check_permission",
    "api_authenticate",
    "api_get_user",
    "register_current_user_callback",
    "set_session_cookie",
    "clear_session_cookie",
    "token_has_role",
]
