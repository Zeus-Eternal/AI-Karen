import importlib.util
import sys
import types
from pathlib import Path


class DummySidebar:
    def __init__(self, values, raise_error=False):
        self._values = values
        self.success_called = False
        self.warning_called = False
        self.raise_error = raise_error

    def subheader(self, text):
        pass

    def selectbox(self, label, options, index=0, key=None):
        return self._values[label]

    def button(self, label, key=None):
        return True

    def success(self, msg):
        self.success_called = True

    def warning(self, msg):
        self.warning_called = True


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src/ui_logic/components/persona/persona_controls.py"
)


def setup_env(monkeypatch, values, raise_error=False):
    sidebar = DummySidebar(values, raise_error)
    fake_streamlit = types.ModuleType("streamlit")
    fake_streamlit.sidebar = sidebar
    fake_streamlit.session_state = {}
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    spec = importlib.util.spec_from_file_location("persona_controls", MODULE_PATH)
    persona_controls = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(persona_controls)

    saved = {}

    def fake_update_config(**kwargs):
        if sidebar.raise_error:
            raise RuntimeError("fail")
        saved.update(kwargs)

    fake_cm = types.ModuleType("ui.mobile_ui.services.config_manager")
    fake_cm.update_config = fake_update_config
    monkeypatch.setitem(sys.modules, "ui.mobile_ui.services.config_manager", fake_cm)
    return persona_controls, sidebar, fake_streamlit.session_state, saved


def test_apply_persona_updates_state_and_config(monkeypatch):
    values = {
        "Persona": "developer",
        "Tone": "professional",
        "Language": "es",
        "Emotion": "sad",
    }
    pc, sidebar, state, saved = setup_env(monkeypatch, values)
    pc.render_persona_controls()
    assert state == {
        "persona": "developer",
        "tone": "professional",
        "language": "es",
        "emotion": "sad",
    }
    assert saved == state
    assert sidebar.success_called


def test_apply_persona_warning_on_error(monkeypatch):
    values = {
        "Persona": "friend",
        "Tone": "playful",
        "Language": "fr",
        "Emotion": "happy",
    }
    pc, sidebar, state, _ = setup_env(monkeypatch, values, raise_error=True)
    pc.render_persona_controls()
    assert state == {
        "persona": "friend",
        "tone": "playful",
        "language": "fr",
        "emotion": "happy",
    }
    assert sidebar.warning_called
