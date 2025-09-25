from pathlib import Path


def test_only_home_references_fetch_announcements():
    pages_dir = Path(__file__).resolve().parents[1] / "ui_launchers" / "streamlit_ui" / "pages"
    found = []
    for py in pages_dir.glob("*.py"):
        text = py.read_text()
        if "fetch_announcements" in text:
            found.append(py.name)
    assert found == ["home.py"]
