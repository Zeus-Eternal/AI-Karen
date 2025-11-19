"""
Sidebar Components for Kari AI Streamlit Console
"""

import streamlit as st

def render_left_sidebar():
    """Render left sidebar with navigation and chat history"""
    st.markdown('<div class="left-sidebar">', unsafe_allow_html=True)
    
    # New chat button
    if st.button("➕ New Chat", key="new_chat_button"):
        st.session_state.conversation_history = []
        st.rerun()
    
    st.markdown("---")
    
    # Chat history
    st.markdown("### Recent Chats")
    
    # This would normally fetch from a database
    # For now, we'll simulate with some placeholder chats
    chat_history = [
        {"id": "chat_1", "title": "Project Planning Discussion", "timestamp": "2023-11-15"},
        {"id": "chat_2", "title": "Code Review Session", "timestamp": "2023-11-14"},
        {"id": "chat_3", "title": "Research on AI Models", "timestamp": "2023-11-13"},
    ]
    
    for chat in chat_history:
        if st.button(chat["title"], key=f"chat_{chat['id']}"):
            st.info(f"Loading chat: {chat['title']}")
    
    st.markdown("---")
    
    # User info and settings
    st.markdown("### User Settings")
    
    # Model selection in left sidebar
    render_model_selector()
    
    # Reasoning mode
    render_reasoning_selector()
    
    st.markdown("---")
    
    # Plugin toggles
    render_plugin_toggles()
    
    st.markdown("---")
    
    # User info
    st.markdown(f"**User:** {st.session_state.user_id}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_model_selector():
    """Render model selection widget"""
    st.markdown("#### Model")
    model_options = [
        "llama-cpp-7B (Local)",
        "llama-cpp-13B (Local)",
        "llama-cpp-70B (Local)",
        "gpt-3.5-turbo (Cloud)",
        "gpt-4 (Cloud)",
        "gpt-4-turbo (Cloud)",
        "claude-3-haiku (Cloud)",
        "claude-3-sonnet (Cloud)",
        "claude-3-opus (Cloud)"
    ]
    selected_model = st.selectbox(
        "",
        options=model_options,
        index=0,
        key="left_sidebar_model"
    )
    # Extract model name without version details
    st.session_state.current_model = selected_model.split(" ")[0] + "-" + selected_model.split(" ")[1].split("-")[0]

def render_reasoning_selector():
    """Render reasoning mode selector"""
    reasoning_options = ["Off", "Standard", "Detailed"]
    st.session_state.reasoning_mode = st.selectbox(
        "Reasoning",
        options=reasoning_options,
        index=1,
        key="left_sidebar_reasoning"
    )

def render_plugin_toggles():
    """Render plugin toggle widgets"""
    st.markdown("#### Plugins")
    for plugin, active in st.session_state.active_plugins.items():
        st.session_state.active_plugins[plugin] = st.checkbox(
            plugin.capitalize(),
            value=active,
            key=f"left_sidebar_plugin_{plugin}"
        )

def render_config_zone():
    """Render config zone in right sidebar"""
    with st.sidebar:
        # Logo and App Name
        st.markdown("# 🧠 Kari AI")
        st.markdown("### Lite Console")
        st.markdown("---")
        
        # System Status
        st.markdown("#### System Status")
        render_system_status()
        
        # Debug Mode Toggle
        st.markdown("---")
        st.session_state.debug_mode = st.checkbox("Debug Mode", value=st.session_state.debug_mode)

def render_system_status():
    """Render system status indicators"""
    status_col1, status_col2 = st.columns([1, 3])
    with status_col1:
        st.markdown('<div class="status-indicator status-online"></div>', unsafe_allow_html=True)
    with status_col2:
        st.markdown("Model Ready")
    
    status_col3, status_col4 = st.columns([1, 3])
    with status_col3:
        st.markdown('<div class="status-indicator status-online"></div>', unsafe_allow_html=True)
    with status_col4:
        st.markdown("DB Connected")
    
    status_col5, status_col6 = st.columns([1, 3])
    with status_col5:
        st.markdown('<div class="status-indicator status-warning"></div>', unsafe_allow_html=True)
    with status_col6:
        st.markdown("Plugins: 2/3")