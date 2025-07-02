import streamlit as st

from logic.model_registry import get_models
from logic.runtime_dispatcher import dispatch_runtime


def render_model_catalog() -> None:
    st.markdown("## :brain: Model Catalog")
    models = get_models()
    if not models:
        st.info("No models found in registry")
        return

    for meta in models:
        name = meta.get("model_name", "unknown")
        with st.expander(name):
            st.markdown(
                f"**Runtime:** {meta.get('runtime', 'n/a')} | "
                f"**Provider:** {meta.get('provider', 'n/a')}"
            )
            st.markdown(f"**Path:** {meta.get('path', '-')}")
            st.markdown(
                f"Tokenizer: {meta.get('tokenizer_type', '-')}",
            )
            limit = meta.get("prompt_limit_bytes")
            if limit:
                st.markdown(f"Prompt Limit: {limit}")
            feats = [
                f"Streaming {'✅' if meta.get('streaming') else '❌'}",
                f"Quantized {'✅' if meta.get('quantized') else '❌'}",
                f"LoRA {'✅' if meta.get('lora_support') else '❌'}",
            ]
            st.markdown(" | ".join(feats))

            prompt_key = f"prompt_{name}"
            prompt = st.text_input("Quick Prompt", key=prompt_key)
            if st.button("Run Quick Prompt", key=f"run_{name}") and prompt:
                with st.spinner("Running..."):
                    response = dispatch_runtime(meta, prompt)
                st.write(response)

            loaded = st.session_state.get(f"loaded_{name}", False)
            if st.button("Unload" if loaded else "Load", key=f"load_{name}"):
                st.session_state[f"loaded_{name}"] = not loaded
            st.caption(
                "Loaded" if st.session_state.get(f"loaded_{name}", False) else "Unloaded"
            )
            st.markdown("---")


if __name__ == "__main__":
    render_model_catalog()

