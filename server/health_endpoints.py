# mypy: ignore-errors
"""
Health and status endpoints for Kari FastAPI Server.
Handles health checks, ping, and status endpoints.
"""

import logging
from datetime import datetime, timezone
from fastapi import FastAPI

logger = logging.getLogger("kari")


def register_health_endpoints(app: FastAPI) -> None:
    """Register all health and status endpoints"""
    
    @app.get("/api/ping", tags=["system"])
    async def api_ping():
        from datetime import datetime, timezone
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

    @app.get("/ping", tags=["system"])
    async def root_ping():
        from datetime import datetime, timezone
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

    @app.get("/health", tags=["system"])
    async def root_health():
        # Alias to /api/health summary with minimal payload to keep UI happy
        return {"status": "ok"}

    @app.get("/api/status", tags=["system"])
    async def api_status():
        from datetime import datetime, timezone
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}