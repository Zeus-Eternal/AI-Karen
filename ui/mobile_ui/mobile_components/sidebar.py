# mobile_ui/components/sidebar.py

import streamlit as st
import pandas as pd
from typing import Optional

from ui.mobile_ui.services.config_manager import (
    load_config,
    update_config,
    get_status,
    list_configured_providers,
    get_provider_config,
)
from ui.mobile_ui.services.model_registry import (
    list_providers,
    get_models,
    ensure_model_downloaded,
)


def select_model(provider: str) -> Optional[str]:
    """Render a model selection widget for a given provider and allow on-demand download."""
    st.subheader("🎯 Select Model")
    entries = get_models(provider)
    options = [m.get("alias", m.get("name")) for m in entries]
    if not options:
        st.warning("No models available for this provider.")
        return None

    choice = st.selectbox("Model", options)
    if st.button("Ensure Model Ready"):
        entry = next((m for m in entries if m.get("alias", m.get("name")) == choice), None)
        if entry:
            try:
                path = ensure_model_downloaded(entry)
                st.success(f"{choice} is ready at {path}.")
            except Exception as e:
                st.error(f"Failed to download {choice}: {e}")
    return choice


def render_models() -> None:
    """Show a table of all models for the selected provider."""
    st.title("🧠 Model Catalog")
    provider = st.selectbox("Choose Provider", list_providers())
    data = get_models(provider)
    if data:
        st.table(pd.DataFrame(data))
    else:
        st.info("No models to display for this provider.")


def render_sidebar() -> str:
    """
    Render the sidebar UI for LLM configuration and navigation.
    Returns the selected page key.
    """
    st.sidebar.title("⚙️ LLM Configuration")
    cfg = load_config()

    # Providers
    providers = list_providers()
    if any(m.get("provider") == "custom" for m in get_models()):
        providers.append("custom")

    default_prov = cfg.get("provider", providers[0] if providers else "")
    if default_prov not in providers and providers:
        default_prov = providers[0]

    selected_prov = st.sidebar.selectbox(
        "LLM Provider", providers, index=providers.index(default_prov)
    )
    if selected_prov != cfg.get("provider"):
        update_config(provider=selected_prov)
        cfg["provider"] = selected_prov

    # Models
    entries = get_models(selected_prov)
    names = [m.get("alias", m.get("name")) for m in entries]
    default_model = cfg.get("model", names[0] if names else "")
    if default_model not in names and names:
        default_model = names[0]

    selected_model = st.sidebar.selectbox(
        "Model", names, index=names.index(default_model) if names else 0
    )
    if selected_model and selected_model != cfg.get("model"):
        update_config(model=selected_model)
        cfg["model"] = selected_model

    # Auto-download for local providers
    if selected_prov.startswith("local") and selected_model:
        entry = next((m for m in entries if m.get("alias", m.get("name")) == selected_model), None)
        if entry:
            try:
                ensure_model_downloaded(entry)
            except Exception:
                pass  # silent; user can re-trigger via select_model

    # Status
    status = get_status()
    emoji = {"Ready": "🟢", "Pending Config": "🟡", "Invalid": "🔴"}.get(status, "❔")
    st.sidebar.markdown(f"**Status:** {emoji} {status}")

    # Configured providers
    configured = list_configured_providers()
    if configured:
        st.sidebar.subheader("Configured Providers")
        for prov in configured:
            meta = get_provider_config(prov)
            st.sidebar.write(f"- {prov}: {meta.get('model', '-')}" )

    # Navigation
    return st.sidebar.radio(
        "🧭 Navigate",
        ["Chat", "Settings", "Models", "Memory", "Diagnostics"],
        index=0,
    )
