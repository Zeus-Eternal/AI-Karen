import streamlit as st
from ui.mobile_ui.services.config_manager import (
    load_config,
    save_config,
    save_provider_config,
    get_provider_config,
)
from ui.mobile_ui.services.model_registry import get_models, list_providers

LOCAL_PROVIDERS = {"local", "ollama_cpp"}


def render_settings():
    st.title("\u2699\ufe0f Kari Configuration")
    config = load_config()

    providers = list_providers()
    if any(m.get("provider") == "custom_provider" for m in get_models()):
        if "custom_provider" not in providers:
            providers.append("custom_provider")
            
    default_provider = config.get("provider", "deepseek")
    if default_provider not in providers and providers:
        default_provider = "deepseek" if "deepseek" in providers else providers[0]
    provider = st.selectbox(
        "Default Provider",
        providers,
        index=providers.index(default_provider) if default_provider in providers else 0,
    )
    prov_conf = get_provider_config(provider)
    models = [
        m.get("alias", m.get("model_name"))
        for m in get_models()
        if m.get("provider") == provider
    ]
    default_model = st.selectbox(
        "Default Model",
        models,
        index=models.index(prov_conf.get("model", models[0])) if models else 0,
    ) if models else ""

    st.markdown("### Provider Configuration")
    for prov in providers:
        with st.expander(prov, expanded=False):
            prov_conf = get_provider_config(prov)
            models = [
                m.get("alias", m.get("model_name"))
                for m in get_models()
                if m.get("provider") == prov
            ]
            model = st.selectbox(
                "Model",
                models,
                index=models.index(prov_conf.get("model", models[0])) if models else 0,
                key=f"model_{prov}",
            ) if models else ""

            api_key = ""
            if prov not in LOCAL_PROVIDERS:
                api_key = st.text_input(
                    f"{prov} API Key",
                    type="password",
                    value=prov_conf.get("api_key", ""),
                    key=f"key_{prov}",
                )

            if st.button("Save", key=f"save_{prov}"):
                save_provider_config(prov, {"model": model, "api_key": api_key})
                st.success(f"Saved {prov}")

    st.subheader("Memory Settings")
    use_memory = st.checkbox("Enable Memory", value=config.get("use_memory", True))
    context_len = st.slider("Context Length", 50, 2048, value=config.get("context_length", 512))
    decay = st.slider("Memory Decay", 0.0, 1.0, value=config.get("decay", 0.1))

    persona = st.text_input("Persona", value=config.get("persona", "default"))
    tone = st.selectbox(
        "Tone",
        ["neutral", "friendly", "professional", "playful"],
        index=["neutral", "friendly", "professional", "playful"].index(
            config.get("tone", "neutral")
        ),
    )
    language = st.selectbox(
        "Language",
        ["en", "es", "fr", "de"],
        index=["en", "es", "fr", "de"].index(config.get("language", "en")),
    )
    emotion = st.selectbox(
        "Emotion",
        ["neutral", "happy", "sad", "angry"],
        index=["neutral", "happy", "sad", "angry"].index(config.get("emotion", "neutral")),
    )

    prov_conf = get_provider_config(provider)
    if st.button("\U0001F4BE Save Configuration"):
        save_config({
            "provider": provider,
            "model": default_model,
            "api_key": prov_conf.get("api_key", ""),
            "use_memory": use_memory,
            "context_length": context_len,
            "decay": decay,
            "persona": persona,
            "tone": tone,
            "language": language,
            "emotion": emotion,
        })
        st.success("Settings saved.")
