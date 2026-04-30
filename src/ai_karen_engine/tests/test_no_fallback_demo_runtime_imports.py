from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = PROJECT_ROOT / "src" / "ai_karen_engine"


def test_fallback_demo_not_imported_by_runtime_modules() -> None:
    """CI guard: runtime modules must not reference the demo module."""
    forbidden = "fallback_demo"
    violations: list[str] = []

    for path in RUNTIME_ROOT.rglob("*.py"):
        rel_path = path.relative_to(PROJECT_ROOT)
        path_text = str(rel_path)

        if "/tests/" in path_text or path_text.endswith("/tests.py"):
            continue

        content = path.read_text(encoding="utf-8")
        if forbidden in content:
            violations.append(path_text)

    assert not violations, (
        "Non-test runtime modules cannot reference fallback_demo: "
        + ", ".join(sorted(violations))
    )
