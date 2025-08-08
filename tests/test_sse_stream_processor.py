import pytest

from src.ai_karen_engine.chat.stream_processor import StreamProcessor


@pytest.mark.asyncio
async def test_sse_stream_headers_and_format():
    processor = StreamProcessor()
    response = await processor.create_sse_stream(None, None)

    assert response is not None
    content_type = response.headers.get("content-type", "")
    assert "text/event-stream" in content_type
    assert response.headers.get("cache-control") == "no-cache"
    assert response.headers.get("connection") == "keep-alive"

    body_text = ""
    async for chunk in response.body_iterator:
        body_text += chunk.decode() if isinstance(chunk, bytes) else chunk
    assert (
        "data: {\"type\": \"start\", \"message\": \"Stream started\"}\n\n" in body_text
    )
    assert (
        "data: {\"type\": \"end\", \"message\": \"Stream ended\"}\n\n" in body_text
    )
