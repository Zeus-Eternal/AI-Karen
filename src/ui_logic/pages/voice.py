"""Interactive voice interface configuration page."""

from __future__ import annotations

from typing import Dict, List

import pandas as pd
import streamlit as st

from ai_karen_engine.integrations.provider_registry import ProviderRegistration
from ai_karen_engine.integrations.voice_registry import get_voice_registry
from ui_logic.pages._shared import require_page_access

REQUIRED_ROLES = ["user", "admin"]
FEATURE_FLAG = "enable_voice_io"


def _build_provider_overview(registry) -> pd.DataFrame:
    rows: List[Dict[str, str]] = []
    for provider_name in registry.list_providers(category="VOICE") or registry.list_providers():
        info: ProviderRegistration | None = registry.get_provider_info(provider_name)
        if not info:
            continue
        models = ", ".join(model.name for model in info.models) if info.models else "—"
        capabilities = ", ".join(
            {cap for model in info.models for cap in model.capabilities}
        ) if info.models else "—"
        rows.append(
            {
                "Provider": provider_name,
                "Description": info.description or "—",
                "Models": models,
                "Default Model": info.default_model or "—",
                "Capabilities": capabilities or "—",
                "API Key Required": "Yes" if info.requires_api_key else "No",
            }
        )
    return pd.DataFrame(rows)


def render_page(user_ctx: Dict | None = None) -> None:
    """Render the Voice control centre."""

    user = require_page_access(
        user_ctx,
        required_roles=REQUIRED_ROLES,
        feature_flag=FEATURE_FLAG,
        feature_name="Voice I/O",
        rbac_message="Voice page access denied",
    )

    registry = get_voice_registry()
    providers = registry.list_providers(category="VOICE") or registry.list_providers()

    st.title("🔊 Voice Interface Control Centre")
    st.caption(
        "Configure text-to-speech engines and inspect voice telemetry."
        "  All operations execute locally unless an external provider is selected."
    )

    if not providers:
        st.warning("No voice providers are currently registered. Register one via the backend configuration API.")
        return

    overview = _build_provider_overview(registry)
    if not overview.empty:
        st.dataframe(overview, use_container_width=True, hide_index=True)

    st.markdown("---")

    provider_name = st.selectbox("Voice provider", providers)
    provider_info = registry.get_provider_info(provider_name)

    models = registry.list_models(provider_name)
    if not models and provider_info and provider_info.default_model:
        models = [provider_info.default_model]

    model = st.selectbox("Voice model", models, index=0 if models else -1) if models else None

    st.write(
        "Configure the synthesis request below.  The built-in provider generates deterministic"
        " sine-wave clips for rapid smoke tests."
    )

    default_prompt = st.session_state.get("voice_last_prompt", "Hello from Kari's voice interface!")
    prompt = st.text_area("Text to synthesise", default_prompt, height=120)

    col_rate, col_volume = st.columns(2)
    with col_rate:
        sample_rate = st.slider("Sample rate", min_value=8_000, max_value=48_000, value=16_000, step=1_000)
    with col_volume:
        amplitude = st.slider("Output gain", min_value=0.1, max_value=0.9, value=0.35, step=0.05)

    generated_audio: bytes | None = None
    if st.button("Generate sample audio", use_container_width=True):
        try:
            synthesiser = registry.get_provider(provider_name, model=model) if model else registry.get_provider(provider_name)
            generated_audio = synthesiser.synthesize_speech(
                prompt,
                sample_rate=sample_rate,
                amplitude=amplitude,
            )
            st.session_state["voice_last_prompt"] = prompt
            st.audio(generated_audio, format="audio/wav")
            st.success("Audio sample generated successfully.")
        except Exception as exc:  # pragma: no cover - streamlit surface
            st.error(f"Failed to synthesise audio: {exc}")

    uploaded = st.file_uploader("Analyse an audio response (WAV)", type=["wav"])
    if uploaded is not None:
        try:
            analyser = registry.get_provider(provider_name, model=model) if model else registry.get_provider(provider_name)
            analysis = analyser.recognize_speech(uploaded.read())
            st.info(analysis)
        except Exception as exc:  # pragma: no cover - streamlit surface
            st.error(f"Unable to analyse audio clip: {exc}")

    if generated_audio:
        st.download_button(
            label="Download last sample",
            data=generated_audio,
            file_name=f"kari-voice-{provider_name}.wav",
            mime="audio/wav",
        )

    with st.expander("Active provider details"):
        if provider_info:
            st.json(
                {
                    "provider": provider_name,
                    "models": [model.name for model in provider_info.models],
                    "default_model": provider_info.default_model,
                    "description": provider_info.description,
                    "requires_api_key": provider_info.requires_api_key,
                }
            )
        else:
            st.info("Provider metadata not available.")

