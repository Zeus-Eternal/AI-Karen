"""Session helpers for the Streamlit UI."""

from __future__ import annotations

import os
import streamlit as st

API_URL = os.getenv("KARI_API_URL", "http://localhost:8000")


def _verify_token(token: str) -> dict | None:
    """Return user context for ``token`` or ``None`` if invalid."""
    try:
        import httpx  # imported lazily to avoid hard dependency during tests

        resp = httpx.get(
            f"{API_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def _load_token() -> str | None:
    """Load token from ``session_state`` or query params."""
    token = st.session_state.get("token")
    if not token:
        params = st.experimental_get_query_params()
        if params.get("token"):
            token = params["token"][0]
            st.session_state["token"] = token
    return token


def get_user_context() -> dict:
    """Return verified user context and set ``st.session_state['roles']``."""

    st.session_state.pop("roles", None)  # remove defaults to prevent spoofing
    token = _load_token()
    ctx = {"user_id": None, "roles": [], "token": token}
    if token:
        data = _verify_token(token)
        if data:
            ctx["user_id"] = data.get("user_id") or data.get("sub")
            ctx["roles"] = list(data.get("roles", []))
    st.session_state["roles"] = ctx["roles"]
    return ctx


def store_token(token: str) -> None:
    """Persist ``token`` in session and browser query params."""

    st.session_state["token"] = token
    st.experimental_set_query_params(token=token)
