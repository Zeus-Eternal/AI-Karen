from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx


class ExtensionAPIClient:
    """Async client for extension management API."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        *,
        timeout: float = 10.0,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.logger = logging.getLogger("extension.api_client")
        self.client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self) -> "ExtensionAPIClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001, D401
        await self.close()

    async def close(self) -> None:
        await self.client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        for attempt in range(self.max_retries + 1):
            try:
                resp = await self.client.request(method, url, headers=headers, **kwargs)
                resp.raise_for_status()
                return resp
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in {401, 403}:
                    raise PermissionError(exc.response.text) from exc
                if 500 <= exc.response.status_code < 600 and attempt < self.max_retries:
                    delay = self.backoff_factor * (2**attempt)
                    await asyncio.sleep(delay)
                    continue
                raise
            except httpx.RequestError as exc:
                if attempt < self.max_retries:
                    delay = self.backoff_factor * (2**attempt)
                    await asyncio.sleep(delay)
                    continue
                raise
        raise RuntimeError("Request failed after retries")

    async def list_extensions(self) -> List[Dict[str, Any]]:
        resp = await self._request("GET", "/extensions")
        return resp.json()

    async def get_extension_status(self, name: str) -> Dict[str, Any]:
        resp = await self._request("GET", f"/extensions/{name}")
        return resp.json()

    async def load_extension(self, name: str) -> Dict[str, Any]:
        resp = await self._request("POST", f"/extensions/{name}/load")
        return resp.json()

    async def unload_extension(self, name: str) -> Dict[str, Any]:
        resp = await self._request("POST", f"/extensions/{name}/unload")
        return resp.json()

    async def reload_extension(self, name: str) -> Dict[str, Any]:
        resp = await self._request("POST", f"/extensions/{name}/reload")
        return resp.json()

    async def discover_extensions(self) -> Dict[str, Any]:
        resp = await self._request("GET", "/extensions/discover")
        return resp.json()

    async def consume_events(self) -> List[Dict[str, Any]]:
        resp = await self._request("GET", "/api/events/")
        return resp.json()

    async def poll_events(self, interval: float = 5.0):
        """Yield events by polling the events API."""
        while True:
            try:
                events = await self.consume_events()
                if events:
                    yield events
            except Exception as exc:  # pragma: no cover - network errors
                self.logger.error("Event polling error: %s", exc)
            await asyncio.sleep(interval)

