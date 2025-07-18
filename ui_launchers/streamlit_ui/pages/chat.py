"""
Kari Chat Panel (Evil Twin Enterprise Version) - Enhanced UX/UI
- Async, context-aware, plugin/tool injection, memory/trace preview
- Provider/model selection, live role switching, emoji toaster, RBAC, observability
"""

import streamlit as st
import time
import uuid
from datetime import datetime

# Try to import the third-party auto-refresh helper
try:
    from streamlit_autorefresh import st_autorefresh
    AUTO_REFRESH_AVAILABLE = True
except ImportError:
    AUTO_REFRESH_AVAILABLE = False

from ui_logic.hooks.rbac import user_has_role
from ui_logic.utils.api import fetch_user_profile
from ui_logic.components.analytics.chart_builder import render_quick_charts
from ui_logic.components.memory.session_explorer import render_session_explorer
from ui_logic.components.plugins.plugin_manager import render_plugin_manager
from ui_logic.components.memory.memory_analytics import render_memory_analytics


# ==============================================
# ============ CORE FUNCTIONALITY ==============
# ==============================================

def rerun() -> None:
    """Trigger Streamlit to re-execute the script from the top."""
    st.experimental_rerun()


def _auto_refresh(interval_ms: int = 2000) -> None:
    """
    Enhanced auto-refresh with status indicator
    """
    params = st.query_params
    if params.get("page", [""])[0] == "chat":
        if AUTO_REFRESH_AVAILABLE:
            st_autorefresh(interval=interval_ms, key="chat_autorefresh")
        else:
            with st.status("Syncing...", state="running"):
                time.sleep(interval_ms / 1000)
                st.experimental_rerun()


# ==============================================
# ========== ENHANCED STATE HANDLING ===========
# ==============================================

def get_context_state():
    """Initialize all required session state variables"""
    defaults = {
        "chat_history": [],
        "system_role": "default",
        "provider": "ollama",
        "model": "llama3.2:latest",
        "chat_trace_id": str(uuid.uuid4()),
        "toast_stack": [],
        "show_context_preview": False,
        "dark_mode": False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ==============================================
# ============ ENHANCED COMPONENTS =============
# ==============================================

def evil_toast(msg: str, emoji: str = "💀"):
    """Enhanced toast with smart stacking and auto-dismiss"""
    if len(st.session_state["toast_stack"]) > 3:
        st.session_state["toast_stack"].pop(0)
    
    toast_id = f"{time.time()}-{emoji}-{msg[:10]}"
    st.session_state["toast_stack"].append({
        "id": toast_id,
        "message": f"{emoji} {msg}",
        "emoji": emoji,
        "timestamp": time.time()
    })
    
    st.toast(f"{emoji} {msg}", icon=emoji)


def _render_toast_history():
    """Display recent toasts in sidebar"""
    if st.session_state["toast_stack"]:
        with st.sidebar.expander("🔔 Recent Notifications", expanded=False):
            for toast in reversed(st.session_state["toast_stack"][-3:]):
                cols = st.columns([0.2, 0.8])
                cols[0].write(f"{toast['emoji']}")
                cols[1].caption(toast["message"])
                st.markdown("---")


def context_trace_panel():
    """Enhanced context preview with copy functionality"""
    with st.container(border=True):
        st.markdown("### 🧠 Current Context")
        
        tab1, tab2 = st.tabs(["Summary", "Raw Data"])
        
        with tab1:
            st.markdown(f"**Trace ID:** `{st.session_state['chat_trace_id']}`")
            st.code("Click 'Copy Trace ID' to share this session", language="text")
            
            if st.button("📋 Copy Trace ID", use_container_width=True):
                st.session_state["clipboard"] = st.session_state["chat_trace_id"]
                evil_toast("Trace ID copied!", "📋")
            
            st.markdown("---")
            st.markdown(f"**Last {min(3, len(st.session_state['chat_history']))} Messages:**")
            for msg in st.session_state["chat_history"][-3:]:
                role = "User" if msg["role"] == "user" else "Kari"
                st.caption(f"{role}: {msg['text'][:50]}...")
        
        with tab2:
            st.json({
                "trace_id": st.session_state["chat_trace_id"],
                "history": st.session_state["chat_history"][-5:]
            })


def role_switcher(user_ctx: dict):
    """Enhanced role switcher with visual indicators"""
    roles = user_ctx.get("roles", [])
    current = st.session_state.get("system_role", "default")
    
    with st.container(border=True):
        st.markdown("#### 👤 Active Persona")
        
        if not roles:
            st.warning("No additional roles available")
            st.session_state["system_role"] = "default"
            return
        
        cols = st.columns([0.7, 0.3])
        with cols[0]:
            selected = st.selectbox(
                "Select role:",
                options=["default"] + roles,
                index=(["default"] + roles).index(current),
                label_visibility="collapsed"
            )
        
        with cols[1]:
            st.markdown("")
            if st.button("Apply", use_container_width=True):
                st.session_state["system_role"] = selected
                evil_toast(f"Switched to {selected} persona", "👤")
        
        if selected != current:
            st.info(f"Role will change to: **{selected}**", icon="ℹ️")


def provider_model_select():
    """Enhanced model selection with descriptions"""
    providers = {
        "ollama": {
            "models": ["llama3.2:latest", "phi3:medium", "mistral:latest"],
            "icon": "🦙"
        },
        "gemini": {
            "models": ["gemini-pro", "gemini-1.5-flash"],
            "icon": "♊"
        },
        "anthropic": {
            "models": ["claude-3-haiku", "claude-3-opus"],
            "icon": "🅰️"
        }
    }
    
    with st.container(border=True):
        st.markdown("#### 🧠 AI Configuration")
        
        # Provider selection
        current_provider = st.session_state.get("provider", "ollama")
        provider = st.radio(
            "Select Provider:",
            options=list(providers.keys()),
            index=list(providers.keys()).index(current_provider),
            format_func=lambda x: f"{providers[x]['icon']} {x.capitalize()}",
            horizontal=True
        )
        
        # Model selection
        current_model = st.session_state.get("model", providers[provider]["models"][0])
        model = st.selectbox(
            "Select Model:",
            options=providers[provider]["models"],
            index=providers[provider]["models"].index(current_model) if current_model in providers[provider]["models"] else 0,
            help="Different models have different capabilities and costs"
        )
        
        # Apply button
        if st.button("💾 Save Configuration", use_container_width=True):
            st.session_state["provider"] = provider
            st.session_state["model"] = model
            evil_toast(f"Saved: {provider} - {model}", "✅")


def _render_chat_message(entry):
    """Enhanced chat message with metadata"""
    who = "🧑 You" if entry["role"] == "user" else "🤖 Kari"
    timestamp = datetime.fromtimestamp(entry["ts"]).strftime('%H:%M:%S')
    
    with st.chat_message(entry["role"]):
        # Header with avatar and timestamp
        cols = st.columns([0.8, 0.2])
        cols[0].markdown(f"**{who}**")
        cols[1].caption(timestamp)
        
        # Message content
        st.write(entry["text"])
        
        # Optional metadata (for system messages)
        if entry.get("metadata"):
            with st.expander("Technical Details", expanded=False):
                st.json(entry["metadata"])


def _enhanced_chat_input():
    """Modern chat input with features"""
    with st.form(key="evil_chat_form", clear_on_submit=True):
        # Input area with character counter
        user_msg = st.text_area(
            "Your message",
            max_chars=2048,
            key="chat_input",
            label_visibility="collapsed",
            placeholder="Type your message to Kari...",
            height=100
        )
        
        # Control buttons
        col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
        
        with col1:
            st.caption(f"{len(user_msg)}/2048 characters")
        
        with col2:
            if st.form_submit_button("🚀 Send", type="primary", use_container_width=True):
                if not user_msg.strip():
                    st.warning("Message cannot be empty")
                    st.stop()
                return user_msg.strip()
        
        with col3:
            if st.form_submit_button("📎 Attach", use_container_width=True):
                evil_toast("Attachment feature coming soon!", "📎")
                st.stop()
    
    return None


# ==============================================
# ============== MAIN INTERFACE ================
# ==============================================

def _render_sidebar(user_ctx):
    """Enhanced sidebar with all controls"""
    with st.sidebar:
        # Header with theme toggle
        col1, col2 = st.columns([0.7, 0.3])
        col1.title("⚙️ Control Panel")
        with col2:
            if st.toggle("🌙", value=st.session_state.get("dark_mode", False)):
                st.session_state["dark_mode"] = not st.session_state.get("dark_mode", False)
        
        # Main controls
        provider_model_select()
        role_switcher(user_ctx)
        
        st.markdown("---")
        
        # Context management
        with st.expander("🔍 Session Context", expanded=False):
            context_trace_panel()
        
        if st.button("🧹 Clear Chat History", use_container_width=True):
            st.session_state["chat_history"] = []
            evil_toast("Chat history cleared!", "🧹")
        
        st.markdown("---")
        
        # Notification history
        _render_toast_history()


def chat_panel(user_ctx: dict):
    """Enhanced main chat interface"""
    # Initialize session state and configure page
    get_context_state()
    st.session_state["user_ctx"] = user_ctx
    st.set_page_config(layout="wide", page_title="Kari Chat")
    
    # Apply dark mode if enabled
    if st.session_state.get("dark_mode"):
        st.markdown("""
        <style>
            .stApp { background-color: #0e1117; }
            .stChatInput { background-color: #262730; }
        </style>
        """, unsafe_allow_html=True)
    
    # Main layout columns
    main_col, side_col = st.columns([0.7, 0.3])
    
    with main_col:
        # Header with status indicator
        st.title("💬 Kari Chat")
        st.caption("Twin Mode: All interactions are audit-logged. All glory to Kari.")
        
        # Chat history container with scroll
        chat_container = st.container(height=500)
        with chat_container:
            for entry in st.session_state["chat_history"]:
                _render_chat_message(entry)
        
        # Enhanced input
        user_msg = _enhanced_chat_input()
        if user_msg:
            # Process user message
            st.session_state["chat_history"].append({
                "role": "user",
                "text": user_msg,
                "ts": time.time()
            })
            evil_toast("Message sent!", "✉️")
            
            # Generate response
            try:
                from ai_karen_engine.integrations.llm_utils import generate_text
                with st.status("Kari is thinking...", expanded=False):
                    llm_resp = generate_text(
                        prompt=user_msg,
                        provider=st.session_state["provider"],
                        user_ctx=user_ctx,
                        trace_id=st.session_state["chat_trace_id"],
                        model=st.session_state["model"]
                    )
                
                st.session_state["chat_history"].append({
                    "role": "kari",
                    "text": llm_resp,
                    "ts": time.time()
                })
                evil_toast("Kari responded!", "🤖")
            except Exception as ex:
                error_msg = f"LLM Error: {str(ex)}"
                st.session_state["chat_history"].append({
                    "role": "kari",
                    "text": error_msg,
                    "ts": time.time(),
                    "metadata": {"error": True}
                })
                evil_toast("LLM error occurred", "💀")
                st.error(error_msg)
            
            rerun()
    
    with side_col:
        _render_sidebar(user_ctx)
        
        # User profile
        with st.expander("👤 User Profile", expanded=False):
            profile = fetch_user_profile(user_ctx.get("user_id"))
            st.json(profile, expanded=False)
        
        # Admin features
        if user_has_role(user_ctx, "admin"):
            with st.expander("📊 Analytics", expanded=False):
                render_quick_charts(user_ctx)
            
            with st.expander("🧠 Memory", expanded=False):
                render_memory_analytics(user_ctx)
                
            with st.expander("📚 Sessions", expanded=False):
                render_session_explorer(user_ctx)
        
        # Plugin manager
        if user_has_role(user_ctx, "admin") or user_has_role(user_ctx, "plugin_manager"):
            with st.expander("🧩 Plugins", expanded=False):
                render_plugin_manager(user_ctx)
    
    _auto_refresh()


# ==============================================
# ================== ENTRYPOINT ================
# ==============================================

def render(user_ctx=None):
    """Entry point for the chat panel"""
    if user_ctx is None or not user_has_role(user_ctx, ["user", "admin"]):
        st.error("🔒 You must be logged in with sufficient privileges to access chat.")
        st.stop()
    
    try:
        chat_panel(user_ctx)
    except Exception as e:
        st.error(f"System Error: {str(e)}")
        st.stop()


# For direct test/dev
if __name__ == "__main__":
    mock_user = {
        "user_id": "evil_tester",
        "roles": ["admin", "plugin_manager", "user"],
        "org_id": "default",
    }
    render(mock_user)