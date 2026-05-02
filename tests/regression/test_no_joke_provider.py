from pathlib import Path


def test_no_joke_provider_symbol():
    for path in Path("src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "JokeProvider" not in text
