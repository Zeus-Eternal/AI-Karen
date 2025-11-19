"""
Kari AI – UI Layer
Phase: v0.5 – "Lite Streamlit Console"
Subphase: P0.5.1 – Personal-DB-Aware Chat Shell

"Lite console. Heavy brains. Kari whispers in neon while world still types in grayscale."
"""

import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import time
from typing import Dict, List, Optional, Any
import os
from datetime import datetime

# Import services
from services.conversation_service import (
    create_conversation, get_conversation, get_user_conversations,
    add_message_to_conversation, delete_conversation, search_conversations,
    create_session, get_session, update_session
)
from services.user_service import get_user_profile

# Page Configuration
st.set_page_config(
    page_title="Kari AI - Lite Console",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark neon theme
def load_neon_theme():
    neon_css = """
    <style>
    :root {
        --primary-neon: #00FFFF;
        --secondary-neon: #FF00FF;
        --background-dark: #0F0F1B;
        --background-panel: #1A1A2E;
        --background-sidebar: #16161A;
        --text-primary: #FFFFFF;
        --text-secondary: #00FFFF;
        --text-accent: #FF00FF;
        --border-color: rgba(0, 255, 255, 0.3);
    }
    
    body {
        background-color: var(--background-dark);
        color: var(--text-primary);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .stApp {
        background-color: var(--background-dark);
    }
    
    /* Main container styling */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        background-color: var(--background-dark);
    }
    
    /* Right sidebar styling (Streamlit default) */
    .css-1d391kg {
        background-color: var(--background-panel);
        border-right: 1px solid var(--border-color);
    }
    
    /* Left sidebar styling */
    .left-sidebar {
        background-color: var(--background-sidebar);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid var(--border-color);
    }
    
    /* Left sidebar button styling */
    .left-sidebar button {
        width: 100%;
        text-align: left;
        background-color: transparent;
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        padding: 0.5rem;
        margin-bottom: 0.5rem;
        transition: all 0.3s ease;
    }
    
    .left-sidebar button:hover {
        background-color: rgba(0, 255, 255, 0.2);
        border-color: var(--primary-neon);
        color: var(--primary-neon);
        box-shadow: 0 0 8px rgba(0, 255, 255, 0.4);
    }
    
    /* Left sidebar heading styling */
    .left-sidebar h3 {
        color: var(--text-secondary);
        font-size: 1rem;
        margin-bottom: 0.5rem;
        margin-top: 1rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .left-sidebar h4 {
        color: var(--text-accent);
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
        margin-top: 1rem;
    }
    
    /* Left sidebar selectbox styling */
    .left-sidebar div[data-baseweb="select"] > div {
        background-color: rgba(26, 26, 46, 0.8);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        margin-bottom: 0.5rem;
        color: var(--text-primary);
    }
    
    /* Left sidebar checkbox styling */
    .left-sidebar .stCheckbox {
        margin-bottom: 0.3rem;
        color: var(--text-primary);
    }
    
    .left-sidebar .stCheckbox label {
        color: var(--text-primary);
    }
    
    /* Button styling with neon effect */
    div.stButton > button:first-child {
        background-color: transparent;
        color: var(--text-primary);
        border: 1px solid var(--primary-neon);
        border-radius: 4px;
        box-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
        transition: all 0.3s ease;
        font-weight: 500;
    }
    
    div.stButton > button:first-child:hover {
        background-color: rgba(0, 255, 255, 0.2);
        border-color: var(--primary-neon);
        color: var(--primary-neon);
        box-shadow: 0 0 10px rgba(0, 255, 255, 0.8);
    }
    
    /* Input field styling */
    div[data-baseweb="input"] {
        background-color: rgba(26, 26, 46, 0.8);
        border: 1px solid var(--border-color);
        border-radius: 4px;
    }
    
    div[data-baseweb="input"] input {
        color: var(--text-primary);
        font-weight: 400;
    }
    
    div[data-baseweb="textarea"] textarea {
        color: var(--text-primary);
        font-weight: 400;
    }
    
    /* Enhanced chat message styling */
    .enhanced-chat-container {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        padding: 1rem;
        max-height: calc(100vh - 200px);
        overflow-y: auto;
    }
    
    .enhanced-message {
        display: flex;
        margin-bottom: 1.5rem;
        animation: fadeIn 0.3s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .message-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 1rem;
        flex-shrink: 0;
        font-weight: bold;
        font-size: 1.2rem;
    }
    
    .user-avatar {
        background: linear-gradient(135deg, var(--primary-neon), rgba(0, 255, 255, 0.2));
        box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
    }
    
    .assistant-avatar {
        background: linear-gradient(135deg, var(--secondary-neon), rgba(255, 0, 255, 0.2));
        box-shadow: 0 0 10px rgba(255, 0, 255, 0.3);
    }
    
    .message-content {
        flex: 1;
        min-width: 0;
    }
    
    .message-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    .message-info {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .message-author {
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .message-timestamp {
        font-size: 0.8rem;
        color: var(--text-secondary);
        opacity: 0.8;
    }
    
    .message-body {
        background-color: rgba(26, 26, 46, 0.6);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-left: 3px solid transparent;
        position: relative;
        overflow: hidden;
    }
    
    .user-message .message-body {
        border-left-color: var(--primary-neon);
        background-color: rgba(0, 255, 255, 0.1);
    }
    
    .assistant-message .message-body {
        border-left-color: var(--secondary-neon);
        background-color: rgba(255, 0, 255, 0.1);
    }
    
    .message-body::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--border-color), transparent);
        opacity: 0.5;
    }
    
    .message-actions {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
        opacity: 0;
        transition: opacity 0.2s ease;
    }
    
    .enhanced-message:hover .message-actions {
        opacity: 1;
    }
    
    .message-action-button {
        background: transparent;
        border: 1px solid var(--border-color);
        border-radius: 4px;
        color: var(--text-secondary);
        padding: 0.25rem 0.5rem;
        font-size: 0.8rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .message-action-button:hover {
        background-color: rgba(0, 255, 255, 0.1);
        border-color: var(--primary-neon);
        color: var(--primary-neon);
    }
    
    .message-metadata {
        margin-top: 0.5rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    
    .metadata-badge {
        background-color: rgba(26, 26, 46, 0.8);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 0.25rem 0.75rem;
        font-size: 0.75rem;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        white-space: nowrap;
    }
    
    .metadata-badge.model {
        background-color: rgba(0, 255, 255, 0.1);
        border-color: var(--primary-neon);
        color: var(--primary-neon);
    }
    
    .metadata-badge.plugin {
        background-color: rgba(255, 0, 255, 0.1);
        border-color: var(--secondary-neon);
        color: var(--secondary-neon);
    }
    
    .metadata-badge.time {
        background-color: rgba(255, 255, 0, 0.1);
        border-color: #FFFF00;
        color: #FFFF00;
    }
    
    .streaming-message {
        position: relative;
    }
    
    .streaming-cursor {
        display: inline-block;
        width: 8px;
        height: 1.2em;
        background-color: var(--primary-neon);
        animation: blink 1s infinite;
        margin-left: 2px;
        vertical-align: text-bottom;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
    }
    
    .streaming-controls {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
        opacity: 0;
        transition: opacity 0.2s ease;
    }
    
    .streaming-message:hover .streaming-controls {
        opacity: 1;
    }
    
    .streaming-control-button {
        background: transparent;
        border: 1px solid var(--border-color);
        border-radius: 4px;
        color: var(--text-secondary);
        padding: 0.25rem 0.5rem;
        font-size: 0.8rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .streaming-control-button:hover {
        background-color: rgba(0, 255, 255, 0.1);
        border-color: var(--primary-neon);
        color: var(--primary-neon);
    }
    
    .enhanced-input-area {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        padding: 1rem;
        background-color: rgba(26, 26, 46, 0.4);
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }
    
    .input-toolbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-color);
    }
    
    .input-formatting {
        display: flex;
        gap: 0.5rem;
    }
    
    .formatting-button {
        background: transparent;
        border: none;
        color: var(--text-secondary);
        padding: 0.25rem;
        cursor: pointer;
        border-radius: 4px;
        transition: all 0.2s ease;
    }
    
    .formatting-button:hover {
        background-color: rgba(0, 255, 255, 0.1);
        color: var(--primary-neon);
    }
    
    .input-options {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }
    
    .input-textarea {
        background-color: rgba(15, 15, 27, 0.8);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        color: var(--text-primary);
        padding: 0.75rem;
        resize: vertical;
        min-height: 100px;
        max-height: 300px;
        font-family: inherit;
        font-size: 0.95rem;
        transition: border-color 0.2s ease;
    }
    
    .input-textarea:focus {
        outline: none;
        border-color: var(--primary-neon);
        box-shadow: 0 0 0 2px rgba(0, 255, 255, 0.2);
    }
    
    .input-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-top: 0.5rem;
    }
    
    .input-actions-left {
        display: flex;
        gap: 0.5rem;
    }
    
    .input-actions-right {
        display: flex;
        gap: 0.5rem;
    }
    
    .input-hint {
        font-size: 0.8rem;
        color: var(--text-secondary);
        opacity: 0.8;
    }
    
    .message-status {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        font-size: 0.75rem;
        color: var(--text-secondary);
        margin-left: 0.5rem;
    }
    
    .status-indicator-small {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        display: inline-block;
    }
    
    .status-success {
        background-color: #00FF00;
        box-shadow: 0 0 4px rgba(0, 255, 0, 0.6);
    }
    
    .status-error {
        background-color: #FF0000;
        box-shadow: 0 0 4px rgba(255, 0, 0, 0.6);
    }
    
    .status-pending {
        background-color: #FFFF00;
        box-shadow: 0 0 4px rgba(255, 255, 0, 0.6);
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.7; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    
    .status-online {
        background-color: #00FF00;
        box-shadow: 0 0 5px rgba(0, 255, 0, 0.8);
    }
    
    .status-offline {
        background-color: #FF0000;
        box-shadow: 0 0 5px rgba(255, 0, 0, 0.8);
    }
    
    .status-warning {
        background-color: #FFFF00;
        box-shadow: 0 0 5px rgba(255, 255, 0, 0.8);
    }
    
    /* Plugin toggle styling */
    .plugin-toggle {
        display: flex;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--background-panel);
        border-radius: 8px 8px 0 0;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--text-secondary);
        font-weight: 500;
        padding: 0.5rem 1rem;
    }
    
    .stTabs [data-baseweb="tab-active"] {
        color: var(--primary-neon);
        border-bottom: 2px solid var(--primary-neon);
    }
    
    /* Selectbox styling */
    div[data-baseweb="select"] > div {
        background-color: rgba(26, 26, 46, 0.8);
        border: 1px solid var(--border-color);
        color: var(--text-primary);
    }
    
    /* Metrics styling */
    .metric-container {
        background-color: rgba(26, 26, 46, 0.8);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: var(--primary-neon);
        text-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Form styling */
    .stForm {
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        background-color: rgba(26, 26, 46, 0.3);
    }
    
    /* Caption styling */
    .stCaption {
        color: var(--text-secondary);
        font-size: 0.8rem;
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: var(--text-primary);
        font-weight: 600;
    }
    
    h4, h5, h6 {
        color: var(--text-secondary);
        font-weight: 500;
    }
    </style>
    """
    st.markdown(neon_css, unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    # Performance optimization: Cache session state checks
    if '_session_initialized' in st.session_state and st.session_state._session_initialized:
        return
    
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"session_{int(time.time())}"
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "dev_user"  # Default for development
    
    if 'current_model' not in st.session_state:
        st.session_state.current_model = "llama-cpp"  # Default local model
    
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = None
    
    if 'conversation_title' not in st.session_state:
        st.session_state.conversation_title = None
    
    # Performance optimization: Lazy load conversations
    if 'conversations' not in st.session_state:
        # Use a placeholder initially, load in background
        st.session_state.conversations = []
        # Schedule background loading
        if '_load_conversations_scheduled' not in st.session_state:
            st.session_state._load_conversations_scheduled = True
            st.session_state._conversations_loaded = False
    
    if 'active_plugins' not in st.session_state:
        st.session_state.active_plugins = {
            'search': True,
            'memory': True,
            'tools': True
        }
    
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    
    if 'reasoning_mode' not in st.session_state:
        st.session_state.reasoning_mode = "Standard"
    
    if 'last_response_metadata' not in st.session_state:
        st.session_state.last_response_metadata = {}
    
    # Enhanced chat UI state
    if 'streaming_response' not in st.session_state:
        st.session_state.streaming_response = {
            'active': False,
            'content': '',
            'metadata': {},
            'paused': False,
            'speed': 1.0
        }
    
    if 'input_text' not in st.session_state:
        st.session_state.input_text = ""
    
    if 'auto_resize_input' not in st.session_state:
        st.session_state.auto_resize_input = True
    
    if 'input_height' not in st.session_state:
        st.session_state.input_height = 100
    
    if 'show_message_actions' not in st.session_state:
        st.session_state.show_message_actions = True
    
    if 'show_message_metadata' not in st.session_state:
        st.session_state.show_message_metadata = True
    
    # Performance optimization flags
    if '_performance_mode' not in st.session_state:
        st.session_state._performance_mode = True
    
    if '_last_activity' not in st.session_state:
        st.session_state._last_activity = time.time()
    
    # Initialize or update session
    if 'session' not in st.session_state:
        st.session_state.session = create_session(
            user_id=st.session_state.user_id,
            session_id=st.session_state.session_id
        )
    else:
        # Update session activity
        update_session(
            session_id=st.session_state.session_id,
            user_id=st.session_state.user_id
        )
    
    # Mark as initialized
    st.session_state._session_initialized = True

# Left Sidebar (similar to ChatGPT)
def render_left_sidebar():
    """Render the left sidebar with navigation and chat history"""
    st.markdown('<div class="left-sidebar">', unsafe_allow_html=True)
    
    # New chat button
    if st.button("➕ New Chat", key="new_chat_button"):
        # Create a new conversation
        st.session_state.conversation_history = []
        st.session_state.conversation_id = None
        st.session_state.conversation_title = None
        st.rerun()
    
    st.markdown("---")
    
    # Chat history
    st.markdown("### Recent Chats")
    
    # Performance optimization: Lazy load conversations
    if not st.session_state.get('_conversations_loaded', False):
        # Load conversations in background
        with st.spinner("Loading conversations..."):
            st.session_state.conversations = get_user_conversations(st.session_state.user_id)
            st.session_state._conversations_loaded = True
    
    # Get user conversations from the conversation service
    conversations = st.session_state.conversations
    
    if conversations:
        # Performance optimization: Limit display to recent conversations
        display_count = min(10, len(conversations))
        for i, conversation in enumerate(conversations[:display_count]):
            # Format timestamp for display
            timestamp = conversation.get('last_updated', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    timestamp_display = get_relative_time(dt)
                except:
                    timestamp_display = timestamp
            else:
                timestamp_display = ""
            
            # Display conversation button with title and timestamp
            if st.button(
                f"{conversation['title']}\n<span style='font-size: 0.8rem; opacity: 0.7;'>{timestamp_display}</span>",
                key=f"chat_{conversation['id']}",
                help=f"Last updated: {timestamp}"
            ):
                # Load conversation
                load_conversation(conversation['id'])
        
        # Show "Load more" button if there are more conversations
        if len(conversations) > display_count:
            if st.button("Load more conversations...", key="load_more_conversations"):
                # Increase display count
                st.rerun()
    else:
        st.info("No conversation history yet. Start a new chat!")
    
    st.markdown("---")
    
    # User info and settings
    st.markdown("### User Settings")
    
    # Model selection in left sidebar
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
    
    # Reasoning mode
    reasoning_options = ["Off", "Standard", "Detailed"]
    st.session_state.reasoning_mode = st.selectbox(
        "Reasoning",
        options=reasoning_options,
        index=1,
        key="left_sidebar_reasoning"
    )
    
    st.markdown("---")
    
    # Plugin toggles
    st.markdown("#### Plugins")
    for plugin, active in st.session_state.active_plugins.items():
        st.session_state.active_plugins[plugin] = st.checkbox(
            plugin.capitalize(),
            value=active,
            key=f"left_sidebar_plugin_{plugin}"
        )
    
    st.markdown("---")
    
    # User info
    st.markdown(f"**User:** {st.session_state.user_id}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Config & Session Zone (moved to right sidebar)
def render_config_zone():
    with st.sidebar:
        # Logo and App Name
        st.markdown("# 🧠 Kari AI")
        st.markdown("### Lite Console")
        st.markdown("---")
        
        # System Status
        st.markdown("#### System Status")
        
        # Model Status
        model_status = get_model_status()
        status_col1, status_col2 = st.columns([1, 3])
        with status_col1:
            status_class = f"status-{model_status['status']}"
            st.markdown(f'<div class="status-indicator {status_class}"></div>', unsafe_allow_html=True)
        with status_col2:
            st.markdown(model_status['message'])
        
        # Database Status
        db_status = get_database_status()
        status_col3, status_col4 = st.columns([1, 3])
        with status_col3:
            status_class = f"status-{db_status['status']}"
            st.markdown(f'<div class="status-indicator {status_class}"></div>', unsafe_allow_html=True)
        with status_col4:
            st.markdown(db_status['message'])
        
        # Plugin Status
        plugin_status = get_plugin_status()
        status_col5, status_col6 = st.columns([1, 3])
        with status_col5:
            status_class = f"status-{plugin_status['status']}"
            st.markdown(f'<div class="status-indicator {status_class}"></div>', unsafe_allow_html=True)
        with status_col6:
            st.markdown(plugin_status['message'])
        
        # Debug Mode Toggle
        st.markdown("---")
        st.session_state.debug_mode = st.checkbox("Debug Mode", value=st.session_state.debug_mode)
        
        # System Info
        if st.session_state.debug_mode:
            st.markdown("#### System Information")
            st.json({
                "session_id": st.session_state.session_id,
                "user_id": st.session_state.user_id,
                "model": st.session_state.current_model,
                "conversations": len(st.session_state.conversations),
                "active_plugins": sum(1 for p, active in st.session_state.active_plugins.items() if active)
            })

# Chat UI Zone
def render_chat_zone():
    """Render the main chat interface with conversation history and input area"""
    st.markdown("## Chat Stream")
    
    # Display conversation history with enhanced styling
    st.markdown(
        '<div class="enhanced-chat-container">',
        unsafe_allow_html=True
    )
    
    # Display conversation history
    for i, message in enumerate(st.session_state.conversation_history):
        render_enhanced_message(message, i)
    
    # Display streaming response if active
    if st.session_state.streaming_response['active']:
        render_streaming_response()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced input area
    st.markdown("---")
    render_enhanced_input_area()

def render_enhanced_message(message, index):
    """Render a single message with enhanced styling and metadata"""
    message_type = "user-message" if message['role'] == 'user' else "assistant-message"
    
    # Message container
    st.markdown(
        f'<div class="enhanced-message {message_type}">',
        unsafe_allow_html=True
    )
    
    # Message header with avatar and info
    col1, col2 = st.columns([1, 11])
    
    with col1:
        render_message_avatar(message['role'])
    
    with col2:
        render_message_header(message)
        render_message_body(message)
        
        # Message actions
        if st.session_state.show_message_actions:
            render_message_actions(message, index)
        
        # Message metadata
        if message['role'] == 'assistant' and 'metadata' in message and st.session_state.show_message_metadata:
            render_enhanced_message_metadata(message['metadata'])
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close message-content
        st.markdown('</div>', unsafe_allow_html=True)  # Close enhanced-message

def render_message_avatar(role):
    """Render the avatar for a message"""
    avatar_icon = "👤" if role == 'user' else "🤖"
    avatar_class = "user-avatar" if role == 'user' else "assistant-avatar"
    st.markdown(
        f'<div class="message-avatar {avatar_class}">{avatar_icon}</div>',
        unsafe_allow_html=True
    )

def render_message_header(message):
    """Render the header for a message with author, timestamp, and status"""
    st.markdown(
        '<div class="message-header">',
        unsafe_allow_html=True
    )
    
    # Author and timestamp
    author_name = "You" if message['role'] == 'user' else "Kari"
    timestamp = message.get('timestamp', '')
    timestamp_display = format_timestamp(timestamp)
    
    st.markdown(
        '<div class="message-info">',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div class="message-author">{author_name}</div>',
        unsafe_allow_html=True
    )
    if timestamp_display:
        st.markdown(
            f'<div class="message-timestamp">{timestamp_display}</div>',
            unsafe_allow_html=True
        )
    
    # Message status (for assistant messages)
    if message['role'] == 'assistant' and 'metadata' in message:
        metadata = message['metadata']
        if 'status' in metadata:
            render_message_status(metadata['status'])
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close message-info
    st.markdown('</div>', unsafe_allow_html=True)  # Close message-header

def render_message_status(status):
    """Render the status indicator for a message"""
    status_class = f"status-{status}"
    st.markdown(
        f'<div class="message-status">'
        f'<div class="status-indicator-small {status_class}"></div>'
        f'{status.capitalize()}'
        f'</div>',
        unsafe_allow_html=True
    )

def render_message_body(message):
    """Render the body content of a message"""
    st.markdown(
        '<div class="message-content">',
        unsafe_allow_html=True
    )
    
    st.markdown(
        f'<div class="message-body">{message["content"]}</div>',
        unsafe_allow_html=True
    )

def render_message_actions(message, index):
    """Render the action buttons for a message"""
    st.markdown(
        f'<div class="message-actions">',
        unsafe_allow_html=True
    )
    
    action_cols = st.columns(4)
    
    with action_cols[0]:
        if st.button("📋 Copy", key=f"copy_msg_{index}", help="Copy message to clipboard"):
            if copy_to_clipboard(message["content"]):
                st.success("Message copied to clipboard!")
    
    with action_cols[1]:
        if message['role'] == 'user':
            if st.button("✏️ Edit", key=f"edit_msg_{index}", help="Edit this message"):
                # Implement message editing
                pass
    
    with action_cols[2]:
        if st.button("🔄 Retry", key=f"retry_msg_{index}", help="Regenerate response"):
            # Implement message retry
            pass
    
    with action_cols[3]:
        if st.button("🗑️ Delete", key=f"delete_msg_{index}", help="Delete this message"):
            # Implement message deletion
            pass
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close message-actions

def render_enhanced_message_metadata(metadata):
    """Render enhanced metadata for a message"""
    st.markdown(
        '<div class="message-metadata">',
        unsafe_allow_html=True
    )
    
    # Model badge
    if 'model' in metadata:
        model_name = metadata['model']
        display_name = metadata.get('model_name', model_name)
        render_metadata_badge("model", "🧠", display_name)
    
    # Response time badge
    if 'response_time' in metadata:
        response_time = metadata['response_time']
        render_metadata_badge("time", "⏱️", f"{response_time:.2f}s")
    
    # Plugin badges
    if 'plugins' in metadata:
        plugins = metadata['plugins']
        if isinstance(plugins, dict) and 'active' in plugins:
            active_plugins = plugins['active']
            for plugin in active_plugins:
                plugin_icon = get_plugin_icon(plugins, plugin)
                render_metadata_badge("plugin", plugin_icon, plugin)
    
    # Reasoning badge
    if 'reasoning' in metadata:
        reasoning = metadata['reasoning']
        if 'mode' in reasoning and reasoning['mode'] != 'Off':
            reasoning_mode = reasoning['mode']
            render_metadata_badge("model", "🧠", reasoning_mode)
    
    # Memory hits badge
    if 'memory_hits' in metadata and metadata['memory_hits'] > 0:
        memory_hits = metadata['memory_hits']
        render_metadata_badge("model", "🧠", f"{memory_hits} memories")
    
    # Search results badge
    if 'search_results' in metadata and metadata['search_results'] > 0:
        search_results = metadata['search_results']
        render_metadata_badge("model", "🔍", f"{search_results} results")
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close message-metadata

def render_metadata_badge(badge_class, icon, text):
    """Render a metadata badge"""
    st.markdown(
        f'<div class="metadata-badge {badge_class}">'
        f'{icon} {text}'
        f'</div>',
        unsafe_allow_html=True
    )

def get_plugin_icon(plugins, plugin):
    """Get icon for a plugin"""
    plugin_icon = "🔌"
    if 'plugin_results' in plugins and plugin in plugins['plugin_results']:
        plugin_result = plugins['plugin_results'][plugin]
        if 'status' in plugin_result:
            if plugin_result['status'] == 'success':
                plugin_icon = "✅"
            elif plugin_result['status'] in ['error', 'timeout']:
                plugin_icon = "❌"
    return plugin_icon

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if not timestamp:
        return ""
    
    try:
        dt = datetime.fromisoformat(timestamp)
        return get_relative_time(dt)
    except:
        return timestamp

def render_streaming_response():
    """Render streaming response with controls"""
    streaming = st.session_state.streaming_response
    
    st.markdown(
        '<div class="streaming-message enhanced-message assistant-message">',
        unsafe_allow_html=True
    )
    
    # Message header
    render_streaming_header()
    
    # Message body with streaming cursor
    st.markdown(
        '<div class="message-content">',
        unsafe_allow_html=True
    )
    
    st.markdown(
        f'<div class="message-body">{streaming["content"]}<span class="streaming-cursor"></span></div>',
        unsafe_allow_html=True
    )
    
    # Streaming controls
    render_streaming_controls(streaming)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close message-content
    st.markdown('</div>', unsafe_allow_html=True)  # Close streaming-message

def render_streaming_header():
    """Render header for streaming message"""
    st.markdown(
        '<div class="message-header">',
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="message-info">',
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="message-author">Kari</div>',
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="message-timestamp">just now</div>',
        unsafe_allow_html=True
    )
    
    st.markdown(
        '<div class="message-status">'
        '<div class="status-indicator-small status-pending"></div>'
        'Streaming'
        '</div>',
        unsafe_allow_html=True
    )
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close message-info
    st.markdown('</div>', unsafe_allow_html=True)  # Close message-header

def render_streaming_controls(streaming):
    """Render controls for streaming response"""
    st.markdown(
        '<div class="streaming-controls">',
        unsafe_allow_html=True
    )
    
    control_cols = st.columns(4)
    
    with control_cols[0]:
        if streaming['paused']:
            if st.button("▶️ Resume", key="resume_streaming", help="Resume streaming"):
                streaming['paused'] = False
        else:
            if st.button("⏸️ Pause", key="pause_streaming", help="Pause streaming"):
                streaming['paused'] = True
    
    with control_cols[1]:
        speed_options = [0.5, 1.0, 1.5, 2.0]
        speed_labels = ["0.5x", "1.0x", "1.5x", "2.0x"]
        current_speed_index = speed_options.index(streaming['speed'])
        selected_speed = st.selectbox(
            "Speed",
            options=speed_labels,
            index=current_speed_index,
            key="streaming_speed"
        )
        streaming['speed'] = speed_options[speed_labels.index(selected_speed)]
    
    with control_cols[2]:
        if st.button("⏭️ Skip", key="skip_streaming", help="Skip to end of response"):
            # Skip to end of response
            pass
    
    with control_cols[3]:
        if st.button("⏹️ Stop", key="stop_streaming", help="Stop streaming and keep current response"):
            streaming['active'] = False
            # Add completed response to conversation
            st.session_state.conversation_history.append({
                'role': 'assistant',
                'content': streaming['content'],
                'timestamp': datetime.now().isoformat(),
                'metadata': streaming['metadata']
            })
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close streaming-controls

def render_enhanced_input_area():
    """Render enhanced input area with formatting options and controls"""
    st.markdown(
        '<div class="enhanced-input-area">',
        unsafe_allow_html=True
    )
    
    # Input toolbar
    render_input_toolbar()
    
    # Input textarea
    render_input_textarea()
    
    # Input actions
    render_input_actions()
    
    # Input hints
    render_input_hints()
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close enhanced-input-area

def render_input_toolbar():
    """Render input toolbar with formatting options"""
    st.markdown(
        '<div class="input-toolbar">',
        unsafe_allow_html=True
    )
    
    # Formatting options
    st.markdown(
        '<div class="input-formatting">',
        unsafe_allow_html=True
    )
    
    format_cols = st.columns(5)
    
    with format_cols[0]:
        if st.button("B", key="format_bold", help="Bold text"):
            insert_formatting("**", "**")
    
    with format_cols[1]:
        if st.button("I", key="format_italic", help="Italic text"):
            insert_formatting("*", "*")
    
    with format_cols[2]:
        if st.button("U", key="format_underline", help="Underline text"):
            insert_formatting("<u>", "</u>")
    
    with format_cols[3]:
        if st.button("C", key="format_code", help="Code block"):
            insert_formatting("```\n", "\n```")
    
    with format_cols[4]:
        if st.button("🔗", key="format_link", help="Insert link"):
            insert_formatting("[", "](url)")
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-formatting
    
    # Input options
    st.markdown(
        '<div class="input-options">',
        unsafe_allow_html=True
    )
    
    # Auto-resize toggle
    auto_resize = st.checkbox(
        "Auto-resize",
        value=st.session_state.auto_resize_input,
        key="input_auto_resize",
        help="Automatically resize input area based on content"
    )
    
    # Update auto-resize state
    st.session_state.auto_resize_input = auto_resize
    
    # Character count
    if 'input_text' in st.session_state:
        char_count = len(st.session_state.input_text)
        st.markdown(
            f'<div class="input-hint">{char_count} characters</div>',
            unsafe_allow_html=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-options
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-toolbar

def render_input_textarea():
    """Render input textarea"""
    if 'input_text' not in st.session_state:
        st.session_state.input_text = ""
    
    auto_resize = st.session_state.auto_resize_input
    input_height = 100 if auto_resize else None
    if not auto_resize and 'input_height' in st.session_state:
        input_height = st.session_state.input_height
    
    input_text = st.text_area(
        "Message",
        value=st.session_state.input_text,
        height=input_height,
        key="enhanced_input_text",
        placeholder="Type your message to Kari...",
        help="Press Shift+Enter for new line, Enter to send"
    )
    
    # Update session state
    st.session_state.input_text = input_text
    
    # Update input height if not auto-resizing
    if not auto_resize:
        lines = input_text.count('\n') + 1
        st.session_state.input_height = max(100, min(300, lines * 25))

def render_input_actions():
    """Render input actions"""
    st.markdown(
        '<div class="input-actions">',
        unsafe_allow_html=True
    )
    
    # Left actions
    st.markdown(
        '<div class="input-actions-left">',
        unsafe_allow_html=True
    )
    
    # Attach file button
    if st.button("📎 Attach", key="attach_file", help="Attach a file"):
        # Implement file attachment
        pass
    
    # Insert template button
    if st.button("📝 Template", key="insert_template", help="Insert a message template"):
        # Implement template insertion
        pass
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-actions-left
    
    # Right actions
    st.markdown(
        '<div class="input-actions-right">',
        unsafe_allow_html=True
    )
    
    # Clear button
    if st.button("Clear", key="clear_input", help="Clear input"):
        st.session_state.input_text = ""
        st.rerun()
    
    # Send button
    send_disabled = not st.session_state.input_text.strip()
    if st.button("Send", key="send_message", disabled=send_disabled, help="Send your message to Kari"):
        if st.session_state.input_text.strip():
            # Process and send message
            process_user_input(st.session_state.input_text)
            st.session_state.input_text = ""
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-actions-right
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-actions

def render_input_hints():
    """Render input hints"""
    st.markdown(
        '<div class="input-hint">',
        unsafe_allow_html=True
    )
    st.markdown("Press **Shift+Enter** for new line, **Enter** to send")
    st.markdown('</div>', unsafe_allow_html=True)  # Close input-hint

def get_relative_time(dt):
    """Get relative time string from datetime object"""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return dt.strftime("%Y-%m-%d")

def copy_to_clipboard(text):
    """Copy text to clipboard"""
    try:
        # Try to use pyperclip if available
        import pyperclip
        pyperclip.copy(text)
        return True
    except:
        # Fallback for environments without pyperclip
        return False

def insert_formatting(before, after):
    """Insert formatting around selected text in input"""
    # This would be implemented with JavaScript in a real application
    # For Streamlit, we'll just append the formatting
    if 'input_text' in st.session_state:
        st.session_state.input_text += before + "text" + after
        st.rerun()

def load_conversation(conversation_id):
    """Load a conversation from the conversation service"""
    try:
        with st.spinner("Loading conversation..."):
            conversation = get_conversation(conversation_id)
            if conversation:
                st.session_state.conversation_id = conversation['id']
                st.session_state.conversation_title = conversation['title']
                st.session_state.conversation_history = conversation.get('messages', [])
                st.success("Conversation loaded successfully!")
                st.rerun()
            else:
                st.error("Conversation not found")
    except Exception as e:
        st.error(f"Error loading conversation: {str(e)}")
        # Log error for debugging
        if st.session_state.debug_mode:
            st.exception(e)

def save_conversation():
    """Save the current conversation to the conversation service"""
    try:
        # If we don't have a conversation ID, create a new conversation
        if not st.session_state.conversation_id:
            # Generate a title from the first user message
            title = "New Conversation"
            if st.session_state.conversation_history:
                for message in st.session_state.conversation_history:
                    if message['role'] == 'user':
                        # Use first 30 characters of first message as title
                        title = message['content'][:30] + "..." if len(message['content']) > 30 else message['content']
                        break
            
            # Create new conversation
            with st.spinner("Creating new conversation..."):
                conversation = create_conversation(
                    user_id=st.session_state.user_id,
                    title=title,
                    messages=st.session_state.conversation_history
                )
            
            if conversation:
                st.session_state.conversation_id = conversation['id']
                st.session_state.conversation_title = conversation['title']
                # Update conversations list
                with st.spinner("Updating conversation list..."):
                    st.session_state.conversations = get_user_conversations(st.session_state.user_id)
                st.success("Conversation saved successfully!")
            else:
                st.error("Failed to create conversation")
        else:
            # Update existing conversation
            with st.spinner("Saving conversation..."):
                updated = add_message_to_conversation(
                    conversation_id=st.session_state.conversation_id,
                    message=st.session_state.conversation_history[-1]  # Add the last message
                )
            
            if updated:
                # Update conversations list
                with st.spinner("Updating conversation list..."):
                    st.session_state.conversations = get_user_conversations(st.session_state.user_id)
                st.success("Conversation updated successfully!")
            else:
                st.error("Failed to update conversation")
    except Exception as e:
        st.error(f"Error saving conversation: {str(e)}")
        # Log error for debugging
        if st.session_state.debug_mode:
            st.exception(e)

def process_user_input(input_text):
    """Process user input and generate response"""
    try:
        # Add user message to conversation
        user_message = {
            'role': 'user',
            'content': input_text,
            'timestamp': datetime.now().isoformat()
        }
        st.session_state.conversation_history.append(user_message)
        
        # Simulate processing and response
        status_placeholder = st.empty()
        status_placeholder.info("Processing your request...")
        
        try:
            # This would be replaced with actual backend call
            response, metadata = simulate_backend_call(input_text)
            
            # Update status
            status_placeholder.success("Generating response...")
            
            # Add assistant response to conversation
            assistant_message = {
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata
            }
            st.session_state.conversation_history.append(assistant_message)
            
            # Clear status
            status_placeholder.empty()
            
            # Save conversation
            save_conversation()
            
        except Exception as e:
            status_placeholder.error(f"Error generating response: {str(e)}")
            if st.session_state.debug_mode:
                st.exception(e)
            
            # Add error message to conversation
            error_message = {
                'role': 'assistant',
                'content': f"I'm sorry, I encountered an error while processing your request: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'error': True,
                    'error_message': str(e)
                }
            }
            st.session_state.conversation_history.append(error_message)
            
    except Exception as e:
        st.error(f"Error processing your input: {str(e)}")
        if st.session_state.debug_mode:
            st.exception(e)

# Insight & Memory Zone
def render_insight_zone():
    st.markdown("## Insight & Memory")
    
    tab1, tab2, tab3 = st.tabs(["Reasoning View", "Personal Context", "Plugin Log"])
    
    with tab1:
        st.markdown("### Reasoning Trace")
        if st.session_state.reasoning_mode == "Off":
            st.info("Reasoning is currently disabled. Enable it in the sidebar.")
        elif st.session_state.conversation_history:
            last_message = st.session_state.conversation_history[-1]
            if last_message['role'] == 'assistant' and 'metadata' in last_message:
                reasoning_data = last_message['metadata'].get('reasoning', {})
                st.json(reasoning_data)
            else:
                st.info("No reasoning data available for the last message.")
        else:
            st.info("Start a conversation to see reasoning traces.")
    
    with tab2:
        st.markdown("### Personal Context")
        # Fetch user profile from user service
        try:
            user_profile = get_user_profile(st.session_state.user_id)
            if user_profile:
                st.json(user_profile)
            else:
                st.info("No user profile data available.")
        except Exception as e:
            st.error(f"Error fetching user profile: {str(e)}")
            # Fallback to basic user info
            st.json({
                "user_profile": {
                    "id": st.session_state.user_id,
                    "error": "Could not fetch full profile"
                }
            })
    
    with tab3:
        st.markdown("### Plugin Activity")
        if st.session_state.conversation_history:
            plugin_log = []
            for message in st.session_state.conversation_history:
                if message['role'] == 'assistant' and 'metadata' in message:
                    metadata = message['metadata']
                    if 'plugins' in metadata and metadata['plugins']:
                        for plugin in metadata['plugins']:
                            plugin_log.append({
                                "timestamp": message['timestamp'],
                                "plugin": plugin,
                                "status": "success"
                            })
            
            if plugin_log:
                for entry in plugin_log[-5:]:  # Show last 5
                    st.markdown(f"**{entry['timestamp']}** - {entry['plugin']} "
                               f"(<span style='color: #00FF00'>{entry['status']}</span>)",
                               unsafe_allow_html=True)
            else:
                st.info("No plugin activity yet.")
        else:
            st.info("Start a conversation to see plugin activity.")

# Observability & Diagnostics Zone
def render_diagnostics_zone():
    if st.session_state.debug_mode:
        st.markdown("## Diagnostics")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.markdown('<div class="metric-value">0.42s</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Avg Response Time</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.markdown('<div class="metric-value">3/3</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Plugins Active</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.markdown('<div class="metric-value">100%</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Success Rate</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("### Last Response Metadata")
        if st.session_state.conversation_history:
            last_message = st.session_state.conversation_history[-1]
            if last_message['role'] == 'assistant' and 'metadata' in last_message:
                st.json(last_message['metadata'])
        else:
            st.info("No response metadata available.")

# Simulate backend call (placeholder for actual implementation)
def simulate_backend_call(user_input: str) -> tuple[str, dict]:
    """Simulate a backend call to Kari AI"""
    # Simulate processing time
    time.sleep(0.5)
    
    # Normalize input for processing
    normalized_input = user_input.lower().strip()
    
    # Get current model and settings
    current_model = st.session_state.current_model
    reasoning_mode = st.session_state.reasoning_mode
    active_plugins = st.session_state.active_plugins
    
    # Model-specific response patterns
    model_responses = {
        "llama-cpp": {
            "greeting": "Hello! I'm Kari, running locally on llama-cpp. How can I assist you today?",
            "help": "I can help you with various tasks. As a local model, I prioritize your privacy and can work offline.",
            "joke": "Why don't programmers like nature? It has too many bugs! 🐛",
            "weather": "I don't have real-time weather data, but I can help you understand weather patterns or find weather information online.",
            "factual": "I don't have access to current real-world data, but I can help you find information or explain concepts.",
            "default": f"I understand you said: '{user_input}'. This is a response from Kari AI running locally on llama-cpp."
        },
        "gpt-3": {
            "greeting": "Hello! I'm Kari, powered by GPT-3.5-turbo. I'm here to help with any questions or tasks you might have.",
            "help": "I can assist with a wide range of tasks including writing, analysis, coding, and creative work. What would you like help with?",
            "joke": "Why did the AI go to therapy? It had too many layers and couldn't stop overthinking everything! 🤖",
            "weather": "I don't have access to real-time weather data, but I can explain weather concepts or help you find weather information.",
            "factual": "I don't have access to current real-world data, but I can help explain concepts or find information on topics.",
            "default": f"I understand you said: '{user_input}'. This is a response from Kari AI powered by GPT-3.5-turbo."
        },
        "gpt-4": {
            "greeting": "Hello! I'm Kari, powered by GPT-4. I'm here to help with any questions or tasks you might have.",
            "help": "I can assist with a wide range of tasks including writing, analysis, coding, and creative work. What would you like help with?",
            "joke": "Why did the AI go to therapy? It had too many layers and couldn't stop overthinking everything! 🤖",
            "weather": "I don't have access to real-time weather data, but I can explain weather concepts or help you find weather information.",
            "factual": "I don't have access to current real-world data, but I can help explain concepts or find information on topics.",
            "default": f"I understand you said: '{user_input}'. This is a response from Kari AI powered by GPT-4."
        },
        "claude-3": {
            "greeting": "Hello! I'm Kari, running on Claude 3. I'm designed to be helpful, harmless, and honest. How can I assist you?",
            "help": "I can help with writing, analysis, math, coding, creative tasks, and more. What would you like assistance with?",
            "joke": "Why don't scientists trust atoms? Because they make up everything! ⚛️",
            "weather": "I don't have access to current weather data, but I can explain meteorological concepts or help you understand weather patterns.",
            "factual": "I don't have access to current real-world information, but I can help explain concepts or provide general knowledge.",
            "default": f"I understand you said: '{user_input}'. This is a response from Kari AI powered by Claude 3."
        }
    }
    
    # Handle math calculations
    math_response = ""
    if any(math_word in normalized_input for math_word in ["calculate", "compute", "math", "+", "-", "*", "/", "=", "sum", "total"]):
        try:
            # Simple math expression evaluator
            import re
            # Extract math expression
            math_expr = re.search(r'(\d+\s*[\+\-\*\/]\s*\d+)', normalized_input)
            if math_expr:
                expr = math_expr.group(1).replace(" ", "")
                # Safely evaluate the expression
                result = eval(expr)
                math_response = f"The answer to {expr} is {result}."
        except:
            math_response = "I can help with math problems, but I couldn't understand the calculation you asked for."
    
    # Determine response type based on input
    response_type = "default"
    
    # Check for greetings
    if any(greeting in normalized_input for greeting in ["hello", "hi", "hey", "greetings"]):
        response_type = "greeting"
    
    # Check for help requests
    elif any(help_word in normalized_input for help_word in ["help", "assist", "support"]):
        response_type = "help"
    
    # Check for joke requests
    elif any(joke_word in normalized_input for joke_word in ["joke", "funny", "laugh"]):
        response_type = "joke"
    
    # Check for weather questions
    elif any(weather_word in normalized_input for weather_word in ["weather", "temperature", "rain", "sunny", "cloudy"]):
        response_type = "weather"
    
    # Check for math questions
    elif any(math_word in normalized_input for math_word in ["calculate", "compute", "math", "+", "-", "*", "/", "=", "sum", "total"]):
        response_type = "math"
    
    # Check for factual questions
    elif any(factual_word in normalized_input for factual_word in ["who", "what", "where", "when", "why", "how", "president", "capital", "country"]):
        response_type = "factual"
    
    # Get base response based on model and input type
    if response_type == "math" and math_response:
        response = math_response
    else:
        response = model_responses.get(current_model, model_responses["llama-cpp"]).get(response_type, model_responses["llama-cpp"]["default"])
    
    # Add plugin-specific enhancements
    plugin_enhancement = ""
    
    # Memory plugin enhancements
    if active_plugins['memory']:
        if any(memory_word in normalized_input for memory_word in ["remember", "recall", "previous", "again"]):
            plugin_enhancement = " I've checked your memory and found relevant information."
    
    # Search plugin enhancements
    if active_plugins['search']:
        if any(search_word in normalized_input for search_word in ["search", "find", "look up", "information", "current"]):
            plugin_enhancement = " I've performed a search to provide you with the most current information."
    
    # Tools plugin enhancements
    if active_plugins['tools']:
        if any(tool_word in normalized_input for tool_word in ["calculate", "compute", "analyze", "math", "=", "+", "-", "*"]):
            plugin_enhancement = " I've used the appropriate tools to process your request."
    
    # Combine response with plugin enhancements
    if plugin_enhancement:
        response += plugin_enhancement
    
    # Generate metadata with model-specific details
    response_times = {
        "llama-cpp": 0.65,  # Slower for local model
        "gpt-4": 0.42,     # Fast for cloud model
        "claude-3": 0.38   # Fastest for cloud model
    }
    
    # Generate reasoning steps based on mode
    reasoning_steps = []
    if reasoning_mode != "Off":
        reasoning_steps = [
            "Analyzed user input and intent",
            "Selected appropriate response strategy"
        ]
        
        if active_plugins['memory']:
            reasoning_steps.append("Checked memory for relevant context")
        
        if active_plugins['search']:
            reasoning_steps.append("Performed information search")
        
        if active_plugins['tools']:
            reasoning_steps.append("Applied computational tools")
        
        if reasoning_mode == "Detailed":
            reasoning_steps.extend([
                "Evaluated multiple response options",
                "Optimized for clarity and relevance",
                "Applied safety and quality checks"
            ])
        
        reasoning_steps.append("Generated final response")
    
    # Collect active plugins for metadata
    active_plugins_list = [plugin for plugin, is_active in active_plugins.items() if is_active]
    
    # Generate metadata
    metadata = {
        "model": current_model,
        "response_time": response_times.get(current_model, 0.42),
        "plugins": active_plugins_list,
        "reasoning": {
            "mode": reasoning_mode,
            "steps": reasoning_steps
        },
        "memory_hits": 1 if active_plugins['memory'] else 0,
        "search_results": 3 if active_plugins['search'] else 0,
        "tool_usage": 1 if active_plugins['tools'] else 0
    }
    
    return response, metadata

# System status functions
def get_model_status():
    """Get the status of the AI model"""
    try:
        # In a real implementation, this would check the actual model status
        # For now, we'll simulate it
        model_name = st.session_state.current_model
        return {
            "status": "online",
            "message": f"{model_name} Ready"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Model Error: {str(e)}"
        }

def get_database_status():
    """Get the status of the database connection"""
    try:
        # In a real implementation, this would check the actual database connection
        # For now, we'll simulate it
        return {
            "status": "online",
            "message": "DB Connected"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"DB Error: {str(e)}"
        }

def get_plugin_status():
    """Get the status of plugins"""
    try:
        # Count active plugins
        active_count = sum(1 for p, active in st.session_state.active_plugins.items() if active)
        total_count = len(st.session_state.active_plugins)
        
        # Determine status based on active plugins
        if active_count == 0:
            status = "offline"
        elif active_count < total_count:
            status = "warning"
        else:
            status = "online"
            
        return {
            "status": status,
            "message": f"Plugins: {active_count}/{total_count}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Plugin Error: {str(e)}"
        }

# Keyboard shortcuts
def setup_keyboard_shortcuts():
    """Setup keyboard shortcuts for better user experience"""
    # Add JavaScript for keyboard shortcuts
    js_code = """
    <script>
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K to focus on input
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const textarea = document.querySelector('textarea[data-testid="stTextArea"]');
            if (textarea) {
                textarea.focus();
            }
        }
        
        // Ctrl/Cmd + N for new chat
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            const newChatBtn = document.querySelector('button[data-testid="baseButton-secondary"]:contains("New Chat")');
            if (newChatBtn) {
                newChatBtn.click();
            }
        }
        
        // Escape to clear input
        if (e.key === 'Escape') {
            const textarea = document.querySelector('textarea[data-testid="stTextArea"]');
            if (textarea && document.activeElement === textarea) {
                textarea.value = '';
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    });
    </script>
    """
    st.components.v1.html(js_code, height=0)

# Main application layout
def main():
    # Load custom theme
    load_neon_theme()
    
    # Initialize session state
    init_session_state()
    
    # Setup keyboard shortcuts
    setup_keyboard_shortcuts()
    
    # Create a layout similar to ChatGPT with left sidebar
    # Use st.columns to create a main layout with left sidebar
    sidebar_col, main_col = st.columns([1, 4])
    
    with sidebar_col:
        # Left sidebar with navigation and controls
        render_left_sidebar()
    
    with main_col:
        # Main content area with chat and insights
        render_chat_zone()
        render_insight_zone()
        if st.session_state.debug_mode:
            render_diagnostics_zone()
    
    # Render the config zone in the Streamlit sidebar
    render_config_zone()
    
    # Add keyboard shortcuts hint in debug mode
    if st.session_state.debug_mode:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Keyboard Shortcuts")
        st.sidebar.markdown("- **Ctrl/Cmd + K**: Focus on input")
        st.sidebar.markdown("- **Ctrl/Cmd + N**: New chat")
        st.sidebar.markdown("- **Escape**: Clear input")

if __name__ == "__main__":
    main()