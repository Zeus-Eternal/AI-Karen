"""
Simple authentication middleware for FastAPI.
"""

try:
    from fastapi import Request, HTTPException
    from fastapi.responses import JSONResponse
except Exception:
    from ai_karen_engine.fastapi_stub import Request, HTTPException, JSONResponse


async def auth_middleware(request: Request, call_next):
    """Simple bearer-token authentication middleware."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)

    token = auth_header.split(" ", 1)[1]
    from ai_karen_engine.utils.auth import validate_session  # local import for tests

    user_data = validate_session(
        token,
        request.headers.get("user-agent", ""),
        request.client.host if request.client else "",
    )
    if not user_data:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)

    request.state.user = user_data.get("sub")
    request.state.roles = user_data.get("roles", [])
    return await call_next(request)