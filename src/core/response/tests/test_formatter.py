import importlib
import pytest

formatter_mod = importlib.import_module("core.response.formatter")
DRYFormatter = formatter_mod.DRYFormatter


def test_basic_formatting():
    formatter = DRYFormatter(enable_copilotkit=False)
    result = formatter.format(
        "Title",
        "Body text",
        bullets=["one", "two"],
        code="print('hi')",
        language="python",
    )
    assert result == (
        "## Title\n\n"
        "Body text\n\n"
        "- one\n- two\n\n"
        "```python\nprint('hi')\n```"
    )


def test_copilotkit_enhancement(monkeypatch):
    calls = []

    def fake_enhance(text: str) -> str:
        calls.append(text)
        return text + " [enhanced]"

    monkeypatch.setattr(formatter_mod, "enhance_text", fake_enhance)
    formatter = DRYFormatter()
    result = formatter.format("Heading", "Text")
    assert result.endswith("[enhanced]")
    assert calls and calls[0].startswith("## Heading")


def test_copilotkit_unavailable(monkeypatch):
    monkeypatch.setattr(formatter_mod, "enhance_text", None)
    formatter = DRYFormatter()
    result = formatter.format("Heading", "Text")
    assert result == "## Heading\n\nText"
