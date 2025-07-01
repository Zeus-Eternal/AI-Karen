from pathlib import Path

try:  # optional dependency
    from jinja2 import Template
except Exception:  # pragma: no cover - optional dep
    Template = None  # type: ignore


async def run(params: dict) -> str:
    """Return a friendly greeting rendered from ``prompt.txt``."""
    prompt_file = Path(__file__).with_name("prompt.txt")
    data = prompt_file.read_text(encoding="utf-8")
    if Template is None:
        return data.strip()
    return Template(data).render()
