import asyncio
from typing import Any, Dict, List

import pytest

from ai_karen_engine.chat.ChatOrchestrator.mixins.core_mixin import ChatCoreMixin
from ai_karen_engine.chat.stream_processor import AsyncStreamProcessor
from ai_karen_engine.api_routes.formatting_routes import (
    FormatRequest,
    format_content,
)
from ai_karen_engine.services.response_formatting_engine import (
    AccessibilityLevel,
    DisplayContext,
    FormatType,
    FormattingContext,
    ResponseFormattingEngine,
)


@pytest.mark.asyncio
async def test_analyze_content_structure_detects_code_citations_and_density() -> None:
    engine = ResponseFormattingEngine()
    content = """# Title

Use this endpoint:
```python
def handler():
    return {"ok": True}
```

See [Docs](https://example.com/docs) and https://example.com/more
"""
    analysis = await engine.analyze_content_structure(content)
    assert analysis["code_blocks"]
    assert analysis["citations"]
    assert analysis["reading_time"] >= 1
    assert analysis["technical_density"] > 0


@pytest.mark.asyncio
async def test_format_response_repairs_markdown_and_code_fences() -> None:
    engine = ResponseFormattingEngine()
    raw = "Title: Quick Guide\n- item one\n- item two\n```\\nprint('x')\\n```"
    context = FormattingContext(
        display_context=DisplayContext.DESKTOP,
        accessibility_level=AccessibilityLevel.BASIC,
    )
    result = await engine.format_response(raw, context)
    assert "# Quick Guide" in result.content
    assert "```python" in result.content or "```text" in result.content
    assert result.metadata["format_type"] == result.format_type.value


@pytest.mark.asyncio
async def test_search_answer_appends_deduplicated_sources() -> None:
    engine = ResponseFormattingEngine()
    raw = "Latest update from [Site](https://example.com/a) and again https://example.com/a."
    context = FormattingContext(display_context=DisplayContext.DESKTOP)
    result = await engine.format_response(raw, context)
    assert result.format_type in {FormatType.SEARCH_ANSWER, FormatType.STANDARD_MARKDOWN}
    assert "## Sources" in result.content
    assert result.content.count("https://example.com/a") <= 2


@pytest.mark.asyncio
async def test_accessibility_and_display_modes() -> None:
    engine = ResponseFormattingEngine()
    raw = "## Section\n\nParagraph with [link](https://example.com)."

    mobile = await engine.format_response(
        raw,
        FormattingContext(display_context=DisplayContext.MOBILE),
    )
    assert mobile.format_type == FormatType.MOBILE_COMPACT

    terminal = await engine.format_response(
        raw,
        FormattingContext(display_context=DisplayContext.TERMINAL),
    )
    assert terminal.format_type == FormatType.TERMINAL_PLAIN
    assert "link (https://example.com)" in terminal.content

    accessible = await engine.format_response(
        raw,
        FormattingContext(accessibility_level=AccessibilityLevel.FULL),
    )
    assert "screen_reader_text" in accessible.accessibility_features
    assert accessible.accessibility_features.get("section_count", 0) >= 1


@pytest.mark.asyncio
async def test_formatting_route_uses_canonical_engine() -> None:
    request = FormatRequest(
        content="Title: Route Test\n- one\n- two\nhttps://example.com",
        display_context="desktop",
        accessibility_level="basic",
    )
    response = await format_content(request)
    assert response.formatted_content
    assert response.format_type
    assert isinstance(response.metadata, dict)


class _DummyCore(ChatCoreMixin):
    def __init__(self) -> None:
        self.formatting_engine = ResponseFormattingEngine()
        self.response_policy_enforcer = None

    def _build_formatting_context(
        self,
        turn_context: Any,
        *,
        content_length: int = 0,
    ) -> FormattingContext:
        return FormattingContext(
            display_context=DisplayContext.DESKTOP,
            accessibility_level=AccessibilityLevel.BASIC,
            content_length=content_length,
        )


@pytest.mark.asyncio
async def test_core_mixin_formatting_payload_contract() -> None:
    core = _DummyCore()
    turn_context = type("TurnContext", (), {"message": "Write a full answer"})()
    content, payload = await core._format_response_with_engine(
        "Title: Answer\n- a\n- b\nhttps://example.com",
        turn_context,
    )
    assert content
    assert payload.get("formatted") is True
    assert payload.get("render_type")
    assert isinstance(payload.get("formatting", {}).get("sections"), list)


class _MetricHandle:
    def labels(self, **_: Any) -> "_MetricHandle":
        return self

    def inc(self, *_: Any, **__: Any) -> None:
        return None

    def observe(self, *_: Any, **__: Any) -> None:
        return None


class _MetricStub:
    def register_counter(self, *_: Any, **__: Any) -> _MetricHandle:
        return _MetricHandle()

    def register_histogram(self, *_: Any, **__: Any) -> _MetricHandle:
        return _MetricHandle()


class _StructuredLoggerStub:
    def log_event(self, **_: Any) -> None:
        return None

    def log_error(self, **_: Any) -> None:
        return None


@pytest.mark.asyncio
async def test_stream_processor_emits_formatted_completion_metadata() -> None:
    processor = AsyncStreamProcessor()
    processor.metrics_manager = _MetricStub()
    processor.structured_logger = _StructuredLoggerStub()
    await processor.initialize()
    session_id = await processor.create_stream_session(
        user_id="u1",
        response_id="r1",
        metadata={"display_context": "desktop", "accessibility_level": "basic"},
    )

    async def fake_stream(**_: Any):
        for token in ["Hello ", "world."]:
            yield token

    processor._generate_response_stream = fake_stream  # type: ignore[assignment]
    processor._send_chunk = lambda chunk: asyncio.sleep(0)  # type: ignore[assignment]

    chunks: List[Any] = []
    async for chunk in processor.process_streaming_response(
        messages=[{"role": "user", "content": "tell me"}],
        model="m",
        temperature=0.2,
        max_tokens=20,
        session_id=session_id,
        user_id="u1",
        response_id="r1",
    ):
        chunks.append(chunk)

    assert chunks
    last = chunks[-1]
    assert last.finished is True
    assert last.metadata.get("formatted") is True
    assert "formatting" in last.metadata
    await processor.shutdown()
