"""Simple sidebar controls to select persona settings."""
import streamlit as st
from ui_logic.hooks.rbac import require_roles
import importlib


def _load_update_config():
    try:  # pragma: no cover - optional dependency
        mod = importlib.import_module("ui.mobile_ui.services.config_manager")
        return getattr(mod, "update_config")
    except Exception:  # pragma: no cover - optional dependency
        def noop(**_):
            return None

        return noop


def render_persona_controls(user_ctx=None):
    """Render persona selector and persist selection."""
    if user_ctx and not require_roles(user_ctx, ["user", "branding"]):
        st.warning("Insufficient permissions to change persona")
        return
    st.sidebar.subheader("Persona Controls")
    persona = st.sidebar.selectbox("Persona", ["friend", "developer", "assistant"], index=0)
    tone = st.sidebar.selectbox("Tone", ["playful", "professional"], index=0)
    language = st.sidebar.selectbox("Language", ["en", "es", "fr"], index=0)
    emotion = st.sidebar.selectbox("Emotion", ["happy", "sad"], index=0)
    if st.sidebar.button("Apply", key="apply_persona"):
        st.session_state["persona"] = persona
        st.session_state["tone"] = tone
        st.session_state["language"] = language
        st.session_state["emotion"] = emotion
        updater = _load_update_config()
        try:
            updater(
                persona=persona,
                tone=tone,
                language=language,
                emotion=emotion,
            )
            st.sidebar.success("Persona updated")
        except Exception:
            st.sidebar.warning("Failed to update persona")


__all__ = ["render_persona_controls"]
