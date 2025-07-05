"""Minimal chat hub with slash commands and in-memory NeuroVault."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, AsyncGenerator, Dict, List, Optional

try:
    from prometheus_client import Histogram, Counter

    CHAT_HUB_LATENCY = Histogram(
        "chat_hub_latency_seconds", "Time to generate each reply"
    )
    SLASH_COMMAND_ERROR = Counter(
        "slash_command_error_total", "Slash command errors"
    )
except Exception:  # pragma: no cover - prometheus optional
    class _Metric:
        def observe(self, *a, **k):
            pass

        def inc(self, *a, **k):
            pass

    CHAT_HUB_LATENCY = _Metric()
    SLASH_COMMAND_ERROR = _Metric()


class NeuroVault:
    """Very small in-memory store for recent replies."""

    def __init__(self, max_items: int = 100) -> None:
        self.max_items = max_items
        self._items: List[tuple[float, str]] = []

    def store(self, text: str) -> None:
        self._items.append((time.time(), text))
        if len(self._items) > self.max_items:
            self._items.pop(0)

    def recall(self, limit: Optional[int] = None) -> List[str]:
        items = self._items[-limit:] if limit else self._items
        return [t for _, t in items]

    def purge(self) -> None:
        self._items.clear()


@dataclass
class SlashCommand:
    keyword: str
    description: str
    roles: List[str]
    handler: Callable[["ChatHub"], AsyncGenerator[str, None]]


class ChatHub:
    def __init__(self, router: Any, memory: Optional[NeuroVault] = None) -> None:
        self.router = router
        self.memory = memory or NeuroVault()
        self.commands: Dict[str, SlashCommand] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register_command(
            SlashCommand(
                "help",
                "List available commands",
                ["user"],
                self._cmd_help,
            )
        )
        self.register_command(
            SlashCommand(
                "memory",
                "Show recent memory snippets",
                ["user"],
                self._cmd_memory,
            )
        )
        self.register_command(
            SlashCommand(
                "purge",
                "Clear short-term memory",
                ["dev"],
                self._cmd_purge,
            )
        )

    def register_command(self, cmd: SlashCommand) -> None:
        self.commands[cmd.keyword] = cmd

    async def _cmd_help(self) -> AsyncGenerator[str, None]:
        cmds = [f"/{c.keyword}: {c.description}" for c in self.commands.values()]
        yield "\n".join(cmds)

    async def _cmd_memory(self) -> AsyncGenerator[str, None]:
        yield "\n".join(self.memory.recall()) or "(empty)"

    async def _cmd_purge(self) -> AsyncGenerator[str, None]:
        self.memory.purge()
        yield "Memory cleared"

    async def stream_reply(
        self, text: str, roles: Optional[List[str]] = None
    ) -> AsyncGenerator[str, None]:
        roles = roles or ["user"]
        start = time.time()
        try:
            if text.startswith("/"):
                cmd_name = text.lstrip("/")
                cmd = self.commands.get(cmd_name)
                if not cmd:
                    SLASH_COMMAND_ERROR.inc()
                    yield f"Unknown command: {cmd_name}"
                    return
                if cmd.roles and not any(r in roles for r in cmd.roles):
                    SLASH_COMMAND_ERROR.inc()
                    yield "Permission denied"
                    return
                async for chunk in cmd.handler():
                    yield chunk
                return
            reply = self.router.generate_reply(text)
            self.memory.store(reply)
            yield reply
        finally:
            CHAT_HUB_LATENCY.observe(time.time() - start)


__all__ = ["ChatHub", "SlashCommand", "NeuroVault"]
