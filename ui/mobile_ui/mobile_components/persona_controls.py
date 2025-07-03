import streamlit as st

DEFAULT_PERSONA = "default"
DEFAULT_TONE = "neutral"
DEFAULT_LANGUAGE = "en"
DEFAULT_EMOTION = "neutral"

PERSONA_OPTIONS = ["default", "coach", "developer", "friend", "admin"]
TONE_OPTIONS = ["neutral", "friendly", "professional", "playful"]
LANG_OPTIONS = ["en", "es", "fr", "de"]
EMOTION_OPTIONS = ["neutral", "happy", "sad", "angry"]


def render_persona_controls() -> None:
    """Render dynamic persona and tone controls."""
    st.sidebar.subheader("\U0001F464 Persona")
    persona = st.sidebar.selectbox(
        "Persona",
        PERSONA_OPTIONS,
        index=PERSONA_OPTIONS.index(st.session_state.get("persona", DEFAULT_PERSONA)),
        key="persona_select",
    )
    tone = st.sidebar.selectbox(
        "Tone",
        TONE_OPTIONS,
        index=TONE_OPTIONS.index(st.session_state.get("tone", DEFAULT_TONE)),
        key="tone_select",
    )
    language = st.sidebar.selectbox(
        "Language",
        LANG_OPTIONS,
        index=LANG_OPTIONS.index(st.session_state.get("language", DEFAULT_LANGUAGE)),
        key="lang_select",
    )
    emotion = st.sidebar.selectbox(
        "Emotion",
        EMOTION_OPTIONS,
        index=EMOTION_OPTIONS.index(st.session_state.get("emotion", DEFAULT_EMOTION)),
        key="emotion_select",
    )
    if st.sidebar.button("Apply Style", key="apply_style"):
        st.session_state.update(
            persona=persona, tone=tone, language=language, emotion=emotion
        )
        try:
            from ui.mobile_ui.services.config_manager import update_config
            update_config(
                persona=persona, tone=tone, language=language, emotion=emotion
            )
            st.sidebar.success("Style updated")
        except Exception:
            st.sidebar.warning("Could not persist style settings")
