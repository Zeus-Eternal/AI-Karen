"""
Kari Chat Panel (Evil Twin Enterprise Version)
- Async, context-aware, plugin/tool injection, memory/trace preview
- Provider/model selection, live role switching, emoji toaster, RBAC, observability
"""

import streamlit as st
import time
import uuid

def _auto_refresh(interval: int = 1000, key: str = "chat_refresh") -> None:
    """Lightweight auto-refresh using experimental_rerun."""
    now = int(time.time() * 1000)
    last = st.session_state.get(key, now)
    if now - last >= interval:
        st.session_state[key] = now
        st.experimental_rerun()
from ui_logic.hooks.rbac import user_has_role
from ui_logic.utils.api import (
    fetch_user_profile, 
    fetch_announcements,
    ping_services,
)
from ui_logic.components.analytics.chart_builder import render_quick_charts
from ui_logic.components.memory.session_explorer import render_session_explorer
from ui_logic.components.plugins.plugin_manager import render_plugin_manager
from ui_logic.components.memory.memory_analytics import render_memory_analytics

# ==============================================
# ====== EVIL CONTEXT AND STATE HANDLING =======
# ==============================================

def get_context_state():
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "system_role" not in st.session_state:
        st.session_state["system_role"] = "default"
    if "provider" not in st.session_state:
        st.session_state["provider"] = "ollama"
    if "model" not in st.session_state:
        st.session_state["model"] = "llama3.2:latest"
    if "chat_trace_id" not in st.session_state:
        st.session_state["chat_trace_id"] = str(uuid.uuid4())
    if "toast_stack" not in st.session_state:
        st.session_state["toast_stack"] = []
    if "show_context_preview" not in st.session_state:
        st.session_state["show_context_preview"] = False

# ========== Toaster Helper ==========
def evil_toast(msg, emoji="💀"):
    st.session_state["toast_stack"].append(f"{emoji} {msg}")
    st.toast(f"{emoji} {msg}")

# ========== Context/Trace Preview =====
def context_trace_panel():
    st.markdown("### :crystal_ball: Context & Memory")
    st.json({"trace_id": st.session_state["chat_trace_id"],
             "history": st.session_state["chat_history"][-5:]})
    if st.button("Clear Chat Context", key="clear_ctx_btn"):
        st.session_state["chat_history"] = []
        evil_toast("Chat context cleared!", "🧹")

# ========== Role Switch ==========
def role_switcher(user_ctx):
    st.markdown("#### System/User Role")
    roles = user_ctx.get("roles", [])
    chosen_role = st.radio(
        "Chat as...",
        options=["default"] + roles,
        index=roles.index(st.session_state.get("system_role", "default")) + 1
        if st.session_state.get("system_role", "default") in roles else 0,
        horizontal=True,
        key="role_radio"
    )
    st.session_state["system_role"] = chosen_role
    evil_toast(f"Role switched to {chosen_role}", "👤")

# ========== Provider/Model Select ==========
def provider_model_select():
    st.markdown("#### LLM Provider / Model")
    providers = ["ollama", "gemini", "anthropic"]  # Add more as you wire in
    provider = st.selectbox("Provider", providers, index=providers.index(st.session_state["provider"]))
    st.session_state["provider"] = provider
    # Dynamic model list
    model_map = {
        "ollama": ["llama3.2:latest", "phi3:medium", "mistral:latest"],
        "gemini": ["gemini-pro", "gemini-1.5-flash"],
        "anthropic": ["claude-3-haiku", "claude-3-opus"]
    }
    model = st.selectbox("Model", model_map[provider], index=0)
    st.session_state["model"] = model
    evil_toast(f"Provider: {provider} | Model: {model}", "🧠")

# ========== Announcements/Observability Panel ==========
def sys_announce_panel():
    st.markdown("#### Announcements & System Status")
    announcements = fetch_announcements(limit=5)
    for a in announcements:
        st.info(f"[{a.get('timestamp','')}] {a.get('message','')}")
    st.write("##### Service Health")
    st.write(ping_services())

# ========== Main Chat Logic ==========
def chat_panel(user_ctx):
    st.title("💬 Kari Chat")
    _auto_refresh()
    get_context_state()
    sys_announce_panel()
    st.sidebar.header("Session Controls")
    provider_model_select()
    role_switcher(user_ctx)

    # Context Preview Toggle
    with st.sidebar:
        st.markdown("---")
        if st.button("Toggle Context Preview", key="toggle_ctx_preview"):
            st.session_state["show_context_preview"] = not st.session_state["show_context_preview"]
        if st.session_state["show_context_preview"]:
            context_trace_panel()

    # User Profile Quick Preview
    with st.expander("Your Profile", expanded=False):
        st.json(fetch_user_profile(user_ctx.get("user_id")))

    # Memory & Analytics (hidden for normies, show for admin)
    if user_has_role(user_ctx, "admin"):
        with st.expander("🧠 Memory Analytics", expanded=False):
            render_memory_analytics(user_ctx)
        with st.expander("📈 Quick Charts", expanded=False):
            render_quick_charts(user_ctx)

    # Session Explorer (for nerds/admins)
    if user_has_role(user_ctx, "admin"):
        with st.expander("📚 Session Explorer", expanded=False):
            render_session_explorer(user_ctx)

    # Plugin Manager (if admin or plugin_manager)
    if user_has_role(user_ctx, "admin") or user_has_role(user_ctx, "plugin_manager"):
        with st.expander("🧩 Plugin Manager", expanded=False):
            render_plugin_manager(user_ctx)

    # Chat Box UI
    st.markdown("---")
    st.subheader("Your Evil Chat")
    for entry in st.session_state["chat_history"]:
        who = "🧑" if entry["role"] == "user" else "🤖"
        st.chat_message(who).write(entry["text"])

    with st.form(key="evil_chat_form", clear_on_submit=True):
        user_msg = st.text_input("Type your message...", max_chars=2048, key="chat_input")
        submitted = st.form_submit_button("Send", type="primary")
        if submitted and user_msg.strip():
            # Push user msg to chat history
            st.session_state["chat_history"].append({"role": "user", "text": user_msg, "ts": time.time()})
            evil_toast("You: " + user_msg, "🗨️")
            # ===== LLM Backend Wireup (plugin/llm_utils/api etc) =====
            try:
                from ai_karen_engine.integrations.llm_utils import generate_text
                llm_resp = generate_text(
                    prompt=user_msg,
                    provider=st.session_state["provider"],
                    user_ctx=user_ctx,
                    trace_id=st.session_state["chat_trace_id"],
                    model=st.session_state["model"]
                )
                st.session_state["chat_history"].append({"role": "kari", "text": llm_resp, "ts": time.time()})
                evil_toast("Kari responded.", "🤖")
            except Exception as ex:
                err = f"LLM failure: {ex}"
                st.session_state["chat_history"].append({"role": "kari", "text": err, "ts": time.time()})
                evil_toast("LLM error. Check backend.", "💀")
                st.error(err)
            st.experimental_rerun()

    st.caption("Twin Mode: All interactions are audit-logged. All glory to Kari.")

# ========== Entrypoint ==========
def render(user_ctx=None):
    if user_ctx is None or not user_has_role(user_ctx, ["user", "admin"]):
        st.warning("You must be logged in with sufficient privileges to access chat.")
        return
    chat_panel(user_ctx)

# For direct test/dev
if __name__ == "__main__":
    evil_user_ctx = {
        "user_id": "evil_tester",
        "roles": ["admin", "plugin_manager", "user"],
        "org_id": "default",
    }
    render(evil_user_ctx)
