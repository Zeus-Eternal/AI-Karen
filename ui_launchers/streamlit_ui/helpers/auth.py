"""Backend authentication helpers for Streamlit UI."""

from __future__ import annotations

import os
import streamlit as st

API_URL = os.getenv("KARI_API_URL", "http://localhost:8000")


def login(email: str, password: str) -> bool:
    """Authenticate against the backend and persist the token."""
    try:
        import httpx  # imported lazily to avoid dependency during tests

        resp = httpx.post(
            f"{API_URL}/api/auth/login",
            # Backend expects an email field
            json={"email": email, "password": password},
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("token")
            if token:
                from .session import store_token

                store_token(token)
                return True
    except Exception:
        pass
    return False
