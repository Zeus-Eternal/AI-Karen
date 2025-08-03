import asyncio
import contextlib
from typing import List, Optional


class WebSocketMessage:
    """Represents a message sent or received over the websocket."""
    def __init__(self, content: str, type_: 'MessageType'):
        self.content = content
        self.type = type_


class MessageType:
    """Enumeration of websocket message types."""
    TEXT = "text"
    BINARY = "binary"
    PING = "ping"
    PONG = "pong"
    CLOSE = "close"

class WebSocketGateway:
    """Manage websocket background tasks such as cleanup and heartbeats."""

    def __init__(self, cleanup_interval: float = 30.0, heartbeat_interval: float = 30.0) -> None:
        self.cleanup_interval = cleanup_interval
        self.heartbeat_interval = heartbeat_interval
        self._typing_cleanup_task: Optional[asyncio.Task] = None
        self._presence_cleanup_task: Optional[asyncio.Task] = None
        self._message_cleanup_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._tasks: List[asyncio.Task] = []

    async def start(self) -> None:
        """Start background maintenance tasks."""
        self._typing_cleanup_task = asyncio.create_task(self._cleanup_expired_typing())
        self._presence_cleanup_task = asyncio.create_task(self._cleanup_expired_presence())
        self._message_cleanup_task = asyncio.create_task(self._cleanup_expired_messages())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._tasks = [
            self._typing_cleanup_task,
            self._presence_cleanup_task,
            self._message_cleanup_task,
            self._heartbeat_task,
        ]

    async def shutdown(self) -> None:
        """Cancel and await background tasks."""
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self._tasks.clear()

    async def _cleanup_expired_typing(self) -> None:  # pragma: no cover - loop
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
        except asyncio.CancelledError:
            pass

    async def _cleanup_expired_presence(self) -> None:  # pragma: no cover - loop
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
        except asyncio.CancelledError:
            pass

    async def _cleanup_expired_messages(self) -> None:  # pragma: no cover - loop
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
        except asyncio.CancelledError:
            pass

    async def _heartbeat_loop(self) -> None:  # pragma: no cover - loop
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
        except asyncio.CancelledError:
            pass
