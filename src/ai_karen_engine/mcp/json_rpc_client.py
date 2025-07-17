"""JSON-RPC client implementation for MCP."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Optional

try:
    import httpx
except Exception:  # pragma: no cover - optional dep
    httpx = None

from .base import BaseMCPClient


class JSONRPCClient(BaseMCPClient):
    """Perform JSON-RPC calls to services in the registry."""

    def call(self, service: str, method: str, params: Optional[Dict] = None, token: str = "") -> Any:
        svc = self.registry.lookup(service)
        if not svc or svc.get("kind") != "jsonrpc":
            raise ValueError(f"Service '{service}' not found")
        self._auth(service, token, svc.get("roles"))
        if httpx is None:
            raise RuntimeError("httpx is required for JSONRPCClient")
        payload = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": method, "params": params or {}}
        start = time.time()
        try:
            resp = httpx.post(svc["endpoint"], json=payload, timeout=svc.get("timeout", 10))
            resp.raise_for_status()
            self._record_metric(service, time.time() - start, True)
            data = resp.json()
            if "error" in data:
                raise RuntimeError(data["error"])
            return data.get("result")
        except Exception:
            self._record_metric(service, time.time() - start, False)
            raise

