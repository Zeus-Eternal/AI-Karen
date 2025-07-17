import importlib.util
import sys
import types
from pathlib import Path

import pytest


@pytest.fixture
def config_modules(monkeypatch):
    """Load config modules with a fake ``streamlit`` present."""
    fake_st = types.ModuleType("streamlit")
    fake_st.markdown = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)
    root = Path(__file__).resolve().parents[2]
    env_path = root / "ui_launchers/streamlit_ui/config/env.py"
    theme_path = root / "ui_launchers/streamlit_ui/config/theme.py"

    spec_env = importlib.util.spec_from_file_location("env_mod", env_path)
    env = importlib.util.module_from_spec(spec_env)
    assert spec_env.loader is not None
    spec_env.loader.exec_module(env)

    spec_theme = importlib.util.spec_from_file_location("theme_mod", theme_path)
    theme = importlib.util.module_from_spec(spec_theme)
    assert spec_theme.loader is not None
    spec_theme.loader.exec_module(theme)
    yield env, theme
    monkeypatch.delitem(sys.modules, "streamlit", raising=False)


def test_env_helpers(monkeypatch, config_modules):
    env, _ = config_modules
    monkeypatch.setenv("TEST_BOOL", "true")
    monkeypatch.setenv("TEST_INT", "42")
    assert env.get_bool_setting("TEST_BOOL") is True
    assert env.get_bool_setting("MISSING_BOOL", True) is True
    assert env.get_int_setting("TEST_INT") == 42
    monkeypatch.setenv("TEST_INT", "oops")
    assert env.get_int_setting("TEST_INT", 7) == 7


def test_available_themes_includes_defaults(config_modules):
    _, theme = config_modules
    names = theme.available_themes()
    assert {"light", "dark"}.issubset(set(names))


def test_theme_helpers(monkeypatch, config_modules):
    _, theme = config_modules
    assert theme.theme_exists("light")
    assert not theme.theme_exists("nope")
    monkeypatch.setenv("KARI_UI_THEME", "dark")
    assert theme.get_default_theme() == "dark"
