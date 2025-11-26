"""
Simple bearer token auth dependency for FastAPI.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status


def make_auth_dependency(expected_token: str | None):
    async def verify(request: Request) -> None:
        if not expected_token:
            return
        header = request.headers.get("authorization", "")
        if not header.lower().startswith("bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
        token = header.split(" ", 1)[1]
        if token != expected_token:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")
    return verify

