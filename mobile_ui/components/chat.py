import asyncio
import streamlit as st

from logic.memory_controller import restore_memory, sync_memory
from utils.api_client import post, get


def _run_async(coro):
    """Run an async coroutine safely from Streamlit callbacks."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        return asyncio.create_task(coro)
    return asyncio.run(coro)


async def send_message(text: str, role: str = "user"):
    """Send a chat message to the backend."""
    return await post("/chat", {"text": text, "role": role})


def _display_history() -> None:
    """Render chat history stored in session state."""
    for msg in st.session_state.get("messages", []):
        with st.chat_message(msg.get("role", "user")):
            st.markdown(msg.get("text", ""))


def render_chat() -> None:
    """Interactive chat interface linked to Kari's backend."""
    st.title("\U0001f4ac Chat with Kari")

    restore_memory()

    col1, col2 = st.columns([3, 1])

    with col2:
        if st.button("\U0001f9e0 Recall Memory"):
            restore_memory()
            st.toast("Memory restored")
        if st.button("\U0001f4dc Show Logs"):
            logs = _run_async(get("/self_refactor/logs"))
            if isinstance(logs, dict):
                st.expander("Logs").write("\n".join(logs.get("logs", [])))

    with col1:
        show_prompt = st.checkbox("Show system prompt", value=False)
        if show_prompt:
            st.expander("System Prompt").write("Placeholder system prompt.")

        _display_history()

        user_input = st.chat_input("Type your message")
        if user_input:
            st.session_state.setdefault("messages", []).append(
                {"role": "user", "text": user_input}
            )
            with st.chat_message("user"):
                st.markdown(user_input)
            with st.chat_message("assistant"):
                placeholder = st.empty()
                data = _run_async(send_message(user_input))
                if data and not data.get("error"):
                    response = data.get("response", "")
                    placeholder.markdown(response)
                    st.session_state["messages"].append(
                        {"role": "assistant", "text": response}
                    )
                    sync_memory()
                else:
                    placeholder.error(data.get("error", "error"))
