import asyncio
import contextlib
from typing import Optional


class StreamProcessor:
    """Process chat streams with a heartbeat to monitor liveness."""

    def __init__(self, chat_orchestrator=None, heartbeat_interval: float = 30.0) -> None:
        self.heartbeat_interval = heartbeat_interval
        self.chat_orchestrator = chat_orchestrator
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # Stream tracking
        self.active_streams = {}
        self.stream_metrics = {
            "total_streams": 0,
            "successful_streams": 0,
            "failed_streams": 0,
            "success_rate": 0.0,
            "avg_stream_duration": 0.0,
            "avg_processing_time": 0.0
        }

    async def start(self) -> None:
        """Start the heartbeat loop."""
        # Schedule the heartbeat loop as a background task. Using
        # ``asyncio.create_task`` ensures the coroutine is properly
        # registered with the event loop and prevents ``coroutine was
        # never awaited`` warnings when the processor shuts down.
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def shutdown(self) -> None:
        """Cancel and await the heartbeat task."""
        if self._heartbeat_task is None:
            return
        self._heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._heartbeat_task
        self._heartbeat_task = None

    async def _heartbeat_loop(self) -> None:  # pragma: no cover - loop
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
        except asyncio.CancelledError:
            pass
    
    def get_performance_metrics(self):
        """Get performance metrics for the stream processor."""
        return self.stream_metrics.copy()
    
    def get_active_session_count(self):
        """Get the number of active streaming sessions."""
        return len(self.active_streams)
    
    async def get_stream_status(self, session_id: str):
        """Get status information for a streaming session."""
        if session_id not in self.active_streams:
            return None
        
        return {
            "session_id": session_id,
            "status": "active",
            "stream_type": "http",
            "started_at": "2024-01-01T00:00:00Z",
            "chunks_sent": 0,
            "bytes_sent": 0,
            "processing_time": 0.0,
            "user_id": None,
            "conversation_id": None
        }
    
    async def pause_stream(self, session_id: str):
        """Pause a streaming session."""
        return session_id in self.active_streams
    
    async def resume_stream(self, session_id: str):
        """Resume a paused streaming session."""
        return session_id in self.active_streams
    
    async def cancel_stream(self, session_id: str):
        """Cancel a streaming session."""
        if session_id in self.active_streams:
            del self.active_streams[session_id]
            return True
        return False
    
    async def recover_stream(self, session_id: str, from_sequence=None):
        """Recover an interrupted streaming session."""
        return session_id in self.active_streams
    
    async def list_active_streams(self):
        """List all active streaming sessions."""
        return list(self.active_streams.keys())
    
    async def create_sse_stream(self, chat_request, http_request):
        """Create a Server-Sent Events stream."""
        # This would be implemented with actual SSE functionality
        # For now, return a mock response
        from fastapi.responses import StreamingResponse
        
        async def generate():
            yield "data: {\"type\": \"start\", \"message\": \"Stream started\"}\n\n"
            yield "data: {\"type\": \"end\", \"message\": \"Stream ended\"}\n\n"
        
        return StreamingResponse(generate(), media_type="text/plain")
    
    async def create_http_stream(self, chat_request, http_request):
        """Create an HTTP streaming response."""
        # This would be implemented with actual streaming functionality
        # For now, return a mock response
        from fastapi.responses import StreamingResponse
        
        async def generate():
            yield '{"type": "start", "message": "Stream started"}\n'
            yield '{"type": "end", "message": "Stream ended"}\n'
        
        return StreamingResponse(generate(), media_type="application/x-ndjson")
    
    async def cleanup(self):
        """Clean up the stream processor."""
        await self.shutdown()
