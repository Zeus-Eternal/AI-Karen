"""Generic gRPC client for MCP."""

from __future__ import annotations

import time
from typing import Any

from .base import BaseMCPClient


class GRPCClient(BaseMCPClient):
    """Call gRPC services discovered via the service registry."""

    def call(self, service: str, method: str, payload: bytes, token: str) -> Any:
        svc = self.registry.lookup(service)
        if not svc or svc.get("kind") != "grpc":
            raise ValueError(f"Service '{service}' not found")
        self._auth(service, token, svc.get("roles"))
        start = time.time()
        try:
            import grpc  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dep
            raise RuntimeError("grpcio is required for GRPCClient") from exc
        channel = grpc.insecure_channel(svc["endpoint"])
        stub = channel.unary_unary(method)
        try:
            resp = stub(payload)
            self._record_metric(service, time.time() - start, True)
            return resp
        except Exception:
            self._record_metric(service, time.time() - start, False)
            raise

