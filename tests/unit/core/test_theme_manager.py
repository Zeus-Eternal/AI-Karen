import os
import types
import sys
from pathlib import Path

import ui_logic.themes.theme_manager as tm


def test_get_available_themes(tmp_path, monkeypatch):
    theme_dir = tmp_path / "themes"
    theme_dir.mkdir()
    (theme_dir / "light.css").write_text("body {}")
    (theme_dir / "dark.css").write_text("body {}")
    monkeypatch.setenv("KARI_THEME_CONFIG", str(theme_dir))
    themes = tm.get_available_themes()
    assert themes == {
        "light": str(theme_dir / "light.css"),
        "dark": str(theme_dir / "dark.css"),
    }


def test_set_theme_writes_audit_and_marks_css(tmp_path, monkeypatch):
    theme_dir = tmp_path / "themes"
    theme_dir.mkdir()
    css_file = theme_dir / "light.css"
    css_file.write_text("body {color:red}")
    audit_log = tmp_path / "audit.log"
    monkeypatch.setenv("KARI_THEME_CONFIG", str(theme_dir))
    monkeypatch.setenv("KARI_THEME_AUDIT_LOG", str(audit_log))

    fake_st = types.ModuleType("streamlit")
    recorded = {}

    def markdown(css, unsafe_allow_html=False):
        recorded["css"] = css
        recorded["allow"] = unsafe_allow_html

    fake_st.markdown = markdown
    fake_st.session_state = {}
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)

    tm.set_theme("light", {"user_id": "tester"})

    assert recorded["allow"]
    assert "color:red" in recorded["css"]
    assert audit_log.exists()
    log = audit_log.read_text()
    assert "set_theme" in log
