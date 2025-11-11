from pathlib import Path


def test_ui_launcher_directories_are_curated():
    ui_dir = Path(__file__).resolve().parents[1] / "ui_launchers"
    directories = {p.name for p in ui_dir.iterdir() if p.is_dir()}
    expected = {"common", "desktop_ui", "web_ui", "admin_ui"}
    assert directories.issuperset(expected)
    assert directories == expected
