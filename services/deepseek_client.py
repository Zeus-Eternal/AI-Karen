"""Simple DeepSeek text generation client."""

from __future__ import annotations

import os

try:  # pragma: no cover - optional dep
    import httpx
except Exception:  # pragma: no cover - optional dep
    httpx = None

API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")


class DeepSeekClient:
    """Minimal DeepSeek API wrapper."""

    def __init__(self, model: str = "deepseek-chat") -> None:
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.model = model

    def generate_text(self, prompt: str, max_tokens: int = 128) -> str:
        if not self.api_key or httpx is None:
            return f"{prompt} (deepseek unavailable)"
        try:
            resp = httpx.post(
                API_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception:
            return f"{prompt} (deepseek error)"
