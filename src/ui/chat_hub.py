from __future__ import annotations

import asyncio
import math
import re
import time
from dataclasses import dataclass
from typing import Iterable, List, Optional

try:
    from prometheus_client import Counter, Summary
except Exception:  # pragma: no cover
    class Counter:
        def __init__(self, *a, **k): pass
        def inc(self, *a, **k): pass
    class Summary:
        def __init__(self, *a, **k): pass
        def observe(self, *a, **k): pass

from src.core.prompt_router import PromptRouter


@dataclass
class SlashCommand:
    keyword: str
    description: str
    required_roles: List[str]


class NeuroVault:
    """In-memory short-term memory with exponential decay."""

    def __init__(self) -> None:
        self.records: List[tuple[float, str]] = []

    def add(self, text: str) -> None:
        self.records.append((time.time(), text))

    def recall(self, limit: int = 5) -> List[str]:
        now = time.time()
        weighted = [
            (math.exp(-0.05 * (now - ts) / 86400), text)
            for ts, text in self.records
        ]
        weighted.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in weighted[:limit]]

    def purge(self) -> None:
        self.records.clear()


CHAT_LATENCY = Summary(
    "chat_hub_latency_seconds", "Time spent generating replies"
)
CMD_ERRORS = Counter(
    "slash_command_error_total", "Number of slash command errors"
)


class ChatHub:
    """Route chat messages and manage short-term memory."""

    def __init__(self, router: Optional[PromptRouter] = None) -> None:
        self.router = router or PromptRouter()
        self.memory = NeuroVault()
        self.commands = [
            SlashCommand("help", "List commands", ["user"]),
            SlashCommand("memory", "Show recent memory", ["user"]),
            SlashCommand("purge", "Clear memory", ["dev"]),
        ]

    async def stream_reply(self, text: str, roles: Iterable[str] | None = None):
        roles = set(roles or [])
        start = time.time()
        try:
            if text.startswith("/"):
                reply = self._handle_command(text[1:], roles)
            else:
                self.memory.add(text)
                reply = self.router.generate_reply(text)
                self.memory.add(reply)
            for word in reply.split():
                yield word + " "
                await asyncio.sleep(0)
        finally:
            CHAT_LATENCY.observe(time.time() - start)

    def _handle_command(self, body: str, roles: Iterable[str]) -> str:
        parts = body.split()
        if not parts:
            CMD_ERRORS.inc()
            return "Invalid command"
        keyword = parts[0]
        if not re.fullmatch(r"[a-z0-9_-]+", keyword):
            CMD_ERRORS.inc()
            return "Invalid command"
        cmd = next((c for c in self.commands if c.keyword == keyword), None)
        if not cmd:
            CMD_ERRORS.inc()
            return "Unknown command"
        if cmd.required_roles and not set(cmd.required_roles).intersection(roles):
            CMD_ERRORS.inc()
            return "Access denied"
        if keyword == "help":
            return "\n".join(f"/{c.keyword} - {c.description}" for c in self.commands)
        if keyword == "memory":
            return "\n".join(self.memory.recall()) or "(empty)"
        if keyword == "purge":
            self.memory.purge()
            return "Memory cleared"
        CMD_ERRORS.inc()
        return "Not implemented"

